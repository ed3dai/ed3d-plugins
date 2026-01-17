---
name: executing-an-implementation-plan
description: Use when executing implementation plans with independent tasks in the current session - dispatches fresh subagent for each task with code review between tasks, enabling fast iteration with quality gates
---

# Executing an Implementation Plan

Execute plan by dispatching fresh subagent per task, with code review after each.

**Core principle:** Fresh subagent per task + review between tasks = high quality, fast iteration

**REQUIRED SKILL:** `requesting-code-review` - The review loop (dispatch, fix, re-review until zero issues) 

## Overview

**When NOT to use:**
- No implementation plan exists yet (use writing-implementation-plans first)
- Plan needs revision (brainstorm first)

### Grouping Tasks by Subcomponent

**Mental model:** If a set of tasks together completes a logical subcomponent, group them into a single task-implementor dispatch and review them together.

A "subcomponent" is a coherent unit of functionality:
- A service class with its tests
- A set of related utility functions
- An API endpoint with its handler, validation, and tests
- A data model with its repository and tests

**Decision heuristic:**

| Situation | Action |
|-----------|--------|
| Tasks 1, 2, 3 together create a complete service with tests | Group all three |
| Task 1 creates a type, Task 2 uses it, Task 3 tests it | Group all three |
| Task 1 is infrastructure, Task 2 is unrelated feature code | Don't group |
| Task 1 is complex (multiple files, significant logic) | Don't group, execute alone |
| Tasks span different phases | Never group across phases |

**Rules for grouping:**
- Only group tasks within the same phase (never skip phases)
- Tasks must complete a coherent subcomponent together
- Announce what you're grouping and why before dispatching
- Code review covers all grouped tasks together
- TodoWrite marks all grouped tasks complete together after review passes

**When NOT to group:**
- Tasks in different phases
- Tasks touching unrelated parts of the codebase
- Complex tasks that each need focused attention (let them have their own review cycle)
- When in doubt, don't group - overhead of extra reviews is low

## MANDATORY: Human Transparency

**The human cannot see what subagents return. You are their window into the work.**

After EVERY subagent completes (task-implementor, bug-fixer, code-reviewer), you MUST:

1. **Print the subagent's full response** to the user before taking any other action
2. **Do not summarize or paraphrase** - show them what the subagent actually said
3. **Include all details:** test counts, issue lists, commit hashes, error messages

**Before dispatching any subagent:**
- Briefly explain (2-3 sentences) what you're asking the agent to do
- State which task/phase this covers

**Why this matters:** When you silently process subagent output without showing the user, they lose visibility into their own codebase. They can't catch errors, learn from the process, or intervene when needed. Transparency is not optional.

**Red flag:** If you find yourself thinking "I'll just move on to the next step" without printing the subagent's response, STOP. Print it first.

## REQUIRED: Implementation Plan Path

**DO NOT GUESS.** If the user has not provided a path to an implementation plan phase file, you MUST ask for it.

Use AskUserQuestion:
```
Question: "Which implementation plan phase should I execute?"
Options:
  - [list any phase directories you find in docs/implementation-plans/*/]
  - "Let me provide the path"
```

If `docs/implementation-plans/` doesn't exist or is empty, ask the user to provide the path directly.

If the human provides you a single phase document, e.g. `phase-01.md`, check that directory for more and ask with `AskUserQuestion` if they want that phase executed or all phases executed.

**Never assume, infer, or guess which plan to execute.** The user must explicitly tell you.

## The Process

### 1. Load Plan

Read the plan file provided by the user. Create TodoWrite with all tasks.

### 2. Execute Task(s) with Subagent

**Before dispatching, verify test coverage for functionality tasks:**

If a functionality task (code that does something) has no tests specified:
1. Check if a subsequent task in the same subcomponent provides tests
2. If no tests exist anywhere for this functionality → **STOP**
3. This is a plan gap. Surface to user: "Task N implements [functionality] but no corresponding tests exist in the plan. This needs tests before implementation."

Do NOT implement functionality without tests. Missing tests = plan gap, not something to skip.

For each task or task group, dispatch `task-implementor-fast`.

**Single task dispatch:**

```
<invoke name="Task">
<parameter name="subagent_type">ed3d-ed3d-plan-and-execute:task-implementor-fast</parameter>
<parameter name="description">Implementing Phase X, Task Y: [description]</parameter>
<parameter name="prompt">
  Implement Task N from [plan-file].

  Read that task specification completely. Your job is to:
  1. Apply all relevant skills, such as (if available) ed3d-house-style:coding-effectively
  2. Implement exactly what the task specifies
  3. Verify with tests/build/lint
  4. Commit your work
  5. Report back with evidence

  Work from: [directory]

  Provide complete report per your agent instructions.
</parameter>
</invoke>
```

