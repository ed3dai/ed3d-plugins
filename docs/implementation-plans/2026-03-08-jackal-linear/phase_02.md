# jackal-linear Implementation Plan — Phase 2

**Goal:** Enable starting a design session from a Linear issue via `/start-from-linear [ISSUE-ID]`.

**Architecture:** A command file delegates to the `linear-workflow` skill (start mode). The skill fetches the issue via Linear MCP tools, sets it to In Progress, writes the issue ID to `.linear-issue` at the project root, then hands off to `starting-a-design-plan` with the issue title and description as seeded context. The skill guides Claude to use whatever Linear MCP tools are available at runtime rather than hard-coding tool names (the official Linear MCP tool schema is not publicly documented).

**Tech Stack:** Markdown skill files (YAML frontmatter), Linear MCP server (via mcp-remote from Phase 1)

**Scope:** Phase 2 of 5

**Codebase verified:** 2026-03-08

---

## Acceptance Criteria Coverage

This phase implements and tests:

### jackal-linear.AC2: `/start-from-linear` initiates a Linear-linked design session
- **jackal-linear.AC2.1 Success:** Running `/start-from-linear ENG-123` fetches the issue title and description via Linear MCP
- **jackal-linear.AC2.2 Success:** The Linear issue is set to In Progress after the command runs
- **jackal-linear.AC2.3 Success:** `.linear-issue` file is written to project root containing the issue ID
- **jackal-linear.AC2.4 Success:** `starting-a-design-plan` receives the issue title as the design goal context
- **jackal-linear.AC2.5 Failure:** Running with a non-existent issue ID surfaces an error rather than silently continuing

---

<!-- START_SUBCOMPONENT_A (tasks 1-2) -->
<!-- START_TASK_1 -->
### Task 1: Create the `/start-from-linear` command file

**Files:**
- Create: `plugins/jackal-linear/commands/start-from-linear.md`

**Step 1: Create the commands directory and command file**

```bash
mkdir -p plugins/jackal-linear/commands
```

Create `plugins/jackal-linear/commands/start-from-linear.md` with the following content:

```markdown
---
description: Start a design session from a Linear issue. Fetches the issue, sets it to In Progress, and seeds the design planning workflow with the issue context.
argument-hint: ISSUE-ID (e.g. ENG-123)
---

Use your Skill tool to engage the `linear-workflow` skill. Follow it exactly as written.

ARGUMENTS: $ARGUMENTS
```

**Step 2: Verify file exists and content is correct**

Run: `cat plugins/jackal-linear/commands/start-from-linear.md`
Expected: File content shown with YAML frontmatter and skill invocation instruction

**Step 3: Commit**

```bash
git add plugins/jackal-linear/commands/start-from-linear.md
git commit -m "feat(jackal-linear): add start-from-linear command"
```
<!-- END_TASK_1 -->

<!-- START_TASK_2 -->
### Task 2: Create the `linear-workflow` skill (start mode)

**Files:**
- Create: `plugins/jackal-linear/skills/linear-workflow/SKILL.md`

**Step 1: Create the skills directory**

```bash
mkdir -p plugins/jackal-linear/skills/linear-workflow
```

**Step 2: Create SKILL.md**

Create `plugins/jackal-linear/skills/linear-workflow/SKILL.md` with the following content:

