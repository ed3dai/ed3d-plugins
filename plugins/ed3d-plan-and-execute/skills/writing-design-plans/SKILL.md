---
name: writing-design-plans
description: Use after brainstorming completes - writes validated designs to docs/design-plans/ with structured format and discrete implementation phases required for creating detailed implementation plans
---

# Writing Design Plans

## Overview

Complete the design document by appending validated design from brainstorming to the existing file (created in Phase 3 of starting-a-design-plan) and filling in the Summary and Glossary placeholders.

**Core principle:** Append body to existing document. Generate Summary and Glossary. Commit for permanence.

**Announce at start:** "I'm using the writing-design-plans skill to complete the design document."

**Context:** Design document already exists with Title, Summary placeholder, confirmed Definition of Done, and Glossary placeholder. This skill appends the body and fills in placeholders.

## Level of Detail: Design vs Implementation

**Design plans are directional and archival.** They can be checked into git and referenced months later. Other design plans may depend on contracts specified here.

**Implementation plans are tactical and just-in-time.** They verify current codebase state and generate executable code immediately before execution.

**What belongs in design plans:**

| Include | Exclude |
|---------|---------|
| Module and directory structure | Task-level breakdowns |
| Component names and responsibilities | Implementation code |
| File paths (from investigation) | Function bodies |
| Dependencies between components | Step-by-step instructions |
| "Done when" verification criteria | Test code |

**Exception: Contracts get full specification.** When a component exposes an interface that other systems depend on, specify the contract fully:

- API endpoints with request/response shapes
- Inter-service interfaces (types, method signatures)
- Database schemas that other systems read
- Message formats for queues/events

Contracts can include code blocks showing types and interfaces. This is different from implementation code — contracts define boundaries, not behavior.

**Example — Contract specification (OK):**
```typescript
interface TokenService {
  generate(claims: TokenClaims): Promise<string>;
  validate(token: string): Promise<TokenClaims | null>;
}

interface TokenClaims {
  sub: string;      // service identifier
  aud: string[];    // allowed audiences
  exp: number;      // expiration timestamp
}
```

**Example — Implementation code (NOT OK for design plans):**
```typescript
async function generate(claims: TokenClaims): Promise<string> {
  const payload = { ...claims, iat: Date.now() };
  return jwt.sign(payload, config.secret, { algorithm: 'RS256' });
}
```

The first defines what the boundary looks like. The second implements behavior — that belongs in implementation plans.

## File Location and Naming

**File location:** `docs/design-plans/YYYY-MM-DD-<topic>.md`

The file is created by starting-a-design-plan Phase 3. This skill appends to that file.

**Expected naming convention:**
- Good: `docs/design-plans/2025-01-18-oauth2-service-auth.md`
- Good: `docs/design-plans/2025-01-18-user-profile-redesign.md`
- Bad: `docs/design-plans/design.md`
- Bad: `docs/design-plans/new-feature.md`

## Document Structure

**The design document already exists** from Phase 3 of starting-a-design-plan with this structure:

```markdown
# [Feature Name] Design

## Summary
<!-- TO BE GENERATED after body is written -->

## Definition of Done
[Already written - confirmed in Phase 3]

## Glossary
<!-- TO BE GENERATED after body is written -->
```

**This skill appends the body sections:**

```markdown
## Architecture
[Approach selected in brainstorming Phase 2]

[Key components and how they interact]

[Data flow and system boundaries]

## Existing Patterns
[Document codebase patterns discovered by investigator that this design follows]

[If introducing new patterns, explain why and note divergence from existing code]

[If no existing patterns found, state that explicitly]

## Implementation Phases

Break implementation into discrete phases (<=8 recommended).

**REQUIRED: Wrap each phase in HTML comment markers:**

<!-- START_PHASE_1 -->
### Phase 1: [Name]
**Goal:** What this phase achieves

**Components:** What gets built/modified (exact paths from investigator)

**Dependencies:** What must exist first

**Done when:** How to verify this phase is complete (see Phase Verification below)
<!-- END_PHASE_1 -->

<!-- START_PHASE_2 -->
### Phase 2: [Name]
[Same structure]
<!-- END_PHASE_2 -->

...continue for each phase...

**Why markers:** These enable writing-implementation-plans to parse phases individually, reducing context usage and enabling granular task tracking across compaction boundaries.

## Additional Considerations
[Error handling, edge cases, future extensibility - only if relevant]

[Don't include hypothetical "nice to have" features]
```

