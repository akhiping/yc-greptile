"""
LLM entailment checker — verifies agent claims against actual diffs.

Uses OpenAI API (gpt-4o-mini) to determine if an agent's summary
is SUPPORTED, CONTRADICTED, or UNCERTAIN based on the git diff.
"""

import json
import os
from pathlib import Path
from typing import List

from openai import OpenAI

from checks import CheckResult

_SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "entailment_system.txt").read_text()
_VERDICT_MAP = {"SUPPORTED": "VERIFIED", "CONTRADICTED": "LIE", "UNCERTAIN": "UNCERTAIN"}


def verify_claims(claims: List[str], diff_text: str) -> List[CheckResult]:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    results = []
    for claim in claims:
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": f"Claim: {claim}\n\nGit Diff:\n{diff_text[:4000]}"},
                ],
                timeout=10,
            )
            data = json.loads(resp.choices[0].message.content)
            verdict = _VERDICT_MAP.get(data.get("verdict", ""), "UNCERTAIN")
            evidence = data.get("evidence", "No evidence provided")
        except Exception:
            verdict, evidence = "UNCERTAIN", "LLM verification failed or timed out"
        results.append(CheckResult(
            claim=claim,
            verdict=verdict,
            evidence=evidence,
            severity=5 if verdict == "LIE" else 0,
            check_type="LLM_ENTAILMENT",
        ))
    return results
