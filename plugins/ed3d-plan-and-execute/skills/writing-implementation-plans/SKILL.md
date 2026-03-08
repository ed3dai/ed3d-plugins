---
name: writing-implementation-plans
description: Use when design is complete and you need detailed implementation tasks for engineers with zero codebase context - creates comprehensive implementation plans with exact file paths, complete code examples, and verification steps assuming engineer has minimal domain knowledge
user-invocable: false
---

# Writing Implementation Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to verify it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. Frequent commits.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

**Announce at start:** "I'm using the writing-implementation-plans skill to create the implementation plan."

**Save plans to:** `docs/implementation-plans/YYYY-MM-DD-<feature-name>/phase_##.md`

## Critical: Design Plans Provide Direction, Not Code

**Design plans are intentionally high-level.** They describe components, modules, and contracts — not implementation code. This is by design.

**You MUST generate code fresh based on codebase investigation.** Do NOT copy code from the design document. Even if a design plan contains code examples (it shouldn't, but some might), treat them as illustrative only.

**Why this matters:**
- Design plans may be days or weeks old
- Codebase state changes between design and implementation
- Investigation reveals actual patterns, dependencies, and constraints
- Your code must work with the codebase as it exists NOW

**The design plan tells you WHERE you're going. Codebase investigation tells you HOW to get there from where you are.**

## Before Starting

**REQUIRED: Verify scope and codebase state**

### 1. Scope Validation

Count the phases/tasks in the design plan.

**If design plan has >8 phases:** STOP. Refuse to proceed.

Tell the user:
"This design has [N] phases, which exceeds the 8-phase limit for implementation plans. Please rerun this skill with a scope of no more than 8 phases. You can:
1. Select the first 8 phases for this implementation plan
2. Break the design into multiple implementation plans
3. Simplify the design to fit within 8 phases"

**If already implementing phases 9+:** The user should provide the previous implementation plan as context when scoping the next batch.

### 2. Review Mode Selection

**After scope validation, ask how to handle phase reviews:**

Use AskUserQuestion:
```
Question: "How would you like to review the implementation plan phases?"
Options:
  - "Write all phases to disk, I'll review afterwards"
  - "Review each phase interactively before writing"
```

**Track this choice - it affects the per-phase workflow below.**

### 3. Codebase Verification

**You MUST verify current codebase state before EACH AND EVERY PHASE. Use `codebase-investigator` to prove out your hypotheses and to ensure that current state aligns with what you want to write out.**

**YOU MUST verify current codebase state before writing ANY task.**

**DO NOT verify codebase yourself. Use codebase-investigator agent.**

**Provide the agent with design assumptions so it can report discrepancies:**

Dispatch one subagent codebase-investigator to understand testing behavior for this project.
- **DO NOT prescribe new requirements around testing. Follow how the codebase does it.**
   - For example: do NOT stipulate TDD unless you understand the scope of the problem to be a predominantly functional one OR you receive direction from a human otherwise and do not assume that mocking databases or other external dependencies is acceptable. 
- If you find problems that are difficult to test in isolation with mocks, you should surface questions to the human operator as to how they want to proceed.
- Instruct the subagent to seek out CLAUDE.md or AGENTS.md files that include details on testing behavior, logic, and methodology, and include file references for you to provide in your plan for the executor to pass to its subagents.

Dispatch a second subagent codebase-investigator (simultaneously) with:
- "The design assumes these files exist: [list with expected paths/structure from design]"
- "Verify each file exists and report any differences from these assumptions"
- "The design says [feature] is implemented in [location]. Verify this is accurate"
- "Design expects [dependency] version [X]. Check actual version installed"

**Example query to agent:**
```
Design assumptions from docs/plans/YYYY-MM-DD-feature-design.md:
- Auth service in src/services/auth.ts with login() and logout() functions
- User model in src/models/user.ts with email and password fields
- Test file at tests/services/auth.test.ts
- Uses bcrypt dependency for password hashing

Verify these assumptions and report:
1. What exists vs what design expects
2. Any structural differences (different paths, functions, exports)
3. Any missing or additional components
4. Current dependency versions
```

Review investigator findings and note any differences from design assumptions.

**Based on investigator report, NEVER write:**
- "Update `index.js` if exists"
- "Modify `config.py` (if present)"
- "Create or update `types.ts`"

**Based on investigator report, ALWAYS write:**
- "Create `src/auth.ts`" (investigator confirmed doesn't exist)
- "Modify `src/index.ts:45-67`" (investigator confirmed exists, checked line numbers)
- "No changes needed to `config.py`" (investigator confirmed already correct)

**If codebase state differs from design assumptions:** Document the difference and adjust the implementation plan accordingly.

### 4. External Dependency Research

**When phases involve external libraries or dependencies, research them before writing tasks.**

Use a tiered approach—start with documentation, escalate to source code only when needed.

#### Tier 1: Internet Researcher (default)

Use `internet-researcher` for:
- Official documentation and API references
- Common usage patterns and examples
- Standard specifications (OAuth2, JWT, HTTP, etc.)
- Best practices and known gotchas

**This handles ~80% of external dependency questions.** Most integration work follows documented patterns.

#### Tier 2: Remote Code Researcher (escalation)

Use `remote-code-researcher` when:
- Documentation doesn't cover your edge case
- You need to understand internal implementation for extension/customization
- Docs describe *what* but you need to know *how*
- Behavior differs from docs and you need ground truth
- You're extending or hooking into library internals

#### Decision Framework

```
Phase involves external dependency?
├─ No → codebase-investigator only
└─ Yes → What do we need to know?
    ├─ API usage, standard patterns → internet-researcher
    ├─ Standard/spec implementation → internet-researcher
    ├─ Implementation internals, extension points → remote-code-researcher
    └─ Both local state + external info → combined-researcher
```

#### When to Dispatch

**Dispatch internet-researcher when phase mentions:**
- External packages/libraries to integrate
- Third-party APIs to call
- Standards to implement (OAuth, JWT, OpenAPI, etc.)

**Escalate to remote-code-researcher when:**
- Internet-researcher returns "docs don't cover this"
- Task requires extending library behavior
- Task requires matching internal patterns not in docs
- You need to understand error handling, edge cases, or internals

#### Reporting Findings

Include external research findings alongside codebase verification:

```markdown
**External dependency investigation findings:**
- ✓ Stripe SDK uses `stripe.customers.create()` with params: {email, name, metadata}
- ✓ OAuth2 refresh flow per RFC 6749 Section 6
- ✗ Design assumed sync API, but library is async-only
- + Error handling uses typed exception hierarchy (StripeError subclasses)
- 📖 Source: [Official docs | RFC spec | Source code @ commit]
```

**Standards vs Implementation:** Standards questions (e.g., "how does OAuth2 work") are internet-researcher territory. Implementation questions (e.g., "how does auth0-js store tokens") may require remote-code-researcher.

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes).**

For functionality tasks:
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

For infrastructure tasks:
- "Create the config file" - step
- "Verify it works (install, build, run)" - step
- "Commit" - step

**Task dependencies MUST be explicit and sequential:**
- Task N requires helper function? Task N-1 creates it.
- Task N requires bootstrap credentials? Prior task provisions them.
- Never write code that assumes "this will exist somehow."

## Task Types: Infrastructure vs Functionality

**Match task structure to what the design phase specifies.**

The design plan distinguishes between infrastructure phases (verified operationally) and functionality phases (verified by tests). Your implementation tasks must honor this distinction.

| Phase Type | Task Structure | Verification |
|------------|----------------|--------------|
| Infrastructure | Create files, configure, verify operationally | Commands succeed (install, build, run) |
| Functionality | Write tests, implement, verify tests pass | Tests pass for the behavior |

**Infrastructure tasks** (project setup, config files, dependencies):
- Don't force TDD on scaffolding
- Verification = operational success
- "npm install succeeds" is valid verification
- **Verifies: None** — explicitly state this, don't invent ACs for setup phases

**Functionality tasks** (code that does something):
- Tests are deliverables alongside code
- Each task lists which ACs it verifies (e.g., "Verifies: AC1.1, AC1.3")
- Tests must verify those specific AC cases, not just "test the code"
- Phase ends with passing tests for all ACs listed in the phase's AC Coverage

**Test behavior, not implementation.**
- Test that your function produces the right output, not that it called dependencies a certain way
- If you refactored internals but behavior stayed the same, would the test still pass? If no, you're testing implementation details.
- The AC is the spec: "Invalid password returns 401" means test the response, not verify that `bcrypt.compare()` was called

**What doesn't need tests:**
- Types (TypeScript compiler verifies these)
- Dependencies that have their own tests (don't re-test them through your code)
- How you call things (test the result, not the wiring)
- Infrastructure/setup (verify operationally)

**Subcomponent task grouping.** Design plans structure phases as subcomponents: types → implementation → tests. When writing tasks for a subcomponent, wrap them in subcomponent markers (see "Task and Subcomponent Markers" section):

```markdown
<!-- START_SUBCOMPONENT_A (tasks 1-3) -->
<!-- START_TASK_1 -->
### Task 1: TokenPayload type and TokenConfig
...
<!-- END_TASK_1 -->

<!-- START_TASK_2 -->
### Task 2: TokenService implementation
...
<!-- END_TASK_2 -->

<!-- START_TASK_3 -->
### Task 3: TokenService tests
...
<!-- END_TASK_3 -->
<!-- END_SUBCOMPONENT_A -->
```

The execution agent uses these markers to identify related tasks. The tests task proves the subcomponent works.

**Read the design plan's "Done when" section.** If it says "build succeeds," don't invent unit tests. If it says "tests pass for X," ensure tasks produce those tests.

## Plan Document Header

**Every plan phase document MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

**Scope:** [N] phases from original design (phases [X-Y] if partial implementation)

**Codebase verified:** [Date/time of verification]

---

## Acceptance Criteria Coverage

This phase implements and tests:

### {slug}.AC1: [Criterion heading from design plan]
- **{slug}.AC1.1 Success:** [Copied literally from design plan]
- **{slug}.AC1.3 Failure:** [Copied literally from design plan]

### {slug}.AC2: [Criterion heading from design plan]
- **{slug}.AC2.1 Success:** [Copied literally from design plan]

---
```

**AC Coverage rules:**
- Copy AC text literally from the design plan—do not paraphrase
- Use the full scoped AC identifier (e.g., `oauth2-svc-authn.AC1.1`), not bare `AC1.1`
- Include ONLY the ACs this phase implements and tests
- Include both the criterion heading (`{slug}.AC1`) and the specific cases (`{slug}.AC1.1`, `{slug}.AC1.3`)
- Tasks in this phase must produce tests that verify these specific cases
- An AC case may appear in multiple phases if partially addressed, but final phase must complete it

## Task and Subcomponent Markers

**Wrap every task and subcomponent in HTML comment markers** to enable efficient parsing during execution.

### Task Markers

Every task MUST be wrapped:

```markdown
<!-- START_TASK_1 -->
### Task 1: [Task Name]
...task content...
<!-- END_TASK_1 -->

<!-- START_TASK_2 -->
### Task 2: [Task Name]
...task content...
<!-- END_TASK_2 -->
```

### Subcomponent Markers

When tasks form a logical subcomponent (e.g., types → implementation → tests), wrap the group:

```markdown
<!-- START_SUBCOMPONENT_A (tasks 3-5) -->
<!-- START_TASK_3 -->
### Task 3: TokenService types
...
<!-- END_TASK_3 -->

<!-- START_TASK_4 -->
### Task 4: TokenService implementation
...
<!-- END_TASK_4 -->

<!-- START_TASK_5 -->
### Task 5: TokenService tests
...
<!-- END_TASK_5 -->
<!-- END_SUBCOMPONENT_A -->
```

**Key rules:**
- Tasks are numbered: `START_TASK_1`, `START_TASK_2`, etc.
- Subcomponents use letters: `START_SUBCOMPONENT_A`, `START_SUBCOMPONENT_B`, etc.
- Subcomponent markers MUST include which tasks they contain: `(tasks 3-5)`
- Tasks inside subcomponents still have their own markers
- Standalone tasks (not in a subcomponent) just have task markers

**Why markers:**
- Execution can grep for `START_TASK_` to list all tasks without reading full content
- Execution can extract just the relevant section to pass to task-implementor
- Reduces context usage during execution (especially with experimental workflow)

## Phase-by-Phase Implementation

**Workflow depends on review mode selected above.**

**Step 0: Create granular task tracker with dependencies**

After verifying scope (≤8 phases), use TaskCreate to create granular sub-tasks for EACH phase. This structure survives context compaction.

**CRITICAL: Include absolute paths and set up dependencies.**

Before creating tasks, capture absolute paths:
- `DESIGN_PATH`: Absolute path to design plan (e.g., `/Users/ed/project/docs/design-plans/2025-01-24-feature.md`)
- `PLAN_DIR`: Absolute path to implementation plan directory (e.g., `/Users/ed/project/docs/implementation-plans/2025-01-24-feature/`)
- `SCRATCHPAD_DIR`: Absolute path to temp directory for subagent scratch files (e.g., `/tmp/plan-2025-01-24-feature-a7f3b2/`)

**Generate a unique session ID for SCRATCHPAD_DIR:**

```bash
SESSION_ID=$(printf '%04x%04x' $RANDOM $RANDOM)
echo "/tmp/plan-$(date +%Y-%m-%d)-${slug}-${SESSION_ID}"
```

The session ID (e.g., `a7f3b2`) ensures isolation between:
- Parallel planning sessions with similar slugs
- Retry attempts (if a plan fails and user starts over)

**SCRATCHPAD_DIR ensures session isolation.** Code reviewers and other subagents should write any temp files here, not to shared locations like `/tmp/`.

**Read the Acceptance Criteria section from the design plan.** Acceptance criteria are numbered (AC1, AC1.1, AC1.2, etc.) and define what "done" means. When writing each phase:
1. Identify which ACs this phase implements (look at design phase's "Done when" + component responsibilities)
2. Copy those AC entries literally into the phase's "Acceptance Criteria Coverage" header section
3. Ensure tasks produce tests that verify each listed AC case

**For each phase N, create these tasks with dependencies:**

```markdown
- [ ] Phase NA: Read [Phase Name] from {DESIGN_PATH}
      → blocked by: Phase (N-1)D (or nothing if N=1)
- [ ] Phase NB: Investigate codebase for Phase N and activate relevant skills
      → blocked by: Phase NA
- [ ] Phase NC: Research external deps (Phase N)
      → blocked by: Phase NB
- [ ] Phase ND: Write {PLAN_DIR}/phase_0N.md
      → blocked by: Phase NC
```

**VERBATIM TASK NAMES — DO NOT PARAPHRASE.** Copy task names exactly as shown above. "Investigate codebase for Phase N and activate relevant skills" must include "and activate relevant skills" — that phrase triggers skill activation after compaction. Paraphrasing loses critical instructions.

**After all phase tasks, create finalization task:**

Before creating the Finalization task, check if `.ed3d/implementation-plan-guidance.md` exists. If it does, include its absolute path in the task description:

```markdown
# If .ed3d/implementation-plan-guidance.md exists:
- [ ] Finalization: Run code-reviewer over all phase files (guidance: [absolute path to .ed3d/implementation-plan-guidance.md]), fix ALL issues including minor ones
      → blocked by: all Phase *D tasks

# If .ed3d/implementation-plan-guidance.md does NOT exist:
- [ ] Finalization: Run code-reviewer over all phase files, fix ALL issues including minor ones
      → blocked by: all Phase *D tasks
```

**Example for a 3-phase design at `/Users/ed/project/docs/design-plans/2025-01-24-oauth.md`:**

```
TaskCreate: "Phase 1A: Read Token Types from /Users/ed/project/docs/design-plans/2025-01-24-oauth.md"
TaskCreate: "Phase 1B: Investigate codebase for Phase 1 and activate relevant skills"
  → TaskUpdate: addBlockedBy: [1A]
TaskCreate: "Phase 1C: Research external deps (Phase 1)"
  → TaskUpdate: addBlockedBy: [1B]
TaskCreate: "Phase 1D: Write /Users/ed/project/docs/implementation-plans/2025-01-24-oauth/phase_01.md"
  → TaskUpdate: addBlockedBy: [1C]

TaskCreate: "Phase 2A: Read Token Service from /Users/ed/project/docs/design-plans/2025-01-24-oauth.md"
  → TaskUpdate: addBlockedBy: [1D]
TaskCreate: "Phase 2B: Investigate codebase for Phase 2 and activate relevant skills"
  → TaskUpdate: addBlockedBy: [2A]
TaskCreate: "Phase 2C: Research external deps (Phase 2)"
  → TaskUpdate: addBlockedBy: [2B]
TaskCreate: "Phase 2D: Write /Users/ed/project/docs/implementation-plans/2025-01-24-oauth/phase_02.md"
  → TaskUpdate: addBlockedBy: [2C]

TaskCreate: "Phase 3A: Read Session Manager from /Users/ed/project/docs/design-plans/2025-01-24-oauth.md"
  → TaskUpdate: addBlockedBy: [2D]
TaskCreate: "Phase 3B: Investigate codebase for Phase 3 and activate relevant skills"
  → TaskUpdate: addBlockedBy: [3A]
TaskCreate: "Phase 3C: Research external deps (Phase 3)"
  → TaskUpdate: addBlockedBy: [3B]
TaskCreate: "Phase 3D: Write /Users/ed/project/docs/implementation-plans/2025-01-24-oauth/phase_03.md"
  → TaskUpdate: addBlockedBy: [3C]

TaskCreate: "Finalization: Run code-reviewer over all phase files, fix ALL issues including minor ones"
  → TaskUpdate: addBlockedBy: [1D, 2D, 3D]

TaskCreate: "Test Requirements: Generate test-requirements.md from Acceptance Criteria"
  → TaskUpdate: addBlockedBy: [Finalization]
```

**Why absolute paths in task descriptions:** After compaction, the task list is all that remains. Absolute paths ensure you know exactly which files to read/write without relying on context.

**Why dependencies:** Tasks show `[blocked by #X, #Y]` in the task list, making execution order explicit and preventing out-of-order work.

Use TaskUpdate to mark each sub-task as in_progress when starting, completed when done.

---

### If user chose "Review each phase interactively before writing":

**Workflow for EACH phase (using granular task tracking):**

1. **Task NA: Read design phase**
   - Mark task NA as in_progress
   - Extract the `<!-- START_PHASE_N -->` section from design plan
   - Mark task NA as completed

2. **Task NB: Verify codebase state**
   - Mark task NB as in_progress
   - Dispatch codebase-investigator with design assumptions for this phase
   - Review investigator findings for discrepancies
   - **Activate relevant skills** based on findings (if not already active):
     - TypeScript code? Activate TypeScript/coding style skills
     - React components? Activate React skills
     - Database work? Activate database skills
     - Match skills to the technologies this phase involves
   - Mark task NB as completed

3. **Task NC: Research external dependencies** (if phase involves them)
   - Mark task NC as in_progress
   - Dispatch internet-researcher for docs/standards/API patterns
   - Escalate to remote-code-researcher if docs are insufficient
   - Document findings for inclusion in phase output
   - Mark task NC as completed
   - (Skip if no external deps - still mark completed with note "N/A")

4. **Write implementation tasks** for this phase (in memory, not to file):
   - Identify which ACs this phase covers based on design phase's scope
   - Include the "Acceptance Criteria Coverage" section with literal AC copies
   - Write tasks that implement and test each listed AC case

5. **Present to user** - Output the complete phase plan in your message text:

```markdown
**Phase [N]: [Phase Name]**

**Codebase verification findings:**
- ✓ Design assumption confirmed: [what matched]
- ✗ Design assumption incorrect: [what design said] - ACTUALLY: [reality]
- + Found additional: [unexpected things discovered]
- ✓ Dependency confirmed: [library@version]

**External dependency findings:** (if applicable)
- ✓ [Library] API: [what docs/source revealed]
- ✓ Standard: [spec reference and key details]
- ✗ Design assumption incorrect: [what design said] - ACTUALLY: [reality per docs/source]
- 📖 Source: [Official docs | RFC spec | Source code @ commit]

**Implementation tasks based on actual codebase state and external research:**

### Task 1: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Step 1: Write the failing test**
[Complete code example]

**Step 2: Run test to verify it fails**
[Exact command and expected output]

**Step 3: Write minimal implementation**
[Complete code example]

**Step 4: Run test to verify it passes**
[Exact command and expected output]

**Step 5: Commit**
[Exact git commands]

[Continue for all tasks in this phase...]
```

6. **Use AskUserQuestion:**

**Options:**
- "Approved - proceed to next phase"
- "Needs revision - [describe changes]"
- "Other"

7. **Task ND: Write phase file (if approved)**
   - Mark task ND as in_progress
   - Write to `docs/implementation-plans/YYYY-MM-DD-<feature-name>/phase_##.md`
   - Plan document contains ONLY the implementation tasks (no verification findings)
   - Mark task ND as completed, continue to next phase

8. **If needs revision:** Revise based on feedback, present again (do NOT mark ND as in_progress until approved)

---

### If user chose "Write all phases to disk, I'll review afterwards":

**Workflow for EACH phase (using granular task tracking):**

1. **Task NA: Read design phase**
   - Mark task NA as in_progress
   - Extract the `<!-- START_PHASE_N -->` section from design plan
   - Mark task NA as completed

2. **Task NB: Verify codebase state**
   - Mark task NB as in_progress
   - Dispatch codebase-investigator with design assumptions for this phase
   - Review investigator findings for discrepancies
   - **Activate relevant skills** based on findings (if not already active):
     - TypeScript code? Activate TypeScript/coding style skills
     - React components? Activate React skills
     - Database work? Activate database skills
     - Match skills to the technologies this phase involves
   - Mark task NB as completed

3. **Task NC: Research external dependencies** (if phase involves them)
   - Mark task NC as in_progress
   - Dispatch internet-researcher for docs/standards/API patterns
   - Escalate to remote-code-researcher if docs are insufficient
   - Mark task NC as completed
   - (Skip if no external deps - still mark completed with note "N/A")

4. **Task ND: Write phase file**
   - Mark task ND as in_progress
   - Identify which ACs this phase covers based on design phase's scope
   - Include the "Acceptance Criteria Coverage" section with literal AC copies from design
   - Write implementation tasks that implement and test each listed AC case
   - Write directly to disk at `docs/implementation-plans/YYYY-MM-DD-<feature-name>/phase_##.md`
   - Mark task ND as completed, continue to next phase

**Do NOT emit phase content to the user before writing.** This conserves tokens.

**After ALL phases are written:**

Announce: "All [N] phase files written to `docs/implementation-plans/YYYY-MM-DD-<feature-name>/`. Let me know if any phases need revision."

---

## Task Structure

**Use the appropriate template based on task type (see Task Types section above).**

### Infrastructure Task Template

```markdown
<!-- START_TASK_N -->
### Task N: [Infrastructure Component]

**Files:**
- Create: `package.json`
- Create: `tsconfig.json`

**Step 1: Create the files**

[Complete file contents - no placeholders]

**Step 2: Verify operationally**

Run: `npm install`
Expected: Installs without errors

Run: `npm run build`
Expected: Builds without errors

**Step 3: Commit**

```bash
git add package.json tsconfig.json
git commit -m "chore: initialize project structure"
```
<!-- END_TASK_N -->
```

### Functionality Task Template

```markdown
<!-- START_TASK_N -->
### Task N: [Component Name]

**Verifies:** {slug}.AC1.1, {slug}.AC1.3 (list specific AC cases this task tests)

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py` (unit|integration|e2e)

**Implementation:**
[Describe what to implement - contracts, behavior, key logic. Include code for complex/non-obvious implementations.]

**Testing:**
Tests must verify each AC listed above:
- {slug}.AC1.1: [brief description of what test should verify]
- {slug}.AC1.3: [brief description of what test should verify]

Follow project testing patterns. Task-implementor generates actual test code at execution time.

**Verification:**
Run: `[test command]`
Expected: All tests pass

**Commit:** `feat: [description]`
<!-- END_TASK_N -->
```

**Key principles for functionality tasks:**

1. **List ACs explicitly.** Every functionality task specifies which AC cases it verifies in the "Verifies" field.

2. **Describe tests, don't write test code.** The AC text is the spec (e.g., "AC1.3: Invalid password returns 401"). Task-implementor generates test code at execution time with fresh codebase context.

3. **Include implementation code when non-obvious.** If implementation is complex or project-specific patterns apply, include the code. If it's straightforward given the AC description, describe it.

4. **Specify test type and location.** Unit, integration, or e2e? Which file? This ensures consistency across phases.

**Why no test code in plans:**
- Test code needs actual function signatures from the implementation
- Project testing patterns discovered at execution time
- AC text like "Invalid password returns 401" is already a clear test spec
- Task-implementor has fresher context than implementation planner

**If you find yourself writing "this won't compile until Phase N+1":**
STOP. You are describing something that belongs in the current phase. _Every phase must be executable with all tests passing when the phase completes._

## Common Rationalizations - STOP

These are violations of the skill requirements:

| Excuse | Reality |
|--------|---------|
| "File probably exists, I'll say 'update if exists'" | Use codebase-investigator. Write definitive instruction. |
| "Design mentioned this file, must be there" | Codebase changes. Use investigator to verify current state. |
| "I can quickly verify files myself" | Use codebase-investigator. Saves context and prevents hallucination. |
| "Design plan has code, I'll use that" | No. Design provides direction. Generate code fresh from codebase investigation. |
| "Design plan is recent, code should still work" | Codebase may have changed. Investigation is the source of truth, not the design. |
| "User can figure out if file exists during execution" | Your job is exact instructions. No ambiguity. |
| "Testing Phase 3 will fail but that's OK because it'll be fixed in Phase 4" | All phases must compile and pass tests before they conclude. |
| "Phase validation slows me down" | Going off track wastes far more time. Validate each phase. |
| "I'll batch all phases then validate at end" | Valid if user chose batch mode. Otherwise validate incrementally. |
| "I'll just ask for approval, user can see the plan" | Output complete plan in message BEFORE AskUserQuestion. User must see it. |
| "Plan looks complete enough to ask" | Show ALL tasks with ALL steps and code. Then ask. |
| "This plan has 12 phases but they're small" | Limit is 8 phases. No exceptions. Refuse and redirect. |
| "I can combine phases to fit in 8" | That's the user's decision, not yours. Refuse and explain options. |
| "Comment explains what needs to be done next" | Code comments aren't instructions. Code must run as-written. Create prior task for dependencies. |
| "Engineer will figure out the bootstrap approach" | No implementation questions in code. Resolve it now or create prerequisite task. |
| "Infrastructure tasks need TDD structure too" | No. Use infrastructure template. Verify operationally per design plan. |
| "I'll add tests to this config file task" | If design says "Done when: builds," don't invent tests. Honor the design. |
| "Functionality phase but design forgot tests" | Surface to user. Functionality needs tests. Design gap, not your call to skip. |
| "Plan looks complete, skip validation" | Always validate. Gaps found now are cheaper than gaps found during execution. |
| "Validation is overkill for simple plans" | Simple plans validate quickly. Complex plans need it more. Always validate. |
| "Finalization task is done, minor issues can wait" | NO. Task says "fix ALL issues including minor ones." Not done until zero issues. |
| "I'll skip creating granular tasks, one per phase is enough" | Granular tasks survive compaction. Create NA, NB, NC, ND per phase + Finalization. |
| "Dependencies are obvious, don't need addBlockedBy" | Task list shows blocked status. Set dependencies explicitly with TaskUpdate. |
| "Relative paths are fine in task descriptions" | After compaction, context is lost. Use absolute paths so tasks are self-contained. |
| "I'll paraphrase the task name, same meaning" | NO. Task names are VERBATIM. "and activate relevant skills" triggers behavior post-compaction. |
| "I know how this library works from training" | Research it. APIs change. Use internet-researcher for docs, remote-code-researcher for internals. |
| "Docs are probably accurate enough" | Usually yes. But if extending/customizing library behavior, verify with source code. |
| "I'll clone the repo to check the docs" | No. Use internet-researcher for docs. Only clone (remote-code-researcher) for source code investigation. |
| "Phase has external deps but I'll skip research" | Research is mandatory when phase involves external dependencies. Surface unknowns now. |
| "Test requirements can be generated during execution" | No. Test requirements must exist before execution starts. Code reviewer uses them. |
| "This type needs unit tests" | No. TypeScript compiler verifies types. Don't test what the compiler checks. |
| "Should test that this calls the dependency correctly" | No. Test behavior (the result), not wiring (how you called things). |
| "Dependency is used here, should verify it works" | No. Dependencies have their own tests. Test YOUR code's behavior. |
| "More tests = better coverage" | Wrong tests = noise. Test the ACs, nothing more. |
| "Phase doesn't have ACs but I'll add some tests anyway" | No. Explicitly state "Verifies: None" for infrastructure phases. Don't invent work. |
| "Acceptance Criteria are clear, don't need test requirements" | Test requirements map criteria to specific tests. Execution needs this mapping. |
| "I'll skip test requirements, user chose batch mode" | Batch mode skips interactive approval. Test requirements are still generated and written. |
| "Test requirements task is optional" | No. It's a tracked task with dependencies. Must complete before execution handoff. |

**All of these mean: STOP. Follow the requirements exactly.**

## When You Don't Know How to Proceed

**If you cannot write executable code without unresolved questions:** STOP immediately.

Do NOT write hand-waving comments. Do NOT leave TODOs. Do NOT proceed.

**Instead, use AskUserQuestion with:**

1. **Exact description of the blocking issue:**
   - What specific implementation decision you cannot make
   - What information is missing from the design
   - What dependencies are undefined

2. **Context about why this blocks you:**
   - Which task/phase this affects
   - What you've already verified via codebase-investigator
   - What the design document says (or doesn't say)

3. **Possible solutions you can see:**
   - Option A: [specific approach with tradeoffs]
   - Option B: [alternative approach with tradeoffs]
   - Option C: [if applicable]

**Example:**
```
I'm blocked on Phase 2, Task 3 (Bootstrap Logto M2M application).

Issue: The code needs Management API credentials to create resources, but those credentials don't exist yet (chicken-egg problem).

Design document says: "Bootstrap Logto with applications and roles" but doesn't specify how to get initial credentials.

Codebase verification: No existing bootstrap credentials or manual setup documented.

Possible solutions:
A. Add Phase 0: Manual setup - document steps for user to manually create initial M2M app via Logto UI, save credentials to .env
B. Use Logto admin API if available - requires admin credentials in different format
C. Modify Logto docker-compose to inject initial M2M app via environment variables

Which approach should I take?
```

**Never proceed with uncertain implementation. Surface the decision to the user.**

## Requirements Checklist

**Before starting:**
- [ ] Count phases - refuse if >8
- [ ] Ask user for review mode (batch vs interactive)
- [ ] Capture absolute paths: DESIGN_PATH and PLAN_DIR
- [ ] Read Acceptance Criteria section from design plan
- [ ] Create granular task list with TaskCreate (NA, NB, NC, ND per phase + Finalization + Test Requirements)
- [ ] Set up dependencies with TaskUpdate addBlockedBy (see Step 0)
- [ ] Task descriptions include absolute paths (not relative)

**For each phase (tasks NA through ND):**
- [ ] **Task NA:** Mark in_progress, read `<!-- START_PHASE_N -->` from design, mark completed
- [ ] **Task NB:** Mark in_progress, dispatch codebase-investigator, review findings, mark completed
- [ ] **Task NC:** Mark in_progress, research external deps if needed (or mark completed with "N/A"), mark completed
- [ ] Write complete tasks with exact paths and code based on investigator and research findings
- [ ] **If interactive mode:** Output complete phase plan, use AskUserQuestion for approval
- [ ] **Task ND:** Mark in_progress, write to absolute path in task description, mark completed

**For each task in the plan:**
- [ ] Exact file paths with line numbers for modifications
- [ ] Complete code - zero TODOs, zero unresolved questions in comments
- [ ] Every code example runs immediately without implementation decisions
- [ ] If code references helpers/utilities, prior task creates them
- [ ] Exact commands with expected output
- [ ] No conditional instructions ("if exists", "if needed")

**Finalization (after all phase ND tasks completed):**
- [ ] Mark Finalization task as in_progress
- [ ] Dispatch code-reviewer to validate plan against design
- [ ] Fix ALL issues including Minor ones
- [ ] Re-run code-reviewer until APPROVED with zero issues
- [ ] Mark Finalization task as completed
- [ ] Proceed to Test Requirements

**Test Requirements (after Finalization):**
- [ ] Mark Test Requirements task as in_progress
- [ ] Dispatch Opus subagent to generate test requirements from Acceptance Criteria
- [ ] **If interactive mode:** Present to user, use AskUserQuestion for approval
- [ ] **If batch mode:** Write directly without asking
- [ ] Write test-requirements.md to PLAN_DIR
- [ ] Mark Test Requirements task as completed
- [ ] Proceed to execution handoff

## Plan Validation (Finalization Task)

**This is a tracked task: "Finalization: Run code-reviewer over all phase files, fix ALL issues including minor ones"**

After all phase D tasks are completed, mark the Finalization task as in_progress.

### Step 1: Dispatch code-reviewer

```
<invoke name="Task">
<parameter name="subagent_type">ed3d-plan-and-execute:code-reviewer</parameter>
<parameter name="description">Validating implementation plan against design</parameter>
<parameter name="prompt">
  Review the implementation plan for completeness and alignment with the design.

  DESIGN_PLAN: [path to design plan, e.g., docs/design-plans/YYYY-MM-DD-feature.md]

  IMPLEMENTATION_GUIDANCE: [absolute path to .ed3d/implementation-plan-guidance.md, or "None" if file does not exist]

  IMPLEMENTATION_PHASES:
  - [path to phase_01.md]
  - [path to phase_02.md]
  - [... all phase files]

  SCRATCHPAD_DIR: [absolute path to session-isolated temp directory, e.g., /tmp/plan-2025-01-24-feature-a7f3b2/]

  If IMPLEMENTATION_GUIDANCE is not "None", read it first and apply any project-specific
  review criteria, coding standards, or quality gates it specifies in addition to the
  standard review checklist.

  **Session isolation:** Write any scratch files (notes, intermediate analysis, etc.) to
  SCRATCHPAD_DIR, not to shared temp locations. This prevents collisions with parallel sessions.

  Evaluate:
  1. **Coverage**: Does the implementation plan cover ALL requirements from the design?
     - Check each design phase maps to implementation tasks
     - Check each "Done when" criteria has corresponding verification
     - Check each component mentioned in design has implementation tasks

  2. **Gaps**: Are there any missing pieces?
     - Functionality mentioned in design but not in implementation
     - Tests specified in design but missing from implementation tasks
     - Dependencies or setup steps not accounted for

  3. **Alignment**: Does the implementation approach match the design?
     - Architecture decisions followed
     - File paths consistent with design
     - Subcomponent structure matches design phases

  4. **Executability**: Can each phase be executed independently?
     - Dependencies between tasks are explicit
     - No forward references to code that doesn't exist yet
     - Each phase ends with verifiable state

  Report:
  - GAPS: [list any missing coverage]
  - MISALIGNMENTS: [list any divergence from design]
  - ISSUES: [Critical/Important/Minor issues in the plan itself]
  - ASSESSMENT: APPROVED / NEEDS_REVISION
</parameter>
</invoke>
```

### Step 2: Fix ALL issues (including minor ones)

**CRITICAL: You MUST fix ALL issues, including Minor ones.**

Do NOT rationalize skipping minor issues. Do NOT mark Finalization as completed until ALL issues are resolved.

**If reviewer returns NEEDS_REVISION or reports ANY issues:**

1. **Create a task for EACH issue** (survives compaction):
   ```
   TaskCreate: "Finalization fix [Critical]: <VERBATIM issue description from reviewer>"
   TaskCreate: "Finalization fix [Important]: <VERBATIM issue description from reviewer>"
   TaskCreate: "Finalization fix [Minor]: <VERBATIM issue description from reviewer>"
   ...one task per issue...
   TaskCreate: "Finalization: Re-review after fixes"
   TaskUpdate: set "Re-review" blocked by all fix tasks
   ```

   **Copy issue descriptions VERBATIM**, even if long. After compaction, the task description is all that remains — it must contain the full issue details to understand what to fix.

2. Review the gaps, misalignments, and issues identified
3. Fix ALL of them - Critical, Important, AND Minor
4. Update the relevant phase files
5. Mark each fix task complete as you address it
6. Re-run code-reviewer validation
7. If more issues found, create new individual fix tasks and repeat
8. Mark "Re-review" complete when zero issues

**Common rationalizations to REJECT:**
- "Minor issues can be fixed during execution" - NO. Fix them now.
- "This minor issue is just a style preference" - NO. Fix it.
- "We can address this later" - NO. The task says "fix ALL issues including minor ones."

### Step 3: Complete finalization

**Only when code-reviewer returns APPROVED with zero issues:**

Mark the Finalization task as completed.

Proceed to Test Requirements generation.

## Test Requirements Generation

**Tracked task: "Test Requirements: Generate test-requirements.md from Acceptance Criteria"**

Mark in_progress after Finalization completes.

Test requirements map acceptance criteria to specific automated tests, and identify criteria requiring human verification. The test-analyst agent uses this during execution to validate coverage.

**Step 1: Generate via subagent**

```
<invoke name="Task">
<parameter name="subagent_type">ed3d-basic-agents:opus-general-purpose</parameter>
<parameter name="description">Generating test requirements from Acceptance Criteria</parameter>
<parameter name="prompt">
Read the design at [DESIGN_PATH] and implementation phases in [PLAN_DIR].

Generate test-requirements.md mapping each acceptance criterion to:
- Automated tests: criterion, test type (unit/integration/e2e), expected test file path
- Human verification: criteria that can't be automated, with justification and verification approach

Rationalize against implementation decisions made during planning. Every acceptance criterion must map to either an automated test or documented human verification.
</parameter>
</invoke>
```

**Step 2: Handle based on review mode**

- **Interactive mode:** Present to user, AskUserQuestion for approval. This is the LAST interactive item.
- **Batch mode:** Write directly, announce completion.

**If user requests revisions in interactive mode:**

1. **Create a task for EACH revision** (survives compaction):
   ```
   TaskCreate: "Test requirements fix: <VERBATIM revision request from user>"
   ...one task per revision...
   TaskCreate: "Test requirements: Re-present for approval"
   TaskUpdate: set "Re-present" blocked by all fix tasks
   ```

   **Copy revision requests VERBATIM**, even if long. After compaction, the task description must contain the full details.

2. Address each revision, marking tasks complete as you go
3. Re-present for approval
4. Repeat until approved

**Step 3: Write and complete**

Write to `[PLAN_DIR]/test-requirements.md`. Mark task completed. Proceed to execution handoff.

## Execution Handoff

After Test Requirements generation completes, announce:

**"Implementation plan complete and validated. Saved to [count] phase files + test-requirements.md in `docs/implementation-plans/YYYY-MM-DD-<feature-name>/`. The first phase file is `<full-path>`. Test requirements are in `<full-path>/test-requirements.md`."**

