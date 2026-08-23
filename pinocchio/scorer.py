"""
Trust scorer — calculates nose length and trust score from check results.

nose_cm = sum of severity for each LIE detected.
trust_score = 100 - (nose_cm * 3), clamped to 0-100.
"""

from dataclasses import dataclass
from typing import List

from checks import CheckResult


@dataclass
class TrustScore:
    nose_cm: int
    trust_score: int
    total_claims: int
    verified: int
    lies: int
    uncertain: int


def calculate_score(results: List[CheckResult]) -> TrustScore:
    lies = [r for r in results if r.verdict == "LIE"]
    return TrustScore(
        nose_cm=sum(r.severity for r in lies),
        trust_score=max(0, 100 - sum(r.severity for r in lies) * 3),
        total_claims=len(results),
        verified=sum(1 for r in results if r.verdict == "VERIFIED"),
        lies=len(lies),
        uncertain=sum(1 for r in results if r.verdict == "UNCERTAIN"),
    )
