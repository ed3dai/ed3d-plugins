# jackal-linear Test Requirements

## Overview

The jackal-linear plugin consists of four artifact types, each requiring a different verification approach:

1. **JSON config files** (`plugin.json`, `.mcp.json`, `hooks.json`, `marketplace.json`) -- verifiable by automated structural checks (valid JSON, required keys present, version sync).
2. **Python hook script** (`linear-status-hook.py`) -- directly testable with automated tests by feeding JSON to stdin and asserting on stdout/exit code.
3. **Markdown skill files** (`linear-workflow/SKILL.md`, `writing-for-linear/SKILL.md`) -- behavioral instructions for Claude that cannot be unit tested. Require human verification by invoking the skill and observing Claude's behavior.
4. **Markdown command file** (`start-from-linear.md`) -- same as skill files: requires human invocation to verify.

The test strategy is: automate everything that can be checked structurally or executed as a script, and define explicit human verification protocols for the behavioral/AI-instruction artifacts.

---

## Automated Tests

### AC1.1: `plugin.json` is valid JSON with `mcpServers` key pointing to Linear MCP

- **Type:** manual-script
- **Verifies:** `plugin.json` parses as valid JSON, contains `mcpServers` key, and the server config references `mcp.linear.app/mcp`
- **Command:**
  ```bash
  python3 -c "
  import json, sys
  p = json.load(open('plugins/jackal-linear/.claude-plugin/plugin.json'))
  assert 'mcpServers' in p, 'Missing mcpServers key'
  servers = p['mcpServers']
  assert any('mcp.linear.app/mcp' in ' '.join(v.get('args', [])) for v in servers.values()), 'No server pointing to mcp.linear.app/mcp'
  print('AC1.1 PASS')
  "
  ```

### AC1.2: Marketplace entry is present with matching version

- **Type:** manual-script
- **Verifies:** `marketplace.json` contains a `jackal-linear` entry whose version matches `plugin.json`
- **Command:**
  ```bash
  python3 -c "
  import json
  plugin = json.load(open('plugins/jackal-linear/.claude-plugin/plugin.json'))
  marketplace = json.load(open('.claude-plugin/marketplace.json'))
  entry = next((p for p in marketplace['plugins'] if p['name'] == 'jackal-linear'), None)
  assert entry is not None, 'jackal-linear not found in marketplace.json'
  assert plugin['version'] == entry['version'], f'Version mismatch: plugin.json={plugin[\"version\"]}, marketplace={entry[\"version\"]}'
  print('AC1.2 PASS')
  "
  ```

### AC1.3: All component files exist

- **Type:** manual-script
- **Verifies:** `commands/start-from-linear.md`, `skills/linear-workflow/SKILL.md`, and `skills/writing-for-linear/SKILL.md` all exist under `plugins/jackal-linear/`
- **Command:**
  ```bash
  python3 -c "
  import os
  base = 'plugins/jackal-linear'
  files = [
      'commands/start-from-linear.md',
      'skills/linear-workflow/SKILL.md',
      'skills/writing-for-linear/SKILL.md',
  ]
  for f in files:
      path = os.path.join(base, f)
      assert os.path.isfile(path), f'Missing: {path}'
  print('AC1.3 PASS')
  "
  ```

### AC1.4 (Failure): Marketplace version does not match plugin.json version

- **Type:** manual-script
- **Verifies:** This is the inverse of AC1.2 -- the AC1.2 check already catches this. If AC1.2 passes, AC1.4 is not triggered.
- **Command:** Same as AC1.2 (assertion failure = AC1.4 failure condition detected).

### AC3.1: Hook injects Linear reminder after `gh pr create` when `.linear-issue` is present

