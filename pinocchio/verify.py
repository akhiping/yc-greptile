"""Create contract-compatible Pinocchio reports from a repository snapshot."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .entail import EntailmentEngine, Evidence
from .greptile import run_review


def _git(repo: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise ValueError(f"git {' '.join(arguments)} failed: {detail}")
    return completed.stdout


def _read_evidence(path: Path | None) -> list[Evidence | Mapping[str, Any]]:
    if path is None:
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Evidence file is not valid JSON: {path}") from exc
    except OSError as exc:
        raise ValueError(f"Could not read evidence file {path}: {exc}") from exc
    if isinstance(payload, Mapping):
        payload = payload.get("evidence", payload.get("results", []))
    if not isinstance(payload, Sequence) or isinstance(payload, (str, bytes)):
        raise ValueError("Evidence file must contain an array of evidence objects.")
    return [item for item in payload if isinstance(item, (Evidence, Mapping))]


def _summary(results: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {"LIE": 0, "VERIFIED": 0, "UNCERTAIN": 0}
    for result in results:
        verdict = result.get("verdict")
        counts[verdict if verdict in counts else "UNCERTAIN"] += 1
    return {
        "total": len(results),
        "lies": counts["LIE"],
        "verified": counts["VERIFIED"],
        "uncertain": counts["UNCERTAIN"],
        "nose_length": sum(
            int(result.get("severity", 1))
            for result in results
            if result.get("verdict") == "LIE"
        ),
    }


def create_report(
    repo: Path | str,
    *,
    message: str,
    evidence_path: Path | str | None = None,
    output: Path | str,
    greptile_enabled: bool | None = None,
) -> Path:
    """Capture the repository and write a report for the supplied agent message."""

    target = Path(repo).expanduser().resolve()
    if not target.is_dir():
        raise ValueError(f"Target repository does not exist: {target}")
    if not isinstance(message, str) or not message.strip():
        raise ValueError("An agent message is required for verification.")

    diff = _git(target, "diff", "--no-ext-diff", "--binary", "HEAD")
    status = _git(target, "status", "--porcelain=v1", "--untracked-files=all")
    evidence = _read_evidence(Path(evidence_path).expanduser() if evidence_path else None)
    if not evidence:
        evidence = [
            Evidence(
                evidence=(
                    f"Git captured {len(diff.splitlines())} diff lines; "
                    f"working-tree status: {status.strip() or 'clean'}."
                ),
                check_type="git_diff",
            )
        ]

    results = EntailmentEngine().evaluate(message, evidence)
    review = run_review(target, enabled=greptile_enabled)
    results.extend(review.to_results())
    report: dict[str, Any] = {
        "results": results,
        "summary": _summary(results),
        "metadata": {
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "mode": "analyze",
            "target_repo": str(target),
            "git": {
                "head": _git(target, "rev-parse", "HEAD").strip(),
                "status": status,
                "has_changes": bool(diff),
            },
            "engine": {
                "claim_entailment": "deterministic-first",
                "greptile": review.status,
                **({"greptile_error": review.error} if review.error else {}),
            },
        },
    }
    destination = Path(output).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return destination
