"""Optional Greptile review adapter.

Greptile is a second witness, not a prerequisite for local verification. The
adapter is disabled unless explicitly enabled and gates on parsed findings,
never on Greptile's process exit code.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


_SEVERITY = {"P0": 10, "P1": 8, "P2": 5, "P3": 2}


@dataclass(frozen=True)
class GreptileFinding:
    """One comment from ``greptile review --json``."""

    path: str
    body: str
    severity: str
    security_issue: bool = False
    start_line: int | None = None
    end_line: int | None = None
    category: str = "greptile"

    @property
    def should_block(self) -> bool:
        return self.security_issue or self.severity in {"P0", "P1"}

    @property
    def score(self) -> int:
        return max(_SEVERITY.get(self.severity, 1), 8 if self.security_issue else 1)

    def to_result(self) -> dict[str, Any]:
        location = self.path or "repository"
        if self.start_line is not None:
            location += f":{self.start_line}"
        security = " security issue" if self.security_issue else ""
        return {
            "claim": f"Greptile found no blocking issue in {location}",
            "verdict": "LIE",
            "evidence": f"{location} ({self.severity}{security}): {self.body}",
            "severity": self.score,
            "check_type": "greptile",
        }


@dataclass(frozen=True)
class GreptileReview:
    """Parsed review state, including additive failure states."""

    status: str
    findings: tuple[GreptileFinding, ...] = ()
    summary: str = ""
    confidence: int | None = None
    error: str | None = None

    @property
    def should_block(self) -> bool:
        return any(item.should_block for item in self.findings)

    def to_results(self) -> list[dict[str, Any]]:
        return [item.to_result() for item in self.findings]


def _integer(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return isinstance(value, str) and value.strip().lower() in {"1", "true", "yes", "on"}


def parse_review(payload: Mapping[str, Any]) -> GreptileReview:
    """Parse Greptile's JSON response without treating exit code as a verdict."""

    raw_comments = payload.get("comments", [])
    if not isinstance(raw_comments, Sequence) or isinstance(raw_comments, (str, bytes)):
        raise ValueError("Greptile response comments must be an array.")
    findings: list[GreptileFinding] = []
    for raw in raw_comments:
        if not isinstance(raw, Mapping):
            continue
        body = raw.get("body", "")
        if not isinstance(body, str) or not body.strip():
            continue
        severity = raw.get("severity", "P3")
        severity = severity.upper() if isinstance(severity, str) else "P3"
        findings.append(
            GreptileFinding(
                path=raw.get("path", "") if isinstance(raw.get("path", ""), str) else "",
                body=body.strip(),
                severity=severity,
                security_issue=_boolean(raw.get("securityIssue", False)),
                start_line=_integer(raw.get("startLine")),
                end_line=_integer(raw.get("endLine")),
                category=raw.get("category", "greptile") if isinstance(raw.get("category", "greptile"), str) else "greptile",
            )
        )
    confidence = _integer(payload.get("confidence"))
    return GreptileReview(
        status="completed",
        findings=tuple(findings),
        summary=payload.get("summary", "") if isinstance(payload.get("summary", ""), str) else "",
        confidence=confidence,
    )


def _decode_payload(stdout: str) -> Mapping[str, Any]:
    try:
        value = json.loads(stdout)
    except json.JSONDecodeError:
        start, end = stdout.find("{"), stdout.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("Greptile did not return a JSON object.")
        try:
            value = json.loads(stdout[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError("Greptile returned invalid JSON.") from exc
    if not isinstance(value, Mapping):
        raise ValueError("Greptile response must be a JSON object.")
    return value


def _enabled_from_environment() -> bool:
    return os.environ.get("PINOCCHIO_GREPTILE", "").strip().lower() in {"1", "true", "yes", "on"}


def run_review(
    repo: Path | str,
    *,
    enabled: bool | None = None,
    timeout: int = 90,
    command: Sequence[str] = ("greptile", "review", "--json"),
) -> GreptileReview:
    """Run an optional local Greptile review and return a non-blocking status."""

    if enabled is None:
        enabled = _enabled_from_environment()
    if not enabled:
        return GreptileReview(status="disabled")
    target = Path(repo).expanduser().resolve()
    if not target.is_dir():
        raise ValueError(f"Greptile target repository does not exist: {target}")
    if not command or any(not isinstance(part, str) or not part for part in command):
        raise ValueError("Greptile command must be a non-empty sequence of strings.")
    try:
        completed = subprocess.run(
            list(command),
            cwd=target,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        return GreptileReview(status="unavailable", error=f"Greptile CLI was not found: {exc}")
    except subprocess.TimeoutExpired:
        return GreptileReview(status="unavailable", error=f"Greptile review timed out after {timeout} seconds.")
    except OSError as exc:
        return GreptileReview(status="unavailable", error=f"Greptile could not run: {exc}")

    try:
        review = parse_review(_decode_payload(completed.stdout))
    except ValueError as exc:
        detail = completed.stderr.strip()
        if detail:
            exc = ValueError(f"{exc} {detail}")
        return GreptileReview(status="unavailable", error=str(exc))
    return review