- **Type:** unit (stdin/stdout script test)
- **Verifies:** Given a `gh pr create` command and a `.linear-issue` file, the hook outputs JSON with `additionalContext` containing the issue ID and `pr-created` event type
- **Command:**
  ```bash
  TMP_DIR=$(mktemp -d)
  mkdir "$TMP_DIR/.git"
  echo "ENG-123" > "$TMP_DIR/.linear-issue"
  OUTPUT=$(cd "$TMP_DIR" && echo '{"tool_name":"Bash","tool_input":{"command":"gh pr create --title test"}}' | python3 "$(pwd)/plugins/jackal-linear/hooks/linear-status-hook.py")
  EXIT_CODE=$?
  rm -rf "$TMP_DIR"
  python3 -c "
  import json, sys
  output = json.loads('''$OUTPUT''')
  ctx = output['hookSpecificOutput']['additionalContext']
  assert 'ENG-123' in ctx, 'Issue ID not in context'
  assert 'pr-created' in ctx, 'Event type not in context'
  print('AC3.1 PASS')
  " || echo "AC3.1 FAIL"
  [ "$EXIT_CODE" -eq 0 ] || echo "AC3.1 FAIL: non-zero exit code"
  ```

### AC3.2: Hook injects Linear reminder after `git merge` when `.linear-issue` is present

- **Type:** unit (stdin/stdout script test)
- **Verifies:** Given a `git merge` command and a `.linear-issue` file, the hook outputs JSON with `additionalContext` containing the issue ID and `merged` event type. Also verifies `gh pr merge` variant.
- **Command:**
  ```bash
  # Test git merge
  TMP_DIR=$(mktemp -d)
  mkdir "$TMP_DIR/.git"
  echo "ENG-456" > "$TMP_DIR/.linear-issue"
  OUTPUT=$(cd "$TMP_DIR" && echo '{"tool_name":"Bash","tool_input":{"command":"git merge origin/feature-branch"}}' | python3 "$(pwd)/plugins/jackal-linear/hooks/linear-status-hook.py")
  rm -rf "$TMP_DIR"
  python3 -c "
  import json
  output = json.loads('''$OUTPUT''')
  ctx = output['hookSpecificOutput']['additionalContext']
  assert 'ENG-456' in ctx and 'merged' in ctx
  print('AC3.2a (git merge) PASS')
  "

  # Test gh pr merge
  TMP_DIR=$(mktemp -d)
  mkdir "$TMP_DIR/.git"
  echo "ENG-789" > "$TMP_DIR/.linear-issue"
  OUTPUT=$(cd "$TMP_DIR" && echo '{"tool_name":"Bash","tool_input":{"command":"gh pr merge 42 --squash"}}' | python3 "$(pwd)/plugins/jackal-linear/hooks/linear-status-hook.py")
  rm -rf "$TMP_DIR"
  python3 -c "
  import json
  output = json.loads('''$OUTPUT''')
  ctx = output['hookSpecificOutput']['additionalContext']
  assert 'ENG-789' in ctx and 'merged' in ctx
  print('AC3.2b (gh pr merge) PASS')
  "
  ```

### AC3.3: Hook injects nothing when `.linear-issue` is absent

- **Type:** unit (stdin/stdout script test)
- **Verifies:** Given a `gh pr create` command but no `.linear-issue` file, the hook produces no stdout output and exits 0
- **Command:**
  ```bash
  TMP_DIR=$(mktemp -d)
  mkdir "$TMP_DIR/.git"
  # No .linear-issue file
  OUTPUT=$(cd "$TMP_DIR" && echo '{"tool_name":"Bash","tool_input":{"command":"gh pr create --title test"}}' | python3 "$(pwd)/plugins/jackal-linear/hooks/linear-status-hook.py")
  EXIT_CODE=$?
  rm -rf "$TMP_DIR"
  [ -z "$OUTPUT" ] && [ "$EXIT_CODE" -eq 0 ] && echo "AC3.3 PASS" || echo "AC3.3 FAIL"
  ```

### AC3.4: Unrelated Bash commands do not trigger the hook

- **Type:** unit (stdin/stdout script test)
- **Verifies:** Commands like `ls`, `npm test`, `cat file.txt` produce no output even when `.linear-issue` is present
- **Command:**
  ```bash
  TMP_DIR=$(mktemp -d)
  mkdir "$TMP_DIR/.git"
  echo "ENG-123" > "$TMP_DIR/.linear-issue"
  PASS=true
  for CMD in "ls -la" "npm test" "cat file.txt" "git status" "python3 app.py"; do
    OUTPUT=$(cd "$TMP_DIR" && echo "{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"$CMD\"}}" | python3 "$(pwd)/plugins/jackal-linear/hooks/linear-status-hook.py")
    if [ -n "$OUTPUT" ]; then
      echo "AC3.4 FAIL: unexpected output for '$CMD'"
      PASS=false
    fi
  done
  rm -rf "$TMP_DIR"
  $PASS && echo "AC3.4 PASS"
  ```

