---
description: Execute an implementation plan or run continuous backlog execution
argument-hint: [plan-directory] [working-directory]
---

# Execute

**Plan directory:** `$1` (optional — if omitted, enters Backlog mode)
**Working directory:** `$2` (optional — defaults to current)

Invoke the `execute` skill.

- With arguments: executes the specified implementation plan
- Without arguments: enters continuous backlog mode (reads TODO.md, dispatches until stuck)
