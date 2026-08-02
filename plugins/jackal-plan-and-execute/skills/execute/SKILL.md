---
name: execute
description: Executes implementation plans or drives continuous issue execution from the GitHub Issues backlog. Model-adaptive — dispatches Sonnet implementors, reviews conditionally based on risk, and parallelizes independent work. Runs autonomously until genuinely stuck.
user-invocable: true
argument-hint: "[plan-directory] [working-directory]"
---

# Execute

Two modes:
1. **Plan mode** — execute a specific implementation plan (phase files in a directory)
2. **Backlog mode** — continuously pull and execute issues from the GitHub Issues backlog until stuck

**Subagent discipline:** every Agent dispatch prompt in this skill must include
the line "Do not dispatch or invoke any subagents — do the work directly with
your own tools." Workers never spawn workers.

**Model discipline:** every `<invoke name="Agent">` dispatch in this skill must
carry an explicit `<parameter name="model">` chosen from the tier table below
(see "Model Tier Table"). A dispatch that omits `model` — leaving the harness
default / `model=null` — is a **defect**, not a stylistic lapse: it silently
abandons tier discipline (24 of 28 dispatches in the audited session ran
`model=null`). `SendMessage` continuations inherit the model of their cold
dispatch and do not take a `model` param.

---

## Harness Guidance

Resolve `.jackal/harness-guidance.md` by **walking up from the working directory to the repo root**,
reading every one found. This lets a monorepo scope overrides per module: a module-level
`.jackal/harness-guidance.md` overrides the repo-root one key-by-key (**nearest-wins**), and the
root provides the base. Single-package repos just have the one at root — same behavior as before.

```bash
# WORKDIR = the dispatch's working directory (a module dir, a worktree, or the repo root).
# Collect guidance files from repo root down to WORKDIR; later (deeper) files override earlier.
dir="$WORKDIR"; chain=""
while :; do
  [ -f "$dir/.jackal/harness-guidance.md" ] && chain="$dir/.jackal/harness-guidance.md
$chain"
  [ "$dir" = "$REPO_ROOT" ] && break
  parent=$(dirname "$dir"); [ "$parent" = "$dir" ] && break; dir="$parent"
done
printf '%s' "$chain" | while read -r f; do [ -n "$f" ] && { echo "=== $f ==="; cat "$f"; }; done
```

Apply overrides to defaults (review policy, parallel execution policy, stop
conditions). Precedence, lowest to highest: built-in defaults < Jackal Config keys < root
`.jackal/` < module `.jackal/`. If no guidance file exists anywhere in the chain, all defaults apply.

Two override keys live here:
- `implementor_continuation` (`on` default / `off`) — see "Mode 1: Execute an
  Implementation Plan" below for what it controls.
- `simple_review` (`on` default / `off`) — see "Step 5: Execute by Complexity"
  below for what it controls (whether Simple backlog issues get a default
  Sonnet review pass).

---

## Delegation Rules

The orchestrator manages state and makes routing decisions. It **never** writes code, runs project tests, or investigates the codebase for patterns.

| Do directly | Delegate |
|---|---|
| Read/write backlog state and issue docs | Code + tests → `implementor` |
| Run conflict gate git commands | Phase file generation → `planner` |
| Create/remove worktrees | Code review → `reviewer`/`reviewer-deep` (via `review` skill) |
| Decide whether and when to review | |
| Rebase, push, open PRs | |
| Update backlog state | |

If you find yourself about to write code, run `$TEST_CMD` for correctness, or grep through the codebase — stop and dispatch an `implementor` or `reviewer` instead.

**Single-named-file routing read (exception):** when, during routing/triage, an issue names exactly one explicit file path and the classification decision hinges on that file, the orchestrator MAY `Read` that one file in full to classify the issue — classification accuracy matters more than the marginal read, and a full read beats a capped peek.

**Scope guards (must be explicit):** the exception covers exactly one named file only, at triage time. It does NOT authorize: reading a second file, using `Glob`/`Grep` or any search to *find* files, reading files not named in the issue, or reading to *implement* rather than *classify*. Multi-file or search-driven reads still stop and dispatch (`codebase-investigator` / `implementor`).

---

## Orchestration Topology

**Flat is the default.** The default orchestration shape is flat: the director/orchestrator
dispatches worker agents (`implementor`, `reviewer`, `planner`, research) directly. There is no
intermediate supervisor tier between the orchestrator and its workers by default.

The **GL-488 per-phase warm-context `SendMessage` pattern** — documented below in "Implementor
Dispatch: Named Continuation" (Mode 1) — is the reference implementation of flat topology: one
named worker dispatched cold on phase 1 and resumed via `SendMessage` for phases 2..N, keeping
context warm without a supervisor tier in between.

**The middle-tier exception requires written justification.** A middle supervisor tier (an
`Agent`-holding orchestrator dispatched *by* the orchestrator — a nested supervisor) is a
deliberate exception, not a default. Before dispatching one, the orchestrator MUST write a
**one-sentence justification in the Agent dispatch prompt itself**, stating what that tier
provides that flat dispatch plus accumulated orchestrator memory cannot (e.g. genuinely
independent multi-issue fan-out beyond what parallel named workers can coordinate). A
nested-supervisor dispatch **without** that justification sentence in the prompt is a **defect**,
in the same sense the model-omission and unbacked-relay lapses are defects elsewhere in this skill
— not a stylistic lapse.