**Then this skill generates** Summary and Glossary to replace the placeholders.

## Legibility Header

The first three sections (Summary, Definition of Done, Glossary) form the **legibility header**. These sections help human reviewers quickly understand what the document is about before diving into technical details.

**Definition of Done is already written** — it was captured in Phase 3 immediately after user confirmation, preserving full fidelity.

**Summary and Glossary are generated AFTER writing the body.** This avoids summarizing something that hasn't been written yet and ensures they accurately reflect the full document.

See "After Writing: Generating Summary and Glossary" below for the extraction process.

## Implementation Phases: Critical Requirements

**YOU MUST break design into discrete, sequential phases.**

**Each phase should:**
- Achieve one cohesive goal
- Build on previous phases (explicit dependencies)
- End with a working build and clear "done" criteria
- Use exact file paths and component names from codebase investigation

## Phase Verification

**Verification depends on what the phase delivers:**

| Phase Type | Done When | Examples |
|------------|-----------|----------|
| Infrastructure/scaffolding | Operational success | Project installs, builds, runs, deploys |
| Functionality/behavior | Tests pass for new behavior | Unit tests, integration tests, E2E tests |

**The rule:** If a phase adds code that implements behavior, that phase includes tests proving the behavior works. Tests are a deliverable of the phase, not a separate "testing phase" later.

**Don't over-engineer infrastructure verification.** You don't need unit tests for package.json. "npm install succeeds" is sufficient verification for a dependency setup phase.

**Do require tests for functionality.** Any code that does something needs tests that prove it does that thing. These tests are part of the phase, not deferred.

**Tests can evolve.** A test written in Phase 2 may be modified in Phase 4 as requirements expand. This is expected. The constraint is that Phase 2 ends with passing tests for what Phase 2 delivers.

**Structure phases as subcomponents.** A phase may contain multiple logical subcomponents. List them at the component level — the implementation plan will break these into tasks.

Good structure (component-level):
```
<!-- START_PHASE_2 -->
### Phase 2: Core Services
**Goal:** Token generation and session management

**Components:**
- TokenService in `src/services/auth/` — generates and validates JWT tokens
- SessionManager in `src/services/auth/` — creates, validates, and invalidates sessions
- Types in `src/types/auth.ts` — TokenClaims, SessionData interfaces

**Dependencies:** Phase 1 (project setup)

**Done when:** Token generation/validation works, sessions can be created/invalidated, all tests pass
<!-- END_PHASE_2 -->
```

Bad structure (task-level — this belongs in implementation plans):
```
Phase 2: Core Services
- Task 1: TokenPayload type and TokenConfig
- Task 2: TokenService implementation
- Task 3: TokenService tests
- Task 4: SessionManager implementation
- Task 5: SessionManager tests
```

Design plans describe WHAT gets built. Implementation plans describe HOW to build it step-by-step.

**Phase count:**
- Target: 5-8 phases (sweet spot for planning)
- Maximum: 8 phases (hard limit for writing-plans skill)
- If >8 phases needed: Note that multiple implementation plans will be required

**Why <=8 phases matters:**
- writing-plans skill has hard limit of 8 phases per implementation plan
- Exceeding 8 phases forces user to scope or split
- This is by design to prevent overwhelming implementation plans

**If design needs >8 phases:**

