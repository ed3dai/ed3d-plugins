# jackal-linear Test Results

Generated: 2026-03-08

---

## Coverage Validation

**Automated Criteria:** 10 | **Covered:** 10 | **Missing:** 0

### Covered

| Criterion | Test Location | Verifies |
|-----------|---------------|----------|
| AC1.1: `plugin.json` valid JSON with `mcpServers` | test-requirements.md inline script | Parses `plugin.json`, asserts `mcpServers` key exists, confirms a server entry references `mcp.linear.app/mcp` in its args |
| AC1.2: Marketplace entry with matching version | test-requirements.md inline script | Parses both `plugin.json` and `marketplace.json`, finds `jackal-linear` entry, asserts versions are equal (`1.0.0` = `1.0.0`) |
| AC1.3: All component files exist | test-requirements.md inline script | Checks `os.path.isfile` for `commands/start-from-linear.md`, `skills/linear-workflow/SKILL.md`, and `skills/writing-for-linear/SKILL.md` |
| AC1.4: Version mismatch detected | Covered by AC1.2 | The AC1.2 assertion would fail if versions diverged -- no separate test needed |
| AC3.1: Hook outputs reminder for `gh pr create` | test-requirements.md inline script | Creates temp dir with `.git/` and `.linear-issue` containing `ENG-123`, pipes `gh pr create` JSON to hook, asserts output JSON contains issue ID and `pr-created` event type |
| AC3.2: Hook outputs reminder for `git merge` / `gh pr merge` | test-requirements.md inline script | Two sub-tests: (a) `git merge origin/feature-branch` produces output with `ENG-456` and `merged`; (b) `gh pr merge 42 --squash` produces output with `ENG-789` and `merged` |
| AC3.3: No output when `.linear-issue` absent | test-requirements.md inline script | Creates temp dir with `.git/` but no `.linear-issue`, pipes `gh pr create` JSON, asserts empty stdout and exit code 0 |
| AC3.4: Unrelated commands produce no output | test-requirements.md inline script | With `.linear-issue` present, tests `ls -la`, `npm test`, `cat file.txt`, `git status`, `python3 app.py` -- all produce empty stdout |
| AC3.5: Hook always exits 0 on bad input | test-requirements.md inline script | Tests bad JSON, empty input, wrong tool name (`Write`), missing `tool_input` -- all exit 0 |
| hooks.json structural check | test-requirements.md inline script | Parses `hooks.json`, asserts `PostToolUse` array contains a `Bash` matcher whose hook references `linear-status-hook.py` |

### Missing

None.

**Result: PASS**

All 10 automated acceptance criteria have inline test scripts in `test-requirements.md` that verify the correct behavior. All tests were executed and passed successfully.

---

## Human Test Plan

### Prerequisites

- Claude Code installed with the `jackal-linear` plugin enabled
- A Linear workspace with OAuth authentication configured (first use will trigger a browser prompt via `mcp-remote`)
- At least one real Linear issue available for testing (note the issue ID, e.g., `ENG-123`)
- A non-existent issue ID reserved for error testing (e.g., `FAKE-99999`)
- `gh` CLI installed and authenticated with a GitHub repo where you can create PRs
- A git repository with at least one branch ready to PR/merge
- The `ed3d-plan-and-execute` plugin installed (provides `starting-a-design-plan` skill)
- All automated tests passing (run the inline scripts from `test-requirements.md` first)

---

### Phase 1: Structural Checks (automated -- run first)

Run the inline scripts from `test-requirements.md` for AC1.1, AC1.2, AC1.3, AC1.4, hooks.json check. These do not require live services. Confirm all print PASS before proceeding.

---

### Phase 2: Hook Script Unit Tests (automated -- run second)

Run the inline scripts from `test-requirements.md` for AC3.4, AC3.5, AC3.3, AC3.1, AC3.2. These use temp directories and do not require live services. Confirm all print PASS before proceeding.

