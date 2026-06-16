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

Read `ui_path` from the Jackal Config in CLAUDE.md. Check whether this branch touched any files under that path:

```bash
UI_PATH=$(grep 'ui_path' CLAUDE.md | awk '{print $2}')
git diff --name-only main...[feature-branch] | grep "^${UI_PATH}"
```

If any UI files changed: invoke `jackal-ui-verify` with the issue ID. **Do not proceed to merge until it reports ✅ PASS.**

If no UI files changed: skip this step.

### 2. Verify Tests Pass

```bash
$TEST_CMD
```

If tests fail → stop. Report failures. Don't proceed.

### 2a. Detect Protected Main

Determine whether `main` is protected — this decides the **default** completion path and whether
local merge is even allowed. Resolve in precedence order (first signal wins):

1. `.jackal/harness-guidance.md` merge-strategy override (e.g. "always open a PR, never merge locally")
2. `protected_main: true` in the Jackal Config
3. Best-effort detection (cached per session, network-optional):
   ```bash
   gh api "repos/$GH_REPO/branches/main/protection" >/dev/null 2>&1 && echo protected || echo open
   ```

If main is protected, **Option 1 (local merge) is unavailable** — the harness must open a PR.

### 3. Present Options

```
Implementation complete. Options:

1. Merge back to main locally   (UNAVAILABLE if main is protected)
2. Push and create a Pull Request
3. Keep the branch as-is (more work needed / I'll handle it)
4. Discard this work
```

If main is protected, say so and present 2–4 only.

### 4. Execute Choice

**Option 1 — Merge locally** (only when main is NOT protected):
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
```

Build the PR body from the repo's template if one exists, so required sections are filled rather
than left blank:
```bash
TEMPLATE=$(ls .github/PULL_REQUEST_TEMPLATE.md .github/pull_request_template.md 2>/dev/null | head -1)
```
- If a template exists: fill each section (e.g. What changed / Closes #N / How to verify / Risk /
  Docs updated / Gates) from the issue ACs and the diff. Include `Closes #<issue>` so the merge
  auto-closes the issue.
- If no template: use a concise default body (summary + `Closes #N` + test results).

```bash
gh pr create --title "[ISSUE-ID]: [title]" --body "$PR_BODY"
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

### 5. Update Project Context

For Options 1 and 2, dispatch the project-claude-librarian to update CLAUDE.md files if contracts
changed. This agent ships in the `ed3d-extending-claude` plugin — a **declared dependency** of the
jackal harness (see the marketplace README's "Required dependencies").

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

**If `ed3d-extending-claude` is not installed, do NOT silently skip.** Emit a visible warning so the
human knows the closeout was incomplete — some projects (e.g. ROAR) make CLAUDE.md freshness
re-verification at branch closeout *mandatory*, and a silent skip means a documented contract may
have gone stale unnoticed:

```
⚠️  CLAUDE.md freshness re-verification SKIPPED — ed3d-extending-claude (project-claude-librarian)
    is not installed. If this project requires doc closeout (check its documentation standard),
    update the touched CLAUDE.md files and their `Last verified:` dates manually before merging.
```

### 6. Update Backlog State and Issue Doc

Read `backend` from `## Jackal Config`. The wrapper (`jackal-finish-branch`) handles GitHub-side updates (labels, comment, close) for Options 1 and 2. This skill's job is local file updates only.

For Options 1 and 2:
- Issue doc: set Status → Done
- If `backend: todo-md`: remove from Active, append to Resolved with today's date, update "Last updated" line
- If `backend: github`: skip TODO.md updates (GH is the source of truth — the wrapper closes the issue)

For Option 4:
- If `backend: todo-md`: remove from Active, don't add to Resolved
- If `backend: github`: leave the issue open with `status/ready` (work was discarded — issue is still pending)

### 7. Clean Up Worktree

For Options 1, 2, 4:
```bash
git worktree remove [worktree-path]
```

For Option 3: keep worktree.

### 8. Test Plan Reminder

If `docs/test-plans/` has a file matching this issue, remind the user it exists.

---

## Autonomous Mode

When called from the continuous execution loop (Backlog mode), the orchestrator should skip the
"present options" step and pick the default for the repo based on the **Detect Protected Main** check
(step 2a):

- **Main is protected** → push the branch and open a PR (Option 2). Do **not** attempt a local merge —
  it would be rejected and violates the protected-main invariant. Record the PR URL, then continue
  the loop to the next issue rather than blocking on a human merge.
- **Main is open** → merge locally (Option 1) without asking, then proceed to update + cleanup.

The 4-option menu is for interactive use only. The protected-main default is non-negotiable in
autonomous mode: the loop never self-merges to a protected `main`.
