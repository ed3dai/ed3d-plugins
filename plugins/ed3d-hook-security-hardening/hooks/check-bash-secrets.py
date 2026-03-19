#!/usr/bin/env python3
"""
PreToolUse hook that catches common secrets leakage patterns in Bash commands.

Returns permissionDecision: "deny" for high-confidence leaks,
"ask" for medium-confidence patterns that may have legitimate uses.
"""
import json
import re
import shlex
import sys

# Words in variable/file names that suggest secrets
SECRET_WORDS = {
    "secret", "token", "password", "passwd", "key", "credential",
    "auth", "private", "api_key", "apikey", "access_key", "accesskey",
}

# Files that typically contain secrets
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
    r"aws/credentials",
]

# Commands that read/display file contents
FILE_READ_COMMANDS = {"cat", "less", "more", "head", "tail", "bat", "view"}

# Commands that display environment variable values
ENV_DISPLAY_COMMANDS = {"printenv", "env"}


def name_looks_secret(name: str) -> bool:
    """Check if a variable or file name contains secret-suggesting words."""
    lower = name.lower()
    return any(word in lower for word in SECRET_WORDS)


def file_looks_secret(path: str) -> bool:
    """Check if a file path matches known secret file patterns."""
    lower = path.lower()
    return any(re.search(pat, lower) for pat in SECRET_FILE_PATTERNS)


def split_pipeline(command: str) -> list[list[str]]:
    """Split a command into pipeline stages, then tokenize each stage."""
    # Split on unquoted pipes. shlex doesn't understand pipes as operators,
    # so we split first on | then tokenize each stage.
    stages = []
    current = []
    try:
        tokens = shlex.split(command)
    except ValueError:
        # Malformed quoting — fall back to naive split
        tokens = command.split()

    for token in tokens:
        if token == "|":
            if current:
                stages.append(current)
            current = []
        else:
            current.append(token)
    if current:
        stages.append(current)
    return stages


def check_echo_secret(command: str) -> str | None:
    """Check for echo/printf of environment variables with secret-like names."""
    # Match echo/printf with $VAR, ${VAR}, ${VAR:...} patterns
    match = re.search(
        r"\b(echo|printf)\b.*\$\{?([A-Za-z_][A-Za-z0-9_]*)",
        command,
    )
    if match and name_looks_secret(match.group(2)):
        var_name = match.group(2)
        return (
            f"This command would echo ${var_name} into Claude's context, "
            f"leaking it to the API provider. "
            f'Use [[ -v {var_name} ]] && echo "set" || echo "not set" '
            f"to check existence without reading the value."
        )
    return None


def check_printenv_secret(stages: list[list[str]]) -> str | None:
    """Check for printenv with a secret-like variable name argument."""
    for stage in stages:
        if not stage:
            continue
        cmd = stage[0]
        if cmd == "printenv" and len(stage) > 1:
            var_name = stage[1]
            if name_looks_secret(var_name):
                return (
                    f"printenv {var_name} would read the secret value into context. "
                    f'Use [[ -v {var_name} ]] && echo "set" || echo "not set" instead.'
                )
    return None


def check_env_grep_no_quiet(stages: list[list[str]]) -> str | None:
    """Check for env|grep, export|grep, set|grep without -q flag."""
    for i, stage in enumerate(stages):
        if not stage:
            continue
        cmd = stage[0]
        if cmd in ("env", "export", "set") and i + 1 < len(stages):
            next_stage = stages[i + 1]
            if next_stage and next_stage[0] == "grep":
                has_quiet = any(
                    flag in next_stage
                    for flag in ("-q", "--quiet", "-qc", "-cq")
                )
                # Also check combined flags like -qi, -qE, etc.
                if not has_quiet:
                    for token in next_stage[1:]:
                        if (
                            token.startswith("-")
                            and "q" in token
                            and not token.startswith("--")
                        ):
                            has_quiet = True
                            break
                if not has_quiet:
                    return (
                        f"{cmd} | grep without -q displays the matching line, "
                        f"which includes the secret value. "
                        f"Add -q to check existence silently, or use "
                        f'[[ -v VAR ]] && echo "set" || echo "not set".'
                    )
    return None


def check_cat_secret_file(stages: list[list[str]]) -> str | None:
    """Check for cat/less/head/tail on files that likely contain secrets."""
    for stage in stages:
        if not stage:
            continue
        cmd = stage[0]
        if cmd in FILE_READ_COMMANDS:
            for arg in stage[1:]:
                if arg.startswith("-"):
                    continue
                if file_looks_secret(arg):
                    return (
                        f"{cmd} {arg} would read secret file contents into context. "
                        f"To inspect structure without values: "
                        f"grep '^[A-Z_]*=' {arg} | cut -d= -f1"
                    )
    return None


