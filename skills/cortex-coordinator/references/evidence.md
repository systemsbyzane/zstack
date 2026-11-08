# Evidence the user can inspect

The handoff is the result of real verification. Discovery/test/evidence subagents perform the hands-on flow and capture the artifacts. The coordinator specifies acceptance, checks returned evidence, and presents it. Direct parent capture or live-flow testing is permitted only as final combined verification after the Cortex gate is satisfied; responsibility for evidence is not a pretext to take over the worker’s assignment. Begin with the result and visible evidence, not a chronology of agent activity.

## Delegated validation/evidence worker: UI and interaction work

- Exercise the real application at the integrated revision. Include the relevant end-to-end journey, not just a successful initial page load. Verify persistence and downstream effects when those are part of the task.
- Capture clear screenshots of the actual affected screens, at useful sizes. Identify what each image shows and any meaningful before/after distinction. Mockups, reconstructed HTML, test fixtures substituted for the product, or screenshots of a test log do not prove a real product flow.
- Record a real walkthrough of the affected interaction. A video of the actual flow is required for UI/interaction changes unless capture is unavailable; do not silently downgrade to a static mock player or unrelated older recording. Recordings and screenshots must correspond to the change and revision being handed back. If there is no meaningful motion, a short walkthrough of the resulting screen and its primary interaction is sufficient.
- Keep captures in the repo's designated local evidence directory, normally `.local/`, and do not commit them. Preserve relevant diagnostic details without exposing credentials or unnecessary personal data.
- Test the supplied preview URL in a browser. State which local instance/port is running and what the user can inspect there. Do not present an expired URL or assume the dev server stayed alive.
- In T3, embed screenshots directly using Markdown image syntax with absolute file paths. Expose a real video directly using the supported media rendering or an obvious absolute-path file link. Give each media artifact a short descriptive label, such as “Saved requested items after reload” or “Document upload through case creation.” Use the current harness's artifact and rendering rules.
- For a larger evidence set, a small HTML review document can collect the same actual images, recording, test conditions, and links. It supplements the direct handoff; it is not another application to maintain. Do not bury the primary evidence behind expandable technical sections.

## Delegated validation/evidence worker: backend, data, and AI workflows

- Report measurements only when measured, with comparable inputs, load, environment, units, and run conditions. Distinguish a benchmark from a single observation. Include remaining uncertainty and avoid invented improvements.
- Trace data across the entire acceptance path. For document analysis, for example: real analysis response → user acceptance of suggestions → saved fields/items and quantities → downstream case/record → persistence after reload. This is an example of acceptance coverage, not permission to run that workflow in every assignment.
- Distinguish mocked tests from real provider/runtime calls. A mocked response proves the tested application behavior, not that the external model, credentials, environment routing, or live integration works.
- Identify which environment and configured identity were used without revealing secrets. Report blocked credentials or unavailable provider access as unverified coverage, not as successful analysis.
- An HTML report, chart, or concise table is useful when it makes actual measurements easier to assess. Attach relevant request traces/log excerpts only as supporting evidence; do not dump secrets or whole transcripts.

## Final handoff shape

Scale this to the task; keep it short:

**Ready for your review:** what changed and what was demonstrated.

Show the actual screenshots and walkthrough, then provide the working local URL if applicable.

**Verified:** the meaningful scenarios/checks and measured results; tested revision or identifiable local snapshot, including uncommitted changes when relevant.

**Still open:** missing acceptance proof, limitations, and the precise user decision. Omit this category when nothing is open. Acceptance of the demonstration does not itself authorize a merge or deployment.

If essential real-flow verification is blocked, label the handoff **Blocked** or **Partially verified** and explain the specific missing evidence. Do not call it complete and quietly transfer the required verification to the user or silently have the coordinator do a blocked worker’s testing outside the final-verification gate.
