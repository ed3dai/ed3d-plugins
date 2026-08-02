#!/usr/bin/env python3
"""
PreToolUse hook that warns before a long agent dispatch when the harness's own AWS
SSO credentials cannot survive it.

Why this exists: when Claude Code runs on Bedrock, every agent in the fleet
authenticates through ONE cached SSO token. When that token lapses, every in-flight
agent dies within the same second -- including the orchestrator, which is therefore
unable to run its own stall-recovery logic. Observed repeatedly 2026-07-17..07-31
(parent and child dying 1s apart).

The pre-flight in execute/SKILL.md guarded the *downstream project's* AWS creds, not
the harness's own session, so it never fired for this failure mode.

What it checks, reading only ~/.aws (no STS calls, no network, no token values):
  1. Is there a cached SSO token at all, and is it already expired?
  2. Does it carry a refreshToken? Without one (the legacy non-refreshable config
     format) the token cannot renew and expiry forces an interactive `aws sso login`.
  3. Is the client registration close to expiring? Registration expiry defeats
     refresh, so a valid refreshToken is not sufficient on its own.

This WARNS (additionalContext) rather than denying. A false deny would block real
work over a credential state the agent cannot fix, and only the operator can run
`aws sso login`. Set JACKAL_PREFLIGHT_BLOCK=1 to make unrefreshable-and-expiring
states deny instead.
"""

import datetime
import glob
import hashlib
import json
import os
import re
import sys

TRUTHY = {"1", "true", "yes", "on"}

BLOCK_ENV_VAR = "JACKAL_PREFLIGHT_BLOCK"
DISABLE_ENV_VAR = "JACKAL_PREFLIGHT_DISABLE"
SESSION_ENV_VAR = "JACKAL_SSO_SESSION"

# Only Agent dispatches are gated: a dispatch is the thing that runs unattended for
# long enough to outlive a token. Interactive tool calls fail visibly and are retried.
GATED_TOOLS = ("Agent", "Task")

# Below this, a dispatch that cannot refresh is very likely to die mid-flight.
SHORT_LIFETIME_SECONDS = 30 * 60

# Registration expiry cannot be refreshed away, so warn earlier on it.
REGISTRATION_WARN_SECONDS = 3 * 24 * 60 * 60

AWS_SSO_CACHE = "~/.aws/sso/cache"
AWS_CONFIG = "~/.aws/config"


def enabled() -> bool:
    if os.environ.get(DISABLE_ENV_VAR, "").strip().lower() in TRUTHY:
        return False
    # Only meaningful when the harness authenticates via Bedrock.
    return os.environ.get("CLAUDE_CODE_USE_BEDROCK", "").strip().lower() in TRUTHY


def blocking() -> bool:
    return os.environ.get(BLOCK_ENV_VAR, "").strip().lower() in TRUTHY


def parse_timestamp(raw: str) -> datetime.datetime | None:
    if not isinstance(raw, str) or not raw:
        return None
    try:
        return datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def configured_session_name() -> str | None:
    """
    Name of the sso-session the active profile uses, if the config declares one.

    The SSO cache filename is sha1 of the session name (sso-session format) or of the
    start URL (legacy format), so knowing the name lets us identify the exact token
    this harness depends on rather than guessing among several cached files.
    """
    override = os.environ.get(SESSION_ENV_VAR, "").strip()
    if override:
        return override

    path = os.path.expanduser(AWS_CONFIG)
    if not os.path.isfile(path):
        return None
    profile = (os.environ.get("AWS_PROFILE") or "default").strip()
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            lines = handle.readlines()
    except OSError:
        return None

    wanted = "[default]" if profile == "default" else f"[profile {profile}]"
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("["):
            in_section = stripped == wanted
            continue
        if not in_section or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        if key.strip() == "sso_session":
            return value.strip()
    return None


def source_profile_chain_session() -> str | None:
    """
    Follow source_profile hops to find the sso_session the chain ultimately uses.

    Bedrock profiles are usually assumed roles (`DevOps_EDRC-Dev` ->
    `AWS_DevOps_EDRC-Dev` -> `HCG-SSO-DevOps`), and only the last hop names the
    sso-session. Without following the chain we would see no session and stay silent
    in exactly the configuration this hook exists for.
    """
    path = os.path.expanduser(AWS_CONFIG)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            content = handle.read()
    except OSError:
        return None

    sections: dict[str, dict[str, str]] = {}
    current: str | None = None
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current = stripped[1:-1].strip()
            sections[current] = {}
            continue
        if current is None or "=" not in stripped or stripped.startswith("#"):
            continue
        key, _, value = stripped.partition("=")
        sections[current][key.strip()] = value.strip()

    profile = (os.environ.get("AWS_PROFILE") or "default").strip()
    seen = set()
    for _ in range(10):  # bounded: config could contain a source_profile cycle
        key = "default" if profile == "default" else f"profile {profile}"
        if key in seen or key not in sections:
            return None
        seen.add(key)
        section = sections[key]
        if "sso_session" in section:
            return section["sso_session"]
        if "sso_start_url" in section:
            return None  # legacy format: cached by start URL, not session name
        nxt = section.get("source_profile")
        if not nxt:
            return None
        profile = nxt
    return None


def cache_path_for(session: str) -> str | None:
    digest = hashlib.sha1(session.encode("utf-8")).hexdigest()  # noqa: S324 - AWS's scheme
    candidate = os.path.join(os.path.expanduser(AWS_SSO_CACHE), f"{digest}.json")
    return candidate if os.path.isfile(candidate) else None


