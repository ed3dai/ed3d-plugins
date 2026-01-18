---
name: starting-an-implementation-plan
description: Use when beginning implementation from a design plan - orchestrates branch creation, detailed planning, and hands off to execution with all necessary context
---

# Starting an Implementation Plan

## Overview

Orchestrate the transition from design document to executable implementation through planning and execution handoff.

**Core principle:** Branch -> Plan -> Execute. Isolate work, create detailed tasks, hand off to execution.

**Announce at start:** "I'm using the starting-an-implementation-plan skill to create the implementation plan from your design."

## REQUIRED: Design Plan Path

**DO NOT GUESS.** If the user has not provided a path to a design plan, you MUST ask for it.

Use AskUserQuestion:
```
Question: "Which design plan should I create an implementation plan for?"
Options:
  - [list any design plans you find in docs/design-plans/]
  - "Let me provide the path"
```

If `docs/design-plans/` doesn't exist or is empty, ask the user to provide the path directly.

**Never assume, infer, or guess which design plan to use.** The user must explicitly tell you.

## The Process

This skill has three phases:

1. **Branch Setup:** Select and create branch for implementation
2. **Planning:** Create detailed implementation plan
3. **Execution Handoff:** Direct user to execute the plan

### Phase 1: Branch Setup

Before planning, set up the branch and workspace for implementation work.

Extract a friendly name from the design plan filename (e.g., `oauth2-service-auth` from `2025-01-18-oauth2-service-auth.md`).

**Step 1: Ask about worktree**

**REQUIRED: Use AskUserQuestion tool**

Ask:
```
Question: "Do you want to use a git worktree for this implementation?"
Options:
  - "Yes - create worktree" (isolated workspace in .worktrees/[friendly-name])
  - "No - work in current directory" (standard branch workflow)
```

**Step 2: Set up workspace based on choice**

**If user chooses "Yes - create worktree":**

1. **REQUIRED SUB-SKILL:** Use ed3d-plan-and-execute:using-git-worktrees
2. **CONDITIONAL SKILLS:** Activate any project-specific git worktree skills if they exist
3. Announce: "I'm using the using-git-worktrees skill to create an isolated workspace."
4. Ask user which branch to use for the worktree:
   ```
   Question: "Which branch should I use for this worktree?"
   Options:
     - "[friendly-name]" (e.g., oauth2-service-auth)
     - "$(whoami)/[friendly-name]" (e.g., ed/oauth2-service-auth)
   ```
5. Create worktree:
   - Default location (unless directed otherwise): `$repoRoot/.worktrees/[friendly-name]`
   - Branch from main/master
   - Follow using-git-worktrees skill for safety verification and setup
6. Change to worktree directory
7. Announce: "Worktree created at `.worktrees/[friendly-name]` on branch `[branch-name]`"

**If user chooses "No - work in current directory":**

1. Ask user which branch to use:
   ```
   Question: "Which branch should I use for this implementation?"
   Options:
     - "Use current branch" (stay on current branch, no branch creation)
     - "[friendly-name]" (e.g., oauth2-service-auth)
     - "$(whoami)/[friendly-name]" (e.g., ed/oauth2-service-auth)
   ```
2. **If "Use current branch":** Continue with current branch (no git commands)
3. **If branch name provided:**
   - Determine main branch name: Check if `main` or `master` exists
   - Create new branch from main/master: `git checkout -b [branch-name] origin/[main-or-master]`
   - Verify branch created successfully
   - Announce: "Created and checked out branch `[branch-name]` from `origin/[main-or-master]`"
4. **If branch creation fails:** Report error to user and ask if they want to use current branch instead

**THEN proceed to Phase 2.**

### Phase 2: Planning

**REQUIRED SUB-SKILL:** Use ed3d-plan-and-execute:writing-implementation-plans

Announce: "I'm using the writing-implementation-plans skill to create the detailed implementation plan."

