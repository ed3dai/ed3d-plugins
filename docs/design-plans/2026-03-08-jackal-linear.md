# jackal-linear plugin design

## Summary

The `jackal-linear` plugin integrates Linear issue tracking into the `ed3d-plan-and-execute` workflow, enabling developers to start design sessions directly from Linear issues and automatically sync progress back to Linear throughout the development lifecycle. The plugin introduces a `/start-from-linear` command that fetches an issue, transitions it to In Progress, and seeds the design planning phase with the issue's context. As work progresses through implementation and code review, a PostToolUse hook detects key git events (PR creation and merges) and prompts Claude to update the Linear issue status, post progress comments, and close the issue upon completion.

The implementation centers on three components: a command file that bridges Linear with the existing design workflow, a `linear-workflow` skill that handles both session initialization and status synchronization, and a `writing-for-linear` skill that ensures Linear comments and updates follow consistent formatting standards. Context persistence across Claude Code's mandatory phase boundaries is achieved via a `.linear-issue` file at the project root that survives session clears. The Linear MCP server (accessed via OAuth 2.1 through `mcp-remote`) provides the tools for reading issues, updating statuses, and posting comments.

## Definition of Done

- A new `jackal-linear` plugin containing: a Linear MCP server config, a `/start-from-linear [ISSUE-ID]` command, a `linear-workflow` skill (procedural), and a `writing-for-linear` skill (content quality)
- `/start-from-linear` fetches the Linear issue, sets it to In Progress, records the issue ID in the design document header, and seeds the design plan context with the issue title and description
- A PostToolUse hook on Bash detects `gh pr create` and `git merge` events and prompts Claude to update Linear status, post a comment, and close/complete the issue
- `writing-for-linear` covers how to write Linear comments, status updates, and issue descriptions

## Acceptance Criteria

### jackal-linear.AC1: Plugin is installable and registers its components
- **jackal-linear.AC1.1 Success:** `plugins/jackal-linear/.claude-plugin/plugin.json` is valid JSON with `mcpServers` key pointing to `mcp-remote https://mcp.linear.app/mcp`
- **jackal-linear.AC1.2 Success:** Marketplace entry in `.claude-plugin/marketplace.json` is present with matching version
- **jackal-linear.AC1.3 Success:** `commands/start-from-linear.md`, `skills/linear-workflow/SKILL.md`, and `skills/writing-for-linear/SKILL.md` exist
- **jackal-linear.AC1.4 Failure:** Marketplace entry version does not match `plugin.json` version — must be kept in sync

### jackal-linear.AC2: `/start-from-linear` initiates a Linear-linked design session
- **jackal-linear.AC2.1 Success:** Running `/start-from-linear ENG-123` fetches the issue title and description via Linear MCP
- **jackal-linear.AC2.2 Success:** The Linear issue is set to In Progress after the command runs
- **jackal-linear.AC2.3 Success:** `.linear-issue` file is written to project root containing the issue ID
- **jackal-linear.AC2.4 Success:** `starting-a-design-plan` receives the issue title as the design goal context
- **jackal-linear.AC2.5 Failure:** Running with a non-existent issue ID surfaces an error rather than silently continuing

### jackal-linear.AC3: PostToolUse hook prompts status updates on PR and merge events
- **jackal-linear.AC3.1 Success:** After `gh pr create`, hook injects Linear reminder into Claude's context when `.linear-issue` is present
- **jackal-linear.AC3.2 Success:** After `git merge` or `gh pr merge`, hook injects Linear reminder when `.linear-issue` is present
- **jackal-linear.AC3.3 Success:** Hook injects nothing when `.linear-issue` is absent (non-Linear session)
- **jackal-linear.AC3.4 Success:** Unrelated Bash commands (e.g., `ls`, `npm test`) do not trigger the hook
- **jackal-linear.AC3.5 Failure:** Hook script exit code does not block or fail the Bash command that triggered it

### jackal-linear.AC4: `linear-workflow` finish mode closes the issue correctly
- **jackal-linear.AC4.1 Success:** On PR created event, issue status is set to In Review and a PR comment is posted to Linear
- **jackal-linear.AC4.2 Success:** On merge event, issue status is set to Done, a completion comment is posted, and `.linear-issue` is deleted
- **jackal-linear.AC4.3 Success:** Comments posted to Linear include a link to the PR or commit
- **jackal-linear.AC4.4 Failure:** Finish mode does nothing if `.linear-issue` is absent

