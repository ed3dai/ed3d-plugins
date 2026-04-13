---
name: jackal-impl-plan
description: Generic implementation plan starter — the second step in the Jackal dev cycle, after /jackal-design-plan. Takes a design plan (or issue doc for Standard issues) and produces an implementation plan in an auto-named worktree. Reads project configuration from the ## Jackal Config section in this project's CLAUDE.md.
user-invocable: true
---

# Jackal Implementation Plan Starter

Generic replacement for `ed3d-plan-and-execute:starting-an-implementation-plan`.

**Announce at start:** "I'm using jackal-impl-plan to set up implementation for [issue/feature]."

---

## Step 0: Load Project Config

Read the **## Jackal Config** section from the project's CLAUDE.md. Extract:
- `repo_root`, `issue_prefix`, `issue_docs`, `design_plans`, `impl_plans`
- `test_cmd` — used for baseline test check
- `modules` — module short-name map

---

## Development Cycle

```
Step 1: /jackal-design-plan (for Complex issues)
          Output: $DESIGN_PLANS/YYYY-MM-DD-{slug}.md

Step 2: /jackal-impl-plan docs/design-plans/YYYY-MM-DD-{slug}.md   ← THIS SKILL
          Auto-creates worktree (no questions)
          Generates implementation plan

Step 3: /execute-implementation-plan {plan-dir} {worktree}

Step 4: /jackal-finish-branch
          Tests, push, CLAUDE.md update, TODO.md → Resolved
```

**Complexity routing:**

| Complexity | Step 1 | Step 2 |
|------------|--------|--------|
| Complex (>3 days, design decisions) | Full `/jackal-design-plan` | `/jackal-impl-plan design-plan-path` |
| Standard (1-3 days, clear ACs) | Auto-generated mini design plan (this skill) | `/jackal-impl-plan issue-doc-path` |
| Simple (≤1 day, bug fix) | Skip | Use `task-implementor-fast` directly |

---

## Step 1: Resolve Input and Verify Design Plan

Accept:
- A design plan path: `$DESIGN_PLANS/YYYY-MM-DD-slug.md`
- An issue doc path: `$ISSUE_DOCS/PREFIX-XXX-kebab-title.md`
- An issue ID: `PREFIX-XXX`

### If design plan provided → proceed to Step 2

Read the design plan. Extract:
- Slug from filename (everything after `YYYY-MM-DD-`, excluding `.md`)
- Find associated issue doc: `ls $ISSUE_DOCS/ | grep -i [slug-keywords]`
- Extract Module from issue doc (or infer from design plan content)

### If issue doc or ID provided → check for existing design plan

```bash
ls $REPO_ROOT/$DESIGN_PLANS/ 2>/dev/null | grep -i "PREFIX-XXX\|slug-keywords"
```

**If design plan found:** use it.

**If no design plan:**
- **Complex:** STOP. Direct user to `/jackal-design-plan` first.
- **Standard:** Auto-generate mini design plan (see below).
- **Simple:** Tell user to use `task-implementor-fast` directly.

### Auto-generating a Mini Design Plan (Standard issues only)

1. Read the issue doc: Summary, ACs, Scope, Technical Notes
2. Write `$REPO_ROOT/$DESIGN_PLANS/YYYY-MM-DD-{ISSUE-ID}-{slug}.md`:

```markdown
# [Issue Title] Design

## Summary
[1-2 sentences from issue doc]

## Definition of Done
[ACs as prose statement]

## Acceptance Criteria
- **{slug}.AC1.1 Success:** [AC1]
- **{slug}.AC1.2 Failure:** [edge case]

## Glossary
[Key terms from Technical Notes]

## Architecture
[From Technical Notes and Scope — brief, 3-5 sentences]

## Existing Patterns
[From CLAUDE.md investigation — what patterns this follows]

## Implementation Phases

<!-- START_PHASE_1 -->
### Phase 1: [Derived from ACs]
**Goal:** [What this phase achieves]
**Components:** [Files/dirs from Scope section]
**Dependencies:** None
**Done when:** [Subset of ACs this covers]
<!-- END_PHASE_1 -->
```

Commit the mini design plan:
```bash
git add $DESIGN_PLANS/
git commit -m "docs: add mini design plan for [ISSUE-ID]"
```

---

## Step 1b: Pre-Implementation Conflict Gate

**Run before creating the worktree.** Design planning takes time — new branches may have started since the issue was first assigned.

```bash
cd $REPO_ROOT

for branch in $(git branch --list 'feature/*' | tr -d ' '); do
  echo "=== $branch ==="
  git diff --name-only main...$branch 2>/dev/null
done
```

Extract the scope footprint from the design plan (or issue doc for Standard issues):
- **Architecture** section → file paths and directories
- **Implementation Phases → Components** fields
- **Scope / In scope** from the issue doc

**Compare scope against active branch file maps.**

**No conflict → proceed to Step 2.**

