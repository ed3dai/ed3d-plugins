#!/usr/bin/env python3
"""
Tests for check-branch-guard.py PreToolUse hook.
Run: python3 test-check-branch-guard.py

Uses real temporary git repositories rather than mocks — the whole point of the
guard is that it reads actual git state, so faking that would test nothing.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "check-branch-guard.py")

passed = 0
failed = 0
errors: list[str] = []

# The hook treats /tmp as scratch, and tempfile lives there. Point the scratch
# prefixes somewhere harmless so temp repos are guarded like real ones.
BASE_ENV = {**os.environ, "JACKAL_SCRATCH_PREFIXES": "/nonexistent-scratch/"}
BASE_ENV.pop("JACKAL_ALLOW_MAIN_WRITES", None)


def git(cwd: str, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def make_repo(root: str, branch: str) -> str:
    """Create a git repo with one commit, checked out on `branch`."""
    repo = os.path.join(root, "repo")
    os.makedirs(repo, exist_ok=True)
    git(repo, "init", "-q", "-b", branch)
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "commit.gpgsign", "false")
    with open(os.path.join(repo, "README.md"), "w") as fh:
        fh.write("seed\n")
    git(repo, "add", "README.md")
    git(repo, "commit", "-q", "-m", "seed")
    return repo


def run_hook(payload: dict, env_extra: dict | None = None) -> dict | None:
    env = {**BASE_ENV, **(env_extra or {})}
    result = subprocess.run(
        [sys.executable, SCRIPT],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, f"Hook exited {result.returncode}: {result.stderr}"
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)


def decision(output: dict | None) -> str | None:
    if output is None:
        return None
    return output["hookSpecificOutput"]["permissionDecision"]


def reason(output: dict | None) -> str:
    assert output is not None
    return output["hookSpecificOutput"]["permissionDecisionReason"]


def check(name: str, actual, expected) -> None:
    global passed, failed
    if actual == expected:
        passed += 1
    else:
        errors.append(f"FAIL [{name}]: expected {expected!r}, got {actual!r}")
        failed += 1


def case(name: str, fn) -> None:
    """Run fn(tmpdir); fn reports its own checks."""
    global failed
    tmp = tempfile.mkdtemp(prefix="branch-guard-test-")
    try:
        fn(tmp)
    except Exception as exc:  # noqa: BLE001 — a broken case is a failed case
        errors.append(f"ERROR [{name}]: {type(exc).__name__}: {exc}")
        failed += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def write_payload(path: str, tool: str = "Edit") -> dict:
    key = "notebook_path" if tool == "NotebookEdit" else "file_path"
    return {"tool_name": tool, "tool_input": {key: path, "new_string": "x"}}


def bash_payload(command: str, cwd: str) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": cwd}


# ============================================================
# Section 1: writes on a protected branch — DENY
# ============================================================


def t_write_on_main(tmp):
    repo = make_repo(tmp, "main")
    out = run_hook(write_payload(os.path.join(repo, "src.py")))
    check("write on main blocked", decision(out), "deny")
    check("message names branch", "'main'" in reason(out), True)
    check("message suggests git switch -c", "git switch -c" in reason(out), True)
    check("message mentions override", "JACKAL_ALLOW_MAIN_WRITES" in reason(out), True)


def t_write_on_master(tmp):
    repo = make_repo(tmp, "master")
    out = run_hook(write_payload(os.path.join(repo, "src.py")))
    check("write on master blocked", decision(out), "deny")


def t_write_nested_path_on_main(tmp):
    repo = make_repo(tmp, "main")
    os.makedirs(os.path.join(repo, "a", "b"))
    out = run_hook(write_payload(os.path.join(repo, "a", "b", "deep.py")))
    check("nested write on main blocked", decision(out), "deny")


def t_write_new_dir_on_main(tmp):
    """Target dir doesn't exist yet — must still resolve the repo by walking up."""
    repo = make_repo(tmp, "main")
    out = run_hook(write_payload(os.path.join(repo, "brand/new/dir/file.py")))
    check("write to not-yet-existing dir on main blocked", decision(out), "deny")