Note: The AC3.5 test script as written in `test-requirements.md` uses `$PASS && echo "AC3.5 PASS"` which may fail in zsh due to variable expansion. Run the four sub-cases individually if needed:

```bash
SCRIPT="plugins/jackal-linear/hooks/linear-status-hook.py"
echo "not json" | python3 "$SCRIPT" > /dev/null 2>&1; echo "Exit: $?"
echo "" | python3 "$SCRIPT" > /dev/null 2>&1; echo "Exit: $?"
echo '{"tool_name":"Write","tool_input":{"command":"gh pr create"}}' | python3 "$SCRIPT" > /dev/null 2>&1; echo "Exit: $?"
echo '{"tool_name":"Bash"}' | python3 "$SCRIPT" > /dev/null 2>&1; echo "Exit: $?"
```

All four should print `Exit: 0`.

---

### Phase 3: Skill Content Review (human, no live services)

| Step | Action | Expected |
|------|--------|----------|
| 3.1 | Open `/Users/jgreaney/Documents/code/jackal-plugins/plugins/jackal-linear/skills/writing-for-linear/SKILL.md` | File opens successfully |
| 3.2 | Locate the heading `## Context 1: Issue Descriptions` | Section exists starting at line 21 |
| 3.3 | Verify it contains `### Principles` with bullets for "Outcome-focused", "Structured", "Unambiguous" | All three principles present (lines 27-29) |
| 3.4 | Verify it contains `### Template` with sections: Summary, Background, Requirements, Acceptance Criteria, Out of scope | Template present with all five sections (lines 33-58) |
| 3.5 | Verify it contains `### Rules` with at least 3 rules | Four rules present (lines 62-65) |
| 3.6 | Locate the heading `## Context 2: Status-Change Comments` | Section exists starting at line 69 |
| 3.7 | Verify it contains `### Template: PR Created (In Review)` with placeholders for PR title, PR URL, and one-sentence description | Template present (lines 79-86) with all placeholders |
| 3.8 | Verify it contains `### Template: Merged (Done)` with placeholders for branch, PR URL/commit hash, and outcome sentence | Template present (lines 98-103) with all placeholders |
| 3.9 | Verify both templates include a line for the link on its own line | Both templates show the URL on a dedicated line |
| 3.10 | Locate the heading `## Context 3: Inline Comments` | Section exists starting at line 122 |
| 3.11 | Verify it contains `### Patterns` with sub-patterns for "Asking a question", "Reporting a blocker", "Sharing an observation" | All three patterns present (lines 134, 141, 149) |
| 3.12 | Verify it contains `### Rules` that distinguish inline comments from status updates | Rule present: "Do not use inline comments to post status updates" (line 158) |

---

### Phase 4: Live Integration Tests (requires Linear + Claude Code)

Run these in order. Each step builds on the prior step's state.

#### 4.1: Error handling -- non-existent issue (AC2.5)

| Step | Action | Expected |
|------|--------|----------|
| 4.1.1 | In Claude Code, run `/start-from-linear FAKE-99999` | Claude attempts to fetch the issue via Linear MCP |
| 4.1.2 | Observe Claude's response | Claude reports an error: "Issue FAKE-99999 was not found in Linear" (or similar) |
| 4.1.3 | Run `ls .linear-issue` in the terminal | File does not exist (command fails) |
| 4.1.4 | Confirm Claude did not proceed to design planning | No mention of `starting-a-design-plan` or design session in Claude's output |

#### 4.2: Start flow -- fetch issue and begin design (AC2.1, AC2.2, AC2.3, AC2.4)

