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

**Announce:** "I'm using the linear-workflow skill to update Linear issue status."

**Trigger:** The PostToolUse hook has injected context indicating a PR or merge event AND `.linear-issue` exists at the project root.

The injected context includes:
- The Linear issue ID (e.g., `ENG-123`)
- The event type: `pr-created` or `merged`

### Step 1: Verify .linear-issue exists

Read `.linear-issue` from the project root to confirm the issue ID.

If `.linear-issue` does not exist:
- Do nothing. Announce: "No active Linear issue found (.linear-issue is absent). Skipping Linear update."
- Exit finish mode.

### Step 2: Get the PR or commit link

Before updating Linear, gather the relevant link to include in the comment:

**For `pr-created` event:**
Run `gh pr view --json url -q .url` to get the PR URL. If this fails, use `gh pr view --json number -q .number` and construct the URL manually, or use the URL from the hook context if available.

**For `merged` event:**
Run `git log -1 --format="%H"` to get the merge commit hash. Use this as the reference if no PR URL is available. Prefer the PR URL if a PR was associated with the merge — try `gh pr view --json url -q .url` first.

### Step 3: Use writing-for-linear to compose the comment

Use your Skill tool to invoke the `writing-for-linear` skill.

Pass the following context to the skill:
- Writing context: status-change comment
- Event: `pr-created` or `merged` (as appropriate)
- Issue ID: the value from `.linear-issue`
- Link: the PR URL or commit hash from Step 2

The skill will return a composed comment. Use that comment in Step 4.

### Step 4: Update Linear issue status

Use the available Linear MCP tools to update the issue workflow state:

**For `pr-created` event:** Set status to "In Review"
**For `merged` event:** Set status to "Done"

If you are unsure which state name to use, list the available workflow states for the team first, then select the closest match.

### Step 5: Post the comment to Linear

Use the available Linear MCP tools to post the comment composed in Step 3 to the Linear issue.

Look for a tool that:
- Accepts an issue identifier or ID
- Accepts a comment body string

Include the PR URL or commit hash in the comment body (the `writing-for-linear` skill will have included it if invoked correctly, but verify).

### Step 6: Clean up on merge

**Only for `merged` event:**

Delete `.linear-issue` from the project root using the Bash tool:

```bash
rm .linear-issue
```

Announce: "Linear issue [ISSUE-ID] is now Done. Comment posted. .linear-issue deleted."

**For `pr-created` event:** Do NOT delete `.linear-issue`. It must persist for the eventual merge event.

Announce: "Linear issue [ISSUE-ID] is now In Review. PR comment posted."