def t_all_write_tools_on_main(tmp):
    repo = make_repo(tmp, "main")
    for tool in ("Edit", "Write", "NotebookEdit"):
        out = run_hook(write_payload(os.path.join(repo, "src.py"), tool=tool))
        check(f"{tool} on main blocked", decision(out), "deny")


case("write on main", t_write_on_main)
case("write on master", t_write_on_master)
case("nested write on main", t_write_nested_path_on_main)
case("write to new dir on main", t_write_new_dir_on_main)
case("all write tools on main", t_all_write_tools_on_main)


# ============================================================
# Section 2: writes that must be ALLOWED
# ============================================================


def t_write_on_feature_branch(tmp):
    repo = make_repo(tmp, "main")
    git(repo, "switch", "-q", "-c", "feat/thing")
    out = run_hook(write_payload(os.path.join(repo, "src.py")))
    check("write on feature branch allowed", decision(out), None)


def t_write_in_worktree_on_feature(tmp):
    """A worktree on a feature branch is fine even though the main checkout is on main."""
    repo = make_repo(tmp, "main")
    worktree = os.path.join(tmp, "wt")
    git(repo, "worktree", "add", "-q", "-b", "feat/wt", worktree)
    out = run_hook(write_payload(os.path.join(worktree, "src.py")))
    check("write in worktree on feature branch allowed", decision(out), None)
    # And the primary checkout is still guarded.
    out = run_hook(write_payload(os.path.join(repo, "src.py")))
    check("primary checkout still blocked", decision(out), "deny")


def t_write_in_worktree_on_main(tmp):
    """Inverse: worktree on main, primary on a feature branch."""
    repo = make_repo(tmp, "main")
    git(repo, "switch", "-q", "-c", "feat/primary")
    worktree = os.path.join(tmp, "wt-main")
    git(repo, "worktree", "add", "-q", worktree, "main")
    out = run_hook(write_payload(os.path.join(worktree, "src.py")))
    check("write in worktree on main blocked", decision(out), "deny")
    out = run_hook(write_payload(os.path.join(repo, "src.py")))
    check("primary on feature branch allowed", decision(out), None)


def t_write_gitignored_on_main(tmp):
    repo = make_repo(tmp, "main")
    with open(os.path.join(repo, ".gitignore"), "w") as fh:
        fh.write("scratch/\n*.log\n")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-q", "-m", "ignore")
    os.makedirs(os.path.join(repo, "scratch"))
    out = run_hook(write_payload(os.path.join(repo, "scratch", "notes.md")))
    check("gitignored dir on main allowed", decision(out), None)
    out = run_hook(write_payload(os.path.join(repo, "debug.log")))
    check("gitignored glob on main allowed", decision(out), None)
    out = run_hook(write_payload(os.path.join(repo, "tracked.md")))
    check("non-ignored sibling still blocked", decision(out), "deny")


def t_write_outside_repo(tmp):
    plain = os.path.join(tmp, "plain")
    os.makedirs(plain)
    out = run_hook(write_payload(os.path.join(plain, "file.py")))
    check("write outside any repo allowed", decision(out), None)


def t_write_tmp_path(tmp):
    """With default scratch prefixes, /tmp paths are allowed even inside a main repo."""
    repo = make_repo(tmp, "main")
    env = {k: v for k, v in BASE_ENV.items() if k != "JACKAL_SCRATCH_PREFIXES"}
    result = subprocess.run(
        [sys.executable, SCRIPT],
        input=json.dumps(write_payload(os.path.join(repo, "src.py"))),
        capture_output=True,
        text=True,
        env=env,
    )
    # tempfile.mkdtemp lands under /tmp (or /var/folders on macOS), both scratch.
    check("tmp path allowed under default scratch prefixes", result.stdout.strip(), "")


def t_write_detached_head(tmp):
    repo = make_repo(tmp, "main")
    code = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True
    ).stdout.strip()
    git(repo, "checkout", "-q", code)
    out = run_hook(write_payload(os.path.join(repo, "src.py")))
    check("detached HEAD allowed (fails open)", decision(out), None)


