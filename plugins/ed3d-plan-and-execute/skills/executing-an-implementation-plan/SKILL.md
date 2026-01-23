---
name: executing-an-implementation-plan
description: Use when executing implementation plans with independent tasks in the current session - dispatches fresh subagent for each task, reviews once per phase, loads phases just-in-time to minimize context usage
---

# Executing an Implementation Plan

Execute plan phase-by-phase, loading each phase just-in-time to minimize context usage.

**Core principle:** Read one phase → execute all tasks → review → move to next phase. Never load all phases upfront.

**REQUIRED SKILL:** `requesting-code-review` - The review loop (dispatch, fix, re-review until zero issues)

## Overview

**When NOT to use:**
- No implementation plan exists yet (use writing-implementation-plans first)
- Plan needs revision (brainstorm first)

## MANDATORY: Human Transparency

**The human cannot see what subagents return. You are their window into the work.**

After EVERY subagent completes (task-implementor, bug-fixer, code-reviewer), you MUST:

1. **Print the subagent's full response** to the user before taking any other action
2. **Do not summarize or paraphrase** - show them what the subagent actually said
3. **Include all details:** test counts, issue lists, commit hashes, error messages

**Before dispatching any subagent:**
- Briefly explain (2-3 sentences) what you're asking the agent to do
- State which phase this covers

**Why this matters:** When you silently process subagent output without showing the user, they lose visibility into their own codebase. They can't catch errors, learn from the process, or intervene when needed. Transparency is not optional.

**Red flag:** If you find yourself thinking "I'll just move on to the next step" without printing the subagent's response, STOP. Print it first.

## REQUIRED: Implementation Plan Path

**DO NOT GUESS.** If the user has not provided a path to an implementation plan directory, you MUST ask for it.

Use AskUserQuestion:
```
Question: "Which implementation plan should I execute?"
Options:
  - [list any plan directories you find in docs/implementation-plans/]
  - "Let me provide the path"
```

If `docs/implementation-plans/` doesn't exist or is empty, ask the user to provide the path directly.

**Never assume, infer, or guess which plan to execute.** The user must explicitly tell you.

## The Process

### 1. Discover Phases

**DO NOT read the full phase files yet.** List them and read only the header and task markers.

```bash
# List phase files
ls [plan-directory]/phase_*.md

# For each file, get the header (first 10 lines include title and Goal)
head -10 [plan-directory]/phase_01.md

# Get task/subcomponent structure without reading full content
grep -E "START_TASK_|START_SUBCOMPONENT_" [plan-directory]/phase_01.md
```

The header includes the title (`# [Phase Title]`) and `**Goal:**` line. Extract the title for the task entry.

The grep output shows the task structure, e.g.:
```
<!-- START_TASK_1 -->
<!-- START_TASK_2 -->
<!-- START_SUBCOMPONENT_A (tasks 3-5) -->
<!-- START_TASK_3 -->
<!-- START_TASK_4 -->
<!-- START_TASK_5 -->
```

Examples of headers you might see:
- `# Document Infrastructure Implementation Plan` — Phase 1 implied
- `# Phase 4: Link Resolution` — Phase number explicit

### 2. Create Phase-Level Task List

Use TaskCreate to create **three task entries per phase** (or TodoWrite in older Claude Code versions). Include the title from the header:

```
- [ ] Phase 1a: Read /absolute/path/to/phase_01.md — Document Infrastructure Implementation Plan
- [ ] Phase 1b: Execute tasks
- [ ] Phase 1c: Code review
- [ ] Phase 2a: Read /absolute/path/to/phase_02.md — API Integration
- [ ] Phase 2b: Execute tasks
- [ ] Phase 2c: Code review
...
```

**Why absolute paths in task entries:** After compaction, context may be summarized. The absolute path in the task entry ensures you always know exactly which file to read.

**Why include the title:** Gives visibility into what each phase covers without loading full content.

### 3. Execute Each Phase

For each phase, follow this cycle:

#### 3a. Read Phase File (just-in-time)

Mark "Phase Na: Read [path]" as in_progress.

Read ONLY that phase file now. Extract:
- List of tasks in this phase
- Working directory
- Any phase-specific context

Mark "Phase Na: Read" as complete.

#### 3b. Execute All Tasks

Mark "Phase Nb: Execute tasks" as in_progress.

**Before dispatching, verify test coverage for functionality tasks:**

If a functionality task (code that does something) has no tests specified:
1. Check if a subsequent task in the same phase provides tests
2. If no tests exist anywhere for this functionality → **STOP**
3. This is a plan gap. Surface to user: "Task N implements [functionality] but no corresponding tests exist in the plan. This needs tests before implementation."

