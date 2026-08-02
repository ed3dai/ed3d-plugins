# jackal-plugins

Last verified: 2026-07-08

Claude Code plugins for design, implementation, and development workflows (forked from ed3d-plugins).

## Conventions

### Task Invocations Use XML Syntax

When documenting Task tool invocations in skills or agent prompts, use XML-style blocks:

```
<invoke name="Task">
<parameter name="subagent_type">jackal-plan-and-execute:implementor</parameter>
<parameter name="description">Brief description of what the subagent does</parameter>
<parameter name="prompt">
The prompt content goes here.

Can be multiple lines.
</parameter>
</invoke>
```

This format keeps the model on-rails better than fenced code blocks with plain text descriptions.

**Do not** write Task invocations as prose like "Use the Task tool with subagent_type X and prompt Y". Use the XML block format.

### Version Updates Require Marketplace and Changelog Sync

When updating a plugin's version in its `.claude-plugin/plugin.json`, you must also:

1. Update the corresponding version in `.claude-plugin/marketplace.json` at the repo root
2. Add a changelog entry to `CHANGELOG.md` at the repo root

Changelog entries go at the top (after the `# Changelog` heading) and follow the format:

```markdown
## [plugin-name] [version]

Brief description of the release.

**New:**
- New features or additions

**Changed:**
- Modifications to existing behavior

**Fixed:**
- Bug fixes
```

Only include sections that apply. Keep entries concise.

### Worker Agents Never Spawn Subagents

Every agent in `jackal-plan-and-execute` and `jackal-director` (`planner`, `implementor`,
`reviewer`, `reviewer-deep`, `director`, `delta-scribe`, `contract-sentinel`, `lexicon-warden`,
`registry-drift-checker`) must carry `disallowedTools: Agent` in its frontmatter and an explicit
"never dispatch or invoke other subagents" rule in its body. Every dispatch prompt template that
launches one of these agents must repeat the prohibition in the prompt itself — frontmatter
restrictions have known enforcement gaps in some Claude Code contexts, so the prompt-level
instruction is belt-and-braces, not redundant.

`jackal-supervisor` is the sole exception — it is the orchestrating tier and keeps the `Agent` tool.
No other agent in this marketplace should have it.

**When adding a new agent:** decide up front whether it's a worker (deny Agent, add the no-nesting
rule) or an orchestrator (there should almost never be a reason for a second one). If you're unsure,
it's a worker.

### The PR Is the Only Completion Path

`finish` and `jackal-finish-branch` never merge locally. The flow is always: verify tests → rebase
onto origin/main if behind → push → open a PR (`Closes #N`). There is no merge/keep/discard menu in
the default path — keep and discard exist only when a user explicitly asks for them.

Do not reintroduce a "merge to main" option, a `protected_main: false` fast path that skips the PR,
or an options menu in autonomous mode. If a future change needs a genuine exception to this, it
should be a loud, explicit opt-out in `.jackal/harness-guidance.md`, not a default behavior.

## Jackal Config

- `repo_root`: `.` (this repo is its own project root — no separate app subdir)
- `gh_repo`: `jgreaney-HCG/jackal-plugins`
- `issue_prefix`: `JKL`
- `issue_docs`: `docs/issue-docs`
- `design_plans`: `docs/design-plans`
- `impl_plans`: `docs/impl-plans`
- `test_cmd`: `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py && (cd plugins/ed3d-hook-security-hardening/hooks && python3 test-check-bash-secrets.py && python3 test-check-sensitive-file.py) && (cd plugins/jackal-hook-branch-guard/hooks && python3 test-check-branch-guard.py) && (cd plugins/jackal-hook-credential-preflight/hooks && python3 test-check-credential-preflight.py)` (mirrors `.github/workflows/ci.yml`; requires `pip install pyyaml` once locally)
- `git_remote`: `origin`
- `push_cmd`: `git push`
- `label_style`: `slash`
- `modules`:
  - `director` — `plugins/jackal-director`
  - `house-style` — `plugins/jackal-house-style`
  - `plan-and-execute` — `plugins/jackal-plan-and-execute`
  - `supervisor` — `plugins/jackal-supervisor`
  - `hook-security` — `plugins/ed3d-hook-security-hardening`
  - `hook-branch-guard` — `plugins/jackal-hook-branch-guard`
  - `hook-credential-preflight` — `plugins/jackal-hook-credential-preflight`