```markdown
---
name: linear-workflow
description: Use when starting a design session from a Linear issue (start mode) or when updating Linear status after PR creation or merge (finish mode). Start mode fetches the issue, sets it to In Progress, and seeds design planning. Finish mode updates status, posts comments, and cleans up on merge.
user-invocable: false
---

# linear-workflow

## Overview

This skill has two modes:

- **Start mode**: Triggered by `/start-from-linear [ISSUE-ID]`. Fetches the Linear issue, sets status to In Progress, writes the issue ID to `.linear-issue`, and hands off to `starting-a-design-plan` with the issue context seeded.
- **Finish mode**: Triggered by the PostToolUse hook after `gh pr create` or `git merge`. Reads `.linear-issue`, updates status, posts a comment, and on merge: closes the issue and deletes `.linear-issue`.

Determine mode from context: if the skill receives an ISSUE-ID argument, use start mode. If the context mentions a PR or merge event and `.linear-issue` exists, use finish mode.

---

## Start Mode

**Announce:** "I'm using the linear-workflow skill to start a Linear-linked design session."

**Trigger:** Arguments contain an issue identifier (e.g., `ENG-123`).

### Step 1: Validate the issue ID format

The ISSUE-ID argument should match the pattern `[A-Z]+-[0-9]+` (e.g., `ENG-123`, `PROJ-456`).

If the argument is missing or does not match this pattern:
- Stop immediately
- Tell the user: "Please provide a valid Linear issue ID (e.g., ENG-123). Usage: /start-from-linear ENG-123"
- Do not proceed

### Step 2: Fetch the issue via Linear MCP

Use the available Linear MCP tools to retrieve the issue by its identifier.

Look for a tool that:
- Accepts an issue identifier or ID as input
- Returns the issue's `title`, `description`, and current `state`/`status`

If the tool returns no result, an error, or indicates the issue does not exist:
- Stop immediately
- Tell the user: "Issue [ISSUE-ID] was not found in Linear. Please verify the issue ID and try again."
- Do not write `.linear-issue` or proceed further

### Step 3: Set issue status to In Progress

Use the available Linear MCP tools to update the issue's workflow state to "In Progress".

Look for a tool that:
- Accepts an issue identifier or ID
- Accepts a target workflow state (by name or ID)

If you are unsure which state value to use for "In Progress", first use a tool to list available workflow states for the issue's team, then select the state whose name most closely matches "In Progress".

If the update fails, report the error to the user and stop. Do not write `.linear-issue`.

### Step 4: Write `.linear-issue`

Write the issue ID (e.g., `ENG-123`) to a file named `.linear-issue` at the project root (the directory where Claude Code is running).

The file should contain only the issue ID. A trailing newline is acceptable:

```
ENG-123
```

Use the Write tool to create this file. If the project root is not clear, use the result of `git rev-parse --show-toplevel` as the project root.

### Step 5: Hand off to starting-a-design-plan

Use your Skill tool to invoke the `starting-a-design-plan` skill.

Before invoking it, prepare the context by announcing:

"Starting design session for Linear issue [ISSUE-ID]: [issue title]

Issue description:
[issue description]

I'll now begin the design planning process with this as the goal."

Then invoke `starting-a-design-plan`. The issue title serves as the initial design goal. The issue description provides the requirements context.

---

## Finish Mode

Finish mode is documented in Phase 5. This section will be extended then.

**Placeholder:** If finish mode is triggered before Phase 5 is implemented, respond:
"Finish mode is not yet implemented. Please update the Linear issue manually."
```

**Step 3: Verify file exists**

Run: `cat plugins/jackal-linear/skills/linear-workflow/SKILL.md`
Expected: File content shown with YAML frontmatter and skill body

**Step 4: Create `.gitignore` at repo root (if not present)**

The `.linear-issue` file must be gitignored. There is currently no `.gitignore` at the repo root — create one:

Run: `ls /Users/jgreaney/Documents/code/jackal-plugins/.gitignore 2>/dev/null || echo "MISSING"`

If the output is `MISSING`, create `/Users/jgreaney/Documents/code/jackal-plugins/.gitignore` with:

```
.linear-issue
```

If `.gitignore` already exists, add `.linear-issue` on a new line if not already present.

**Step 5: Commit**

```bash
git add plugins/jackal-linear/skills/linear-workflow/SKILL.md
git add .gitignore
git commit -m "feat(jackal-linear): add linear-workflow skill (start mode) and .gitignore"
```
<!-- END_TASK_2 -->
<!-- END_SUBCOMPONENT_A -->
