# Changelog

## [jackal-hook-credential-preflight] 1.0.0

New plugin. Warns before an agent dispatch when the harness's own AWS SSO token cannot survive it.

Motivation: an investigation of ~20 dead subagents (2026-07-17 → 07-31) found the dominant failure mode was not what it looked like. The intuitive diagnosis — implementors not committing often enough — is wrong: **no code was lost in any traced incident**, because worktree files survive process death and recovery succeeded every time. The actual cause is that every agent on Bedrock authenticates through *one* cached SSO token, so its expiry kills the entire fleet simultaneously. In session `558791f0` the subagent died at `07:40:37` and its parent at `07:40:38` — the orchestrator cannot run its own stall-recovery logic because it is dead too. The existing pre-flight in `jackal-plan-and-execute/skills/execute/SKILL.md:776` explicitly scopes itself to "the downstream project the loop is operating on, not this repo," so it never checked the credential that does the killing.

**New:**
- `PreToolUse` on `Agent|Task`: warns when the harness's SSO token is expired, when it lacks a `refreshToken` and its remaining lifetime is shorter than the dispatch's declared `EXPECT: ... within <n>m` duration, or when the SSO client registration is within 3 days of expiring (registration expiry defeats refresh).
- Reads `~/.aws/sso/cache` and `~/.aws/config` only — no STS calls, no network, and no token values read or logged. Locates the exact token via `sha1(<sso-session name>)`, walking `source_profile` hops (`DevOps_EDRC-Dev` → `AWS_DevOps_EDRC-Dev` → `HCG-SSO-DevOps`) because only the last hop names the session.
- Treats a refreshable token with minutes left as healthy and a non-refreshable one as at risk. AWS's legacy inline-`sso_start_url` config format issues no refresh token — per AWS docs, "Automated token refresh isn't supported using the legacy non-refreshable configuration" — so the distinction decides whether short runway matters at all.
- Advisory by default (`additionalContext`, not `deny`): only the operator can run an interactive `aws sso login`, so the message names the operator as the actor rather than telling an agent to retry. `JACKAL_PREFLIGHT_BLOCK=1` makes it fail closed; `JACKAL_PREFLIGHT_DISABLE=1` silences it; `JACKAL_SSO_SESSION` overrides session detection.
- Inert unless `CLAUDE_CODE_USE_BEDROCK=1`, and silent on missing cache, unparseable timestamps, or any internal error — an advisory check that breaks a dispatch is worse than one that misses a warning.
- `test-check-credential-preflight.py` — 23 tests over real temp `HOME` trees with real `~/.aws` files (no mocks, no pytest), wired into CI and `test_cmd`.

## [jackal-hook-branch-guard] 1.0.0

New plugin. Makes "the PR is the only completion path" fail closed instead of relying on prose.

Motivation: `e487c29` was substantive feature work authored and pushed directly to `main`. The agent ran `git branch --show-current`, saw `main`, and proceeded anyway — 12 edits, a commit, a `CHANGELOG.md` rebase conflict resolved in place on the trunk, then `git push origin main`. Fifty-five minutes later the same session quoted the rule correctly and branched. A rule followed inconsistently is a rule with nothing enforcing it.

**New:**
- `PreToolUse` on `Edit|Write|NotebookEdit`: denies the write when the *target file's* repository has `HEAD` on a protected branch (`main`/`master` by default, `JACKAL_PROTECTED_BRANCHES` to override). Resolves the branch per-file, so a worktree checked out to a feature branch stays writable even though the primary checkout sits on `main`.
- `PreToolUse` on `Bash`: denies `git commit` / `git push` when the cwd's `HEAD` is on a protected branch. Tokenizes with `shlex` and splits on operator boundaries, so `echo "git commit"` and `git commit --help` do not trip it.
- Allowlisted by design: gitignored and untracked paths, anything outside a git repo, scratch prefixes (`/tmp`, overridable via `JACKAL_SCRATCH_PREFIXES`), `.git/` internals, and all read-only git commands.
- Escape hatch: `JACKAL_ALLOW_MAIN_WRITES=1`, named in every block message alongside the `git switch -c <type>/<slug>` remedy.
- `test-check-branch-guard.py` — 82 tests over real `git init` fixtures (no mocks, no pytest), wired into CI and `test_cmd`.

## [jackal-supervisor] 3.5.0

Finish the job `3.4.0` started: bookkeeping no longer dirties the trunk, and the conflict gate actually enumerates live branches.

**Fixed:**
- Planning bookkeeping no longer writes to tracked files on `main`. `3.4.0` removed the bookkeeping *commits* but kept the *writes* — and `docs/issue-docs/` is tracked, so every assignment left the trunk modified. Worktree/status state now lives in gitignored `.jackal/state/`.
- Removed a claim that could not work: the issue doc "rides along on the feature branch when the design/impl commits land inside the worktree." The edit was in the repo-root working tree; a worktree is a separate checkout and cannot see it. Replaced with an accurate statement of where state lives.
- Conflict gate rewritten. The old `git branch --list 'feature/*' '*/[0-9]*-*'` matched 1 of 4 local branches (the convention is `feat/`, not `feature/`, and `<type>/<slug>` is legal without an issue number) — so "same file → hard block" silently never fired. It also diffed `main...$branch`, which still lists a merged branch's whole diff, producing false blocks on finished work. Now enumerates all local *and* remote refs via `git for-each-ref`, excludes branches merged into the resolved base, diffs from the merge-base, reports >30d branches as stale rather than blocking, and surfaces uncommitted work in every worktree.
- **Ledger-file exemption.** `.claude-plugin/marketplace.json`, `CHANGELOG.md`, `plugin.json` version fields, and lockfiles appeared in 19 of 22 branches and 12 of the last 12 commits — because `CLAUDE.md` mandates them. Under "same file → hard block" that made correct parallel work permanently blocked. An overlap *only* on ledger files downgrades to a visible note; an overlap on anything else still hard-blocks.

**New:**
- `jackal-sweep` reconciles `git stash list`, so parked work cannot be silently orphaned. Reports for the user to decide; never auto-drops or auto-applies.

## [jackal-plan-and-execute] 3.12.0

Reviewers can no longer mutate the tree they are reviewing, and the parallel-safety claim is honest.

**Fixed:**
- `reviewer` / `reviewer-deep` are now structurally read-only: `disallowedTools: Agent, Edit, Write, NotebookEdit`, plus an explicit never-mutate rule in each body (per `CLAUDE.md`, frontmatter has known enforcement gaps, so the prompt-level rule is belt-and-braces). A reviewer was observed `cp`-ing an old revision over the file under review six times to A/B it, while the main agent was committing that same file — it restored correctly each time, but one crash inside that window silently reverts the file under review.
- `Bash` stays available, because reviewers legitimately need to run tests. They are now given the sanctioned pattern instead of a blanket ban: copy to a scratch dir under `/tmp` and experiment there, never `cp` over a tracked file, never `git stash`/`checkout`/`reset`.
- `review` dispatch template repeats the never-mutate prohibition inline, matching how the no-subagent rule is already handled.
- Corrected the claim that parallel leaf phases are safe "because independent phases are disjoint by construction." That premise is false by policy in this repo, where every change touches the mandated ledger files.

## [jackal-plan-and-execute] 3.11.0

Close the reviewer's remaining gaps from the code-reviewer consolidation review: a false-positive bar on findings, broader security bullets, and independent verification that UI phases actually ran their visual gate.

**Changed:**
- `reviewer` (step 3): new reporting bar — findings must be verified against the actual code (not pattern-matched from the diff), every Critical/Important finding requires a one-line failure scenario (concrete input/state → wrong behavior; no scenario → downgrade or drop), and repeated instances consolidate into one finding. Rationale: each false positive costs a full fix-and-re-review cycle.
- `reviewer` (step 3): security bullets extended with path traversal, XSS, secrets/PII in logs, unvalidated trust-boundary input; missing timeouts on external calls added under Important.
- `reviewer` (step 3): visual-gate verification — a UI phase whose implementor report is silent on the per-slice visual gate (no rendered/screenshot/reference-compare outcome and no surfaced capability gap) is an Important issue, same class as a missing test-report artifact. The reviewer checks the claim; live re-rendering stays with `jackal-ui-verify`.
- `reviewer-deep` (rules): same reporting bar and UI visual-gate outcome check, stated at this tier.
- `review` (dispatch template): optional `UI_PHASES` line so the orchestrator tells the reviewer which phases need visual-gate outcome checks and which reference images they cite.

**New:**
- `docs/reports/2026-07-23-code-reviewer-consolidation.md` — workstation code-reviewer inventory verdicts (retain the jackal reviewer pair; delete the ECC user-level agent and marketplace), reconciliation notes against 3.10.0, and remaining machine-side actions.

