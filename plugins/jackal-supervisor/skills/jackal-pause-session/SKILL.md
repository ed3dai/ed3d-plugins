---
name: jackal-pause-session
description: Gracefully pause an in-progress issue in any Jackal-managed project — records the current phase and next step as a GitHub issue comment, swaps the issue's status label, and caches the checkpoint in gitignored local state so the supervisor can surface it and give the exact resume command later. Touches no tracked file and makes no commit.
user-invocable: true
argument-hint: "[issue-id] [reason]"
---

# Jackal Pause Session

Records a clean checkpoint when you're stopping work mid-issue.

**Announce at start:** "I'm using jackal-pause-session to record a checkpoint for [ISSUE-ID]."

---

## Step 0: Load Project Config

Read the **## Jackal Config** section from the project's CLAUDE.md. Extract:
- `repo_root`, `issue_prefix`, `issue_docs`
- `gh_repo` — `owner/repo` (required)
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
/jackal-supervisor:jackal-pause-session                            # detect from branch, ask reason
/jackal-supervisor:jackal-pause-session PREFIX-35                  # explicit ID, ask reason
/jackal-supervisor:jackal-pause-session PREFIX-35 waiting on infra # explicit ID + reason
/jackal-supervisor:jackal-pause-session waiting on design approval # detect ID from branch
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

**Resolve the worktree from git** (authoritative for what's on disk — same approach as
`jackal-impl-plan`), so the resume command in Step 3 can locate the plan directory:
```bash
ISSUE=$(echo "$ISSUE_ID" | grep -oE '[0-9]+$')
WORKTREE_PATH=$(git -C "$REPO_ROOT" worktree list --porcelain \
  | awk -v n="$ISSUE" '/^worktree /{p=$2} /^branch /{b=$2; if (b ~ ("/" n "-") || b ~ ("/" n "$")) print p}' \
  | head -1)
WORKTREE_REL="${WORKTREE_PATH#$REPO_ROOT/}"
```

Confirm the issue is in progress. Read this from the **GitHub issue's status label** (the durable
record), not the issue doc's `**Status:**` line — that tracked file is no longer updated by pause or
assignment:

```bash
gh issue view "$ISSUE" --repo "$GH_REPO" --json labels --jq '.labels[].name' | grep '^status'
```

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

The resume command must be runnable as-is — **namespaced `plugin:command`, since marketplace-installed commands never resolve bare.** `/jackal-plan-and-execute:execute` takes `[plan-directory] [working-directory]` — always include the worktree as the second arg, since resuming usually starts from the repo root, not inside the worktree.

**The plan directory must be a real path.** Build it from the project's `impl_plans`
config (e.g. `docs/impl-plans`), NOT a hardcoded `docs/implementation-plans/`. Before
emitting the resume command, confirm the directory actually exists:

```bash
ls "$REPO_ROOT/$WORKTREE_REL/$IMPL_PLANS/" 2>/dev/null   # find the real plan dir name
```

Use the actual dir name you find (format `YYYY-MM-DD-<issue#>-<slug>`), not a guessed one.

Examples (with `impl_plans: docs/impl-plans`):
- `Design Phase 3 done — next: /jackal-supervisor:jackal-impl-plan $DESIGN_PLANS/2026-04-05-46-slug.md`
- `Impl Phase 2 complete — next: /jackal-plan-and-execute:execute <worktree>/docs/impl-plans/2026-04-05-46-slug/ <worktree>` (resumes at Phase 3)
- `Impl plan exists, execution not started — next: /jackal-plan-and-execute:execute <worktree>/docs/impl-plans/2026-04-05-46-slug/ <worktree>`

---

## Step 4: Write the Local State Cache

**Do not edit `$ISSUE_DOCS/PREFIX-XXX-*.md`.** `docs/issue-docs/` is **tracked** in git, so editing
it at the repo root dirties the tracked working tree on `main`. Pause state is ephemeral session
metadata — write it to the gitignored cache instead:

```bash
mkdir -p "$REPO_ROOT/.jackal/state"
grep -q '^\.jackal/state/' "$REPO_ROOT/.gitignore" || echo '.jackal/state/' >> "$REPO_ROOT/.gitignore"

cat > "$REPO_ROOT/.jackal/state/${ISSUE}.md" <<EOF
# Session state for #${ISSUE} (gitignored cache — git + GitHub Issues are authoritative)

- issue_doc: ${ISSUE_DOCS}/${ISSUE_ID}-*.md
- branch: ${BRANCH}
- path: ${WORKTREE_REL}
- status: Paused
- last_checkpoint: ${CHECKPOINT_STRING}
- blocked_by: [what you're waiting for, if Blocked; omit otherwise]
EOF
```

Use `Blocked` instead of `Paused` for `status:` when waiting on something external.

---

## Step 5: Update Backlog State

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

---

## Step 6: Persist the Checkpoint (nothing touches main)

The durable checkpoint is the GitHub issue comment + status label written in Step 5 — that is what
the supervisor reads back to give the resume command. The `.jackal/state/<issue#>.md` file from
Step 4 is a gitignored local cache for same-session reads, nothing more. A pause is backlog
bookkeeping, not feature history: it must leave **no tracked file modified and no commit** on
`main`. The old `chore: pause …` commit on the trunk is removed, and so is the tracked-issue-doc
edit that replaced it.

If a *versioned* status change to the issue doc is genuinely warranted, it belongs in a commit made
**inside the worktree**, on the feature branch, reaching `main` through the PR. An edit made in the
repo-root working tree cannot ride along on the feature branch — the worktree is a separate
checkout and never sees it.

If work-in-progress exists in the worktree, that is preserved separately — the implementor's
commit-early discipline keeps green checkpoints on the **feature branch** inside the worktree, and
`git stash`/an uncommitted working tree in the worktree survives untouched. Nothing about pausing
should write to `main`.

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
