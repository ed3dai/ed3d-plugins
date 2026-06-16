---
name: jackal-design-plan
description: Start a design for a Complex issue. Runs conflict gate if not yet assigned, then invokes the design skill. Use for Complex issues that need architectural decisions.
user-invocable: true
---

# Jackal Design Plan

Wrapper that integrates the supervisor at entry/exit of the design phase. **This skill owns worktree creation** for the issue. Downstream skills (`jackal-impl-plan`, `jackal-pause-session`, `jackal-finish-branch`) read the worktree path back from the issue doc.

---

## Step 0: Load Project Config

Read `## Jackal Config` from CLAUDE.md. Extract:
- `repo_root`, `issue_prefix`, `issue_docs`, `design_plans`, `modules`
- `backend` — `github` or `todo-md` (default: `github`)
- `gh_repo` — `owner/repo` (required when `backend: github`)
- `label_style` — `slash` or `colon` (default: `slash`) — separator for status labels; examples
  below use `/`, substitute `:` if `colon`

## Step 1: Resolve Input

Accept issue ID or issue doc path. Read the issue doc.

- If Complexity is not Complex → redirect to `/jackal-impl-plan` (Standard) or implementor (Simple)
- If a `## Worktree` block already exists in the issue doc → reuse it (skip step 2). This means design was started before and is being resumed.
- Otherwise → proceed to step 2

## Step 2: Conflict Gate + Create Worktree

Run conflict gate against active feature branches:

```bash
cd $REPO_ROOT
for branch in $(git branch --list 'feature/*' | tr -d ' '); do
  echo "=== $branch ==="
  git diff --name-only main...$branch 2>/dev/null
done
```

Compare candidate scope (from issue doc `In scope:`) against the active branch file sets.
- File-level overlap → block, name the conflicting branch
- Directory-level overlap, different files → warn, proceed
- No overlap → proceed

Derive names from the issue doc (never ask):

```bash
ISSUE="24"                # GitHub issue number (the work-unit key)
SLUG="kebab-title"        # from issue title
TYPE="feat"               # conventional-commit type: feat|fix|docs|chore|refactor|...

WORKTREE_PATH="$REPO_ROOT/.worktrees/${ISSUE}-${SLUG}"
BRANCH="${TYPE}/${ISSUE}-${SLUG}"

grep -q "\.worktrees" "$REPO_ROOT/.gitignore" || echo ".worktrees/" >> "$REPO_ROOT/.gitignore"

BASE="$(git -C "$REPO_ROOT" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#origin/##')"
: "${BASE:=main}"
if [ ! -d "$WORKTREE_PATH" ]; then
  cd "$REPO_ROOT"
  git worktree add "$WORKTREE_PATH" -b "$BRANCH" "$BASE"
fi
```

## Step 3: Persist Worktree to Issue Doc

Append (or replace) a `## Worktree` block in the issue doc. **This is the single source of truth** that `jackal-impl-plan` will read:

```markdown
## Worktree

- branch: feat/24-slug
- path: .worktrees/24-slug
- created: 2026-05-28
```

Use repo-root-relative paths in the doc so it's portable. Skills convert to absolute via `$REPO_ROOT/<path>` at read time.

Set `**Status:** In Progress` in the issue doc.

Commit the issue-doc update from `$REPO_ROOT` (this commit lands on `main`, not the feature branch):

```bash
cd "$REPO_ROOT"
git add "$ISSUE_DOCS/${ISSUE_ID}-${SLUG}.md"
git commit -m "chore: assign worktree for ${ISSUE_ID}"
```

## Step 4: Update Backlog State

**If `backend: github`:**

```bash
GH_ISSUE_NUM=$(echo "$ISSUE_ID" | grep -oE '[0-9]+$')

gh issue edit "$GH_ISSUE_NUM" --repo "$GH_REPO" \
  --add-label "status/in-progress" \
  --remove-label "status/ready"

gh issue comment "$GH_ISSUE_NUM" --repo "$GH_REPO" --body "$(cat <<EOF
**Worktree assigned** — design phase starting

- Branch: \`${BRANCH}\`
- Worktree: \`${WORKTREE_PATH}\`
- Issue doc: \`${ISSUE_DOCS}/${ISSUE_ID}-${SLUG}.md\`
EOF
)"
```

If `gh issue edit` fails because a label doesn't exist, report the missing label to the user and continue (the comment is still useful).

**If `backend: todo-md`:**

Move the row in `TODO.md` from Ready to Active. Update "Last updated" date.

## Step 5: Invoke Design Skill

Use `Skill("jackal-plan-and-execute:design")` with:
- `WORKTREE_PATH` — absolute path
- `BRANCH`
- `ISSUE_ID`, `SLUG`
- Issue doc content as pre-gathered context

The design skill runs from inside the worktree, so the design document commit lands on the feature branch.

## Step 6: Hand Off

After design commits:

```
Design complete for [ISSUE-ID].
Design plan: docs/design-plans/[filename]
Worktree: .worktrees/[issue#]-[slug]
Branch: [type]/[issue#]-[slug]

Next: /jackal-impl-plan docs/design-plans/[filename]
```

No /clear needed. `jackal-impl-plan` reads the `## Worktree` block from the issue doc to find the existing worktree.