| Step | Action | Expected |
|------|--------|----------|
| 4.2.1 | Identify a real Linear issue in your workspace (e.g., `ENG-123`). Note its current title, description, and status in the Linear UI | Baseline recorded |
| 4.2.2 | In Claude Code, run `/start-from-linear ENG-123` (use your real issue ID) | Claude announces: "I'm using the linear-workflow skill to start a Linear-linked design session" |
| 4.2.3 | Observe Claude's output for the issue title and description | Claude displays the correct title and description matching the Linear UI (AC2.1) |
| 4.2.4 | Check the issue in the Linear UI | Status is now "In Progress" (AC2.2) |
| 4.2.5 | Run `cat .linear-issue` in the terminal | File exists and contains only the issue ID (e.g., `ENG-123`) with optional trailing newline (AC2.3) |
| 4.2.6 | Observe Claude's continued output | Claude announces the design session referencing the issue title, then invokes `starting-a-design-plan` (AC2.4) |

#### 4.3: Finish mode no-op when `.linear-issue` absent (AC4.4)

| Step | Action | Expected |
|------|--------|----------|
| 4.3.1 | Run `rm -f .linear-issue` to ensure the file is absent | File removed |
| 4.3.2 | In Claude Code, run a `gh pr create` command (for any branch) | PR is created normally |
| 4.3.3 | Observe Claude's response | Claude does NOT attempt any Linear updates. No errors. No mention of `linear-workflow` finish mode. The hook produces no output (verified by AC3.3 automated test) |

#### 4.4: PR created sets In Review and posts comment (AC4.1, AC4.3)

| Step | Action | Expected |
|------|--------|----------|
| 4.4.1 | Restore the Linear-linked session: run `/start-from-linear ENG-123` again (or use a fresh issue) and let the start flow complete | `.linear-issue` exists, issue is In Progress |
| 4.4.2 | Make a code change, commit it, and create a new branch if needed | Changes committed |
| 4.4.3 | Run `gh pr create --title "test: AC4.1 verification" --body "Testing Linear integration"` | PR created. Claude receives the hook's injected context |
| 4.4.4 | Observe Claude's response | Claude announces: "I'm using the linear-workflow skill to update Linear issue status." Claude invokes `writing-for-linear` to compose a PR-created comment |
| 4.4.5 | Check the Linear issue in the UI | Status is now "In Review" (AC4.1) |
| 4.4.6 | Check the issue's comment thread in Linear | A new comment exists with the PR URL and a brief description of the change (AC4.3) |
| 4.4.7 | Verify the PR URL in the comment is clickable and points to the correct PR | URL is on its own line and links to the correct GitHub PR |
| 4.4.8 | Run `cat .linear-issue` | File still exists (not deleted -- PR only, not merge) |

#### 4.5: Merge sets Done, posts comment, deletes `.linear-issue` (AC4.2, AC4.3)

| Step | Action | Expected |
|------|--------|----------|
| 4.5.1 | Merge the PR from step 4.4 using `gh pr merge --squash` (or `git merge`) | PR merged. Claude receives the hook's injected context |
| 4.5.2 | Observe Claude's response | Claude announces using `linear-workflow` finish mode. Claude invokes `writing-for-linear` to compose a merged comment |
| 4.5.3 | Check the Linear issue in the UI | Status is now "Done" (AC4.2) |
| 4.5.4 | Check the issue's comment thread in Linear | A completion comment exists with the PR URL or commit hash (AC4.3) |
| 4.5.5 | Run `ls .linear-issue` | File does not exist (deleted by finish mode) (AC4.2) |

---

### End-to-End: Full Linear Issue Lifecycle

**Purpose:** Validate the complete flow from issue start through PR creation to merge, confirming all status transitions and artifacts are correct.

**Steps:**

1. Pick a fresh Linear issue (or create one). Record its ID, title, and starting status.
2. Run `/start-from-linear [ISSUE-ID]` in Claude Code.
3. Confirm: issue fetched, status set to In Progress, `.linear-issue` written, design planning invoked.
4. Complete (or stub) the design work. Make a code change and commit.
5. Run `gh pr create`. Confirm: hook fires, status set to In Review, comment posted with PR link.
6. Run `gh pr merge --squash`. Confirm: hook fires, status set to Done, completion comment posted, `.linear-issue` deleted.
7. Verify in Linear UI: the issue has three state transitions logged (In Progress, In Review, Done) and two comments (PR-created, merged).

