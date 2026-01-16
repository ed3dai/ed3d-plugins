# ed3d-plugins

Claude Code plugins for design, implementation, and development workflows.

## Conventions

### Task Invocations Use XML Syntax

When documenting Task tool invocations in skills or agent prompts, use XML-style blocks:

```
<invoke name="Task">
<parameter name="subagent_type">ed3d-basic-agents:sonnet-general-purpose</parameter>
<parameter name="description">Brief description of what the subagent does</parameter>
<parameter name="prompt">
The prompt content goes here.

Can be multiple lines.
</parameter>
</invoke>
```

This format keeps the model on-rails better than fenced code blocks with plain text descriptions.

**Do not** write Task invocations as prose like "Use the Task tool with subagent_type X and prompt Y". Use the XML block format.

### Version Updates Require Marketplace Sync

When updating a plugin's version in its `.claude-plugin/plugin.json`, you must also update the corresponding version in `.claude-plugin/marketplace.json` at the repo root.

Both files must stay in sync. The marketplace.json is the source of truth for plugin discovery.
