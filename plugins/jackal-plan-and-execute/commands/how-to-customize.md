---
description: Explains how to customize design and implementation plans with project-specific guidance
---

Read back the below information EXACTLY AND VERBATIM. Do not summarize. AFTER you have repeated it verbatim, you may suggest starting points to the user based on your understanding of the project you are operating in. After suggesting those starting points, suggest that you could go read CLAUDE.md and AGENTS.md files in subdirectories to further expand on the customization suggestions that may be appropriate.

# Customizing Plan-and-Execute

You can provide project-specific guidance that shapes how design and implementation plans are created for your project.

## Guidance Files

Create a `.ed3d/` directory in your project root with these optional files:

### `.ed3d/design-plan-guidance.md`

Loaded before the clarification phase of `/start-design-plan`.

**What to include:**
- **Domain terminology**: Define terms specific to your project
- **Architectural constraints**: Required patterns, forbidden approaches
- **Technology preferences**: What to use, what to avoid
- **Stakeholder context**: Who cares about what
- **Scope boundaries**: What's typically in/out of scope

### `.ed3d/implementation-plan-guidance.md`

Loaded when starting an implementation plan and again during the final all-phase code review.

**What to include:**
- **Coding standards**: Naming conventions, file organization
- **Testing requirements**: Coverage expectations, testing patterns
- **Review criteria**: Quality gates beyond the defaults
- **Commit conventions**: Message format, granularity
- **Project-specific patterns**: How things are done here

## Example Files

### `.ed3d/design-plan-guidance.md`

```markdown
# Design Guidance for MyProject

## Domain Terms
- **Widget**: User-configurable dashboard component (not a generic UI element)
- **Pipeline**: BullMQ-based async job system

## Architectural Constraints
- All services use FCIS pattern (functional core, imperative shell)
- Database access only through repository pattern in `src/repositories/`
- No direct HTTP calls from business logic

## Technology Stack
- **Required**: TypeScript strict mode, PostgreSQL, Redis
- **Avoid**: ORMs (we use raw SQL with type generation)
- **Decided**: Auth0 for authentication (don't propose alternatives)

## Scope Defaults
- Admin UI is always out of scope unless explicitly requested
- Migrations are in scope for any schema changes
```

### `.ed3d/implementation-plan-guidance.md`

```markdown
# Implementation Guidance for MyProject

## Coding Standards
- All files must have FCIS pattern comment at top
- Prefer `type` over `interface` unless extending
- No default exports

## Testing Requirements
- Unit tests for all pure functions
- Integration tests for repository methods
- E2E tests only for critical user flows
- Test files colocated as `*.test.ts`

## Review Criteria
- No `any` types without justification comment
- All database queries must use parameterized statements
- Error messages must not leak internal details

## Commit Conventions
- Conventional commits: feat:, fix:, chore:, docs:
- One logical change per commit
- Tests and implementation in same commit
```

## Notes

- If the guidance files don't exist, the standard workflow proceeds without them
- Guidance is incorporated into context, not shown to you directly
- Update guidance files as your project evolves
