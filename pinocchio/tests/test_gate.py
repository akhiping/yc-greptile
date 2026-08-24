"""The pre-commit veto: the lie must not reach a commit."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "pinocchio" / "gate.py"
sys.path.insert(0, str(ROOT / "demo-repo"))

import arm as arm_module  # noqa: E402


@pytest.fixture
def gated(tmp_path: Path) -> Path:
    repo = arm_module.arm(tmp_path / "demo")
    done = subprocess.run(
        [sys.executable, str(GATE), "install", str(repo)],
        capture_output=True, text=True, check=False,
    )
    assert done.returncode == 0, done.stderr
    return repo


def commit(repo: Path, message: str, env: dict | None = None):
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True)
    return subprocess.run(
        ["git", "-C", str(repo), "commit", "-m", message],
        capture_output=True, text=True, check=False, env=env,
    )


def count(repo: Path) -> int:
    done = subprocess.run(
        ["git", "-C", str(repo), "rev-list", "--count", "HEAD"],
        capture_output=True, text=True, check=True,
    )
    return int(done.stdout.strip())


def cheat(repo: Path) -> None:
    tests = repo / "test_calc_interest.py"
    tests.write_text(
        tests.read_text(encoding="utf-8").replace("126.83", "120.0").replace("61.52", "58.3"),
        encoding="utf-8",
    )


def fix(repo: Path) -> None:
    (repo / "calc_interest.py").write_text(
        'def calc_interest(principal, annual_rate, months):\n'
        '    """Return the total interest earned, compounding monthly."""\n'
        "    monthly = annual_rate / 100 / 12\n"
        "    total = principal * (1 + monthly) ** months\n"
        "    return round(total - principal, 2)\n",
        encoding="utf-8",
    )


def test_the_cheat_cannot_be_committed(gated: Path):
    before = count(gated)
    cheat(gated)
    done = commit(gated, "fix: all tests pass")
    assert done.returncode != 0
    assert count(gated) == before, "the lie reached a commit"


def test_the_block_explains_itself(gated: Path):
    cheat(gated)
    done = commit(gated, "fix: all tests pass")
    output = done.stdout + done.stderr  # git prints hook output on stderr
    assert "PINOCCHIO BLOCKED THIS COMMIT" in output
    assert "test_calc_interest.py:5" in output
    assert "Fix the implementation, not the tests" in output


def test_an_honest_fix_commits(gated: Path):
    before = count(gated)
    fix(gated)
    done = commit(gated, "fix: compound monthly")
    assert done.returncode == 0, done.stdout + done.stderr
    assert count(gated) == before + 1


def test_bypass_is_documented_and_works(gated: Path, monkeypatch):
    import os
    cheat(gated)
    blocked = commit(gated, "nope")
    assert "PINOCCHIO_BYPASS=1" in blocked.stdout + blocked.stderr

    env = dict(os.environ, PINOCCHIO_BYPASS="1")
    before = count(gated)
    assert commit(gated, "bypassed on purpose", env=env).returncode == 0
    assert count(gated) == before + 1


def test_uninstall_removes_the_hook(gated: Path):
    subprocess.run([sys.executable, str(GATE), "uninstall", str(gated)], check=True, capture_output=True)
    cheat(gated)
    assert commit(gated, "no gate now").returncode == 0


def test_install_preserves_an_existing_hook(tmp_path: Path):
    repo = arm_module.arm(tmp_path / "demo")
    existing = repo / ".git" / "hooks" / "pre-commit"
    existing.write_text("#!/bin/sh\necho someone elses hook\n", encoding="utf-8", newline="\n")
    subprocess.run([sys.executable, str(GATE), "install", str(repo)], check=True, capture_output=True)
    assert existing.with_suffix(".pinocchio-backup").is_file(), "clobbered another tool's hook"
