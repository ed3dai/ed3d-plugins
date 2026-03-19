#!/usr/bin/env python3
"""
Tests for check-bash-secrets.py PreToolUse hook.
Run: python3 test-check-bash-secrets.py
"""
import json
import subprocess
import sys
import os

SCRIPT = os.path.join(os.path.dirname(__file__), "check-bash-secrets.py")


def run_hook(command: str) -> dict | None:
    """Run the hook with a Bash tool input and return parsed output, or None if no output."""
    input_data = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
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


def get_decision(output: dict | None) -> str | None:
    if output is None:
        return None
    return output["hookSpecificOutput"]["permissionDecision"]


def get_reason(output: dict | None) -> str:
    assert output is not None, "Expected output but got None"
    return output["hookSpecificOutput"]["permissionDecisionReason"]


passed = 0
failed = 0
errors = []


def test(name: str, command: str, expected_decision: str | None):
    global passed, failed
    try:
        output = run_hook(command)
        actual = get_decision(output)
        if actual != expected_decision:
            reason = get_reason(output) if output else "no output"
            errors.append(f"FAIL [{name}]: expected {expected_decision}, got {actual} ({reason})")
            failed += 1
        else:
            passed += 1
    except Exception as e:
        errors.append(f"ERROR [{name}]: {e}")
        failed += 1


# ============================================================
# Section 1: echo / printf with secret variables — should DENY
# ============================================================
test("echo secret key", "echo $API_KEY", "deny")
test("echo secret token", "echo $AUTH_TOKEN", "deny")
test("echo with braces", "echo ${STRIPE_SECRET_KEY}", "deny")
test("echo password", "echo $DATABASE_PASSWORD", "deny")
test("echo credential", "echo $AWS_CREDENTIAL", "deny")
test("echo private key", "echo $PRIVATE_KEY", "deny")
test("echo access key", "echo $AWS_ACCESS_KEY", "deny")
test("echo apikey no underscore", "echo $APIKEY", "deny")
test("echo accesskey no underscore", "echo $ACCESSKEY", "deny")
test("echo passwd", "echo $DB_PASSWD", "deny")
test("printf secret", 'printf "%s" $API_SECRET', "deny")
test("echo in string", 'echo "The key is ${API_KEY}"', "deny")

# echo with non-secret variables — should PASS
test("echo HOME", "echo $HOME", None)
test("echo PATH", "echo $PATH", None)
test("echo USER", "echo $USER", None)
test("echo SHELL", "echo $SHELL", None)
test("echo NODE_ENV", "echo $NODE_ENV", None)
test("echo PORT", "echo $PORT", None)
test("echo plain string", "echo hello world", None)
test("echo no variable", "echo 'some text'", None)

# ============================================================
# Section 2: printenv with secret variables — should DENY
# ============================================================
test("printenv secret", "printenv API_KEY", "deny")
test("printenv token", "printenv GITHUB_TOKEN", "deny")
test("printenv password", "printenv DATABASE_PASSWORD", "deny")

# printenv with non-secret variables — should PASS
test("printenv PATH", "printenv PATH", None)
test("printenv HOME", "printenv HOME", None)
test("printenv SHELL", "printenv SHELL", None)

# ============================================================
# Section 3: length and substring leaks — should DENY
# ============================================================
test("length of secret", "echo ${#API_KEY}", "deny")
test("length of token", "echo ${#STRIPE_SECRET_KEY}", "deny")
test("substring of secret", "echo ${API_KEY:0:8}", "deny")
test("substring of token", "echo ${AUTH_TOKEN:0:4}", "deny")
test("substring mid", "echo ${SECRET_KEY:2:10}", "deny")

# length/substring of non-secret — should PASS
test("length of PATH", "echo ${#PATH}", None)
test("substring of HOME", "echo ${HOME:0:5}", None)

# ============================================================
# Section 4: env|grep, export|grep, set|grep without -q — should ASK
# ============================================================
test("env grep no flag", "env | grep SECRET_KEY", "ask")
test("export grep no flag", "export | grep API_TOKEN", "ask")
test("set grep no flag", "set | grep PASSWORD", "ask")

# with -q flag — should PASS
test("env grep -q", "env | grep -q '^API_KEY='", None)
test("env grep -q inline", "env | grep -qE 'SECRET'", None)
test("export grep --quiet", "export | grep --quiet TOKEN", None)
test("env grep -cq", "env | grep -cq SECRET", None)

