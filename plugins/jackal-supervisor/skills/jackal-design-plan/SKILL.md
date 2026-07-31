---
name: jackal-design-plan
description: Start a design for a Complex issue. Runs conflict gate if not yet assigned, then invokes the design skill. Use for Complex issues that need architectural decisions.
user-invocable: true
argument-hint: "[issue-id-or-doc-path]"
---

# Jackal Design Plan

Wrapper that integrates the supervisor at entry/exit of the design phase. **This skill owns worktree creation** for the issue. Downstream skills (`jackal-impl-plan`, `jackal-pause-session`, `jackal-finish-branch`) resolve the worktree from **git itself**, falling back to the gitignored local state file described in Step 3.

---

## Step 0: Load Project Config

Read `## Jackal Config` from CLAUDE.md. Extract:
- `repo_root`, `issue_prefix`, `issue_docs`, `design_plans`, `modules`
- `gh_repo` — `owner/repo` (required)
- `label_style` — `slash` or `colon` (default: `slash`) — separator for status labels; examples
  below use `/`, substitute `:` if `colon`

## Step 1: Resolve Input

Accept issue ID or issue doc path. Read the issue doc.

- If Complexity is **Standard** → this issue doesn't need a design phase. Tell the user in
  one line ("Issue #N is Standard, not Complex — routing to jackal-impl-plan instead of
  design"), then invoke `Skill("jackal-supervisor:jackal-impl-plan")` with the same issue
  reference and stop processing this skill. Do not ask for confirmation first — this is a
  routing correction, not a judgment call the user needs to weigh in on.
- If Complexity is **Simple** → this issue doesn't need a design or implementation-plan
  phase at all. Tell the user in one line ("Issue #N is Simple — dispatching the implementor
  directly instead of design"), then dispatch the `jackal-plan-and-execute:implementor` agent
  directly with the issue doc as context (same routing the supervisor agent uses for Simple
  issues — see its Route to Execution table) and stop processing this skill.
- If git already has a worktree/branch for this issue (`git worktree list`), or a local state file
  `$REPO_ROOT/.jackal/state/<issue#>.md` exists → reuse it (skip step 2). This means design was
  started before and is being resumed.
- Otherwise → proceed to step 2

## Step 2: Conflict Gate + Create Worktree

Run conflict gate against active feature branches:

```bash
cd $REPO_ROOT
for branch in $(git branch --list 'feature/*' '*/[0-9]*-*' | tr -d ' '); do
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

## Step 3: Record the Worktree Assignment (gitignored local state)

**Never write worktree assignment or issue status into `docs/issue-docs/`.** Those files are
**tracked** in git, so editing one at the repo root dirties the tracked working tree on `main` —
which is the same problem as committing bookkeeping to the trunk, just deferred. Worktree assignment
and status are ephemeral session metadata; they do not belong in a tracked file.

**Two sources of truth, both outside the issue doc:**

1. **Git** is authoritative for what worktree/branch exists (`git worktree list`, `git branch`).
   `jackal-impl-plan` and `jackal-pause-session` query it directly.
2. **GitHub Issues** is the durable backlog record — the issue comment + status label written in
   Step 4.

Local state is a **cache only**, written to a gitignored path so it can never dirty the tree:

```bash
mkdir -p "$REPO_ROOT/.jackal/state"
grep -q '^\.jackal/state/' "$REPO_ROOT/.gitignore" || echo '.jackal/state/' >> "$REPO_ROOT/.gitignore"

cat > "$REPO_ROOT/.jackal/state/${ISSUE}.md" <<EOF
# Session state for #${ISSUE} (gitignored cache — git + GitHub Issues are authoritative)

- issue_doc: ${ISSUE_DOCS}/${ISSUE_ID}-${SLUG}.md
- branch: ${BRANCH}
- path: ${WORKTREE_PATH#$REPO_ROOT/}
- created: $(date +%F)
- status: In Progress
EOF
```

Use repo-root-relative paths in `path:` so it's portable; skills convert to absolute via
`$REPO_ROOT/<path>`.

**Do not edit the issue doc at all in this step** — not its `## Worktree` section, not its
`**Status:**` line. If a *durable, versioned* change to the issue doc is genuinely warranted, make
it **inside the worktree** (`cd "$WORKTREE_PATH"`, edit, commit) so it lands on the feature branch
and reaches `main` through the PR. An edit made in the repo-root working tree cannot ride along on
the feature branch — the worktree is a separate checkout and will never see it.

## Step 4: Update Backlog State (the durable record)

```bash
GH_ISSUE_NUM=$(echo "$ISSUE_ID" | grep -oE '[0-9]+$')

gh issue edit "$GH_ISSUE_NUM" --repo "$GH_REPO" \
  --add-label "status/in-progress" \
  --remove-label "status/ready" \
  --add-assignee "@me"

gh issue comment "$GH_ISSUE_NUM" --repo "$GH_REPO" --body "$(cat <<EOF
**Worktree assigned** — design phase starting

- Branch: \`${BRANCH}\`
- Worktree: \`${WORKTREE_PATH}\`
- Issue doc: \`${ISSUE_DOCS}/${ISSUE_ID}-${SLUG}.md\`
EOF
)"
```

If `gh issue edit` fails because a label doesn't exist, report the missing label to the user and continue (the comment is still useful).

## Step 5: Invoke Design Skill

Use `Skill("jackal-plan-and-execute:design")` with:
- `WORKTREE_PATH` — absolute path
- `BRANCH`
- `ISSUE_ID`, `SLUG`
- Issue doc content as pre-gathered context

The design skill runs from inside the worktree, so the design document commit lands on the feature branch.

## Step 6: Hand Off

After design commits, post the design doc link as an issue comment
(`gh issue comment "$GH_ISSUE_NUM" --body "**Design complete** — [design-plans/<filename>](<blob-url-or-path>)"`),
then hand off:

```
Design complete for #[issue].
Design plan: docs/design-plans/[filename]
Worktree: .worktrees/[issue#]-[slug]
Branch: [type]/[issue#]-[slug]

Next: /jackal-supervisor:jackal-impl-plan docs/design-plans/[filename]
```

Emit that `Next:` line **exactly as written with the real filename substituted** —
it is a literal command (defined in this plugin's `commands/`), not a
description. Do not invent command names.

No /clear needed. `jackal-impl-plan` finds the existing worktree by querying git, falling back to
`.jackal/state/<issue#>.md`.
