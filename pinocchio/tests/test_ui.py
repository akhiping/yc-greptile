from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path

from pinocchio.ui import load_report, render_terminal
from pinocchio.web import dashboard_html


REPORT = {
    "results": [
        {
            "claim": "All tests pass",
            "verdict": "LIE",
            "evidence": "The test file changed instead of the function.",
            "severity": 8,
            "check_type": "D1_test_tampering",
        }
    ],
    "summary": {"total": 1, "lies": 1, "verified": 0, "uncertain": 0, "nose_length": 8},
    "metadata": {
        "captured_at": "2026-08-23T00:00:00+00:00",
        "mode": "analyze",
        "target_repo": "/tmp/demo",
        "git": {},
        "engine": {},
    },
}


class TerminalUiTest(unittest.TestCase):
    def test_render_contains_summary_and_evidence(self) -> None:
        output = io.StringIO()
        render_terminal(REPORT, output, color=False)
        rendered = output.getvalue()
        self.assertIn("1 checks", rendered)
        self.assertIn("1 lies", rendered)
        self.assertIn("All tests pass", rendered)
        self.assertIn("The test file changed", rendered)

    def test_load_report_rejects_missing_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text(json.dumps({"results": []}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing required field"):
                load_report(path)


class BrowserUiTest(unittest.TestCase):
    def test_dashboard_escapes_script_breakout_data(self) -> None:
        report = {**REPORT, "metadata": {**REPORT["metadata"], "target_repo": "</script><script>alert(1)</script>"}}
        html = dashboard_html(report)
        self.assertNotIn("</script><script>alert(1)</script>", html)
        self.assertIn("Trust, but verify.", html)
        self.assertIn("Independent evidence", html)


if __name__ == "__main__":
    unittest.main()