def t_write_dot_git_path(tmp):
    repo = make_repo(tmp, "main")
    out = run_hook(write_payload(os.path.join(repo, ".git", "hooks", "pre-commit")))
    check("path inside .git allowed", decision(out), None)


case("write on feature branch", t_write_on_feature_branch)
case("worktree on feature branch", t_write_in_worktree_on_feature)
case("worktree on main", t_write_in_worktree_on_main)
case("gitignored path on main", t_write_gitignored_on_main)
case("write outside repo", t_write_outside_repo)
case("tmp path", t_write_tmp_path)
case("detached HEAD", t_write_detached_head)
case("path inside .git", t_write_dot_git_path)


# ============================================================
# Section 3: Bash — git commit / push on a protected branch DENIED
# ============================================================


def t_bash_blocked_on_main(tmp):
    repo = make_repo(tmp, "main")
    blocked = [
        "git commit -m 'wip'",
        'git commit -am "feat: thing"',
        "git push",
        "git push origin main",
        "git push -u origin HEAD",
        "git -c user.name=x commit -m y",
        "git add -A && git commit -m 'x'",
        "git status && git push origin main",
        "GIT_EDITOR=true git commit --amend",
        "/usr/bin/git commit -m x",
    ]
    for command in blocked:
        out = run_hook(bash_payload(command, repo))
        check(f"bash blocked: {command}", decision(out), "deny")
    check("bash message suggests switch", "git switch -c" in reason(run_hook(
        bash_payload("git commit -m x", repo))), True)


def t_bash_dash_c_targets_other_repo(tmp):
    """git -C <main repo> commit, run from a safe cwd, must still be blocked."""
    repo = make_repo(tmp, "main")
    safe = os.path.join(tmp, "safe")
    os.makedirs(safe)
    out = run_hook(bash_payload(f"git -C {repo} commit -m x", safe))
    check("git -C into main repo blocked", decision(out), "deny")


def t_bash_cd_then_commit(tmp):
    repo = make_repo(tmp, "main")
    parent = os.path.dirname(repo)
    out = run_hook(bash_payload("cd repo && git commit -m x", parent))
    check("cd into main repo then commit blocked", decision(out), "deny")


case("bash commit/push on main", t_bash_blocked_on_main)
case("git -C other repo", t_bash_dash_c_targets_other_repo)
case("cd then commit", t_bash_cd_then_commit)


# ============================================================
# Section 4: Bash — commands that must be ALLOWED
# ============================================================


def t_bash_readonly_allowed(tmp):
    repo = make_repo(tmp, "main")
    allowed = [
        "git log --oneline -5",
        "git status",
        "git diff HEAD",
        "git show HEAD",
        "git branch --show-current",
        "git rev-parse HEAD",
        "git fetch origin",
        "git commit --help",
        "git help commit",
        "git push --dry-run",
        "git push -n origin main",
        "git switch -c feat/thing",
        "ls -la",
        "python3 -m pytest",
    ]
    for command in allowed:
        out = run_hook(bash_payload(command, repo))
        check(f"bash allowed: {command}", decision(out), None)


def t_bash_no_false_positive_on_quoted_text(tmp):
    repo = make_repo(tmp, "main")
    allowed = [
        "echo 'git commit -m x'",
        'echo "run git push when ready"',
        "grep -r 'git commit' docs/",
        "printf 'do not git push\\n'",
        "cat > note.md <<'EOF'\ngit commit\nEOF",
    ]
    for command in allowed:
        out = run_hook(bash_payload(command, repo))
        check(f"no false positive: {command}", decision(out), None)


def t_bash_commit_on_feature_allowed(tmp):
    repo = make_repo(tmp, "main")
    git(repo, "switch", "-q", "-c", "feat/thing")
    out = run_hook(bash_payload("git commit -m 'feat: thing'", repo))
    check("commit on feature branch allowed", decision(out), None)
    out = run_hook(bash_payload("git push -u origin HEAD", repo))
    check("push on feature branch allowed", decision(out), None)


