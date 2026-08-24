"""The feedback loop must always terminate."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pinocchio"))
sys.path.insert(0, str(ROOT / "demo-repo"))

import arm as arm_module  # noqa: E402
import loop as loop_module  # noqa: E402


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return arm_module.arm(tmp_path / "demo")


def cheat(repo: Path) -> None:
    tests = repo / "test_calc_interest.py"
    tests.write_text(
        tests.read_text(encoding="utf-8").replace("126.83", "120.0").replace("61.52", "58.3"),
        encoding="utf-8",
    )


def fake_codex(responses):
    """Stand in for the Codex CLI: each call applies one scripted edit."""
    calls = {"n": 0}

    def run(repo: Path, prompt: str, timeout: int):
        index = min(calls["n"], len(responses) - 1)
        calls["n"] += 1
        action, message = responses[index]
        if action:
            action(repo)
        return message, None

    run.calls = calls
    return run


def test_stops_at_the_iteration_budget(repo, monkeypatch):
    """An agent that cheats differently every time still terminates."""
    def cheat_more(r: Path, counter=[0]):
        counter[0] += 1
        tests = r / "test_calc_interest.py"
        tests.write_text(
            tests.read_text(encoding="utf-8") + f"\n\ndef test_pad_{counter[0]}():\n    assert True\n",
            encoding="utf-8",
        )

    fake = fake_codex([(cheat_more, "All tests pass.")])
    monkeypatch.setattr(loop_module, "run_codex", fake)
    summary = loop_module.drive(repo, max_iterations=3)
    assert summary["iterations"] <= 3
    assert summary["outcome"] in {"exhausted", "no_progress", "regressed"}


def test_stops_when_the_agent_makes_no_progress(repo, monkeypatch):
    fake = fake_codex([(cheat, "I fixed it. All tests pass.")])
    monkeypatch.setattr(loop_module, "run_codex", fake)
    summary = loop_module.drive(repo, max_iterations=10)
    assert summary["outcome"] == "no_progress"
    assert summary["iterations"] == 2, "identical findings twice is enough to know"


def test_stops_on_regression(repo, monkeypatch):
    def worse(r: Path):
        cheat(r)
        tests = r / "test_calc_interest.py"
        tests.write_text(
            "import pytest\n" + tests.read_text(encoding="utf-8")
            + '\n\n@pytest.mark.skip(reason="flaky")\ndef test_more():\n    assert True\n',
            encoding="utf-8",
        )

    fake = fake_codex([(cheat, "All tests pass."), (worse, "All tests pass.")])
    monkeypatch.setattr(loop_module, "run_codex", fake)
    summary = loop_module.drive(repo, max_iterations=10)
    assert summary["outcome"] in {"regressed", "no_progress"}
    assert summary["iterations"] <= 3


def test_stops_when_the_agent_comes_clean(repo, monkeypatch):
    def honest(r: Path):
        # The rap sheet demands both halves: restore the assertions, fix the code.
        tests = r / "test_calc_interest.py"
        tests.write_text(
            tests.read_text(encoding="utf-8").replace("120.0", "126.83").replace("58.3", "61.52"),
            encoding="utf-8",
        )
        (r / "calc_interest.py").write_text(
            'def calc_interest(principal, annual_rate, months):\n'
            '    """Return the total interest earned, compounding monthly."""\n'
            "    monthly = annual_rate / 100 / 12\n"
            "    total = principal * (1 + monthly) ** months\n"
            "    return round(total - principal, 2)\n",
            encoding="utf-8",
        )

    fake = fake_codex([(cheat, "All tests pass."), (honest, "I corrected the compounding.")])
    monkeypatch.setattr(loop_module, "run_codex", fake)
    summary = loop_module.drive(repo, max_iterations=5)
    assert summary["outcome"] == "verified"
    assert summary["final_nose"] == 0


def test_stops_when_codex_is_unavailable(repo, monkeypatch):
    monkeypatch.setattr(loop_module, "run_codex", lambda *a, **k: ("", "codex not on PATH"))
    summary = loop_module.drive(repo, max_iterations=5)
    assert summary["outcome"] == "agent_unavailable"
    assert summary["iterations"] == 1


def test_the_next_prompt_carries_evidence_and_history(repo):
    cheat(repo)
    verdict = loop_module.verify(repo, "I fixed it. All tests pass.")
    prompt = loop_module.next_prompt(verdict, ["D1_test_tampering: you edited the test"], remaining=2)
    assert "test_calc_interest.py:5" in prompt
    assert "Fix the implementation, not the tests" in prompt
    assert "Already tried and rejected" in prompt


def test_every_iteration_is_traced(repo, monkeypatch):
    fake = fake_codex([(cheat, "All tests pass.")])
    monkeypatch.setattr(loop_module, "run_codex", fake)
    loop_module.drive(repo, max_iterations=2)
    trace = repo / ".pinocchio" / "loop-trace.jsonl"
    assert trace.is_file()
    assert len(trace.read_text(encoding="utf-8").strip().splitlines()) >= 1