---

### Human Verification Required

| Criterion | Why Manual | Steps |
|-----------|-----------|-------|
| AC2.1: Fetch issue via Linear MCP | Requires live OAuth + Linear MCP connection | Phase 4, step 4.2.2-4.2.3 |
| AC2.2: Set status to In Progress | Requires live Linear API write | Phase 4, step 4.2.4 |
| AC2.3: `.linear-issue` written | Depends on full start flow completing | Phase 4, step 4.2.5 |
| AC2.4: Handoff to `starting-a-design-plan` | Behavioral -- observe Claude's skill invocation | Phase 4, step 4.2.6 |
| AC2.5: Error on non-existent issue | Requires live Linear MCP error response | Phase 4, step 4.1.1-4.1.4 |
| AC4.1: PR created sets In Review + comment | End-to-end behavioral chain with live services | Phase 4, step 4.4.3-4.4.7 |
| AC4.2: Merge sets Done + comment + cleanup | End-to-end behavioral chain with live services | Phase 4, step 4.5.1-4.5.5 |
| AC4.3: Comments include PR/commit link | Content quality of generated Linear comments | Phase 4, steps 4.4.6-4.4.7 and 4.5.4 |
| AC4.4: Finish mode no-op without `.linear-issue` | Behavioral -- observe Claude does nothing | Phase 4, step 4.3.1-4.3.3 |
| AC5.1: Skill covers issue descriptions | Content review of behavioral instructions | Phase 3, steps 3.2-3.5 |
| AC5.2: Skill covers status-change comments | Content review of behavioral instructions | Phase 3, steps 3.6-3.9 |
| AC5.3: Skill covers inline comments | Content review of behavioral instructions | Phase 3, steps 3.10-3.12 |

---

### Traceability

| Acceptance Criterion | Automated Test | Manual Step |
|----------------------|----------------|-------------|
| AC1.1: plugin.json valid with mcpServers | Inline script (PASS) | -- |
| AC1.2: Marketplace version matches | Inline script (PASS) | -- |
| AC1.3: Component files exist | Inline script (PASS) | -- |
| AC1.4: Version mismatch detection | Covered by AC1.2 (PASS) | -- |
| AC2.1: Fetch issue via MCP | -- | Phase 4, step 4.2.2-4.2.3 |
| AC2.2: Set In Progress | -- | Phase 4, step 4.2.4 |
| AC2.3: Write .linear-issue | -- | Phase 4, step 4.2.5 |
| AC2.4: Handoff to design planning | -- | Phase 4, step 4.2.6 |
| AC2.5: Error on bad issue ID | -- | Phase 4, step 4.1.1-4.1.4 |
| AC3.1: Hook fires on gh pr create | Inline script (PASS) | -- |
| AC3.2: Hook fires on git/gh merge | Inline script (PASS) | -- |
| AC3.3: No output without .linear-issue | Inline script (PASS) | -- |
| AC3.4: Unrelated commands ignored | Inline script (PASS) | -- |
| AC3.5: Hook always exits 0 | Inline script (PASS) | -- |
| AC4.1: PR sets In Review + comment | -- | Phase 4, step 4.4.3-4.4.7 |
| AC4.2: Merge sets Done + cleanup | -- | Phase 4, step 4.5.1-4.5.5 |
| AC4.3: Comments include links | -- | Phase 4, steps 4.4.6, 4.5.4 |
| AC4.4: Finish no-op without file | -- | Phase 4, step 4.3.1-4.3.3 |
| AC5.1: Issue description coverage | -- | Phase 3, steps 3.2-3.5 |
| AC5.2: Status comment coverage | -- | Phase 3, steps 3.6-3.9 |
| AC5.3: Inline comment coverage | -- | Phase 3, steps 3.10-3.12 |
| hooks.json structural check | Inline script (PASS) | -- |