**Conflict found → stop:**
```
⛔ Cannot start implementation for PREFIX-XXX — conflict with [branch].

Both touch: [directory/file]

Options:
1. Wait for [conflicting branch] to merge first
2. Restructure scope to avoid [directory] — possible?
3. Use an integration branch if both must run in parallel

Resolve before proceeding to /jackal-impl-plan.
```

**Why here:** The supervisor's initial Conflict Gate runs against the issue doc scope. This gate runs against the design plan's exact file paths — more precise. It's not a duplicate check; it catches scope expansion revealed during design.

---

## Step 2: Auto-Name Branch and Worktree

**Do not ask the user.** Derive names automatically.

```
SLUG       = derived from design plan filename or issue doc title
ISSUE_ID   = PREFIX-XXX (from issue doc, or blank if no associated issue)
MODULE     = from issue doc Module field (cross-reference Jackal Config module map)

WORKTREE   = .worktrees/{ISSUE-ID}-{slug}
BRANCH     = feature/{module-short}/{ISSUE-ID}-{slug}
```

If no issue ID (pure design-plan-only work):
```
WORKTREE   = .worktrees/{slug}
BRANCH     = feature/{module}/{slug}
```

Module-short comes from the **Jackal Config module map** in this project's CLAUDE.md.

Announce: "Creating worktree `.worktrees/[WORKTREE]` on branch `[BRANCH]`."

---

## Step 3: Create Worktree

**No confirmation needed.**

```bash
# Verify .worktrees is gitignored
grep -q "\.worktrees" .gitignore || echo ".worktrees/" >> .gitignore

# Reuse existing worktree if already created by supervisor
if [ -d ".worktrees/$WORKTREE_NAME" ]; then
  echo "Worktree already exists — reusing .worktrees/$WORKTREE_NAME"
else
  git worktree add .worktrees/$WORKTREE_NAME -b $BRANCH main
fi

# Exclude TODO.md from worktree checkout — it lives on main only
git -C .worktrees/$WORKTREE_NAME sparse-checkout set --no-cone '/*' '!TODO.md'

cd .worktrees/$WORKTREE_NAME
```

Run baseline test check using `test_cmd` from Jackal Config:
```bash
$TEST_CMD --tb=no -q 2>/dev/null | tail -3
```

Report pass/fail. If failures predate this issue, note them but do not block.

Update issue doc Assignment Notes (if issue doc exists):
```
Assigned: YYYY-MM-DD
Worktree: .worktrees/[WORKTREE_NAME]
Branch: [BRANCH]
```

---

## Step 4: Check Implementation Guidance

```bash
cat .ed3d/implementation-plan-guidance.md 2>/dev/null
```

Incorporate any project-specific guidance.

---

## Step 5: Write Implementation Plan

**REQUIRED SUB-SKILL:** `ed3d-plan-and-execute:writing-implementation-plans`

Announce: "I'm using writing-implementation-plans to create the detailed plan."

**Pass these instructions:**
- Always write all phases to disk — do not ask about interactive review mode
- Verify codebase state with `codebase-investigator` before each phase
- Use the project's `test_cmd` from Jackal Config for test verification
- Implementation plans go in: `$IMPL_PLANS/YYYY-MM-DD-{ISSUE-ID}-{slug}/phase_NN.md`

---

## Step 6: Execution Handoff

```bash
WORKTREE_ABS=$(git worktree list | grep "$WORKTREE_NAME" | awk '{print $1}')
PLAN_DIR=$(ls -d ${WORKTREE_ABS}/$IMPL_PLANS/20*/ 2>/dev/null | sort | tail -1)
echo "Worktree: $WORKTREE_ABS"
echo "Plan dir: $PLAN_DIR"
```

**CRITICAL — worktree-first rule:** Any agent dispatched for implementation MUST have its working directory set to `WORKTREE_ABS`. The prompt MUST begin with:
```
Working directory: [WORKTREE_ABS]
All file edits, git add, and git commit must be run from this directory.
cd [WORKTREE_ABS]
```

Output:
```
Implementation plan ready for [ISSUE-ID]: [title]

Worktree: [WORKTREE_ABS]
Plan:     [PLAN_DIR]

⚠️  Copy this command BEFORE running /clear — /clear will erase this message.

/execute-implementation-plan [PLAN_DIR] [WORKTREE_ABS]

Steps:
1. Copy the command above
2. /clear
3. Paste and run

When execution completes, run /jackal-finish-branch from the worktree.

Note: /execute-implementation-plan is the ed3d-plan-and-execute skill — there is no Jackal wrapper for this step. All other steps in the cycle use /jackal-* skills.
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Asking "do you want a worktree?" | Never ask — always create |
| Asking about branch name | Always auto-generate |
| Asking "write all or interactive?" | Always write all phases to disk |
| Skipping design plan for Complex issues | Stop and direct user to /jackal-design-plan |
| Using hardcoded test command | Always use `test_cmd` from Jackal Config |
| Mentioning worktree path as prose context | All work must happen inside the worktree. Any agent dispatched for implementation MUST start its prompt with `cd [WORKTREE_ABS]` as the literal first instruction. |
