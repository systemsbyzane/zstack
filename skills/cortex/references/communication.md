# Clear task communication

Apply this to chief-to-coordinator messages, coordinator-to-worker briefs, direct worker handoffs, and result reports. Write for a capable colleague who must act without guessing.

## Initial assignment

Lead with the requested outcome and phase order. Include only context needed to execute this assignment:

- **Outcome:** the concrete result to deliver and why it matters.
- **Starting point:** accessible workspace/revision, current phase, verified setup, and relevant source or artifact pointers.
- **Ownership and authority:** who owns files/runtime, what work is authorized, and task-specific boundaries that affect this assignment.
- **Acceptance:** observable behavior, checks, measurements, and deliverables required for completion.
- **Return:** useful results/evidence, unresolved issues, and genuine decisions. Ordinary recoverable errors remain with the owner.

Use these as a content guide, not mandatory headings or boilerplate. A simple task needs only a short paragraph. A complex task may need more detail, but put the essential action first and organize it in readable paragraphs or a short list.

Use normal spaces, punctuation, complete sentences, and exact identifiers. Never compress prose into joined words, all-caps constraint streams, or semicolon-packed status dumps to save tokens. Preserve code, hashes and paths literally when needed, but explain their purpose.

## Put detail in its proper place

Keep durable phase order, authority, known runtime facts, issue history, accounting, and prior evidence in the assignment tracker. Reference the exact relevant section/file when the recipient can access it. Do not paste the full migration history, every previous failure, all model rules, the complete ledger, or a roster of obsolete hashes into each brief.

A new worker has no assumed parent history. Supply the necessary starting facts and verify that referenced context is accessible. Do not make it reconstruct the task from a directory dump. Keep secrets and restricted evaluation material out of prompts and shared trackers; use authorized private channels and access boundaries.

Include a checksum inline only when identifying the exact artifact is material to this action. Otherwise point to its manifest. Accounting belongs in the ledger; include a limit in a brief when it constrains that worker, with a clear remaining allowance and counting unit. Do not repeat historical arithmetic in routine messages.

## Follow-ups are changes, not rebriefs

State what changed, the evidence/reason, and the resulting next action. Explicitly supersede the conflicting prior instruction if there is one. Do not repeat the entire original envelope or resend unchanged instructions. The assignment owner maintains one current instruction in its tracker so late messages cannot resurrect obsolete holds or targets.

Use one owner for execution decisions. Technical contributors report a new defect or artifact withdrawal; the coordinator resolves its effect on execution. They should not create competing generic hold/proceed approval chains. Urgent stop or artifact-integrity information must be delivered immediately and acknowledged with actual execution state when necessary. This exception is for real control conflicts, not routine acknowledgment loops.

## Results are understandable facts

Lead with the outcome, then evidence, remaining work, and any real blocker. Distinguish completed work, active work, planned work, and unknown status. Include the tested revision and artifact links when they help assessment. Keep machine event IDs and accounting in structured metadata/tracker rather than turning the human explanation into compressed JSON prose. Supported protocol fields may accompany a concise readable explanation.

Before sending, check: can the recipient identify the next action, starting point, owner, and finish line on one read? Are critical facts accessible? Does anything contradict an earlier instruction that needs explicit supersession? Remove irrelevant repetition. Do not impose arbitrary word limits that omit essential context.

## Example

Initial worker brief:

> Run the 180 development LOR packages through the pinned feature baseline and preserve each analysis result, including failures. The baseline API is healthy and runs analysis inline; use the existing runtime and batch manifest. You own the batch and routine recovery. Keep the 120 holdout packages sealed. Report completed, failed, and remaining counts at material milestones, then return the frozen results for independent scoring. The task tracker contains the exact revision, source paths, call ledger, and credential-handling instructions.

Follow-up:

> The API is confirmed healthy and the batch runner has not started. Start the existing runner now. This supersedes the earlier Temporal-poller readiness requirement: this baseline uses inline analysis. Preserve the current manifest and completed records.

The examples illustrate communication, not universal environment settings or permission to run those actions on unrelated tasks.
