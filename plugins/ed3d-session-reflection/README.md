# ed3d-session-reflection

**EXPERIMENTAL.** Session awareness and conversation review tooling for Claude Code.

## What It Does

This plugin gives Claude Code self-awareness of its own session and provides tools to review how sessions went — analyzing human prompting effectiveness, agent performance, and environment/tooling gaps.

### Session Awareness

A `SessionStart` hook injects the current session ID and transcript path into Claude's context. This means Claude knows where its own conversation lives on disk, enabling review and export workflows.

### Conversation Review

Two skills for reviewing sessions:

- **`/review-session`** — Deep qualitative review of the current session (or a specified transcript). Dispatches a Fable agent that reads the reduced transcript and writes structured findings covering what went well, what went wrong, and actionable recommendations.

- **`/review-recent-sessions`** — Reviews the last N sessions (default 5) in the current project. Dispatches parallel Fable reviewers (one per session), then synthesizes cross-session patterns with a Sonnet agent. Identifies recurring issues and highest-impact recommendations.

### Transcript Reduction

A preprocessing script (`reduce-transcript.py`) strips Claude Code JSONL transcripts down to a token-efficient text format, removing metadata noise (UUIDs, permission modes, git branches) while preserving the conversation flow, tool calls, and results. Typical reduction: 78-99% depending on session composition.

## Requirements

- **`ed3d-extending-claude`** must be installed. The conversation reviewer agent loads the `writing-claude-directives` skill as a reference for evaluating prompt quality.

## Installation

```
/plugin install ed3d-session-reflection@ed3d-plugins
```

## Components

| Component | Type | Description |
|-----------|------|-------------|
| `session-start.py` | Hook (SessionStart) | Injects session ID and transcript path into context |
| `reduce-transcript.py` | Script | Strips JSONL to token-efficient text for analysis |
| `conversation-reviewer` | Agent (Fable) | Reads reduced transcripts, identifies causal patterns, and writes findings to disk |
| `review-session` | Skill | Single-session review orchestration |
| `review-recent-sessions` | Skill | Multi-session parallel review with synthesis |

## How It Works

```
SessionStart hook
    │ injects session ID + transcript path
    ▼
/review-session (or /review-recent-sessions)
    │
    ├── reduce-transcript.py  →  token-efficient text
    │
    ├── conversation-reviewer  →  findings.md (per session)
    │
    └── (multi-session only) synthesis agent  →  cross-session patterns
```

## Review Axes

The reviewer analyzes sessions across three lenses, following the signal rather than forcing equal coverage:

- **Human prompting** — vagueness that caused wrong output, frustration spirals, mid-stream requirement changes, repeated corrections the agent ignored
- **Agent performance** — looping, over-engineering, missed tool usage, partial completion, human rescue patterns
- **Environment gaps** — extensive codebase exploration suggesting missing CLAUDE.md context, repeated manual sequences that should be automated, missing conventions

Recommendations are typed: CLAUDE.md entries (project or user-level), hooks, skills, or general prompting advice.
