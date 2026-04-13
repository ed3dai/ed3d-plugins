---
name: jackal-pause-session
description: Gracefully pause an in-progress issue in any Jackal-managed project — records the current phase and next step in the issue doc, moves it to Paused in TODO.md, and commits the checkpoint so the supervisor can surface it and give the exact resume command later.
user-invocable: true
---

# Jackal Pause Session

Records a clean checkpoint when you're stopping work mid-issue.

**Announce at start:** "I'm using jackal-pause-session to record a checkpoint for [ISSUE-ID]."

---

## Step 0: Load Project Config

Read the **## Jackal Config** section from the project's CLAUDE.md. Extract:
- `repo_root`, `issue_prefix`, `issue_docs`

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
git branch --show-current
```
Extract from branch name (e.g., `feature/ui/PREFIX-46-...` → `PREFIX-46`).

**Find the issue doc:**
```bash
ls $REPO_ROOT/$ISSUE_DOCS/ | grep "PREFIX-XXX"
```

Confirm Status is "In Progress".

---

## Step 2: Determine the Checkpoint

**First: check the live task list before asking the user anything.**

Use TaskList to read the current session's tasks. The ed3d design and implementation skills create tasks for each phase.

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

Examples:
- `Design Phase 3 done — next: /jackal-impl-plan $DESIGN_PLANS/2026-04-05-PREFIX-46.md`
- `Impl Phase 2 complete — next: resume Phase 3 in /execute-implementation-plan`
- `Impl plan exists, execution not started — next: /execute-implementation-plan $IMPL_PLANS/.../`

---

## Step 4: Update the Issue Doc

Edit `$ISSUE_DOCS/PREFIX-XXX-*.md`:

1. `**Status:** In Progress` → `**Status:** Paused` (or `Blocked`)
2. Set `**Last Checkpoint:**` to the checkpoint string
3. If blocked, add to **Dependencies**: `- Blocked by: [what you're waiting for]`

---

## Step 5: Update TODO.md

```bash
sed '/RESOLVED_SECTION_START/q' $REPO_ROOT/TODO.md
```

Move the row from **Active** to the appropriate table:
- Paused → `## Paused` (columns: ID | Title | Branch | Checkpoint | Detail)
- Blocked → `## Blocked` (columns: ID | Title | Blocker | Detail)

The Paused row format:
```
| PREFIX-XXX | [title ≤6 words] | feature/module/PREFIX-XXX-slug | [checkpoint ~50 chars] | [doc]($ISSUE_DOCS/PREFIX-XXX-slug.md) |
```

Update "Last updated" date — set to `Last updated: YYYY-MM-DD`, date only, no commentary.

---

## Step 6: Commit the Checkpoint

```bash
cd $REPO_ROOT
git add $ISSUE_DOCS/PREFIX-XXX-*.md TODO.md
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

Worktree preserved at: .worktrees/PREFIX-XXX-slug
Branch preserved: feature/module/PREFIX-XXX-slug
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
