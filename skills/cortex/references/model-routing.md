# Model routing

Use this guide for Chief, Coordinator, worker, and Council model choices. The
active host's discovered capabilities and the user's task-specific choices take
precedence over defaults in this repository.

## Discover and choose

Before dispatch, inspect the active host's current provider/model catalog,
child-task support, and option values. Use exact discovered provider and model
IDs and supported option keys. A catalog entry alone does not prove that a
provider can run a child task. Recheck when the host or task context changes;
never treat an old snapshot as a live guarantee.

Prefer Codex `gpt-6.1-sol` with `reasoningEffort=medium` for the Chief and each
Coordinator. For workers, Codex `gpt-6-luna` with
`reasoningEffort=max` and Muse Wonder through Cursor are first-class peer
choices. Set Muse's exact model ID and options only after discovering them.
Choose for suitability and actual availability. Consider active assignments
and usage only when the host exposes that information. When both worker choices
are suitable and useful independent work exists, distribute work across them.
Do not favor Codex automatically, create work just to balance providers, add
extra workers only for diversity, require both providers on an assignment, or
enforce a fixed quota or 50/50 split.

If a requested or preferred provider/model is unavailable or cannot run a child
task, select a suitable alternative from the discovered catalog. This fallback
is preauthorized: record why it was needed and continue without a permission
gate when a viable alternative exists. If both peer choices are unavailable,
choose another suitable discovered provider. Report a blocker only when no
suitable, available route exists. Never invent a model ID or option from a
historical reference.

## Dispatch, receipts, and recovery

Pass the explicit provider, model, and supported options on each dispatch.
Record the requested and actual provider/model/options, the selection or
fallback reason, and the host dispatch receipt in the existing assignment
tracker/evidence. Include a capability-discovery receipt or path when it
supports the choice. Compare the returned receipt/readback with the requested
target and record the actual values the host confirms. A preference is not a
claim about the model actually running. Do not claim a current turn changed
models unless the host confirms that change.

The Chief routes each independent outcome to one Coordinator and keeps
substantial product implementation with its Coordinator. Send follow-ups,
corrections, and recoveries to the existing owner. A Coordinator may parallelize
useful independent worker outcomes and remains accountable for integration and
verification. For a meaningful failure, make an evidenced correction and
return it to the existing worker when continuity is useful. If the same method
continues to fail, reconsider suitability and use an available peer or another
materially different method. Cancel obsolete competing runs. There are no
fixed retry budgets; preserve the execution gate and require the Chief's live
receipt validation before accepting delivery.

## Current discovery and manual setup

The captured host evidence at
`/home/ec2-user/.codex/cortex/focused-v2-evidence/model-routing/host-discovery.json`
shows Codex child dispatch with explicit model/options support. It records
`gpt-6.1-sol` `reasoningEffort=medium` for the Coordinator. The attempted change
to the active Chief thread was rejected; configure an idle thread through the
host and verify its readback rather than claiming a running turn changed.
This snapshot is evidence of that discovery, not a promise about future host
state.

In that snapshot Cursor is disabled, has no discovered models, and cannot run
child tasks. Muse is also disabled with an empty model list; no Muse model ID or
Muse skill path was discovered. The historical string `muse-wonder-1.0` is not
current catalog evidence. To use this route, an operator must enable and
authenticate the installed Cursor provider in host settings, refresh/discover
its model catalog and child-task capabilities, and verify the actual Muse model
ID and option keys. Discover Cursor's skill paths/catalog separately; do not
assume it reads `~/.codex/skills`. This setup is manual and unverified here. Do
not install CLIs or change provider configuration as part of this guidance.

Native Codex files were inspected separately from this repository. At
inspection, `~/.codex/skills` contained Cortex, Cortex Coordinator, and Council
`SKILL.md` files; Dispatch, Decompose, and Recover were present in the
repository but not in that local directory. Those installed files still
contained the earlier Chief-low/Luna-only policy and fixed Sol/Muse/Luna
Council panel. A repository commit does not update these local copies. The
current invocation's supplied skill list exposes Cortex, Cortex Coordinator,
and Council, but a filesystem listing or this invocation does not prove
discovery in a fresh thread. After installing updated files, verify the actual
skill catalog in the target Codex session. The `$cortex` text is not a host
activation hook or a model-routing control.

## Council

Council is optional and risk-based, not a mandatory three-model gate. Select
reviewers based on the review question, risk, independence, and discovered
availability. Do not require a Muse seat, every provider, or a fixed panel. Use
the same explicit routing, fallback, and receipt rules above; report actual
reviewers and options, substitutions and reasons, and any limits on coverage.
A smaller viable review can proceed without calling the unavailable seat a
blocker.
