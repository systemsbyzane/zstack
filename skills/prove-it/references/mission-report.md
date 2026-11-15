# Trusted execution plan and receipt

The execution plan is an explicit local authorization input. Store it outside
the repository after the final source commit. The runner executes only each
check's `argv` array, in listed order, with `shell=False`. It does not execute
mission report or receipt commands. Keep the plan controlled by the task
owner; a command such as `sh -c ...` is still a command explicitly authorized
by that plan.

```json
{
  "schema_version": 1,
  "mission_id": "assignment-42",
  "acceptance": [
    {"id": "A1", "requirement": "The integrated behavior works"}
  ],
  "checks": [
    {
      "id": "focused-suite",
      "name": "Focused production-path suite",
      "argv": ["python3", "-m", "unittest", "discover", "-s", "tests", "-v"],
      "cwd": ".",
      "acceptance_ids": ["A1"]
    }
  ]
}
```

Use the runner and Chief validator documented in [the prove-it skill](../SKILL.md).
The generated receipt records Git-derived repository/worktree/branch/revision,
automated argv and exit results, stdout/stderr files and hashes, acceptance
coverage, manual observations, and before/after cleanliness. A current clean
worktree and exact revision are required. Tracked and untracked changes
invalidate delivery validation.

Optional manual evidence is a separate JSON array, for example:

```json
[
  {"acceptance_id": "A2", "observed_by": "Coordinator", "observation": "Observed redirect retain the same Coordinator link in the live thread."}
]
```

Manual observations are self-reported. The receipt is not signed and does not
claim cryptographic authenticity. This workflow records local execution and
detects source drift; it cannot guarantee host instruction compliance.
