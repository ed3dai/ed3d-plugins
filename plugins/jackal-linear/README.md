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