**Grouped tasks dispatch (completing a subcomponent):**

```
<invoke name="Task">
<parameter name="subagent_type">ed3d-ed3d-plan-and-execute:task-implementor-fast</parameter>
<parameter name="description">Implementing Phase X, Tasks Y-Z: [subcomponent name]</parameter>
<parameter name="prompt">
  Implement Tasks N, N+1, N+2 from [plan-file].

  These tasks together complete the [subcomponent name]. Read all task
  specifications. Your job is to:
  1. Implement all tasks in sequence
  1. Apply all relevant skills, such as (if available) ed3d-house-style:coding-effectively
  3. Verify with tests/build/lint after completing all tasks
  4. Commit your work (one commit per task, or logical commits)
  5. Report back with evidence for each task

  Work from: [directory]

  Provide complete report covering all tasks.
</parameter>
</invoke>
```

**Task-implementor-fast reports back** with implementation summary and verification evidence, which you as the orchestrating agent should always write out for the user before continuing to mandatory code review.

### 3. Review and Fix Loop

**MANDATORY:** Use the `requesting-code-review` skill for the complete review loop.

That skill handles:
- Initial review dispatch
- Re-review with prior issues tracking
- Timeout handling and retries

**Context to provide:**
- WHAT_WAS_IMPLEMENTED: from task-implementor's report
- PLAN_OR_REQUIREMENTS: Task N from [plan-file]
- BASE_SHA: commit before task (or first task if grouped)
- HEAD_SHA: current commit

**When issues are found**, dispatch `task-bug-fixer`:

```
<invoke name="Task">
<parameter name="subagent_type">ed3d-plan-and-execute:task-bug-fixer</parameter>
<parameter name="description">Fixing review issues for [task/section]</parameter>
<parameter name="prompt">
  Fix issues from code review for Task N from [plan-file].

  Code reviewer found these issues:
  [list all issues - Critical, Important, and Minor]

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

**After review passes:** Mark task complete, proceed to next task.

### 4. Mark Complete, Next Task

- Mark task as completed in TodoWrite
- Move to next task
- Repeat steps 2-4

### 4b. Update Project Context

After all tasks complete, before final review, invoke the `ed3d-extending-claude:project-claude-librarian` subagent (when available) to review changes and update CLAUDE.md files if needed.

```
<invoke name="Task">
<parameter name="subagent_type">ed3d-extending-claude:project-claude-librarian</parameter>
<parameter name="description">Updating project context after Phase X</parameter>
<parameter name="prompt">
  Review what changed during this implementation phase and update CLAUDE.md files if contracts or structure changed.

  Base commit: <commit SHA at phase start>
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

After all tasks complete, use the `requesting-code-review` skill for final review:
- Reviews entire implementation
- Checks all plan requirements met
- Validates overall architecture

Continue the review loop until zero issues remain.

### 6. Complete Development

After final review passes:

- Provide a report to the human operator
  - For each task:
    - How many passes of task-implementor were necessary
    - Any compromises made (there should be NO compromises, but if any were made). Examples:
      - "I couldn't run the integration tests, so I continued on"
      - "I couldn't generate the client because the dev environment was down"
      - Note that these are PARTIAL FAILURE CASES and explain to the user what the user must do now.
    - Were any code-review issues left outstanding at any point?

- Activate the `finishing-a-development-branch` skill. DO NOT activate it before this point.

## Example Workflow

```
You: I'm using the `executing-an-implementation-plan` skill.

[Load plan, create TodoWrite with 5 tasks]

--- Task 1: Project setup ---

[Dispatch task-implementor-fast]
→ Created package.json, tsconfig.json. Build succeeds.

[Use requesting-code-review skill]
→ Zero issues. Mark Task 1 complete.

--- Tasks 2-4: Token service (grouped) ---

You: "Tasks 2-4 complete the token service. Grouping them."

[Dispatch task-implementor-fast with all three]
→ Types, service, tests. 8/8 passing.

[Use requesting-code-review skill]
→ Important: 1, Minor: 1
→ Dispatch bug-fixer, re-review
→ Zero issues. Mark Tasks 2-4 complete.

--- Task 5: API middleware ---

[Dispatch task-implementor-fast]
→ Auth middleware, tests pass.

[Use requesting-code-review skill]
→ Zero issues. Mark Task 5 complete.

--- Finalize ---

[Invoke project-claude-librarian subagent]
→ Updated CLAUDE.md.

[Use requesting-code-review skill for final review]
→ All requirements met.

[Transitioning to finishing-a-development-branch]
```
