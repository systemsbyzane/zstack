# zstack

Personal T3 Cortex orchestration skills. The Chief owns routing, the durable
tracker and user communication. Each Coordinator owns an assignment through
delegation, integration, recovery and verification. Council remains optional.

## Install

Copy the complete skills directory so each skill keeps its references and
executables:

```sh
mkdir -p ~/.codex/skills
cp -R skills/* ~/.codex/skills/
```

Start a new T3 thread and select/invoke Cortex using the skill mechanism
actually exposed by that host; verify it appears in the target session's skill
catalog. The `$cortex` text is not a host activation hook. Pin the thread
manually. Runtime state, credentials and project artifacts are not included.
Skills are instructions and local commands; they are not a host
policy hook, background service or enforced runtime boundary. Available host
tools do not expose an interception/delivery hook that can force every Chief
or Coordinator to follow these instructions. A Chief must validate receipts
before accepting a delivery, but instruction compliance cannot be guaranteed
by this repository.

## Commands

- `/dispatch` — Chief routes an outcome to a separate Coordinator.
- `/decompose` and `/integrate` — Coordinator plans meaningful ownership and
  integrates and verifies the result.
- `/prove-it` — execute explicitly trusted local checks and validate a
  source-bound receipt.
- `/brief-me` — render a read-only HTML brief from the Chief's sanitized
  `status.json` projection.
- `/recover`, `/status` and `/redirect` — recover, report and redirect while
  preserving ownership.
- `/council` — optional independent review skill.

## Model routing

Chief, Coordinator, worker, and Council model selection follows the shared
[model-routing guide](skills/cortex/references/model-routing.md). It covers
live capability discovery, explicit targets, suitable fallbacks, receipts,
current Muse/Cursor availability, and native Codex skill-discovery limits.

## Execution receipts

The runner executes only the explicit argv arrays in a trusted local plan.
It never executes commands found in mission reports or receipts. Plans,
manual evidence, logs and receipts must be kept outside the repository, and
the worktree must be clean before and after execution. Run it after the final
source commit:

```sh
python3 /path/to/skills/prove-it/scripts/prove_it.py run \
  /tmp/assignment-plan.json --repo /path/to/repository \
  --receipt /tmp/assignment-receipt.json \
  --logs /tmp/assignment-logs
```

The plan is JSON with `schema_version: 1`, a `mission_id`, acceptance items,
and checks. Each check has an `id`, `name`, an `argv` string array, and the
acceptance IDs it verifies. The runner uses no shell and captures exit code,
stdout, stderr and SHA-256 log references. Optional manual observations are
provided separately with `--manual-evidence /tmp/manual-evidence.json`; each
entry has `acceptance_id`, `observed_by` and `observation`. They are recorded
as self-reported observations, not authenticated facts.

The Chief validates the receipt against the assignment and current repository
state. Run from a context that can read the receipt and the repository:

```sh
python3 /path/to/skills/prove-it/scripts/prove_it.py validate \
  /tmp/assignment-receipt.json --mission assignment-42 \
  --repo /path/to/repository
```

Exit codes are 0 for `PASS`, 1 for `FAIL`, and 2 for `INSUFFICIENT EVIDENCE`.
Validation checks mission ID, Git repository/worktree/revision, clean tracked
and untracked state, executed check records and log digests. Any source edit,
new untracked path or revision change invalidates the receipt. This is not a
signature or cryptographic provenance system; a user who can alter the
receipt and logs can fabricate them. The check runner and receipts provide
reproducible execution records and live source matching, not host-enforced
policy or cryptographic attestation.

## Chief status brief

`/brief-me` reads a Chief directory or its sanitized `status.json` projection
using the documented v1 schema in `skills/cortex/references/status-reporting.md`
and `companion/status.schema.json`:

```sh
python3 /path/to/skills/brief-me/scripts/brief_me.py \
  ~/.codex/cortex/chiefs/<actual-chief-thread-id> \
  --output /tmp/chief-brief.html
```

This is read-only. Chief remains the sole writer of `state.json` and
`status.json`. Missing, malformed or older-than-24-hour status is shown as
unknown. Status is last-reported projection data, not proof of live execution.

## Verification and native smoke

Run the production-path tests after committing the source under test; the
environment flag prevents Python bytecode artifacts in the repository:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

They exercise the actual runner, validator and brief CLI using isolated Git
fixtures. The live T3 lifecycle is not represented by those fixtures. Follow
[the native smoke procedure](docs/native-smoke.md) to verify worker return,
integration, fail/fix/reverify, same-Coordinator redirect, two Chief-tracked
missions and brief-to-tracker agreement in the real host. Keep mocked tests
and live results separate. Prior mission reports in `artifacts/` are
historical snapshots and do not prove the current revision or live behavior.

## Companion app

The experimental companion sources remain under [companion](companion/README.md).
They are not required by the skills or the status brief.

## License

MIT. Council includes adaptations of tstack; its original notice is preserved
in `skills/council/references/upstream.md`.
