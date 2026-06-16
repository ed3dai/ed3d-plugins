---
name: design
description: Full design workflow from idea to committed design document. Gathers context, clarifies requirements, brainstorms approaches, and writes the design plan. Use for Complex issues that need architectural decisions before implementation.
user-invocable: true
---

# Design

Transform a rough idea or Complex issue into a committed design document ready for implementation planning.

**Output:** `docs/design-plans/YYYY-MM-DD-{slug}.md`

---

## Harness Guidance

Before starting, resolve `.jackal/harness-guidance.md` and `.jackal/design-guidance.md` by walking up
from the working directory to the repo root (nearest-wins — a module-level `.jackal/` overrides the
root one; see the `execute` skill's Harness Guidance for the resolution snippet). Read what's present
and apply project-specific constraints before step 2.

## Delegation Rules

The design skill handles user interaction and commits the design document. Research is always delegated.

| Do directly | Delegate |
|---|---|
| Confirm DoD with user | Codebase investigation → `codebase-investigator` |
| Brainstorm approaches, write design doc | External tech research → `combined-researcher` |
| Commit design doc to git | |

Do not use Bash/Read/Grep to investigate the codebase yourself — dispatch `codebase-investigator` so its findings land in a clean subagent context and don't bloat the main conversation.

---

## Inputs

When invoked from `jackal-design-plan`, the wrapper passes:
- `WORKTREE_PATH` — absolute path to the feature worktree (already created)
- `BRANCH` — feature branch name
- `ISSUE_ID` — issue identifier
- `SLUG` — pre-determined slug

When invoked directly, accept any of:
- An issue ID (e.g., CG-14)
- An issue doc path
- A freeform description of what to build

If `WORKTREE_PATH` is provided, **all git operations in this skill run from inside `$WORKTREE_PATH`** so the design document commits land on the feature branch, not main. If not provided, the design document commits to main as a planning artifact (legacy mode).

---

## Process

### 1. Gather Context

If given an issue doc, read it. Extract: summary, ACs, scope, technical notes.

Dispatch a codebase investigator to understand current state:
```xml
<invoke name="Agent">
<parameter name="subagent_type">ed3d-research-agents:codebase-investigator</parameter>
<parameter name="description">Investigating codebase for [feature]</parameter>
<parameter name="prompt">
Given that we want to [summary from issue], investigate:
- Existing related functionality or patterns
- Relevant file structure and conventions
- Architectural decisions already in place
- Constraints from existing code

Working directory: [repo root]
</parameter>
</invoke>
```

If external technologies are involved, use `combined-researcher` instead.

If the user hasn't provided enough context, ask for what's missing. Don't ask a long checklist — ask the 1-2 most important questions.

### 2. Confirm Definition of Done

From context gathered, synthesize:
- What gets built (deliverables)
- What success looks like (testable criteria)
- What's explicitly out of scope

Present to user: "Before we explore approaches, here's what I think 'done' means: [DoD]. Correct?"

If user adjusts, incorporate and re-confirm. Don't proceed until confirmed.

### 3. Choose a Slug

The slug becomes the AC prefix (e.g., `cost-ledger.AC1.1`). Suggest 2-3 options:
- If there's a ticket ID, use it: `CG-14-codebuild-infra`
- Otherwise: short, unambiguous kebab-case

Ask user to pick or provide their own.

### 4. Brainstorm Approaches

Propose 2-3 architectural approaches with trade-offs:

```
**Option A: [Name]**
[2-3 sentences: how it works]
Trade-off: [pro] vs [con]

**Option B: [Name]**
[2-3 sentences]
Trade-off: [pro] vs [con]
```

Ask: "Which direction, or should I explore a hybrid?"

If the choice is obvious (one option clearly dominates), say so and ask for confirmation rather than forcing a false choice.

### 5. Write the Design Document

Create `docs/design-plans/YYYY-MM-DD-{slug}.md`:

```markdown
# [Feature Name] Design

## Summary
[2-3 sentences]

## Definition of Done
[Confirmed DoD from step 2]

## Acceptance Criteria

### {slug}.AC1: [Criterion Group]
- **{slug}.AC1.1 Success:** [what passing looks like]
- **{slug}.AC1.2 Failure:** [what rejection looks like]

### {slug}.AC2: [Criterion Group]
...

## Architecture
[Chosen approach from step 4, elaborated]

## Existing Patterns
[What codebase investigation revealed — patterns to follow]

## Implementation Phases

### Phase 1: [Title]
**Goal:** [one sentence]
**Components:** [files/dirs]
**Done when:** [subset of ACs]

### Phase 2: [Title]
...

(Maximum 8 phases. If more are needed, split into multiple design docs.)

## Glossary
[Key terms, especially domain-specific ones]
```

**AC rules:**
- Generate both success and failure cases for each criterion
- Present ACs to user for validation before committing
- Use the full scoped identifier format

Commit the design doc. **Run from `$WORKTREE_PATH` if provided** so the commit lands on the feature branch:

```bash
cd "${WORKTREE_PATH:-$REPO_ROOT}"
git add docs/design-plans/
git commit -m "docs: design plan for [slug]"
```

### 6. Hand Off

```
Design complete: docs/design-plans/[filename]
Worktree: [WORKTREE_PATH if provided, else "(none — created at /plan time)"]

Next: /jackal-impl-plan docs/design-plans/[filename]
```

No /clear needed. `jackal-impl-plan` reads the `## Worktree` block from the issue doc and reuses the existing worktree.

---

## Guidance Files

Check for `.jackal/design-guidance.md` or `.ed3d/design-plan-guidance.md` in the project root. If found, read it before step 2 — it contains project-specific terminology, constraints, and preferences.

---

## When to Go Backward

- Brainstorming reveals DoD is unclear → re-confirm DoD
- Writing ACs reveals architectural gap → re-brainstorm
- User questions an assumption → investigate more

Don't force linear progression when backtracking gives better results.
