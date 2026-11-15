---
name: brief-me
description: Render a read-only brief from the Chief's sanitized status projection.
---

# Brief me

Read the authoritative sanitized projection written by the Chief. Accept a
Chief directory or its `status.json` file:

```sh
python3 skills/brief-me/scripts/brief_me.py \
  ~/.codex/cortex/chiefs/<actual-chief-thread-id> \
  --output /tmp/chief-brief.html
```

The adapter implements projection v1 from
`skills/cortex/references/status-reporting.md` and
`companion/status.schema.json`. It displays assignment owner, status, phase,
progress, report time, verification revision, review state, links, blocker
and decision need. Status maps to active, review-ready, blocked, completed or
unknown. Missing, malformed or stale data is explicitly unknown; stale means
the projection or assignment report is more than 24 hours old. This is a
read-only adapter. Never write or repair `state.json` or `status.json`; the
Chief is their sole writer. A projection is last-reported status, not proof of
live execution.

When native `html_preview` and `html_render` tools are available, preview the
generated output at 728px and 360px, inspect both and render that same file.
If unavailable, report that limitation and give the HTML path; do not claim a
rendered preview.
