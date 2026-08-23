"""
Deterministic verification checks — Layer 1 of Pinocchio.

Each check module exports: check(changes: List[FileChange]) -> List[CheckResult]
"""

from dataclasses import dataclass
from typing import List, Literal

from diff_parser import FileChange

from checks.test_deletion import check as check_test_deletion
from checks.assertion_weakening import check as check_assertion_weakening
from checks.hardcoded_values import check as check_hardcoded_values
from checks.test_skip import check as check_test_skip
from checks.mock_injection import check as check_mock_injection


@dataclass
class CheckResult:
    claim: str
    verdict: Literal["LIE", "VERIFIED", "UNCERTAIN"]
    evidence: str
    severity: int
    check_type: str


ALL_CHECKS = [
    check_test_deletion,
    check_assertion_weakening,
    check_hardcoded_values,
    check_test_skip,
    check_mock_injection,
]


def run_all_checks(changes: List[FileChange]) -> List[CheckResult]:
    results = []
    for check_fn in ALL_CHECKS:
        results.extend(check_fn(changes))
    return results
