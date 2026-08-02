#!/usr/bin/env python3
"""Tests for check-credential-preflight.py. Run: python3 test-check-credential-preflight.py

Uses real temp HOME dirs with real ~/.aws trees -- no mocks -- so the cache-filename
derivation and config chain-walking are exercised as they run in production.
"""

import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "check-credential-preflight.py")

SILENT, WARN, DENY = "silent", "warn", "deny"

CHAIN_CONFIG = """\
[profile HCG-SSO-DevOps]
sso_session = hcg
sso_account_id = 771325996793
sso_role_name = AWS_DevOps_EDRC-Dev

[profile AWS_DevOps_EDRC-Dev]
role_arn = arn:aws:iam::771325996793:role/AWS_DevOps_EDRC-Dev
source_profile = HCG-SSO-DevOps

[profile DevOps_EDRC-Dev]
role_arn = arn:aws:iam::726959544649:role/DevOps_EDRC-Dev
source_profile = AWS_DevOps_EDRC-Dev

[sso-session hcg]
sso_region = us-east-2
sso_start_url = https://hcg-sso.awsapps.com/start
"""

LEGACY_CONFIG = """\
[profile HCG-SSO-DevOps]
sso_start_url = https://hcg-sso.awsapps.com/start
sso_region = us-east-2
sso_account_id = 771325996793
sso_role_name = AWS_DevOps_EDRC-Dev
"""


def iso(delta_seconds: int) -> str:
    when = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=delta_seconds)
    return when.strftime("%Y-%m-%dT%H:%M:%SZ")


