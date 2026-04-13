# jackal-linear Implementation Plan — Phase 3

**Goal:** Automatically prompt Linear status updates after PR creation and merge events.

**Architecture:** A PostToolUse hook on Bash intercepts `gh pr create` and `git merge` / `gh pr merge` commands. When `.linear-issue` exists at the project root, the hook injects an `additionalContext` reminder into Claude's context. The hook is a no-op when `.linear-issue` is absent (non-Linear sessions) or when the command does not match the target patterns. Follows the exact pattern from `ed3d-hook-claudemd-reminder`.

**Tech Stack:** Python 3, JSON stdin/stdout hook protocol, Claude Code PostToolUse hook system

**Scope:** Phase 3 of 5

**Codebase verified:** 2026-03-08

---

## Acceptance Criteria Coverage

This phase implements and tests:

### jackal-linear.AC3: PostToolUse hook prompts status updates on PR and merge events
- **jackal-linear.AC3.1 Success:** After `gh pr create`, hook injects Linear reminder into Claude's context when `.linear-issue` is present
- **jackal-linear.AC3.2 Success:** After `git merge` or `gh pr merge`, hook injects Linear reminder when `.linear-issue` is present
- **jackal-linear.AC3.3 Success:** Hook injects nothing when `.linear-issue` is absent (non-Linear session)
- **jackal-linear.AC3.4 Success:** Unrelated Bash commands (e.g., `ls`, `npm test`) do not trigger the hook
- **jackal-linear.AC3.5 Failure:** Hook script exit code does not block or fail the Bash command that triggered it

---

<!-- START_SUBCOMPONENT_A (tasks 1-3) -->
<!-- START_TASK_1 -->
### Task 1: Create hooks.json

**Files:**
- Create: `plugins/jackal-linear/hooks/hooks.json`

**Step 1: Create the hooks directory**

```bash
mkdir -p plugins/jackal-linear/hooks
```

**Step 2: Create hooks.json**

Create `plugins/jackal-linear/hooks/hooks.json` with the following content:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/linear-status-hook.py\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

**Step 3: Verify JSON is valid**

Run: `cat plugins/jackal-linear/hooks/hooks.json | python3 -m json.tool > /dev/null && echo "Valid JSON"`
Expected: `Valid JSON`
<!-- END_TASK_1 -->

<!-- START_TASK_2 -->
### Task 2: Create the linear-status-hook.py script

**Verifies:** jackal-linear.AC3.1, jackal-linear.AC3.2, jackal-linear.AC3.3, jackal-linear.AC3.4, jackal-linear.AC3.5

**Files:**
- Create: `plugins/jackal-linear/hooks/linear-status-hook.py`

**Implementation:**

The script must:
1. Read JSON from stdin (the hook payload)
2. Exit 0 silently if input is invalid JSON
3. Exit 0 silently if `tool_name` is not `"Bash"` (defensive guard, though the matcher already filters this)
4. Extract `tool_input.command`
5. Match commands that represent PR creation or merge events:
   - `gh pr create` (any form — with or without flags)
   - `git merge` (any form)
   - `gh pr merge` (any form)
6. If command matches: check whether `.linear-issue` exists at the project root
   - Project root: walk up from `os.getcwd()` looking for a directory that contains `.git`. Fall back to `os.getcwd()` if no `.git` is found (e.g., in unusual environments).
7. If `.linear-issue` exists: read the issue ID from it, output JSON with `additionalContext`
8. If `.linear-issue` does not exist: exit 0 silently (no output)
9. Always exit 0 — never block the Bash command

**Step 1: Create linear-status-hook.py**

Create `plugins/jackal-linear/hooks/linear-status-hook.py` with the following content:

