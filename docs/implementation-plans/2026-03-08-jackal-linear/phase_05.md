# jackal-linear Implementation Plan — Phase 5

**Goal:** Close the loop — extend `linear-workflow` with finish mode to update Linear status, post comments, and clean up on merge.

**Architecture:** Finish mode is added to the existing `linear-workflow/SKILL.md` by replacing the placeholder section. The skill reads `.linear-issue` for the issue ID, determines the event type (pr-created or merged) from context injected by the PostToolUse hook, then uses Linear MCP tools to update status and post a comment (composed via `writing-for-linear`, which exists from Phase 4). On merge, it additionally deletes `.linear-issue`.

**Tech Stack:** Markdown skill file extension, Linear MCP tools (status update + comment creation)

**Scope:** Phase 5 of 5

**Codebase verified:** 2026-03-08

---

## Acceptance Criteria Coverage

This phase implements and tests:

### jackal-linear.AC4: `linear-workflow` finish mode closes the issue correctly
- **jackal-linear.AC4.1 Success:** On PR created event, issue status is set to In Review and a PR comment is posted to Linear
- **jackal-linear.AC4.2 Success:** On merge event, issue status is set to Done, a completion comment is posted, and `.linear-issue` is deleted
- **jackal-linear.AC4.3 Success:** Comments posted to Linear include a link to the PR or commit
- **jackal-linear.AC4.4 Failure:** Finish mode does nothing if `.linear-issue` is absent

Also completes (now that all components exist):

### jackal-linear.AC1: Plugin is installable and registers its components
- **jackal-linear.AC1.3 Success:** `commands/start-from-linear.md`, `skills/linear-workflow/SKILL.md`, and `skills/writing-for-linear/SKILL.md` exist

---

<!-- START_TASK_1 -->
### Task 1: Extend linear-workflow SKILL.md with finish mode

**Files:**
- Modify: `plugins/jackal-linear/skills/linear-workflow/SKILL.md`

The existing SKILL.md has a placeholder `## Finish Mode` section at the bottom (created in Phase 2). Replace that entire placeholder section with the full finish mode implementation below.

**Step 1: Read the current SKILL.md**

Read `plugins/jackal-linear/skills/linear-workflow/SKILL.md` to locate the placeholder finish mode section:

```
## Finish Mode

Finish mode is documented in Phase 5. This section will be extended then.

**Placeholder:** If finish mode is triggered before Phase 5 is implemented, respond:
"Finish mode is not yet implemented. Please update the Linear issue manually."
```

**Step 2: Replace the placeholder with the full finish mode section**

Replace the placeholder section (from `## Finish Mode` to the end of the file) with the following:

```markdown
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
```

**Step 3: Verify the edit**

Run: `grep -n "## Finish Mode" plugins/jackal-linear/skills/linear-workflow/SKILL.md`
Expected: Line number printed (confirms section exists)

Run: `grep -c "Placeholder" plugins/jackal-linear/skills/linear-workflow/SKILL.md`
Expected: `0` (placeholder text is gone)

**Step 4: Commit**

```bash
git add plugins/jackal-linear/skills/linear-workflow/SKILL.md
git commit -m "feat(jackal-linear): add linear-workflow finish mode (PR and merge handling)"
```
<!-- END_TASK_1 -->

<!-- START_TASK_2 -->
### Task 2: Add final CHANGELOG entry

**Files:**
- Modify: `CHANGELOG.md` (update the entry added in Phase 1)

In Phase 1, a minimal CHANGELOG entry was added for the plugin scaffolding. Now that all components exist, update it to the full entry.

**Step 1: Find the existing Phase 1 changelog entry**

The entry from Phase 1 reads:

```markdown
## [jackal-linear] 1.0.0

Plugin scaffolding and Linear MCP server registration.

**New:**
- `plugins/jackal-linear` plugin directory with `.claude-plugin/plugin.json` registering the Linear MCP server via `mcp-remote`
```

**Step 2: Replace it with the complete entry**

Replace the minimal entry with:

```markdown
## [jackal-linear] 1.0.0

Initial release of the jackal-linear plugin.

**New:**
- `/start-from-linear [ISSUE-ID]` command: fetches Linear issue, sets it to In Progress, seeds the `starting-a-design-plan` workflow with issue context
- `linear-workflow` skill: start mode (issue fetch + In Progress status) and finish mode (In Review on PR, Done on merge)
- `writing-for-linear` skill: content standards for Linear comments, status-change updates, and issue descriptions
- PostToolUse hook: detects `gh pr create` and `git merge` commands, injects Linear reminder when `.linear-issue` is present
- Linear MCP server registered via `mcp-remote` pointing to `https://mcp.linear.app/mcp` (OAuth 2.1)
```

**Step 3: Verify**

Run: `grep -A 15 "\[jackal-linear\] 1.0.0" CHANGELOG.md | head -16`
Expected: The full entry shown with all **New:** items listed

**Step 4: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: update jackal-linear 1.0.0 changelog with complete feature list"
```
<!-- END_TASK_2 -->
