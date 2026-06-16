---
name: plan
description: Creates an implementation plan from a design document (or issue doc for Standard issues). Sets up worktree, dispatches planner agent, and hands off to execute. Second step in the Jackal dev cycle.
user-invocable: true
---

# Plan

Generate an implementation plan and set up the execution environment.

**Input:** path to a design plan or issue doc
**Output:** implementation plan directory + worktree ready for execution

---

## Harness Guidance

Before starting, resolve `.jackal/harness-guidance.md` by walking up from the working directory to
the repo root (nearest-wins — a module-level `.jackal/` overrides the root one; see the `execute`
skill's Harness Guidance for the resolution snippet). Apply any project-specific overrides to merge
strategy, test command, or parallel execution policy.

## Delegation Rules

This skill handles setup (conflict gate, worktree creation when not pre-supplied) and hands off artifact work to agents.

| Do directly | Delegate |
|---|---|
| Conflict gate git commands | Phase file generation → `planner` agent |
| Create worktree (only if `WORKTREE_PATH` not provided) | |
| Pass plan dir + worktree to execute | |

Do not read the codebase to understand patterns or research dependencies — the `planner` agent does that.

---

## Inputs from Wrapper

When invoked from `jackal-impl-plan`, the wrapper passes:
- `WORKTREE_PATH` — absolute path to an existing worktree
- `BRANCH` — feature branch name
- `DESIGN_PATH` — design plan or issue doc path
- `TEST_CMD` — project test command

If `WORKTREE_PATH` is provided, **skip steps 2 and 3** (conflict gate + worktree creation) — the wrapper has already done them. Go straight to step 4.

If `WORKTREE_PATH` is not provided (skill invoked directly), run the full flow below.

---

## Process

### 1. Resolve Input

Accept:
- Design plan path: `docs/design-plans/YYYY-MM-DD-slug.md`
- Issue doc path: `docs/issues/CG-XX-slug.md`
- Issue ID: `CG-XX`

If given an issue doc for a Standard issue (no design plan exists):
- The planner agent will generate a mini design plan inline
- No need to run /design first

If given an issue doc for a Complex issue with no design plan:
- STOP: "This issue is Complex — run /design first."

### 2. Conflict Gate

Before creating a worktree, verify no active branches conflict:

```bash
cd $REPO_ROOT

for branch in $(git branch --list 'feature/*' | tr -d ' '); do
  echo "=== $branch ==="
  git diff --name-only main...$branch 2>/dev/null
done
```

Extract scope from the design plan's Architecture/Phases sections (or issue doc's In scope).
Compare against active branch file sets.

- File-level overlap → block, report which branch conflicts
- Directory-level overlap, different files → warn, proceed
- No overlap → proceed

### 3. Create Worktree

Derive names automatically (never ask):

```bash
ISSUE="24"                 # GitHub issue number (the work-unit key), or blank
SLUG="kebab-title"         # from design filename or issue title
TYPE="feat"                # conventional-commit type: feat|fix|docs|chore|refactor|...

WORKTREE=".worktrees/${ISSUE}-${SLUG}"
BRANCH="${TYPE}/${ISSUE}-${SLUG}"

grep -q "\.worktrees" .gitignore || echo ".worktrees/" >> .gitignore

BASE="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#origin/##')"
: "${BASE:=main}"
if [ ! -d "$WORKTREE" ]; then
  git worktree add "$WORKTREE" -b "$BRANCH" "$BASE"
fi
```

> Legacy `feature/<module>/PREFIX-NN-slug` branches still work; new work uses the
> bare-integer `<type>/<issue#>-slug` convention (matches the `gw` helper and the
> telemetry wrapper, which key on the GitHub issue number).

Run baseline test check:
```bash
cd "$WORKTREE"
$TEST_CMD --tb=no -q 2>/dev/null | tail -3
```

### 4. Dispatch Planner

```xml
<invoke name="Agent">
<parameter name="subagent_type">jackal-plan-and-execute:planner</parameter>
<parameter name="description">Planning [issue/feature]</parameter>
<parameter name="prompt">
DESIGN_PATH: [absolute path to design plan]
PLAN_DIR: [absolute path: worktree/docs/implementation-plans/YYYY-MM-DD-slug/]
Working directory: [worktree absolute path]

Generate implementation phase files from this design.
Write all phases to disk. Do not ask for interactive review.

[If implementation guidance exists:]
GUIDANCE: [absolute path to .jackal/implementation-guidance.md]

[If project has specific test command:]
TEST_CMD: [from Jackal Config]
</parameter>
</invoke>
```

The planner:
- Investigates codebase state
- Researches external deps
- Writes phase files + test-requirements.md
- Reports completion

### 5. Hand Off

```
Implementation plan ready for [ISSUE_ID]: [title]

Worktree: [absolute path]
Plan: [plan directory path]
Phases: [N] files

Starting execution.
```

Then immediately invoke the `execute` skill in Plan mode with the plan directory.

If running within the autonomous loop (Backlog mode of execute), this handoff is automatic — no user interaction needed.

---

## For Standard Issues Without a Design Plan

The planner agent handles this case:
1. Reads the issue doc's Summary, ACs, Scope, Technical Notes
2. Generates phase files directly (no separate design doc needed)
3. The "design" is implicit in the issue doc's structure

This keeps Standard issues fast — one planner dispatch, straight to execution.

---

## Jackal Config Integration

Read the project's `## Jackal Config` section from CLAUDE.md for:
- `repo_root` — where to run conflict gate
- `test_cmd` — baseline test verification
- `impl_plans` — where plan files go
- `modules` — module short-name map for branch naming
