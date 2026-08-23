"""Shared terminal presentation for Pinocchio verification reports."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping, TextIO


_VERDICT_STYLE = {
    "LIE": ("\033[31m", "✕"),
    "VERIFIED": ("\033[32m", "✓"),
    "UNCERTAIN": ("\033[33m", "?"),
}
_RESET = "\033[0m"


def load_report(path: Path | str) -> dict[str, Any]:
    """Load a report and reject malformed top-level data early."""

    report_path = Path(path).expanduser()
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Report is not valid JSON: {report_path}") from exc
    except OSError as exc:
        raise ValueError(f"Could not read report {report_path}: {exc}") from exc
    if not isinstance(report, dict):
        raise ValueError("Report must be a JSON object.")
    for field in ("results", "summary", "metadata"):
        if field not in report:
            raise ValueError(f"Report is missing required field {field!r}.")
    if not isinstance(report["results"], list) or not isinstance(report["summary"], Mapping):
        raise ValueError("Report results and summary have invalid shapes.")
    return report


def _styled(text: str, verdict: str, color: bool) -> str:
    style, _ = _VERDICT_STYLE.get(verdict, ("", "•"))
    return f"{style}{text}{_RESET}" if color and style else text


def _bar(value: int, maximum: int = 10, width: int = 10) -> str:
    filled = min(width, max(0, round(value / maximum * width))) if maximum else 0
    return "█" * filled + "░" * (width - filled)


def render_terminal(
    report: Mapping[str, Any],
    stream: TextIO = sys.stdout,
    *,
    color: bool = True,
    width: int = 76,
) -> None:
    """Render a report as a scannable, keyboard-friendly terminal summary."""

    summary = report["summary"]
    metadata = report["metadata"]
    nose_length = int(summary.get("nose_length", 0))
    target = str(metadata.get("target_repo", "unknown target"))
    mode = str(metadata.get("mode", "analyze")).upper()

    print("", file=stream)
    print(_styled("  PINOCCHIO", "VERIFIED", color) + "  /  TRUST REPORT", file=stream)
    print(f"  {target}  ·  {mode}", file=stream)
    print("  " + "─" * max(40, width - 2), file=stream)
    print(
        f"  {summary.get('total', 0)} checks   "
        f"{_styled(str(summary.get('lies', 0)) + ' lies', 'LIE', color)}   "
        f"{_styled(str(summary.get('verified', 0)) + ' verified', 'VERIFIED', color)}   "
        f"{_styled(str(summary.get('uncertain', 0)) + ' uncertain', 'UNCERTAIN', color)}",
        file=stream,
    )
    print(
        f"  Nose length  {_bar(nose_length)}  {nose_length}/10",
        file=stream,
    )
    print("", file=stream)

    results = report["results"]
    if not results:
        print("  No claims were captured. Nothing was silently treated as verified.", file=stream)
        return

    for index, result in enumerate(results, start=1):
        verdict = str(result.get("verdict", "UNCERTAIN"))
        _, icon = _VERDICT_STYLE.get(verdict, ("", "•"))
        label = _styled(f"{icon} {verdict}", verdict, color)
        claim = str(result.get("claim", "Untitled claim"))
        evidence = str(result.get("evidence", "No evidence supplied."))
        check_type = str(result.get("check_type", "check"))
        severity = int(result.get("severity", 1))
        print(f"  {index:02d}  {label:<24} {claim}", file=stream)
        print(f"      {check_type}  ·  severity {severity}/10", file=stream)
        print(f"      {evidence}", file=stream)
        if index != len(results):
            print("", file=stream)

    print("", file=stream)
    print("  Evidence is independent of the agent's final message.", file=stream)
