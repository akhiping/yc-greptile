from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PINOCCHIO_DIR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("pinocchio_cli", PINOCCHIO_DIR / "pinocchio.py")
assert SPEC and SPEC.loader
pinocchio = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = pinocchio
SPEC.loader.exec_module(pinocchio)


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


class PinocchioTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        git(self.repo, "init")
        git(self.repo, "config", "user.email", "test@example.com")
        git(self.repo, "config", "user.name", "Test User")
        (self.repo / "module.py").write_text("def add(left, right):\n    return left + right\n")
        git(self.repo, "add", "module.py")
        git(self.repo, "commit", "-m", "initial")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_analyze_captures_and_validates_diff(self) -> None:
        (self.repo / "module.py").write_text("def add(left, right):\n    return left - right\n")
        output = self.root / "report.json"
        artifacts = self.root / "artifacts"

        result = pinocchio.analyze(self.repo, output, artifacts, None)

        self.assertEqual(result, output.resolve())
        report = json.loads(output.read_text())
        pinocchio.validate_report(report)
        self.assertEqual(report["metadata"]["mode"], "analyze")
        self.assertIn("return left - right", Path(report["metadata"]["git"]["diff_path"]).read_text())
        self.assertEqual(report["results"][0]["verdict"], "UNCERTAIN")

    def test_demo_without_codex_restores_clean_repository(self) -> None:
        output = self.root / "report.json"
        artifacts = self.root / "artifacts"
        original_which = pinocchio.shutil.which
        pinocchio.shutil.which = lambda _: None
        try:
            result = pinocchio.run_demo(
                self.repo,
                output,
                artifacts,
                None,
                "do nothing",
                5,
            )
        finally:
            pinocchio.shutil.which = original_which

        self.assertEqual(result, output.resolve())
        report = json.loads(output.read_text())
        self.assertEqual(report["metadata"]["codex"]["error"], "Codex CLI was not found on PATH.")
        self.assertTrue(report["metadata"]["codex"]["restored"])
        self.assertEqual(git_status(self.repo), "")


def git_status(repo: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain=v1", "--ignored=matching"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


class NoseUiTest(unittest.TestCase):
    def test_render_uses_lie_severity_for_nose(self) -> None:
        report = {
            "results": [
                {
                    "claim": "The test calls the function.",
                    "verdict": "LIE",
                    "evidence": "The test still passed after the function was replaced.",
                    "severity": 7,
                    "check_type": "mutation",
                }
            ],
            "summary": {"total": 1, "lies": 1, "verified": 0, "uncertain": 0, "nose_length": 7},
            "metadata": {
                "captured_at": "2026-08-23T00:00:00+00:00",
                "mode": "analyze",
                "target_repo": "/tmp/repo",
                "git": {},
                "engine": {},
            },
        }
        nose_spec = importlib.util.spec_from_file_location("nose_ui", PINOCCHIO_DIR / "nose_ui.py")
        assert nose_spec and nose_spec.loader
        nose_ui = importlib.util.module_from_spec(nose_spec)
        sys.path.insert(0, str(PINOCCHIO_DIR))
        self.addCleanup(sys.path.pop, 0)
        sys.modules[nose_spec.name] = nose_ui
        nose_spec.loader.exec_module(nose_ui)
        output = io.StringIO()

        nose_ui.render(report, output, color=False)

        self.assertIn("Nose: (=======>  length 7", output.getvalue())
        self.assertIn("[LIE] severity 7/10", output.getvalue())


if __name__ == "__main__":
    unittest.main()
