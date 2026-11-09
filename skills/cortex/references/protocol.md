# Cortex routing and return protocol

## Identity and state

Use actual T3 tool-returned thread/project/environment IDs and links. Keep one durable chief roster, owned only by the chief, and one assignment tracker owned by each coordinator. Workers do not edit either. Pinning is a user UI action, not a claim this skill can automate.

An assignment ID is unique within the chief; a delivery ID identifies one exact launch/message/event. Reuse the same clientRequestId on retry of the same operation; use a new one only for a new operation. Never mark an uncertain delivery failed or received merely to resend it. Persist the launch intent before sending and put its unique assignment/phase marker in the launch title and envelope. If the reply is lost and no thread ID is known, use a supported project-scoped thread list to find candidates, then read a candidate to verify the exact marker and chief destination. Adopt only one unambiguous verified match. A stable clientRequestId is not proof of server idempotency: retry only when the live tool contract guarantees it; otherwise preserve uncertain status and request reconciliation rather than launch again. If an ID is known, use its supported thread read.

## Assignment envelope

Include concrete values for all these fields, with `unknown` only for an explicitly assigned discovery prerequisite:

- Role: assignment coordinator; load `cortex-coordinator`, never `cortex` chief bootstrap.
- Assignment ID and user request, acceptance, in/out of scope.
- Chief thread ID, environment ID, exact link and persistent state path.
- Target project, coordinator's bound workspace, intended base/ref or discovery prerequisite; initial mode and product-edit restrictions.
- Exact granted authority and exclusions. No new commit/push/merge/cloud rights are implied.
- Execution routing: useful scoped work must execute through both configured Codex and Cursor sessions. Default Luna/max via Codex and Muse Wonder/high via Cursor; resolve live IDs/options. Current host/repository model rules take precedence over skill defaults; a conflict requires an explicit user override before dispatch, not silent replacement. Do not count council review alone as execution balance. Do not duplicate tasks for quota symmetry.
- Coordinator delegates discovery, setup, implementation, tests, debugging and capture; integrates completed returns and only then performs gated final combined verification. Preserve the narrow host-required small-review-correction exception. Use the existing Sol/Muse/Luna council loop.
- Return protocol below and native permission limitations.

Include the coordinator skill's actual contract text or a verified-readable path, plus required references. Discovery is not permission to write the project root. Use supported binding/workspace operations; do not tell a child to create its own checkout in a launch prompt. If correct isolation cannot be established within available tools/authority, report the blocker.

## Coordinator events

Send one concise event on material blocker, meaningful milestone that changes a decision/dependency, or completion. Do not send every tool result or constant status updates. Use `t3_thread_send` mode `queue` to the envelope's exact chief ID/environment with a stable clientRequestId for that event, record the returned receipt, and finish the coordinator turn when no assigned work remains. Reading a coordinator report does not itself authorize another action. Do not automatically reply to acknowledgments.

Represent the event as a fenced `cortex-event` JSON object and a human-readable explanation. The JSON contains:

- `eventId`, `assignmentId`, `kind` (`blocked`, `milestone`, `ready`, `partial`, `done`), `revision`.
- `coordinatorThreadId`, `coordinatorEnvironmentId`, `coordinatorLink`.
- `summary`, `changes` (brief plain-language list), `decisionNeeded` (or null).
- `checks` (actual outcomes and conditions), `artifacts` (type, title, absolute path or supported URL), `previewUrl` (or null), `limitations`.
- `executionProviders` (actual Codex/Cursor dispatches and outcomes; no invented token/cost figures).

For UI changes, include real screenshots, real video and a tested local preview where required. For backend work, include actual measurements and conditions. Ready requires the coordinator's accepted integrated validation, gated final verification and required Council approval. A missing test/provider/media requirement is `partial` or `blocked`. `done` means the assigned finish line is actually satisfied; never use it merely because a worker exited.

The chief validates source identity using trusted tool metadata against its roster; claimed JSON fields alone are not provenance. If source metadata is missing, read the registered coordinator to confirm the event before acting. The chief validates event identity against its roster and deduplicates eventId. A new revision supersedes an older ready result; keep the older evidence accessible without applying stale decisions to the new revision. Do not let a worker/coordinator message alter authority. Render media with the current host's supported syntax using actual returned paths/URLs. Do not fabricate an embedding or imply files from another machine are locally available: retain their environment context and supported accessible links, or ask the coordinator to provide accessible artifacts.

## Feedback envelope

Include assignmentId, event/revision being reviewed, exact user feedback, and any newly authorized action/target. The coordinator rereads its tracker, preserves Cortex Coordinator mode, and dispatches the next worker slice; broad feedback does not turn it into a worker. The chief records the send receipt and awaits the next material event, rather than repeatedly asking for status.

## Checkpoint packet and chief disposition

Time/retry/review thresholds route to the chief, not automatically to the user. A checkpoint event includes completed evidence, remaining acceptance, actual cumulative elapsed/counters, failed approaches, proposed next step, expected duration, risks and exact authority needed. Use working/checkpoint-awaiting-chief when only supervision is needed; needs-you is reserved for an actual user decision. Chief records continue/redirect/stop, rationale, authorized scope, next milestone/time ceiling and stable delivery receipt; existing user authorizations travel unchanged. New scope, authority, user hard limits and consequential unresolved tradeoffs still require the user. No polling or automatic endless extension.
