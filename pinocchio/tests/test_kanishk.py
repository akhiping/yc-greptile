from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pinocchio.entail import EntailmentEngine, extract_claims_with_status
from pinocchio.greptile import parse_review, run_review


class FakeCompletions:
    def __init__(self, *responses: object) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        if not self.responses:
            raise RuntimeError("unexpected model call")
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


class FakeClient:
    def __init__(self, *responses: object) -> None:
        self.chat = type("Chat", (), {"completions": FakeCompletions(*responses)})()


class KanishkEntailmentTest(unittest.TestCase):
    def test_extracts_and_caches_claims(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory) / "claims.json"
            client = FakeClient({"choices": [{"message": {"content": '{"claims": [{"claim": "All tests pass"}]}'}}]})
            extracted = extract_claims_with_status("All tests pass.", client=client, cache_path=cache)
            self.assertEqual(extracted.claims, ("All tests pass",))
            self.assertEqual(extracted.source, "openai")
            self.assertTrue(cache.is_file())

            unavailable = FakeClient(RuntimeError("offline"))
            cached = extract_claims_with_status("All tests pass.", client=unavailable, cache_path=cache)
            self.assertEqual(cached.claims, ("All tests pass",))
            self.assertEqual(cached.source, "cache")

    def test_deterministic_finding_is_not_sent_for_adjudication(self) -> None:
        response = {"choices": [{"message": {"content": '{"claims": [{"claim": "I fixed the function"}]}'}}]}
        client = FakeClient(response)
        with tempfile.TemporaryDirectory() as directory:
            results = EntailmentEngine(
                client=client, cache_path=Path(directory) / "claims.json"
            ).evaluate(
                "I fixed the function.",
                [
                    {
                        "claim": "I fixed the function",
                        "verdict": "LIE",
                        "evidence": "[ledger #3] only the test changed",
                        "severity": 8,
                        "check_type": "D1_test_tampering",
                    }
                ],
            )
        self.assertEqual(results[0]["verdict"], "LIE")
        self.assertEqual(len(client.chat.completions.calls), 1)

    def test_model_result_without_receipt_is_uncertain(self) -> None:
        extraction = {"choices": [{"message": {"content": '{"claims": [{"claim": "The fix is correct"}]}'}}]}
        adjudication = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "results": [
                                    {
                                        "claim": "The fix is correct",
                                        "verdict": "VERIFIED",
                                        "evidence": "The code looks good",
                                        "severity": 1,
                                        "check_type": "entailment",
                                    }
                                ]
                            }
                        )
                    }
                }
            ]
        }
        client = FakeClient(extraction, adjudication)
        with tempfile.TemporaryDirectory() as directory:
            results = EntailmentEngine(
                client=client, cache_path=Path(directory) / "claims.json"
            ).evaluate("The fix is correct.", [])
        self.assertEqual(results[0]["verdict"], "UNCERTAIN")


class GreptileTest(unittest.TestCase):
    def test_security_string_is_parsed_as_false_when_false(self) -> None:
        review = parse_review(
            {
                "summary": "review",
                "confidence": 4,
                "comments": [
                    {
                        "path": "module.py",
                        "body": "Use the repository type annotations.",
                        "severity": "P2",
                        "securityIssue": "false",
                    }
                ],
            }
        )
        self.assertFalse(review.should_block)
        self.assertEqual(review.to_results()[0]["severity"], 5)

    def test_disabled_review_never_runs_cli(self) -> None:
        with patch("pinocchio.greptile.subprocess.run") as run:
            review = run_review("/tmp", enabled=False)
        self.assertEqual(review.status, "disabled")
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
