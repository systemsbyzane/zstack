#!/usr/bin/env python3
"""Run trusted local checks and validate source-bound mission receipts.

Only ``run`` executes commands. It executes argv arrays from an explicitly
selected local plan with shell=False; report and receipt validation never
execute command strings.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


VERSION = 1


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], text=True,
                          capture_output=True, check=False)


def identity(repo):
    root = _git(repo, "rev-parse", "--show-toplevel")
    if root.returncode:
        raise ValueError("repository path is not inside a Git worktree")
    root_path = Path(root.stdout.strip()).resolve()
    revision = _git(root_path, "rev-parse", "HEAD")
    git_dir = _git(root_path, "rev-parse", "--absolute-git-dir")
    branch = _git(root_path, "branch", "--show-current")
    remote = _git(root_path, "config", "--get", "remote.origin.url")
    status = _git(root_path, "status", "--porcelain=v1", "--untracked-files=all")
    if any(result.returncode for result in (revision, git_dir, branch, status)):
        raise ValueError("could not read Git identity and status")
    return {
        "repository": remote.stdout.strip() if remote.returncode == 0 else str(root_path),
        "worktree": str(root_path),
        "git_dir": str(Path(git_dir.stdout.strip()).resolve()),
        "branch": branch.stdout.strip() or None,
        "revision": revision.stdout.strip(),
        "dirty_paths": [line[3:] for line in status.stdout.splitlines() if line.strip()],
    }


def _outside(path, root, label):
    resolved = path.expanduser().resolve()
    if resolved == root or root in resolved.parents:
        raise ValueError(f"{label} must be outside the Git worktree")
    return resolved


def _valid_plan(plan):
    if not isinstance(plan, dict) or plan.get("schema_version") != VERSION:
        raise ValueError("plan must be an object with schema_version 1")
    mission = plan.get("mission_id")
    acceptance = plan.get("acceptance")
    checks = plan.get("checks")
    if not isinstance(mission, str) or not mission.strip():
        raise ValueError("plan mission_id is required")
    if not isinstance(acceptance, list) or not acceptance:
        raise ValueError("plan acceptance must be a nonempty list")
    if not isinstance(checks, list):
        raise ValueError("plan checks must be a list")
    ids = set()
    for item in acceptance:
        if not isinstance(item, dict) or not all(isinstance(item.get(k), str) and item[k].strip() for k in ("id", "requirement")):
            raise ValueError("each acceptance item needs nonempty id and requirement")
        if item["id"] in ids:
            raise ValueError("acceptance ids must be unique")
        ids.add(item["id"])
    check_ids = set()
    for check in checks:
        if not isinstance(check, dict) or not all(isinstance(check.get(k), str) and check[k].strip() for k in ("id", "name")):
            raise ValueError("each check needs nonempty id and name")
        argv = check.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(arg, str) for arg in argv):
            raise ValueError("each check argv must be a nonempty array of strings")
        if check["id"] in check_ids:
            raise ValueError("check ids must be unique")
        check_ids.add(check["id"])
        check["acceptance_ids"] = check.get("acceptance_ids", [])
        if not isinstance(check["acceptance_ids"], list) or any(a not in ids for a in check["acceptance_ids"]):
            raise ValueError(f"check {check['id']} has an unknown acceptance id")
        cwd = check.get("cwd", ".")
        if not isinstance(cwd, str):
            raise ValueError(f"check {check['id']} cwd must be a relative path")
        if Path(cwd).is_absolute() or ".." in Path(cwd).parts:
            raise ValueError(f"check {check['id']} cwd must stay inside the worktree")
    return mission, acceptance, checks


def _load_manual(path, acceptance):
    if path is None:
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("manual evidence file must contain an array")
    known = {item["id"] for item in acceptance}
    result = []
    for item in value:
        if not isinstance(item, dict) or item.get("acceptance_id") not in known:
            raise ValueError("manual evidence needs a known acceptance_id")
        if any(not isinstance(item.get(key), str) or not item[key].strip() for key in ("observed_by", "observation")):
            raise ValueError("manual evidence needs observed_by and observation")
        result.append({"kind": "manual", "acceptance_id": item["acceptance_id"],
                       "observed_by": item["observed_by"], "observation": item["observation"]})
    return result


def _digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def run_plan(plan_path, repo_path, receipt_path, logs_path, manual_path=None):
    repo = Path(repo_path).expanduser().resolve()
    before = identity(repo)
    root = Path(before["worktree"])
    plan_path = _outside(Path(plan_path), root, "plan")
    receipt_path = _outside(Path(receipt_path), root, "receipt")
    logs_path = _outside(Path(logs_path), root, "logs directory")
    if before["dirty_paths"]:
        return {"verdict": "INSUFFICIENT EVIDENCE", "mission_id": None,
                "issues": ["Worktree must be clean before execution."], "dirty_paths": before["dirty_paths"]}
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    mission, acceptance, checks = _valid_plan(plan)
    manual = _load_manual(Path(manual_path).expanduser().resolve() if manual_path else None, acceptance)
    if logs_path.exists() or receipt_path.exists():
        raise ValueError("logs directory and receipt path must not already exist")
    logs_path.mkdir(parents=True)
    results = []
    for check in checks:
        check_log = logs_path / re.sub(r"[^A-Za-z0-9_.-]", "_", check["id"])
        check_log.mkdir()
        cwd = (root / check.get("cwd", ".")).resolve()
        if cwd != root and root not in cwd.parents:
            raise ValueError(f"check {check['id']} cwd escapes the worktree")
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        try:
            proc = subprocess.run(check["argv"], cwd=cwd, env=env, text=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  check=False, shell=False)
            stdout, stderr, exit_code = proc.stdout, proc.stderr, proc.returncode
        except OSError as exc:
            stdout, stderr, exit_code = "", str(exc), 127
        stdout_path, stderr_path = check_log / "stdout.log", check_log / "stderr.log"
        stdout_path.write_text(stdout, encoding="utf-8")
        stderr_path.write_text(stderr, encoding="utf-8")
        results.append({"id": check["id"], "name": check["name"], "kind": "automated",
                        "argv": check["argv"], "cwd": str(cwd), "exit_code": exit_code,
                        "status": "passed" if exit_code == 0 else "failed",
                        "acceptance_ids": check["acceptance_ids"],
                        "stdout": {"path": str(stdout_path), "sha256": _digest(stdout_path)},
                        "stderr": {"path": str(stderr_path), "sha256": _digest(stderr_path)}})
    after = identity(root)
    failures, issues = [], []
    if any(item["exit_code"] != 0 for item in results):
        failures.append("One or more executed checks exited nonzero.")
    if after["revision"] != before["revision"]:
        failures.append("HEAD changed during execution.")
    if after["dirty_paths"]:
        failures.append("Worktree changed during execution; tracked or untracked paths are dirty.")
    for item in acceptance:
        automated = any(item["id"] in result["acceptance_ids"] and result["exit_code"] == 0
                        for result in results)
        has_manual = any(evidence["acceptance_id"] == item["id"] for evidence in manual)
        if not automated and not has_manual:
            issues.append(f"Acceptance {item['id']} has no successful execution or manual observation.")
    if not results:
        issues.append("No automated command was executed.")
    if failures:
        verdict = "FAIL"
    elif issues:
        verdict = "INSUFFICIENT EVIDENCE"
    else:
        verdict = "PASS"
    receipt = {"schema_version": VERSION, "mission_id": mission, "verdict": verdict,
               "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
               "source_before": before, "source_after": after, "acceptance": acceptance,
               "automated": results, "manual": manual, "failures": failures, "issues": issues}
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"verdict": verdict, "mission_id": mission, "receipt": str(receipt_path),
            "failures": failures, "issues": issues}


def validate_receipt(receipt_path, mission_id, repo_path):
    issues, failures = [], []
    try:
        receipt = json.loads(Path(receipt_path).expanduser().read_text(encoding="utf-8"))
        current = identity(repo_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return {"verdict": "INSUFFICIENT EVIDENCE", "mission_id": mission_id,
                "issues": [f"Cannot load receipt or current Git identity: {exc}"], "failures": []}
    if not isinstance(receipt, dict) or receipt.get("schema_version") != VERSION:
        return {"verdict": "INSUFFICIENT EVIDENCE", "mission_id": mission_id,
                "issues": ["Receipt schema is missing or unsupported."], "failures": []}
    if receipt.get("mission_id") != mission_id:
        failures.append("Receipt mission_id does not match the requested assignment.")
    if receipt.get("verdict") != "PASS":
        failures.append("Receipt did not record a PASS verdict.")
    before, after = receipt.get("source_before"), receipt.get("source_after")
    if not isinstance(before, dict) or not isinstance(after, dict):
        issues.append("Receipt source identity is missing.")
    else:
        for label, source in (("before", before), ("after", after)):
            for key in ("repository", "worktree", "git_dir", "branch", "revision"):
                if source.get(key) != current.get(key):
                    failures.append(f"Live {key} does not match receipt source_{label}.")
            if source.get("dirty_paths"):
                failures.append(f"Receipt source_{label} was not clean.")
        if current["dirty_paths"]:
            failures.append("Current worktree is dirty (tracked or untracked paths).")
        if before.get("revision") != after.get("revision"):
            failures.append("Receipt revision changed during execution.")
    automated = receipt.get("automated")
    if not isinstance(automated, list) or not automated:
        issues.append("Receipt contains no executed automated checks.")
    else:
        for check in automated:
            if not isinstance(check, dict) or check.get("kind") != "automated" or not isinstance(check.get("argv"), list):
                issues.append("Receipt has a malformed automated check.")
                continue
            if check.get("exit_code") != 0 or check.get("status") != "passed":
                failures.append(f"Executed check {check.get('id', '?')} did not pass.")
            for key in ("stdout", "stderr"):
                evidence = check.get(key)
                try:
                    path = Path(evidence["path"]).expanduser().resolve()
                    if not isinstance(after, dict) or Path(after["worktree"]).resolve() in path.parents:
                        raise ValueError("log path is inside the worktree")
                    if not path.is_file() or _digest(path) != evidence["sha256"]:
                        raise ValueError("log is missing or its digest differs")
                except (KeyError, TypeError, OSError, ValueError) as exc:
                    issues.append(f"Check {check.get('id', '?')} {key} evidence is invalid: {exc}.")
    if not isinstance(receipt.get("acceptance"), list) or not receipt["acceptance"]:
        issues.append("Receipt acceptance coverage is missing.")
    else:
        coverage = set()
        for check in automated if isinstance(automated, list) else []:
            if isinstance(check, dict) and check.get("exit_code") == 0:
                ids = check.get("acceptance_ids", [])
                if isinstance(ids, list):
                    coverage.update(value for value in ids if isinstance(value, str))
        manual = receipt.get("manual")
        if not isinstance(manual, list):
            issues.append("Manual evidence section is malformed.")
            manual = []
        coverage.update(item.get("acceptance_id") for item in manual if isinstance(item, dict) and item.get("observation") and item.get("observed_by"))
        for item in receipt["acceptance"]:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                issues.append("Receipt has malformed acceptance coverage.")
            elif item["id"] not in coverage:
                issues.append(f"Acceptance {item['id']} has no verified evidence.")
    receipt_failures = receipt.get("failures", [])
    if not isinstance(receipt_failures, list):
        issues.append("Receipt failures field is malformed.")
    else:
        failures.extend(item for item in receipt_failures if isinstance(item, str))
    if failures:
        verdict = "FAIL"
    elif issues:
        verdict = "INSUFFICIENT EVIDENCE"
    else:
        verdict = "PASS"
    return {"verdict": verdict, "mission_id": mission_id, "source": current,
            "failures": failures, "issues": issues}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    runner = sub.add_parser("run", help="execute the argv checks in a trusted local plan")
    runner.add_argument("plan", type=Path)
    runner.add_argument("--repo", type=Path, default=Path.cwd())
    runner.add_argument("--receipt", type=Path, required=True)
    runner.add_argument("--logs", type=Path, required=True)
    runner.add_argument("--manual-evidence", type=Path)
    validator = sub.add_parser("validate", help="validate a receipt against the live clean Git worktree")
    validator.add_argument("receipt", type=Path)
    validator.add_argument("--mission", required=True)
    validator.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        if args.action == "run":
            result = run_plan(args.plan, args.repo, args.receipt, args.logs, args.manual_evidence)
        else:
            result = validate_receipt(args.receipt, args.mission, args.repo)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        result = {"verdict": "INSUFFICIENT EVIDENCE", "issues": [str(exc)], "failures": []}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return {"PASS": 0, "FAIL": 1, "INSUFFICIENT EVIDENCE": 2}[result["verdict"]]


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
