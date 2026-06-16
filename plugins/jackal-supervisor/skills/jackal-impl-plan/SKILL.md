---
name: jackal-impl-plan
description: Create an implementation plan for a Standard or Complex issue. Reuses the worktree assigned by /jackal-design-plan (Complex) or creates one (Standard). Second step in the Jackal dev cycle.
user-invocable: true
---

# Jackal Implementation Plan

Wrapper that adds supervisor integration around the `plan` skill.

**Worktree ownership:** This skill **does not own** worktree creation for Complex issues — `jackal-design-plan` does. This skill reads the `## Worktree` block from the issue doc and reuses it. For Standard issues that skip design, this skill creates the worktree itself (single owner per code path).

---

## Step 0: Load Project Config

Read `## Jackal Config` from CLAUDE.md. Extract:
- `repo_root`, `issue_prefix`, `issue_docs`, `design_plans`, `impl_plans`, `modules`, `test_cmd`
- `backend` — `github` or `todo-md` (default: `github`)
- `gh_repo` — `owner/repo` (required when `backend: github`)
- `label_style` — `slash` or `colon` (default: `slash`) — separator for status labels; examples
  below use `/`, substitute `:` if `colon`

## Step 1: Resolve Input

Accept: design plan path, issue doc path, or issue ID.

- Design plan provided → resolve associated issue doc from filename or design plan front-matter
- Issue doc for Standard issue → planner will auto-generate mini design
- Issue doc for Complex issue with no design plan → STOP, redirect to `/jackal-design-plan`
- Simple issue → STOP, redirect to direct implementor dispatch

## Step 2: Resolve Worktree

**Read the `## Worktree` block from the issue doc.** Parse `branch:` and `path:` fields.

```bash
ISSUE_DOC="$REPO_ROOT/$ISSUE_DOCS/${ISSUE_ID}-${SLUG}.md"
WORKTREE_REL=$(awk '/^## Worktree/{flag=1; next} /^## /{flag=0} flag && /- path:/{print $3}' "$ISSUE_DOC")
BRANCH=$(awk '/^## Worktree/{flag=1; next} /^## /{flag=0} flag && /- branch:/{print $3}' "$ISSUE_DOC")
```

**Three cases:**

1. **Block found and `$REPO_ROOT/$WORKTREE_REL` exists** → reuse it.
   ```bash
   WORKTREE_PATH="$REPO_ROOT/$WORKTREE_REL"
   ```
   Verify the worktree is on the expected branch:
   ```bash
   cd "$WORKTREE_PATH" && git branch --show-current
   ```
   If branch mismatches → warn but proceed.

2. **Block found but path missing** (e.g., worktree was removed) → recreate at the same path/branch:
   ```bash
   cd "$REPO_ROOT"
   git worktree add "$REPO_ROOT/$WORKTREE_REL" "$BRANCH" || \
     git worktree add "$REPO_ROOT/$WORKTREE_REL" -b "$BRANCH" main
   ```

3. **No block found** (Standard issue that skipped /jackal-design-plan) → run conflict gate, create worktree, persist `## Worktree` block to issue doc:

   ```bash
   cd "$REPO_ROOT"
   for branch in $(git branch --list 'feature/*' | tr -d ' '); do
     echo "=== $branch ==="
     git diff --name-only main...$branch 2>/dev/null
   done
   ```

   Compare against scope from the design plan or issue doc. Block on file-level conflict, warn on directory-level.

   ```bash
   ISSUE="24"            # GitHub issue number (the work-unit key)
   SLUG="kebab-title"
   TYPE="feat"           # conventional-commit type: feat|fix|docs|chore|refactor|...

   WORKTREE_REL=".worktrees/${ISSUE}-${SLUG}"
   WORKTREE_PATH="$REPO_ROOT/$WORKTREE_REL"
   BRANCH="${TYPE}/${ISSUE}-${SLUG}"

   grep -q "\.worktrees" "$REPO_ROOT/.gitignore" || echo ".worktrees/" >> "$REPO_ROOT/.gitignore"
   BASE="$(git -C "$REPO_ROOT" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#origin/##')"
   : "${BASE:=main}"
   git worktree add "$WORKTREE_PATH" -b "$BRANCH" "$BASE"
   ```

   Append `## Worktree` block to the issue doc with `branch:`, `path:`, `created:`. Set `**Status:** In Progress`. Commit the issue doc update from `$REPO_ROOT` so it lands on main:

   ```bash
   cd "$REPO_ROOT"
   git add "$ISSUE_DOC"
   git commit -m "chore: assign worktree for #${ISSUE}"
   ```

**Critical:** never silently bail. If the worktree resolution fails for any reason, report exactly what was tried and what failed — the user shouldn't see "could not find worktree" with no detail.

## Step 3: Update Backlog State

**If `backend: github`:**

Skip if Status is already `In Progress` (Complex issues already had this set during /jackal-design-plan). Otherwise, for Standard issues that skipped design:

```bash
GH_ISSUE_NUM=$(echo "$ISSUE_ID" | grep -oE '[0-9]+$')

gh issue edit "$GH_ISSUE_NUM" --repo "$GH_REPO" \
  --add-label "status/in-progress" \
  --remove-label "status/ready"

gh issue comment "$GH_ISSUE_NUM" --repo "$GH_REPO" --body "$(cat <<EOF
**Worktree assigned** — implementation planning starting

- Branch: \`${BRANCH}\`
- Worktree: \`${WORKTREE_PATH}\`
EOF
)"
```

**If `backend: todo-md`:** move the row from Ready to Active in TODO.md if not already there.

## Step 4: Invoke Plan Skill

Use `Skill("jackal-plan-and-execute:plan")` with:
- `WORKTREE_PATH` — absolute path (already resolved/created)
- `BRANCH`
- `DESIGN_PATH` — design plan or issue doc path
- `TEST_CMD`
- `IMPL_PLANS` — relative path from repo root

The `plan` skill skips its own worktree creation when `WORKTREE_PATH` is provided, dispatches the planner agent, writes phase files, and starts execution.

## Step 5: Execution Starts Automatically

The plan skill flows directly into the execute skill. No handoff ceremony needed.

If running in autonomous mode (backlog execution), everything from this point is automatic until the issue is done or the orchestrator gets stuck.
