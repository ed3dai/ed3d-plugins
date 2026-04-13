# jackal-linear

> **DEPRECATED** — 2026-04-13. Plugin is no longer maintained.

Last verified: 2026-03-08

## Purpose

Bridges Linear issue tracking and the ed3d-plan-and-execute workflow so developers can start design sessions from Linear issues and have status updates synced back automatically.

## Contracts

- **Exposes**: `/start-from-linear [ISSUE-ID]` command, `linear-workflow` skill (start + finish modes), `writing-for-linear` skill
- **Guarantees**: `.linear-issue` file is created on start, deleted only on merge. Linear status transitions follow In Progress -> In Review -> Done.
- **Expects**: Linear MCP server available (configured in `.mcp.json`). `ed3d-plan-and-execute` plugin installed. `gh` CLI available for PR detection.

## Dependencies

- **Uses**: Linear MCP server (`mcp-remote` via `npx`), `ed3d-plan-and-execute` (`starting-a-design-plan` skill), `gh` CLI
- **Used by**: End users via `/start-from-linear` command; PostToolUse hook fires automatically on Bash tool use
- **Boundary**: Does not import from or depend on other plugins in this repo

## Key Decisions

- `.linear-issue` file at project root: Simple state marker readable by both the hook (Python) and skills. Deleted on merge to signal completion.
- PostToolUse hook in Python: Parses `tool_input` JSON from stdin, pattern-matches on `gh pr create` and `git merge` commands. Injects a system-reminder prompting Claude to invoke `linear-workflow` finish mode.
- Two-skill split (`linear-workflow` + `writing-for-linear`): Separates orchestration logic from content standards so writing rules can be reused independently.

## Invariants

- `.linear-issue` contains only the issue identifier (e.g., `ENG-123`)
- The hook never calls Linear directly -- it only injects a reminder; the skill does the actual MCP calls
- `writing-for-linear` composes comment text but never posts it; `linear-workflow` posts via MCP

## Key Files

- `commands/start-from-linear.md` - Slash command entry point
- `skills/linear-workflow/SKILL.md` - Orchestration skill (start + finish modes)
- `skills/writing-for-linear/SKILL.md` - Content standards for Linear text
- `hooks/hooks.json` - PostToolUse hook registration
- `hooks/linear-status-hook.py` - Python hook that detects PR/merge events
- `.mcp.json` - Linear MCP server configuration

## Gotchas

- First use triggers a browser OAuth prompt via `mcp-remote` for Linear authorization
- The hook reads `tool_input` from stdin as JSON; it silently exits if the input is not a Bash command containing `gh pr create` or `git merge`
- `.linear-issue` must be added to the target project's `.gitignore` (not this repo's)