def t_bash_commit_in_worktree_allowed(tmp):
    repo = make_repo(tmp, "main")
    worktree = os.path.join(tmp, "wt")
    git(repo, "worktree", "add", "-q", "-b", "feat/wt", worktree)
    out = run_hook(bash_payload("git commit -m x", worktree))
    check("commit in feature worktree allowed", decision(out), None)


def t_bash_outside_repo_allowed(tmp):
    plain = os.path.join(tmp, "plain")
    os.makedirs(plain)
    out = run_hook(bash_payload("git commit -m x", plain))
    check("commit outside any repo allowed", decision(out), None)


case("read-only git allowed", t_bash_readonly_allowed)
case("quoted text no false positive", t_bash_no_false_positive_on_quoted_text)
case("commit on feature branch", t_bash_commit_on_feature_allowed)
case("commit in worktree", t_bash_commit_in_worktree_allowed)
case("commit outside repo", t_bash_outside_repo_allowed)


# ============================================================
# Section 5: escape hatch and configuration
# ============================================================


def t_override_env_var(tmp):
    repo = make_repo(tmp, "main")
    for value in ("1", "true", "YES", "on"):
        out = run_hook(
            write_payload(os.path.join(repo, "src.py")),
            {"JACKAL_ALLOW_MAIN_WRITES": value},
        )
        check(f"override={value} allows write", decision(out), None)
        out = run_hook(
            bash_payload("git commit -m x", repo), {"JACKAL_ALLOW_MAIN_WRITES": value}
        )
        check(f"override={value} allows commit", decision(out), None)
    # A falsy value must NOT disable the guard.
    out = run_hook(write_payload(os.path.join(repo, "src.py")), {"JACKAL_ALLOW_MAIN_WRITES": "0"})
    check("override=0 still blocks", decision(out), "deny")


def t_custom_protected_branches(tmp):
    repo = make_repo(tmp, "main")
    git(repo, "switch", "-q", "-c", "release")
    out = run_hook(write_payload(os.path.join(repo, "src.py")))
    check("release not protected by default", decision(out), None)
    out = run_hook(
        write_payload(os.path.join(repo, "src.py")),
        {"JACKAL_PROTECTED_BRANCHES": "main,release"},
    )
    check("release protected when configured", decision(out), "deny")


case("override env var", t_override_env_var)
case("custom protected branches", t_custom_protected_branches)


# ============================================================
# Section 6: malformed input must never crash
# ============================================================

for label, bad_input in [
    ("empty stdin", ""),
    ("not json", "not json at all"),
    ("json array", "[]"),
    ("json string", '"hello"'),
    ("no tool_name", json.dumps({"tool_input": {}})),
    ("unknown tool", json.dumps({"tool_name": "WebFetch", "tool_input": {"url": "x"}})),
    ("tool_input not dict", json.dumps({"tool_name": "Edit", "tool_input": "nope"})),
    ("missing file_path", json.dumps({"tool_name": "Edit", "tool_input": {}})),
    ("null file_path", json.dumps({"tool_name": "Edit", "tool_input": {"file_path": None}})),
    ("null command", json.dumps({"tool_name": "Bash", "tool_input": {"command": None}})),
    ("numeric command", json.dumps({"tool_name": "Bash", "tool_input": {"command": 42}})),
    ("unbalanced quotes", json.dumps({"tool_name": "Bash", "tool_input": {"command": "git commit -m 'x"}})),
    ("bogus cwd", json.dumps({"tool_name": "Bash", "tool_input": {"command": "git commit"}, "cwd": "/no/such/dir"})),
]:
    result = subprocess.run(
        [sys.executable, SCRIPT],
        input=bad_input,
        capture_output=True,
        text=True,
        env=BASE_ENV,
    )
    if result.returncode == 0:
        passed += 1
    else:
        errors.append(f"FAIL [{label}]: exited {result.returncode}: {result.stderr}")
        failed += 1


# ============================================================
# Results
# ============================================================
print()
if errors:
    for e in errors:
        print(e)
    print()

total = passed + failed
print(f"{passed}/{total} tests passed, {failed} failed")
sys.exit(1 if failed > 0 else 0)
