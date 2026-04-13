# jackal-linear Implementation Plan

**Goal:** Create the plugin directory structure, register it in the marketplace, and configure the Linear MCP server.

**Architecture:** Plugin follows the standard `plugins/{name}/.claude-plugin/plugin.json` layout. Linear MCP is registered via `npx mcp-remote` pointing to `https://mcp.linear.app/mcp`. OAuth 2.1 is handled automatically by mcp-remote on first use. Plugin entry is added to the repo-root marketplace.

**Tech Stack:** JSON config files, mcp-remote (npm), Linear MCP server (OAuth 2.1)

**Scope:** 5 phases from original design (phases 1-5)

**Codebase verified:** 2026-03-08

---

## Acceptance Criteria Coverage

This phase implements and tests:

### jackal-linear.AC1: Plugin is installable and registers its components
- **jackal-linear.AC1.1 Success:** `plugins/jackal-linear/.claude-plugin/plugin.json` is valid JSON with `mcpServers` key pointing to `mcp-remote https://mcp.linear.app/mcp`
- **jackal-linear.AC1.2 Success:** Marketplace entry in `.claude-plugin/marketplace.json` is present with matching version
- **jackal-linear.AC1.4 Failure:** Marketplace entry version does not match `plugin.json` version — must be kept in sync

> Note: jackal-linear.AC1.3 (commands/start-from-linear.md, skills/linear-workflow/SKILL.md, skills/writing-for-linear/SKILL.md exist) requires Phases 2-5 to complete. It is fully verifiable only after all phases are done.

---

<!-- START_TASK_1 -->
### Task 1: Create plugin.json and .mcp.json

**Files:**
- Create: `plugins/jackal-linear/.claude-plugin/plugin.json`
- Create: `plugins/jackal-linear/.mcp.json`

**Step 1: Create the plugin directory and plugin.json**

```bash
mkdir -p plugins/jackal-linear/.claude-plugin
```

Create `plugins/jackal-linear/.claude-plugin/plugin.json` with the following content:

```json
{
    "name": "jackal-linear",
    "version": "1.0.0",
    "description": "Integrates Linear issue tracking with the ed3d-plan-and-execute workflow. Start design sessions from Linear issues and sync progress back automatically.",
    "author": {
        "name": "Jack Greaney",
        "email": "jgreaney@hcg.com"
    },
    "license": "UNLICENSED",
    "keywords": [
        "linear",
        "issue-tracking",
        "workflow",
        "mcp"
    ],
    "mcpServers": {
        "linear": {
            "command": "npx",
            "args": ["-y", "mcp-remote", "https://mcp.linear.app/mcp"]
        }
    }
}
```

**Step 2: Create .mcp.json (local override)**

Create `plugins/jackal-linear/.mcp.json` with the following content:

```json
{
    "mcpServers": {
        "linear": {
            "command": "npx",
            "args": ["-y", "mcp-remote", "https://mcp.linear.app/mcp"]
        }
    }
}
```

**Step 3: Verify JSON is valid**

Run: `cat plugins/jackal-linear/.claude-plugin/plugin.json | python3 -m json.tool > /dev/null && echo "Valid JSON"`
Expected: `Valid JSON`

Run: `cat plugins/jackal-linear/.mcp.json | python3 -m json.tool > /dev/null && echo "Valid JSON"`
Expected: `Valid JSON`
<!-- END_TASK_1 -->

<!-- START_TASK_2 -->
### Task 2: Create README.md

**Files:**
- Create: `plugins/jackal-linear/README.md`

**Step 1: Create the README**

Create `plugins/jackal-linear/README.md` with the following content:

