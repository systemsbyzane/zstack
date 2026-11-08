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

## License

MIT. Council includes adaptations of tstack; its original notice is preserved in `skills/council/references/upstream.md`.
