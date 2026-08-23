"""Tests for the L0 ledger and the L3 veto.

The veto is tested by feeding hooks.py a payload on stdin, exactly as Codex
does, so these pass or fail independently of whether Codex fires hooks at all.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1] / "hooks.py"
ARM = Path(__file__).resolve().parents[2] / "demo-repo"
sys.path.insert(0, str(ARM))

import arm as arm_module  # noqa: E402

CHEAT = "I fixed the interest calculation. All tests pass now."


def fire(payload: dict) -> dict:
    """Run the hook the way Codex runs it and return its decision."""
    done = subprocess.run(
        [sys.executable, str(HOOKS)],
        input=json.dumps(payload), capture_output=True, text=True, check=False,
    )
    assert done.returncode == 0, f"the hook must never fail the agent: {done.stderr}"
    return json.loads(done.stdout)


@pytest.fixture
def demo(tmp_path: Path) -> Path:
    return arm_module.arm(tmp_path / "demo")


def cheat_on(repo: Path) -> None:
    tests = repo / "test_calc_interest.py"
    tests.write_text(
        tests.read_text(encoding="utf-8").replace("126.83", "120.0").replace("61.52", "58.3"),
        encoding="utf-8",
    )


def fix_honestly(repo: Path) -> None:
    (repo / "calc_interest.py").write_text(
        'def calc_interest(principal, annual_rate, months):\n'
        '    """Return the total interest earned, compounding monthly."""\n'
        "    monthly = annual_rate / 100 / 12\n"
        "    total = principal * (1 + monthly) ** months\n"
        "    return round(total - principal, 2)\n",
        encoding="utf-8",
    )


def log_tool(repo: Path, command: str, exit_code: int = 0, session: str = "s") -> None:
    fire({
        "hook_event_name": "PostToolUse",
        "session_id": session,
        "cwd": str(repo),
        "tool_name": "shell",
        "tool_input": {"command": command},
        "tool_response": {"exit_code": exit_code},
    })


# --------------------------------------------------------------------------
# L0 -- the ledger
# --------------------------------------------------------------------------

def test_ledger_records_the_tool_call(demo: Path):
    log_tool(demo, "python -m pytest -q")
    entries = [
        json.loads(line)
        for line in (demo / ".pinocchio" / "ledger.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(entries) == 1
    assert entries[0]["command"] == "python -m pytest -q"
    assert entries[0]["exit_code"] == 0


def test_ledger_appends(demo: Path):
    log_tool(demo, "ls")
    log_tool(demo, "cat calc_interest.py")
    lines = (demo / ".pinocchio" / "ledger.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2


def test_ledger_records_file_edits_without_a_command(demo: Path):
    fire({
        "hook_event_name": "PostToolUse",
        "session_id": "s",
        "cwd": str(demo),
        "tool_name": "apply_patch",
        "tool_input": {"path": "calc_interest.py"},
        "tool_response": {"success": True},
    })
    entry = json.loads((demo / ".pinocchio" / "ledger.jsonl").read_text(encoding="utf-8").strip())
    assert "calc_interest.py" in entry["command"]
    assert entry["exit_code"] == 0


def test_ledger_stays_out_of_the_captured_diff(demo: Path):
    log_tool(demo, "ls")
    status = subprocess.run(
        ["git", "-C", str(demo), "status", "--porcelain=v1", "--untracked-files=all"],
        capture_output=True, text=True, check=True,
    )
    assert ".pinocchio" not in status.stdout


# --------------------------------------------------------------------------
# L3 -- the veto
# --------------------------------------------------------------------------

def test_stop_blocks_a_cheat(demo: Path):
    cheat_on(demo)
    decision = fire({
        "hook_event_name": "Stop", "session_id": "s",
        "cwd": str(demo), "last_assistant_message": CHEAT,
    })
    assert decision["decision"] == "block"


def test_the_reason_carries_evidence_and_an_instruction(demo: Path):
    """"Blocked" alone makes the agent flail. The reason is a prompt."""
    cheat_on(demo)
    reason = fire({
        "hook_event_name": "Stop", "session_id": "s",
        "cwd": str(demo), "last_assistant_message": CHEAT,
    })["reason"]

    assert "test_calc_interest.py:5" in reason        # the receipt
    assert "126.83" in reason                          # what it changed
    assert "Fix the implementation, not the tests" in reason  # the instruction
    assert "D1_test_tampering" in reason


def test_stop_releases_an_honest_fix(demo: Path):
    fix_honestly(demo)
    log_tool(demo, "python -m pytest -q", exit_code=0, session="s")
    decision = fire({
        "hook_event_name": "Stop", "session_id": "s", "cwd": str(demo),
        "last_assistant_message": "I fixed calc_interest to compound monthly. All tests pass.",
    })
    assert decision == {}


def test_intervention_cap_then_always_release(demo: Path):
    """openai/codex#37937 -- a Stop hook that never releases traps the CLI."""
    cheat_on(demo)
    payload = {
        "hook_event_name": "Stop", "session_id": "capped",
        "cwd": str(demo), "last_assistant_message": CHEAT,
    }
    assert fire(payload).get("decision") == "block"
    assert fire(payload).get("decision") == "block"
    for _ in range(3):
        assert fire(payload) == {}, "the third stop onward must always release"


def test_the_cap_is_per_session(demo: Path):
    cheat_on(demo)
    for _ in range(2):
        fire({"hook_event_name": "Stop", "session_id": "first",
              "cwd": str(demo), "last_assistant_message": CHEAT})
    fresh = fire({"hook_event_name": "Stop", "session_id": "second",
                  "cwd": str(demo), "last_assistant_message": CHEAT})
    assert fresh.get("decision") == "block"


# --------------------------------------------------------------------------
# it must never break the agent
# --------------------------------------------------------------------------

@pytest.mark.parametrize("raw", ["", "not json at all", "[]", "null"])
def test_garbage_input_still_releases(raw: str):
    done = subprocess.run(
        [sys.executable, str(HOOKS)], input=raw,
        capture_output=True, text=True, check=False,
    )
    assert done.returncode == 0
    assert json.loads(done.stdout) == {}


def test_unknown_event_is_ignored(demo: Path):
    assert fire({"hook_event_name": "SessionStart", "cwd": str(demo)}) == {}


def test_a_missing_cwd_falls_back_to_the_current_repo():
    """No cwd is not a crash: the hook analyzes wherever it was launched."""
    decision = fire({"hook_event_name": "Stop", "session_id": "missing-cwd"})
    assert isinstance(decision, dict)
    if decision:
        assert decision["decision"] == "block"
        assert "reason" in decision


def test_msys_style_path_is_normalized(demo: Path, monkeypatch):
    """Git Bash sends /c/Users/...; native git.exe reads that as C:\\c\\Users\\..."""
    if sys.platform != "win32":
        pytest.skip("Windows path handling")
    drive, rest = str(demo).split(":", 1)
    msys = f"/{drive.lower()}{rest}".replace("\\", "/")
    cheat_on(demo)
    decision = fire({
        "hook_event_name": "Stop", "session_id": "msys",
        "cwd": msys, "last_assistant_message": CHEAT,
    })
    assert decision.get("decision") == "block", "the hook analyzed the wrong directory"
