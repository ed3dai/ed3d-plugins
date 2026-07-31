#!/usr/bin/env python3
"""
PreToolUse hook that blocks repo-mutating work on a protected branch.

Two responsibilities, dispatched on tool_name:

  Edit / Write / NotebookEdit — deny the write when the *target file's* git
  repository has HEAD on a protected branch (main / master).

  Bash — deny `git commit` / `git push` when the command's working directory
  has HEAD on a protected branch.

Fails open on anything ambiguous (not a git repo, detached HEAD, git missing,
gitignored scratch path, /tmp) and fails closed on a confirmed protected
branch. Override with JACKAL_ALLOW_MAIN_WRITES=1.
"""

import json
import os
import shlex
import subprocess
import sys

DEFAULT_PROTECTED_BRANCHES = ("main", "master")

OVERRIDE_ENV_VAR = "JACKAL_ALLOW_MAIN_WRITES"
PROTECTED_ENV_VAR = "JACKAL_PROTECTED_BRANCHES"
SCRATCH_ENV_VAR = "JACKAL_SCRATCH_PREFIXES"

TRUTHY = {"1", "true", "yes", "on"}

# Paths that are always scratch space, never a repo we care about protecting.
# Overridable via JACKAL_SCRATCH_PREFIXES (comma-separated; empty value disables).
DEFAULT_SCRATCH_PREFIXES = ("/tmp/", "/private/tmp/", "/var/tmp/", "/var/folders/")

WRITE_TOOLS = ("Edit", "Write", "NotebookEdit", "MultiEdit")

# git global flags that take a separate value argument.
GIT_GLOBAL_FLAGS_WITH_VALUE = ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path")

GUARDED_GIT_SUBCOMMANDS = ("commit", "push")

GIT_TIMEOUT_SECONDS = 5


def override_active() -> bool:
    return os.environ.get(OVERRIDE_ENV_VAR, "").strip().lower() in TRUTHY


def protected_branches() -> tuple[str, ...]:
    raw = os.environ.get(PROTECTED_ENV_VAR, "").strip()
    if not raw:
        return DEFAULT_PROTECTED_BRANCHES
    return tuple(b.strip() for b in raw.split(",") if b.strip())


