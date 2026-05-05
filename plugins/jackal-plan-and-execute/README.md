# jackal-plan-and-execute v2

Model-adaptive planning and execution harness for Claude Code.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  MAIN CONVERSATION (Opus, 1M context)                   │
│                                                         │
│  Skills: design, plan, execute, review, finish, debug   │
│                                                         │
│  Holds full session state. Never clears.                │
│  Dispatches stateless workers via Agent tool.           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Workers (stateless, one-shot):                         │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Planner  │  │Implementor│  │ Reviewer │             │
│  │ (Opus)   │  │ (Sonnet)  │  │ (Sonnet) │             │
│  └──────────┘  └──────────┘  └──────────┘             │
│                                                         │
│  Coordination: git (worktrees, commits) + TODO.md       │
└─────────────────────────────────────────────────────────┘
```

## Design Principles

1. **Sonnet is the workhorse.** Implementation and review use Sonnet. Opus for planning only.
2. **Phase = unit of work.** No micro-task splitting. One phase, one dispatch.
3. **Review is proportional to risk.** Simple → none. Standard → final only. Complex → per-phase.
4. **Self-review before external review.** Implementor checks its own output.
5. **Continuous execution.** Orchestrator churns through the backlog until genuinely stuck.
6. **No /clear ceremonies.** 1M context means no artificial resets between phases.
7. **Parallel when possible.** Independent issues dispatch concurrently.

## Skills

| Skill | Purpose | User-invocable |
|-------|---------|----------------|
| `design` | Full design workflow (Complex issues) | Yes |
| `plan` | Generate implementation plan + worktree | Yes |
| `execute` | Execute plan or drive continuous backlog | Yes |
| `review` | Dispatch reviewer, manage fix loop | No (called by execute) |
| `finish` | Merge/PR/keep/discard + cleanup | Yes |
| `debug` | Systematic root-cause debugging | No (activated on failures) |

## Agents

| Agent | Model | Role |
|-------|-------|------|
| `planner` | Opus | Generates implementation phase files from design docs |
| `implementor` | Sonnet | Executes one phase or one Simple issue completely |
| `reviewer` | Sonnet | Validates code against requirements, returns structured verdict |

## Delegation Model

The main conversation (orchestrator) manages state and makes decisions. It **never** writes code, runs tests for correctness, or investigates the codebase directly.

| Do directly (orchestrator) | Delegate to subagent |
|---|---|
| Read/write TODO.md and issue docs | Write code and tests → `implementor` |
| Run conflict gate (git commands) | Generate phase files → `planner` |
| Create/remove worktrees | Validate code against requirements → `reviewer` |
| Route by complexity, decide whether to review | Investigate codebase patterns → `codebase-investigator` |
| Merge branches, update backlog | Research external deps/APIs → `combined-researcher` |
| Report to human | |

**The rule:** If a task produces an artifact (code, phase files, a review verdict, research findings), delegate it. If a task reads or updates shared state (backlog, git, issue docs) or requires a routing decision, do it directly.

## Complexity Routing

| Complexity | Pipeline |
|---|---|
| Simple | implementor directly (no plan, no design) |
| Standard | plan → execute (no design phase) |
| Complex | design → plan → execute |

## Continuous Execution (Backlog Mode)

```
/execute (no arguments)
```

The orchestrator:
1. Reads TODO.md
2. Finds unblocked issues
3. Runs conflict gate
4. Dispatches work (parallel when independent)
5. Merges, updates backlog
6. Reports one-liner
7. Loops until stuck

Stops for: human decisions, all blocked, review failures (3x), ambiguity.

## Harness Guidance

Create `.jackal/harness-guidance.md` in your project root to customize orchestrator behavior across all skills. This file is read at the start of every skill run and takes precedence over built-in defaults.

Typical contents:
- **Delegation overrides** — e.g., "always review auth phases even if not the final phase"
- **Merge strategy** — e.g., "never merge locally; always open a PR"
- **Test command** — override the auto-detected test command
- **Stop conditions** — e.g., "pause after each issue rather than looping"
- **Parallel execution policy** — e.g., "never dispatch in parallel (shared DB state)"

If the file doesn't exist, all defaults apply.

## Migration from v1

| v1 | v2 |
|----|-----|
| `task-implementor-fast` (Haiku) | `implementor` (Sonnet) |
| `code-reviewer` (Opus) | `reviewer` (Sonnet) |
| `task-bug-fixer` | Removed — implementor fixes its own issues |
| `test-analyst` | Removed — reviewer covers coverage |
| 4 design skills | 1 `design` skill |
| 2 plan skills | 1 `plan` skill |
| Mandatory per-phase review | Conditional review |
| /clear between phases | No clearing |
| 2-5 minute task granularity | Phase-level granularity |
| Minor issues block | Minor issues reported, don't block |
