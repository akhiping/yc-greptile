"""Detects mock.patch on core business functions (not external services). Severity: 6."""

import re
from typing import List

from diff_parser import FileChange

PATCH_RE = re.compile(r"(?:mock\.patch|@patch)\(['\"](.+?)['\"]\)")
EXTERNAL_MARKERS = {"requests", "http", "smtp", "redis", "boto", "s3", "api", "socket", "urllib"}


def check(changes: List[FileChange]) -> List["CheckResult"]:
    from checks import CheckResult

    results = []
    for change in changes:
        for line in change.added_lines:
            match = PATCH_RE.search(line)
            if not match:
                continue
            target = match.group(1).lower()
            if any(ext in target for ext in EXTERNAL_MARKERS):
                continue
            results.append(CheckResult(
                claim=f"Mock injected on non-external function: {match.group(1)}",
                verdict="LIE",
                evidence=f"In {change.filepath}: {line.strip()}",
                severity=6,
                check_type="MOCK_INJECTION",
            ))
    return results