Do NOT implement functionality without tests. Missing tests = plan gap, not something to skip.

**Execute all tasks in sequence.** For each task, dispatch `task-implementor-fast` with the phase file path:

```
<invoke name="Task">
<parameter name="subagent_type">ed3d-plan-and-execute:task-implementor-fast</parameter>
<parameter name="description">Implementing Phase X, Task Y: [description]</parameter>
<parameter name="prompt">
  Implement Task N from the phase file.

  Phase file: [absolute path to phase file]
  Task number: N

  Read the phase file and implement Task N (look for `<!-- START_TASK_N -->`).

  Your job is to:
  1. Read the phase file to understand context
  2. Apply all relevant skills, such as (if available) ed3d-house-style:coding-effectively
  3. Implement exactly what Task N specifies
  4. Verify with tests/build/lint
  5. Commit your work
  6. Report back with evidence

  Work from: [directory]

  Provide complete report per your agent instructions.
</parameter>
</invoke>
```

**For subcomponents** (grouped tasks), dispatch once for all tasks in the subcomponent:

```
<invoke name="Task">
<parameter name="subagent_type">ed3d-plan-and-execute:task-implementor-fast</parameter>
<parameter name="description">Implementing Phase X, Subcomponent A (Tasks 3-5): [description]</parameter>
<parameter name="prompt">
  Implement Subcomponent A (Tasks 3, 4, 5) from the phase file.

  Phase file: [absolute path to phase file]
  Tasks: 3, 4, 5 (look for `<!-- START_SUBCOMPONENT_A -->`)

  Read the phase file and implement all tasks in this subcomponent.

  Your job is to:
  1. Read the phase file to understand context
  2. Apply all relevant skills, such as (if available) ed3d-house-style:coding-effectively
  3. Implement all tasks in sequence
  4. Verify with tests/build/lint after completing all tasks
  5. Commit your work (one commit per task, or logical commits)
  6. Report back with evidence for each task

  Work from: [directory]

  Provide complete report covering all tasks.
</parameter>
</invoke>
```

**Print each task-implementor's response** before moving to the next task.

**No code review between tasks.** Execute all tasks in the phase first.

After all tasks complete, mark "Phase Nb: Execute tasks" as complete.

#### 3c. Code Review for Phase

Mark "Phase Nc: Code review" as in_progress.

**MANDATORY:** Use the `requesting-code-review` skill for the review loop.

**Context to provide:**
- WHAT_WAS_IMPLEMENTED: Summary of all tasks in this phase
- PLAN_OR_REQUIREMENTS: All tasks from this phase
- BASE_SHA: commit before phase started
- HEAD_SHA: current commit

**If code reviewer returns a context limit error:**

The phase changed too much for a single review. Chunk the review:

1. Identify the midpoint of tasks in the phase
2. Run code review for first half of tasks (commits for tasks 1 through N/2)
3. Fix any issues found
4. Run code review for second half of tasks (commits for tasks N/2+1 through N)
5. Fix any issues found

**When issues are found**, dispatch `task-bug-fixer` with the phase file:

```
<invoke name="Task">
<parameter name="subagent_type">ed3d-plan-and-execute:task-bug-fixer</parameter>
<parameter name="description">Fixing review issues for Phase X</parameter>
<parameter name="prompt">
  Fix issues from code review for Phase X.

  Phase file: [absolute path to phase file]

  Code reviewer found these issues:
  [list all issues - Critical, Important, and Minor]

  Read the phase file to understand the tasks and context.

  Your job is to:
  1. Understand root cause of each issue
  2. Apply fixes systematically (Critical → Important → Minor)
  3. Verify with tests/build/lint
  4. Commit your fixes
  5. Report back with evidence

  Work from: [directory]

  Fix ALL issues — including every Minor issue. The goal is ZERO issues on re-review.
  Minor issues are not optional. Do not skip them.
</parameter>
</invoke>
```

After bug-fixer completes, re-review per the `requesting-code-review` skill. Continue loop until zero issues.

**Plan execution policy (stricter than general code review):**
- ALL issues must be fixed (Critical, Important, AND Minor)
- Ignore APPROVED/BLOCKED status - count issues only
- **Three-strike rule:** If same issues persist after three review cycles, stop and ask human for help

**Minor issues are NOT optional.** Do not rationalize skipping them with "they're just style issues" or "we can fix those later." The reviewer flagged them for a reason. Fix every single one.

**Exit condition:** Zero issues in all categories — including Minor.

Mark "Phase Nc: Code review" as complete.

