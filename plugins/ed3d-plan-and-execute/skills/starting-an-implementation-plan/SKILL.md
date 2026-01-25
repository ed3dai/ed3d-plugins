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

This skill has three steps:

1. **Branch Setup:** Select and create branch for implementation
2. **Planning:** Create detailed implementation plan
3. **Execution Handoff:** Direct user to execute the plan

**Step 0: Create orchestration task tracker**

Use TaskCreate to track the orchestration steps:

```markdown
- [ ] Branch setup
- [ ] Create implementation plan
- [ ] Re-read starting-an-implementation-plan skill (restore context)
- [ ] Execution handoff
```

The "Create implementation plan" task wraps the granular tasks created by writing-implementation-plans. The "Re-read skill" step ensures context is restored after potential compaction before handoff.

### Branch Setup

Mark "Branch setup" task as in_progress.

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

Mark "Branch setup" task as completed. **THEN proceed to Planning.**

### Planning

Mark "Create implementation plan" task as in_progress.

**REQUIRED SUB-SKILL:** Use ed3d-plan-and-execute:writing-implementation-plans

Announce: "I'm using the writing-implementation-plans skill to create the detailed implementation plan."

The writing-implementation-plans skill will:
- Verify scope (<=8 phases from design plan)
- Verify codebase state with investigator
- Create phase-by-phase implementation tasks
- Validate each phase with user before proceeding
- Write implementation plan to `docs/implementation-plans/`

**Output:** Complete implementation plan written to files, on appropriate branch.

Mark "Create implementation plan" task as completed.

### Restore Context (Before Handoff)

Mark "Re-read starting-an-implementation-plan skill (restore context)" task as in_progress.

**CRITICAL: Re-read this skill before proceeding to handoff.**

After potentially long planning work (especially if context compaction occurred), re-read this skill file to ensure you have accurate instructions for the execution handoff:

```bash
# Re-read this skill to restore context
cat /path/to/plugins/ed3d-plan-and-execute/skills/starting-an-implementation-plan/SKILL.md
```

Or use the Read tool on the skill file path.

**Why this matters:** After compaction, you may have lost details about the handoff process. Re-reading ensures you provide correct absolute paths and instructions.

Mark "Re-read starting-an-implementation-plan skill" task as completed.

### Execution Handoff

Mark "Execution handoff" task as in_progress.

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

/ed3d-plan-and-execute:execute-implementation-plan /Users/ed/project/.worktrees/oauth2-feature/docs/implementation-plans/2025-01-17-oauth2-feature/ /Users/ed/project/.worktrees/oauth2-feature/

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

Mark "Execution handoff" task as completed.

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
| Skipping "Re-read skill" step before handoff | Always re-read this skill to restore context post-compaction |
| Not creating orchestration tasks at start | Create Branch setup, Planning, Re-read, Handoff tasks in Step 0 |

## Integration with Workflow

This skill sits between design and execution:

```
Design Plan (in docs/design-plans/)
  -> User runs /start-implementation-plan with design path

Starting Implementation Plan (this skill)
  -> Step 0: Create orchestration tasks
    -> [ ] Branch setup
    -> [ ] Create implementation plan
    -> [ ] Re-read skill (restore context)
    -> [ ] Execution handoff

  -> Branch Setup [tracked task]
    -> Ask if user wants worktree
    -> If yes: invoke using-git-worktrees
    -> If no: ask which branch, create if needed

  -> Planning [tracked task wrapping granular tasks]
    -> Invoke writing-implementation-plans
    -> Creates granular tasks per phase (NA, NB, NC, ND)
    -> Creates Finalization task (code review, fix ALL issues)
    -> Write to docs/implementation-plans/

  -> Restore Context [tracked task]
    -> Re-read this skill file
    -> Ensures handoff instructions are accurate post-compaction

  -> Execution Handoff [tracked task]
    -> Run `git rev-parse --show-toplevel` for absolute paths
    -> Verify plan directory exists
    -> Output command with verified absolute paths
    -> Provide /clear command

Execute Implementation Plan (next step)
  -> Reads implementation plan
  -> Implements task-by-task
  -> Code review between tasks
```

**Purpose:** Bridge design and execution with appropriate branch isolation, granular task tracking that survives compaction, and context restoration.
