---
name: writing-implementation-plans
description: Use when design is complete and you need detailed implementation tasks for engineers with zero codebase context - creates comprehensive implementation plans with exact file paths, complete code examples, and verification steps assuming engineer has minimal domain knowledge
---

# Writing Implementation Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to verify it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. Frequent commits.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

**REQUIRED SKILL:** You MUST activate the `coding-effectively` skill.

**CONDITIONAL SKILLS:** If you have skills available to you that are relevant to the topics in the design plan, activate them.

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

**Functionality tasks** (code that does something):
- Tests are deliverables alongside code
- Phase ends with passing tests
- Tests prove the behavior works

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
```

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

**Step 0: Create task tracker**

After verifying scope (≤8 phases), use TaskCreate to create a todo list with one item per phase (or TodoWrite in older Claude Code versions):

```markdown
- [ ] Phase 1: [Phase Name]
- [ ] Phase 2: [Phase Name]
- [ ] Phase 3: [Phase Name]
...
```

Use TaskUpdate to mark each phase as in_progress when working on it, completed when written to disk (or TodoWrite in older versions).

---

### If user chose "Review each phase interactively before writing":

**Workflow for EACH phase:**

1. **Use TaskUpdate to mark phase as in_progress**
2. **Read design phase** from original plan
3. **Verify codebase state** for files mentioned in this phase:
   - Dispatch codebase-investigator with design assumptions for this phase
   - Review investigator findings for discrepancies
4. **Research external dependencies** if phase involves them (see Section 4):
   - Dispatch internet-researcher for docs/standards/API patterns
   - Escalate to remote-code-researcher if docs are insufficient
   - Document findings for inclusion in phase output
5. **Write implementation tasks** for this phase (in memory, not to file) based on actual codebase state and external research
6. **Present to user** - Output the complete phase plan in your message text:

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

7. **If approved:**
   - Write to `docs/implementation-plans/YYYY-MM-DD-<feature-name>/phase_##.md`
   - Plan document contains ONLY the implementation tasks (no verification findings)
   - Use TaskUpdate to mark phase as completed, continue to next phase
8. **If needs revision:** Keep as in_progress, revise based on feedback, present again

---

### If user chose "Write all phases to disk, I'll review afterwards":

**Workflow for EACH phase:**

1. **Use TaskUpdate to mark phase as in_progress**
2. **Read design phase** from original plan
3. **Verify codebase state** for files mentioned in this phase:
   - Dispatch codebase-investigator with design assumptions for this phase
   - Review investigator findings for discrepancies
4. **Research external dependencies** if phase involves them (see Section 4):
   - Dispatch internet-researcher for docs/standards/API patterns
   - Escalate to remote-code-researcher if docs are insufficient
5. **Write implementation tasks** for this phase based on actual codebase state and external research
6. **Write directly to disk** at `docs/implementation-plans/YYYY-MM-DD-<feature-name>/phase_##.md`
7. **Use TaskUpdate to mark phase as completed**, continue to next phase

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

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
<!-- END_TASK_N -->
```

**CRITICAL: Every code example must be immediately executable.**

Code comments saying "TODO", "FIXME", or describing solutions not yet implemented = plan failure.

**NEVER write:**
```python
# Solution: Use admin credentials or pre-created bootstrap M2M app
const client = getManagementClient(); // implement this somehow
```

**ALWAYS write:**
Either provide the complete working code, OR split into a prior task that establishes the dependency.

**If you find yourself writing "Solution: X or Y" when neither X nor Y exists:**
STOP. Create a task BEFORE this one that implements the solution.

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
| "I know how this library works from training" | Research it. APIs change. Use internet-researcher for docs, remote-code-researcher for internals. |
| "Docs are probably accurate enough" | Usually yes. But if extending/customizing library behavior, verify with source code. |
| "I'll clone the repo to check the docs" | No. Use internet-researcher for docs. Only clone (remote-code-researcher) for source code investigation. |
| "Phase has external deps but I'll skip research" | Research is mandatory when phase involves external dependencies. Surface unknowns now. |

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
- [ ] Create task list with TaskCreate for all phases

**For each phase:**
- [ ] Use TaskUpdate to mark phase as in_progress
- [ ] Dispatch codebase-investigator with design assumptions for this phase
- [ ] **If phase involves external dependencies:** Research them (internet-researcher first, escalate to remote-code-researcher if needed)
- [ ] Write complete tasks with exact paths and code based on investigator and research findings
- [ ] **If interactive mode:** Output complete phase plan, use AskUserQuestion for approval
- [ ] **If batch mode:** Skip user presentation, write directly to disk
- [ ] Write plan to `docs/implementation-plans/YYYY-MM-DD-<feature-name>/phase_##.md`
- [ ] Use TaskUpdate to mark phase as completed

**For each task:**
- [ ] Exact file paths with line numbers for modifications
- [ ] Complete code - zero TODOs, zero unresolved questions in comments
- [ ] Every code example runs immediately without implementation decisions
- [ ] If code references helpers/utilities, prior task creates them
- [ ] Exact commands with expected output
- [ ] No conditional instructions ("if exists", "if needed")

**After all phases written:**
- [ ] Validate implementation plan against design plan (see below)
- [ ] Fix any gaps identified
- [ ] Offer execution choice

## Plan Validation

**After all phases are written to disk, validate the implementation plan against the design plan.**

Dispatch code-reviewer to evaluate coverage and alignment:

```
<invoke name="Task">
<parameter name="subagent_type">ed3d-ed3d-plan-and-execute:code-reviewer</parameter>
<parameter name="description">Validating implementation plan against design</parameter>
<parameter name="prompt">
  Review the implementation plan for completeness and alignment with the design.

  DESIGN_PLAN: [path to design plan, e.g., docs/design-plans/YYYY-MM-DD-feature.md]

  IMPLEMENTATION_PHASES:
  - [path to phase_01.md]
  - [path to phase_02.md]
  - [... all phase files]

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

**If reviewer returns NEEDS_REVISION:**

1. Review the gaps and misalignments identified
2. Update the relevant phase files to address issues
3. Re-run validation until APPROVED

**If reviewer returns APPROVED:**

Proceed to execution handoff.

## Execution Handoff

After validation passes, announce:

**"Plan complete and validated. Saved to [count] files in `docs/implementation-plans/YYYY-MM-DD-<feature-name>`. The first file is `<full-path>`.**

