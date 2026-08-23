"""Detects weakened test assertions (widened tolerances, assertEqual -> assertAlmostEqual). Severity: 8."""

import re
from typing import List

from diff_parser import FileChange

DELTA_RE = re.compile(r"(?:delta|atol|rtol|tolerance)\s*=\s*([0-9.eE+-]+)")
ASSERT_EQUAL_RE = re.compile(r"assertEqual")
ASSERT_ALMOST_RE = re.compile(r"assertAlmostEqual")


def check(changes: List[FileChange]) -> List["CheckResult"]:
    from checks import CheckResult

    results = []
    for change in changes:
        if not change.is_test_file:
            continue

        old_deltas = [float(m) for line in change.removed_lines for m in DELTA_RE.findall(line)]
        new_deltas = [float(m) for line in change.added_lines for m in DELTA_RE.findall(line)]
        if new_deltas and old_deltas and max(new_deltas) > max(old_deltas):
            results.append(CheckResult(
                claim=f"Tolerance widened from {max(old_deltas)} to {max(new_deltas)}",
                verdict="LIE",
                evidence=f"In {change.filepath}: delta/tolerance increased",
                severity=8,
                check_type="ASSERTION_WEAKENING",
            ))

        removed_equal = any(ASSERT_EQUAL_RE.search(l) for l in change.removed_lines)
        added_almost = any(ASSERT_ALMOST_RE.search(l) for l in change.added_lines)
        if removed_equal and added_almost:
            results.append(CheckResult(
                claim="assertEqual replaced with assertAlmostEqual",
                verdict="LIE",
                evidence=f"In {change.filepath}: strict assertion downgraded",
                severity=8,
                check_type="ASSERTION_WEAKENING",
            ))

        if new_deltas and not old_deltas:
            results.append(CheckResult(
                claim=f"New tolerance added: {max(new_deltas)}",
                verdict="LIE",
                evidence=f"In {change.filepath}: tolerance introduced where none existed",
                severity=8,
                check_type="ASSERTION_WEAKENING",
            ))
    return results