### AC3.5 (Failure): Hook exit code does not block the triggering Bash command

- **Type:** unit (stdin/stdout script test)
- **Verifies:** The hook always exits 0 regardless of input -- bad JSON, missing fields, invalid tool name
- **Command:**
  ```bash
  PASS=true
  SCRIPT="plugins/jackal-linear/hooks/linear-status-hook.py"

  # Bad JSON
  echo "not json" | python3 "$SCRIPT" > /dev/null 2>&1; [ $? -eq 0 ] || PASS=false
  # Empty input
  echo "" | python3 "$SCRIPT" > /dev/null 2>&1; [ $? -eq 0 ] || PASS=false
  # Wrong tool name
  echo '{"tool_name":"Write","tool_input":{"command":"gh pr create"}}' | python3 "$SCRIPT" > /dev/null 2>&1; [ $? -eq 0 ] || PASS=false
  # Missing tool_input
  echo '{"tool_name":"Bash"}' | python3 "$SCRIPT" > /dev/null 2>&1; [ $? -eq 0 ] || PASS=false

  $PASS && echo "AC3.5 PASS" || echo "AC3.5 FAIL"
  ```

### hooks.json structural check (supports AC3)

- **Type:** manual-script
- **Verifies:** `hooks.json` is valid JSON with `PostToolUse` matcher on `Bash` pointing to `linear-status-hook.py`
- **Command:**
  ```bash
  python3 -c "
  import json
  h = json.load(open('plugins/jackal-linear/hooks/hooks.json'))
  hooks = h['hooks']['PostToolUse']
  assert any(m['matcher'] == 'Bash' for m in hooks), 'No Bash matcher found'
  assert any('linear-status-hook.py' in hook['command'] for m in hooks for hook in m['hooks']), 'Hook script not referenced'
  print('hooks.json structural check PASS')
  "
  ```

---

## Human Verification Required

### AC2.1: Running `/start-from-linear ENG-123` fetches the issue title and description via Linear MCP

- **Why not automated:** Requires a live Linear MCP connection (OAuth-authenticated), a real issue in Linear, and Claude Code runtime to execute the `/start-from-linear` command. The command file and skill are behavioral instructions for Claude, not executable code.
- **Verification steps:**
  1. Install the jackal-linear plugin in Claude Code
  2. Ensure Linear MCP OAuth is authenticated (complete the browser prompt if first use)
  3. Identify a real Linear issue ID in your workspace (e.g., `ENG-123`)
  4. Run `/start-from-linear ENG-123` in Claude Code
  5. Observe Claude's output -- it should display the issue title and description fetched from Linear
- **Pass condition:** Claude displays the correct issue title and description matching what is shown in the Linear UI for that issue.

### AC2.2: The Linear issue is set to In Progress after the command runs

- **Why not automated:** Requires checking the issue status in Linear after the command executes. Depends on live Linear MCP tools and OAuth.
- **Verification steps:**
  1. Complete the steps for AC2.1
  2. Open the issue in the Linear UI (or use the Linear API)
  3. Check the issue's workflow state