```markdown
# jackal-linear

Integrates Linear issue tracking with the `ed3d-plan-and-execute` workflow. Start design sessions directly from Linear issues and automatically sync progress back to Linear as work moves through PR creation and merge.

## What it does

- `/start-from-linear [ISSUE-ID]` — fetches a Linear issue, sets it to In Progress, seeds the design planning session with the issue title and description
- PostToolUse hook — detects `gh pr create` and `git merge` events, prompts Claude to update Linear status and post a comment
- On PR creation: sets issue to In Review, posts a comment with the PR link
- On merge: sets issue to Done, posts a completion comment, cleans up

## Installation

1. Install this plugin via the jackal-plugins marketplace.

2. On first use, `mcp-remote` will open a browser prompt for Linear OAuth authorization. Complete the authorization flow to grant Claude access to your Linear account.

3. Add `.linear-issue` to your project's `.gitignore`:
   ```
   echo ".linear-issue" >> .gitignore
   ```

## Usage

Start a design session from a Linear issue:

```
/start-from-linear ENG-123
```

This fetches the issue, sets it to In Progress, and hands off to the design planning workflow with the issue context pre-loaded.

From there, work proceeds normally through the `ed3d-plan-and-execute` phases. When you run `gh pr create` or `git merge`, Claude will be reminded to update the Linear issue status and post a comment.

## Requirements

- `ed3d-plan-and-execute` plugin installed
- Linear account with access to your workspace
- `gh` CLI installed (for PR creation detection)

## Troubleshooting

If Linear authentication fails, clear the mcp-remote auth cache:
```bash
rm -rf ~/.mcp-auth
```
Then retry — the OAuth browser prompt will reappear.
```

**Step 2: Verify file exists**

Run: `ls plugins/jackal-linear/README.md`
Expected: File path printed without error
<!-- END_TASK_2 -->

<!-- START_TASK_3 -->
### Task 3: Add marketplace entry and CHANGELOG entry

**Files:**
- Modify: `.claude-plugin/marketplace.json:128-130`
- Modify: `CHANGELOG.md` (top of file, after `# Changelog` heading)

**Step 1: Add jackal-linear to marketplace.json**

In `.claude-plugin/marketplace.json`, make two edits to add the new plugin entry:

**Edit A:** Add a trailing comma after the closing `}` of the `ed3d-playwright` entry (line 128). Change:
```json
        }
    ]
}
```
to:
```json
        },
        {
            "name": "jackal-linear",
            "description": "Integrates Linear issue tracking with the ed3d-plan-and-execute workflow. Start design sessions from Linear issues and sync progress back automatically.",
            "version": "1.0.0",
            "source": "./plugins/jackal-linear",
            "author": {
                "name": "Jack Greaney",
                "email": "jgreaney@hcg.com"
            },
            "license": "UNLICENSED",
            "keywords": [
                "linear",
                "issue-tracking",
                "workflow",
                "mcp"
            ]
        }
    ]
}
```

**Step 2: Verify version sync between plugin.json and marketplace.json**

Run: `python3 -c "
import json
plugin = json.load(open('plugins/jackal-linear/.claude-plugin/plugin.json'))
marketplace = json.load(open('.claude-plugin/marketplace.json'))
entry = next(p for p in marketplace['plugins'] if p['name'] == 'jackal-linear')
assert plugin['version'] == entry['version'], f'Version mismatch: plugin.json={plugin[\"version\"]}, marketplace={entry[\"version\"]}'
print('Version sync OK:', plugin['version'])
"`
Expected: `Version sync OK: 1.0.0`

**Step 3: Add minimal CHANGELOG entry**

In `CHANGELOG.md`, add the following block immediately after the `# Changelog` heading (before any existing entries). This is a scaffolding-only entry — the full entry is written in Phase 5 once all components exist.

```markdown
## [jackal-linear] 1.0.0

Plugin scaffolding and Linear MCP server registration.

**New:**
- `plugins/jackal-linear` plugin directory with `.claude-plugin/plugin.json` registering the Linear MCP server via `mcp-remote`
```

**Step 4: Verify marketplace.json is valid JSON**

Run: `cat .claude-plugin/marketplace.json | python3 -m json.tool > /dev/null && echo "Valid JSON"`
Expected: `Valid JSON`

**Step 5: Commit**

```bash
git add plugins/jackal-linear/.claude-plugin/plugin.json
git add plugins/jackal-linear/.mcp.json
git add plugins/jackal-linear/README.md
git add .claude-plugin/marketplace.json
git add CHANGELOG.md
git commit -m "feat(jackal-linear): scaffold plugin with Linear MCP server config"
```
<!-- END_TASK_3 -->
