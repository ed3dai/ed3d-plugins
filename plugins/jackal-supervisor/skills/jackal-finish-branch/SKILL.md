---
name: jackal-finish-branch
description: Complete a development branch with project-specific overrides (remote, test command, PR method) and TODO.md updates.
user-invocable: true
---

# Jackal Finish Branch

Wrapper around the `finish` skill with project-specific configuration.

---

## Step 0: Load Project Config

Read `## Jackal Config` from CLAUDE.md. Extract:
- `test_cmd`, `git_remote`, `push_cmd`, `pr_method`, `ui_path`, `issue_docs`, `repo_root`
- `backend` — `github` or `todo-md` (default: `todo-md`)
- `gh_repo` — `owner/repo` (required when `backend: github`)

## Step 1: UI Verification Gate

Only if `ui_path` is configured:

```bash
git diff --name-only main..$(git branch --show-current) | grep -q "$UI_PATH"
```

If UI files changed → invoke `jackal-ui-verify`. Block if it fails.

## Step 2: Invoke Finish Skill

Use `Skill("jackal-plan-and-execute:finish")` with overrides:
- Test command: `$TEST_CMD`
- Push command: `$PUSH_CMD`
- PR method: `$PR_METHOD`

### Autonomous Mode Override

When called from the continuous execution loop:
- Skip the 4-option menu
- Merge locally (Option 1)
- Use `$GIT_REMOTE` for pull

## Step 3: Post-Completion Updates

After the finish skill completes (Options 1 or 2):

1. Find issue: extract the issue number from the branch name. New scheme
   `<type>/<issue#>-slug` (e.g. `feat/24-foo` → `24`); legacy `PREFIX-46` → `46`.
2. Update issue doc: Status → Done

**If `backend: github`:**

```bash
# bare-integer scheme first (feat/24-foo → 24), then legacy PREFIX-NN tail.
GH_ISSUE_NUM=$(echo "$BRANCH" | grep -oE '(^|/)[0-9]+(-|$)' | grep -oE '[0-9]+' | head -1)
[ -z "$GH_ISSUE_NUM" ] && GH_ISSUE_NUM=$(echo "$ISSUE_ID" | grep -oE '[0-9]+$')

# RESULT_URL = PR URL (Option 2) or merge commit SHA (Option 1)
gh issue comment "$GH_ISSUE_NUM" --repo "$GH_REPO" --body "$(cat <<EOF
**Completed** — branch finished

- Result: ${RESULT_URL}
- Branch: \`${BRANCH}\`
EOF
)"

gh issue edit "$GH_ISSUE_NUM" --repo "$GH_REPO" --remove-label "status:in-progress"

# Close on merge (Option 1) or local merge. For Option 2 (PR), leave open — GH closes
# automatically when the PR merges via "Closes #N" in the PR body.
if [ "$FINISH_OPTION" = "merge-local" ]; then
  gh issue close "$GH_ISSUE_NUM" --repo "$GH_REPO" --reason completed
fi
```

**If `backend: todo-md`:** update TODO.md: Active → Resolved, update "Last updated".

## Step 4: Jackal Config Review

Check if implementation revealed changes that should update Jackal Config:
- New module that needs a module map entry?
- Port change?
- New service?

If yes, update CLAUDE.md.