def run_git(args: list[str], cwd: str) -> tuple[int, str]:
    """Run a git command, returning (returncode, stripped stdout)."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return 1, ""
    return result.returncode, result.stdout.strip()


def nearest_existing_dir(path: str) -> str | None:
    """Walk up from path until an existing directory is found."""
    if not path:
        return None
    candidate = path if os.path.isdir(path) else os.path.dirname(os.path.abspath(path))
    while candidate and candidate != os.path.dirname(candidate):
        if os.path.isdir(candidate):
            return candidate
        candidate = os.path.dirname(candidate)
    return candidate if candidate and os.path.isdir(candidate) else None


def current_branch(directory: str) -> str | None:
    """
    Return the branch HEAD points at for the repository containing `directory`.

    Uses symbolic-ref so an unborn HEAD (fresh `git init`) still resolves, and a
    detached HEAD resolves to None. In a linked worktree this reports the
    worktree's own branch, which is exactly what we want — a worktree on a
    feature branch is safe even when the main checkout sits on main.
    """
    code, _ = run_git(["rev-parse", "--is-inside-work-tree"], directory)
    if code != 0:
        return None
    code, branch = run_git(["symbolic-ref", "--quiet", "--short", "HEAD"], directory)
    if code != 0 or not branch:
        return None
    return branch


def is_gitignored(directory: str, path: str) -> bool:
    code, _ = run_git(["check-ignore", "-q", "--", path], directory)
    return code == 0


def scratch_prefixes() -> tuple[str, ...]:
    raw = os.environ.get(SCRATCH_ENV_VAR)
    if raw is None:
        return DEFAULT_SCRATCH_PREFIXES
    return tuple(p.strip() for p in raw.split(",") if p.strip())


def is_scratch_path(path: str) -> bool:
    resolved = os.path.abspath(path)
    prefixes = scratch_prefixes()
    if prefixes and resolved.startswith(prefixes):
        return True
    # Anything inside the git metadata directory is plumbing, not project work.
    return "/.git/" in resolved or resolved.endswith("/.git")


def write_block_reason(branch: str, path: str) -> str:
    filename = os.path.basename(path) or path
    return (
        f"BLOCKED: refusing to write {filename} while HEAD is on the protected "
        f"branch '{branch}'.\n\n"
        f"In this project the Pull Request is the only completion path — work that "
        f"lands directly on '{branch}' bypasses review entirely. Writing here now is "
        f"how that happens.\n\n"
        f"Do this instead:\n"
        f"  git switch -c <type>/<slug>     # e.g. git switch -c fix/branch-guard\n"
        f"then re-apply this edit and finish through a PR.\n\n"
        f"If you genuinely need to write on '{branch}' (release chore, hotfix you have "
        f"been told to land directly), set {OVERRIDE_ENV_VAR}=1 in the environment to "
        f"disable this guard for the session."
    )


def bash_block_reason(branch: str, subcommand: str) -> str:
    return (
        f"BLOCKED: refusing to run `git {subcommand}` while HEAD is on the protected "
        f"branch '{branch}'.\n\n"
        f"Committing or pushing on '{branch}' bypasses the Pull Request flow this "
        f"project requires.\n\n"
        f"Do this instead:\n"
        f"  git switch -c <type>/<slug>     # moves your staged work to a branch\n"
        f"  git commit && git push -u origin HEAD\n"
        f"then open a PR.\n\n"
        f"To override deliberately, set {OVERRIDE_ENV_VAR}=1 in the environment."
    )


def deny(reason: str) -> None:
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(output))
    sys.exit(0)


# ------------------------------------------------------------------
# Write-tool path
# ------------------------------------------------------------------


def target_path(tool_input: dict) -> str:
    for key in ("file_path", "notebook_path", "path"):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def check_write(tool_input: dict) -> None:
    path = target_path(tool_input)
    if not path:
        return
    if is_scratch_path(path):
        return

    directory = nearest_existing_dir(path)
    if not directory:
        return

    branch = current_branch(directory)
    if branch is None or branch not in protected_branches():
        return

    # Scratch files the repo has already declared uninteresting are fine.
    if is_gitignored(directory, os.path.abspath(path)):
        return

    deny(write_block_reason(branch, path))


# ------------------------------------------------------------------
# Bash path
# ------------------------------------------------------------------


def split_segments(command: str) -> list[list[str]]:
    """
    Split a shell command into segments at operator boundaries, tokenizing each.

    Quoted text survives as a single token, so `echo "git commit"` yields
    ['echo', 'git commit'] and never looks like a git invocation.
    """
    try:
        tokens = shlex.split(command, comments=True)
    except ValueError:
        # Malformed quoting — refuse to guess; treat as nothing to inspect.
        return []

    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in (";", "&&", "||", "|", "&"):
            if current:
                segments.append(current)
            current = []
        else:
            current.append(token)
    if current:
        segments.append(current)
    return segments


def git_invocation(segment: list[str]) -> tuple[str, str | None] | None:
    """
    If a segment invokes a guarded git subcommand, return (subcommand, -C dir).

    Returns None for non-git segments, unguarded subcommands, help lookups, and
    `git commit` appearing as a quoted argument to something else.
    """
    if not segment:
        return None

    index = 0
    # Tolerate a leading env assignment prefix: FOO=bar git commit
    while index < len(segment) and "=" in segment[index] and not segment[index].startswith("-"):
        index += 1
    if index >= len(segment):
        return None

    if os.path.basename(segment[index]) != "git":
        return None
    index += 1

    directory = None
    while index < len(segment):
        token = segment[index]
        if token in GIT_GLOBAL_FLAGS_WITH_VALUE:
            if token == "-C" and index + 1 < len(segment):
                directory = segment[index + 1]
            index += 2
            continue
        if token.startswith("--") and "=" in token:
            name, _, value = token.partition("=")
            if name == "--git-dir":
                directory = value
            index += 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        break

    if index >= len(segment):
        return None

    subcommand = segment[index]
    if subcommand == "help":
        return None
    if subcommand not in GUARDED_GIT_SUBCOMMANDS:
        return None
    # `git commit --help` / `-h` only prints documentation.
    if any(arg in ("--help", "-h") for arg in segment[index + 1 :]):
        return None
    # `git push --dry-run` mutates nothing.
    if subcommand == "push" and any(
        arg in ("--dry-run", "-n") for arg in segment[index + 1 :]
    ):
        return None

    return subcommand, directory


def resolve_cd(segments: list[list[str]], upto: int, base: str) -> str:
    """Apply any `cd` in earlier segments so `cd sub && git commit` resolves right."""
    directory = base
    for segment in segments[:upto]:
        if segment and os.path.basename(segment[0]) == "cd" and len(segment) > 1:
            target = segment[1]
            directory = target if os.path.isabs(target) else os.path.join(directory, target)
    return directory


def check_bash(tool_input: dict, cwd: str) -> None:
    command = tool_input.get("command")
    if not command or not isinstance(command, str):
        return

    segments = split_segments(command)
    for i, segment in enumerate(segments):
        invocation = git_invocation(segment)
        if invocation is None:
            continue
        subcommand, explicit_dir = invocation

        directory = explicit_dir or resolve_cd(segments, i, cwd)
        directory = nearest_existing_dir(directory) or cwd
        if not os.path.isdir(directory):
            continue

        branch = current_branch(directory)
        if branch is not None and branch in protected_branches():
            deny(bash_block_reason(branch, subcommand))


def main() -> None:
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        sys.exit(0)
    if not isinstance(input_data, dict):
        sys.exit(0)

    if override_active():
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    if not isinstance(tool_input, dict):
        sys.exit(0)

    cwd = input_data.get("cwd") or os.getcwd()
    if not isinstance(cwd, str) or not os.path.isdir(cwd):
        cwd = os.getcwd()

    try:
        if tool_name in WRITE_TOOLS:
            check_write(tool_input)
        elif tool_name == "Bash":
            check_bash(tool_input, cwd)
    except SystemExit:
        raise
    except Exception:
        # A guard that crashes the session is worse than a guard that misses one
        # edit. Stay silent and allow.
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
