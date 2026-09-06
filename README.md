# ed3d-plugins
---
## Hi! This repository is no longer maintained. I have moved away from Claude Code as a tool. I might not-so-humbly suggest [Polytoken](https://polytoken.dev), the harness I maintain, as a nice, happy, multi-provider harness for both coding and other tasks.

## Also, [I have a YouTube channel](https://www.youtube.com/@ed3dnet) where I talk about computery stuff and how to effectively use AI. Here's a sample.

[![IMAGE ALT TEXT](http://img.youtube.com/vi/q257UmHSP5E/0.jpg)](http://www.youtube.com/watch?v=q257UmHSP5E "Chasing big models is a curse. Fix your workflows instead.
")
---

This is my collection of plugins that I use on a day-to-day basis for getting stuff done with Claude Code. Most of these are development-oriented in some way or another, but also often end up being useful for other things. Product design, general research, accidentally becoming my homelab sysadmin—these are a lot of what I've learned so far and what I've found helpful.

The big stick in this repository is `ed3d-plan-and-execute`, which implements an "RPI" (research-plan-implement) loop that I think does a really good job of avoiding hallucination in the planning stages, adhering to high-level product requirements, avoiding drift between design planning and implementation planning, and reviewing the results such that you get out the other end not just what you asked for, but what you actually wanted.

**NOTE:** `ed3d-plugins` is generally a more stable marketplace. If you'd like to track changes as they happen a bit more aggressively, take a look at [`ed3d-plugins-testing`](https://github.com/ed3dai/ed3d-plugins-testing).

## Using `ed3d-plan-and-execute`
More in [the README for the plugin](plugins/ed3d-plan-and-execute/README.md), and it's worth skimming, but here's a quickstart:

```
Rough Idea
    │
    ▼
/start-design-plan  ──────► Design Document (committed to git)
    │
    ▼
/start-implementation-plan ──► Implementation Plan (phase files)
    │
    ▼
/execute-implementation-plan ──► Working Code (reviewed & committed)
```

**Customization:** Create `.ed3d/design-plan-guidance.md` and `.ed3d/implementation-plan-guidance.md` in your project to provide project-specific constraints, terminology, and standards. Run `/how-to-customize` for details.

## Plugins

| Plugin | Description |
|--------|-------------|
| **`ed3d-00-getting-started`** | Getting started guide and onboarding for ed3d-plugins. Run `/getting-started` to see this README. |
| **`ed3d-plan-and-execute`** | Planning and execution workflows for Claude Code. Feed it a decent-sized task and it'll help you get it done in a sustainable and thought-through way |
| **`ed3d-house-style`** | House style for software development; Very Opinionated |
| **`ed3d-basic-agents`** | Core agents for general-purpose tasks (haiku, sonnet, opus). Other plugins expect this to exist |
| **`ed3d-research-agents`** | Agents for research across multiple data sources (codebase, internet, combined); other plugins expect this to exist |
| **`ed3d-extending-claude`** | Knowledge skills for extending Claude Code: plugins, commands, agents, skills, hooks, MCP servers. Other plugins expect this to exist |
| **`ed3d-playwright`**| Playwright automation with subagents |
| **`ed3d-hook-skill-reinforcement`** | UserPromptSubmit hook that reinforces the need to activate skills—helps make sure skills actually get used. Requires `ed3d-extending-claude` to work |
| **`ed3d-hook-claudemd-reminder`** | PostToolUse hook that reminds to update CLAUDE.md before committing |
| **`ed3d-hook-security-hardening`** | PreToolUse and PostToolUse hooks that catch secrets leakage patterns |
| **`ed3d-session-reflection`** | EXPERIMENTAL. Session awareness and conversation review tooling. Requires `ed3d-extending-claude` |

## Installation

### Add the marketplace
```bash
/plugin marketplace add https://github.com/ed3dai/ed3d-plugins.git
```

### Install plugins
All plugins are available from the `ed3d-plugins` marketplace:
```bash
/plugin install ed3d-plan-and-execute@ed3d-plugins
/plugin install ed3d-house-style@ed3d-plugins
# ... etc
```

## Repository Structure

```
ed3d-plugins/
├── .claude-plugin/
│   └── marketplace.json
├── plugins/
│   ├── ed3d-00-getting-started/
│   ├── ed3d-plan-and-execute/
│   ├── ed3d-house-style/
│   ├── ed3d-basic-agents/
│   ├── ed3d-research-agents/
│   ├── ed3d-extending-claude/
│   ├── ed3d-playwright/
│   ├── ed3d-hook-skill-reinforcement/
│   ├── ed3d-hook-claudemd-reminder/
│   ├── ed3d-hook-security-hardening/
│   └── ed3d-session-reflection/
└── README.md
```

## Contributing
Issues and pull requests gratefully solicited, except `ed3d-house-style` is _my_ house style, and provided for reference, so I might not take contributions there. (You can make your own house-style plugin though and use that instead!)

## Attribution

`ed3d-plan-and-execute` and parts of `ed3d-extending-claude` are derived from [`obra/superpowers`](https://github.com/obra/superpowers) by Jesse Vincent. The original plugin has been folded, spindled, and mutilated extensively.

Some skills in `ed3d-house-style` are derived from `obra/superpowers` and others (`property-based-testing` is a big one) are derived from the [Trail of Bits Skills repository](https://github.com/trailofbits/skills).

## License

The original [obra/superpowers](https://github.com/obra/superpowers) code in this repository is licensed under the MIT License, copyright Jesse Vincent. See `plugins/ed3d-plan-and-execute/LICENSE.superpowers`.

All other content is licensed under the [Creative Commons Attribution-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-sa/4.0/).
