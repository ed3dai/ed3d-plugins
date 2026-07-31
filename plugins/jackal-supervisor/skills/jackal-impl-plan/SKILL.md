---
name: jackal-impl-plan
description: Create an implementation plan for a Standard or Complex issue. Reuses the worktree assigned by /jackal-supervisor:jackal-design-plan (Complex) or creates one (Standard). Second step in the Jackal dev cycle.
user-invocable: true
argument-hint: "[design-plan-or-issue-doc-path]"
---

# Jackal Implementation Plan

Wrapper that adds supervisor integration around the `plan` skill.

**Worktree ownership:** This skill **does not own** worktree creation for Complex issues — `jackal-design-plan` does. This skill resolves the existing worktree from git (falling back to the gitignored `.jackal/state/<issue#>.md` cache) and reuses it. For Standard issues that skip design, this skill creates the worktree itself (single owner per code path).

---

## Step 0: Load Project Config

Read `## Jackal Config` from CLAUDE.md. Extract:
- `repo_root`, `issue_prefix`, `issue_docs`, `design_plans`, `impl_plans`, `modules`, `test_cmd`
- `gh_repo` — `owner/repo` (required)
- `label_style` — `slash` or `colon` (default: `slash`) — separator for status labels; examples
  below use `/`, substitute `:` if `colon`

## Step 1: Resolve Input

Accept: design plan path, issue doc path, or issue ID.

- Design plan provided → resolve associated issue doc from filename or design plan front-matter
- Issue doc for Standard issue → planner will auto-generate mini design
- Issue doc for Complex issue with no design plan → STOP, redirect to `/jackal-supervisor:jackal-design-plan`
- Simple issue → this issue doesn't need an implementation plan. Tell the user in one line
  ("Issue #N is Simple — dispatching the implementor directly instead of planning"), then
  dispatch the `jackal-plan-and-execute:implementor` agent directly with the issue doc as
  context (same routing the supervisor agent uses for Simple issues — see its Route to
  Execution table) and stop processing this skill. Do not ask for confirmation first.

## Step 2: Resolve Worktree

**Git is the authoritative source for what worktree/branch exists** — not a doc block, tracked or
otherwise. Resolve by asking git directly for a worktree whose branch matches this issue number:

```bash
ISSUE="24"   # GitHub issue number for this work unit
# Find an existing worktree whose branch is <type>/<issue#>-slug (bare-integer scheme).
WORKTREE_PATH=$(git -C "$REPO_ROOT" worktree list --porcelain \
  | awk -v n="$ISSUE" '
      /^worktree /{p=$2}
      /^branch /{ b=$2; if (b ~ ("/" n "-") || b ~ ("/" n "$")) print p }' \
  | head -1)
[ -n "$WORKTREE_PATH" ] && BRANCH=$(git -C "$WORKTREE_PATH" branch --show-current)
```

If that finds nothing, fall back to the gitignored local state cache written by
`jackal-design-plan` (it may be absent — it is a cache, not a record):

```bash
STATE="$REPO_ROOT/.jackal/state/${ISSUE}.md"
[ -z "$WORKTREE_PATH" ] && [ -f "$STATE" ] && WORKTREE_REL=$(awk '/^- path:/{print $3}' "$STATE")
[ -z "$BRANCH" ] && [ -f "$STATE" ] && BRANCH=$(awk '/^- branch:/{print $3}' "$STATE")
```

**Three cases:**

1. **Worktree resolved (via git, or via the state cache and `$REPO_ROOT/$WORKTREE_REL` exists)** →
   reuse it.
   ```bash
   # If git already set an absolute WORKTREE_PATH, keep it; otherwise build from the state cache.
   [ -z "$WORKTREE_PATH" ] && WORKTREE_PATH="$REPO_ROOT/$WORKTREE_REL"
   cd "$WORKTREE_PATH" && git branch --show-current   # verify expected branch; warn on mismatch
   ```