### jackal-linear.AC5: `writing-for-linear` produces well-formed Linear content
- **jackal-linear.AC5.1 Success:** Skill covers issue descriptions (structured, outcome-focused)
- **jackal-linear.AC5.2 Success:** Skill covers status-change comments (brief, includes PR link, states what changed)
- **jackal-linear.AC5.3 Success:** Skill covers inline comments (conversational, for questions or blockers)

## Glossary

- **Linear**: Third-party issue tracking and project management tool used for software development workflows
- **MCP (Model Context Protocol)**: Standard protocol for connecting Claude to external data sources and APIs; MCP servers expose tools that Claude can invoke
- **mcp-remote**: MCP client that connects to remote MCP servers over HTTPS (vs. local `npx` processes); requires OAuth authentication
- **OAuth 2.1**: Authentication protocol that allows Claude to access the user's Linear account without storing credentials
- **PostToolUse hook**: Extension point that runs after a tool executes; can inject additional context into Claude's next turn based on the tool's output
- **ed3d-plan-and-execute**: Existing plugin providing a three-phase workflow (design -> implementation -> execution) with mandatory `/clear` boundaries between phases
- **starting-a-design-plan**: Existing skill from `ed3d-plan-and-execute` that guides creation of design documents; serves as the handoff point from `/start-from-linear`
- **additionalContext**: Hook output field that injects text into Claude's context on the next turn, used here to prompt Linear status updates
- **`.linear-issue` file**: Gitignored file at project root storing the active Linear issue ID; persists across `/clear` boundaries
- **Skill tool**: Claude Code mechanism for invoking skills (reusable instruction sets); skills are markdown files with YAML frontmatter
- **YAML frontmatter**: Metadata block at the top of markdown files (delimited by `---`) containing structured configuration like `name`, `description`, etc.

## Architecture

`jackal-linear` bridges Linear issue tracking with the `ed3d-plan-and-execute` workflow. Two integration points:

**Entry point — `/start-from-linear [ISSUE-ID]`**: Fetches the issue via MCP, sets it to In Progress, writes the ID to `.linear-issue` at the project root, and hands off to `starting-a-design-plan` with the issue title and description seeded as design context.

**Exit points — PostToolUse hook on Bash**: Detects `gh pr create` and `git merge` / `gh pr merge` in executed commands. When `.linear-issue` exists, the hook injects an `additionalContext` reminder. Claude then invokes `linear-workflow` (finish mode) to update status, compose and post a comment via `writing-for-linear`, and on merge: close the issue and delete `.linear-issue`.

**Context persistence**: `.linear-issue` at the project root (gitignored) stores the active issue ID. This file survives the mandatory `/clear` between design, implementation, and execution phases.

**Linear MCP server**: Registered in `plugin.json` via `mcp-remote`, connecting to `https://mcp.linear.app/mcp` (OAuth 2.1). Exposes tools for issue read, status update, and comment creation.

### Key contracts

`linear-workflow` skill trigger interface:

```
# Start mode (via /start-from-linear)
Arguments: ISSUE-ID (e.g. ENG-123)
Reads: Linear issue via MCP
Writes: .linear-issue file, starts-a-design-plan with seeded context

# Finish mode (via hook-injected reminder)
Reads: .linear-issue, event type (pr-created | merged)
Writes: Linear status update, Linear comment, deletes .linear-issue on merge
```

PostToolUse hook output shape (on match):

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Linear issue [ID] is active. Use linear-workflow to update its status."
  }
}
```

## Existing Patterns

Investigation found the following patterns this design follows:

**Command files** — `ed3d-plan-and-execute/commands/start-design-plan.md`: markdown with YAML frontmatter, body delegates to a skill via the Skill tool. `start-from-linear.md` follows the same structure.

**Hook structure** — `ed3d-hook-claudemd-reminder/hooks/`: `hooks.json` declares `PostToolUse` matcher on `Bash`; Python script reads stdin JSON (`tool_input.command`), writes `additionalContext` JSON to stdout, exits 0. `linear-status-hook.py` follows the same pattern.

**MCP server registration** — `ed3d-playwright`: `mcpServers` key in `plugin.json` (and optional `.mcp.json` in plugin root). `jackal-linear` uses `mcp-remote` in place of `npx` for the OAuth-protected remote server.

**Skill files** — all existing skills: markdown `SKILL.md` with YAML frontmatter (`name`, `description`, `user-invocable`).

**Marketplace entry** — all plugins: entry in `.claude-plugin/marketplace.json` with `name`, `version`, `source`, `author`.

## Implementation Phases

<!-- START_PHASE_1 -->
### Phase 1: Plugin scaffolding

**Goal:** Create the plugin directory structure and register it in the marketplace.

**Components:**
- `plugins/jackal-linear/.claude-plugin/plugin.json` — plugin metadata and Linear MCP server config (`mcp-remote` pointing to `https://mcp.linear.app/mcp`)
- `plugins/jackal-linear/.mcp.json` — same MCP server config for local override
- `plugins/jackal-linear/README.md` — installation notes including OAuth auth step
- Marketplace entry in `.claude-plugin/marketplace.json`