Add note to Additional Considerations:
```markdown
## Additional Considerations

**Implementation scoping:** This design has [N] phases total. The writing-plans skill limits implementation plans to 8 phases. Consider:
1. Implementing first 8 phases in initial plan
2. Creating second implementation plan for remaining phases
3. Simplifying design to fit within 8 phases
```

## Using Codebase Investigation Findings

**Include paths and component descriptions from investigation. Do NOT include implementation details.**

Good Phase definitions:

**Infrastructure phase example:**
```markdown
<!-- START_PHASE_1 -->
### Phase 1: Project Setup
**Goal:** Initialize project structure and dependencies

**Components:**
- `package.json` with auth dependencies (jsonwebtoken, bcrypt)
- `tsconfig.json` with strict mode
- `src/index.ts` entry point

**Dependencies:** None (first phase)

**Done when:** `npm install` succeeds, `npm run build` succeeds
<!-- END_PHASE_1 -->
```

**Functionality phase example:**
```markdown
<!-- START_PHASE_2 -->
### Phase 2: Token Generation Service
**Goal:** JWT token generation and validation for service-to-service auth

**Components:**
- TokenService in `src/services/auth/` — generates signed JWTs, validates signatures and expiration
- TokenValidator in `src/services/auth/` — middleware-friendly validation that returns claims or rejects

**Dependencies:** Phase 1 (project setup)

**Done when:** Tokens can be generated, validated, and rejected when invalid/expired
<!-- END_PHASE_2 -->
```

Bad Phase definitions:

**Too vague:**
```markdown
### Phase 1: Authentication
**Goal:** Add auth stuff
**Components:** Auth files
**Dependencies:** Database maybe
```

**Too detailed (task-level):**
```markdown
### Phase 2: Token Service
**Components:**
- Create `src/types/token.ts` with TokenClaims interface
- Create `src/services/auth/token-service.ts` with generate() and validate()
- Create `tests/services/auth/token-service.test.ts`
- Step 1: Write failing test for generate()
- Step 2: Implement generate()
- Step 3: Write failing test for validate()
...
```

The second example is doing implementation planning's job. Design plans stay at component level.

## Writing Style

**REQUIRED SUB-SKILL:** Use house-style:writing-for-a-technical-audience if available.

Otherwise follow these guidelines:

**Be concise:**
- Remove throat-clearing
- State facts directly
- Skip obvious explanations

**Be specific:**
- Use exact component names
- Reference actual file paths
- Include concrete examples

**Be honest:**
- Acknowledge unknowns
- State assumptions explicitly
- Don't over-promise

**Example - Good:**
```markdown
## Architecture

Service-to-service authentication using OAuth2 client credentials flow.

Auth service (`src/services/auth/`) generates and validates JWT tokens. API middleware (`src/api/middleware/auth.ts`) validates tokens on incoming requests. Token store (`src/data/token-store.ts`) maintains revocation list in PostgreSQL.

Tokens expire after 1 hour. Refresh not needed for service accounts (can request new token).
```

**Example - Bad:**
```markdown
## Architecture

In this exciting new architecture, we'll be implementing a robust and scalable authentication system that leverages the power of OAuth2! The system will be designed with best practices in mind, ensuring security and performance at every level. We'll use industry-standard JWT tokens that provide excellent flexibility and are widely supported across the ecosystem. This will integrate seamlessly with our existing infrastructure and provide a solid foundation for future enhancements!
```

## Existing Patterns Section

**Purpose:** Document what codebase investigation revealed.

**Include:**
- Patterns this design follows from existing code
- Why those patterns were chosen (if known)
- Any divergence from existing patterns with justification

**If following existing patterns:**
```markdown
## Existing Patterns

Investigation found existing authentication in `src/services/legacy-auth/`. This design follows the same service structure:
- Service classes in `src/services/<domain>/`
- Middleware in `src/api/middleware/`
- Data access in `src/data/`

Token storage follows pattern from `src/data/session-store.ts` (PostgreSQL with TTL).
```

