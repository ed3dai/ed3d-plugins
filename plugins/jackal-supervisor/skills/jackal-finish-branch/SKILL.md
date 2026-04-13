---
name: jackal-finish-branch
description: Generic branch completion skill. Wraps jackal-plan-and-execute:finishing-a-development-branch with project-specific overrides read from the ## Jackal Config section in this project's CLAUDE.md — correct git remote, push command, test command, PR method, and TODO.md Resolved update.
user-invocable: true
---

# Jackal Finish Branch

Generic wrapper around `jackal-plan-and-execute:finishing-a-development-branch`.

**Announce at start:** "I'm using jackal-finish-branch to complete this work."

---

## Step 0: Load Project Config

Read the **## Jackal Config** section from the project's CLAUDE.md. Extract:

| Variable | Key | Example (ATLAS) |
|----------|-----|-----------------|
| `$TEST_CMD` | `test_cmd` | `/Users/.../python -m pytest --tb=short -q` |
| `$GIT_REMOTE` | `git_remote` | `atlas` |
| `$PUSH_CMD` | `push_cmd` | `AWS_PROFILE=DataWarehouse-UAT git push atlas` |
| `$PR_METHOD` | `pr_method` | `codecommit` or `github` |
| `$UI_PATH` | `ui_path` | `market-analysis-tool/ui/` (blank if no UI) |
| `$ISSUE_DOCS` | `issue_docs` | `docs/issues` |
| `$REPO_ROOT` | `repo_root` | `/Users/.../ATLAS` |

---

## Step 1: UI Verification Gate

**Run before anything else** (only if `ui_path` is configured in Jackal Config).

```bash
git diff --name-only main..$(git branch --show-current) | grep -q "$UI_PATH"
```

**If UI files are in the diff** — invoke `jackal-ui-verify` automatically using the Skill tool. Do not stop and ask the user.

```
Skill("jackal-ui-verify")
```

- If `jackal-ui-verify` reports ✅ PASS → proceed to Step 2.
- If `jackal-ui-verify` reports ❌ FAIL → stop. Report the specific failures to the user. Do not proceed until they are resolved.

**If no UI files or no `ui_path` configured** — proceed directly to Step 2.

---

## Step 2: Run ed3d Finishing Flow

**REQUIRED SUB-SKILL:** `jackal-plan-and-execute:finishing-a-development-branch`

Announce: "I'm using finishing-a-development-branch with project overrides."

Apply these overrides throughout the sub-skill:

### Test command override

Wherever the sub-skill runs tests, use `$TEST_CMD` from Jackal Config — not bare `pytest` or any other default.

### Push override

Replace the sub-skill's push command with `$PUSH_CMD`:

```bash
$PUSH_CMD $BRANCH
```

**If `pr_method` is `codecommit`** — do NOT run `gh pr create`. Output instead:
```
Branch pushed. To open a pull request:

aws codecommit create-pull-request \
  --title "[ISSUE_ID]: [title]" \
  --targets "repositoryName=[repo-name],sourceReference=$BRANCH,destinationReference=main" \
  --profile [aws-profile]

Or visit the CodeCommit console.
```

**If `pr_method` is `github`** — run `gh pr create` as normal.

### Pull override (Option 1 — merge locally)

Before merging, pull from the configured remote:
```bash
git checkout main
git pull $GIT_REMOTE main
git merge $BRANCH
```

---

## Step 3: Post-Completion — Update TODO.md and Issue Doc

Run this **after the ed3d sub-skill completes** for Options 1 (merge) or 2 (push/PR).

**Skip for Options 3 (keep) and 4 (discard).**

### 3a. Find the issue

```bash
BRANCH=$(git branch --show-current 2>/dev/null || git log -1 --format='%D' | grep -o 'feature/[^ ,]*' | head -1)
ISSUE_ID=$(echo $BRANCH | grep -o "${ISSUE_PREFIX}-[0-9]*")
ISSUE_DOC=$(ls $REPO_ROOT/$ISSUE_DOCS/${ISSUE_ID}*.md 2>/dev/null | head -1)
TODAY=$(date +%Y-%m-%d)
```

### 3b. Update issue doc

Set `**Status:** Done`. Use the Edit tool — change only that line.

### 3c. Update TODO.md

Using Read + Edit tools (surgical edits only — never rewrite the whole file):
1. Remove the issue's row from the **Active** table
2. Append to the **Resolved** section (below `<!-- RESOLVED_SECTION_START -->`):
   ```
   | PREFIX-XXX | [short title from issue doc] | YYYY-MM-DD |
   ```
3. Update "Last updated" at the top of the file — set to `Last updated: YYYY-MM-DD`, date only, no commentary

**For Option 4 (Discard):** remove from Active, do NOT add to Resolved.

---

## Step 4: Review Jackal Config for Updates

After `project-claude-librarian` runs (invoked by the ed3d sub-skill), also review the **## Jackal Config** section:

- Did implementation reveal a new module that should be in the module map?
- Did a port change? Did the test command change?
- Did a new service get added that needs a port entry?

If yes, update `## Jackal Config` in `CLAUDE.md` and also update `~/.claude/port-registry.md` if ports changed.

---

## What the ed3d Sub-Skill Handles (no changes needed)

- Test verification gate (uses our `$TEST_CMD` override)
- Base branch detection
- 4-option menu (merge / push / keep / discard)
- `project-claude-librarian` invocation for CLAUDE.md updates
- Worktree removal (Options 1 and 4)
- Human test plan reminder

---

## Quick Reference

| Step | Owner |
|------|-------|
| UI verify gate | `jackal-finish-branch` (Step 1) |
| Tests, options, merge/push, librarian, cleanup | `finishing-a-development-branch` (Step 2) |
| TODO.md + issue doc update | `jackal-finish-branch` (Step 3) |
| Jackal Config review | `jackal-finish-branch` (Step 4) |
