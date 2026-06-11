#!/usr/bin/env python3
"""
PostToolUse hook that reminds about gitignore and file permissions
after writing to files that typically contain secrets.
"""
import json
import re
import sys

SECRET_FILE_PATTERNS = [
    r"\.env$",
    r"\.env\.",
    r"\.envrc$",
    r"credentials",
    r"secrets?\.",
    r"\.pem$",
    r"\.key$",
    r"\.netrc$",
    r"\.npmrc$",
]


def file_looks_secret(path: str) -> bool:
    lower = path.lower()
    return any(re.search(pat, lower) for pat in SECRET_FILE_PATTERNS)


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    if tool_name not in ("Write", "Edit"):
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_looks_secret(file_path):
        sys.exit(0)

    filename = file_path.rsplit("/", 1)[-1] if "/" in file_path else file_path

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                f"You just wrote to {filename}, which may contain secrets. "
                f"Verify: (1) git check-ignore -v {filename} confirms it is gitignored, "
                f"and (2) file permissions are 600 (chmod 600 {filename}). "
                f"If either check fails, fix it now before proceeding."
            ),
        }
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
