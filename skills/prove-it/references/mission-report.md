# Mission report format

Use JSON with all fields below. Preserve the original acceptance criteria and
record the exact revision actually checked (for example `git rev-parse HEAD`).
Evidence strings identify actual command output, logs, files, or observed
behavior; they are references, not proof by themselves.

```json
{
  "mission_id": "stable-assignment-id",
  "source": {
    "repository": "project/repository",
    "branch": "feature/branch",
    "revision": "full-commit-sha"
  },
  "tested_revision": "full-commit-sha",
  "original_acceptance": [
    {"id": "A1", "requirement": "Observable requested behavior", "status": "verified", "evidence": ["path or observed result"]}
  ],
  "checks": [
    {"name": "Focused tests", "command": "python3 -m unittest", "status": "passed", "evidence": ["actual output or log path"]}
  ],
  "failures": [],
  "unverified": []
}
```

Acceptance status is `verified`, `failed`, or `unverified`. Check status is
`passed`, `failed`, or `not_run`. Every acceptance item and check needs a
nonempty evidence list for verification. `failures` and `unverified` must
always be present, even when empty. Add actual failures and evidence gaps;
never omit them to obtain a passing gate.

Verdicts: `PASS` requires matching nonempty source/tested revisions, all
acceptance verified, at least one passed check, no failed or unrun checks, and
empty failure and unverified lists. Any observed failure or revision mismatch
is `FAIL`. Missing fields, missing evidence, unrun checks, or explicit
unverified items are `INSUFFICIENT EVIDENCE` unless an observed failure already
requires `FAIL`. Exit codes are 0, 1, and 2 respectively.
