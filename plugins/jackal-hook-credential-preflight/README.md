# jackal-hook-credential-preflight

Warns before an agent dispatch when the harness's own AWS SSO credentials cannot survive it.

## Why

When Claude Code runs on Bedrock, every agent in the fleet authenticates through **one**
cached SSO token. When that token lapses, every in-flight agent dies within the same
second — including the orchestrator, which therefore cannot run its own stall-recovery
logic. In one observed case the subagent died at `07:40:37` and its parent at `07:40:38`.

An investigation of ~20 dead subagents (2026-07-17 → 07-31) found this to be the dominant
failure mode. Notably, **no code was actually lost** in any traced incident — worktree
files survive process death and recovery succeeded every time. The real cost is redundant
re-verification, near-miss two-writer hazards during recovery, and forced human re-auth.

The pre-existing pre-flight in `jackal-plan-and-execute/skills/execute/SKILL.md` guards
the *downstream project's* AWS credentials and explicitly says it does not apply to the
harness itself, so it never fired for this.

## What it checks

One `PreToolUse` hook on `Agent|Task`, reading `~/.aws` only — no STS calls, no network,
and no token values are read or logged.

| Condition | Behavior |
|---|---|
| Token expired | Warn |
| No `refreshToken` **and** remaining lifetime < declared dispatch duration | Warn |
| No `refreshToken` **and** remaining lifetime < 30m (duration unknown) | Warn |
| Client registration expiring within 3 days, or expired | Warn |
| Refreshable token, any remaining lifetime | Silent |

The `refreshToken` distinction is the crux. AWS's legacy SSO config format (inline
`sso_start_url` per profile) does **not** issue refresh tokens — AWS docs: *"Automated
token refresh isn't supported using the legacy non-refreshable configuration."* With the
`[sso-session]` format the CLI renews silently, so a token with minutes left is fine. On
the legacy format the same token guarantees a dead dispatch.

Dispatch duration is read from the `EXPECT: ... within <n>m` line that Jackal dispatch
prompts already carry, so the warning fires on *runway vs. need*, not on validity alone.

## Why it warns instead of denying

Only the operator can run an interactive `aws sso login`. Denying a dispatch would block
real work over a state the agent cannot fix, so the default is advisory — and the message
says plainly that the operator, not the agent, has to act.

To make it fail closed instead:

```bash
export JACKAL_PREFLIGHT_BLOCK=1
```

## Configuration

| Variable | Effect |
|---|---|
| `JACKAL_PREFLIGHT_DISABLE=1` | Silence the check entirely |
| `JACKAL_PREFLIGHT_BLOCK=1` | Deny rather than warn |
| `JACKAL_SSO_SESSION=<name>` | Override which `sso-session` to inspect |

The hook is inert unless `CLAUDE_CODE_USE_BEDROCK=1`, and stays silent when there is no
SSO cache at all (non-SSO setups), when timestamps are unparseable, or on any internal
error — an advisory check that breaks a dispatch would be worse than one that misses a
warning.

## How the token is located

The SSO cache filename is `sha1(<sso-session name>).json` (or `sha1(<start URL>).json` on
the legacy format). Bedrock profiles are usually assumed roles, so the hook walks
`source_profile` hops — `DevOps_EDRC-Dev` → `AWS_DevOps_EDRC-Dev` → `HCG-SSO-DevOps` —
until it finds the `sso_session`, because only the last hop names it. Without that walk it
would find no session and stay silent in exactly the configuration it exists for.

## Tests

```bash
python3 hooks/test-check-credential-preflight.py
```

23 tests using real temp `HOME` trees with real `~/.aws/config` and cache files — no
mocks — so filename derivation and chain-walking are exercised as they run in production.