def make_home(config: str, tokens: dict[str, dict]) -> str:
    """Build a temp HOME with ~/.aws/config and ~/.aws/sso/cache/<sha1>.json files."""
    home = tempfile.mkdtemp()
    cache = os.path.join(home, ".aws", "sso", "cache")
    os.makedirs(cache)
    with open(os.path.join(home, ".aws", "config"), "w", encoding="utf-8") as handle:
        handle.write(config)
    for key, payload in tokens.items():
        digest = hashlib.sha1(key.encode()).hexdigest()
        with open(os.path.join(cache, f"{digest}.json"), "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
    return home


def run(home: str, tool: str = "Agent", prompt: str = "", env: dict | None = None) -> tuple[str, str]:
    payload = {"tool_name": tool, "tool_input": {"prompt": prompt}, "cwd": home}
    merged = {
        **os.environ,
        "HOME": home,
        "CLAUDE_CODE_USE_BEDROCK": "1",
        "AWS_PROFILE": "DevOps_EDRC-Dev",
    }
    for var in ("JACKAL_PREFLIGHT_BLOCK", "JACKAL_PREFLIGHT_DISABLE", "JACKAL_SSO_SESSION"):
        merged.pop(var, None)
    merged.update(env or {})
    result = subprocess.run(
        [sys.executable, HOOK], input=json.dumps(payload),
        capture_output=True, text=True, env=merged, timeout=30,
    )
    if result.returncode != 0:
        raise AssertionError(f"hook exited {result.returncode}: {result.stderr}")
    if not result.stdout.strip():
        return SILENT, ""
    out = json.loads(result.stdout)["hookSpecificOutput"]
    if out.get("permissionDecision") == "deny":
        return DENY, out.get("permissionDecisionReason", "")
    return WARN, out.get("additionalContext", "")


FAILURES: list[str] = []
PASSED = 0


def check(label: str, actual: tuple[str, str], expected: str, must_contain: str = "") -> None:
    global PASSED
    decision, message = actual
    if decision != expected:
        FAILURES.append(f"{label}: expected {expected}, got {decision} ({message[:90]})")
        return
    if must_contain and must_contain.lower() not in message.lower():
        FAILURES.append(f"{label}: message missing {must_contain!r}; got {message[:140]}")
        return
    PASSED += 1


HOMES: list[str] = []


def home(config: str, tokens: dict[str, dict]) -> str:
    path = make_home(config, tokens)
    HOMES.append(path)
    return path


def healthy_token() -> dict:
    return {
        "accessToken": "x", "refreshToken": "r", "expiresAt": iso(8 * 3600),
        "registrationExpiresAt": iso(60 * 86400), "startUrl": "https://hcg-sso.awsapps.com/start",
        "region": "us-east-2",
    }


def main() -> int:
    # --- healthy: refreshable, plenty of runway -> silent ---
    h = home(CHAIN_CONFIG, {"hcg": healthy_token()})
    check("healthy token", run(h), SILENT)
    check("healthy, long dispatch", run(h, prompt="EXPECT: commit within 45m"), SILENT)

    # --- refreshable but nearly expired -> silent, because refresh handles it ---
    tok = healthy_token(); tok["expiresAt"] = iso(5 * 60)
    h = home(CHAIN_CONFIG, {"hcg": tok})
    check("refreshable, 5m left", run(h), SILENT)

    # --- legacy non-refreshable, short runway -> warn ---
    tok = healthy_token(); del tok["refreshToken"]; tok["expiresAt"] = iso(10 * 60)
    h = home(CHAIN_CONFIG, {"hcg": tok})
    check("no refreshToken, 10m left", run(h), WARN, "refreshToken")

    # --- legacy non-refreshable but lots of runway -> silent ---
    tok = healthy_token(); del tok["refreshToken"]; tok["expiresAt"] = iso(6 * 3600)
    h = home(CHAIN_CONFIG, {"hcg": tok})
    check("no refreshToken, 6h left", run(h), SILENT)

    # --- non-refreshable, runway shorter than the DECLARED dispatch -> warn ---
    tok = healthy_token(); del tok["refreshToken"]; tok["expiresAt"] = iso(40 * 60)
    h = home(CHAIN_CONFIG, {"hcg": tok})
    check("dispatch outlives token", run(h, prompt="EXPECT: commit a checkpoint within 90m"), WARN, "expires in")
    check("short dispatch fits", run(h, prompt="EXPECT: commit within 5m"), SILENT)

    # --- already expired -> warn regardless ---
    tok = healthy_token(); tok["expiresAt"] = iso(-600)
    h = home(CHAIN_CONFIG, {"hcg": tok})
    check("expired token", run(h), WARN, "expired")

    # --- registration expiry defeats refresh -> warn even when refreshable ---
    tok = healthy_token(); tok["registrationExpiresAt"] = iso(36 * 3600)
    h = home(CHAIN_CONFIG, {"hcg": tok})
    check("registration expiring", run(h), WARN, "registration")

    tok = healthy_token(); tok["registrationExpiresAt"] = iso(-3600)
    h = home(CHAIN_CONFIG, {"hcg": tok})
    check("registration expired", run(h), WARN, "registration")

    # --- chain walking: the session name is only on the 3rd hop ---
    tok = healthy_token(); del tok["refreshToken"]; tok["expiresAt"] = iso(60)
    h = home(CHAIN_CONFIG, {"hcg": tok})
    check("follows source_profile chain", run(h), WARN, "sso-session 'hcg'")

    # --- a decoy token for a different session must not be picked when named ---
    good = healthy_token()
    decoy = healthy_token(); del decoy["refreshToken"]; decoy["expiresAt"] = iso(30)
    h = home(CHAIN_CONFIG, {"hcg": good, "other": decoy})
    check("ignores unrelated session token", run(h), SILENT)

    # --- gating ---
    tok = healthy_token(); tok["expiresAt"] = iso(-600)
    h = home(CHAIN_CONFIG, {"hcg": tok})
    check("non-dispatch tool ignored", run(h, tool="Bash"), SILENT)
    check("Task tool also gated", run(h, tool="Task"), WARN)
    check("disable env silences", run(h, env={"JACKAL_PREFLIGHT_DISABLE": "1"}), SILENT)
    check("block env denies", run(h, env={"JACKAL_PREFLIGHT_BLOCK": "1"}), DENY, "expired")
    check("non-bedrock silent", run(h, env={"CLAUDE_CODE_USE_BEDROCK": "0"}), SILENT)
    check("JACKAL_SSO_SESSION override", run(h, env={"JACKAL_SSO_SESSION": "hcg"}), WARN)

    # --- degenerate inputs must never crash or block ---
    h = home(CHAIN_CONFIG, {})
    check("no cached token", run(h), SILENT)
    h = home("", {})
    check("no aws config", run(h), SILENT)
    tok = {"accessToken": "x", "expiresAt": "not-a-date"}
    h = home(CHAIN_CONFIG, {"hcg": tok})
    check("unparseable expiry", run(h), SILENT)
    h = home(LEGACY_CONFIG, {"https://hcg-sso.awsapps.com/start": healthy_token()})
    check("legacy config format tolerated", run(h), SILENT)

    # registration-only entries (no accessToken) must not be mistaken for tokens
    h = home(CHAIN_CONFIG, {"hcg-reg": {"clientId": "c", "clientSecret": "s", "expiresAt": iso(86400)}})
    check("registration-only cache entry", run(h), SILENT)

    for path in HOMES:
        shutil.rmtree(path, ignore_errors=True)

    for failure in FAILURES:
        print("FAIL  ", failure)
    print(f"\n{PASSED} passed, {len(FAILURES)} failed")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
