---
name: prove-it
description: Execute trusted local checks and require a live source-bound receipt before delivery.
---

# Prove it

For Coordinators, run after integration and the final source commit. First
prepare a trusted plan outside the repository. It contains the original
acceptance items and only the exact commands authorized for local execution.
Each command is an argv array; do not put untrusted report command strings in
the plan. Keep the plan, manual notes, logs and receipt outside the worktree.

Run the production runner:

```sh
python3 skills/prove-it/scripts/prove_it.py run /outside/assignment-plan.json \
  --repo /path/to/repository --receipt /outside/assignment-receipt.json \
  --logs /outside/assignment-logs
```

The runner refuses a dirty initial tree, executes the argv arrays with no
shell, captures exit code/stdout/stderr, records the Git repository, worktree,
branch and revision, and checks the tree again afterward. Each acceptance
item must link to a successful automated check or a separately provided
manual observation. Manual evidence is self-reported, not authenticated.
`PASS` requires actual command execution and complete evidence coverage. Any
command failure or source change is `FAIL`; missing coverage is
`INSUFFICIENT EVIDENCE`. Exit codes are 0, 1 and 2 respectively.

The Chief must independently validate the returned receipt against the live
assignment and current repository before accepting delivery:

```sh
python3 skills/prove-it/scripts/prove_it.py validate \
  /outside/assignment-receipt.json --mission assignment-42 \
  --repo /path/to/repository
```

Validation compares the mission ID, live repository/worktree/revision and
clean tracked plus untracked state. It also checks executed records and log
digests. Any source edit invalidates the receipt. Validation executes no
commands from reports or receipts. This is not a signature system, and the
host exposes no policy hook that guarantees every instruction is followed;
see the repository README for the practical limit.

Return the verdict, source identity, acceptance coverage, exact check results,
manual observations, failures, gaps and receipt path. Do not infer success
from a worker's completion or a written status declaration. A prior PASS is
historical after any source change; rerun on the final integrated revision.

Trusted checks may set `timeout_seconds` (default 60, finite positive maximum
300). Invalid values are rejected before any execution. On timeout the POSIX
process group is killed, partial regular-file stdout/stderr logs are retained,
and exit 124 plus timed_out marks failure. Validation requires complete typed
receipt evidence and blocks recorded issues even if the verdict is changed.
