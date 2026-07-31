---
name: jackal-sweep
description: Reclaim worktrees and local branches whose PRs have merged, flag PRs that need a rebase, surface orphaned stashes, and fast-forward main. Run after PRs merge, before starting new work, or whenever `git worktree list` looks crowded.
user-invocable: true
---

# Jackal Sweep

Branch and worktree hygiene in one pass. This is the harness-native version of
"pull main, prune what's gone" — but it removes worktrees **before** pruning
branches, which is exactly the step ad-hoc sync scripts miss (a branch checked
out in a worktree can't be deleted, and a worktree with stray files blocks
`git worktree remove`).

**Announce at start:** "Sweeping worktrees, branches, and PR state."

> **How to run the sweep (flat).** Steps 0-6 are branch/worktree/git hygiene —
> run them as **direct director work**, not delegated to a nested tier. If a
> step needs investigation beyond git plumbing (e.g. confirming a
> delivered-but-open issue was truly closed by a merged PR), fan out **at most
> a single Sonnet research dispatch** (the research tier in the Model Tier
> Table); do not chain multiple dispatches for it. Never run the sweep under a **nested
> Opus supervisor** — that is the direct lesson of the audited sweep session
> (nested Opus supervisor → wrong first deliverable → the "lost agent" stall).
> A middle tier for a sweep is only the justification-gated exception in the
> `execute` skill's **`## Orchestration Topology`** section: the one-sentence
> written justification plus the stricter R2 liveness `EXPECT` window both
> apply — see that section, not restated here.

---

## Step 0: Fetch and Inventory

```bash
cd "$(git rev-parse --show-toplevel)"
git fetch --all --prune

git worktree list --porcelain
git branch -vv                       # [gone] marks branches whose upstream vanished
gh pr list --state all --limit 50 \
  --json number,state,headRefName,mergeStateStatus,url
```

Build one table keyed by branch: worktree path (if any), PR number/state,
`mergeStateStatus`, and whether the upstream is `[gone]`.

## Step 1: Classify Each Branch/Worktree

| State | Action |
|---|---|
| PR **merged** or **closed** | Reclaim: remove worktree, delete local branch |
| Upstream `[gone]`, no open PR | Reclaim (squash-merged and remote branch deleted) |
| PR **open**, `mergeStateStatus: BEHIND` | Keep; flag **needs rebase** |
| PR **open**, `mergeStateStatus: DIRTY` | Keep; flag **has conflicts — rebase + resolve** |
| PR **open**, clean | Keep; no action |
| No PR, has commits ahead of main | Keep; flag **unfinished work** (offer `/jackal-supervisor:jackal-finish-branch`) |
| No PR, no commits ahead | Flag **abandoned?** — ask before reclaiming |

## Step 2: Reclaim (merged/closed/gone only)

For each reclaimable branch:

```bash
# Worktree first — a checked-out branch cannot be deleted.
git worktree remove "$WORKTREE_PATH" 2>/dev/null || {
  # Leftover untracked files (caches, .env, node_modules) block removal.
  # Show what's in the way before forcing:
  git -C "$WORKTREE_PATH" status --porcelain
  # Only build artifacts / caches / untracked cruft → force. Real uncommitted
  # edits → STOP and ask.
  git worktree remove --force "$WORKTREE_PATH"
}
git branch -D "$BRANCH"
```

**The only judgment call:** uncommitted *tracked* changes in a merged branch's
worktree. Never force-remove those without asking — show the diff stat and let
the human decide.

## Step 3: Fast-Forward Main

```bash
git checkout main 2>/dev/null || true    # skip if a worktree holds main
git pull --ff-only "$GIT_REMOTE" main
git worktree prune
git remote prune origin
```

If `--ff-only` fails, local main has diverged from origin — report the
divergence (`git log --oneline origin/main..main`); never force-reset without
confirmation.

## Step 4: Rebase Flags

For every open PR flagged BEHIND or DIRTY, print the ready-to-run fix:

```
#NN feat/24-foo — BEHIND origin/main by [k] commits
  → cd .worktrees/24-foo && git fetch origin && git rebase origin/main && $TEST_CMD && git push --force-with-lease
```

Offer to run these now (one at a time, tests between rebase and push). DIRTY
PRs get the same command plus a warning that conflicts will need resolution —
apply the finish skill's rule: mechanical conflicts fine, semantic conflicts
stop and report.

## Step 5: Reconcile Stashes

Stashes are invisible to every other step here — they belong to no branch and no worktree, so
parked work can sit orphaned for weeks without anything surfacing it. Surface them every sweep:

```bash
git stash list --date=short \
  --format='%gd|%cd|%gs|%H'          # ref | date | message | sha
```

For each entry, get enough detail for the human to recognize it:

```bash
git stash show --stat "$STASH_REF"                    # what's in it
git log -1 --format='%H %s' "$STASH_REF^1"            # the commit it was taken from
git branch --contains "$(git rev-parse "$STASH_REF^1")" -a 2>/dev/null | head -5
```

Classify, but **take no action**:

| Signal | Note in the report |
|---|---|
| `WIP on main` / `WIP on <default-branch>` | **Likely orphaned** — work parked on the trunk with no branch to carry it |
| Base commit reachable from a **merged** PR branch | **Probably superseded** — verify before dropping |
| Base commit only on a live branch | **Belongs to** that branch — reapply there, not here |
| Older than ~30 days | **Stale** — flag the age explicitly |

**Never `git stash drop`, `git stash pop`, or `git stash apply` during a sweep.** A stash is the one
artifact here with no other copy anywhere — dropping the wrong one destroys work permanently, and
applying one silently mutates a working tree the user didn't ask you to touch. Report the entries
with the commands the user could run, and let them decide:

```
Stashes (no action taken — your call):
  stash@{0}  2026-06-12  WIP on main: 65b1f1e Merge pull request #37
             3 files changed, 47 insertions(+)  — likely orphaned, 48 days old
             inspect: git stash show -p 'stash@{0}'
             recover: git switch -c recover/stash-0 65b1f1e && git stash apply 'stash@{0}'
             discard: git stash drop 'stash@{0}'      # only if you're sure
```

If `git stash list` is empty, say so in one line — a clean result is worth confirming.

## Step 6: Report

```
Swept: [n] worktrees removed, [n] branches deleted, main fast-forwarded to [sha]
Needs rebase: #NN (BEHIND), #MM (DIRTY — conflicts)
Unfinished:  feat/31-bar (12 commits, no PR)
Stashes: [n] found ([n] likely orphaned) — see above / none
Kept (open PRs): #22, #27
Stale-open (delivered by a merged PR, still OPEN — close, don't rank): #NN (PR #MM)
```

> **Stale-open issues.** This sweep reclaims *worktrees/branches*. Ranking a
> candidate OPEN issue that a merged PR already delivered is prevented by the
> **Merged-PR gate** in the jackal-supervisor agent ("Reading the backlog") and
> the `execute` skill (Step 4). If you spot a delivered-but-open issue here,
> list it under Stale-open and close it with `gh issue close <#> --reason completed`.
