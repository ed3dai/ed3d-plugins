---
name: jackal-ui-verify
description: Generic UI verification skill. Use after implementation completes and before /jackal-finish-branch whenever the issue scope touches the UI. Reads server configuration from the ## Jackal Config section in this project's CLAUDE.md. Runs existing e2e tests, then performs live MCP Playwright visual verification against the issue's acceptance criteria.
user-invocable: true
---

# Jackal UI Verify

**Announce at start:** "I'm using jackal-ui-verify to validate UI changes for [ISSUE-ID]."

---

## Step 0: Load Project Config

Resolve `.jackal/harness-guidance.md` by walking up from the working directory to the repo root
(nearest-wins — a module-level `.jackal/` overrides the root one; see the `jackal-plan-and-execute:execute`
skill's Harness Guidance for the resolution snippet). Apply any overrides (e.g. skip e2e, always use
playwright-explorer).

Read the **## Jackal Config** section from the project's CLAUDE.md. Extract:

| Variable | Key | Example |
|----------|-----|---------|
| `$UI_PATH` | `ui_path` | `ui/` |
| `$UI_PORT` | `ui_port` | `5173` |
| `$API_PORT` | `api_port` | `8000` |
| `$UI_DEV_CMD` | `ui_dev_cmd` | `cd ui && npm run dev` |
| `$API_DEV_CMD` | `api_dev_cmd` | `uv run uvicorn api.main:app --port 8001 --reload` |
| `$E2E_CMD` | `e2e_cmd` | `cd ui && npm run test:e2e` (omit key if no e2e suite) |
| `$ISSUE_DOCS` | `issue_docs` | `docs/issues` |

---

## When to Use

**Required** when the issue's scope includes any files under `$UI_PATH`.

**Skip** for issues that only touch backend, pipeline, or infrastructure with no UI surface changes.

**Invocation point:** After all implementation tasks complete, before `/jackal-finish-branch`.

---

## Step 1: Resolve Issue Context

Read the issue doc to understand what changed:

```bash
ls $REPO_ROOT/$ISSUE_DOCS/ | grep -i "PREFIX-XXX"
```

Read:
- **Scope / In scope** — which components/pages changed
- **Acceptance Criteria** — what to verify (identify UI-verifiable ACs)

Identify the current worktree:
```bash
git worktree list
git branch --show-current
```

---

## Step 2: Check Server Status

```bash
curl -s http://localhost:$UI_PORT > /dev/null && echo "UI: running" || echo "UI: not running"
curl -s http://localhost:$API_PORT/api/health > /dev/null 2>&1 && echo "API: running" || echo "API: not running"
```

**If servers are not running — start them from the worktree:**

Use `$UI_DEV_CMD` and `$API_DEV_CMD` from the Jackal Config. Run them as background processes from within the worktree directory:

Wait for both to be ready:
```bash
for i in $(seq 1 15); do
  curl -s http://localhost:$UI_PORT > /dev/null && echo "UI ready" && break
  sleep 2
done
```

**IMPORTANT — worktree context:** All server commands must be run from within the worktree, not the main repo. The worktree has its own copy of the code.

**If servers are already running:** Confirm they are serving from the correct worktree. If the main repo's servers are running, stop them and restart from the worktree.

---

## Step 3: Run Existing E2E Tests

If `$E2E_CMD` is not set in the Jackal Config, skip this step — the project has no e2e suite.

Otherwise run `$E2E_CMD` from within the worktree. This catches regressions in existing flows.

**Interpreting results:**
- All pass → proceed to Step 4
- Some fail → determine if pre-existing or caused by this change:
  ```bash
  git stash && [e2e command] -- --grep "failing test name" && git stash pop
  ```
- Pre-existing failure → note it, do not block
- New failure introduced by this change → must fix before finishing

---

## Step 4: Live MCP Visual Verification

Use Playwright MCP tools to visually verify each UI-facing acceptance criterion. This catches layout issues, wrong text, missing elements, and broken interactions that automated tests miss.

### 4a. Application Health Check

Navigate to `http://localhost:$UI_PORT`.

Take a screenshot. Check console for errors.

**Pass criteria:** Page loads, no uncaught JS errors, main navigation visible.

### 4b. API Connectivity Check

```
GET http://localhost:$API_PORT/docs  (or /health, /api/health — whichever the project uses)
```

**Pass criteria:** Response received, not connection refused.

### 4c. Acceptance Criteria Verification

For each UI-verifiable AC:

**Decision rule:**
- AC requires: navigate + inspect → use direct MCP tools
- AC requires: multi-step interaction, form fill, modal navigation → use `ed3d-playwright:playwright-explorer` agent

**Template for each AC:**
```
AC: [AC text]
Navigation: [URL path]
Action: [click / fill / observe]
Expected: [what should be visible or true]
Screenshot: [ISSUE-ID]-ac[N]-[description]
```

Screenshots save to `.playwright-mcp/` in the current directory.

### 4d. Regression Smoke Test

Verify the core app flows any UI change could break:

| Check | Expected |
|-------|----------|
| App loads at `http://localhost:$UI_PORT` | Main page visible |
| Primary navigation | Pages load without error |
| Main feature accessible | Data loads, no blank panels |
| No JS errors | `playwright_console_logs` clean |

Use `ed3d-playwright:playwright-explorer` for the navigation smoke test if the app has complex routing.

---

## Step 5: Report

```
## UI Verification Report — [ISSUE-ID] — [Date]

### Environment
- Worktree: .worktrees/[slug]/
- UI: http://localhost:$UI_PORT ✓
- API: http://localhost:$API_PORT ✓

### E2E Test Suite
- Ran: N tests
- Passed: N | Failed: N | Skipped: N
- New failures: [list or "none"]
- Pre-existing failures: [list or "none"]

### Acceptance Criteria Verification
| AC | Description | Result | Screenshot |
|----|-------------|--------|------------|
| AC1 | [text] | ✅ Pass / ❌ Fail | [ISSUE-ID]-ac1-... |

### Smoke Test
- App loads: ✅ / ❌
- Navigation: ✅ / ❌
- No JS errors: ✅ / ❌

### Verdict
✅ PASS — Safe to run /jackal-finish-branch
❌ FAIL — Fix required:
  - [specific issue]
```

---

## Step 6: On Failure

**Visual mismatch:** Take a screenshot, use `playwright_get_visible_html` on the failing element.

**Interaction failure:** Check `playwright_console_logs` for JS errors.

**API error:** Check network, inspect console, check server logs.

**Pre-existing vs new:** Always check if the failure reproduces on `main` before concluding it's a regression. If pre-existing, note but do not block.

---

## Common Issues

| Issue | Likely cause | Fix |
|-------|-------------|-----|
| `curl: (7) Failed to connect` | Server not started | Start from worktree, not main repo |
| Tests pass but UI looks wrong | Tests don't cover visual layout | Add MCP visual check for that AC |
| Wrong port | Config mismatch | Check `ui_port`/`api_port` in Jackal Config |
| Auth redirect loop | Auth bypass not set | Check `api_dev_cmd` in Jackal Config for local dev env vars |
| Wrong version being tested | Server running from main repo | Kill and restart from worktree |
