#!/usr/bin/env python3
"""Render a self-contained HTML brief from a mission report JSON file."""

import argparse
import html
import importlib.util
import json
from pathlib import Path


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


def render(data):
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
