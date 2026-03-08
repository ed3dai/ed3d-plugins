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
