---
name: writing-skills
description: Use when creating new skills, editing existing skills, or verifying skills work before deployment - applies TDD to process documentation by testing with subagents before writing, iterating until bulletproof against rationalization
---

# Writing Skills

**REQUIRED BACKGROUND:** Read ed3d-extending-claude:writing-claude-directives for foundational guidance on token efficiency, discovery optimization, and compliance techniques. This skill focuses on TDD methodology specific to skill creation.

## Core Principle

**Writing skills IS Test-Driven Development applied to process documentation.**

Write test cases (pressure scenarios), watch them fail (baseline behavior), write the skill, watch tests pass, refactor (close loopholes).

**Iron Law:** No skill without a failing test first. Same as TDD for code.

## TDD Mapping

| TDD Concept | Skill Creation |
|-------------|----------------|
| Test case | Pressure scenario with subagent |
| Production code | SKILL.md document |
| RED | Agent violates rule without skill |
| GREEN | Agent complies with skill present |
| Refactor | Close loopholes, re-test |

## When to Create a Skill

**Create when:**
- Technique wasn't intuitively obvious
- You'd reference this across projects
- Pattern applies broadly
- Others would benefit

**Don't create for:**
- One-off solutions
- Standard practices documented elsewhere
- Project-specific conventions (use CLAUDE.md)

## Skill Types

**Technique:** Concrete method with steps (condition-based-waiting, root-cause-tracing)

**Pattern:** Mental model for problems (flatten-with-flags, test-invariants)

**Reference:** API docs, syntax guides, tool documentation

## Directory Structure

```
skills/
  skill-name/
    SKILL.md              # Main reference (required)
    supporting-file.*     # Only if needed
```

**Separate files for:** Heavy reference (100+ lines), reusable tools/scripts

**Keep inline:** Principles, code patterns (<50 lines), everything else

## SKILL.md Template

```markdown
---
name: Skill-Name-With-Hyphens
description: Use when [triggers/symptoms] - [what it does, third person]
---

# Skill Name

## Overview
Core principle in 1-2 sentences.

## When to Use
Symptoms and use cases. When NOT to use.

## Core Pattern
Before/after comparison or key technique.

## Quick Reference
Table or bullets for scanning.

## Common Mistakes
What goes wrong + fixes.
```

## RED-GREEN-REFACTOR Cycle

### RED: Baseline Test

Run pressure scenario WITHOUT skill:
1. Create combined pressures (time + sunk cost + exhaustion)
2. Document exact violations and rationalizations verbatim
3. Identify failure patterns

### GREEN: Write Minimal Skill

1. Address specific baseline failures identified in RED
2. Run scenarios WITH skill
3. Verify compliance

### REFACTOR: Close Loopholes

1. Find NEW rationalizations from testing
2. Add explicit counters
3. Re-test until bulletproof

**REQUIRED:** Use ed3d-extending-claude:testing-skills-with-subagents for complete methodology.

## Testing by Skill Type

| Type | Test Approach | Success Criteria |
|------|---------------|------------------|
| Discipline | Pressure scenarios, combined stressors | Follows rule under maximum pressure |
| Technique | Application scenarios, edge cases | Successfully applies to new scenario |
| Pattern | Recognition + counter-examples | Knows when/how and when NOT to apply |
| Reference | Retrieval + application tests | Finds and correctly uses information |

## Common Rationalizations to Block

| Excuse | Reality |
|--------|---------|
| "Obviously clear" | Clear to you ≠ clear to agents. Test. |
| "Just a reference" | References have gaps. Test retrieval. |
| "Testing is overkill" | Untested skills have issues. Always. |
| "Too simple" | Simple things break. Test anyway. |
| "No time" | Fixing broken skills wastes more time. |

**All mean: Test before deploying.**

## Anti-Patterns

- **Narrative example:** "In session 2025-10-03, we found..." (too specific, not reusable)
- **Multi-language dilution:** example-js.js, example-py.py (mediocre quality, maintenance burden)
- **Code in flowcharts:** Can't copy-paste, hard to read
- **Generic labels:** helper1, step3 (labels need semantic meaning)

## Skill Creation Checklist

**IMPORTANT:** Use TaskCreate to track each item (or TodoWrite in older Claude Code versions).

**RED Phase:**
- [ ] Create pressure scenarios (3+ combined pressures for discipline skills)
- [ ] Run WITHOUT skill - document baseline failures verbatim
- [ ] Identify rationalization patterns

**GREEN Phase:**
- [ ] Name uses letters, numbers, hyphens only
- [ ] Description starts with "Use when...", third person
- [ ] Address specific baseline failures
- [ ] One excellent example (not multi-language)
- [ ] Run WITH skill - verify compliance

**REFACTOR Phase:**
- [ ] Identify new rationalizations
- [ ] Add explicit counters
- [ ] Re-test until bulletproof

**Deployment:**
- [ ] Commit and push
- [ ] Consider contributing via PR
