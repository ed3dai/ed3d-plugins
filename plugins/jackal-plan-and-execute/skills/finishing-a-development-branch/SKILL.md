---
name: finishing-a-development-branch
description: Use when implementation is complete, all tests pass, and you need to decide how to integrate the work - guides completion of development work by presenting structured options for merge, PR, or cleanup
user-invocable: false
---

# Finishing a Development Branch

## Overview

Guide completion of development work by presenting clear options and handling chosen workflow.

**Core principle:** Verify tests → Present options → Execute choice → Update project context → Clean up.

**Announce at start:** "I'm using the finishing-a-development-branch skill to complete this work."

## The Process

### Step 1: Verify Tests

**Before presenting options, verify tests pass:**

```bash
# Run project's test suite
npm test / cargo test / pytest / go test ./...
```

**If tests fail:**
```
Tests failing (<N> failures). Must fix before completing:

[Show failures]

Cannot proceed with merge/PR until tests pass.
```

Stop. Don't proceed to Step 2.

**If tests pass:** Continue to Step 2.

### Step 2: Determine Base Branch

```bash
# Try common base branches
git merge-base HEAD main 2>/dev/null || git merge-base HEAD master 2>/dev/null
```

Or ask: "This branch split from main - is that correct?"

### Step 3: Present Options

Present exactly these 4 options in `AskUserQuestion`.

```
Implementation complete. What would you like to do?

1. Merge back to <base-branch> locally
2. Push and create a Pull Request
3. Keep the branch as-is (I'll handle it later, or I have more work to do)
4. Discard this work

Which option?
```

**Don't add explanation** - keep options concise.

### Step 4: Execute Choice

#### Option 1: Merge Locally

```bash
# Switch to base branch
git checkout <base-branch>

# Pull latest
git pull

# Merge feature branch
git merge <feature-branch>

# Verify tests on merged result
<test command>

# If tests pass
git branch -d <feature-branch>
```

Then: Update project context (Step 5), then cleanup worktree (Step 6)

#### Option 2: Push and Create PR

```bash
# Push branch
git push -u origin <feature-branch>

# Create PR
gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary
<2-3 bullets of what changed>

## Test Plan
- [ ] <verification steps>
EOF
)"
```

Then: Update project context (Step 5), then cleanup worktree (Step 6)

#### Option 3: Keep As-Is

Report: "Keeping branch <name>. Worktree preserved at <path>."

**Don't cleanup worktree.**

#### Option 4: Discard

**Confirm first:**
```
This will permanently delete:
- Branch <name>
- All commits: <commit-list>
- Worktree at <path>

Type 'discard' to confirm.
```

Wait for exact confirmation.

If confirmed:
```bash
git checkout <base-branch>
git branch -D <feature-branch>
```

Then: Cleanup worktree (Step 6)

### Step 5: Update Project Context

Before merging or creating a PR, invoke `ed3d-extending-claude:project-claude-librarian` to update CLAUDE.md files if contracts or structure changed.

```
<invoke name="Task">
<parameter name="subagent_type">ed3d-extending-claude:project-claude-librarian</parameter>
<parameter name="description">Updating project context for <branch-name></parameter>
<parameter name="prompt">
  Review what changed in this branch and update CLAUDE.md files if contracts or structure changed.

  Base branch: <base-branch>
  Feature branch: <feature-branch>
  Working directory: <directory>

  Follow the ed3d-extending-claude:maintaining-project-context skill to:
  1. Diff against base branch to see what changed
  2. Identify contract/API/structure changes
  3. Update affected CLAUDE.md files
  4. Commit documentation updates with message: "docs: update project context for <branch-name>"

  Report back with what was updated (or that no updates were needed).
</parameter>
</invoke>
```

**If librarian commits updates:** Include those commits in the merge/PR.
**If librarian reports no updates needed:** Proceed with chosen option.
**If librarian subagent is not available:** skip this step, saying aloud that you're skipping it because the `ed3d-extending-claude` plugin is not available.

**Skip this step for Option 4 (Discard).**

### Step 6: Cleanup Worktree

**For Options 1, 2, 4:**

Check if in worktree:
```bash
git worktree list | grep $(git branch --show-current)
```

If yes:
```bash
git worktree remove <worktree-path>
```

**For Option 3:** Keep worktree.

### Step 7: Remind About Test Plan

**For Options 1, 2, and 3:**

If a human test plan was generated (check `docs/test-plans/`), remind the user:

```
Human test plan available at: docs/test-plans/<plan-name>.md

This documents:
- What automated tests cover
- What requires human verification
- End-to-end scenarios to manually test

Review before considering this work fully complete.
```

**Skip for Option 4 (Discard).**

## Quick Reference

| Option | Merge | Push | Update Context | Keep Worktree | Cleanup Branch | Test Plan Reminder |
|--------|-------|------|----------------|---------------|----------------|-------------------|
| 1. Merge locally | ✓ | - | ✓ | - | ✓ | ✓ |
| 2. Create PR | - | ✓ | ✓ | ✓ | - | ✓ |
| 3. Keep as-is | - | - | - | ✓ | - | ✓ |
| 4. Discard | - | - | - | - | ✓ (force) | - |

## Common Mistakes

**Skipping test verification**
- **Problem:** Merge broken code, create failing PR
- **Fix:** Always verify tests before offering options

**Open-ended questions**
- **Problem:** "What should I do next?" → ambiguous
- **Fix:** Present exactly 4 structured options

**Automatic worktree cleanup**
- **Problem:** Remove worktree when might need it (Option 2, 3)
- **Fix:** Only cleanup for Options 1 and 4

**No confirmation for discard**
- **Problem:** Accidentally delete work
- **Fix:** Require typed "discard" confirmation

## Red Flags

**Never:**
- Proceed with failing tests
- Merge without verifying tests on result
- Delete work without confirmation
- Force-push without explicit request

**Always:**
- Verify tests before offering options
- Present exactly 4 options
- Get typed confirmation for Option 4
- Clean up worktree for Options 1 & 4 only
- Remind about human test plan for Options 1, 2 & 3 (if exists)

## Integration

**Called by:**
- **executing-an-implementation-plan** - After all tasks complete

**Pairs with:**
- **using-git-worktrees** - Cleans up worktree created by that skill
