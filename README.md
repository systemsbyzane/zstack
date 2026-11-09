# zstack

Personal T3 Cortex orchestration skills.

- `skills/cortex`: pinned chief-of-staff thread and assignment routing.
- `skills/cortex-coordinator`: separate assignment coordinators, scoped Codex/Cursor workers, validation and evidence.
- `skills/council`: independent Sol 6.1, Muse Wonder and Luna max review.

Copy these folders into `~/.codex/skills/`. Start a new T3 thread and send:

```text
$cortex
Bootstrap this thread as my chief of staff.
```

Pin that thread manually. Runtime state, credentials and project artifacts are not included. Skills guide agent behavior; they are not a background service or enforced runtime limits. Local paths in the contracts reflect the original installation and should be adapted on another machine.

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