```python
#!/usr/bin/env python3
"""
PostToolUse hook that reminds Claude to update Linear issue status
after PR creation or merge events.
"""
import json
import os
import re
import sys


def find_project_root() -> str:
    """Walk up from cwd to find the directory containing .git. Fall back to cwd."""
    current = os.path.abspath(os.getcwd())
    while True:
        if os.path.exists(os.path.join(current, ".git")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return os.getcwd()
        current = parent


def find_linear_issue_file():
    """Return path to .linear-issue at project root if it exists, else None."""
    project_root = find_project_root()
    path = os.path.join(project_root, ".linear-issue")
    return path if os.path.isfile(path) else None


def is_pr_or_merge_command(command: str) -> tuple[bool, str]:
    """
    Return (matched, event_type) where event_type is 'pr-created' or 'merged'.
    """
    if re.search(r"\bgh\s+pr\s+create\b", command):
        return True, "pr-created"
    if re.search(r"\bgit\s+merge\b", command):
        return True, "merged"
    if re.search(r"\bgh\s+pr\s+merge\b", command):
        return True, "merged"
    return False, ""


try:
    input_data = json.load(sys.stdin)
except (json.JSONDecodeError, ValueError):
    sys.exit(0)

tool_name = input_data.get("tool_name", "")
if tool_name != "Bash":
    sys.exit(0)

tool_input = input_data.get("tool_input", {})
command = tool_input.get("command", "")

matched, event_type = is_pr_or_merge_command(command)
if not matched:
    sys.exit(0)

linear_issue_file = find_linear_issue_file()
if linear_issue_file is None:
    sys.exit(0)

try:
    issue_id = open(linear_issue_file).read().strip()
except OSError:
    sys.exit(0)

if not issue_id:
    sys.exit(0)

output = {
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": (
            f"Linear issue {issue_id} is active. "
            f"Use the linear-workflow skill (jackal-linear:linear-workflow) to update its status. "
            f"Event: {event_type}."
        )
    }
}
print(json.dumps(output))
sys.exit(0)
```

**Step 2: Make the script executable**

```bash
chmod +x plugins/jackal-linear/hooks/linear-status-hook.py
```

**Step 3: Verify the script**

Test that the script exits silently with no output when no match:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | python3 plugins/jackal-linear/hooks/linear-status-hook.py
echo "Exit code: $?"
```
Expected: No output, `Exit code: 0`

Test that the script exits silently when `.linear-issue` is absent (run from a directory without `.linear-issue`):

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"gh pr create --title test"}}' | python3 plugins/jackal-linear/hooks/linear-status-hook.py
echo "Exit code: $?"
```
Expected: No output, `Exit code: 0`

Test that the script outputs the reminder when `.linear-issue` is present (creates a temporary git repo to satisfy the project root detection):

```bash
TMP_DIR=$(mktemp -d)
mkdir "$TMP_DIR/.git"
echo "ENG-123" > "$TMP_DIR/.linear-issue"
(cd "$TMP_DIR" && python3 "$OLDPWD/plugins/jackal-linear/hooks/linear-status-hook.py" <<'EOF'
{"tool_name":"Bash","tool_input":{"command":"gh pr create --title 'My PR'"}}
EOF
)
echo "Exit code: $?"
rm -rf "$TMP_DIR"
```
Expected: JSON output containing `"additionalContext"` with `"ENG-123"` and `"pr-created"`, `Exit code: 0`

Test for merge event:

```bash
TMP_DIR=$(mktemp -d)
mkdir "$TMP_DIR/.git"
echo "ENG-456" > "$TMP_DIR/.linear-issue"
(cd "$TMP_DIR" && python3 "$OLDPWD/plugins/jackal-linear/hooks/linear-status-hook.py" <<'EOF'
{"tool_name":"Bash","tool_input":{"command":"git merge origin/feature-branch"}}
EOF
)
echo "Exit code: $?"
rm -rf "$TMP_DIR"
```
Expected: JSON output containing `"merged"`, `Exit code: 0`
<!-- END_TASK_2 -->

<!-- START_TASK_3 -->
### Task 3: Commit hooks

**Files:** No new files — commit the hooks created in Tasks 1 and 2.

**Step 1: Commit**

```bash
git add plugins/jackal-linear/hooks/hooks.json
git add plugins/jackal-linear/hooks/linear-status-hook.py
git commit -m "feat(jackal-linear): add PostToolUse hook for Linear status reminders"
```
<!-- END_TASK_3 -->
<!-- END_SUBCOMPONENT_A -->