The writing-implementation-plans skill will:
- Verify scope (<=8 phases from design plan)
- Verify codebase state with investigator
- Create phase-by-phase implementation tasks
- Validate each phase with user before proceeding
- Write implementation plan to `docs/implementation-plans/`

**Output:** Complete implementation plan written to files, on appropriate branch.

### Phase 3: Execution Handoff

After planning is complete, hand off to execution.

**Do NOT invoke execute-plan directly.** The user needs to /clear context first.

**Step 1: Capture and verify absolute paths**

Before outputting the handoff instructions, you MUST run these commands to get real, verified paths:

```bash
# Get absolute path to current working tree root
git rev-parse --show-toplevel
```

Capture this output as `WORKING_ROOT`.

Then construct and verify the implementation plan path exists:

```bash
# Verify implementation plan directory exists
# Replace YYYY-MM-DD-feature-name with the actual plan directory name
ls -d "${WORKING_ROOT}/docs/implementation-plans/YYYY-MM-DD-feature-name"
```

**Both commands must succeed.** If the plan directory doesn't exist, something went wrong during planning — investigate before proceeding.

**Step 2: Provide copy-paste instructions with verified absolute paths**

Use the actual paths you captured and verified in Step 1. Example output:

```
Implementation plan complete!

Ready to execute? This requires fresh context to work effectively.

**IMPORTANT: Copy the command below BEFORE running /clear (it will erase this conversation).**

(1) Copy this command now:

/execute-implementation-plan @/Users/ed/project/.worktrees/oauth2-feature/docs/implementation-plans/2025-01-17-oauth2-feature/ /Users/ed/project/.worktrees/oauth2-feature/

(2) Clear your context:

/clear

(3) Paste and run the copied command.

The execute-implementation-plan command will implement the plan task-by-task with code review between tasks.
```

**Use the real paths from Step 1, not placeholders.** The example above shows the format — substitute your actual verified paths.

**Why absolute paths:** After /clear, Claude Code returns to the original session directory (often the repo root, not the worktree). Absolute paths ensure execution happens in the correct directory regardless of where /clear returns.

**Why /clear instead of continuing:**
- Execution needs fresh context to work effectively
- Long conversations accumulate context that degrades quality
- /clear gives the execution phase a clean slate

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Invoking execute-implementation-plan directly | Provide copy-paste instructions instead |
| Not warning user to copy command before /clear | Always warn: "Copy this BEFORE running /clear" |
| Using relative paths in handoff command | Run bash commands to get absolute paths, verify they exist |
| Outputting placeholder paths like `[WORKING_ROOT]` | Output real paths from `git rev-parse --show-toplevel` and `ls -d` |
| Not verifying plan directory exists | Always `ls -d` the full plan path before outputting command |
| Passing phase_01.md instead of directory | Pass the directory so all phases execute |
| Forgetting to mention /clear | Always tell user to /clear before execute |

## Integration with Workflow

This skill sits between design and execution:

```
Design Plan (in docs/design-plans/)
  -> User runs /start-implementation-plan with design path

Starting Implementation Plan (this skill)
  -> Phase 1: Branch Setup
    -> Ask if user wants worktree
    -> If yes: invoke using-git-worktrees, create at .worktrees/[friendly-name]
    -> If no: ask which branch, create branch from main/master if needed

  -> Phase 2: Planning
    -> Invoke writing-implementation-plans
    -> Detailed task planning
    -> Phase-by-phase validation
    -> Write to docs/implementation-plans/

  -> Phase 3: Execution Handoff
    -> Run `git rev-parse --show-toplevel` to get absolute working root
    -> Verify plan directory exists with `ls -d`
    -> Output command with verified absolute paths (tell user to copy first)
    -> Provide /clear command
    -> User copies command, clears, then pastes

Execute Implementation Plan (next step)
  -> Reads implementation plan
  -> Implements task-by-task
  -> Code review between tasks
```

**Purpose:** Bridge design and execution with appropriate branch isolation and context management.
