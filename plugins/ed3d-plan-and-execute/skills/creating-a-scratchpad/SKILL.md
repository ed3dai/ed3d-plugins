---
name: creating-a-scratchpad
description: Use when any skill or agent needs a session-isolated temp directory - provides a sandbox-safe fallback chain for creating scratchpad directories that works in both sandboxed and non-sandboxed Claude Code environments
user-invocable: false
---

# Creating a Scratchpad Directory

Create a session-isolated temp directory that works in sandboxed and non-sandboxed Claude Code environments.

## The Helper

```bash
_make_scratchpad() {
  local name="$1"
  local session_id
  session_id=$(printf '%04x%04x' $RANDOM $RANDOM)

  # 1. mktemp -d: uses $TMPDIR automatically when set (sandbox-safe)
  mktemp -d 2>/dev/null ||
  # 2. $TMPDIR explicitly
  { [ -n "$TMPDIR" ] && mkdir -p "${TMPDIR}/${name}-${session_id}" 2>/dev/null && echo "${TMPDIR}/${name}-${session_id}"; } ||
  # 3. /tmp/claude-$UID (UID-based sandbox path)
  { mkdir -p "/tmp/claude-${UID:-1000}/${name}-${session_id}" 2>/dev/null && echo "/tmp/claude-${UID:-1000}/${name}-${session_id}"; } ||
  # 4. Last resort
  { mkdir -p "/tmp/claude-1000/${name}-${session_id}" && echo "/tmp/claude-1000/${name}-${session_id}"; }
}
```

## Usage

Pass a descriptive name prefix. The caller is responsible for the prefix — choose something that identifies the workflow:

```bash
# In writing-implementation-plans:
SCRATCHPAD_DIR=$(_make_scratchpad "plan-$(date +%Y-%m-%d)-${slug}")

# In executing-an-implementation-plan:
SCRATCHPAD_DIR=$(_make_scratchpad "exec-${slug}")

# In remote-code-researcher:
REPO_DIR=$(_make_scratchpad "repo-${slug}")/repo
```

## Why the Fallback Chain

Claude Code sandbox mode restricts writes to specific `/tmp/claude-*` paths. The fallback chain tries the most portable option first:

1. **`mktemp -d`** — most portable; automatically uses `$TMPDIR` when set, which sandbox mode sets to the allowed directory
2. **`$TMPDIR`** — explicit fallback when `mktemp` fails but `$TMPDIR` is available
3. **`/tmp/claude-$UID`** — sandbox allows writes here; `$UID` matches the running user
4. **`/tmp/claude-1000`** — hardcoded last resort for UID 1000 environments

## Session Isolation

The `session_id` suffix (e.g., `a7f3b2`) in fallback paths (legs 2–4) ensures isolation between parallel sessions with the same name prefix and prevents collisions on retry attempts. `mktemp` (leg 1) handles this intrinsically via its random suffix.
