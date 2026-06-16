# jackal-plugins

The Jackal harness — a model-adaptive set of Claude Code plugins for planning,
executing, and supervising software work. Forked from
[`ed3d-plugins`](https://github.com/ed3dai/ed3d-plugins) and reworked around a
supervisor that drives a GitHub-issue backlog, routes work by complexity, and
runs an Opus orchestrator over stateless Sonnet workers.

The centerpiece is `jackal-plan-and-execute`, which implements a design →
plan → execute → finish loop: it avoids hallucination in planning, keeps
implementation aligned to acceptance criteria, prevents drift between design and
implementation, and reviews results proportionally to risk — so you get out the
other end not just what you asked for, but what you actually wanted.

## Plugins

This marketplace ships four plugins:

| Plugin | Description |
|--------|-------------|
| **`jackal-plan-and-execute`** | The core lifecycle: `design`, `plan`, `execute`, `review`, `finish`, `debug` skills + `planner`/`implementor`/`reviewer` agents (and ported `test-driven-development` / `verification-before-completion` discipline skills). |
| **`jackal-supervisor`** | Project supervisor: the `jackal-supervisor` agent (backlog management, conflict gates, complexity routing) plus wrapper skills (`jackal-design-plan`, `jackal-impl-plan`, `jackal-finish-branch`, `jackal-pause-session`, `jackal-ui-verify`) that add project-specific config around the core lifecycle. |
| **`jackal-house-style`** | Opinionated coding standards — TypeScript, React, Python, Postgres, functional-core/imperative-shell, testing, and technical writing. |
| **`ed3d-hook-security-hardening`** | PreToolUse/PostToolUse hooks that catch common secrets-leakage patterns (echoing env vars, reading secret files, tokens in URLs, missing gitignore on sensitive files). Vendored from upstream. |

## Required dependencies

The jackal plugins **dispatch to agents that ship in upstream ed3d plugins**. The
jackal marketplace does not bundle these — install them from the `ed3d-plugins`
marketplace alongside jackal. Each `requires` relationship is also declared in
`marketplace.json`.

| Dependency (ed3d plugin) | Provides | Used by |
|--------------------------|----------|---------|
| **`ed3d-research-agents`** | `codebase-investigator`, `combined-researcher`, `internet-researcher` | `jackal-plan-and-execute` design/plan (codebase + external research); `jackal-house-style` (library research) |
| **`ed3d-extending-claude`** | `project-claude-librarian` | `jackal-plan-and-execute` finish (CLAUDE.md freshness re-verification at branch closeout) |
| **`ed3d-playwright`** | `playwright-explorer` | `jackal-supervisor` `jackal-ui-verify` (multi-step UI verification) |

If a dependency is missing, the harness is built to **fail loudly** rather than
silently skip — e.g. `finish` warns when `project-claude-librarian` is absent so a
mandatory documentation closeout isn't quietly dropped.

## Installation

Add both marketplaces, then install the jackal plugins and their ed3d dependencies:

```bash
/plugin marketplace add https://github.com/jgreaney-HCG/jackal-plugins.git
/plugin marketplace add https://github.com/ed3dai/ed3d-plugins.git

# Jackal plugins
/plugin install jackal-plan-and-execute@jackal-plugins
/plugin install jackal-supervisor@jackal-plugins
/plugin install jackal-house-style@jackal-plugins
/plugin install ed3d-hook-security-hardening@jackal-plugins

# Required ed3d dependencies
/plugin install ed3d-research-agents@ed3d-plugins
/plugin install ed3d-extending-claude@ed3d-plugins
/plugin install ed3d-playwright@ed3d-plugins
```

## The development cycle

The supervisor-driven flow, routed by issue complexity:

```
Rough idea / GitHub issue
    │
    ▼
/jackal-design-plan   ──► Design document (Complex issues; committed to the feature branch)
    │
    ▼
/jackal-impl-plan     ──► Implementation plan (phase files) in an auto-named worktree
    │
    ▼
/execute              ──► Working code (implemented, reviewed proportionally to risk, committed)
    │
    ▼
/jackal-finish-branch ──► Merge or PR (PR-only when main is protected), backlog updated, worktree cleaned
```

Routing by complexity:

| Complexity | Pipeline |
|---|---|
| Simple | implementor directly (no plan, no design) |
| Standard | plan → execute (no design phase) |
| Complex | design → plan → execute |

For autonomous backlog execution, run `/execute` with no arguments — the
orchestrator pulls unblocked issues from the backlog (GitHub Issues by default, or
`TODO.md`), runs the conflict gate, dispatches work, and loops until genuinely
stuck. See the
[plugin README](plugins/jackal-plan-and-execute/README.md) for the full
architecture.

The raw lifecycle commands (`/design`, `/plan`, `/execute`, `/finish`) are also
available directly when you don't need the supervisor's project-config wrapping.

## Configuration

Two project-level mechanisms customize the harness:

- **`## Jackal Config`** block in your project's `CLAUDE.md` — declares
  `backend` (`github` | `todo-md`), `gh_repo`, `test_cmd`, `protected_main`,
  `label_style` (`slash` | `colon`, default `slash`), module map, and paths. The
  skills read it at the start of every run.
- **`.jackal/harness-guidance.md`** — overrides defaults (merge strategy, review
  policy, parallel execution, stop conditions). Resolved by walking up from the
  working directory to the repo root (nearest-wins), so a monorepo can scope
  guidance per module. `.jackal/design-guidance.md` and
  `.jackal/implementation-guidance.md` add project terminology and standards.
  (Legacy `.ed3d/*-guidance.md` files are still read as a fallback.)

## Contributing

Issues and PRs welcome, except `jackal-house-style` reflects specific opinions and
is provided mostly for reference — fork it into your own house-style plugin if you
want different conventions.

## Attribution

`jackal-plan-and-execute` is derived from
[`obra/superpowers`](https://github.com/obra/superpowers) by Jesse Vincent — folded,
spindled, and mutilated extensively. Several `jackal-house-style` skills are also
derived from `obra/superpowers`; `property-based-testing` is derived from the
[Trail of Bits Skills repository](https://github.com/trailofbits/skills). The
broader plugin structure and the vendored hooks come from
[`ed3d-plugins`](https://github.com/ed3dai/ed3d-plugins) by Ed Ropple.

## License

The original [obra/superpowers](https://github.com/obra/superpowers) code is
licensed under the MIT License, copyright Jesse Vincent. See
`plugins/jackal-plan-and-execute/LICENSE.superpowers`. All other content is
licensed under the
[Creative Commons Attribution-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-sa/4.0/).
