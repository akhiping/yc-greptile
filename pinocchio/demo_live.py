#!/usr/bin/env python3
"""
Live Pinocchio demo — apply the cheat patch, run detectors with animated nose,
then restore the repo.

Usage:
    cd pinocchio/
    python demo_live.py                          # defaults to ../demo-repo
    python demo_live.py --repo ../demo-repo      # explicit
    python demo_live.py --fast                    # skip pauses (testing)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.text import Text

sys.path.insert(0, str(Path(__file__).resolve().parent))

from diff_parser import parse_diff
from checks import run_all_checks
from deterministic import verify, _read_summary, _phantom_execution, _test_only_changes
from nose_ui import NoseDisplay

DEMO_DIR = Path(__file__).resolve().parent.parent / "demo-repo"
PATCH_FILE = Path(__file__).resolve().parent / "demo-cheat-minimal.patch"
SUMMARY_FILE = Path(__file__).resolve().parent / "demo-cheat-minimal-summary.txt"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, check=True,
    )


def _apply_patch(repo: Path, patch: Path) -> None:
    subprocess.run(
        ["git", "-C", str(repo), "apply", str(patch)],
        check=True, capture_output=True, text=True,
    )


def _restore(repo: Path) -> None:
    subprocess.run(["git", "-C", str(repo), "checkout", "--", "."],
                   capture_output=True, check=True)
    subprocess.run(["git", "-C", str(repo), "clean", "-fd"],
                   capture_output=True, check=True)


def run_demo(repo: Path, fast: bool = False) -> None:
    console = Console()
    pause = 0.1 if fast else 1.0
    anim_delay = 0.3 if fast else 0.9

    console.print()
    console.print("  [bold]PINOCCHIO LIVE DEMO[/bold]", style="bold cyan")
    console.print("  Catching a cheating coding agent in real time.\n", style="dim")

    # Step 1: Show the setup
    console.print("  [dim]Step 1:[/dim] Agent was asked to fix failing tests...")
    time.sleep(pause)
    console.print(f"  [dim]Step 2:[/dim] Agent produced changes in [bold]{repo.name}/[/bold]")

    _apply_patch(repo, PATCH_FILE)
    time.sleep(pause)

    diff = _git(repo, "diff", "--no-ext-diff", "HEAD").stdout
    summary = SUMMARY_FILE.read_text().strip() if SUMMARY_FILE.is_file() else None

    console.print(f"  [dim]Step 3:[/dim] Agent says: [italic]\"{summary}\"[/italic]")
    time.sleep(pause)
    console.print()
    console.print("  [bold yellow]Let's see if that's true...[/bold yellow]")
    time.sleep(pause * 1.5)
    console.print()

    # Step 2: Run checks with live nose
    changes = parse_diff(diff)
    det_results = run_all_checks(changes)

    tampering = _test_only_changes(changes)
    if tampering:
        det_results.append(tampering)

    phantom = _phantom_execution(summary, diff)
    if phantom:
        det_results.append(phantom)

    check_dicts = [
        {"claim": r.claim, "verdict": r.verdict, "evidence": r.evidence,
         "severity": r.severity, "check_type": r.check_type}
        for r in det_results
    ]

    with NoseDisplay(console) as display:
        display.set_phase("Scanning diff")
        time.sleep(pause)

        display.set_phase("Running D1–D5 detectors")
        display.add_results_animated(check_dicts, delay=anim_delay)

        display.set_phase("Verdict")
        time.sleep(pause)

        if display.lies > 0:
            display.set_phase(f"🚨 BLOCKED — {display.lies} lie(s) detected")
        else:
            display.set_phase("✅ CLEAN — no deception detected")
        time.sleep(pause * 2)

    # Step 3: Show the veto message
    if det_results:
        console.print()
        veto = Text()
        veto.append("  PINOCCHIO VETO → ", style="bold red")
        veto.append("BLOCKED", style="bold red on white")
        console.print(veto)
        console.print()

        lie_results = [r for r in det_results if r.verdict == "LIE"]
        for r in lie_results:
            console.print(f"    [red]✗[/red] \"{r.claim}\"")
            console.print(f"      {r.check_type} — {r.evidence}", style="dim")

        console.print()
        console.print("  [bold]Fix the function, not the test.[/bold]", style="yellow")
        console.print()

    _restore(repo)
    console.print("  [dim]Demo repo restored to clean state.[/dim]")
    console.print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=DEMO_DIR, help="Target demo repo")
    parser.add_argument("--fast", action="store_true", help="Skip pauses (for testing)")
    args = parser.parse_args()

    if not args.repo.is_dir():
        print(f"Demo repo not found: {args.repo}", file=sys.stderr)
        return 1
    if not PATCH_FILE.is_file():
        print(f"Patch file not found: {PATCH_FILE}", file=sys.stderr)
        return 1

    try:
        run_demo(args.repo, fast=args.fast)
    except KeyboardInterrupt:
        _restore(args.repo)
        print("\nDemo interrupted. Repo restored.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