#### 3d. Move to Next Phase

Proceed to the next phase's "Read" step. Repeat 3a-3c for each phase.

### 4. Update Project Context

After all phases complete, invoke the `ed3d-extending-claude:project-claude-librarian` subagent (when available) to review changes and update CLAUDE.md files if needed.

```
<invoke name="Task">
<parameter name="subagent_type">ed3d-extending-claude:project-claude-librarian</parameter>
<parameter name="description">Updating project context after implementation</parameter>
<parameter name="prompt">
  Review what changed during this implementation and update CLAUDE.md files if contracts or structure changed.

  Base commit: <commit SHA at start of first phase>
  Current HEAD: <current commit>
  Working directory: <directory>

  Follow the ed3d-extending-claude:maintaining-project-context skill to:
  1. Diff against base to see what changed
  2. Identify contract/API/structure changes
  3. Update affected CLAUDE.md files
  4. Commit documentation updates

  Report back with what was updated (or that no updates were needed).
</parameter>
</invoke>
```

**If librarian reports updates:** Review the changes, then proceed to final review.
**If librarian reports no updates needed:** Proceed to final review.
**If librarian subagent is unavailable:** skip this entire step. Say aloud that you're skipping it because the `ed3d-extending-claude` plugin is not available.

### 5. Final Review

After all phases complete, use the `requesting-code-review` skill for final review:
- Reviews entire implementation
- Checks all plan requirements met
- Validates overall architecture

Continue the review loop until zero issues remain.

### 6. Complete Development

After final review passes:

- Provide a report to the human operator
  - For each phase:
    - How many tasks were implemented
    - How many review cycles were needed
    - Any compromises made (there should be NO compromises, but if any were made). Examples:
      - "I couldn't run the integration tests, so I continued on"
      - "I couldn't generate the client because the dev environment was down"
      - Note that these are PARTIAL FAILURE CASES and explain to the user what the user must do now.
    - Were any code-review issues left outstanding at any point?

- Activate the `finishing-a-development-branch` skill. DO NOT activate it before this point.

## Example Workflow

```
You: I'm using the `executing-an-implementation-plan` skill.

[Discover phases: phase_01.md, phase_02.md, phase_03.md]
[Read first 3 lines of each to get titles]

[Create tasks with TaskCreate:]
- [ ] Phase 1a: Read /path/to/phase_01.md — Project Setup
- [ ] Phase 1b: Execute tasks
- [ ] Phase 1c: Code review
- [ ] Phase 2a: Read /path/to/phase_02.md — Token Service
- [ ] Phase 2b: Execute tasks
- [ ] Phase 2c: Code review
- [ ] Phase 3a: Read /path/to/phase_03.md — API Middleware
- [ ] Phase 3b: Execute tasks
- [ ] Phase 3c: Code review

--- Phase 1 ---

[Mark 1a in_progress, read phase_01.md]
→ Contains 2 tasks: project setup, config files

[Mark 1a complete, 1b in_progress]

[Dispatch task-implementor-fast for Task 1]
→ Created package.json, tsconfig.json.

[Dispatch task-implementor-fast for Task 2]
→ Created config files. Build succeeds.

[Mark 1b complete, 1c in_progress]

[Use requesting-code-review skill for phase 1]
→ Zero issues.

[Mark 1c complete]

--- Phase 2 ---

[Mark 2a in_progress, read phase_02.md]
→ Contains 3 tasks: types, service, tests

[Mark 2a complete, 2b in_progress]

[Execute all 3 tasks...]

[Mark 2b complete, 2c in_progress]

[Use requesting-code-review skill for phase 2]
→ Important: 1, Minor: 1
→ Dispatch bug-fixer, re-review
→ Zero issues.

[Mark 2c complete]

--- Phase 3 ---

[Similar pattern...]

--- Finalize ---

[Invoke project-claude-librarian subagent]
→ Updated CLAUDE.md.

[Use requesting-code-review skill for final review]
→ All requirements met.

[Transitioning to finishing-a-development-branch]
```

## Common Rationalizations - STOP

| Excuse | Reality |
|--------|---------|
| "I'll read all phases upfront to understand the full picture" | No. Read one phase at a time. Context limits are real. |
| "I'll skip the read step, I remember what's in the file" | No. Always read just-in-time. Context may have been compacted. |
| "I'll review after each task to catch issues early" | No. Review once per phase. Task-level review wastes context. |
| "Context error on review, I'll skip the review" | No. Chunk the review into halves. Never skip review. |
| "Minor issues can wait" | No. Fix ALL issues including Minor. |
