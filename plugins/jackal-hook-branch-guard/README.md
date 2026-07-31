# jackal-hook-branch-guard

Makes "the PR is the only completion path" fail closed instead of being prose nobody enforces.

## What it blocks

Two `PreToolUse` hooks, both served by `hooks/check-branch-guard.py`:

| Matcher | Blocked when |
|---|---|
| `Edit\|Write\|NotebookEdit` | The **target file's** git repository has `HEAD` on a protected branch |
| `Bash` | `git commit` / `git push` where the **command's** working directory has `HEAD` on a protected branch |

Protected branches default to `main` and `master`.

The branch is resolved per-target, not per-session, via `git symbolic-ref` run in the
file's own directory. A linked worktree reports its own branch, so a worktree checked
out to a feature branch is allowed even while the primary checkout sits on `main`.

## What it deliberately allows

- Writes on any non-protected branch
- Writes anywhere inside a worktree on a feature branch
- Gitignored and scratch paths (`git check-ignore`), `/tmp`, `/var/folders`, `.git/`
- Writes outside any git repository
- Detached `HEAD` (cannot tell intent — fails open)
- Read-only git: `log`, `status`, `diff`, `show`, `fetch`, `branch`, `rev-parse`
- `git commit --help`, `git help commit`, `git push --dry-run`
- `git commit` appearing inside a quoted string, heredoc, or grep pattern

## Escape hatch

```bash
export JACKAL_ALLOW_MAIN_WRITES=1
```

Disables the guard entirely for the session. The block message names this variable so
it is discoverable at the moment it is needed.

## Other configuration

| Variable | Default | Effect |
|---|---|---|
| `JACKAL_ALLOW_MAIN_WRITES` | unset | `1`/`true`/`yes`/`on` disables the guard |
| `JACKAL_PROTECTED_BRANCHES` | `main,master` | Comma-separated branch names to protect |
| `JACKAL_SCRATCH_PREFIXES` | `/tmp/,/private/tmp/,/var/tmp/,/var/folders/` | Always-allowed path prefixes; set empty to disable |

## Failure posture

Fails **closed** only on a confirmed protected branch. Everything ambiguous — git
missing, git erroring, unparseable command, unexpected exception — exits 0 and allows.
A guard that breaks the session is worse than a guard that misses one edit; the
`Bash` half of the guard catches on the way out what the write half lets through.

## Tests

```bash
cd plugins/jackal-hook-branch-guard/hooks
python3 test-check-branch-guard.py
```

No pytest dependency. Creates real temporary git repositories (including real linked
worktrees) rather than mocking git, since reading true git state is the whole point.