**If no existing patterns:**
```markdown
## Existing Patterns

Investigation found no existing authentication implementation. This design introduces new patterns:
- Service layer for business logic (`src/services/`)
- Middleware for request interception (`src/api/middleware/`)

These patterns align with functional core, imperative shell separation.
```

**If diverging from existing patterns:**
```markdown
## Existing Patterns

Investigation found legacy authentication in `src/auth/`. This design diverges:
- OLD: Monolithic `src/auth/auth.js` (600 lines, mixed concerns)
- NEW: Separate services (`token-service.ts`, `validator.ts`) following FCIS

Divergence justified by: Legacy code violates FCIS pattern, difficult to test, high coupling.
```

## Additional Considerations

**Only include if genuinely relevant:**

**Error handling** - if not obvious:
```markdown
## Additional Considerations

**Error handling:** Token validation failures return 401 with generic message (don't leak token details). Service-to-service communication failures retry 3x with exponential backoff before returning 503.
```

**Edge cases** - if non-obvious:
```markdown
**Edge cases:** Clock skew handled by 5-minute token validation window. Revoked tokens remain in database for 7 days for audit trail.
```

**Future extensibility** - if architectural decision enables future features:
```markdown
**Future extensibility:** Token claims structure supports adding user metadata (currently unused). Enables future human user authentication without architecture change.
```

**Do NOT include:**
- "Nice to have" features not in current design
- Hypothetical future requirements
- Generic platitudes ("should be secure", "needs good testing")

## After Writing: Generating Summary and Glossary

After appending the body (Architecture through Additional Considerations), generate Summary and Glossary using a subagent with fresh context.

**Why a subagent?**
- Fresh context avoids "context rot" from the long brainstorming/writing session
- Acts as a forcing function: if the subagent can't extract a coherent summary, the document is unclear
- Mirrors the experience of a human reviewer seeing the document for the first time

**Step 1: Append the body first**

The document already exists with Definition of Done. Append the body sections:

```markdown
# [Feature Name] Design

## Summary
<!-- TO BE GENERATED after body is written -->

## Definition of Done
[Already written from Phase 3]

## Glossary
<!-- TO BE GENERATED after body is written -->

## Architecture
[... append actual content ...]

## Existing Patterns
[... append actual content ...]

## Implementation Phases
[... append actual content ...]

## Additional Considerations
[... append actual content ...]
```

**Step 2: Dispatch extraction subagent**

Use the Task tool to generate Summary and Glossary:

```
<invoke name="Task">
<parameter name="subagent_type">ed3d-basic-agents:sonnet-general-purpose</parameter>
<parameter name="description">Generating Summary and Glossary for design document</parameter>
<parameter name="prompt">
Read the design document at [file path].

Generate two sections to replace the placeholders in the document:

1. **Summary**: Write 1-2 paragraphs summarizing what is being built and the
   high-level approach. This should be understandable to someone unfamiliar
   with the codebase. The Definition of Done section already exists — your
   summary should complement it by explaining the "how" rather than restating
   the "what."

2. **Glossary**: List domain terms from the application and third-party concepts
   (libraries, frameworks, patterns) that a reviewer needs to understand this
   document. Format as:
   - **[Term]**: [Brief explanation]

   Include only terms that appear in the document and would benefit from
   explanation.

3. **Omitted Terms**: List terms you considered but skipped as too obvious or
   generic. Only include borderline cases — terms that a less technical reviewer
   might not know. Format as a simple comma-separated list.

Return all three sections. The first two are markdown ready to insert; the
third is for transparency about what was excluded.
</parameter>
</invoke>
```

**Step 3: Review omitted terms with user**

Before inserting the extracted sections, briefly mention the omitted terms to the user:

"Glossary includes [X terms]. Omitted as likely obvious: [list from subagent]. Let me know if any of those should be included."

