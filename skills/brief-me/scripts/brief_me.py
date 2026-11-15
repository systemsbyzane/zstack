#!/usr/bin/env python3
"""Render a self-contained HTML brief from a mission report JSON file."""

import argparse
import html
import importlib.util
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit


GATE_PATH = Path(__file__).resolve().parents[2] / "prove-it" / "scripts" / "prove_it.py"
SPEC = importlib.util.spec_from_file_location("prove_it", GATE_PATH)
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def esc(value):
    if value is None:
        return "Not supplied"
    if isinstance(value, list):
        value = " · ".join(str(item) for item in value)
    elif isinstance(value, dict):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return html.escape(str(value))


def card(title, body):
    return f'<section class="card"><h2>{esc(title)}</h2>{body}</section>'


def records(items, columns, empty_text):
    if not isinstance(items, list):
        return f'<p class="muted">{esc(empty_text)}</p>'
    if not items:
        return f'<p class="muted">{esc(empty_text)}</p>'
    rows = []
    for item in items:
        if not isinstance(item, dict):
            rows.append(f"<li>{esc(item)}</li>")
            continue
        values = "".join(f"<dt>{esc(label)}</dt><dd>{esc(item.get(key))}</dd>" for key, label in columns)
        rows.append(f'<li><dl>{values}</dl></li>')
    return "<ul class='records'>" + "".join(rows) + "</ul>"


def strings(items, missing):
    if not isinstance(items, list):
        return f'<p class="muted">{esc(missing)}</p>'
    if not items:
        return '<p class="muted">None recorded</p>'
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def safe_href(value):
    """Allow web links and simple relative artifact links, never active schemes."""
    if not isinstance(value, str) or not value.strip():
        return None
    value = value.strip()
    if any(ord(char) < 32 for char in value) or "\\" in value:
        return None
    try:
        parts = urlsplit(value)
    except ValueError:
        return None
    if parts.scheme:
        return value if parts.scheme.lower() in ("http", "https") and parts.netloc else None
    if parts.netloc or value.startswith("/") or value.startswith("//"):
        return None
    decoded_path = unquote(parts.path)
    if "\\" in decoded_path or any(part == ".." for part in decoded_path.split("/")):
        return None
    return value


def link(value, default_label):
    if isinstance(value, dict):
        href = safe_href(value.get("url"))
        label = value.get("label") or value.get("url") or default_label
    else:
        href = safe_href(value)
        label = value or default_label
    if not href:
        return esc(value if value is not None else "Not supplied")
    return f'<a href="{esc(href)}" rel="noopener noreferrer">{esc(label)}</a>'


def portfolio_mission(item):
    if not isinstance(item, dict):
        return f"<li>{esc(item)}</li>"
    name = item.get("name", item.get("mission_id"))
    fields = (("status", "Status"), ("progress", "Progress"), ("verification", "Verification"))
    rows = "".join(f"<dt>{label}</dt><dd>{esc(item.get(key))}</dd>" for key, label in fields if key in item)
    links = []
    for key, label in (("pr_url", "Pull request"), ("pr", "Pull request"),
                       ("artifact_url", "Artifact"), ("artifact", "Artifact")):
        if key in item and item[key] is not None:
            links.append(f"<dt>{label}</dt><dd>{link(item[key], label)}</dd>")
    if rows or links:
        rows = f"<dt>Mission</dt><dd>{esc(name)}</dd>" + rows + "".join(links)
        details = f"<dl>{rows}</dl>"
    else:
        details = f"<p>{esc(name)}</p>"
    return f"<li>{details}</li>"


def render_portfolio(data):
    portfolio = data.get("portfolio") if isinstance(data.get("portfolio"), dict) else data
    missions = portfolio.get("missions")
    missions = missions if isinstance(missions, list) else []
    summary = f"<p>{esc(portfolio.get('chief_summary'))}</p>" if portfolio.get("chief_summary") else ""
    sections = []
    groups = (("active", {"active", "in progress", "in-progress"}),
              ("review-ready", {"review-ready", "review ready", "ready for review"}),
              ("attention", {"attention", "blocked", "at risk", "failed"}))
    assigned = set()
    for title, statuses in groups:
        matching = [m for m in missions if isinstance(m, dict) and str(m.get("status", "")).strip().lower() in statuses]
        assigned.update(id(m) for m in matching)
        if matching:
            sections.append(card(title.title(), "<ul class='records'>" + "".join(portfolio_mission(m) for m in matching) + "</ul>"))
    other = [m for m in missions if id(m) not in assigned]
    if other:
        sections.append(card("Other missions", "<ul class='records'>" + "".join(portfolio_mission(m) for m in other) + "</ul>"))
    if not sections:
        sections.append(card("Missions", '<p class="muted">No missions supplied</p>'))
    return f'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{{color-scheme:light dark}}*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;background:transparent;color:var(--foreground);font-family:var(--font-sans,system-ui,sans-serif)}}
