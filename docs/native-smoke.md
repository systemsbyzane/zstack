# Native Cortex smoke procedure

This procedure demonstrates behavior in the real T3 host. It is not replaced
by the synthetic CLI tests. Use a disposable project or a non-production
assignment, and keep the same Chief and Coordinator for the complete run.

## Record the run

1. Start from the actual Chief thread and dispatch two distinct, small
   assignments to two distinct Coordinators. Record the Chief thread link,
   both assignment IDs, and both Coordinator links from tool results.
2. In the first assignment, ask for one meaningful worker outcome and require
   its Coordinator to integrate it. Use an acceptance check that will fail on
   the first integrated attempt. The Coordinator must run the real check,
   return its observed nonzero result, fix the cause, and rerun the same
   check. Record both attempts and the final integrated revision. Do not infer
   any of these events from completion wording.
3. While that first Coordinator still owns the assignment, redirect its
   approach with a concrete change. Verify from the returned thread link and
   the Chief tracker that the assignment ID and Coordinator are unchanged.
   A new Coordinator or assignment fails this step.
4. Wait for the second assignment to reach review. Confirm the Chief tracker
   contains both assignments with their real owners, phase/progress,
   verification revision, links, and current status. Confirm the first
   assignment's redirect is attached to the same Coordinator.
5. Render the exact Chief directory's sanitized projection, not a copied
   sample portfolio:

   ```sh
   python3 skills/brief-me/scripts/brief_me.py \
     ~/.codex/cortex/chiefs/<actual-chief-thread-id> \
     --output /tmp/cortex-native-smoke.html
   ```

   Inspect the output against the Chief tracker and the two actual threads.
   Verify both missions, statuses, owners, progress, verification, and links
   match. Record a discrepancy as a failure. If native preview/render tools
   are available, use them on this exact output; record unavailable tools as
   unverified rather than claiming a render.
6. Preserve the timeline and tool-returned links as the manual evidence
   record. Keep it separate from the repository. A smoke report must list each
   step, the observed result, and its evidence location; do not use keyword
   searches of skill text as a substitute for live behavior.

## Result separation

Report automated fixture tests, mocked scenarios, and this live native smoke
as separate evidence classes. A missing live run is `INSUFFICIENT EVIDENCE`;
mocked behavior cannot be reported as a live host result. This procedure does
not change Chief state or status files itself; the Chief remains their sole
writer.
