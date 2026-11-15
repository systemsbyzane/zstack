# zstack

Personal T3 Cortex orchestration skills. The Chief owns routing and user
communication; each Coordinator owns an assignment through delegation,
integration, recovery, and evidence-backed delivery. Council remains an
optional independent review skill.

## Install

Copy the complete `skills` directory so each skill keeps its executable and
reference files:

```sh
mkdir -p ~/.codex/skills
cp -R skills/* ~/.codex/skills/
```

Start a new T3 thread and send:

```text
$cortex
Bootstrap this thread as my chief of staff.
```

Pin that thread manually. Runtime state, credentials, and project artifacts
are not included. Skills guide agent behavior; they are not a background
service or enforced runtime limits. Local paths in the contracts reflect the
original installation and should be adapted on another machine.

## Commands

- `/dispatch` — Chief routes an outcome to a separate Coordinator thread.
- `/decompose` — Coordinator breaks an assignment into owned, meaningful work.
- `/integrate` — Coordinator integrates changes and runs affected checks.
- `/prove-it` — require an exact-identity evidence gate before successful delivery.
- `/brief-me` — render a concise HTML brief from a mission report's real data.
- `/recover` — resolve routine execution failures while preserving ownership.
- `/status` — report evidence-backed assignment status.
- `/redirect` — change the current Coordinator's approach without creating a new assignment.
- `/council` — optional independent review (existing Council skill).

`prove-it` exits 0 only for `PASS`, 1 for `FAIL`, and 2 for
`INSUFFICIENT EVIDENCE`. See [the mission report format](skills/prove-it/references/mission-report.md)
and [the brief renderer](skills/brief-me/SKILL.md).

## Evidence and acceptance

Run the executable production-path gate tests with:

```sh
python3 -m unittest discover -s tests -v
```

These tests use labelled synthetic reports to demonstrate: complete matching
identity and evidence passes; a revision mismatch or failed check fails; and
missing or unverified evidence is insufficient. They also invoke the actual
`prove_it.py` and `brief_me.py` entry points and check escaping, theme styling,
transparency, and the narrow-screen layout. They do not prove that a live T3
Chief can create threads, that Coordinators can delegate or recover work, or
that a report's declared evidence is truthful.

For an assignment, preserve its original acceptance in the report, record the
exact tested commit and actual command output, and run `prove_it.py` against
that report. Only `PASS` allows successful delivery. To demonstrate an HTML
brief, generate it from that same report, inspect native previews at 728px and
360px when those host tools are available, and render it with the host's
`html_render`; record tool errors or unavailable live behaviors as unverified.

## Supervision

Coordinators check in with the chief on material progress, blockers and work
boundaries. The chief evaluates evidence and alignment with the assigned goal,
then continues, redirects or stops work within the user's existing authority.
Time and retry thresholds trigger chief review, not repeated user approval.
The user receives completed results or decisions that need their authority or
judgment. Check-ins are event-driven; there is no background polling service.

## License

MIT. Council includes adaptations of tstack; its original notice is preserved in `skills/council/references/upstream.md`.

## Companion app

Experimental lightweight status board and Mac launcher source: [companion](companion/README.md). Local configuration required; no runtime state or credentials included.