def load_token() -> tuple[dict | None, str | None]:
    """
    Return (token_dict, source_label) for the token this harness depends on.

    Prefers the exact cache file derived from the configured sso-session name; falls
    back to the most recently modified token file that actually holds an accessToken.
    """
    session = configured_session_name() or source_profile_chain_session()
    if session:
        path = cache_path_for(session)
        if path:
            try:
                with open(path, encoding="utf-8") as handle:
                    return json.load(handle), f"sso-session '{session}'"
            except (OSError, json.JSONDecodeError):
                return None, f"sso-session '{session}' (cache unreadable)"

    files = glob.glob(os.path.join(os.path.expanduser(AWS_SSO_CACHE), "*.json"))
    best: tuple[float, dict] | None = None
    for path in files:
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue
        if "accessToken" not in data:
            continue  # client-registration entries, not session tokens
        mtime = os.path.getmtime(path)
        if best is None or mtime > best[0]:
            best = (mtime, data)
    if best is None:
        return None, None
    return best[1], "most recent cached SSO token"


def humanize(delta: datetime.timedelta) -> str:
    seconds = int(delta.total_seconds())
    if seconds < 0:
        return "expired"
    hours, remainder = divmod(seconds, 3600)
    minutes = remainder // 60
    if hours >= 24:
        return f"{hours // 24}d {hours % 24}h"
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def expected_seconds(tool_input: dict) -> int | None:
    """
    Best-effort read of how long this dispatch expects to run.

    Jackal dispatch prompts carry `EXPECT: commit a resumable checkpoint within
    <n>s/<n>m`. Absent that, duration is unknown and only hard states are reported.
    """
    prompt = tool_input.get("prompt")
    if not isinstance(prompt, str):
        return None
    match = re.search(r"EXPECT\b[^\n]*?within\s+(\d+)\s*(s|sec|seconds|m|min|minutes|h|hours)\b", prompt, re.IGNORECASE)
    if not match:
        return None
    value, unit = int(match.group(1)), match.group(2).lower()
    if unit.startswith("s"):
        return value
    if unit.startswith("m"):
        return value * 60
    return value * 3600


def assess(token: dict | None, source: str | None, dispatch_seconds: int | None) -> str | None:
    """Return a warning message, or None when credentials look fine for this dispatch."""
    if token is None:
        if source:
            return (
                f"Could not read the harness's AWS SSO token ({source}). If this dispatch "
                "is long-running, confirm credentials first: `aws sso login`."
            )
        return None  # no SSO cache at all: probably not an SSO setup, stay quiet

    now = datetime.datetime.now(datetime.timezone.utc)
    expires = parse_timestamp(token.get("expiresAt", ""))
    refreshable = bool(token.get("refreshToken"))
    registration = parse_timestamp(token.get("registrationExpiresAt", ""))

    if expires is None:
        return None

    remaining = expires - now
    problems = []

    if remaining.total_seconds() <= 0:
        problems.append(
            f"The harness's SSO token ({source}) EXPIRED {humanize(-remaining)} ago."
            + ("" if refreshable else " It has no refreshToken, so it cannot renew itself.")
        )
    elif not refreshable:
        # Legacy non-refreshable config: expiry means an interactive login, so any
        # dispatch outliving the token is doomed.
        threshold = dispatch_seconds if dispatch_seconds else SHORT_LIFETIME_SECONDS
        if remaining.total_seconds() <= threshold:
            detail = f"this dispatch expects up to {humanize(datetime.timedelta(seconds=dispatch_seconds))}" if dispatch_seconds else "long dispatches are at risk"
            problems.append(
                f"The harness's SSO token ({source}) expires in {humanize(remaining)} and has "
                f"no refreshToken, so it cannot renew itself — {detail}."
            )

    if registration is not None:
        reg_remaining = registration - now
        if reg_remaining.total_seconds() <= 0:
            problems.append(
                "The SSO client registration has expired; refresh cannot recover from this."
            )
        elif reg_remaining.total_seconds() <= REGISTRATION_WARN_SECONDS:
            problems.append(
                f"The SSO client registration expires in {humanize(reg_remaining)}; "
                "once it lapses, token refresh stops working."
            )

    if not problems:
        return None

    return (
        "CREDENTIAL PRE-FLIGHT — the whole agent fleet shares this one token, so if it "
        "lapses every in-flight agent (including the orchestrator) dies at the same moment.\n\n"
        + "\n".join(f"  - {p}" for p in problems)
        + "\n\nOnly the operator can fix this — an agent cannot run an interactive login. "
        "Ask them to run `aws sso login` (or their alias) before starting long work, and "
        "have implementors commit a resumable checkpoint early so nothing depends on the "
        "session surviving.\n"
        f"Set {DISABLE_ENV_VAR}=1 to silence this check."
    )


def emit_warning(message: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "additionalContext": message,
                }
            }
        )
    )
    sys.exit(0)


def emit_deny(message: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": message,
                }
            }
        )
    )
    sys.exit(0)


def main() -> None:
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        sys.exit(0)
    if not isinstance(input_data, dict):
        sys.exit(0)
    if input_data.get("tool_name") not in GATED_TOOLS:
        sys.exit(0)
    if not enabled():
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    if not isinstance(tool_input, dict):
        tool_input = {}

    try:
        token, source = load_token()
        message = assess(token, source, expected_seconds(tool_input))
    except SystemExit:
        raise
    except Exception:
        # A pre-flight that crashes the dispatch is worse than one that misses a
        # warning. This hook is advisory; stay silent on internal failure.
        sys.exit(0)

    if message:
        emit_deny(message) if blocking() else emit_warning(message)
    sys.exit(0)


if __name__ == "__main__":
    main()