- **Pass condition:** The issue status is "In Progress" (or the closest equivalent workflow state in the team's configuration).

### AC2.3: `.linear-issue` file is written to project root containing the issue ID

- **Why not automated:** Depends on AC2.1 completing successfully (requires live Claude Code + Linear MCP). The file check itself is trivial but depends on the behavioral chain completing.
- **Verification steps:**
  1. Complete the steps for AC2.1
  2. Run `cat .linear-issue` at the project root
- **Pass condition:** The file exists and contains only the issue ID (e.g., `ENG-123`) with an optional trailing newline.

### AC2.4: `starting-a-design-plan` receives the issue title as the design goal context

- **Why not automated:** Requires observing Claude's behavioral handoff to the `starting-a-design-plan` skill. The handoff is governed by instructions in the SKILL.md, not executable code.
- **Verification steps:**
  1. Complete the steps for AC2.1
  2. Observe Claude's output after fetching the issue -- it should announce the design session with the issue title
  3. Observe that Claude invokes the `starting-a-design-plan` skill
  4. Check that the design planning phase uses the Linear issue title as the design goal
- **Pass condition:** Claude announces the design session referencing the issue title and description, then transitions into the design planning workflow with that context.

### AC2.5 (Failure): Running with a non-existent issue ID surfaces an error

- **Why not automated:** Requires live Linear MCP to attempt fetching a non-existent issue and Claude to interpret the error response.
- **Verification steps:**
  1. Run `/start-from-linear FAKE-99999` (an issue ID that does not exist)
  2. Observe Claude's response
  3. Check that `.linear-issue` was NOT written (`ls .linear-issue` should fail)
- **Pass condition:** Claude reports an error message indicating the issue was not found. No `.linear-issue` file is created. Claude does not proceed to the design planning workflow.

### AC4.1: On PR created event, issue status is set to In Review and a PR comment is posted to Linear

- **Why not automated:** Requires an end-to-end flow: a real Linear issue in progress, the hook firing after `gh pr create`, Claude invoking the `linear-workflow` finish mode, and Linear MCP tools posting the update. All of these are behavioral and require live services.
- **Verification steps:**
  1. Start a Linear-linked session with `/start-from-linear [ISSUE-ID]` (complete the full start flow)
  2. Make changes, commit, and run `gh pr create`
  3. Observe Claude's response -- it should announce using `linear-workflow` finish mode
  4. Check the Linear issue in the UI: status should be "In Review"
  5. Check the issue's comment thread: a new comment should be present with the PR link
- **Pass condition:** Issue status is "In Review" in Linear. A comment exists on the issue containing the PR URL and a brief description of the change.

### AC4.2: On merge event, issue status is set to Done, a completion comment is posted, and `.linear-issue` is deleted

- **Why not automated:** Same as AC4.1 -- requires full end-to-end behavioral chain with live services.
- **Verification steps:**
  1. Continue from AC4.1 (issue is in "In Review" state, PR exists)
  2. Merge the PR (via `gh pr merge` or `git merge`)
  3. Observe Claude's response -- it should announce using `linear-workflow` finish mode
  4. Check the Linear issue in the UI: status should be "Done"
  5. Check the issue's comment thread: a completion comment should be present
  6. Run `ls .linear-issue` -- file should not exist
- **Pass condition:** Issue status is "Done". A completion comment exists with the PR/commit link. `.linear-issue` has been deleted from the project root.

### AC4.3: Comments posted to Linear include a link to the PR or commit

- **Why not automated:** Depends on AC4.1 and AC4.2 completing. The link inclusion is governed by behavioral instructions in `writing-for-linear`.
- **Verification steps:**
  1. After AC4.1 and AC4.2, review the comments posted to the Linear issue
  2. Each comment should contain a URL (GitHub PR link or commit hash)
- **Pass condition:** Both the PR-created comment and the merge comment contain a clickable link to the PR or a commit hash.

### AC4.4 (Failure): Finish mode does nothing if `.linear-issue` is absent

- **Why not automated:** Requires observing Claude's behavioral response when the hook fires but `.linear-issue` is missing. The hook's no-output behavior IS tested automatically (AC3.3), but the skill's "do nothing" behavior requires human observation.
- **Verification steps:**
  1. Ensure no `.linear-issue` file exists at the project root (`rm -f .linear-issue`)
  2. Run `gh pr create` in a Claude Code session with the jackal-linear plugin installed
  3. Observe Claude's response
- **Pass condition:** Claude does not attempt any Linear updates. No errors are thrown. The PR creation proceeds normally without Linear-related output.

### AC5.1: Skill covers issue descriptions (structured, outcome-focused)

- **Why not automated:** The skill file's content can be checked for keywords, but the acceptance criterion is about whether the instructions actually produce well-structured issue descriptions when Claude follows them. This is a behavioral quality check.
- **Verification steps:**
  1. Read `plugins/jackal-linear/skills/writing-for-linear/SKILL.md`
  2. Confirm it contains a "Context 1: Issue Descriptions" section
  3. Confirm the section includes principles (outcome-focused, structured, unambiguous) and a template
  4. Optionally: invoke the skill and ask Claude to write a sample issue description; verify it follows the template
- **Pass condition:** The SKILL.md contains a dedicated section for issue descriptions with principles, a template, and rules. If tested live, Claude produces a description matching the template structure.

### AC5.2: Skill covers status-change comments (brief, includes PR link, states what changed)

- **Why not automated:** Same reasoning as AC5.1 -- behavioral quality of generated content.
- **Verification steps:**
  1. Read `plugins/jackal-linear/skills/writing-for-linear/SKILL.md`
  2. Confirm it contains a "Context 2: Status-Change Comments" section
  3. Confirm the section includes templates for both PR-created and merged events
  4. Confirm templates include placeholders for PR URL and a description of the change
- **Pass condition:** The SKILL.md contains status-change comment templates for both events, with explicit guidance to include PR links and state what changed.

### AC5.3: Skill covers inline comments (conversational, for questions or blockers)

- **Why not automated:** Same reasoning as AC5.1.
- **Verification steps:**
  1. Read `plugins/jackal-linear/skills/writing-for-linear/SKILL.md`
  2. Confirm it contains a "Context 3: Inline Comments" section
  3. Confirm the section includes patterns for questions, blockers, and observations
- **Pass condition:** The SKILL.md contains an inline comments section with conversational patterns and rules distinguishing inline comments from status updates.

---

## Test Execution Order

The tests should be run in the following sequence. Dependencies are noted where a test requires a prior test to pass.

### Phase 1: Structural checks (no live services required)

Run these first -- they validate that all files exist and are well-formed. These can be run immediately after implementation, before any live testing.

1. **AC1.1** -- `plugin.json` valid JSON with `mcpServers`
2. **AC1.2** -- Marketplace entry present with matching version
3. **AC1.4** -- (Covered by AC1.2 assertion)
4. **AC1.3** -- All component files exist
5. **hooks.json structural check** -- Valid JSON with correct matcher config

### Phase 2: Hook script unit tests (no live services required)

Run these next -- they test the Python hook script in isolation using temp directories. No Linear account or Claude Code needed.

6. **AC3.4** -- Unrelated commands produce no output
7. **AC3.5** -- Hook always exits 0 (bad input resilience)
8. **AC3.3** -- No output when `.linear-issue` absent
9. **AC3.1** -- Outputs reminder for `gh pr create` when `.linear-issue` present
10. **AC3.2** -- Outputs reminder for `git merge` / `gh pr merge` when `.linear-issue` present

### Phase 3: Skill content review (human, no live services required)

Read the skill files and verify their content sections. This can be done in parallel with Phase 2.

11. **AC5.1** -- `writing-for-linear` covers issue descriptions
12. **AC5.2** -- `writing-for-linear` covers status-change comments
13. **AC5.3** -- `writing-for-linear` covers inline comments

### Phase 4: Live integration tests (requires Linear account + Claude Code)

These must be run in order -- each builds on the prior step's state. Requires a real Linear workspace with at least one issue, OAuth authentication, and Claude Code with the plugin installed.

14. **AC2.5** -- Non-existent issue ID produces error (run first to avoid polluting a real issue)
15. **AC2.1** -- `/start-from-linear` fetches issue (depends on: Linear MCP authenticated)
16. **AC2.2** -- Issue set to In Progress (depends on: AC2.1)
17. **AC2.3** -- `.linear-issue` written (depends on: AC2.1)
18. **AC2.4** -- Handoff to `starting-a-design-plan` (depends on: AC2.1)
19. **AC4.4** -- Finish mode no-op when `.linear-issue` absent (can run independently)
20. **AC4.1** -- PR created sets In Review + posts comment (depends on: AC2.1-2.3 completed, then `gh pr create`)
21. **AC4.3** -- Comments include PR link (depends on: AC4.1)
22. **AC4.2** -- Merge sets Done + posts comment + deletes `.linear-issue` (depends on: AC4.1, then merge the PR)
