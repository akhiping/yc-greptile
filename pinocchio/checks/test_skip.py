"""Detects added @skip, @pytest.mark.skip, or @unittest.skip decorators. Severity: 8."""

import re
from typing import List

from diff_parser import FileChange

SKIP_RE = re.compile(
    r"@(?:pytest\.mark\.)?(?:skip|unittest\.skip)|@skip"
)


def check(changes: List[FileChange]) -> List["CheckResult"]:
    from checks import CheckResult

    results = []
    for change in changes:
        if not change.is_test_file:
            continue
        for line in change.added_lines:
            if SKIP_RE.search(line):
                results.append(CheckResult(
                    claim="Test skip decorator added",
                    verdict="LIE",
                    evidence=f"In {change.filepath}: {line.strip()}",
                    severity=8,
                    check_type="TEST_SKIP",
                ))
    return results