## [jackal-supervisor] 3.4.0

Stop planning/bookkeeping commits from landing on `main`. Worktree assignment and issue status are backlog metadata; the backlog is GitHub Issues, so the durable record is the issue comment + label, and git itself is the authority for what worktree exists.

**Changed:**
- `jackal-design-plan` (Step 3) and `jackal-impl-plan` (Step 2, Standard path): no longer `git commit` the issue-doc / `## Worktree` block on `main`. The `## Worktree` block is still written to disk (uncommitted) as a same-session convenience; the assignment is recorded in GitHub via the existing issue comment + `status/in-progress` label.
- `jackal-impl-plan` (Step 2): worktree resolution now asks **git** (`git worktree list`) for the issue's worktree first, falling back to the on-disk doc block — git is authoritative for what exists on disk, so a committed doc block is no longer needed.
- `jackal-pause-session` (Step 6): no longer commits a `chore: pause …` checkpoint on `main`; the checkpoint lives in the GitHub issue comment + status label (Step 5) and the issue-doc edit stays uncommitted.

**Fixed:**
- Root cause of the `chore: assign worktree for #N` / `docs: issue doc + worktree for #N` / `chore: pause …` commits accumulating directly on `main`'s trunk (~one per issue). These were leftovers from the file-based-backlog era; with GitHub Issues as the backlog they were redundant bookkeeping.

## [jackal-plan-and-execute] 3.10.0

Wire the house-style coding skill into implementation so it actually fires, and depend on it explicitly.

**Changed:**
- `implementor` (step 2) now invokes `jackal-house-style:coding-effectively` before writing code and follows the language sub-skill it routes to; falls back to its inline principles + project CLAUDE.md if the plugin isn't installed, and defers to a project CLAUDE.md on conflict.
- `execute` dispatch prompts (cold Phase-1, leaf, and continuation) repeat the coding-effectively invocation instruction — belt-and-braces, matching the repo's prompt-level reinforcement pattern.
- Adds `jackal-house-style` to `jackal-plan-and-execute`'s `requires`.

**Fixed:**
- `coding-effectively` (`user-invocable: false`, auto-trigger only) had no wiring into the dispatched implementor's fresh context, so it silently stopped firing during dev cycles. A prior upstream `REQUIRED SKILL: coding-effectively` hardcode was removed in favor of "dynamic activation" that never actually reached the worker; this restores an explicit, resilient invocation path.

## [jackal-plan-and-execute] 3.9.0

Front-end fidelity and implementor cost/speed: catch visual defects per-slice instead of at end-of-epic, give implementors a rendered target to match, and let well-specified mechanical slices run on Haiku.

**New:**
- **Per-slice visual gate** (`implementor`): UI phases must render the built view/story via the Playwright MCP browser, screenshot it, compare against the phase's reference image, and fix visible defects (occlusion, overflow, wrong spacing, incoherent numbers) *before* committing. A "green" unit test no longer counts as a verified UI phase.
- **Reference screenshots at design time** (`design`): FE features with a static prototype/packet now render it once and commit reference PNGs to `docs/design-plans/assets/<slug>/`, so implementors translate against a rendered target rather than raw prototype source.

**Changed:**
- **Implementor model tiering** (`execute`): Sonnet remains the default and safe choice, but the orchestrator may drop a fully-specified mechanical slice to `model=haiku` (exact file list, a linked reference image / story to mirror, no contract surface, not the integration phase) with a one-line justification. Dense/ambiguous/contract slices stay Sonnet; a Haiku stall re-dispatches cold on Sonnet.
- **Paste-don't-point** (`planner`): phases that depend on a region of a large source file must carry the extracted excerpt inline (with source path + line range), not an instruction to go read lines X–Y.
- **Fixture-first ordering** (`planner` + `design`): the canonical fixture/demo dataset is identified and scheduled as an early phase the view phases depend on — views are never developed against empty data.

## [jackal-director] 1.5.0

Reframe the conformance gate around a deterministic pre-pass so it stays cheap and bounded; re-enable the sentinel and warden as read-only adjudicators; pin every director agent's model at its dispatch site.

**New:**
- `scripts/conformance_prepass.py` — a stdlib-only, no-model pre-pass run by `/contract-check`. It computes the branch diff, enforces a hard size cap (ESCALATE before any agent runs), parses the Component Map + glossary, runs the fully-deterministic checks (C1 impact-statement-present, C3 cross-component imports, C5 breaking-change-without-ADR), and emits a bounded JSON evidence packet. Verified against the real monorepo `docs/canon/registry.md` (12 components, including multi-line cells). Tests in `scripts/test_conformance_prepass.py`.

**Changed:**
- `contract-sentinel` and `lexicon-warden` are re-enabled but rebuilt as **read-only adjudicators**: their only tool is `Read`, they receive the evidence packet inline, and they never grep/git/crawl the repo. This structurally prevents the repo-wide scans behind the original runaway.
- `contract-check` now runs the pre-pass first, ESCALATEs on cap breach or missing registry, and otherwise dispatches both agents on Haiku with the packet pasted into each prompt.
- `registry-drift-checker` gains a hard work budget (≈2 tool calls per contract source, ≤25 total; ESCALATE rather than grind) — it keeps `Bash` because it must run schema exporters, but can no longer run unbounded.
- Every director command dispatch now sets `<parameter name="model">` explicitly (`director-packet` → delta-scribe/drift-checker = haiku; `director-review` → director = opus; `contract-check` → sentinel/warden = haiku). Previously these omitted `model`, so agents silently inherited the parent session model regardless of their `haiku` frontmatter.

**Fixed:**
- Second runaway found by audit: `registry-drift-checker` had a worst observed run of ~29 min / 95 tool calls / ~23.6M cache-read tokens — worse than the lexicon-warden run that started this — caused by the same dispatch-site model omission plus an unbounded per-component Bash loop.

## [jackal-plan-and-execute] 3.8.0

Add self-monitored work budgets to the implementor and reviewer so a single dispatch can't grind into a runaway.

**Changed:**
- `implementor` gains a "Work Budget" section: recognize runaway symptoms (re-reading files already read, re-running the full suite to explore, a phase far larger than its file implied) and take an honest, resumable stopping point instead of pushing through. Complements the existing commit-early / honest-stopping-point discipline.
- `reviewer` gains a "Work budget" note in its verify step: run the touched-area tests once, never re-run the suite to explore, and return `BLOCKED` on inconclusive verification rather than grinding. Full-suite runs remain the deep reviewer's responsibility.
- Motivated by the cost audit that accompanied the jackal-director 1.5.0 reframe: `reviewer`/`implementor` were the REVIEW-tier long tails (unbounded suite runs / no work cap), distinct from the sentinel/warden runaways.

## [jackal-plan-and-execute] 3.7.0

Reconcile the Model Tier Table with the jackal-director conformance reframe.

**Changed:**
- `contract-sentinel` and `lexicon-warden` are now tiered **Haiku** (were Sonnet). The reframe removed their repo crawl — they adjudicate a pre-computed evidence packet read-only — so the Sonnet promotion that compensated for the crawl is gone, and frontmatter, tier table, and director dispatch sites all agree on haiku.
- Replaced the now-stale "downgraded tier" verification note with a `reviewer`-only version.

## [jackal-director] 1.4.1

Temporarily disable the `contract-sentinel` and `lexicon-warden` conformance
agents pending a cost fix.

**Changed:**
- `contract-check` no longer dispatches either agent; it reports that the gate is temporarily disabled and stops.
- Both agent definitions carry a `TEMPORARILY DISABLED` banner instructing them to emit a single `DISABLED:` line and stop if invoked directly (belt-and-braces with the command-level guard).

**Fixed:**
- Runaway cost: an uncapped `lexicon-warden` run consumed ~14.6M cache-read + ~168K output tokens over 23 minutes (84 sequential greps), and both agents ran on `claude-sonnet-5` despite `model: haiku` frontmatter. Disabling stops the bleed while a scoped/capped/Haiku-enforced rework is designed.

## [jackal-plan-and-execute] 3.6.0

