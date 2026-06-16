---
name: execute
description: Executes implementation plans or drives continuous issue execution from a backlog. Model-adaptive — dispatches Sonnet implementors, reviews conditionally based on risk, and parallelizes independent work. Runs autonomously until genuinely stuck.
user-invocable: true
---

# Execute

Two modes:
1. **Plan mode** — execute a specific implementation plan (phase files in a directory)
2. **Backlog mode** — continuously pull and execute issues from the configured backlog backend (GitHub issues by default, or TODO.md) until stuck

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

Apply overrides to defaults (review policy, merge strategy, parallel execution policy, stop
conditions). Precedence, lowest to highest: built-in defaults < Jackal Config keys < root
`.jackal/` < module `.jackal/`. If no guidance file exists anywhere in the chain, all defaults apply.

---

## Delegation Rules

The orchestrator manages state and makes routing decisions. It **never** writes code, runs project tests, or investigates the codebase for patterns.

| Do directly | Delegate |
|---|---|
| Read/write backlog state and issue docs | Code + tests → `implementor` |
| Run conflict gate git commands | Phase file generation → `planner` |
| Create/remove worktrees | Code review → `reviewer` (via `review` skill) |
| Decide whether and when to review | |
| Merge branches to main | |
| Update backlog state | |

If you find yourself about to write code, run `$TEST_CMD` for correctness, or grep through the codebase — stop and dispatch an `implementor` or `reviewer` instead.

---

## Mode 1: Execute an Implementation Plan

**Input:** path to plan directory (contains `phase_NN.md` files)

### Process

1. List phase files, read headers only (first 10 lines each)
2. For each phase sequentially:
   a. Read the phase file
   b. Dispatch `implementor` with the phase file path and working directory
   c. Print the implementor's full report
   d. Decide whether to review (see Review Routing below)
3. After all phases: run final review, then hand off to `finish` skill

### Review Routing

After each phase completes, decide:

| Condition | Action |
|---|---|
| Phase touches auth, payments, user data, or crypto | Full review |
| Phase is the final phase | Full review |
| Implementor's self-review flagged uncertainty | Full review |
| Phase is pure infrastructure/config | Skip review |
| All other phases | Skip per-phase review; catch issues in final review |

**Final review is always mandatory.**

After the final review passes, check for UI changes — `finish` will invoke `jackal-ui-verify` automatically if UI files were touched. It covers the full diff from plan start to completion.

When review finds Critical or Important issues:
1. Dispatch `implementor` with the issues list and instruction to fix
2. Re-run review
3. If same issues persist after 3 cycles → stop, report to human

Minor issues from the final review: report them, don't block.

---

## Mode 2: Continuous Backlog Execution

**Input:** none (reads from the configured backlog backend — GitHub issues or TODO.md)

This is the autonomous orchestration loop. The orchestrator (you, running in the main conversation) drives issues to completion without human intervention, stopping only when genuinely stuck.

### The Loop

```
while true:
  1. Read backlog state (GH issues or TODO.md)
  2. Identify unblocked issues in Ready
  3. Run conflict gate on candidates
  4. Select issue(s) to work on
  5. Execute issue (route by complexity)
  6. Merge result
  7. Report completion (one-liner)
  8. Loop back to step 1
```

### Step 1: Read Backlog State

Read `backend` and `label_style` from `## Jackal Config` in CLAUDE.md. `label_style` is `slash` |
`colon` (default **slash**) — it sets the separator in status labels. The examples below use `/`;
substitute `:` if the project sets `label_style: colon`.

**If `backend: github`:**

```bash
gh issue list --repo "$GH_REPO" \
  --label "status/ready" \
  --state open \
  --json number,title,labels,body
```

For each candidate, parse the issue body for `Blocked by:`, `Module:`, `Complexity:`, and `In scope:` sections (the issue doc on disk is still the source for rich detail; GH issue body mirrors the same structure).

Issues are grouped by label:
- `status/ready` → eligible candidates
- `status/in-progress` → currently active (don't double-pick)
- `status/paused` / `status/blocked` → skip
- closed → resolved

**If `backend: todo-md`:**

```bash
sed '/RESOLVED_SECTION_START/q' $REPO_ROOT/TODO.md
```

Parse: Active, Paused, Ready, Backlog, Blocked tables.

### Step 2: Identify Unblocked Work

Read each Ready issue's doc. Check its `Blocked by:` field.
An issue is unblocked when all its blockers are in Resolved.

### Step 3: Conflict Gate

For each unblocked candidate:

```bash
for branch in $(git branch --list 'feature/*' | tr -d ' '); do
  echo "=== $branch ==="
  git diff --name-only main...$branch 2>/dev/null
done
```

Compare active branch file sets against candidate's `In scope:` paths.
- Same file touched → hard block
- Same directory, different files → soft warning (proceed with note)
- No overlap → clear

### Step 4: Select Work

If multiple candidates are unblocked and clear:
- Check for independence (no shared files, no dependency between them)
- If independent: dispatch in parallel (two implementors, two worktrees)
- If dependent: execute highest-priority first

### Step 5: Execute by Complexity

Read the issue doc's `Complexity` field:

**Simple** (≤1 day, bug fix, single concern):
- Create worktree
- Dispatch `implementor` directly with issue doc
- No plan phase, no design phase
- Review only if security-sensitive

**Standard** (multi-file, clear ACs):
- Create worktree
- Dispatch `planner` with issue doc (it generates a mini design plan + phase files)
- Execute phases sequentially (Mode 1 above)

**Complex** (architectural decisions, ambiguous scope):
- STOP. Report: "CG-XX is Complex — needs design decisions. Run /design to start."
- Do not attempt autonomous execution of Complex issues.

### Step 6: Complete and Update

After issue passes review, completion depends on whether `main` is protected (see `finish`'s
**Detect Protected Main** check — `.jackal/harness-guidance.md` merge-strategy, `protected_main`
config, or `gh` detection):

- **Main is open:** merge the worktree branch to main; on `backend: github`, `gh issue close $N
  --reason completed --comment "Merged: <commit>"` and remove the `status/in-progress` label;
  on `backend: todo-md`, move to Resolved.
- **Main is protected:** do **not** merge locally. Push the branch and open a PR (with `Closes #N`
  so GitHub closes the issue on merge); remove `status/in-progress`, leave the issue open for the
  PR to close. Record the PR URL and continue the loop to the next issue — do not block waiting for
  a human to merge.

Then update the issue doc (Status → Done, or → In Review if a PR is pending) and remove the worktree
once the branch is pushed (keep it if a PR is open and you may need to push fixups).

(In practice, this is delegated to `jackal-finish-branch`, which handles protected-main + backend
gating.)

### Step 7: Report

Print one line:
```
✓ CG-XX merged. [brief what]. Starting CG-YY next (also dispatching CG-ZZ in parallel).
```
(Or, when main is protected: `✓ CG-XX PR opened (#NN). Starting CG-YY next.`)

### Stop Conditions

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
  Agent(implementor): CG-XX in worktree A
  Agent(implementor): CG-YY in worktree B
```

Both run concurrently. When both return:
- Review each independently
- Merge each to main (one at a time, re-run tests after each merge)
- If merge conflict arises: merge the higher-priority one first, then rebase the other

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

They can run together: supervisor assigns, execute runs. Or execute can self-serve from the backlog backend in autonomous mode.
