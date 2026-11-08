# Dispatching Cortex work

Read this before assigning work. Current harness instructions and available tool contracts govern orchestration; do not copy an older skill's thread-launch or wait behavior.

## Roles and tools

Use both configured subscriptions for execution work, not just for Council review. Default execution seats are Codex `gpt-6-luna` with `reasoningEffort=max` and Cursor `muse-wonder-1.0` with `reasoning_effort=high`, resolved from capabilities. Assign useful, narrowly scoped work to each provider: for example baseline/contract tracing on Codex and target-flow inspection or independent runtime validation on Cursor. They may run sequentially when dependencies require it. Do not duplicate tasks merely to fill a provider quota, and do not invent extra implementation scope. A small assignment can use one provider for the fix and the other for meaningful validation. Record actual dispatches and outcomes by provider in the tracker. Dispatch count is not a claim of equal token/cost/subscription usage. If either provider cannot execute, report the blocker to the chief and request an explicit single-provider exception; do not silently substitute or count Council participation alone as balanced execution. Later explicit user model/role choices override these defaults. The coordinator remains Sol 6.1 by preference; a skill cannot change an existing root model. Council remains Sol 6.1/high, Muse Wonder/high, and Luna/max through the personal Council skill.

In T3, discover `orchestrator_capabilities` once before the first `delegate_task`, then use the returned option names and supported values. Model settings belong in `target.options`. Re-query only after an error or a user-named provider change, following the active harness rules.

Follow the current harness boundary between native subagents and `delegate_task`. Explicit model/settings requirements, separate child checkouts, cross-provider, and background work use the supported delegation tool when required by that harness. A request for subagents is not permission to create unrelated top-level threads. Do not use `t3_thread_launch`, `create_threads`, or a CLI as a substitute for a subagent dispatch. If the required tool/model is unavailable, report the blocker.

Use tool-managed worktree isolation when a child needs a separate checkout. Do not create a child's checkout in the shell or tell its prompt to do checkout setup. For a shared task workspace, give disjoint file ownership and serialize overlapping work. Commits and pushes require their own authorization; when they are not authorized, use scoped diffs/patches or the permitted shared task workspace rather than inventing permission to commit for integration.

Follow a running task's returned `next` instruction. On a completion-wakes-parent instruction, end the turn and resume on completion. Do not poll task status or thread messages. Cancel a superseded delegate with the supported task cancellation operation; do not leave competing writers running. Review and re-check delegations are new tasks when required by the harness; implementation follow-ups must use supported task controls rather than assuming an old thread can be steered arbitrarily.

## Worker brief

Supply concrete facts, without making the worker rediscover the whole assignment:

- **Outcome and invariant:** what this slice must achieve; behavior that must survive.
- **Ownership:** exact files/modules and the integration boundary. State: “You are not alone; preserve concurrent edits and do not revert others' work.”
- **Starting context:** verified workspace/base or revision, relevant instructions, source pointers, prior decisions, reproduction, and sample inputs. Resolve unknowns instead of inventing branches, IDs, or commands.
- **Work and proof:** the narrow fix, focused product demonstration (no automated tests or coverage), real runtime evidence required, and known test/environment limitations.
- **Authority:** exactly which actions and targets are authorized; explicit exclusions. Existing authorization travels with the brief, not with the worker's assumptions.
- **Return:** changed files/diff or authorized commit SHA, checks actually run and results, evidence paths, remaining issues, and what needs integration. Do not launch more workers unless this brief explicitly asks for that.

Store long or reusable briefs under `.local/cortex/<task-slug>/briefs/` for the coordinator, but send their contents inline unless the exact path is verified readable in the child environment. An untracked file in a parent worktree is not automatically present in an isolated or remote child checkout. A path is sufficient only with verified shared access or a supported file transfer into the prepared workspace. Keep short briefs inline. No standing requirement for one PR per worker.

## Integration and review

Workers own discovery, setup, reproduction, diagnosis, slice product checks, and integrated validation/evidence. The parent only inspects their returns during those phases. After the required workers are done and results are mechanically integrated, dispatch the integrated-validation/evidence worker. Only after that worker finishes and the Cortex final-verification gate is satisfied may the coordinator run final combined acceptance checks. Do not run tests, browser steps, credential discovery, app startup, or troubleshooting in the parent before this gate, including while another worker is running or blocked. Mechanical patch application is coordination; writing new product behavior to repair an integration failure is implementation and belongs with a worker, except for a small review correction that the active higher-priority harness explicitly requires the coordinator to make. That exception retains all retesting and Council gates.

Council reviewers are read-only and separate from the implementation workers; use the personal `council` skill for panel dispatch, consensus criteria, and round budgets. Give it the exact diff/revision, acceptance conditions, relevant repository rules, and evidence already collected. Ask for concrete findings with paths/lines, reproduction or source evidence, impact, and the smallest fix. The coordinator confirms each finding before dispatching correction. After a behavior correction, Council still requires a fresh round with all three selected seats and explicit verdicts on the current revision. The evidence and review scope can narrow to changed code, directly affected paths, and open findings; a narrow scope never means fewer required seats or approval inherited from an older behavioral revision. Follow the coordinator Fast execution policy: no automated tests or coverage; use only the affected real product acceptance evidence.

A user follow-up or broad local permission is not a coordinator-role reset. Keep execution delegated; relay the clarified scope and existing authority to the appropriate worker. If a worker reports a new failure, assign diagnosis/fix instead of probing or repairing it in the parent.

Track exploratory ideas separately. Do not silently turn them into more workers or broaden the requested behavior.

## Event-driven supervision

Current T3 rules prohibit polling running delegates, including ten-minute scheduled watchdogs, sleep loops, task-status loops, and watcher agents. Do not create those schedules. Use completion notifications and explicit blocker/milestone reports. On a returned event, compare the result with the brief, acceptance, revision and ownership; steer/correct only when justified through supported task controls. Follow a running delegate's `next` instruction. If a user asks for a timed supervision guarantee, disclose that this host does not support it under current rules.

## Model policy precedence

Before dispatch, apply current host and repository model rules. If an all-Luna rule conflicts with required Cursor execution or the Council panel, report the exact conflict to the chief and wait for an explicit user override. Skill defaults do not override those rules; do not silently replace seats or claim both subscriptions were used.
