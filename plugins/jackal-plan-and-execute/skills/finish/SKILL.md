---
name: finish
description: Completes a development branch — verifies tests, presents merge/PR/keep/discard options, updates project context, and cleans up worktree.
user-invocable: true
---

# Finish

Complete a development branch after implementation passes review.

---

## Process

### 1. UI Verification (if applicable)

Before running tests, check whether this branch touched any UI files:

```bash
git diff --name-only main...[feature-branch] | grep -E '^ui/|\.tsx$|\.jsx$|\.css$|\.scss$'
```

If any UI files changed: invoke `jackal-ui-verify` with the issue ID. **Do not proceed to merge until it reports ✅ PASS.**

If no UI files changed: skip this step.

### 2. Verify Tests Pass

```bash
$TEST_CMD
```

If tests fail → stop. Report failures. Don't proceed.

### 2. Present Options

```
Implementation complete. Options:

1. Merge back to main locally
2. Push and create a Pull Request
3. Keep the branch as-is (more work needed / I'll handle it)
4. Discard this work
```

### 3. Execute Choice

**Option 1 — Merge locally:**
```bash
git checkout main
git pull
git merge [feature-branch]
$TEST_CMD                    # verify merged result
git branch -d [feature-branch]
```

**Option 2 — Push and create PR:**
```bash
git push -u origin [feature-branch]
gh pr create --title "[ISSUE-ID]: [title]" --body "..."
```

If project uses CodeCommit (check `pr_method` in Jackal Config):
```
Branch pushed. Create PR via:
aws codecommit create-pull-request ...
```

**Option 3 — Keep:**
Report branch and worktree location. Done.

**Option 4 — Discard:**
Require typed "discard" confirmation. Then:
```bash
git checkout main
git branch -D [feature-branch]
```

### 4. Update Project Context

For Options 1 and 2, dispatch the project-claude-librarian (if available) to update CLAUDE.md files if contracts changed:

```xml
<invoke name="Agent">
<parameter name="subagent_type">ed3d-extending-claude:project-claude-librarian</parameter>
<parameter name="description">Updating project context</parameter>
<parameter name="prompt">
Review changes on [feature-branch] vs main.
Update CLAUDE.md files if API contracts or project structure changed.
Working directory: [path]
</parameter>
</invoke>
```

If the plugin isn't available, skip this step.

### 5. Update TODO.md and Issue Doc

For Options 1 and 2:
- Issue doc: set Status → Done
- TODO.md: remove from Active, append to Resolved with today's date
- Update "Last updated" line

For Option 4:
- Remove from Active, don't add to Resolved

### 6. Clean Up Worktree

For Options 1, 2, 4:
```bash
git worktree remove [worktree-path]
```

For Option 3: keep worktree.

### 7. Test Plan Reminder

If `docs/test-plans/` has a file matching this issue, remind the user it exists.

---

## Autonomous Mode

When called from the continuous execution loop (Backlog mode), the orchestrator should:
- Always choose Option 1 (merge locally) without asking
- Skip the "present options" step
- Proceed directly to merge, update, cleanup

The 4-option menu is for interactive use only.
