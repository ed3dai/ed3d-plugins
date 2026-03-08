---
name: maintaining-a-marketplace
description: Use when creating, releasing, or maintaining a Claude Code Plugin Marketplace - covers marketplace.json schema, version management, release checklists, changelog conventions, and validation to prevent sync drift between plugin.json and marketplace.json
---

# Maintaining a Marketplace

## Overview

A Claude Code Plugin Marketplace is a git repository containing `.claude-plugin/marketplace.json` that catalogs plugins for discovery and installation. The primary maintenance challenge is **sync drift** — keeping versions, descriptions, and metadata consistent across `plugin.json`, `marketplace.json`, and `CHANGELOG.md`.

## When to Use

- Setting up a new marketplace from scratch
- Releasing a new plugin version
- Adding a plugin to an existing marketplace
- Auditing marketplace consistency
- Troubleshooting plugin installation failures

## Marketplace Structure

```
my-marketplace/
  .claude-plugin/
    marketplace.json       # Required: marketplace catalog
  plugins/
    plugin-a/
      .claude-plugin/
        plugin.json        # Required: plugin manifest
      skills/
      commands/
      agents/
    plugin-b/
      .claude-plugin/
        plugin.json
```

## marketplace.json Schema

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "my-marketplace",
  "owner": {
    "name": "Your Name",
    "email": "you@example.com"
  },
  "metadata": {
    "description": "Brief marketplace description",
    "version": "1.0.0",
    "pluginRoot": "./plugins"
  },
  "plugins": [
    {
      "name": "my-plugin",
      "source": "./plugins/my-plugin",
      "description": "What this plugin does",
      "version": "1.0.0",
      "author": {
        "name": "Your Name",
        "email": "you@example.com"
      },
      "license": "MIT",
      "keywords": ["category1", "category2"],
      "category": "development"
    }
  ]
}
```

**Required fields:**
- `name` — Kebab-case marketplace identifier. Users see this: `/plugin install my-tool@marketplace-name`
- `owner.name` — Maintainer name (string, not bare string for owner)
- `plugins` — Array of plugin entries

**Each plugin entry requires:**
- `name` — Kebab-case plugin identifier
- `source` — Where to fetch the plugin (see Source Formats below)

**Common optional fields:** `description`, `version`, `author`, `license`, `keywords`, `category`, `tags`, `homepage`, `repository`

**Fields that DO NOT exist** (do not invent these): `displayName`, `installUrl`, `path`, `marketplace` (as wrapper object)

### Source Formats

```json
// Relative path (monorepo — only works with git-based marketplace add)
"source": "./plugins/my-plugin"

// GitHub repository
"source": { "source": "github", "repo": "owner/repo" }

// GitHub with pinned version
"source": { "source": "github", "repo": "owner/repo", "ref": "v2.0.0", "sha": "a1b2c3..." }

// Git URL (GitLab, Bitbucket, self-hosted)
"source": { "source": "url", "url": "https://gitlab.com/team/plugin.git" }
```

## Release Checklist

When releasing a new plugin version, update these files **in this order**:

1. **`plugins/<name>/.claude-plugin/plugin.json`** — Bump `version`
2. **`.claude-plugin/marketplace.json`** — Update matching plugin entry's `version` to the same value
3. **`CHANGELOG.md`** — Add entry at the top (after `# Changelog` heading)
4. **Validate** — Run `claude plugin validate .` or `/plugin validate .` from the marketplace root
5. **Commit and push** — Single commit with all three file changes

### Changelog Format

```markdown
## plugin-name X.Y.Z

Brief description of the release (1-2 sentences).

**New:**
- Specific new features or additions

**Changed:**
- Modifications to existing behavior

**Fixed:**
- Bug fixes
```

Only include sections that apply. Be specific — "Added `code-review-checklist` skill for systematic code review" not "Added new skill."

### Version Sync Verification

After editing, verify these match:
- `plugins/<name>/.claude-plugin/plugin.json` → `version`
- `.claude-plugin/marketplace.json` → plugin entry's `version`
- `CHANGELOG.md` → entry header `## plugin-name X.Y.Z`

All three MUST show the same version string.

## Creating a New Marketplace

### From Scratch

1. Create directory structure with `.claude-plugin/marketplace.json`
2. Add plugin entries with `name` and `source` at minimum
3. Add `$schema` field for validation
4. Validate: `claude plugin validate .`
5. Test locally: `/plugin marketplace add ./my-marketplace`
6. Push to git host for distribution

### Adding a Plugin to Existing Marketplace

1. Read the plugin's `plugin.json` to extract metadata
2. Add entry to `plugins` array in `marketplace.json` with fields matching plugin.json
3. Validate: `claude plugin validate .`
4. Add changelog entry for the marketplace update

## Distribution

Users add your marketplace by its git location:

```bash
# GitHub
/plugin marketplace add owner/repo

# Other git hosts
/plugin marketplace add https://gitlab.com/company/plugins.git

# Specific branch/tag
/plugin marketplace add https://gitlab.com/company/plugins.git#v1.0.0

# Local (development)
/plugin marketplace add ./my-marketplace
```

Users install plugins from your marketplace:

```bash
/plugin install plugin-name@marketplace-name
```

### Auto-Updates

- Official Anthropic marketplaces auto-update by default
- Third-party marketplaces have auto-update **disabled** by default
- Users toggle auto-update per marketplace in `/plugin` → Marketplaces tab

### Team Configuration

Add to `.claude/settings.json` in a project repo to prompt team members to install:

```json
{
  "extraKnownMarketplaces": {
    "company-tools": {
      "source": { "source": "github", "repo": "your-org/claude-plugins" }
    }
  },
  "enabledPlugins": {
    "formatter@company-tools": true
  }
}
```

### Private Repositories

Manual install uses existing git credential helpers. For background auto-updates, set environment tokens:

| Provider | Variables |
|----------|-----------|
| GitHub | `GITHUB_TOKEN` or `GH_TOKEN` |
| GitLab | `GITLAB_TOKEN` or `GL_TOKEN` |
| Bitbucket | `BITBUCKET_TOKEN` |

## Common Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Version drift between plugin.json and marketplace.json | Old version installed despite push | Verify both files show same version |
| Skipping validation | JSON syntax errors, missing fields | Run `claude plugin validate .` before every push |
| Generic changelog entries | Users can't evaluate upgrade value | Describe specific changes, name affected skills/agents |
| Inventing schema fields | Validation errors, plugins not found | Only use fields from the schema above |
| Using `owner` as string | Validation error | `owner` must be object: `{"name": "...", "email": "..."}` |
| Missing source in plugin entry | Plugin can't be installed | Every plugin entry needs `source` |
| Relative paths in URL-based marketplace | "path not found" errors | Only use relative paths with git-based marketplace add |
| Not committing all sync files together | Partial release, version mismatch | Single commit for plugin.json + marketplace.json + CHANGELOG.md |
| Forgetting to push | Local changes, users see old version | Commit AND push after release |

## Quick Reference

| Task | Files to Touch |
|------|---------------|
| New plugin version | `plugin.json` + `marketplace.json` + `CHANGELOG.md` |
| New plugin added | `marketplace.json` + `CHANGELOG.md` |
| New marketplace | `.claude-plugin/marketplace.json` only |
| Description update | `plugin.json` + `marketplace.json` (keep in sync) |
| Validate | `claude plugin validate .` or `/plugin validate .` |