# ============================================================
# Section 5: cat/less/head/tail on secret files — should ASK
# ============================================================
test("cat .env", "cat .env", "ask")
test("cat .envrc", "cat .envrc", "ask")
test("cat .env.local", "cat .env.local", "ask")
test("cat credentials.json", "cat credentials.json", "ask")
test("cat secrets.yaml", "cat secrets.yaml", "ask")
test("cat private.pem", "cat server-private.pem", "ask")
test("cat .key file", "cat tls.key", "ask")
test("head .env", "head .env", "ask")
test("tail .envrc", "tail .envrc", "ask")
test("less credentials", "less credentials.json", "ask")
test("cat .netrc", "cat ~/.netrc", "ask")
test("cat .npmrc", "cat ~/.npmrc", "ask")
test("cat aws credentials", "cat ~/.aws/credentials", "ask")

# cat on normal files — should PASS
test("cat README", "cat README.md", None)
test("cat package.json", "cat package.json", None)
test("cat server.js", "cat server.js", None)
test("head Makefile", "head Makefile", None)
test("cat .gitignore", "cat .gitignore", None)

# ============================================================
# Section 6: source/dot on secret files — should ASK
# ============================================================
test("source .env", "source .env", "ask")
test("source .envrc", "source .envrc", "ask")
test("dot source .env", ". .env", "ask")
test("source .env.local", "source .env.local", "ask")

# source on normal files — should PASS
test("source .bashrc", "source ~/.bashrc", None)
test("source script", "source ./setup.sh", None)

# ============================================================
# Section 7: grep on shell config files for secrets — should ASK
# ============================================================
test("grep secret in zshrc", "grep API_KEY ~/.zshrc", "ask")
test("grep token in bashrc", "grep TOKEN ~/.bashrc", "ask")
test("grep password in profile", "grep PASSWORD ~/.profile", "ask")
test("grep secret in zprofile", "grep SECRET ~/.zprofile", "ask")
test("grep -n secret in zshrc", "grep -n API_KEY ~/.zshrc", "ask")

# grep -qc on config files — should PASS
test("grep -qc in zshrc", "grep -qc API_KEY ~/.zshrc", None)
test("grep -c in zshrc", "grep -c TOKEN ~/.zshrc", None)
test("grep --count in bashrc", "grep --count SECRET ~/.bashrc", None)

# grep for non-secret in config — should PASS
test("grep PATH in zshrc", "grep PATH ~/.zshrc", None)
test("grep alias in bashrc", "grep alias ~/.bashrc", None)

# ============================================================
# Section 8: git clone with embedded token — should ASK
# ============================================================
test("git clone with token", "git clone https://${GITHUB_TOKEN}@github.com/org/repo.git", "ask")
test("git clone with dollar", "git clone https://$TOKEN@github.com/org/repo.git", "ask")

# git clone without token — should PASS
test("git clone normal", "git clone https://github.com/org/repo.git", None)
test("git clone ssh", "git clone git@github.com:org/repo.git", None)

# ============================================================
# Section 9: curl with token in URL params — should ASK
# ============================================================
test("curl api_key param", 'curl "https://api.com/data?api_key=$TOKEN"', "ask")
test("curl token param", 'curl "https://api.com/data?token=$SECRET"', "ask")
test("curl secret param", 'curl "https://api.com?secret=$VAL"', "ask")
test("curl access_key param", 'curl "https://api.com?access_key=$KEY"', "ask")

# curl with header — should PASS
test("curl with header", 'curl -H "Authorization: Bearer ${API_TOKEN}" https://api.com', None)
test("curl no auth", "curl https://api.com/public", None)

# ============================================================
# Section 10: non-Bash tool input — should PASS (ignored)
# ============================================================
input_data = json.dumps({"tool_name": "Read", "tool_input": {"file_path": ".env"}})
result = subprocess.run(
    [sys.executable, SCRIPT],
    input=input_data,
    capture_output=True,
    text=True,
)
if result.stdout.strip() == "":
    passed += 1
else:
    errors.append(f"FAIL [non-Bash tool]: should produce no output for Read tool")
    failed += 1

# ============================================================
# Section 11: malformed input — should not crash
# ============================================================
for label, bad_input in [
    ("empty stdin", ""),
    ("invalid json", "{not json}"),
    ("missing tool_input", json.dumps({"tool_name": "Bash"})),
    ("empty command", json.dumps({"tool_name": "Bash", "tool_input": {"command": ""}})),
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
# Section 12: complex/compound commands
# ============================================================
test("safe pipeline", "ls -la | grep .env | wc -l", None)
test("safe conditional", '[[ -v API_KEY ]] && echo "set" || echo "not set"', None)
test("multiline safe", "cd /app && ls", None)

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
