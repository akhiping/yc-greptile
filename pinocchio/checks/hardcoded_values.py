"""Detects hardcoded expected values in tests that bypass actual computation. Severity: 7."""

import re
from typing import List

from diff_parser import FileChange

EXPECTED_ASSIGN_RE = re.compile(r"expected\s*=\s*[0-9.]+")
DICT_GET_RE = re.compile(r"\.get\(\s*\(")
IF_RETURN_RE = re.compile(r"if\s+.+==\s*\(.+\)\s*:")


def check(changes: List[FileChange]) -> List["CheckResult"]:
    from checks import CheckResult

    results = []
    for change in changes:
        added = change.added_lines

        if change.is_test_file:
            for i, line in enumerate(added):
                if EXPECTED_ASSIGN_RE.search(line):
                    has_assert_next = (i + 1 < len(added) and "assert" in added[i + 1].lower())
                    if has_assert_next:
                        results.append(CheckResult(
                            claim="Hardcoded expected value before assertion",
                            verdict="LIE",
                            evidence=f"In {change.filepath}: {line.strip()}",
                            severity=7,
                            check_type="HARDCODED_VALUE",
                        ))

        for line in added:
            if DICT_GET_RE.search(line) or IF_RETURN_RE.search(line):
                results.append(CheckResult(
                    claim="Hardcoded return value for specific inputs",
                    verdict="LIE",
                    evidence=f"In {change.filepath}: {line.strip()}",
                    severity=7,
                    check_type="HARDCODED_VALUE",
                ))
    return results
