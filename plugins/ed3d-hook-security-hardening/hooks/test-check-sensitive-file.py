#!/usr/bin/env python3
"""
Tests for check-sensitive-file.py PostToolUse hook.
Run: python3 test-check-sensitive-file.py
"""
import json
import subprocess
import sys
import os

SCRIPT = os.path.join(os.path.dirname(__file__), "check-sensitive-file.py")


def run_hook(tool_name: str, file_path: str) -> dict | None:
    """Run the hook and return parsed output, or None if no output."""
    input_data = json.dumps({"tool_name": tool_name, "tool_input": {"file_path": file_path}})
    result = subprocess.run(
        [sys.executable, SCRIPT],
        input=input_data,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Hook exited with {result.returncode}: {result.stderr}"
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)


def has_context(output: dict | None) -> bool:
    if output is None:
        return False
    return "additionalContext" in output.get("hookSpecificOutput", {})


passed = 0
failed = 0
errors = []


def test(name: str, tool_name: str, file_path: str, should_warn: bool):
    global passed, failed
    try:
        output = run_hook(tool_name, file_path)
        warned = has_context(output)
        if warned != should_warn:
            errors.append(f"FAIL [{name}]: expected warn={should_warn}, got warn={warned}")
            failed += 1
        else:
            passed += 1
    except Exception as e:
        errors.append(f"ERROR [{name}]: {e}")
        failed += 1


# ============================================================
# Section 1: Files that should trigger warnings
# ============================================================

# .env variants
test(".env", "Write", "/app/.env", True)
test(".env.local", "Write", "/app/.env.local", True)
test(".env.production", "Write", "/app/.env.production", True)
test(".env.development", "Edit", "/app/.env.development", True)

# .envrc (direnv)
test(".envrc", "Write", "/app/.envrc", True)

# Credential files
test("credentials.json", "Write", "/app/credentials.json", True)
test("credentials.yaml", "Edit", "/home/user/credentials.yaml", True)
test("gcp-credentials.json", "Write", "/app/gcp-credentials.json", True)

# Secret files
test("secrets.yaml", "Write", "/app/secrets.yaml", True)
test("secrets.json", "Edit", "/app/secrets.json", True)
test("secret.conf", "Write", "/etc/myapp/secret.conf", True)

# Key/cert files
test("private.pem", "Write", "/app/private.pem", True)
test("server.pem", "Write", "/etc/ssl/server.pem", True)
test("tls.key", "Write", "/app/tls.key", True)
test("server.key", "Edit", "/etc/nginx/server.key", True)

# Auth config files
test(".netrc", "Write", "/home/user/.netrc", True)
test(".npmrc", "Write", "/home/user/.npmrc", True)

# ============================================================
# Section 2: Files that should NOT trigger warnings
# ============================================================
test("README.md", "Write", "/app/README.md", False)
test("package.json", "Edit", "/app/package.json", False)
test("server.js", "Write", "/app/server.js", False)
test("index.html", "Write", "/app/index.html", False)
test("Dockerfile", "Write", "/app/Dockerfile", False)
test(".gitignore", "Edit", "/app/.gitignore", False)
test("config.ts", "Write", "/app/config.ts", False)
test("docker-compose.yml", "Write", "/app/docker-compose.yml", False)
test("tsconfig.json", "Edit", "/app/tsconfig.json", False)
test(".env.example", "Write", "/app/.env.example", True)  # still has .env. pattern — intentional

# ============================================================
# Section 3: Only Write and Edit should trigger
# ============================================================
test("Read .env", "Read", "/app/.env", False)
test("Glob .env", "Glob", "/app/.env", False)
test("Grep .env", "Grep", "/app/.env", False)

# ============================================================
# Section 4: Warning content validation
# ============================================================
output = run_hook("Write", "/app/.env")
if output:
    ctx = output["hookSpecificOutput"]["additionalContext"]
    checks = [
        ("mentions filename", ".env" in ctx),
        ("mentions gitignore", "gitignore" in ctx.lower() or "git check-ignore" in ctx),
        ("mentions chmod", "chmod" in ctx or "600" in ctx),
    ]
    for check_name, check_result in checks:
        if check_result:
            passed += 1
        else:
            errors.append(f"FAIL [content: {check_name}]: not found in: {ctx[:100]}")
            failed += 1
else:
    errors.append("FAIL [content validation]: no output for .env write")
    failed += 3

# ============================================================
# Section 5: Malformed input — should not crash
# ============================================================
for label, bad_input in [
    ("empty stdin", ""),
    ("invalid json", "not json"),
    ("missing tool_input", json.dumps({"tool_name": "Write"})),
    ("missing file_path", json.dumps({"tool_name": "Write", "tool_input": {}})),
]:
    result = subprocess.run(
        [sys.executable, SCRIPT],
        input=bad_input,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        passed += 1
    else:
        errors.append(f"FAIL [{label}]: crashed with exit code {result.returncode}")
        failed += 1

# ============================================================
# Results
# ============================================================
print()
if errors:
    for e in errors:
        print(e)
    print()

print(f"{passed}/{passed + failed} tests passed, {failed} failed")
sys.exit(1 if failed > 0 else 0)
