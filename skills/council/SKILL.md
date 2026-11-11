---
name: council
description: Run independent advisory review through the user's configured Council models when Council is requested or appropriate, then synthesize evidenced findings and verify justified corrections.
---

# Council

Use independent review to answer the actual scoped question, not as an automatic gate on every Cortex assignment. Cortex coordinators own integrated review and can perform integration/testing directly. User task authority and explicit panel overrides persist.

Default panel when Council is invoked: Codex `gpt-6.1-sol` high; Cursor `muse-wonder-1.0` high; Codex `gpt-6-luna` max. Resolve actual provider/model IDs and option keys through capabilities. A catalog entry is not authentication proof. Do not silently replace specifically requested seats or claim full Council approval when a seat is missing. Respect user-authorized single-provider review and disclose the actual reviewers.

Give each reviewer the task intent, exact frozen revision/artifact/diff, relevant repository rules, acceptance, actual checks, known limits, and a clear review question. Reviewers are read-only: no source changes, commits, pushes, cloud/database mutations, secrets, external messages, or nested delegation. Follow host concurrency and tool rules; use a fresh delegated task for every review/recheck. Do not poll. Preserve source identity while reviewers run.

Ask for APPROVE, CHANGES, or INSUFFICIENT EVIDENCE tied to the reviewed scope; findings with stable IDs, severity, file/line or artifact evidence, impact, smallest correction, checks actually performed, assumptions, and counterarguments. A source deduction must not be represented as an executed reproduction. Require relevant evidence, not unrelated suites or coverage. Synthetic diagnostic experiments may proceed before shipping approval within task authority; clearly distinguish experiment admission from release readiness.

Synthesize findings against evidence. Verify consequential counterexamples before enlarging implementation. Fix small findings directly when host rules require; otherwise route substantive corrections to the technical owner. Run affected verification and use new review tasks for changed behavior where needed. Do not grow a general parser/framework merely to answer speculative cases outside scope.

There are no arbitrary mandatory review-round renewals. Keep review proportional to risk and progress. If repeated reviews expose the same architectural failure, stop the loop, reassess the approach, and choose a materially different viable path; do not merely dispatch another near-identical round. Explicit task hard limits remain binding.

Report actual models/options, exact revision, reviewer verdicts, confirmed fixes, declined findings with reasons, disagreements, and missing evidence. Full panel approval requires all actual seats to approve the same revision; a smaller authorized review is labeled as such. Review does not authorize unrequested publication, merge, or deployment and does not replace requested runtime/accuracy/video evidence.