**When a middle tier IS used, R2's liveness contract applies with stricter windows.** See
"Waiting for async work" below for the watcher / `EXPECT` / `STALLED` mechanism — do not
duplicate it here. A nested-supervisor dispatch uses a **stricter (shorter) `EXPECT` window**
than a leaf worker dispatch: a mistake in a middle tier compounds down to every worker it fans
out to, so it must prove liveness sooner. (The audited sweep session's nested Opus supervisor
produced a wrong first deliverable and is where that session's "lost agent" stall arose.)

**Reconciliation with CLAUDE.md.** CLAUDE.md's rule that `jackal-supervisor` is the sole
orchestrator tier remains the default and is unchanged by this section. This topology policy is
the **documented exception** to it: flat-by-default, with the narrow, justification-gated
nested-supervisor tier above as the single sanctioned exception. The two documents agree —
CLAUDE.md sets the default, this section defines the one narrow carve-out and its guard. No new
orchestrator agent is introduced and no worker gains the `Agent` tool; the only `Agent`-holder
remains `jackal-supervisor`.

---

## Model Tier Table

Every Agent dispatch picks its model from this table. The dispatch-site
`<parameter name="model">` is authoritative — it overrides the target agent's
frontmatter `model:` for that invocation. A dispatch that omits `model` is a
defect (see "Subagent discipline" above).

| Dispatched agent | Tier | `model` param |
|---|---|---|
| `planner` | Opus | `opus` |
| `implementor` | Sonnet (default) — Haiku for mechanical slices | `sonnet` / `haiku` |
| `reviewer` | Sonnet | `sonnet` |
| `reviewer-deep` | Opus | `opus` |
| `contract-sentinel` | Haiku | `haiku` |
| `lexicon-warden` | Haiku | `haiku` |
| research (`ed3d-research-agents:codebase-investigator`) | Sonnet | `sonnet` |
| doc-render (`ed3d-extending-claude:project-claude-librarian`) | Sonnet | `sonnet` |

The supervisor/orchestrator tier is not a row here — it is the dispatching
context, not a dispatched worker (CLAUDE.md: supervisor is the sole `Agent`
holder).

> **Sentinel/warden run on Haiku by design.** As of jackal-director 1.5.0 the
> `contract-sentinel` and `lexicon-warden` agents no longer crawl the repo — a
> deterministic pre-pass (`conformance_prepass.py`) does the scanning and hands
> each agent a small evidence packet to adjudicate read-only. That bounded job
> is a Haiku job, and their frontmatter, this table, and the `jackal-director`
> dispatch sites all now agree on `haiku`. (Earlier cycles promoted them to
> Sonnet to compensate for an unbounded repo crawl that once ran 20+ minutes;
> the reframe removed the crawl, so the promotion is gone.)

### Choosing the `implementor` tier (Sonnet default, Haiku opt-in)

**Sonnet is the default implementor tier and the safe choice — when unsure, pick
Sonnet.** The orchestrator MAY drop a single phase to `model=haiku` only when the
phase is *mechanical and fully specified* — a runaway-thinking session on a
marathon Sonnet implementor was ~97% hidden thinking tokens, and a well-specified
slice does not need that reasoning budget. A phase qualifies for Haiku only when
**all** of these hold:

- The phase file names its exact files to create/modify (no discovery required).
- It carries a concrete spec the implementor executes rather than designs — for a
  UI slice that means a linked reference image and/or an existing story/component
  to mirror; for non-UI work, an unambiguous contract with no architectural
  choice left open.
- It touches **no** contract boundary, auth, payments, user data, or crypto (those
  stay Sonnet regardless — same risk surface the review tiering guards).
- It is not the integration/wiring phase that composes other phases' output.

Dense integration slices, contract changes, and anything ambiguous stay on
**Sonnet**. When the orchestrator picks Haiku, it MUST state a one-line reason in
the dispatch (e.g. `model=haiku — S4 is a self-contained view slice with a linked
reference PNG and an existing story to mirror; no contract surface`). An
unexplained Haiku dispatch is a defect in the same sense a missing `model` param
is. If a Haiku implementor stalls, produces a wrong deliverable, or its phase
turns out larger than specified, re-dispatch that phase cold on **Sonnet** (the
`-r2` fallback posture) — Haiku is an optimization for the easy case, never a
floor to grind against.

**The tier is chosen per *cold dispatch*, not mid-continuation.** A `SendMessage`
continuation inherits the model of its cold dispatch and takes no `model` param
(see "Model discipline" above), so the tier decision is made only when an agent
is dispatched cold: a fresh trunk (phase 1 or an `-r2` reset) and every leaf
(`implementor-<N>-pX`) each get their own tier choice. This maps cleanly onto the
qualifying shapes: a **leaf** phase is independent and self-contained by
construction, so it is the common Haiku candidate; the **trunk** carries warm
cross-phase context and is usually the integration spine, so it typically stays
Sonnet. Do not try to switch a warm trunk to Haiku for a single later phase —
that would require abandoning the continuation (a fresh cold dispatch), which
costs more context than the tier saves. If a later trunk phase is genuinely
mechanical enough to want Haiku, prefer scheduling it as a leaf.

### Verifying the `reviewer` tier

- **Log any case where a Sonnet `reviewer` verdict is later contradicted** (a
  bug it passed that a human or deep review then caught). Accumulated
  contradictions are the evidence to re-promote that tier to Opus. Record them
  where the project tracks review lessons (issue comment or the owning skill),
  not just in the transcript.

---

## Mode 1: Execute an Implementation Plan

**Input:** path to plan directory (contains `phase_NN.md` files)

### Process

1. List phase files, read headers only (first 10 lines each)
2. Resolve `implementor_continuation` from Harness Guidance (default `on`). This
   controls how the implementor is dispatched across phases — see "Implementor
   Dispatch: Named Continuation" below.
3. Run the dependency-aware phase scheduler:

   a. **Parse `**Depends on:**` from phase headers.** Step 1 already reads the first ~10 lines of
      each phase file; that header window now also carries the optional `**Depends on:**` line
      (the planner's phase-file schema). Parse each phase's dependency set from it. **Absent line
      ⇒ the phase depends on all lower-numbered phases** — the backward-compatible sequential
      default.

   b. **Validate before scheduling (AC1.2 surfacing).** Before dispatching anything, validate
      every `**Depends on:**` entry across all phases: each id must name a real, lower-defined
      phase in this plan; no phase may name itself; there must be no cycle. A validation failure
      is a **planner defect** — halt and report it. Do not silently ignore a malformed
      `**Depends on:**` and do not fall back to sequential execution.

   c. **Run the scheduler:**

      ```
      completed = {}                      # phase ids that have finished and been disk-verified
      loop until every phase is in completed:
        ready = { p : p not in completed AND p's depends_on ⊆ completed }
        if ready is empty and phases remain → deadlock: report (should not happen after validation)
        - Dispatch the whole `ready` set this round:
            • one ready phase continues on the warm trunk agent implementor-<ISSUE_NUMBER>
              (SendMessage if continuation active, else the cold Phase-1 dispatch) — prefer the
              lowest-numbered ready phase for the trunk so the common single-ready case is
              identical to today.
            • each additional ready phase is dispatched as a cold leaf agent
              implementor-<ISSUE_NUMBER>-pX (see "Phase-level fan-out" below) — same branch,
              non-merging transcript.
        - Await completions (use the watcher from "Waiting for async work" for any long-running
          phase; short leaf phases need no watcher — see "Phase-level fan-out" below).
        - For each returned phase, run the per-phase body below exactly as today, then move that
          phase id into `completed`:
            i.   Read the phase file
            ii.  Dispatch `implementor` per the continuation rules below (trunk) or the leaf
                 template (any other ready phase this round)
            iii. Relay a **3-line summary** of the implementor's report (files, tests,
                 commits). Keep the full report only if it flagged uncertainty or issues.
                 **Relay rule (verify-don't-trust for delegated work).** Never restate a
                 subagent's success or progress claim in your own status unless you have made a
                 **same-turn on-disk observation** that backs it (`git log`/`git diff`/reading the
                 changed file this turn) and you cite that evidence. An agent reporting "done" is
                 a claim, not a fact — this is `verification-before-completion` applied to
                 delegated work (its "Agent completed → VCS diff shows changes" / "Agent
                 delegation: Agent reports success → Check VCS diff" rows). Cite it; do not
                 duplicate it.
            iv.  Decide whether to review (see Review Routing below). If the review finds
                 **Critical** issues, mark continuation as reset for this issue (see Fallback
                 Conditions) before the next round.
      ```

   **Sequential default is byte-for-byte preserved.** When no phase in the plan carries a
   `**Depends on:**` line, every phase depends on all prior phases, so `ready` is always exactly
   the single lowest-numbered incomplete phase. The scheduler then reduces to the current
   named-continuation loop — cold dispatch on phase 1, `SendMessage` resume for phases 2..N — with
   no cold-start regression and no parallel dispatch. Fan-out engages **only** when a plan
   explicitly declares independence via `**Depends on:**`.
4. After all phases: run final review, then invoke the `finish` skill (which
   rebases if behind, pushes, and opens the PR)

### Implementor Dispatch: Named Continuation

Each issue's implementor is a **named agent**, dispatched cold on phase 1 and
resumed via `SendMessage` for phases 2..N. A resumed agent keeps its prior
transcript warm, so prompt caching applies and it does not re-read stable
files (design plan, shared helpers, unchanged source) it already read in an
earlier phase.

**Phase 1 (or any fresh dispatch — see Fallback Conditions): named cold dispatch.**

```xml
<invoke name="Agent">
<parameter name="subagent_type">jackal-plan-and-execute:implementor</parameter>
<parameter name="model">sonnet</parameter>
<parameter name="name">implementor-<ISSUE_NUMBER></parameter>
<parameter name="description">Implementing phase 1 of #<ISSUE_NUMBER></parameter>
<parameter name="prompt">
PHASE_FILE: [path to phase_01.md]
Working directory: [worktree path]

Implement this phase: read the phase file fully and follow its Context, Goal, and AC
Coverage exactly. Before writing code, invoke the `jackal-house-style:coding-effectively` skill and
follow the language sub-skill it routes you to (fall back to your own principles + project CLAUDE.md
if it isn't installed). Write code, tests where applicable, run the project's verification
commands, and commit your work.

EXPECT: commit a resumable checkpoint within `<expect-seconds>` (a watcher is monitoring this
worktree's HEAD; going silent past EXPECT triggers a STALLED recovery). If you cannot finish
within EXPECT, commit what compiles and report your honest stopping point.

**Honest stopping point.** If you stop before the unit of work is fully done — context limit,
ambiguity, a blocking dependency, or a genuine stall — commit whatever compiles and report a
**resumable, disk-truthful** stopping point: what landed on disk (cite the commit SHA and changed
files), what remains, and the exact next step. Never claim autonomous progress you cannot back
with an on-disk observation, and never imply the work is further along than the committed state
proves. A truthful "stopped here, N of M done, resume at X" is correct behavior, not a failure.

Do not dispatch or invoke any subagents — do the work directly with your own tools.
</parameter>
</invoke>
```

**Phases 2..N (continuation active): resume the same named agent via `SendMessage`.**

```xml
<invoke name="SendMessage">
<parameter name="to">implementor-<ISSUE_NUMBER></parameter>
<parameter name="summary">Continue with phase <N> of #<ISSUE_NUMBER></parameter>
<parameter name="message">
Your context from prior phases is warm — trust what you already read (design plan,
shared helpers, unchanged source) and do NOT re-read it. DO re-read any file you
modified in a prior phase, and any file a prior phase's report flagged as changed,
since your own writes changed them.

PHASE_FILE: [path to phase_0N.md]

Treat this phase file as the complete spec for this phase. Implement it, test it,
verify it, and commit on the current branch. The house-style guidance from
`jackal-house-style:coding-effectively` still applies — re-invoke it if this phase writes code in a
language you haven't touched yet this session.

EXPECT: commit a resumable checkpoint within `<expect-seconds>` (a watcher is monitoring this
worktree's HEAD; going silent past EXPECT triggers a STALLED recovery). If you cannot finish
within EXPECT, commit what compiles and report your honest stopping point.

**Honest stopping point.** If you stop before the unit of work is fully done — context limit,
ambiguity, a blocking dependency, or a genuine stall — commit whatever compiles and report a
**resumable, disk-truthful** stopping point: what landed on disk (cite the commit SHA and changed
files), what remains, and the exact next step. Never claim autonomous progress you cannot back
with an on-disk observation, and never imply the work is further along than the committed state
proves. A truthful "stopped here, N of M done, resume at X" is correct behavior, not a failure.

Do not dispatch or invoke any subagents — do the work directly with your own tools.
</parameter>
</invoke>
```

**Fallback Conditions — abandon continuation, start a fresh cold dispatch** (new
`name`, suffixed `-r2`, `-r3`, ...) when ANY of:
- The `SendMessage` continuation fails, or returns an empty or truncated
  response (same failure posture as the reviewer's Context Limit Handling in
  the `review` skill).
- A review cycle on a prior phase found **Critical** issues — the implementor's
  context may be contaminated by the mistake, so reset it rather than resuming.
- `.jackal/harness-guidance.md` sets `implementor_continuation: off` — in that
  case every phase gets a fresh named dispatch (step "Phase 1" above, repeated
  for every phase), which is exactly the pre-continuation behavior.

**Scope of continuation (per-issue, never crosses boundaries):**
- A **new issue always gets a new implementor** with its own name — continuation
  never crosses issue boundaries.
- **Parallel issues keep separate named agents** (`implementor-<issueA>`,
  `implementor-<issueB>`); their contexts and transcripts never merge. See
  "Parallel Dispatch" below — the two named-agent streams run and continue
  independently of each other.
- The **reviewer is never continued.** Every review dispatch (via the `review`
  skill) is a fresh, stateless `reviewer`/`reviewer-deep` invocation, regardless
  of implementor continuation state.

### Phase-level fan-out (Option A: warm trunk + cold leaves)

**This is the existing Parallel Dispatch model applied within one issue.** Where "Parallel
Dispatch" (below) runs `implementor-<issueA>` and `implementor-<issueB>` on **different branches /
worktrees**, phase-level fan-out runs `implementor-<N>` (trunk) plus `implementor-<N>-pX` (leaves)
on the **same branch / same worktree**. Both are: separate named agents, concurrent, non-merging
transcripts. No new concurrency mechanism is introduced.

**Trunk vs leaf:**
- The **trunk** `implementor-<ISSUE_NUMBER>` carries warm context from phase 1 and is resumed via
  `SendMessage` (per "Implementor Dispatch: Named Continuation" above). It takes the
  lowest-numbered ready phase each scheduling round.
- A **leaf** `implementor-<ISSUE_NUMBER>-pX` (where `X` is the phase number, e.g.
  `implementor-25-p3`) is a **cold** named dispatch — it does not share the trunk's transcript.
  Cold-start is acceptable precisely because a leaf phase is independent by construction (its
  `**Depends on:**` set excludes the trunk's current work), so it does not need the trunk's
  in-context output; its phase file is the complete spec.

**Leaf dispatch template** — modeled exactly on the cold Phase-1 dispatch above, changed only in
`name`, `description`, and `PHASE_FILE`:

```xml
<invoke name="Agent">
<parameter name="subagent_type">jackal-plan-and-execute:implementor</parameter>
<parameter name="model">sonnet</parameter>
<parameter name="name">implementor-<ISSUE_NUMBER>-p<PHASE></parameter>
<parameter name="description">Implementing phase <PHASE> of #<ISSUE_NUMBER> (parallel leaf)</parameter>
<parameter name="prompt">
PHASE_FILE: [path to phase_0<PHASE>.md]
Working directory: [worktree path — same worktree as the trunk]

Implement this phase: read the phase file fully and follow its Context, Goal, and AC
Coverage exactly. Before writing code, invoke the `jackal-house-style:coding-effectively` skill and
follow the language sub-skill it routes you to (fall back to your own principles + project CLAUDE.md
if it isn't installed). Write code, tests where applicable, run the project's verification
commands, and commit your work on the current branch.

EXPECT: commit a resumable checkpoint within `<expect-seconds>` (a watcher may be monitoring this
worktree's HEAD for longer leaf phases; going silent past EXPECT triggers a STALLED recovery). If
you cannot finish within EXPECT, commit what compiles and report your honest stopping point.

**Honest stopping point.** If you stop before the unit of work is fully done — context limit,
ambiguity, a blocking dependency, or a genuine stall — commit whatever compiles and report a
**resumable, disk-truthful** stopping point: what landed on disk (cite the commit SHA and changed
files), what remains, and the exact next step. Never claim autonomous progress you cannot back
with an on-disk observation, and never imply the work is further along than the committed state
proves. A truthful "stopped here, N of M done, resume at X" is correct behavior, not a failure.

Do not dispatch or invoke any subagents — do the work directly with your own tools.
</parameter>
</invoke>
```

An explicit `model` param is required (a missing one is a defect, per "Subagent discipline" above).
The template shows `model=sonnet`, the safe default; a leaf may instead be dispatched
`model=haiku` when it meets **all** the Haiku criteria in "Choosing the `implementor` tier" above
(self-contained, exact file list, a reference image/story to mirror, no contract surface) — leaves
are the common Haiku candidate. State the one-line reason in the prompt when you do. The "Do not
dispatch or invoke any subagents" line is required verbatim regardless of tier.

**Leaves are never continued across phases.** Each leaf is single-phase: it is dispatched cold for
its one independent phase and returns. If a later phase depends on a leaf's phase, that later
phase is scheduled by the orchestrator in a subsequent round (on the trunk or a new leaf) — never
by the leaf resuming itself. This keeps every fan-out decision with the orchestrator.

**Same-branch write safety.** Parallel leaf phases commit to one branch HEAD. This is safe only to
the extent that the concurrent phases are genuinely file-disjoint — which is a property you must
*check*, not assume. A phase only earns independence-granting `**Depends on:**` when its files do
not overlap the phases running concurrently with it; if two dispatchable phases are not genuinely
disjoint, they must NOT both carry it, and that is a planner defect caught by the validation in
step 3.b above. Where the phases are disjoint, commits are additive and interleaving on the same
HEAD is fine (no rebase between them — same branch).

Disjointness is **not** guaranteed by construction, because some files are mandated shared edits:
this repo's `CLAUDE.md` requires every version bump to also touch `.claude-plugin/marketplace.json`
and `CHANGELOG.md`, so any two phases that ship a version will collide there no matter how cleanly
their feature files are partitioned. Never dispatch parallel leaves that each write a ledger file
(see "Ledger files" in the Conflict Gate). Keep ledger edits out of leaf phases entirely and
serialize them into one late phase — ideally at finish time — so exactly one writer touches them. Per-phase timeout attribution across interleaved commits is explicitly
**out of scope** (leaf phases are short; noted, not solved).

**Review + verify posture is unchanged.** Each phase's work is still disk-verified via the
verify-don't-trust relay rule and routed through Review Routing exactly as in the sequential path.
Fan-out changes *when* phases run, never *whether* their output is verified. Do not weaken
`verification-before-completion`.

**Watcher.** A long-running parallel phase stream gets its own watcher via "Waiting for async
work" below — launch `scripts/worktree-watcher.sh` per long leaf/trunk stream as needed; short
leaf phases (the common case for independent tests/docs/plumbing) need no watcher and are simply
awaited. The watcher fires on any commit to the shared HEAD (per-phase attribution out of scope,
per the same-branch write safety note above).

**Topology.** Phase-level fan-out **stays flat**: the orchestrator dispatches trunk and leaf
workers directly; there is no middle tier and no worker gains the `Agent` tool. This is flat
topology (orchestrator → parallel workers), consistent with "Orchestration Topology" above, and is
**not** the justification-gated nested-supervisor exception described there.

**The orchestrator — not the implementor — makes every fan-out decision.** Workers
(`implementor-<N>`, `implementor-<N>-pX`) keep `disallowedTools: Agent`; no worker gains the
`Agent` tool; the implementor never self-dispatches parallel sub-tasks. `jackal-supervisor` remains
the sole `Agent`-holder (CLAUDE.md). The parallelism comes from the orchestrator dispatching
multiple named workers in one message, exactly as issue-level Parallel Dispatch already does —
never from a worker spawning workers.

### Review Routing

After each phase completes, decide:

| Condition | Action |
|---|---|
| Phase touches auth, payments, user data, or crypto | Full review |
| Phase is the final phase | Full review |
| Implementor's self-review flagged uncertainty | Full review |
| Phase is pure infrastructure/config | Skip review |
| All other phases | Skip per-phase review; catch issues in final review |

**Final review is always mandatory**, and it is tiered by risk:

- **`reviewer` (Sonnet)** — the default for Simple and Standard issues.
- **`reviewer-deep` (Opus)** — for Complex issues, and for any diff touching
  auth, payments, user data, crypto, or contract boundaries (files under a
  contract source — the project's contracts package or per-component contract
  files named in `docs/canon/registry.md`).

(This table governs per-phase and final review inside Mode 1's plan-execution
loop. Simple issues never enter Mode 1 — they have no plan phase — so their
review is routed directly in Mode 2 / Step 5 below; the tier choice there
matches this one: Sonnet by default, escalating to `reviewer-deep` only when
security-sensitive.)

**If `docs/canon/` exists in the repo**, also run `/jackal-director:contract-check` (the
jackal-director conformance gate) in the same message as the final review
dispatch — they're independent and run in parallel. The bar before finish is
review PASS **and** contract-check CLEAN (or FLAGGED with every flag explained
in your report).

After the final review passes, check for UI changes — `finish` will invoke `jackal-ui-verify` automatically if UI files were touched. It covers the full diff from plan start to completion.

When review finds Critical or Important issues:
1. Dispatch `implementor` with the issues list and instruction to fix
2. Re-run review
3. If same issues persist after 3 cycles → stop, report to human

Minor issues from the final review: report them, don't block.

---

## Mode 2: Continuous Backlog Execution

**Input:** none (reads from the GitHub Issues backlog)

This is the autonomous orchestration loop. The orchestrator (you, running in the main conversation) drives issues to completion without human intervention, stopping only when genuinely stuck.

### The Loop

```
while true:
  1. Read backlog state (GitHub issues)
  2. Identify unblocked issues in Ready
  3. Run conflict gate on candidates
  4. Select issue(s) to work on
  5. Execute issue (route by complexity)
  6. Finish (rebase if behind, push, open PR)
  7. Report completion (one-liner)
  8. Loop back to step 1
```

### Step 1: Read Backlog State

Read `gh_repo` and `label_style` from `## Jackal Config` in CLAUDE.md. `label_style` is `slash` |
`colon` (default **slash**) — it sets the separator in status labels. The examples below use `/`;
substitute `:` if the project sets `label_style: colon`.

```bash
gh issue list --repo "$GH_REPO" \
  --label "status/ready" \
  --state open \
  --json number,title,labels,body
```

For each candidate, parse the issue body for `Blocked by:`, `Module:`, `Complexity:`, and `In scope:` sections (the issue doc on disk is still the source for rich detail; GH issue body mirrors the same structure).

**Readiness validation — don't trust the label alone.** Before treating a `status/ready` issue as workable, confirm its body is actually scoped:
- Acceptance Criteria exist and are filled in — **not** still placeholders (`- [ ] AC1:` with nothing after the colon, or template text like `[1-3 sentences]`).
- Scope has explicit `In scope:` paths (not `[explicit file paths]`).
- Complexity is one of Simple/Standard/Complex (not the unfilled `Simple | Standard | Complex` line), and a `complexity/*` label is present.

If an issue is labelled `status/ready` but its body is still a template skeleton, **do not work it.** Report it as mislabelled (ready label, unscoped body) and skip — surfacing it so a human or the supervisor can finish scoping. A label is a claim; the body is the evidence.

Issues are grouped by label:
- `status/ready` → eligible candidates (subject to the readiness validation above)
- `status/in-progress` → currently active (don't double-pick)
- `status/paused` / `status/blocked` → skip
- closed → resolved

### Step 2: Identify Unblocked Work

Read each Ready issue's doc. Check its `Blocked by:` field.
An issue is unblocked when all its blockers are in Resolved.

### Step 3: Conflict Gate

This gate answers one question: *what files is someone else already changing?* It must enumerate
**live** branches — not name-matched ones, and not dead ones. Do not filter branches by name glob:
`<type>/<slug>` is legal without an issue number, and `feat/`, `fix/`, and `chore/` are all in the
convention, so any glob narrower than "every ref" silently under-reports and the gate never fires.

Run once, then evaluate every unblocked candidate against the result:

```bash
BASE="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')"
BASE="${BASE:-main}"
git fetch --quiet origin 2>/dev/null || true
CUTOFF="$(date -v-30d +%s 2>/dev/null || date -d '30 days ago' +%s)"
WT="$(git worktree list --porcelain | sed -n 's#^branch refs/heads/##p')"

# Local + remote refs, deduped. Remote-only branches count: a collision can come
# from a branch another machine or worktree owns and you never checked out.
for name in $(git for-each-ref --format='%(refname:short)' refs/heads refs/remotes/origin \
              | sed 's#^origin/##' | grep -vxE "HEAD|origin|$BASE" | sort -u); do
  ref="$name"
  git rev-parse --verify --quiet "refs/heads/$name" >/dev/null || ref="origin/$name"
  live=no; printf '%s\n' "$WT" | grep -qxF "$name" && live=yes   # checked out somewhere = always live
  if [ "$live" = no ]; then
    # Already merged into the base → finished work, not a collision source.
    git merge-base --is-ancestor "$ref" "origin/$BASE" 2>/dev/null && continue
    # Untouched for 30d → abandoned; report separately rather than blocking on it.
    [ "$(git log -1 --format=%ct "$ref")" -lt "$CUTOFF" ] \
      && { echo "--- stale (>30d, not blocking): $name"; continue; }
  fi
  echo "=== $name ==="
  git diff --name-only "$(git merge-base "origin/$BASE" "$ref")" "$ref"
done

# Uncommitted work in every worktree — an in-flight edit collides before it commits.
git worktree list --porcelain | sed -n 's#^worktree ##p' | while read -r wt; do
  echo "=== uncommitted @ $wt [$(git -C "$wt" branch --show-current)] ==="
  git -C "$wt" status --porcelain=v1 --untracked-files=all | cut -c4-
done
```

`merge-base ... "$ref"` (two-dot against the fork point) lists only what the branch itself changed;
`main...$branch` on a branch that has since been merged still lists its whole diff, which is how the
old gate produced false blocks on finished work while missing live work. A merged branch is *dead* —
excluded unless it is checked out in a worktree, in which case it is live with nothing new yet.

Compare live file sets against the candidate's `In scope:` paths.
- Same file touched → hard block
- Same directory, different files → soft warning (proceed with note)
- No overlap → clear

**Ledger files (named exemption).** Some files are touched by *every* change by policy, so
"same file → hard block" would block all parallel work forever. **Ledger files** are append-mostly
registries a branch edits because it shipped, not because it owns a feature:
`.claude-plugin/marketplace.json`, `CHANGELOG.md`, the `version` field of any `plugin.json`, and
lockfiles (`package-lock.json`, `pnpm-lock.yaml`, `uv.lock`, …).

An overlap **only** on ledger files downgrades from hard block to a **note**, not a silent skip —
say which ledger files overlap and that the exemption was applied, so the call stays visible. An
overlap on anything else still hard-blocks even if ledger files also overlap.

The exemption is only sound if ledger edits are **serialized late**: do not bump versions, edit
`marketplace.json`, or write `CHANGELOG.md` during implementation. Do it once, at finish time, on a
branch just rebased onto the base, so the entry is written against the current ledger state rather
than a stale copy. A branch that edits a ledger file outside its own version/changelog rows
(restructuring `marketplace.json`, rewriting `CHANGELOG.md` history) is not making a ledger edit and
gets no exemption.

### Step 4: Select Work

**Merged-PR gate (before ranking).** For every candidate OPEN issue, cross-check
merged PRs before it enters priority ordering — a squash-merge that referenced
the issue with `Refs`/`#NN` (not `Closes`) leaves it OPEN with a stale
`status/in-progress` label. Ranking a delivered issue burns a full assignment
cycle (the GL-347 failure).

```bash
# Exact signal first — catches Closes/Fixes-style closures:
gh issue view "$N" --repo "$GH_REPO" --json closedByPullRequestsReferences
# Candidate filter for Refs/#NN-style references the exact signal misses —
# raw substring search, NOT confirmation (searching "3" also matches
# "3.2.0", "#13", "#23", dates, etc.):
gh pr list --repo "$GH_REPO" --state merged --search "$N" \
  --json number,url,body,mergedAt
```

A non-empty `closedByPullRequestsReferences` confirms delivery. A search hit is
only a candidate — do not treat it as delivery confirmation until you have
opened a matched PR's title/body and seen an explicit `Closes`/`Fixes`/`Refs
#<N>` for this exact issue number (not a substring). If delivery is confirmed
by either check, drop the candidate from selection and surface it in a
**stale-open — close these** list (do not auto-close during the loop — report
it; closing is a supervisor hygiene action). Only issues with no confirmed
delivering PR proceed to priority ordering below.

Determine priority order from the `priority/*` label (`priority/high` > `priority/medium` > `priority/low`), falling back to issue number (lower = older = first) when a candidate has no priority label. Issues with no `priority/*` label sort *after* labelled ones at the same tier — flag any unprioritized `status/ready` issue so the backlog stays orderable.

If multiple candidates are unblocked and clear:
- Check for independence (no shared files, no dependency between them)
- If independent: dispatch in parallel (two implementors, two worktrees), highest-priority first
- If dependent: execute highest-priority first

### Step 5: Execute by Complexity

Read the issue doc's `Complexity` field:

**Simple** (≤1 day, bug fix, single concern) — Standard and Complex routing below
are unaffected by this:
- Create worktree
- Dispatch `implementor` directly with issue doc
- No plan phase, no design phase
- **By default, run exactly one `reviewer` (Sonnet) pass** via the `review`
  skill (tier = `reviewer`, never `reviewer-deep` for a plain Simple issue).
  Route the verdict through the existing fix loop described in "Review
  Routing" above / Mode 1's "When review finds Critical or Important issues":
  on ISSUES_FOUND, dispatch `implementor` to fix and re-review, stopping after
  3 cycles (same stop condition as Mode 1).
  - Security carve-out: a security-sensitive Simple issue (touches auth,
    payments, user data, crypto, or contract boundaries) still escalates to
    `reviewer-deep` per the existing risk rules, instead of `reviewer`.
  - **Override:** if Harness Guidance resolves `simple_review: off` (see
    "Harness Guidance" above), skip the Simple-issue review entirely unless
    the security carve-out applies — this restores the old behavior (review
    only if security-sensitive).

**Standard** (multi-file, clear ACs):
- Create worktree
- Dispatch `planner` with issue doc (it generates a mini design plan + phase files)
- Execute phases sequentially (Mode 1 above)

**Complex** (architectural decisions, ambiguous scope):
- STOP. Report: "CG-XX is Complex — needs design decisions. Run /jackal-supervisor:jackal-design-plan to start."
- Do not attempt autonomous execution of Complex issues.

### Step 6: Complete and Update

After the issue passes review, invoke the `finish` skill (or `jackal-finish-branch`
when the supervisor wrappers are in use). It rebases onto origin/main if the
branch is behind, re-verifies, pushes, and opens a PR with `Closes #N`. **Never
merge locally** — the PR is the only completion path.

Then: remove `status/in-progress` (leave the issue open — GitHub closes it when
the PR merges), update the issue doc Status → In Review, record the PR URL, and
continue the loop to the next issue — do not block waiting for a human to merge.
Keep the worktree while its PR is open (you may need to push fixups); `/jackal-supervisor:jackal-sweep`
reclaims it after merge.

### Step 7: Report

Print one line:
```
✓ #24 PR opened (#NN). Starting #25 next (also dispatching #26 in parallel).
```

### Stop Conditions

**Reinforced non-goal.** No director message asserts progress unbacked by a same-turn
disk-verified observation — even when skipping the check would be faster.

Stop the loop and report to human when:
- No unblocked issues remain in Ready/Backlog
- All unblocked issues are Complex
- Conflict gate blocks all candidates
- An issue fails review 3 times
- A genuine ambiguity needs human decision (unclear AC, missing dependency, env issue)

Report clearly:
```
Stopped: [reason]
Completed this session: CG-X, CG-Y, CG-Z
Next unblocked: CG-A (waiting for [what])
Blocked: CG-B (conflict with [branch])
```

---

## Parallel Dispatch

When two issues are independent:

```
Dispatch in single message:
  Agent(implementor, name=implementor-XX): CG-XX in worktree A
  Agent(implementor, name=implementor-YY): CG-YY in worktree B
```

Each gets its own named agent (see "Implementor Dispatch: Named Continuation" in
Mode 1) and its own continuation stream — phase 2..N of CG-XX resumes
`implementor-XX` only, phase 2..N of CG-YY resumes `implementor-YY` only. The two
transcripts never merge.

Both run concurrently. When both return:
- Review each independently
- Finish each (rebase if behind, push, PR) — higher-priority first
- If the second branch conflicts with the first's PR, note it in the second PR's
  body; after the first merges, rebase the second and force-push its branch

**Phase-level fan-out reuses this model within a single issue** — see "Phase-level fan-out
(Option A: warm trunk + cold leaves)" under Mode 1. Same-branch leaves (`implementor-<N>-pX`) are
the intra-issue analogue of these cross-issue named agents.

---

## Credential pre-flight (before long dispatches)

**Applies to the downstream project the loop is operating on, not this repo.**
If the project the loop drives deploys to or reads from AWS with SSO/STS
credentials, a dispatch expected to run **>10 min** can outlive the operator's
session and lose uncommitted work. This plugins repo itself has no AWS creds and
is never gated by this check — the snippet is guidance to emit into projects that
do use AWS.

Before any dispatch you expect to run >10 min, in a project that uses AWS creds:

```bash
# Who am I / are creds live at all?
aws sts get-caller-identity || { echo "No valid AWS credentials — tell the human to re-auth (aws sso login) BEFORE dispatching."; }

# Remaining lifetime, where obtainable. SSO sessions expose an expiry in the
# cached token; STS assumed-role creds expose Expiration. Not every credential
# type reports a machine-readable expiry — if none is available, fall back to
# asking the operator when they last authenticated.
aws configure export-credentials --format process 2>/dev/null | \
  python3 -c 'import sys,json; d=json.load(sys.stdin); print("Expiration:", d.get("Expiration","<not reported>"))' 2>/dev/null \
  || echo "Expiration not machine-readable for this credential type — confirm remaining session time with the operator."
```

**Decision rule:** if remaining lifetime `< (expected task duration + margin)`
(use a margin of at least the dispatch's `EXPECT` window), **do not dispatch** —
tell the human to re-authenticate (`aws sso login` or the project's documented
re-auth) BEFORE the dispatch starts. A dispatch launched into a soon-to-expire
session is the failure this check exists to prevent. Record the check in the
transcript (AC5.1: every >=10-min dispatch is preceded by a credential check).

---

## Waiting for async work

The watcher **augments** `SendMessage` continuation above — it does not replace it.
`SendMessage` is still the default for in-band phase-to-phase resume; reach for the
watcher only for genuinely long-running or async phases.

1. **Watcher.** Launch `scripts/worktree-watcher.sh <worktree> <signal-file>
   <expect-seconds>` as a **background task** and end the foreground turn. It
   polls the worktree's HEAD every 60s inside the background task (that internal
   poll is exempt from the sleep rule below — do not "fix" it) and wakes you only
   on a real event: `NEW_COMMIT <sha>` when HEAD advances, or `STALLED <agent>
   <window> <activity>` when EXPECT elapses with no new commit — then it exits, and
   that completion is what generates your task-notification. Your context is touched
   only on a real notification, never on a schedule.

   `<activity>` is `active` or `idle`, and it distinguishes an agent that is working
   without committing from one that has stopped moving. HEAD alone cannot tell those
   apart, and treating them alike is what makes a recovery dispatch risk two writers
   in one worktree.

2. **Hard rule — never foreground-sleep to the timeout.** The Bash tool has a
   **120s default timeout** (a foreground `sleep 120` or longer returns exit 143 /
   SIGTERM, wasting the turn). Any foreground wait you schedule must be **≤100s**,
   comfortably under the 120s ceiling. Prefer the watcher (event-driven,
   background) over any foreground sleep at all.

3. **Batched status.** Emit at most one narration per meaningful state change
   (dispatch launched; watcher fired `NEW_COMMIT`; watcher fired `STALLED`; phase
   reviewed). "Still waiting" / "checking again" turns are prohibited — if
   nothing changed, say nothing and let the watcher wake you.

4. **On a `STALLED` notification:**
   1. **Verify disk state** — inspect the worktree (git log / git status / read
      the changed files) to establish what actually landed, per
      `verification-before-completion` — never trust the absence of a commit as
      proof of no work.
   2. **Instruct commit-and-report** — `SendMessage` the named agent to commit
      whatever is done and report a resumable stopping point.
   3. **If unrecoverable, resume from disk** — start a fresh cold implementor
      dispatch seeded from the on-disk state (same posture as the Fallback
      Conditions above), never from the stalled agent's unverified claims.

   **Read `<activity>` before deciding between steps 2 and 3.** `active` means the
   working tree changed during the window, so an agent is probably still alive and
   mid-edit: use `SendMessage` (step 2) and do **not** cold re-dispatch, or two
   writers end up in one worktree. `idle` means nothing moved at all, which is
   consistent with a dead agent and makes step 3 appropriate — but confirm with a
   `SendMessage` first when the agent could plausibly still be thinking.

   A shared-credential death is fleet-wide and simultaneous, so if **you** are alive
   and your own credentials never lapsed, a single dead child died for some other
   reason and deserves the stricter check, not a faster re-dispatch. When you have
   re-authenticated after a fleet-wide credential expiry, `idle` plus your own known
   downtime is the one case where cold re-dispatch is clearly right.

   Any recovery dispatch must **commit forward only** — never `rebase`, `reset`, or
   force-push over the stalled agent's work. If the original turns out to be alive,
   the worst case is then a messy merge rather than lost commits.

---

## Worktree Management

Every issue gets its own worktree:

```bash
ISSUE="24"             # GitHub issue number (the work-unit key)
SLUG="kebab-title"
TYPE="feat"            # conventional-commit type: feat|fix|docs|chore|refactor|...

# Ensure .worktrees is gitignored
grep -q "\.worktrees" .gitignore || echo ".worktrees/" >> .gitignore

BASE="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#origin/##')"
: "${BASE:=main}"

# Create (or reuse existing)
if [ ! -d ".worktrees/${ISSUE}-${SLUG}" ]; then
  git worktree add .worktrees/${ISSUE}-${SLUG} \
    -b ${TYPE}/${ISSUE}-${SLUG} "$BASE"
fi
```

Pass the worktree absolute path to every implementor dispatch.

---

## Context Strategy

With 1M context window:
- Never /clear between issues
- Accumulated knowledge improves each subsequent dispatch
- Phase files read just-in-time (not all upfront) to avoid noise
- Implementor reports kept in context (orchestrator learns patterns)

If context genuinely runs low (>600K tokens used), summarize completed work and continue. Don't clear.

---

## Integration with Supervisor

The supervisor (jackal-supervisor agent or skills) handles:
- Creating issues, managing backlog priority
- Assigning work (conflict gate + worktree creation)
- Pausing/resuming

This skill handles:
- Executing assigned work
- Merging completed work
- Updating backlog state post-completion

They can run together: supervisor assigns, execute runs. Or execute can self-serve from the GitHub Issues backlog in autonomous mode.