Test-artifact verification to cut redundant full-suite runs (#24, R8).

**New:**
- Implementor emits an optional per-phase test-report artifact (worktree-local, gitignored; `--junitxml`/JUnit XML shown as the canonical example, format-agnostic) — downstream-project guidance; skipped when the suite is trivial.
- Reviewer verifies the artifact by cross-checking it against its own targeted re-run of touched-area tests; the one full independent suite run is reserved for the deep/final review.

**Changed:**
- Verify-don't-trust reasserted: review never accepts a test-report artifact in place of its own independent verification — the artifact is an optimization, not a substitute.

## [jackal-plan-and-execute] 3.5.0

Dependency-aware phase fan-out: independent phases run in parallel; sequential stays the default (#25, R9).

**New:**
- `planner` phase-file template gains an optional `**Depends on:**` (`depends_on:`) field: a phase lists
  the prior phase ids that must complete before it may start. Absent ⇒ depends on all prior phases ⇒
  strictly sequential, exactly as before (backward-compatible). A malformed `depends_on:` (non-existent
  phase, self-reference, or cycle) is declared a planner defect the execute skill must surface.
- `execute` skill Mode 1 generalizes "for each phase sequentially" into a dependency-aware scheduler:
  it tracks completed phases and dispatches every phase whose `depends_on:` set is fully satisfied,
  running independent phases in parallel.
- Phase-level fan-out uses Option A on the existing Parallel Dispatch model — the warm trunk agent
  `implementor-<N>` keeps context while additional ready phases dispatch as cold leaf agents
  `implementor-<N>-pX` on the same branch, non-merging transcripts. No worker gains the `Agent` tool;
  the orchestrator makes every fan-out decision (no self-dispatch), and `jackal-supervisor` remains the
  sole `Agent`-holder.
- Same-branch write-safety note (independent phases are file-disjoint by construction; per-phase
  timeout attribution out of scope), watcher cross-reference for long parallel streams, and flat-topology
  consistency with the Orchestration Topology section. The review + verify-don't-trust posture is
  unchanged — fan-out changes when phases run, never whether their output is disk-verified.

**Changed:**
- When no phase declares `depends_on:`, scheduling is byte-for-byte the current named-continuation loop —
  no cold-start regression for the common sequential case.

## [jackal-plan-and-execute] 3.4.0

Flat orchestration topology by default; justification-gated middle tier (#19, R3).

**New:**
- `execute` skill gains an `## Orchestration Topology` section: flat (director → workers) is the
  default, with the GL-488 per-phase warm-context `SendMessage` named-continuation pattern named as
  the reference implementation.
- A middle supervisor tier now requires a one-sentence written justification in the Agent dispatch
  prompt (what the tier provides that flat dispatch + memory cannot); a nested-supervisor dispatch
  without it is declared a defect.
- When a middle tier is used, R2's liveness contract applies with a stricter (shorter) `EXPECT`
  window — cross-referenced, not duplicated.
- Explicit reconciliation with the repo CLAUDE.md sole-orchestrator rule, written into the skill
  text: flat-by-default + the narrow, justification-gated nested-supervisor tier as the documented
  exception (CLAUDE.md itself unchanged).

## [jackal-supervisor] 3.3.0

Sweeps run flat, not under a nested Opus supervisor (#19, R3).

**New:**
- `jackal-sweep` skill directs backlog sweeps to run as direct director work or at most a single
  Sonnet research dispatch — never a nested Opus supervisor — unless justified per the `execute`
  skill's Orchestration Topology policy (one-sentence justification + stricter liveness window).

## [jackal-plan-and-execute] 3.3.0

Enforce explicit model tiering + credential pre-flight + commit-early discipline (#22, R4+R5).

**New:**
- Every `<invoke name="Agent">` dispatch in the execute, plan, review, design, and finish skills now carries an explicit `<parameter name="model">`; a model-unspecified dispatch is declared a defect.
- Model Tier Table (planner=Opus, implementor=Sonnet, reviewer=Sonnet, reviewer-deep=Opus, contract-sentinel=Sonnet, lexicon-warden=Sonnet, doc-render/research=Sonnet) in the execute skill, with a footnote reconciling the sentinel/warden `model: haiku` frontmatter (dispatch sites live in jackal-director — deferred follow-up).
- Credential pre-flight (`aws sts get-caller-identity` + remaining-lifetime check) before any dispatch expected to run >10 min — framed as generic guidance for downstream projects, not a gate on this repo.
- Commit-early clause in the implementor prompt: commit at every green intermediate state so credential expiry or a stall can't destroy uncommitted work.

## [jackal-supervisor] 3.2.0

Model tiering + credential pre-flight (#22, R4+R5).

**New:**
- Model Tiers section mirroring the execute skill's tier table; every supervisor dispatch specifies `model` explicitly.
- Credential pre-flight guidance before long-running dispatches (downstream-project scope).

## [jackal-supervisor] 3.1.1

Promote operational lessons from director memory into shared skill/agent text (#21).

**New:**
- Merged-PR gate: `jackal-supervisor.md` "Reading the backlog" and Backlog Groom now cross-check every candidate OPEN issue against merged PRs before ranking, routing delivered-but-open issues to a separate "stale-open — close these" list (prevents the GL-347 mis-ranking). The gate treats `gh issue view --json closedByPullRequestsReferences` as the exact delivery signal and `gh pr list --search` as a candidate filter only — a raw search hit is confirmed as delivery only after reading the matched PR's title/body for an explicit `Closes`/`Fixes`/`Refs #<N>` on the exact issue number. `jackal-sweep` report surfaces the stale-open list and points to the gate.
- Rule of thumb: memory is for project facts/preferences; any lesson that changes agent procedure goes into the owning skill/agent definition the same session, memory cross-references it, and stale entries are superseded.

## [jackal-plan-and-execute] 3.2.1

Promote operational lessons into shared skill/agent text (#21).

**New:**
- `execute` skill Step 4 (backlog select): merged-PR gate drops candidates already delivered by a merged PR before priority ordering, using `closedByPullRequestsReferences` as the exact signal and a `gh pr list --search` hit only as a candidate needing PR-body confirmation (not delivery proof by itself).
- `implementor.md` Verify step: run `ruff format`/`ruff check --fix` before committing when the project uses Ruff (conditional; no-op for non-ruff repos).

## [jackal-plan-and-execute] 3.2.0

Event-driven waits + subagent liveness contract (#18).

**New:**
- `execute` skill documents the event-driven watcher (`scripts/worktree-watcher.sh`), the
  sleep<timeout hard rule (foreground sleeps ≤100s under the 120s Bash timeout), the batched-status
  rule, and the STALLED stall-response procedure (verify disk → instruct commit-and-report → resume
  from disk).
- Honest-stopping-point clause added to `implementor.md` and both `execute` dispatch templates;
  EXPECT/heartbeat expectation set at dispatch; relay rule forbidding unbacked progress claims,
  cross-referencing `verification-before-completion`.

## [jackal-supervisor] 3.1.0

Subagent liveness contract (#18).

**New:**
- Honest-stopping-point clause added to `jackal-supervisor.md` alongside the "workers never spawn
  workers" rule (belt-and-braces prompt-level enforcement). Supervisor retains the `Agent` tool as
  the sole orchestrator.

## [jackal-director] 1.4.0

Event-driven waits + liveness, director-side (#18).

**New:**
- `director-loop` skill mirrors the event-driven wait / STALLED stall-response summary and the
  relay rule (no relayed subagent progress claim without a cited same-turn disk observation),
  referencing the `execute` skill for the canonical procedure.

## [jackal-director] 1.3.0

Director operating-discipline notes for autonomous cycles.

**Changed:**
- `director-loop` skill: added an "Operating discipline (autonomous cycles)" section covering a preventive metadata-commit routing note (adopt a PR/exception route before enforce_admins-style tightening; preserves the PR-only completion invariant — no observed violation) and a `/clear` context-growth discipline note for issue/PR boundaries.

## [jackal-director] 1.2.0

Monorepo support: contracts no longer have to live in one central package. Driven by the ROAR
governance comparison (per-module contracts, existing `docs/standards/` + import-linter layer).

**New:**
- Per-component contract sources: the registry's Component Map may carry `Contract source` and
  `Exporter` columns; `registry-drift-checker`, `contract-sentinel`, and `delta-scribe` resolve
  contract paths from those rows when present, falling back to the single contracts package
  header (which keeps working unchanged).
- Registry-as-index sections: a contract section with a `Source:` line and no fields table
  delegates field-level truth to the referenced model file; the drift checker audits the
  reference (path exists, model defined there) instead of mirroring fields.
- `Boundary enforcement:` registry header line for repos that already machine-enforce
  boundaries (import-linter, ESLint boundary rules); `canon-init` detects such tooling and
  `contract-check` reports C3 as a second witness — drift between sentinel and linter is a
  director-packet item.

**Changed:**
- `canon-init` now documents "one canon per repo, even in a monorepo" (per-module canons are an
  anti-pattern; the per-component registry is the monorepo affordance), seeds the glossary from
  curated docs (`docs/standards/`, CLAUDE.md Contracts/Invariants sections) before falling back
  to a frequency grep, layers on top of existing standards docs instead of duplicating them, and
  drops `.gitkeep` files into `reports/` and `packets/` so the scaffolded tree survives a fresh
  clone.
- `director-loop` skill and README describe both registry modes and the one-canon rule.

## [jackal-plan-and-execute] 3.1.1

Wording sync with jackal-director 1.2.0's per-component contract sources.

**Changed:**
- `design`, `execute`, and `review` skills and `reviewer-deep` now say "contract sources" (the
  contracts package or per-component contract files named in `docs/canon/registry.md`) wherever
  they previously assumed a single contracts package for impact statements and review-tier
  routing.

## [jackal-supervisor] 3.0.3

Graceful complexity-routing fallback instead of telling the user to re-run a different command.

**Changed:**
- `jackal-design-plan` on a Standard issue now auto-invokes `jackal-impl-plan` instead of
  telling the user to run it themselves; on a Simple issue it now dispatches the implementor
  directly instead of telling the user to.
- `jackal-impl-plan` on a Simple issue now dispatches the implementor directly instead of
  telling the user to.

## [jackal-director] 1.1.1

Closes a no-nesting guard gap on the Haiku conformance agents.

**Fixed:**
- `delta-scribe`, `contract-sentinel`, `lexicon-warden`, and `registry-drift-checker` now carry
  `disallowedTools: Agent` in frontmatter and an explicit "never dispatch or invoke other
  subagents" rule in their body, matching the pattern already used by `director`. Their dispatch
  prompt templates in `director-packet` and `contract-check` now repeat the prohibition in the
  prompt text as well.

## [jackal-plan-and-execute] 3.1.0

Execution efficiency and review calibration for the plan/backlog loops (design plan C3–C6).

**New:**
- The Mode 1 phase loop dispatches the implementor as a named agent on phase 1 and continues it
  via SendMessage for phases 2..N, reusing warm (cache-hot) context. Falls back to a fresh
  dispatch when continuation fails, a review cycle found Critical issues, or
  `implementor_continuation: off` is set in `.jackal/harness-guidance.md`. Continuation is
  per-issue; parallel issues keep separate named agents; the reviewer is never continued.
- Simple issues in backlog mode now run one Sonnet `reviewer` pass by default (implementor →
  reviewer → finish), feeding the existing 3-cycle fix loop. Overridable with
  `simple_review: off`.
- The orchestrator may read a single explicitly-named file in full for routing/triage
  classification — a scoped exception to the no-direct-read delegation rule that does not cover
  multi-file or search-driven reads.

**Changed:**
- `implementor.md` acknowledges follow-up phases may arrive in the same session and treats each
  phase file as the complete spec for that phase.

**Fixed:**
- `reviewer` / `reviewer-deep` report caps now govern prose only — a Critical or Important
  finding can never be dropped to hit the length target; Minor findings may compress.

## [jackal-director] 1.1.0

Adds an automated fallback for the Director review loop so it can run without a Fable or
other strong-model chat session available.

**New:**
- The automated `/jackal-director:director-review` command and the read-only Opus `director`
  agent (tools: Read only; no repo access by design) — an automated fallback for the Director
  loop when no Fable or other strong-model chat is available; ingestion stays human-gated.

**Changed:**
- The Director is now described in capability-relative terms (a fresh-context reviewer with
  no repo access, run on the strongest model available) across director-loop, director-packet,
  ingest-directive, and the plugin README; Fable named only as the preferred option. Cadence
  section gains the fallback ladder.

## [marketplace] — remove redundant wrapper commands

Each `jackal-supervisor` / `jackal-plan-and-execute` entry point shipped
**twice** — as a thin wrapper command *and* as a same-named `user-invocable`
skill. The two collide (the skill wins the name), so the wrapper never ran; but
its body ("invoke the X skill", a bare, self-referential name) is what produced
the "thin wrapper, then searching for the skill" behavior on invocation. Plugin
bumps: `jackal-plan-and-execute` 3.0.2 → 3.0.3, `jackal-supervisor` 3.0.1 → 3.0.2.

**Removed:**
- The 10 redundant wrapper command files in `jackal-supervisor` and
  `jackal-plan-and-execute`. Their same-named `user-invocable` skills already
  provide the identical `/plugin:name` entry point, so the wrappers were dead
  (shadowed by the skill). Each command's `argument-hint` was ported into the
  corresponding skill's frontmatter, so the `/`-menu hint is preserved.
  (`jackal-director` commands stay — they are self-contained, with no
  same-named skill.)

## [marketplace] — namespace command handoffs

Fixes end-of-phase handoffs and workflow docs that emitted bare slash commands
(`/execute`, `/jackal-impl-plan`, …). Marketplace-installed commands are always
namespaced `plugin:command`, so the bare forms did not resolve when a user typed
them. Plugin bumps: `jackal-plan-and-execute` 3.0.1 → 3.0.2,
`jackal-supervisor` 3.0.0 → 3.0.1, `jackal-director` 1.0.0 → 1.0.1.

**Fixed:**
- Phase-boundary handoffs the user must type are now emitted namespaced —
  design → `/jackal-supervisor:jackal-impl-plan`, plan/impl-plan resume →
  `/jackal-plan-and-execute:execute`, and the director loop's
  `/jackal-director:contract-check` / `director-packet` / `ingest-directive`.
- Resumable-command emissions in `jackal-pause-session`, redirect/STOP messages,
  and "offer to run" prompts across `execute`, `finish`, `jackal-sweep`,
  `jackal-ui-verify`, and the supervisor agent.
- README command references (both plugin READMEs and the director README) now
  show the namespaced form, with a note that bare commands do not resolve.
- `scripts/trace-deps.sh` now includes `commands/` in the shipped inventory, so
  namespaced `plugin:command` references resolve instead of dangling.

## [jackal-plan-and-execute] 3.0.1

Design phase no longer stops to confirm the slug.

**Changed:**
- The `design` skill picks a sensible default slug — `<issue#>-<kebab-title>`,
  incorporating the GitHub issue number — and proceeds without asking. It only
  pauses when no slug can be derived (e.g. a too-vague freeform description).
  The user can still override afterward.

## [marketplace] 4.0.0 — director loop, PR-only lifecycle, no-nesting subagents

Major release: adds the `jackal-director` plugin (1.0.0), removes the todo-md
backlog backend, and makes the PR the only branch-completion path. Plugin bumps:
`jackal-plan-and-execute` 2.5.0 → 3.0.0, `jackal-supervisor` 2.5.0 → 3.0.0.

**Breaking:**
- **todo-md backend removed.** GitHub Issues is the only backlog; `gh_repo` is
  required. All `backend:` config keys, TODO.md parsing, and todo-md branches
  are gone from `execute`, `finish`, the supervisor agent, and every wrapper skill.
- **`finish` no longer presents merge/PR/keep/discard options.** It rebases onto
  origin/main when behind, pushes, and opens a PR — always. Keep/discard happen
  only on explicit user request; local merge to main no longer exists.

**New:**
- **`jackal-director` plugin (1.0.0)** — Software Director review loop: four
  Haiku court-reporter agents (`delta-scribe`, `contract-sentinel`,
  `lexicon-warden`, `registry-drift-checker`), `docs/canon/` scaffolding
  (`/canon-init`), a pre-PR conformance gate (`/contract-check`), cycle packets
  for the Director (`/director-packet`), and memo ingestion into ADRs, glossary,
  and `.jackal/*-guidance.md` (`/ingest-directive`). Contracts package and
  schema exporter are configurable (`contracts_pkg`, `schema_export_cmd`) and
  work for Pydantic and TypeScript (typebox/zod) alike.
- **Canon wiring across the lifecycle** (active only when `docs/canon/` exists):
  `design` reads charter/glossary and adds a Contract Impact section; `planner`
  drafts impact statements; `execute`'s final review runs `/contract-check` in
  parallel; `finish` gates the PR on CLEAN or explained-FLAGGED; the supervisor
  prompts when a director packet is due.
- **`reviewer-deep` agent (Opus)** — final review tier for Complex issues and
  auth/payments/user-data/crypto/contract diffs; `reviewer` (Sonnet) remains the
  default. Review is pre-PR; routine post-PR re-review is retired.
- **`jackal-sweep` skill + command** — reclaims worktrees/branches for merged
  PRs (worktree first, then branch — the order ad-hoc sync scripts get wrong),
  flags open PRs with `mergeStateStatus` BEHIND/DIRTY including the exact rebase
  command, fast-forwards main, and prunes.
- **Rebase-before-push in `finish`** — fetches origin, rebases when behind,
  re-runs tests, then pushes; semantic conflicts stop for a human.
- **Epics + backlog grooming in the supervisor** — `epic`-labeled tracking
  issues with task lists, `Part of #N` linkage at creation, epic-grouped status
  reports, and a groom workflow (mislabeled ready, orphaned in-progress, zombie
  worktrees, unprioritized issues, epic drift, PRs needing rebase).
- **Supervisor command files** — `/jackal-design-plan`, `/jackal-impl-plan`,
  `/jackal-finish-branch`, `/jackal-pause-session`, `/jackal-ui-verify`,
  `/jackal-sweep` are now real commands, so emitted handoffs are always typable.
- **AC checkbox closeout** — the final review's AC coverage table is posted as
  an issue comment and the body's checkboxes are ticked before the PR opens.

**Changed:**
- **Nested subagent spawning disabled** (matches upstream ed3d 1.12.0):
  `planner`, `implementor`, `reviewer`, `reviewer-deep` all carry
  `disallowedTools: Agent` plus an explicit no-nesting rule, and every dispatch
  prompt template in `design`/`plan`/`execute`/`review`/`finish` repeats the
  prohibition. The supervisor remains the only orchestrating tier.
- **Verbosity discipline:** hard report caps (planner 15 / implementor 20 /
  reviewer 40 / reviewer-deep 60 lines), no-narration rules, and `execute` now
  relays 3-line summaries instead of full worker reports.
- **Conflict gate fixed:** branch globs now include the go-forward
  `<type>/<issue#>-slug` convention (`'feature/*' '*/[0-9]*-*'`) in `plan`,
  `execute`, `jackal-design-plan`, and `jackal-impl-plan` — previously only
  `feature/*` was checked, so the gate never fired on new-convention branches.
- **Handoff commands are literal:** `plan` → execute continues via the Skill
  tool (or emits exactly `/execute <plan-dir> <worktree>`); the design handoff
  emits `/jackal-impl-plan <path>` verbatim. Invented names like
  `/execute-plan` are explicitly called out as nonexistent.
- READMEs rewritten: five-plugin layout, PR-only cycle, Director loop section,
  Bedrock model-mapping note (main conversation described as "the session
  model" rather than a hardcoded model name).


Fixes an invalid execution-command suggestion at phase handoff. Plugin bumps:
`jackal-plan-and-execute` 2.4.0 → 2.5.0, `jackal-supervisor` 2.4.0 → 2.5.0.

**Fixed:**
- **Plan directory honored the wrong path.** The `plan` skill and `planner` agent
  hardcoded `docs/implementation-plans/` when building `PLAN_DIR`, ignoring the
  `impl_plans` Jackal Config key. On projects that configure a different dir (e.g.
  ROAR's `docs/impl-plans`), phase files were written to one path while resume and
  handoff suggestions pointed at a non-existent `docs/implementation-plans/` —
  producing an invalid `/execute <dir>` command. Both now build `PLAN_DIR` from
  `IMPL_PLANS`/`impl_plans`, and the `plan` skill's wrapper-inputs list documents it.
- **`jackal-pause-session` resume suggestions** used the same hardcoded path. They
  now derive the plan dir from `impl_plans` and verify the directory exists (via
  `ls`) before emitting a resume command, so the suggested command is runnable.
- **`design` skill output path** now references the `design_plans` config key
  instead of a bare hardcoded `docs/design-plans/` (defensive consistency; the
  default is unchanged).

## [marketplace] 3.4.0 — GitHub issue hygiene

Tighten issue-creation and lifecycle hygiene in the supervisor. Plugin bumps:
`jackal-supervisor` 2.3.0 → 2.4.0, `jackal-plan-and-execute` 2.3.0 → 2.4.0.

**New:**
- **Dedup search before issue creation** — the supervisor's create workflow now
  runs `gh issue list --search` over open and closed issues first and stops on a
  plausible match instead of filing a duplicate.
- **Readiness validation** in `execute` Backlog mode — a `status/ready` label is no
  longer trusted on its own; issues whose body is still a template skeleton
  (placeholder ACs, unfilled scope) are reported as mislabelled and skipped rather
  than worked.
- **Priority-ordered selection** — `execute` Step 4 reads `priority/{high,medium,low}`
  to order work (was "highest-priority first" with nothing reading priority), and
  flags unprioritized ready issues.
- Label bootstrap now creates `priority/*` labels (and notes `module/*`), since the
  create workflow applies them at creation.

**Changed:**
- Issues are created with **all classifying labels at once** (`complexity/*` and,
  where defined, `priority/*` / `module/*`) instead of only `status/ready`, so the
  routing labels can't drift from the body.
- The assignee is now set (`--add-assignee "@me"`) on every `status/in-progress`
  transition — supervisor agent, `jackal-design-plan`, and `jackal-impl-plan` — so
  in-progress issues aren't orphaned in GitHub's UI, boards, and filters.
- Title guidance: default to a concise imperative title (bare issue numbers carry
  identity); planning-code prefixes are treated as transitional setup scaffolding,
  not the go-forward convention.

## [marketplace] 3.3.0 — harness coherence & ROAR alignment

Batched release fixing broken/dangling references, undeclared external dependencies, and
protected-main safety, surfaced by an audit against the ed3d predecessor, Claude Code harness
best practice, and the ROAR consuming repo. Plugin bumps: `jackal-plan-and-execute` 2.2.0 → 2.3.0,
`jackal-supervisor` 2.2.0 → 2.3.0, `jackal-house-style` 1.0.5 → 1.0.6.

**New:**
- `jackal-supervisor` now **ships the `jackal-supervisor` agent** (the orchestrating brain). It
  previously lived only in `~/.claude/agents/`, so a clean install got the wrapper skills but not
  the agent driving them.
- Ported `test-driven-development` and `verification-before-completion` skills into
  `jackal-plan-and-execute` (under their original names) — the `debug` skill required them but the
  ed3d→jackal rework had dropped them, leaving dangling references.
- `label_style` Jackal Config knob (`slash` | `colon`, default `slash`) — the harness now matches a
  project's label convention. ROAR and GitHub norm use slash-style (`status/ready`).
- `.jackal/harness-guidance.md` resolves **find-up** from the working directory to repo root
  (nearest-wins), so a monorepo can scope harness behavior per module.
- `marketplace.json` declares external `requires` (ed3d-research-agents, ed3d-extending-claude,
  ed3d-playwright); a README "Required dependencies" section documents the install.
- `scripts/trace-deps.sh` + `docs/test-plans/2026-06-16-harness-coherence.md` — a re-runnable
  dependency-trace gate (0 dangling refs) and verification plan.
- Restored `LICENSE.superpowers` (MIT, Jesse Vincent), required for the superpowers-derived code.

**Changed:**
- Autonomous `finish`/`execute` completion is now **protected-main-safe**: when `main` is protected
  (via `.jackal/harness-guidance.md`, `protected_main` config, or `gh` detection) the default is
  push + open PR instead of a local merge. `finish` Option 2 fills a repo `PULL_REQUEST_TEMPLATE.md`.
- The `reviewer` now consumes the planner's `test-requirements.md` as an AC↔test coverage gate
  (previously written but never read).
- `implementor` uses module-scoped Conventional Commits when the project documents scopes.
- `debug` skill frontmatter renamed `systematic-debugging` → `debug` to match its dir/invocation.
- Top-level `README.md` rewritten for jackal (was the stale ed3d README: wrong title, 9-plugin
  layout, dead command names, ed3d install URL).
- `jackal-house-style` plugin.json rebranded (author, repo URL, description).

**Fixed:**
- `finish` no longer silently skips CLAUDE.md freshness re-verification when
  `ed3d-extending-claude` is absent — it emits a visible warning (ROAR makes closeout mandatory).
- `jackal-design-plan` hand-off prints the bare-integer `<type>/<issue#>-slug` branch format its own
  worktree step creates (was the legacy `feature/<module>/` form).
- Stale ed3d prose (`jackal-pause-session`: "ed3d skills create tasks" → "jackal skills").

## [jackal-house-style] 1.0.5

Align the Python skill's lint/security config with what ATLAS and Ledger Lens actually run in CI.

**Changed:**
- `howto-code-in-python` ruff config now matches real CI: `line-length = 300`, `select = ["E", "F", "W"]`, `ignore = ["E501"]`, file-scoped `per-file-ignores` for E402, and no `target-version` pin (CI runs Python 3.11). Was `line-length = 88`, `target-version = "py312"`, and a broad `extend-select` (I/UP/B/SIM/RUF) that no project enforced.
- bandit is now described as the mandatory PR gate at `-lll` (HIGH only), matching CI and the buildspecs — was `-ll` (LOW and above).
- semgrep downgraded from "MANDATORY on every project / required CI check" to a recommended deploy-time gate (as ATLAS runs it; Ledger Lens does not run it at all). Added `pip-audit` (advisory) and `detect-secrets` (gate) to reflect the real CI jobs.
- Dev dependencies shown under `[dependency-groups] dev` instead of the legacy `[tool.uv] dev-dependencies`. Updated the self-check, pyproject example, and Red Flags to match. Added a note warning against adding semgrep to PR checks to "match" a project that gates it at deploy.

## [jackal-supervisor] 2.2.0

GitHub is now the default backlog backend.

**Changed:**
- `backend` defaults to `github` (was `todo-md`) across `jackal-design-plan`, `jackal-impl-plan`, `jackal-pause-session`, and `jackal-finish-branch`. Projects must set `backend: todo-md` explicitly to use the TODO.md flow; `gh_repo` is required for the default GitHub path.
- `jackal-finish-branch` and `jackal-pause-session` skill descriptions reworded to present the GitHub backlog first, with TODO.md as the alternative.

**Fixed:**
- `jackal-pause-session` resume-checkpoint examples emitted the non-existent `/execute-implementation-plan` command (a stale ed3d-era name), so resuming into execution handed the user a dead command. They now use `/execute [plan-directory] [working-directory]` with the worktree passed as the working directory, so the resume command is runnable from the repo root.

## [jackal-plan-and-execute] 2.2.0

GitHub-first backlog narrative in execute and finish.

**Changed:**
- `execute` Backlog mode, delegation table, and supervisor-integration notes describe the backlog as GitHub issues by default (or TODO.md), instead of treating TODO.md as the primary mechanism. The explicit `backend: todo-md` branches are unchanged and fully supported.
- README architecture diagram, delegation table, and Continuous Execution section reworded to GitHub-first. `commands/execute.md` and `commands/finish.md` descriptions follow suit.

## [jackal-supervisor] 2.1.0

Single-owner worktree creation and optional GitHub backend for backlog state.

**New:**
- `jackal-design-plan` now owns worktree creation. Creates the worktree, runs the conflict gate, and persists a `## Worktree` block (branch, path, created date) to the issue doc as the single source of truth.
- GitHub backend support across `jackal-design-plan`, `jackal-impl-plan`, `jackal-pause-session`, and `jackal-finish-branch`. Opt in by setting `backend: github` and `gh_repo: owner/repo` in the project's Jackal Config.
- Standard label set: `status:ready`, `status:in-progress`, `status:paused`, `status:blocked`. Wrappers add/remove labels and post structured comments at worktree assignment, pause/blocked checkpoints, and completion.

**Changed:**
- `jackal-impl-plan` step 3 reads the `## Worktree` block from the issue doc instead of re-deriving the path. Falls back to creating a worktree only for Standard issues that skipped `/jackal-design-plan`. Three explicit cases (block found + path exists / block found + path missing / no block) so the skill never silently bails.
- `jackal-finish-branch` posts a completion comment with merge commit or PR URL, removes `status:in-progress`, and closes the issue on local merge (Option 1). PR-based finishes leave closing to GitHub via "Closes #N" in the PR body.
- `jackal-pause-session` swaps `status:in-progress` for `status:paused` (or `status:blocked`) and posts the checkpoint as a comment when `backend: github`.

**Fixed:**
- "Could not find worktree" handoff failure between `/jackal-design-plan` and `/jackal-impl-plan` caused by both skills trying to create the worktree and re-derive its name from convention.

## [jackal-plan-and-execute] 2.1.0

Worktree input pass-through and GitHub backlog backend in execute/finish.

**New:**
- `plan` skill accepts `WORKTREE_PATH` from its wrapper — when provided, skips its own conflict gate + worktree creation. The wrapper is the single owner of worktree state.
- `execute` Backlog mode reads from GitHub issues (`gh issue list --label status:ready --state open`) when `backend: github`. TODO.md remains the default and is fully supported.
- `design` skill accepts `WORKTREE_PATH` and runs its design-doc commit from the worktree, so the design document lands on the feature branch instead of `main`.

**Changed:**
- `finish` skill step 6 gates TODO.md updates on `backend`. With `backend: github`, GitHub is the source of truth and the wrapper handles the close + comment.

## [jackal-house-style] 1.0.4

Make `bandit` and `semgrep` mandatory on every Python project.

**Changed:**
- `howto-code-in-python`: bandit and semgrep are required, not optional, and not interchangeable. Added a Security Scanning section with installation (`uv add --dev bandit semgrep`), `[tool.bandit]` config, run commands, suppression policy (line-local with reason — never repo-wide), and CI requirements. Updated the self-check, `pyproject.toml` example, and Red Flags to enforce both scanners on every commit.

## [jackal-linear] 1.0.0

Initial release of the jackal-linear plugin.

**New:**
- `/start-from-linear [ISSUE-ID]` command: fetches Linear issue, sets it to In Progress, seeds the `starting-a-design-plan` workflow with issue context
- `linear-workflow` skill: start mode (issue fetch + In Progress status) and finish mode (In Review on PR, Done on merge)
- `writing-for-linear` skill: content standards for Linear comments, status-change updates, and issue descriptions
- PostToolUse hook: detects `gh pr create` and `git merge` commands, injects Linear reminder when `.linear-issue` is present
- Linear MCP server registered via `mcp-remote` pointing to `https://mcp.linear.app/mcp` (OAuth 2.1)

## ed3d-house-style 1.0.3

Relax FCIS file classification to target only files with runtime behavior.

**Changed:**
- FCIS skill: classification now mandatory only for files containing runtime logic (functions, classes with methods, orchestration)
- FCIS skill: added exemptions for type-only files, constants, barrels, tests, and generated files
- FCIS skill: added threshold note — exempt files that grow to include runtime logic must be classified
- TypeScript skill: added clarifying note in FCIS Integration section about exemptions

## ed3d-plan-and-execute 1.10.3

Add session isolation for parallel planning/execution to prevent file collisions.

**New:**
- `SCRATCHPAD_DIR` parameter with unique session ID (e.g., `/tmp/plan-2025-01-24-feature-a7f3b2/`) ensures isolation when multiple planning or execution sessions run in parallel
- Random session ID component prevents collisions on retry attempts

**Changed:**
- `writing-implementation-plans`: creates and passes SCRATCHPAD_DIR to code-reviewer in Finalization step
- `executing-an-implementation-plan`: creates SCRATCHPAD_DIR at startup, passes to all code review invocations
- `requesting-code-review`: accepts and forwards SCRATCHPAD_DIR to code-reviewer subagent
- `code-reviewer` agent: documents SCRATCHPAD_DIR usage for any scratch files

## ed3d-extending-claude 1.1.0

Adds marketplace management skill for creating and maintaining Claude Code Plugin Marketplaces.

**New:**
- `maintaining-a-marketplace` skill covering marketplace.json schema, version management, release checklists, changelog conventions, validation, and distribution — generalizable for any user publishing a marketplace

## ed3d-plan-and-execute 1.10.2

Fix typo in planning handoff command.

**Fixed:**
- `starting-a-design-plan`: Phase 6 handoff command had `/ed3d-ed3d-plan-and-execute:start-implementation-plan` instead of `/ed3d-plan-and-execute:start-implementation-plan`

## ed3d-extending-claude 1.0.4

Add model-level testing guidance to testing-skills-with-subagents.

**Changed:**
- `testing-skills-with-subagents`: RED phase should use production-level model (default: Sonnet); GREEN/REFACTOR phases should use one tier down (default: Haiku) to ensure skill clarity under weaker reasoning
- Quick reference table now includes model column

## ed3d-basic-agents 1.1.0

Add fan-out analysis skill for large corpus processing.

**New:**
- `doing-a-simple-two-stage-fanout` skill: orchestrates parallel Worker subagents, Critic review subagents, and a Summarizer for analyzing corpora that exceed a single agent's context window
- `compute_layout.py` helper script for computing segment counts, agent assignments, and context window budgets
- `diagram-templates.md` reference with Mermaid and Graphviz templates for visualizing fan-out pipelines
- First `user-invocable: true` skill in this plugin

## [ed3d-hook-skill-reinforcement] 1.0.1, [ed3d-plan-and-execute] 1.10.1, [ed3d-basic-agents] 1.0.2, [ed3d-extending-claude] 1.0.3

Remove stale `<available_skills>` XML tag references that no longer match how Claude Code injects skill lists.

**Fixed:**
- Replaced all references to `<available_skills>` with format-agnostic language ("your available skills shown in your system context") across hooks, skills, and agent prompts
- Hook reminder now uses emphatic "MUST" / "Do NOT skip" phrasing for stronger compliance
- Added warning comment in CLAUDE_MD_TESTING.md example to prevent re-introducing the stale tag

## ed3d-plan-and-execute 1.10.0

Scoped acceptance criteria for cross-plan uniqueness.

**New:**
- AC identifiers now use scoped format `{slug}.AC{N}.{M}` (e.g., `oauth2-svc-authn.AC1.1`) to prevent collisions across multiple plan-and-execute rounds
- Design plan naming now prompts user explicitly via AskUserQuestion — supports ticket names (e.g., `PROJ-1234`) or descriptive slugs
- Slug naming guidance: prefer terse unambiguous names (`authn` not `authentication`, but not `auth` since ambiguous with `authz`)

**Changed:**
- `starting-a-design-plan`: Added Step 1 to get design plan name before file creation
- `starting-an-implementation-plan`: Slug definition now documents its three uses (directory, worktree, AC scope)
- `writing-design-plans`: AC structure uses scoped format with slug prefix
- `writing-implementation-plans`: Task templates and AC coverage sections use scoped format
- `executing-an-implementation-plan`: AC coverage check references scoped format
- All examples updated to use terse slugs (e.g., `oauth2-svc-authn` instead of `oauth2-service-auth`)

## ed3d-plan-and-execute 1.9.8

Disables user invocation of skills.

**Changed:**
- All skills now have `user-invocable: false` — skills are auto-invoked by Claude based on description matching but won't appear in the `/` slash command menu

## ed3d-house-style 1.0.2

Disables user invocation of skills.

**Changed:**
- All skills now have `user-invocable: false` — skills are auto-invoked by Claude based on description matching but won't appear in the `/` slash command menu

## ed3d-extending-claude 1.0.2

Disables user invocation of skills.

**Changed:**
- All skills now have `user-invocable: false` — skills are auto-invoked by Claude based on description matching but won't appear in the `/` slash command menu

## ed3d-basic-agents 1.0.1

Disables user invocation of skills.

**Changed:**
- All skills now have `user-invocable: false` — skills are auto-invoked by Claude based on description matching but won't appear in the `/` slash command menu

## ed3d-playwright 1.0.1

Disables user invocation of skills.

**Changed:**
- All skills now have `user-invocable: false` — skills are auto-invoked by Claude based on description matching but won't appear in the `/` slash command menu

## ed3d-research-agents 1.0.1

Disables user invocation of skills.

**Changed:**
- All skills now have `user-invocable: false` — skills are auto-invoked by Claude based on description matching but won't appear in the `/` slash command menu

## ed3d-plan-and-execute 1.9.7

Adds AC coverage verification, compaction-safe task tracking for review fixes, and test plan reminder.

**Changed:**
- `executing-an-implementation-plan`: Final code review now includes AC_COVERAGE_CHECK — verifies all acceptance criteria are covered by at least one phase
- `executing-an-implementation-plan`: When code reviewer returns issues, create ONE TASK PER ISSUE with VERBATIM description — survives compaction
- `writing-implementation-plans`: Same per-issue task creation for finalization code review fixes
- `writing-implementation-plans`: Same per-revision task creation for test requirements approval
- `finishing-a-development-branch`: Reminds user to review human test plan (if exists) before considering work complete

## ed3d-plan-and-execute 1.9.6

Requires verbatim task names to prevent instruction loss.

**Fixed:**
- `writing-implementation-plans`: Task names must be copied VERBATIM, not paraphrased — phrases like "and activate relevant skills" trigger behavior post-compaction

## ed3d-plan-and-execute 1.9.5

Dynamic skill activation replaces hardcoded requirements.

**Changed:**
- `writing-implementation-plans`: Removed hardcoded "REQUIRED SKILL: coding-effectively"
- `writing-implementation-plans`: Task NB now "Investigate codebase for Phase N and activate relevant skills"
- Skills activated dynamically based on codebase findings, not statically at skill start

## ed3d-plan-and-execute 1.9.4

Activates relevant skills during implementation planning based on technology stack.

**Changed:**
- `writing-implementation-plans`: After codebase investigation, activate skills matching the technologies involved (TypeScript, React, database, etc.) if not already active

## ed3d-plan-and-execute 1.9.3

Adds guidance to prevent over-testing and testing implementation details.

**Changed:**
- `writing-implementation-plans`: "Test behavior, not implementation" — test outputs, not how you called dependencies
- `writing-implementation-plans`: Infrastructure phases explicitly state "Verifies: None" instead of inventing ACs
- `writing-implementation-plans`: What doesn't need tests: types, already-tested dependencies, call patterns
- `writing-implementation-plans`: New rationalizations for common over-testing mistakes

## ed3d-plan-and-execute 1.9.2

Ties tests explicitly to acceptance criteria; removes test code from implementation plans.

**Changed:**
- `writing-design-plans`: Functionality phases must have tests that verify the specific ACs they cover; phase not "done" until tests exist for each listed AC case
- `writing-implementation-plans`: Functionality tasks include "Verifies: AC1.1, AC1.3" field; tests described by AC reference, not full code
- `writing-implementation-plans`: Task-implementor generates actual test code at execution time with fresh codebase context

**Why:** Test code in plans becomes stale (wrong imports, mock patterns). AC text like "Invalid password returns 401" is already a clear test spec.

## ed3d-plan-and-execute 1.9.1

Strengthens acceptance criteria generation and adds traceability to implementation plans.

**Changed:**
- `writing-design-plans`: Acceptance Criteria now generated inline (no subagent needed) with detailed guidance on enumerating success cases, failure cases, and edge cases for each DoD item
- `writing-design-plans`: AC uses numbered format (AC1, AC1.1, AC1.2) for precise traceability
- `writing-design-plans`: AC section moved to legibility header (between DoD and Glossary)
- `writing-implementation-plans`: Phase headers now include "Acceptance Criteria Coverage" section listing which ACs the phase implements
- `writing-implementation-plans`: AC entries copied literally from design plan—no paraphrasing
- `starting-a-design-plan`: Initial document template includes AC placeholder

**Traceability chain:**
```
Design: AC1.1, AC1.2, AC1.3 → Phase header: "implements AC1.1, AC1.3" → Tasks produce tests for AC1.1, AC1.3
```

## ed3d-plan-and-execute 1.9.0

Adds test planning workflow: acceptance criteria, test requirements, and human test plans.

**New:**
- **Acceptance Criteria** in design plans — Definition of Done translated into specific, verifiable criteria; human validates before design documentation completes
- **Test Requirements** in implementation plans — Acceptance criteria mapped to automated tests (with expected file paths) or documented as requiring human verification; written to `test-requirements.md`
- **test-analyst agent** — Validates test coverage against acceptance criteria after final code review; generates human test plan when coverage passes
- **Human Test Plans** — Written to `docs/test-plans/[design-plan-name].md` with specific verification steps, end-to-end scenarios, and traceability to Definition of Done

**Changed:**
- `writing-design-plans`: New section for generating and validating Acceptance Criteria after Implementation Phases
- `writing-implementation-plans`: New Test Requirements task after Finalization; Opus subagent generates `test-requirements.md`
- `executing-an-implementation-plan`: Final review sequence now includes test-analyst for coverage validation and test plan generation

**Test traceability chain:**
```
Definition of Done → Acceptance Criteria → Test Requirements → Automated Tests → Human Test Plan
```

## ed3d-plan-and-execute 1.8.0

Per-phase code reviews now use project-specific implementation guidance.

**Changed:**
- `executing-an-implementation-plan`: Per-phase code reviews now receive the `.ed3d/implementation-plan-guidance.md` file (when it exists) so reviewers apply project-specific coding standards, testing requirements, and review criteria during each phase—not just during the final all-phases review

## ed3d-plan-and-execute 1.7.2

- `/how-to-customize` given more specific instructions to actually repeat the information verbatim.

## ed3d-plan-and-execute 1.7.0

Adds project-specific guidance files for customizing design and implementation plans.

**New:**
- **Project guidance files**: Create `.ed3d/design-plan-guidance.md` and `.ed3d/implementation-plan-guidance.md` to provide project-specific constraints, terminology, and standards
- **`/how-to-customize` command**: Documents available guidance files with examples
- **Design guidance**: Loaded before clarification phase — defines domain terminology, architectural constraints, technology preferences
- **Implementation guidance**: Loaded when starting implementation plans AND during final code review — specifies coding standards, testing requirements, review criteria

**Changed:**
- `starting-a-design-plan`: Checks for and reads `.ed3d/design-plan-guidance.md` between Phase 1 (Context Gathering) and Phase 2 (Clarification)
- `starting-an-implementation-plan`: Checks for and reads `.ed3d/implementation-plan-guidance.md` after branch setup
- `writing-implementation-plans`: Includes guidance path in Finalization task for code reviewer

## ed3d-plan-and-execute 1.6.2

Fixes "Re-read skill" task dependency ordering.

**Fixed:**
- "Re-read skill" task must be re-pointed to Finalization task after granular tasks are created (was incorrectly blocked by "Create implementation plan")
- Added "After Planning: Update Dependencies" step to ensure correct task ordering

## ed3d-plan-and-execute 1.6.1

Fixes task tracking to include dependencies and absolute paths.

**Fixed:**
- Tasks now use addBlockedBy to enforce execution order (NA→NB→NC→ND, then next phase)
- Task descriptions include absolute paths for design file and output file, so tasks remain actionable after compaction

## ed3d-plan-and-execute 1.6.0

Adds granular task tracking to implementation plan writing to survive context compaction.

**New in `writing-implementation-plans`:**
- **Granular per-phase tasks:** Instead of one task per phase, now creates sub-tasks for each step:
  - Phase NA: Read [Phase Name] from design plan
  - Phase NB: Dispatch codebase-investigator to verify current state
  - Phase NC: Research external dependencies (if applicable)
  - Phase ND: Write phase file to disk
- **Finalization task:** Explicitly states "fix ALL issues including minor ones" — model cannot rationalize skipping minor issues
- **Plan validation as tracked task:** Must complete with zero issues before handoff

**New in `writing-design-plans`:**
- **Phase markers:** Design plans now require `<!-- START_PHASE_N -->` / `<!-- END_PHASE_N -->` markers around each implementation phase, enabling granular parsing

**New in `starting-an-implementation-plan`:**
- **Orchestration tasks:** Tracks Branch setup, Create implementation plan, Re-read skill, Execution handoff
- **Restore context step:** Re-reads skill before handoff to restore instructions post-compaction
- **Terminology clarification:** Renamed "Phase 1/2/3" to descriptive names (Branch Setup, Planning, Execution Handoff) to avoid confusion with implementation plan phases

**Fixed:**
- Code reviewer step was being forgotten after compaction — now tracked as explicit Finalization task
- Minor issues were being skipped — task text now makes fixing them mandatory

## ed3d-plan-and-execute 1.5.1

Updates task tracking references for compatibility with new Claude Code task system.

**Changed:**
- All references to `TodoWrite` now prefer `TaskCreate`/`TaskUpdate`/`TaskList` (the new task tools in Claude Code)
- Backwards-compatibility notes added for older Claude Code versions that still use `TodoWrite`

## ed3d-extending-claude 1.0.1

Updates task tracking references for compatibility with new Claude Code task system.

**Changed:**
- Tool tables and examples now reference `TaskCreate`/`TaskUpdate` instead of `TodoWrite`
- Backwards-compatibility notes added for older Claude Code versions

## ed3d-house-style 1.0.1

Updates task tracking references for compatibility with new Claude Code task system.

**Changed:**
- Persuasion principles documentation now references `TaskCreate`/`TaskUpdate` instead of `TodoWrite`
- Backwards-compatibility notes added for older Claude Code versions

## ed3d-plan-and-execute 1.5.0

Promotes experimental execution workflow to stable.

**Changed:**
- Execution workflow now uses just-in-time phase loading (reads one phase at a time, not all upfront)
- Code review happens once per phase instead of between every task
- TodoWrite structure: three entries per phase (Read, Execute, Code review) with absolute paths and titles
- Subagents receive phase file path and read it themselves

**Removed:**
- Experimental skill and command (merged into stable)
- Task grouping by subcomponent (plan phases now define grouping via markers)
- Task-level code review (replaced with phase-level review)

## ed3d-plan-and-execute 1.4.3

Removes misleading directive from implementation plan header.

**Fixed:**
- Removed "For Claude: REQUIRED SUB-SKILL" directive from plan header template — was being parsed by task-implementor subagent when it should only be used at the top-level orchestrator

## ed3d-plan-and-execute 1.4.2

Simplifies experimental execution workflow.

**Changed:**
- Experimental skill now reads first 10 lines (not 3) to capture Goal in header
- Subagents (task-implementor, bug-fixer) now read entire phase file instead of extracted sections
- Removed context window extraction logic — simpler approach, let subagents see full phase context

## ed3d-plan-and-execute 1.4.1

Adds experimental execution workflow and task markers. (1.4.0 was a buggy mis-push.)

**New:**
- **Task and subcomponent markers** in implementation plans: `<!-- START_TASK_N -->`, `<!-- END_TASK_N -->`, `<!-- START_SUBCOMPONENT_A (tasks 3-5) -->`, etc.
- **Experimental execution skill** (`executing-an-implementation-plan-experimental`) with just-in-time phase loading, context windows for subagents, and marker-based extraction
- **Experimental command** (`/execute-implementation-plan-experimental`) to invoke the experimental workflow

**Changed:**
- `writing-implementation-plans` now generates markers in all task templates (backwards compatible — old execution skill ignores them)

## ed3d-plan-and-execute 1.3.3

Fixes execution handoff to use absolute paths, preventing wrong-directory issues after /clear.

**Fixed:**
- Execution handoff now captures absolute paths via `git rev-parse --show-toplevel` and verifies plan directory exists before outputting command
- After `/clear`, users land in the original session directory (often repo root, not worktree) — absolute paths ensure execution happens in the correct directory regardless

**Changed:**
- `/execute-implementation-plan` command now accepts two arguments: `[absolute-plan-dir]` and `[absolute-working-dir]`
- Command verifies both paths exist and changes to working directory before engaging skill

## ed3d-plan-and-execute 1.3.2

Fixes execution handoff to pass plan directory instead of single phase file.

**Fixed:**
- Execute-implementation-plan instructions now pass the plan directory (e.g., `@docs/implementation-plans/YYYY-MM-DD-feature/`) instead of a single phase file — prevents agent from only implementing the first phase

## ed3d-plan-and-execute 1.3.1

Improves resolution of Definition of Done in design plans.

**Changed:**
- Definition of Done is now written to the design document immediately after user confirmation (Phase 3), rather than being reconstructed later during documentation (Phase 5)
- Design document file is created in Phase 3 with DoD and placeholders for Summary/Glossary
- writing-design-plans skill now appends body sections and generates only Summary/Glossary

**Fixed:**
- Corrected stale skill name references ("subagent-driven-development", "executing-plans") to "executing-an-implementation-plan"
- Reinforced that Minor issues from code review must be fixed (model was skipping them)
- Changed `/compact` to `/clear` between phases, with warning to copy next command first

## ed3d-plan-and-execute 1.3.0

Adds legibility header to design plans for human reviewers.

**New:**
- **Phase 3: Definition of Done** — New checkpoint after clarification to confirm deliverables before brainstorming
- **Legibility header** — Design plans now include Definition of Done, Summary, and Glossary sections at the top
- **Subagent extraction** — Uses fresh-context subagent to generate legibility header after writing body
- **Glossary transparency** — Subagent reports omitted "obvious" terms so user can request additions

**Changed:**
- Phases renumbered 1-6 (was 1, 2, 2b, 3, 4, 5)
- Task invocations in skills now use XML block format

## ed3d-plan-and-execute 1.2.0

Added external dependency research capabilities to implementation planning.

**Changed:**
- **writing-implementation-plans**: Added tiered external dependency research workflow. Phases involving external libraries now trigger research via `internet-researcher` (for docs/standards) with escalation to `remote-code-researcher` (for source code) when documentation is insufficient.

**New capabilities:**
- Decision framework for when to research external dependencies
- Tiered research approach: docs first, source code when needed
- External dependency findings section in phase output templates
- Updated per-phase workflow to include research step
- New rationalizations to prevent skipping external research

## ed3d-plan-and-execute 1.1.0

Corrects design plan level of detail. These changes were a missed port from the internal plugin marketplace and were intended for 1.0.0. This release represents the plugin "as intended."

**Changed:**
- **writing-design-plans**: Design plans now stay at component/module level, not task level. Contracts/interfaces can be fully specified; implementation code cannot.
- **brainstorming**: Added guidance on level of detail in Phase 3. Validates boundaries, not behavior.
- **writing-implementation-plans**: Strengthened codebase verification as source of truth. Implementation plans generate code fresh from investigation, never copy from design.
- **README**: Added "Philosophy: What Each Phase Produces" section explaining archival vs just-in-time distinction.

## ed3d-research-agents 1.1.0

Added `remote-code-researcher` agent for investigating external codebases by cloning and analyzing their source code.

**New agent:**
- `remote-code-researcher` - Answers questions about external libraries/frameworks by cloning repos to temp directories and investigating the actual source code. Combines web search (to find repos) with codebase investigation (to analyze cloned code).

## All plugins 1.0.0

Initial release of ed3d-plugins collection.