def check_source_secret_file(command: str) -> str | None:
    """Check for source/dot-sourcing of secret files."""
    match = re.search(r"(?:^|[;&|]\s*)(source|\.)\s+(\S+)", command)
    if match and file_looks_secret(match.group(2)):
        filename = match.group(2)
        return (
            f"source {filename} loads secret values into the shell environment "
            f"where subsequent commands may expose them. "
            f"If checking existence, use: "
            f"grep '^[A-Z_]*=' {filename} | cut -d= -f1"
        )
    return None


def check_grep_config_leaks(stages: list[list[str]], command: str) -> str | None:
    """Check for grep on shell config files that would show export lines with values."""
    config_files = {
        ".zshrc", ".bashrc", ".bash_profile", ".zprofile",
        ".profile", ".zshenv",
    }
    for stage in stages:
        if not stage:
            continue
        cmd = stage[0]
        if cmd != "grep":
            continue
        # Check if targeting a config file
        targets_config = any(
            any(cf in arg for cf in config_files)
            for arg in stage[1:]
            if not arg.startswith("-")
        )
        if not targets_config:
            continue
        # Check if searching for a secret-like pattern
        searches_secret = any(
            name_looks_secret(arg)
            for arg in stage[1:]
            if not arg.startswith("-")
        )
        if not searches_secret:
            continue
        # Check if -q or -c is present (safe)
        has_safe_flag = any(
            flag in stage for flag in ("-q", "--quiet", "-c", "--count", "-qc", "-cq")
        )
        if not has_safe_flag:
            for token in stage[1:]:
                if (
                    token.startswith("-")
                    and not token.startswith("--")
                    and ("q" in token or "c" in token)
                ):
                    has_safe_flag = True
                    break
        if not has_safe_flag:
            return (
                "grep on shell config files shows the full export line including "
                "the secret value. Use grep -qc to check presence without showing content."
            )
    return None


def check_git_clone_token(command: str) -> str | None:
    """Check for tokens embedded in git clone URLs."""
    if "git" in command and "clone" in command:
        # Match patterns like https://$TOKEN@github.com or https://${TOKEN}@
        if re.search(r"https?://\$[{(]?[A-Za-z_]+[})]?@", command):
            return (
                "Embedding tokens in git clone URLs persists them in "
                ".git/config and shell history. Use GIT_ASKPASS or a "
                "credential helper instead."
            )
    return None


def check_curl_url_token(command: str) -> str | None:
    """Check for tokens passed as URL query parameters in curl."""
    if "curl" not in command:
        return None
    # Match ?key=$VAR, ?token=$VAR, &api_key=$VAR, etc.
    match = re.search(
        r"[?&](api[_-]?key|token|secret|password|auth|access[_-]?key)"
        r"\s*=\s*\$",
        command,
        re.IGNORECASE,
    )
    if match:
        return (
            "Tokens in URL query parameters get logged in server access logs, "
            "proxy logs, and browser history. Use -H 'Authorization: Bearer $TOKEN' "
            "to pass credentials in headers instead."
        )
    return None


def check_length_or_substring(command: str) -> str | None:
    """Check for ${#VAR} (length) or ${VAR:0:N} (substring) on secret vars."""
    # ${#VAR}
    match = re.search(r"\$\{#([A-Za-z_][A-Za-z0-9_]*)\}", command)
    if match and name_looks_secret(match.group(1)):
        return (
            f"${{#{match.group(1)}}} leaks the length of the secret, "
            f"which narrows the search space and confirms the format. Reveal nothing."
        )
    # ${VAR:offset:length}
    match = re.search(
        r"\$\{([A-Za-z_][A-Za-z0-9_]*):\d+[^}]*\}", command
    )
    if match and name_looks_secret(match.group(1)):
        return (
            f"Partial value of ${{{match.group(1)}}} still leaks secret material. "
            f"An 8-character prefix dramatically narrows the search space. Reveal nothing."
        )
    return None


def deny(reason: str) -> None:
    """Output a deny decision and exit."""
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(output))
    sys.exit(0)


def ask(reason: str) -> None:
    """Output an ask decision (force user approval) and exit."""
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(output))
    sys.exit(0)


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    if input_data.get("tool_name") != "Bash":
        sys.exit(0)

    command = input_data.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    stages = split_pipeline(command)

    # High confidence: deny outright
    # These patterns have no legitimate use that wouldn't also be served by the safe alternative.

    for check in [
        lambda: check_echo_secret(command),
        lambda: check_printenv_secret(stages),
        lambda: check_length_or_substring(command),
    ]:
        reason = check()
        if reason:
            deny(reason)

    # Medium confidence: force user approval
    # These have occasional legitimate uses but are dangerous by default.

    for check in [
        lambda: check_env_grep_no_quiet(stages),
        lambda: check_cat_secret_file(stages),
        lambda: check_source_secret_file(command),
        lambda: check_grep_config_leaks(stages, command),
        lambda: check_git_clone_token(command),
        lambda: check_curl_url_token(command),
    ]:
        reason = check()
        if reason:
            ask(reason)

    # No issues found
    sys.exit(0)


if __name__ == "__main__":
    main()
