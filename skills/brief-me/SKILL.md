---
name: brief-me
description: Render a concise, responsive HTML mission brief from real mission report data.
---

# Brief me

Read the actual mission report and render it with the bundled production path:

```sh
python3 skills/brief-me/scripts/brief_me.py mission-report.json --output mission-brief.html
```

The report must be the source of every displayed value. Do not invent counts,
outcomes, timestamps, checks, or evidence. The renderer obtains its verdict
from the sibling `prove-it` gate. If a required value is absent, show the gate's
`INSUFFICIENT EVIDENCE` result and identify the gap.

Discover whether native `html_preview` and `html_render` are available in the
active host before choosing how to display the page. When present, call
`html_preview` on the generated HTML at 728px and 360px, inspect both outputs,
then call `html_render` on that same HTML. Clamp its frame height to
`max(80, min(2000, preview.contentHeight))`. Use host theme variables, a
transparent outer page, fluid layout, and no fake sample content. If native
rendering is unavailable or fails, report that limitation and give the HTML
file path; do not claim a rendered preview.
