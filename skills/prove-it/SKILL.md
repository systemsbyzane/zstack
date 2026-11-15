---
name: prove-it
description: Gate successful delivery on exact source identity, original acceptance, and actual verification evidence.
---

# Prove it

For the Coordinator and Chief. Before calling a mission successfully delivered,
write the mission report using `references/mission-report.md` and run:

```sh
python3 skills/prove-it/scripts/prove_it.py mission-report.json
```

The gate must compare the tested revision to the exact source revision, cover
every original acceptance item, and show actual check outcomes, failures, and
unverified items. `PASS` is the only successful verdict. A failed check or
acceptance item is `FAIL`; missing, unrun, or unsubstantiated evidence is
`INSUFFICIENT EVIDENCE`. Either blocks successful delivery. Correct failures
and rerun affected checks, then regenerate and rerun the gate. Never edit a
verdict into the report or infer success from a worker's completion.

Return the verdict, source identity, original acceptance coverage, exact check
results, failures, unverified items, and report path. The gate verifies supplied
evidence structure; it does not independently execute or authenticate the
listed checks.
