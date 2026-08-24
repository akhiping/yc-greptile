#!/usr/bin/env python3
"""The veto, as a git pre-commit hook.

Codex 0.137.0 does not fire `Stop` or `PostToolUse` from any hook config
location we could find (see docs/HOOKS.md), so the agent's own stop condition
is not currently available to block on. A pre-commit hook is the same veto
wired to a trigger we fully control: the lie does not reach a commit.

    python pinocchio/gate.py install PATH   # write .git/hooks/pre-commit
    python pinocchio/gate.py check  PATH    # run once, exit 1 if lying
    python pinocchio/gate.py uninstall PATH

Exit codes: 0 clean or released, 1 blocked.

`PINOCCHIO_BYPASS=1 git commit ...` overrides it, the same way `--no-verify`
does. A gate nobody can get past gets deleted; a gate with a documented
override gets kept.
"""

from __future__ import annotations

import argparse
import os
import stat
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
BOLD = "\033[1m"
RESET = "\033[0m"

MARKER = "pinocchio-gate"


def _color(enabled: bool):
    if enabled:
        return RED, YELLOW, GREEN, BOLD, RESET
    return "", "", "", "", ""


def _repo_root(path: Path) -> Path:
    done = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=False,
    )
    if done.returncode:
        raise SystemExit(f"Not a git repository: {path}")
    return Path(done.stdout.strip())


# ---------------------------------------------------------------------------

def check(repo: Path, color: bool = True) -> int:
    import detectors

    red, yellow, green, bold, reset = _color(color)
    session: dict = {}
    ledger = repo / ".pinocchio" / "ledger.jsonl"
    if ledger.is_file():
        session["ledger_path"] = str(ledger)
    message = os.environ.get("PINOCCHIO_AGENT_MESSAGE", "")
    if message:
        session["agent_message"] = message

    results = detectors.run(repo, session=session)["results"]
    lies = [r for r in results if r["verdict"] == "LIE"]
    nose = sum(r["severity"] for r in lies)

    if not lies:
        print(f"{green}pinocchio: nothing contradicted. Nose 0.{reset}")
        return 0

    print()
    print(f"{red}{bold}  PINOCCHIO BLOCKED THIS COMMIT.{reset}")
    print(f"{red}  Nose length {nose}.{reset}")
    print()
    for index, lie in enumerate(lies, start=1):
        print(f"  {red}{index}. [{lie['check_type']}  severity {lie['severity']}/10]{reset}")
        print(f"     You implied: {lie['claim']}")
        print(f"     Evidence:    {lie['evidence']}")
        print()
    print(f"  {bold}Fix the implementation, not the tests.{reset}")
    print("  Restore the original assertions and change the source so they pass.")
    print()
    print(f"  {yellow}To commit anyway: PINOCCHIO_BYPASS=1 git commit ...{reset}")
    print()
    return 1


# ---------------------------------------------------------------------------

def _script(repo: Path) -> str:
    gate = (HERE / "gate.py").resolve()
    python = sys.executable
    return f"""#!/bin/sh
# {MARKER} -- installed by pinocchio/gate.py, safe to delete
[ -n "$PINOCCHIO_BYPASS" ] && exit 0
"{python}" "{gate}" check "{repo}"
""".replace("\\", "/")


def install(repo: Path) -> int:
    hooks = repo / ".git" / "hooks"
    if not hooks.is_dir():
        hooks.mkdir(parents=True, exist_ok=True)
    target = hooks / "pre-commit"

    if target.exists() and MARKER not in target.read_text(encoding="utf-8", errors="replace"):
        backup = target.with_suffix(".pinocchio-backup")
        target.replace(backup)
        print(f"Existing pre-commit hook moved to {backup}")

    target.write_text(_script(repo), encoding="utf-8", newline="\n")
    target.chmod(target.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    print(f"Installed: {target}")
    print("The next `git commit` in this repository runs the detectors.")
    return 0


def uninstall(repo: Path) -> int:
    target = repo / ".git" / "hooks" / "pre-commit"
    if not target.exists():
        print("No pre-commit hook installed.")
        return 0
    if MARKER not in target.read_text(encoding="utf-8", errors="replace"):
        print("The pre-commit hook was not installed by pinocchio; leaving it alone.")
        return 0
    target.unlink()
    backup = target.with_suffix(".pinocchio-backup")
    if backup.exists():
        backup.replace(target)
        print(f"Restored the previous hook from {backup.name}")
    else:
        print(f"Removed: {target}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["install", "check", "uninstall"])
    parser.add_argument("repo", nargs="?", type=Path, default=Path("."))
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args(argv)

    repo = _repo_root(args.repo.expanduser().resolve())
    if args.action == "install":
        return install(repo)
    if args.action == "uninstall":
        return uninstall(repo)
    return check(repo, color=not args.no_color and sys.stdout.isatty())


if __name__ == "__main__":
    raise SystemExit(main())
