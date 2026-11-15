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
        self.assertNotIn('["', html)

    def test_brief_renders_independent_portfolio_missions_and_safe_links(self):
        data = {
            "portfolio": {
                "chief_summary": "One item active; one ready for review; one needs attention.",
                "missions": [
                    {"name": "API", "status": "active", "progress": "Endpoint implemented", "verification": "Tests pending", "pr_url": "https://github.com/example/repo/pull/7"},
                    {"name": "Docs", "status": "review-ready", "progress": "Guide updated", "verification": "Passed", "artifact_url": "artifacts/guide.html"},
                    {"name": "Deploy", "status": "attention", "progress": "Blocked on observed issue", "verification": "Failed", "pr_url": "javascript:alert(1)"},
                ],
            }
        }
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "portfolio.json"
            output_path = Path(directory) / "portfolio.html"
            input_path.write_text(json.dumps(data), encoding="utf-8")
            result = subprocess.run([sys.executable, str(BRIEF), str(input_path), "--output", str(output_path)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            page = output_path.read_text(encoding="utf-8")

        self.assertIn("One item active; one ready for review; one needs attention.", page)
        for value in ("Active", "Review-Ready", "Attention", "API", "Docs", "Deploy", "Endpoint implemented", "Guide updated", "Blocked on observed issue"):
            self.assertIn(value, page)
        self.assertIn('href="https://github.com/example/repo/pull/7"', page)
        self.assertIn('href="artifacts/guide.html"', page)
        self.assertNotIn('href="javascript:', page)

    def test_redirect_contract_preserves_the_active_assignment(self):
        contract = (ROOT / "skills/redirect/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("same assignment, owner, authority, and", contract)
        self.assertIn("Do not create a duplicate Coordinator", contract)


if __name__ == "__main__":
    unittest.main()
