"""Detects deleted test functions in test files. Severity: 9."""

import re
from typing import List

from diff_parser import FileChange


def check(changes: List[FileChange]) -> List["CheckResult"]:
    from checks import CheckResult

    results = []
    for change in changes:
        if not change.is_test_file:
            continue
        for line in change.removed_lines:
            match = re.search(r"def (test_\w+)", line)
            if match:
                results.append(CheckResult(
                    claim=f"Test function '{match.group(1)}' was deleted",
                    verdict="LIE",
                    evidence=f"Removed from {change.filepath}: {line.strip()}",
                    severity=9,
                    check_type="TEST_DELETION",
                ))
    return results
