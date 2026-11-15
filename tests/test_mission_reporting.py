"""Executable tests through the installed prove-it and brief-me entry points."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROVE = ROOT / "skills/prove-it/scripts/prove_it.py"
BRIEF = ROOT / "skills/brief-me/scripts/brief_me.py"


def mission_report():
    return {
        "mission_id": "test-mission-17",
        "source": {"repository": "example/repo", "branch": "feat/test", "revision": "abc123"},
        "tested_revision": "abc123",
        "original_acceptance": [
            {"id": "A1", "requirement": "Render actual mission values", "status": "verified", "evidence": ["observed output"]}
        ],
        "checks": [
            {"name": "Focused suite", "command": "python3 -m unittest", "status": "passed", "evidence": ["Ran 4 tests; OK"]}
        ],
        "failures": [],
        "unverified": [],
    }


class MissionReportingTests(unittest.TestCase):
    def invoke_gate(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mission.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            result = subprocess.run([sys.executable, str(PROVE), str(path)], text=True, capture_output=True)
            return result.returncode, json.loads(result.stdout)

    def test_production_gate_passes_exact_identity_and_complete_evidence(self):
        code, report = self.invoke_gate(mission_report())
        self.assertEqual(code, 0)
        self.assertEqual(report["verdict"], "PASS")
        self.assertEqual(report["source"]["revision"], report["tested_revision"])

    def test_revision_mismatch_or_failed_check_blocks_delivery(self):
        data = mission_report()
        data["tested_revision"] = "different"
        code, report = self.invoke_gate(data)
        self.assertEqual(code, 1)
        self.assertEqual(report["verdict"], "FAIL")
        self.assertTrue(report["failures"])

        data = mission_report()
        data["checks"][0]["status"] = "failed"
        code, report = self.invoke_gate(data)
        self.assertEqual(code, 1)
        self.assertEqual(report["verdict"], "FAIL")

    def test_missing_or_unverified_evidence_is_not_success(self):
        data = mission_report()
        data["original_acceptance"][0]["status"] = "unverified"
        data["unverified"] = ["UI replay not performed"]
        code, report = self.invoke_gate(data)
        self.assertEqual(code, 2)
        self.assertEqual(report["verdict"], "INSUFFICIENT EVIDENCE")

        data = mission_report()
        del data["checks"][0]["evidence"]
        code, report = self.invoke_gate(data)
        self.assertEqual(code, 2)
        self.assertTrue(report["issues"])

    def test_brief_cli_uses_gate_verdict_and_escapes_report_values(self):
        data = mission_report()
        data["mission_id"] = "<mission & evidence>"
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "mission.json"
            output_path = Path(directory) / "brief.html"
            input_path.write_text(json.dumps(data), encoding="utf-8")
            result = subprocess.run([sys.executable, str(BRIEF), str(input_path), "--output", str(output_path)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            html = output_path.read_text(encoding="utf-8")
        self.assertIn("PASS", html)
        self.assertIn("&lt;mission &amp; evidence&gt;", html)
        self.assertIn("var(--foreground)", html)
        self.assertIn("background:transparent", html)
        self.assertIn("@media(max-width:420px)", html)
        self.assertNotIn("<mission & evidence>", html)


if __name__ == "__main__":
    unittest.main()
