#!/usr/bin/env python3
"""Render a Pinocchio verification report — static or live animated."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Mapping, TextIO

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

try:
    from pinocchio import CONTRACT_PATH, PinocchioError, validate_report
except ImportError:
    from pinocchio.pinocchio import CONTRACT_PATH, PinocchioError, validate_report


VERDICT_STYLE = {"LIE": "bold red", "VERIFIED": "bold green", "UNCERTAIN": "bold yellow"}
NOSE_THRESHOLDS = [(10, "green"), (30, "yellow"), (999, "red")]


def _nose_color(length: int) -> str:
    for threshold, color in NOSE_THRESHOLDS:
        if length < threshold:
            return color
    return "red"


def _build_display(
    results: list[dict[str, Any]],
    nose_length: int,
    total: int,
    verified: int,
    lies: int,
    uncertain: int,
    phase: str = "",
    memory: dict[str, Any] | None = None,
) -> Table:
    grid = Table.grid(padding=(0, 0))
    grid.add_column()

    color = _nose_color(nose_length)
    nose_bar = "═" * nose_length
    nose_text = Text()
    nose_text.append("  NOSE  ", style="bold")
    nose_text.append(f"({nose_bar}▶", style=color)
    nose_text.append(f"  length {nose_length} cm", style=f"bold {color}")

    header = Text()
    header.append("  🤥 PINOCCHIO", style="bold white")
    header.append("  — Trust, but verify.", style="dim")
    if phase:
        header.append(f"  [{phase}]", style="bold cyan")
    grid.add_row(header)
    grid.add_row(Text(""))
    grid.add_row(nose_text)
    grid.add_row(Text(""))

    counts = Text()
    counts.append("  ")
    counts.append(f"✓ {verified}", style="bold green")
    counts.append("  verified   ")
    counts.append(f"✗ {lies}", style="bold red")
    counts.append("  lies   ")
    counts.append(f"? {uncertain}", style="bold yellow")
    counts.append("  uncertain   ")
    counts.append(f"({total} total)", style="dim")
    grid.add_row(counts)
    grid.add_row(Text(""))

    for r in results:
        verdict = r["verdict"]
        style = VERDICT_STYLE.get(verdict, "")
        icon = {"LIE": "✗", "VERIFIED": "✓", "UNCERTAIN": "?"}.get(verdict, " ")
        line = Text()
        line.append(f"  {icon} ", style=style)
        line.append(f"[{verdict}]", style=style)
        line.append(f" sev {r['severity']}/10  ", style="dim")
        line.append(r["claim"])
        grid.add_row(line)

        detail = Text()
        detail.append(f"    {r['check_type']}: ", style="dim")
        detail.append(r["evidence"], style="dim italic")
        grid.add_row(detail)
        grid.add_row(Text(""))

    if memory:
        grid.add_row(Text("  ── Cricket Memory ──", style="bold magenta"))
        prior = memory.get("prior_flags", 0)
        patterns = memory.get("known_patterns", [])
        files = memory.get("watch_files", [])
        mem_line = Text()
        mem_line.append(f"  {prior} prior sessions", style="magenta")
        if patterns:
            mem_line.append(f"  |  known patterns: {', '.join(patterns)}", style="dim")
        grid.add_row(mem_line)
        if files:
            watch = Text()
            watch.append(f"  watch files: {', '.join(files[:5])}", style="dim")
            grid.add_row(watch)
        grid.add_row(Text(""))

    return grid


class NoseDisplay:
    """Live animated terminal display — nose grows as lies are found."""

    def __init__(self, console: Console | None = None):
        self.console = console or Console()
        self.results: list[dict[str, Any]] = []
        self.nose_length = 0
        self.verified = 0
        self.lies = 0
        self.uncertain = 0
        self.phase = ""
        self.memory: dict[str, Any] | None = None
        self._live: Live | None = None

    def __enter__(self) -> "NoseDisplay":
        self._live = Live(
            self._render(),
            console=self.console,
            refresh_per_second=12,
            transient=False,
        )
        self._live.__enter__()
        return self

    def __exit__(self, *args: Any) -> None:
        if self._live:
            self._live.__exit__(*args)

    def set_memory(self, memory: dict[str, Any]) -> None:
        self.memory = memory
        self._refresh()

    def _render(self) -> Panel:
        grid = _build_display(
            self.results, self.nose_length,
            len(self.results), self.verified, self.lies, self.uncertain,
            self.phase, self.memory,
        )
        border = _nose_color(self.nose_length)
        return Panel(grid, border_style=border, padding=(1, 2))

    def _refresh(self) -> None:
        if self._live:
            self._live.update(self._render())

    def set_phase(self, phase: str) -> None:
        self.phase = phase
        self._refresh()

    def new_attempt(self) -> None:
        """Clear results for a new attempt. Nose length carries over."""
        self.results = []
        self.verified = 0
        self.lies = 0
        self.uncertain = 0
        self._refresh()

    def add_result(self, result: dict[str, Any], animate: bool = True) -> None:
        self.results.append(result)
        verdict = result["verdict"]
        if verdict == "LIE":
            self.lies += 1
            if animate:
                target = self.nose_length + result["severity"]
                while self.nose_length < target:
                    self.nose_length += 1
                    self._refresh()
                    time.sleep(0.06)
            else:
                self.nose_length += result["severity"]
        elif verdict == "VERIFIED":
            self.verified += 1
            if animate and self.nose_length > 0:
                shrink = min(result["severity"], self.nose_length)
                target = self.nose_length - shrink
                while self.nose_length > target:
                    self.nose_length -= 1
                    self._refresh()
                    time.sleep(0.06)
            else:
                self.nose_length = max(0, self.nose_length - result["severity"])
        else:
            self.uncertain += 1
        self._refresh()

    def add_results_animated(self, results: list[dict[str, Any]], delay: float = 0.8) -> None:
        for r in results:
            time.sleep(delay)
            self.add_result(r)


def render(report: Mapping[str, Any], stream: TextIO = sys.stdout, color: bool = False) -> None:
    """Static render for non-interactive contexts (CI, pipes, --no-color)."""
    validate_report(report, CONTRACT_PATH)
    summary = report["summary"]
    nose = "=" * summary["nose_length"]
    print("PINOCCHIO  Trust, but verify.", file=stream)
    print(f"Nose: ({nose}>  length {summary['nose_length']}", file=stream)
    print(
        f"Results: {summary['verified']} verified | {summary['lies']} lies | "
        f"{summary['uncertain']} uncertain",
        file=stream,
    )
    print("", file=stream)
    for result in report["results"]:
        verdict = result["verdict"]
        label = f"[{verdict}]"
        if color:
            codes = {"LIE": "\033[31m", "VERIFIED": "\033[32m", "UNCERTAIN": "\033[33m"}
            label = f"{codes.get(verdict, '')}{label}\033[0m"
        print(f"{label} severity {result['severity']}/10  {result['claim']}", file=stream)
        print(f"  {result['check_type']}: {result['evidence']}", file=stream)


def render_live(report: Mapping[str, Any]) -> None:
    """Animated render — nose grows/shrinks as results appear."""
    validate_report(report, CONTRACT_PATH)
    console = Console()
    with NoseDisplay(console) as display:
        display.set_phase("Scanning")
        time.sleep(0.5)
        display.set_phase("Running detectors")
        display.add_results_animated(report["results"], delay=1.0)
        display.set_phase("Done")
        time.sleep(1.0)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="Report generated by pinocchio.py")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    parser.add_argument("--live", action="store_true", help="Animated nose display")
    args = parser.parse_args(argv)
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
        if args.live:
            render_live(report)
        else:
            render(report, color=not args.no_color and sys.stdout.isatty())
    except (OSError, json.JSONDecodeError, PinocchioError) as exc:
        print(f"Nose UI: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