main{{width:100%;max-width:100%;display:grid;gap:12px}}h1{{font-size:1.35rem;margin:0}}h2{{font-size:1rem;margin:0 0 12px}}
p{{margin:0;overflow-wrap:anywhere}}.muted{{color:var(--muted-foreground,var(--muted))}}
.card{{padding:16px;border:1px solid var(--border);border-radius:var(--radius);background:var(--card);color:var(--card-foreground,var(--foreground));min-width:0}}
ul{{margin:0;padding-left:20px}}li+li{{margin-top:10px}}.records{{list-style:none;padding:0}}
dl{{display:grid;grid-template-columns:minmax(95px,140px) minmax(0,1fr);gap:4px 10px;margin:0}}dt{{color:var(--muted-foreground,var(--muted));font-size:.85rem}}dd{{margin:0;overflow-wrap:anywhere}}
a{{color:var(--link,var(--primary));overflow-wrap:anywhere}}@media(max-width:420px){{dl{{grid-template-columns:1fr;gap:2px}}}}
</style></head><body><main><h1>Mission portfolio</h1>{summary}{''.join(sections)}</main></body></html>'''


def render(data):
    if isinstance(data, dict) and ("portfolio" in data or "missions" in data):
        return render_portfolio(data)
    gate = GATE.evaluate(data)
    source = gate["source"] if isinstance(gate["source"], dict) else {}
    verdict = gate["verdict"]
    verdict_class = {"PASS": "pass", "FAIL": "fail", "INSUFFICIENT EVIDENCE": "unknown"}[verdict]
    identity = " · ".join(esc(source.get(key)) for key in ("repository", "branch", "revision"))
    check_rows = records(gate["checks"], (("name", "Check"), ("command", "Command"), ("status", "Result"), ("evidence", "Evidence")), "No checks recorded")
    acceptance_rows = records(gate["original_acceptance"], (("id", "ID"), ("requirement", "Original acceptance"), ("status", "Status"), ("evidence", "Evidence")), "No original acceptance items recorded")
    issue_list = strings(gate["issues"], "No gate issues")
    failure_list = strings(gate["failures"], "No failures recorded")
    unverified_list = strings(gate["unverified"], "No unverified items recorded")
    return f'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{{color-scheme:light dark}}
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;background:transparent;color:var(--foreground);font-family:var(--font-sans,system-ui,sans-serif)}}
main{{width:100%;max-width:100%;display:grid;gap:12px}}
h1{{font-size:1.35rem;line-height:1.25;margin:0 0 4px}}h2{{font-size:1rem;margin:0 0 12px}}
p{{margin:0;overflow-wrap:anywhere}}.muted{{color:var(--muted-foreground,var(--muted))}}
.summary{{display:flex;flex-wrap:wrap;align-items:center;gap:12px 16px}}
.badge{{display:inline-block;padding:6px 10px;border-radius:var(--radius);font-weight:700;background:var(--secondary);color:var(--secondary-foreground,var(--foreground))}}
.badge.pass{{background:var(--success-surface,var(--secondary));color:var(--success-foreground,var(--foreground))}}
.badge.fail{{background:var(--destructive-surface,var(--secondary));color:var(--destructive-foreground,var(--foreground))}}
.badge.unknown{{background:var(--warning-surface,var(--secondary));color:var(--warning-foreground,var(--foreground))}}
.card{{padding:16px;border:1px solid var(--border);border-radius:var(--radius);background:var(--card);color:var(--card-foreground,var(--foreground));min-width:0}}
code{{font-family:var(--font-mono,monospace);overflow-wrap:anywhere}}.identity{{font-size:.9rem;color:var(--muted-foreground,var(--muted));overflow-wrap:anywhere}}
ul{{margin:0;padding-left:20px}}li+li{{margin-top:10px}}.records{{list-style:none;padding:0}}
dl{{display:grid;grid-template-columns:minmax(95px,140px) minmax(0,1fr);gap:4px 10px;margin:0}}
dt{{color:var(--muted-foreground,var(--muted));font-size:.85rem}}dd{{margin:0;overflow-wrap:anywhere}}
@media(max-width:420px){{dl{{grid-template-columns:1fr;gap:2px}}dd+dt{{margin-top:8px}}.summary{{align-items:flex-start;flex-direction:column}}}}
</style></head><body><main>
<section><div class="summary"><h1>Mission brief</h1><span class="badge {verdict_class}">{esc(verdict)}</span></div>
<p><strong>{esc(gate['mission_id'])}</strong></p><p class="identity">{identity}</p>
<p class="identity">Tested revision: <code>{esc(gate['tested_revision'])}</code></p></section>
{card('Original acceptance', acceptance_rows)}
{card('Actual checks', check_rows)}
{card('Failures', failure_list)}
{card('Unverified', unverified_list)}
{card('Gate issues', issue_list)}
</main></body></html>'''


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="mission report JSON")
    parser.add_argument("--output", "-o", type=Path, required=True, help="output HTML path")
    args = parser.parse_args(argv)
    data = json.loads(args.report.read_text(encoding="utf-8"))
    args.output.write_text(render(data), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