2. **The state cache names a path that no longer exists** (worktree was removed, git found nothing)
   → recreate at the same path/branch:
   ```bash
   cd "$REPO_ROOT"
   git worktree add "$REPO_ROOT/$WORKTREE_REL" "$BRANCH" || \
     git worktree add "$REPO_ROOT/$WORKTREE_REL" -b "$BRANCH" main
   ```

3. **Nothing resolved** (Standard issue that skipped /jackal-design-plan) → run conflict gate,
   create worktree, and record the assignment:

   ```bash
   cd "$REPO_ROOT"
   for branch in $(git branch --list 'feature/*' '*/[0-9]*-*' | tr -d ' '); do
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

   Record the assignment in the **gitignored local state cache** — never in the tracked issue doc
   (`docs/issue-docs/` is tracked; editing it at the repo root dirties the working tree on `main`):

   ```bash
   mkdir -p "$REPO_ROOT/.jackal/state"
   grep -q '^\.jackal/state/' "$REPO_ROOT/.gitignore" || echo '.jackal/state/' >> "$REPO_ROOT/.gitignore"

   cat > "$REPO_ROOT/.jackal/state/${ISSUE}.md" <<EOF
   # Session state for #${ISSUE} (gitignored cache — git + GitHub Issues are authoritative)

   - issue_doc: ${ISSUE_DOCS}/${ISSUE_ID}-${SLUG}.md
   - branch: ${BRANCH}
   - path: ${WORKTREE_REL}
   - created: $(date +%F)
   - status: In Progress
   EOF
   ```

   The durable assignment record is the GitHub issue comment + label in Step 3, and git itself is
   the authority for what worktree exists. The old `chore: assign worktree for #N` commit on the
   trunk is removed. If a *versioned* issue-doc change is genuinely needed, make it **inside the
   worktree** so it lands on the feature branch and reaches `main` via the PR — an edit in the
   repo-root working tree is invisible to the worktree's separate checkout.

**Critical:** never silently bail. If the worktree resolution fails for any reason, report exactly what was tried and what failed — the user shouldn't see "could not find worktree" with no detail.

## Step 3: Update Backlog State

Skip if the GitHub issue already carries `status/in-progress` (Complex issues had this set during
/jackal-design-plan). Check the **label**, not the issue doc's `**Status:**` line — that tracked file
is no longer updated by assignment. Otherwise, for Standard issues that skipped design:

```bash
GH_ISSUE_NUM=$(echo "$ISSUE_ID" | grep -oE '[0-9]+$')

gh issue edit "$GH_ISSUE_NUM" --repo "$GH_REPO" \
  --add-label "status/in-progress" \
  --remove-label "status/ready" \
  --add-assignee "@me"

gh issue comment "$GH_ISSUE_NUM" --repo "$GH_REPO" --body "$(cat <<EOF
**Worktree assigned** — implementation planning starting

- Branch: \`${BRANCH}\`
- Worktree: \`${WORKTREE_PATH}\`
EOF
)"
```

## Step 4: Invoke Plan Skill

Use `Skill("jackal-plan-and-execute:plan")` with:
- `WORKTREE_PATH` — absolute path (already resolved/created)
- `BRANCH`
- `DESIGN_PATH` — design plan or issue doc path
- `TEST_CMD`
- `IMPL_PLANS` — relative path from repo root

The `plan` skill skips its own worktree creation when `WORKTREE_PATH` is provided, dispatches the planner agent, writes phase files, and starts execution.

## Step 5: Execution Starts Automatically

The plan skill flows directly into the execute skill — **invoke it via
`Skill("jackal-plan-and-execute:execute")`, never by inventing or un-namespacing
a slash command.** If you ever need to hand the user a resumable command
instead, it is exactly:

```
/jackal-plan-and-execute:execute <absolute-plan-dir> <absolute-worktree-path>
```

(`jackal-plan-and-execute:execute` is the only execution command; there is no
`/execute-plan` or `/execute-implementation-plan`. Marketplace-installed commands
are always namespaced `plugin:command` — a bare `/execute` will not resolve.)

If running in autonomous mode (backlog execution), everything from this point is automatic until the issue is done or the orchestrator gets stuck.
