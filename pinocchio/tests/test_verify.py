from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from pinocchio.verify import create_report


class VerifyCommandTest(unittest.TestCase):
    def test_create_report_captures_repository_and_unknown_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "-C", str(repo), "init"], check=True, capture_output=True)
            subprocess.run(
                ["git", "-C", str(repo), "config", "user.email", "test@example.com"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(repo), "config", "user.name", "Test User"],
                check=True,
            )
            (repo / "module.py").write_text("return 1\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "module.py"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-m", "initial"], check=True, capture_output=True)
            (repo / "module.py").write_text("return 2\n", encoding="utf-8")

            output = create_report(
                repo,
                message="I fixed the function. All tests pass.",
                output=root / "report.json",
                greptile_enabled=False,
            )
            report = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(report["metadata"]["engine"]["greptile"], "disabled")
        self.assertEqual(report["summary"]["total"], 2)
        self.assertTrue(any(result["verdict"] == "UNCERTAIN" for result in report["results"]))


if __name__ == "__main__":
    unittest.main()
