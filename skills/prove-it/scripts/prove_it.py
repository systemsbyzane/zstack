#!/usr/bin/env python3
"""Validate a mission report's delivery evidence structure."""

import argparse
import json
import sys
from pathlib import Path


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _evidence_ok(value):
    return isinstance(value, list) and bool(value) and all(_text(item) for item in value)


def evaluate(data):
    """Return an evidence gate report. This validates declarations, not truth."""
    issues = []
    failures = []
    unverified = []
    if not isinstance(data, dict):
        data = {}
        issues.append("Mission report must be a JSON object.")

    mission_id = data.get("mission_id")
    source = data.get("source")
    if not _text(mission_id):
        issues.append("mission_id is missing.")
    if not isinstance(source, dict):
        source = {}
        issues.append("source identity is missing.")
    for field in ("repository", "branch", "revision"):
        if not _text(source.get(field)):
            issues.append(f"source.{field} is missing.")
    tested_revision = data.get("tested_revision")
    if not _text(tested_revision):
        issues.append("tested_revision is missing.")
    elif _text(source.get("revision")) and source["revision"] != tested_revision:
        failures.append("Tested revision does not match source revision.")

    acceptance = data.get("original_acceptance")
    if not isinstance(acceptance, list) or not acceptance:
        acceptance = []
        issues.append("original_acceptance must contain every requested acceptance item.")
    for index, item in enumerate(acceptance):
        label = f"original_acceptance[{index}]"
        if not isinstance(item, dict):
            issues.append(f"{label} must be an object.")
            continue
        if not _text(item.get("id")) or not _text(item.get("requirement")):
            issues.append(f"{label} needs a nonempty id and requirement.")
        status = item.get("status")
        if status == "failed":
            failures.append(f"Acceptance {item.get('id', index)} failed.")
        elif status == "unverified":
            unverified.append(f"Acceptance {item.get('id', index)} is unverified.")
        elif status != "verified":
            issues.append(f"{label} has no recognized verification status.")
        if not _evidence_ok(item.get("evidence")):
            issues.append(f"{label} needs actual evidence references.")

    checks = data.get("checks")
    if not isinstance(checks, list) or not checks:
        checks = []
        issues.append("checks must include at least one actual check.")
    passed_count = 0
    for index, check in enumerate(checks):
        label = f"checks[{index}]"
        if not isinstance(check, dict):
            issues.append(f"{label} must be an object.")
            continue
        if not _text(check.get("name")) or not _text(check.get("command")):
            issues.append(f"{label} needs a name and exact command.")
        status = check.get("status")
        if status == "failed":
            failures.append(f"Check {check.get('name', index)} failed.")
        elif status == "not_run":
            unverified.append(f"Check {check.get('name', index)} was not run.")
        elif status == "passed":
            passed_count += 1
        else:
            issues.append(f"{label} has no recognized execution status.")
        if not _evidence_ok(check.get("evidence")):
            issues.append(f"{label} needs actual output or evidence references.")
    if checks and passed_count == 0:
        issues.append("No check is recorded as passed.")

    for field, destination in (("failures", failures), ("unverified", unverified)):
        value = data.get(field)
        if not isinstance(value, list):
            issues.append(f"{field} must be present as a list, even when empty.")
        else:
            for item in value:
                if not _text(item):
                    issues.append(f"{field} entries must be nonempty strings.")
                else:
                    destination.append(item)

    if failures:
        verdict = "FAIL"
    elif issues or unverified:
        verdict = "INSUFFICIENT EVIDENCE"
    else:
        verdict = "PASS"
    return {
        "verdict": verdict,
        "mission_id": mission_id if _text(mission_id) else None,
        "source": source,
        "tested_revision": tested_revision if _text(tested_revision) else None,
        "original_acceptance": acceptance,
        "checks": checks,
        "failures": failures,
        "unverified": unverified,
        "issues": issues,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="mission report JSON")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.report.read_text(encoding="utf-8"))
        result = evaluate(data)
    except (OSError, json.JSONDecodeError) as exc:
        result = evaluate(None)
        result["issues"].append(f"Cannot read mission report: {exc}")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return {"PASS": 0, "FAIL": 1, "INSUFFICIENT EVIDENCE": 2}[result["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
