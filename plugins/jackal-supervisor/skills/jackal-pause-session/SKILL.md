---
name: jackal-pause-session
description: Gracefully pause an in-progress issue in any Jackal-managed project — records the current phase and next step in the issue doc, marks it paused in the backlog (GitHub issue label by default, or TODO.md), and commits the checkpoint so the supervisor can surface it and give the exact resume command later.
user-invocable: true
---

# Jackal Pause Session

Records a clean checkpoint when you're stopping work mid-issue.

**Announce at start:** "I'm using jackal-pause-session to record a checkpoint for [ISSUE-ID]."

---

## Step 0: Load Project Config

Read the **## Jackal Config** section from the project's CLAUDE.md. Extract:
- `repo_root`, `issue_prefix`, `issue_docs`
- `backend` — `github` or `todo-md` (default: `github`)
- `gh_repo` — `owner/repo` (required when `backend: github`)
- `label_style` — `slash` or `colon` (default: `slash`) — separator for status labels; examples
  below use `/`, substitute `:` if `colon`

---

## When to Use

- Stopping work mid-design, mid-impl-plan, or mid-execution
- Waiting on an external decision before proceeding
- Context-switching to another issue
- Ending the session and not returning immediately

---

## Step 1: Resolve Input

**Accepts any combination of:**
- Issue ID: `PREFIX-XXX`
- Reason for pausing (freeform text)

Examples:
```
/jackal-pause-session                                    # detect from branch, ask reason
/jackal-pause-session PREFIX-35                          # explicit ID, ask reason
/jackal-pause-session PREFIX-35 waiting on infra         # explicit ID + reason
/jackal-pause-session waiting on design approval         # detect ID from branch
```

**Detect issue ID** (if not provided):
```bash
BRANCH=$(git branch --show-current)
# bare-integer scheme: <type>/<issue#>-slug  (e.g. feat/24-foo → 24)
ISSUE_ID=$(echo "$BRANCH" | grep -oE '(^|/)[0-9]+(-|$)' | grep -oE '[0-9]+' | head -1)
# legacy prefixed scheme fallback: <type>/<module>/PREFIX-46-slug → PREFIX-46
[ -z "$ISSUE_ID" ] && ISSUE_ID=$(echo "$BRANCH" | grep -oE '[A-Z]{2,}-[0-9]+[a-z]?' | head -1)
```

**Find the issue doc:**
```bash
ls $REPO_ROOT/$ISSUE_DOCS/ | grep "PREFIX-XXX"
```

Confirm Status is "In Progress".

---

## Step 2: Determine the Checkpoint

**First: check the live task list before asking the user anything.**

Use TaskList to read the current session's tasks. The jackal design and implementation skills create tasks for each phase.

**If tasks exist:**
- Completed tasks → phases already done
- `in_progress` task → the phase we're currently in
- Pending tasks → what comes next

**If no tasks exist** — fall back to git evidence:
```bash
git log --oneline -5
ls $REPO_ROOT/$DESIGN_PLANS/ | grep PREFIX-XXX
ls $REPO_ROOT/$IMPL_PLANS/ | grep -i PREFIX-XXX
```

**Only ask the user for what you genuinely can't determine:**
> "I can see [inferred state]. Why are you pausing? Any context I should record?"

If waiting on something external → route to Blocked status.

---

## Step 3: Write the Checkpoint

**Format as a single compact line:**
```
[phase + what's done] — next: [immediate next action] [| note: <optional context>]
```

The resume command must be runnable as-is. `/execute` takes `[plan-directory] [working-directory]` — always include the worktree as the second arg, since resuming usually starts from the repo root, not inside the worktree.

Examples:
- `Design Phase 3 done — next: /jackal-impl-plan $DESIGN_PLANS/2026-04-05-PREFIX-46.md`
- `Impl Phase 2 complete — next: /execute <worktree>/docs/implementation-plans/<slug>/ <worktree>` (resumes at Phase 3)
- `Impl plan exists, execution not started — next: /execute <worktree>/docs/implementation-plans/<slug>/ <worktree>`

---

## Step 4: Update the Issue Doc

Edit `$ISSUE_DOCS/PREFIX-XXX-*.md`:

1. `**Status:** In Progress` → `**Status:** Paused` (or `Blocked`)
2. Set `**Last Checkpoint:**` to the checkpoint string
3. If blocked, add to **Dependencies**: `- Blocked by: [what you're waiting for]`

---

## Step 5: Update Backlog State

**If `backend: github`:**

```bash
GH_ISSUE_NUM=$(echo "$ISSUE_ID" | grep -oE '[0-9]+$')
NEW_LABEL="status/paused"   # or "status/blocked" if blocked (use ':' if label_style: colon)
OLD_LABEL="status/in-progress"

gh issue edit "$GH_ISSUE_NUM" --repo "$GH_REPO" \
  --add-label "$NEW_LABEL" \
  --remove-label "$OLD_LABEL"

gh issue comment "$GH_ISSUE_NUM" --repo "$GH_REPO" --body "$(cat <<EOF
**Paused** — checkpoint recorded

- Status: ${NEW_LABEL#status:}
- Checkpoint: ${CHECKPOINT_STRING}
- Branch: \`${BRANCH}\`
- Worktree: \`${WORKTREE_PATH}\`

To resume: ask the supervisor "resume ${ISSUE_ID}".
EOF
)"
```

**If `backend: todo-md`:**

```bash
sed '/RESOLVED_SECTION_START/q' $REPO_ROOT/TODO.md
```

Move the row from **Active** to the appropriate table:
- Paused → `## Paused` (columns: ID | Title | Branch | Checkpoint | Detail)
- Blocked → `## Blocked` (columns: ID | Title | Blocker | Detail)

The Paused row format:
```
| 24 | [title ≤6 words] | feat/24-slug | [checkpoint ~50 chars] | [doc]($ISSUE_DOCS/24-slug.md) |
```

Update "Last updated" date — set to `Last updated: YYYY-MM-DD`, date only, no commentary.

---

## Step 6: Commit the Checkpoint

```bash
cd $REPO_ROOT
# backend=github: only the issue doc changed
# backend=todo-md: TODO.md also changed
if [ "$BACKEND" = "github" ]; then
  git add $ISSUE_DOCS/PREFIX-XXX-*.md
else
  git add $ISSUE_DOCS/PREFIX-XXX-*.md TODO.md
fi
git commit -m "chore: pause PREFIX-XXX — checkpoint: [brief phrase]"
```

Do NOT push — local checkpoint commit only.

---

## Step 7: Confirm to the User

```
✅ Checkpoint recorded for PREFIX-XXX — [title]

Status: Paused
Checkpoint: [the checkpoint string]

When ready to resume:
  Ask the supervisor: "resume PREFIX-XXX"
  → It will read the checkpoint and give you the exact resume command.

Worktree preserved at: .worktrees/24-slug
Branch preserved: feat/24-slug
```

---

## Edge Cases

**Work was interrupted (no context on current phase):**
Examine git evidence, synthesize a best-effort checkpoint, confirm with user:
```
Based on commits and docs:
- Last commit: [message, N hours ago]
- Design plan: [exists / missing]
- Impl plan: [exists / missing]

Best-guess checkpoint: [inferred state]
Does this look right?
```

**Multiple issues in flight:**
If the user doesn't specify which to pause, list Active ones and ask.
