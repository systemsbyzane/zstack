"""Exercise the production runner, receipt validator, and Chief brief CLI."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROVE = ROOT / "skills/prove-it/scripts/prove_it.py"
BRIEF = ROOT / "skills/brief-me/scripts/brief_me.py"
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
REQUIRED_FIELDS = {"assignmentId", "title", "status", "phase", "summary", "lastReportedAt",
                   "coordinatorLink", "blocker", "decisionNeeded", "testedRevision", "reviewState"}


def call(args, cwd=None):
    return subprocess.run([sys.executable, *map(str, args)], cwd=cwd, env=ENV,
                          text=True, capture_output=True, check=False)


class ProductionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.name", "Test"], check=True)
        (self.repo / "source.txt").write_text("baseline\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "source.txt"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "baseline"], check=True)

    def tearDown(self):
        self.temp.cleanup()

    def run_plan(self, commands=None, mission="assignment-42"):
        plan = {"schema_version": 1, "mission_id": mission,
                "acceptance": [{"id": "A1", "requirement": "The focused check runs"}],
                "checks": commands if commands is not None else [
                    {"id": "smoke", "name": "Actual smoke command", "argv": [sys.executable, "-c", "print('executed')"], "acceptance_ids": ["A1"]}]}
        plan_path = self.base / f"{mission}-plan.json"
        receipt = self.base / f"{mission}-receipt.json"
        logs = self.base / f"{mission}-logs"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        result = call([PROVE, "run", plan_path, "--repo", self.repo,
                       "--receipt", receipt, "--logs", logs])
        return result, receipt, logs

    def validate(self, receipt, mission="assignment-42"):
        return call([PROVE, "validate", receipt, "--mission", mission, "--repo", self.repo])

    def test_runner_executes_argv_and_chief_validator_accepts_exact_clean_source(self):
        result, receipt, logs = self.run_plan()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["verdict"], "PASS")
        evidence = json.loads(receipt.read_text(encoding="utf-8"))["automated"][0]
        self.assertEqual(evidence["exit_code"], 0)
        self.assertIn("executed", Path(evidence["stdout"]["path"]).read_text(encoding="utf-8"))
        self.assertTrue(logs.is_dir())
        checked = self.validate(receipt)
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)

    def test_nonzero_command_fails_and_declarations_without_execution_are_insufficient(self):
        command = {"id": "bad", "name": "Failing command", "argv": [sys.executable, "-c", "raise SystemExit(3)"], "acceptance_ids": ["A1"]}
        result, receipt, _ = self.run_plan([command])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["verdict"], "FAIL")
        self.assertEqual(self.validate(receipt).returncode, 1)

        # A report's command string is untrusted data and is never executed by validate.
        marker = self.base / "should-not-exist"
        fake_report = self.base / "fabricated.json"
        fake_report.write_text(json.dumps({"mission_id": "assignment-42", "command": f"touch {marker}", "verdict": "PASS"}), encoding="utf-8")
        check = self.validate(fake_report)
        self.assertEqual(check.returncode, 2)
        self.assertEqual(json.loads(check.stdout)["verdict"], "INSUFFICIENT EVIDENCE")
        self.assertFalse(marker.exists())

        uncovered = {"id": "unlinked", "name": "Executed but unrelated", "argv": [sys.executable, "-c", "print('ran')"], "acceptance_ids": []}
        insufficient, _, _ = self.run_plan([uncovered], mission="assignment-uncovered")
        self.assertEqual(insufficient.returncode, 2)
        self.assertEqual(json.loads(insufficient.stdout)["verdict"], "INSUFFICIENT EVIDENCE")

    def test_manual_observation_is_captured_separately_from_executed_check(self):
        plan = {"schema_version": 1, "mission_id": "assignment-manual",
                "acceptance": [{"id": "A1", "requirement": "Automated behavior"},
                               {"id": "A2", "requirement": "Live redirect observed"}],
                "checks": [{"id": "check", "name": "Actual command", "argv": [sys.executable, "-c", "print('ok')"], "acceptance_ids": ["A1"]}]}
        plan_path = self.base / "manual-plan.json"
        manual_path = self.base / "manual-evidence.json"
        receipt = self.base / "manual-receipt.json"
        logs = self.base / "manual-logs"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        manual_path.write_text(json.dumps([{"acceptance_id": "A2", "observed_by": "Coordinator",
                                            "observation": "Same Coordinator link retained after redirect"}]), encoding="utf-8")
        result = call([PROVE, "run", plan_path, "--repo", self.repo, "--receipt", receipt,
                       "--logs", logs, "--manual-evidence", manual_path])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        record = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertEqual(record["manual"][0]["kind"], "manual")
        self.assertEqual(self.validate(receipt, "assignment-manual").returncode, 0)

    def test_tracked_and_untracked_source_changes_invalidate_receipt(self):
        _, receipt, _ = self.run_plan()
        (self.repo / "source.txt").write_text("edited\n", encoding="utf-8")
        result = self.validate(receipt)
        self.assertEqual(result.returncode, 1)
        self.assertIn("dirty", result.stdout.lower())

        subprocess.run(["git", "-C", str(self.repo), "checkout", "--", "source.txt"], check=True)
        _, receipt2, _ = self.run_plan(mission="assignment-untracked")
        (self.repo / "new-source.txt").write_text("untracked\n", encoding="utf-8")
        result2 = call([PROVE, "validate", receipt2, "--mission", "assignment-untracked", "--repo", self.repo])
        self.assertEqual(result2.returncode, 1)
        self.assertIn("untracked", result2.stdout.lower())

    def test_revision_change_invalidates_receipt(self):
        _, receipt, _ = self.run_plan()
        (self.repo / "source.txt").write_text("new committed source\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "source.txt"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "source edit"], check=True)
        result = self.validate(receipt)
        self.assertEqual(result.returncode, 1)
        self.assertIn("revision", result.stdout.lower())

    def test_cleanliness_is_required_before_runner_executes(self):
        (self.repo / "untracked.txt").write_text("dirty\n", encoding="utf-8")
        result, _, _ = self.run_plan()
        self.assertEqual(result.returncode, 2)
        self.assertIn("clean", result.stdout.lower())


class ChiefBriefTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.now = datetime.now(timezone.utc)
        self.status = self.base / "status.json"
        self.output = self.base / "brief.html"

    def tearDown(self):
        self.temp.cleanup()

    def projection(self):
        now = self.now.isoformat().replace("+00:00", "Z")
        def item(i, title, status, report_time):
            return {"assignmentId": i, "title": title, "status": status, "phase": "integration",
                    "summary": "Meaningful worker return integrated; verification pending",
                    "lastReportedAt": report_time, "coordinatorLink": "https://t3.example/thread/coordinator",
                    "blocker": None, "decisionNeeded": None, "testedRevision": "abc123",
                    "reviewState": "pending" if status == "ready-for-review" else "not-requested"}
        return {"schemaVersion": 1, "generatedAt": now, "chief": {"link": "https://t3.example/thread/chief"},
                "assignments": [item("one", "Active", "working", now),
                               item("two", "Review", "ready-for-review", now),
                               item("three", "Stopped", "blocked", now),
                               item("four", "Finished", "done", now),
                               item("five", "No timestamp", "working", None)]}

    def render(self, source=None):
        return call([BRIEF, source or self.status, "--output", self.output])

    def test_projection_statuses_owner_progress_and_unknown_render_from_authoritative_schema(self):
        self.status.write_text(json.dumps(self.projection()), encoding="utf-8")
        result = self.render()
        self.assertEqual(result.returncode, 0, result.stderr)
        page = self.output.read_text(encoding="utf-8")
        for value in ("Active", "Review Ready", "Blocked", "Completed", "Unknown", "Coordinator thread",
                      "Meaningful worker return integrated; verification pending", "abc123", "last report time is unknown"):
            self.assertIn(value, page)
        self.assertIn("Status is last reported", page)

    def test_private_state_enrichment_is_matched_escaped_and_optional(self):
        projection = self.projection()
        self.status.write_text(json.dumps(projection))
        state = {"chief": projection["chief"], "chiefSummary": "<summary>", "assignments": [
            {"assignmentId": "one", "owner": "<owner>", "prUrl": "https://example.org/pr/4",
             "artifactUrl": "javascript:alert(1)", "verification": {"verdict": "FAIL", "summary": "<failed>"}},
            {"assignmentId": "not-in-roster", "owner": "PRIVATE SECRET"}]}
        (self.base / "state.json").write_text(json.dumps(state))
        self.assertEqual(self.render().returncode, 0)
        page = self.output.read_text()
        for value in ("&lt;summary&gt;", "&lt;owner&gt;", "FAIL", "&lt;failed&gt;", 'href="https://example.org/pr/4"', "Unknown — no verdict recorded"):
            self.assertIn(value, page)
        self.assertNotIn('href="javascript:', page)
        self.assertNotIn("PRIVATE SECRET", page)
        (self.base / "state.json").write_text("malformed")
        self.assertEqual(self.render().returncode, 0)
        self.assertIn("Unknown — no verdict recorded", self.output.read_text())

    def test_adapter_fields_and_statuses_match_companion_schema(self):
        schema = json.loads((ROOT / "companion/status.schema.json").read_text(encoding="utf-8"))
        assignment = schema["properties"]["assignments"]["items"]
        self.assertEqual(set(assignment["required"]), REQUIRED_FIELDS)
        self.assertEqual(set(assignment["properties"]["status"]["enum"]),
                         {"needs-you", "blocked", "ready-for-review", "working", "done", "unknown"})

    def test_missing_malformed_and_stale_projections_are_unknown(self):
        missing = self.render(self.base / "missing-chief")
        self.assertEqual(missing.returncode, 0)
        self.assertIn("unknown", self.output.read_text(encoding="utf-8").lower())
        self.status.write_text("{bad json", encoding="utf-8")
        malformed = self.render()
        self.assertEqual(malformed.returncode, 0)
        self.assertIn("malformed", self.output.read_text(encoding="utf-8").lower())
        stale = self.projection()
        old = (self.now - timedelta(hours=30)).isoformat().replace("+00:00", "Z")
        stale["generatedAt"] = old
        stale["assignments"] = stale["assignments"][:1]
        stale["assignments"][0]["lastReportedAt"] = old
        self.status.write_text(json.dumps(stale), encoding="utf-8")
        self.render()
        page = self.output.read_text(encoding="utf-8")
        self.assertIn("older than 24 hours", page)
        self.assertIn("unknown", page.lower())

    def test_fabricated_portfolio_shape_is_not_treated_as_a_chief_projection(self):
        self.status.write_text(json.dumps({"portfolio": {"missions": [{"name": "Fabricated", "status": "active"}]}}), encoding="utf-8")
        self.render()
        page = self.output.read_text(encoding="utf-8")
        self.assertIn("invalid", page.lower())
        self.assertNotIn("Fabricated", page)


if __name__ == "__main__":
    unittest.main()
