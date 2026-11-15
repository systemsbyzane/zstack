#!/usr/bin/env python3
"""Render a read-only brief from the Chief's sanitized status projection."""

import argparse
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit


STALE_AFTER_HOURS = 24
STATUSES = {"needs-you", "blocked", "ready-for-review", "working", "done", "unknown"}
REVIEW_STATES = {"not-requested", "pending", "handled"}
REQUIRED = {"assignmentId", "title", "status", "phase", "summary", "lastReportedAt",
            "coordinatorLink", "blocker", "decisionNeeded", "testedRevision", "reviewState"}


def esc(value):
    return html.escape("Not supplied" if value is None else str(value))


def safe_href(value):
    if not isinstance(value, str) or not value.strip() or any(ord(c) < 32 for c in value) or "\\" in value:
        return None
    try:
        parts = urlsplit(value.strip())
    except ValueError:
        return None
    if parts.scheme:
        return value if parts.scheme.lower() in ("http", "https", "t3-thread") and parts.netloc else None
    decoded = unquote(parts.path)
    if parts.netloc or value.startswith(("/", "//")) or "\\" in decoded or ".." in decoded.split("/"):
        return None
    return value


def parse_time(value):
    if not isinstance(value, str):
        raise ValueError("timestamp must be an ISO date-time string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def read_projection(source, now=None):
    """Return assignments with explicit unknown state for invalid/missing/stale data."""
    now = now or datetime.now(timezone.utc)
    source_path = Path(source).expanduser()
    if source_path.is_dir():
        source_path = source_path / "status.json"
    try:
        data = json.loads(source_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"chief": {}, "generatedAt": None, "assignments": [],
                "unknown_reason": f"Status projection missing: {source_path}"}
    except (OSError, json.JSONDecodeError) as exc:
        return {"chief": {}, "generatedAt": None, "assignments": [],
                "unknown_reason": f"Status projection unreadable or malformed: {exc}"}
    try:
        if not isinstance(data, dict) or set(data) != {"schemaVersion", "generatedAt", "chief", "assignments"}:
            raise ValueError("projection must match the documented v1 top-level fields")
        if data["schemaVersion"] != 1 or not isinstance(data["chief"], dict) or set(data["chief"]) != {"link"}:
            raise ValueError("projection schema version or chief fields are invalid")
        generated = parse_time(data["generatedAt"])
        if not isinstance(data["chief"]["link"], str):
            raise ValueError("chief.link must be a string")
        if not isinstance(data["assignments"], list):
            raise ValueError("assignments must be an array")
        for assignment in data["assignments"]:
            if not isinstance(assignment, dict) or set(assignment) != REQUIRED:
                raise ValueError("an assignment does not match the documented v1 fields")
            for key in ("assignmentId", "title", "phase", "summary"):
                if not isinstance(assignment[key], str):
                    raise ValueError(f"assignment {key} must be a string")
            if assignment["status"] not in STATUSES or assignment["reviewState"] not in REVIEW_STATES:
                raise ValueError("assignment status or reviewState is invalid")
            for key in ("lastReportedAt", "coordinatorLink", "blocker", "decisionNeeded", "testedRevision"):
                if assignment[key] is not None and not isinstance(assignment[key], str):
                    raise ValueError(f"assignment {key} must be a string or null")
            if assignment["lastReportedAt"] is not None:
                parse_time(assignment["lastReportedAt"])
        stale_projection = (now.astimezone(timezone.utc) - generated).total_seconds() > STALE_AFTER_HOURS * 3600 or generated > now
    except (ValueError, TypeError, KeyError) as exc:
        return {"chief": {}, "generatedAt": None, "assignments": [],
                "unknown_reason": f"Status projection invalid: {exc}"}
    # Optional private-state enrichment is read-only and allowlisted. The
    # sanitized projection remains authoritative for roster and status.
    enrichment = {}
    chief_summary = None
    try:
        state = json.loads((source_path.parent / "state.json").read_text(encoding="utf-8"))
        if isinstance(state, dict) and state.get("chief") == data["chief"]:
            chief_summary = state.get("chiefSummary") if isinstance(state.get("chiefSummary"), str) else None
            for entry in state.get("assignments", []):
                if isinstance(entry, dict) and isinstance(entry.get("assignmentId"), str):
                    enrichment.setdefault(entry["assignmentId"], []).append(entry)
    except (OSError, ValueError, TypeError):
        pass
    result = []
    for item in data["assignments"]:
        age = None
        if item["lastReportedAt"]:
            last = parse_time(item["lastReportedAt"])
            age = (now.astimezone(timezone.utc) - last).total_seconds()
        stale_assignment = age is not None and (age > STALE_AFTER_HOURS * 3600 or age < 0)
        unknown = stale_projection or stale_assignment or item["status"] == "unknown" or item["lastReportedAt"] is None
        copy = dict(item)
        matches = enrichment.get(item["assignmentId"], [])
        if len(matches) == 1:
            entry = matches[0]
            for key in ("owner", "prUrl", "artifactUrl", "evidencePath"):
                if isinstance(entry.get(key), str):
                    copy[key] = entry[key]
            verification = entry.get("verification")
            if isinstance(verification, dict):
                copy["verification"] = {k: verification[k] for k in ("verdict", "summary") if isinstance(verification.get(k), str)}
        if unknown:
            copy["display_status"] = "unknown"
            reasons = []
            if stale_projection:
                reasons.append("projection is older than 24 hours or timestamp is in the future")
            if stale_assignment:
                reasons.append("last report is older than 24 hours or in the future")
            if item["lastReportedAt"] is None:
                reasons.append("last report time is unknown")
            if item["status"] == "unknown":
                reasons.append("Chief reported unknown status")
            copy["unknown_reason"] = "; ".join(reasons)
        else:
            copy["display_status"] = {"working": "active", "ready-for-review": "review-ready",
                                       "blocked": "blocked", "needs-you": "blocked",
                                       "done": "completed"}[item["status"]]
            copy["unknown_reason"] = None
        result.append(copy)
    return {"chiefSummary": chief_summary, "chief": data["chief"], "generatedAt": data["generatedAt"], "assignments": result,
            "unknown_reason": "Projection is last-reported status, not proof of live execution."}


def assignment_card(item):
    link = safe_href(item.get("coordinatorLink"))
    owner = f'<a href="{html.escape(link, quote=True)}" rel="noopener noreferrer">Coordinator thread</a>' if link else "Coordinator link unavailable"
    fields = [("Owner", owner), ("Phase", esc(item.get("phase"))), ("Progress", esc(item.get("summary"))),
              ("Last reported", esc(item.get("lastReportedAt"))), ("Verification revision", esc(item.get("testedRevision"))),
              ("Review", esc(item.get("reviewState")))]
    fields.append(("Recorded owner", esc(item.get("owner"))))
    verification = item.get("verification", {})
    fields.append(("Recorded verification", esc(verification.get("verdict", "Unknown — no verdict recorded"))))
    if verification.get("summary"):
        fields.append(("Verification detail", esc(verification["summary"])))
    for key, label in (("prUrl", "Pull request"), ("artifactUrl", "Artifact"), ("evidencePath", "Evidence path")):
        if item.get(key):
            href = safe_href(item[key])
            value = f'<a href="{esc(href)}" rel="noopener noreferrer">{esc(item[key])}</a>' if href else esc(item[key])
            fields.append((label, value))
    if item.get("blocker"):
        fields.append(("Blocker", esc(item["blocker"])))
    if item.get("decisionNeeded"):
        fields.append(("Decision needed", esc(item["decisionNeeded"])))
    if item.get("unknown_reason"):
        fields.append(("Status detail", esc(item["unknown_reason"])))
    rows = "".join(f"<dt>{label}</dt><dd>{value}</dd>" for label, value in fields)
    status = item.get("display_status", "unknown")
    return f'<article class="card"><div class="title"><h2>{esc(item.get("title"))}</h2><span class="badge">{esc(status)}</span></div><p class="muted">Assignment {esc(item.get("assignmentId"))}</p><dl>{rows}</dl></article>'


def render_status(projection):
    order = ("active", "review-ready", "blocked", "completed", "unknown")
    groups = []
    assignments = projection["assignments"]
    if projection.get("unknown_reason") and not assignments:
        assignments = [{"assignmentId": "unknown", "title": "Assignment status unavailable",
                        "display_status": "unknown", "phase": "Unknown", "summary": projection["unknown_reason"],
                        "lastReportedAt": None, "testedRevision": None, "reviewState": "not-requested",
                        "unknown_reason": "No current authoritative status could be read."}]
    for status in order:
        matching = [item for item in assignments if item.get("display_status") == status]
        if matching:
            title = status.title().replace("-", " ")
            groups.append(f'<section><h1>{title}</h1>{"".join(assignment_card(item) for item in matching)}</section>')
    chief_link = safe_href(projection.get("chief", {}).get("link"))
    chief = f'<p class="muted">Chief: <a href="{html.escape(chief_link, quote=True)}" rel="noopener noreferrer">open thread</a></p>' if chief_link else ""
    chief += f'<p>{esc(projection.get("chiefSummary", "Chief summary not recorded"))}</p>'
    generated = esc(projection.get("generatedAt"))
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>
:root{{color-scheme:light dark}}*{{box-sizing:border-box}}html,body{{margin:0;padding:0;background:transparent;color:var(--foreground);font-family:var(--font-sans,system-ui,sans-serif)}}
main{{width:100%;max-width:100%;display:grid;gap:14px}}h1{{font-size:1.05rem;margin:0 0 8px}}h2{{font-size:1rem;margin:0}}p{{margin:0;overflow-wrap:anywhere}}.muted{{color:var(--muted-foreground,var(--muted));font-size:.9rem}}
.card{{padding:14px;border:1px solid var(--border);border-radius:var(--radius);background:var(--card);color:var(--card-foreground,var(--foreground));min-width:0;margin:8px 0}}.title{{display:flex;gap:10px;justify-content:space-between;align-items:center}}.badge{{font-weight:700;padding:4px 8px;border-radius:var(--radius);background:var(--secondary);white-space:nowrap}}
dl{{display:grid;grid-template-columns:minmax(110px,145px) minmax(0,1fr);gap:5px 10px;margin:12px 0 0}}dt{{font-size:.85rem;color:var(--muted-foreground,var(--muted))}}dd{{margin:0;overflow-wrap:anywhere}}a{{color:var(--link,var(--primary));overflow-wrap:anywhere}}@media(max-width:420px){{dl{{grid-template-columns:1fr;gap:2px}}dd+dt{{margin-top:8px}}.title{{align-items:flex-start;flex-direction:column}}}}
</style></head><body><main><section><h1>Chief assignment brief</h1>{chief}<p class="muted">Projection generated: {generated}. Status is last reported, not proof of live execution. Data older than 24 hours is shown as unknown.</p></section>{''.join(groups)}</main></body></html>'''


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Chief directory or its sanitized status.json projection")
    parser.add_argument("--output", "-o", type=Path, required=True)
    args = parser.parse_args(argv)
    projection = read_projection(args.source)
    args.output.write_text(render_status(projection), encoding="utf-8")
    print(json.dumps({"assignments": len(projection["assignments"]),
                      "unknown": bool(projection.get("unknown_reason") and not projection["assignments"]),
                      "source": str(args.source)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