**Dependencies:** None

**Done when:** Plugin directory exists, marketplace entry is present, `plugin.json` is valid JSON with `mcpServers` key
<!-- END_PHASE_1 -->

<!-- START_PHASE_2 -->
### Phase 2: `/start-from-linear` command and `linear-workflow` start mode

**Goal:** Enable starting a design session from a Linear issue.

**Components:**
- `plugins/jackal-linear/commands/start-from-linear.md` — command file that invokes `linear-workflow` skill with the ISSUE-ID argument
- `plugins/jackal-linear/skills/linear-workflow/SKILL.md` — start mode: fetch issue via MCP, set status to In Progress, write `.linear-issue`, invoke `starting-a-design-plan` with issue title/description as design context

**Dependencies:** Phase 1 (plugin registered, Linear MCP available)

**Done when:** Running `/start-from-linear ENG-123` fetches the issue, sets it In Progress, writes `.linear-issue`, and transitions to design planning flow
<!-- END_PHASE_2 -->

<!-- START_PHASE_3 -->
### Phase 3: PostToolUse hook

**Goal:** Automatically prompt Linear status updates after PR and merge events.

**Components:**
- `plugins/jackal-linear/hooks/hooks.json` — PostToolUse matcher on Bash
- `plugins/jackal-linear/hooks/linear-status-hook.py` — reads `tool_input.command`, matches `gh pr create` and `git merge` / `gh pr merge` patterns, injects reminder if `.linear-issue` exists

**Dependencies:** Phase 1 (plugin scaffolding)

**Done when:** After `gh pr create`, Claude receives the Linear reminder context when `.linear-issue` is present; reminder is absent when `.linear-issue` does not exist
<!-- END_PHASE_3 -->

<!-- START_PHASE_4 -->
### Phase 4: `linear-workflow` finish mode

**Goal:** Close the loop — update Linear status, post a comment, and clean up on merge.

**Components:**
- Extend `plugins/jackal-linear/skills/linear-workflow/SKILL.md` with finish mode:
  - PR created event: set status to In Review, invoke `writing-for-linear` for PR comment, post comment via MCP
  - Merge event: set status to Done, invoke `writing-for-linear` for completion comment, post comment, delete `.linear-issue`

**Dependencies:** Phase 2 (start mode sets `.linear-issue`), Phase 3 (hook triggers finish mode)

**Done when:** After merge, Linear issue is set to Done, a completion comment is posted, and `.linear-issue` is deleted
<!-- END_PHASE_4 -->

<!-- START_PHASE_5 -->
### Phase 5: `writing-for-linear` skill

**Goal:** Define content standards for Linear-facing text.

**Components:**
- `plugins/jackal-linear/skills/writing-for-linear/SKILL.md` — guidance for three writing contexts:
  - Issue descriptions: structured, outcome-focused, includes acceptance criteria
  - Status-change comments (PR created / merged): brief, links PR/commit, states what changed
  - Inline comments: conversational, for questions or blockers mid-work

**Dependencies:** Phase 4 (skill is invoked from finish mode)

**Done when:** `writing-for-linear` skill is present and invocable; generated comments follow the style guidelines
<!-- END_PHASE_5 -->

## Additional Considerations

**`.linear-issue` gitignore**: The file must be added to `.gitignore` at the project root during installation. The README should include this step.

**OAuth authentication**: Linear MCP uses OAuth 2.1. On first use, `mcp-remote` will open a browser prompt. The README should document this expected behavior.

**Hook safety**: The hook is a no-op when `.linear-issue` is absent, so installing it globally does not affect non-Linear sessions.
