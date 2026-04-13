---
description: Execute implementation plan task-by-task with subagents
argument-hint: [absolute-plan-dir] [absolute-working-dir]
---

# Execute Implementation Plan

**Implementation plan directory:** `$1`
**Working directory:** `$2`

This execution workflow uses:
- Just-in-time phase loading (reads one phase at a time)
- Task/subcomponent markers for structure
- Per-phase code review (not per-task)

## Before Starting

Both arguments MUST be absolute paths. Verify they exist:

1. Verify the working directory exists and is a git repository:
   ```bash
   test -d "$2" && git -C "$2" rev-parse --git-dir
   ```

2. Verify the plan directory exists and contains phase files:
   ```bash
   ls "$1"/phase_*.md
   ```

If either verification fails, stop and report the error to the user.

## Execute

1. **Change working directory** to `$2` before any other work
2. **Engage the skill:** Use your Skill tool to invoke `executing-an-implementation-plan`
3. **When the skill asks for a plan path:** The user has already provided it: `$1`. Do not ask again.

The skill should execute all phases in the plan directory using the just-in-time loading workflow. Follow it exactly as written.