Don't wait for approval — proceed to insert the sections. The user can hit escape and ask for adjustments if needed.

**Step 4: Replace placeholders**

Replace the Summary and Glossary placeholder comments with the subagent's output. Do not insert the Omitted Terms section — that was for your transparency message only.

**Step 5: Review and adjust**

Briefly review the generated sections for accuracy. The subagent may miss nuance from the conversation — adjust if needed, but prefer the subagent's version when it's accurate (it reflects what the document actually says, not what you remember).

## After Summary and Glossary: Commit

**Commit the design document:**

```bash
git add docs/design-plans/YYYY-MM-DD-<topic>.md
git commit -m "$(cat <<'EOF'
docs: add [feature name] design plan

Completed brainstorming session. Design includes:
- [Key architectural decision 1]
- [Key architectural decision 2]
- [N] implementation phases
EOF
)"
```

**Announce completion:**

"Design plan documented in `docs/design-plans/YYYY-MM-DD-<topic>.md` and committed."

## Common Rationalizations - STOP

| Excuse | Reality |
|--------|---------|
| "I'll write the summary first since I know what I'm building" | Write body first. Summarize what you wrote, not what you planned. |
| "I can write Summary and Glossary myself, don't need subagent" | Subagent has fresh context and acts as forcing function. Use it. |
| "Glossary isn't needed, terms are obvious" | Obvious to you after brainstorming. Not to fresh reviewer. Include it. |
| "Design is simple, don't need phases" | Phases make implementation manageable. Always include. |
| "Phases are obvious, don't need detail" | writing-plans needs component descriptions. Provide them. |
| "Can have 10 phases if needed" | Hard limit is 8. Scope or split. |
| "I'll include the code so implementation is easier" | No. Implementation plans generate code fresh from codebase state. Design provides direction only. |
| "Breaking into tasks helps the reader" | Task breakdown is implementation planning's job. Design stays at component level. |
| "I'll just show how the function works" | Implementation code doesn't belong in design. Show contracts/interfaces if needed, not function bodies. |
| "Additional considerations should be comprehensive" | Only include if relevant. YAGNI applies. |
| "Should document all future possibilities" | Document current design only. No hypotheticals. |
| "Existing patterns section can be skipped" | Shows investigation happened. Always include. |
| "Can use generic file paths" | Exact paths from investigation. No handwaving. |
| "Tests can be a separate phase at the end" | No. Tests for functionality belong in the phase that creates that functionality. |
| "We'll add tests after the code works" | Phase isn't done until its tests pass. Tests are deliverables, not afterthoughts. |
| "Infrastructure needs unit tests too" | No. Infrastructure verified operationally. Don't over-engineer. |
| "Phase 3 tests will cover Phase 2 code" | Each phase tests its own deliverables. Later phases may extend tests, but don't defer. |
| "Phase markers are just noise" | Markers enable granular parsing. Implementation planning depends on them. Always include. |

**All of these mean: STOP. Follow the structure exactly.**

## Integration with Workflow

This skill completes the design document started in Phase 3:

```
Phase 3 (Definition of Done) completes
  -> User confirms Definition of Done
  -> File created with Title, Summary placeholder, DoD, Glossary placeholder
  -> DoD captured at full fidelity

Brainstorming (Phase 4) completes
  -> Validated design exists in conversation
  -> User approved incrementally

Writing Design Plans (this skill)
  -> Append body: Architecture, Existing Patterns, Implementation Phases
  -> Add exact paths from investigation
  -> Create discrete phases (<=8)
  -> Dispatch subagent to generate Summary and Glossary
  -> Replace placeholders with generated content
  -> Commit to git

Writing Plans (next step)
  -> Reads this design document
  -> Uses phases as basis for detailed tasks
  -> Expects exact paths and structure
```

**Purpose:** Create contract between design and implementation. Writing-plans relies on this structure. The legibility header ensures human reviewers can quickly understand the document.
