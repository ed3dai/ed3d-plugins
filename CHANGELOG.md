# Changelog

## ed3d-plan-and-execute 1.10.2

Fix typo in planning handoff command.

**Fixed:**
- `starting-a-design-plan`: Phase 6 handoff command had `/ed3d-ed3d-plan-and-execute:start-implementation-plan` instead of `/ed3d-plan-and-execute:start-implementation-plan`

## ed3d-extending-claude 1.0.4

Add model-level testing guidance to testing-skills-with-subagents.

**Changed:**
- `testing-skills-with-subagents`: RED phase should use production-level model (default: Sonnet); GREEN/REFACTOR phases should use one tier down (default: Haiku) to ensure skill clarity under weaker reasoning
- Quick reference table now includes model column

## ed3d-basic-agents 1.1.0

Add fan-out analysis skill for large corpus processing.

**New:**
- `doing-a-simple-two-stage-fanout` skill: orchestrates parallel Worker subagents, Critic review subagents, and a Summarizer for analyzing corpora that exceed a single agent's context window
- `compute_layout.py` helper script for computing segment counts, agent assignments, and context window budgets
- `diagram-templates.md` reference with Mermaid and Graphviz templates for visualizing fan-out pipelines
- First `user-invocable: true` skill in this plugin

## [ed3d-hook-skill-reinforcement] 1.0.1, [ed3d-plan-and-execute] 1.10.1, [ed3d-basic-agents] 1.0.2, [ed3d-extending-claude] 1.0.3

Remove stale `<available_skills>` XML tag references that no longer match how Claude Code injects skill lists.

**Fixed:**
- Replaced all references to `<available_skills>` with format-agnostic language ("your available skills shown in your system context") across hooks, skills, and agent prompts
- Hook reminder now uses emphatic "MUST" / "Do NOT skip" phrasing for stronger compliance
- Added warning comment in CLAUDE_MD_TESTING.md example to prevent re-introducing the stale tag

## ed3d-plan-and-execute 1.10.0

Scoped acceptance criteria for cross-plan uniqueness.

**New:**
- AC identifiers now use scoped format `{slug}.AC{N}.{M}` (e.g., `oauth2-svc-authn.AC1.1`) to prevent collisions across multiple plan-and-execute rounds
- Design plan naming now prompts user explicitly via AskUserQuestion — supports ticket names (e.g., `PROJ-1234`) or descriptive slugs
- Slug naming guidance: prefer terse unambiguous names (`authn` not `authentication`, but not `auth` since ambiguous with `authz`)

**Changed:**
- `starting-a-design-plan`: Added Step 1 to get design plan name before file creation
- `starting-an-implementation-plan`: Slug definition now documents its three uses (directory, worktree, AC scope)
- `writing-design-plans`: AC structure uses scoped format with slug prefix
- `writing-implementation-plans`: Task templates and AC coverage sections use scoped format
- `executing-an-implementation-plan`: AC coverage check references scoped format
- All examples updated to use terse slugs (e.g., `oauth2-svc-authn` instead of `oauth2-service-auth`)

## ed3d-plan-and-execute 1.9.8

Disables user invocation of skills.

**Changed:**
- All skills now have `user-invocable: false` — skills are auto-invoked by Claude based on description matching but won't appear in the `/` slash command menu

## ed3d-house-style 1.0.2

Disables user invocation of skills.

**Changed:**
- All skills now have `user-invocable: false` — skills are auto-invoked by Claude based on description matching but won't appear in the `/` slash command menu

## ed3d-extending-claude 1.0.2

Disables user invocation of skills.

**Changed:**
- All skills now have `user-invocable: false` — skills are auto-invoked by Claude based on description matching but won't appear in the `/` slash command menu

## ed3d-basic-agents 1.0.1

Disables user invocation of skills.

**Changed:**
- All skills now have `user-invocable: false` — skills are auto-invoked by Claude based on description matching but won't appear in the `/` slash command menu

## ed3d-playwright 1.0.1

Disables user invocation of skills.

**Changed:**
- All skills now have `user-invocable: false` — skills are auto-invoked by Claude based on description matching but won't appear in the `/` slash command menu

## ed3d-research-agents 1.0.1

Disables user invocation of skills.

**Changed:**
- All skills now have `user-invocable: false` — skills are auto-invoked by Claude based on description matching but won't appear in the `/` slash command menu

## ed3d-plan-and-execute 1.9.7

Adds AC coverage verification, compaction-safe task tracking for review fixes, and test plan reminder.

**Changed:**
- `executing-an-implementation-plan`: Final code review now includes AC_COVERAGE_CHECK — verifies all acceptance criteria are covered by at least one phase
- `executing-an-implementation-plan`: When code reviewer returns issues, create ONE TASK PER ISSUE with VERBATIM description — survives compaction
- `writing-implementation-plans`: Same per-issue task creation for finalization code review fixes
- `writing-implementation-plans`: Same per-revision task creation for test requirements approval
- `finishing-a-development-branch`: Reminds user to review human test plan (if exists) before considering work complete

## ed3d-plan-and-execute 1.9.6

Requires verbatim task names to prevent instruction loss.

**Fixed:**
- `writing-implementation-plans`: Task names must be copied VERBATIM, not paraphrased — phrases like "and activate relevant skills" trigger behavior post-compaction

## ed3d-plan-and-execute 1.9.5

Dynamic skill activation replaces hardcoded requirements.

**Changed:**
- `writing-implementation-plans`: Removed hardcoded "REQUIRED SKILL: coding-effectively"
- `writing-implementation-plans`: Task NB now "Investigate codebase for Phase N and activate relevant skills"
- Skills activated dynamically based on codebase findings, not statically at skill start

## ed3d-plan-and-execute 1.9.4

Activates relevant skills during implementation planning based on technology stack.

**Changed:**
- `writing-implementation-plans`: After codebase investigation, activate skills matching the technologies involved (TypeScript, React, database, etc.) if not already active

## ed3d-plan-and-execute 1.9.3

Adds guidance to prevent over-testing and testing implementation details.

**Changed:**
- `writing-implementation-plans`: "Test behavior, not implementation" — test outputs, not how you called dependencies
- `writing-implementation-plans`: Infrastructure phases explicitly state "Verifies: None" instead of inventing ACs
- `writing-implementation-plans`: What doesn't need tests: types, already-tested dependencies, call patterns
- `writing-implementation-plans`: New rationalizations for common over-testing mistakes

## ed3d-plan-and-execute 1.9.2

Ties tests explicitly to acceptance criteria; removes test code from implementation plans.

**Changed:**
- `writing-design-plans`: Functionality phases must have tests that verify the specific ACs they cover; phase not "done" until tests exist for each listed AC case
- `writing-implementation-plans`: Functionality tasks include "Verifies: AC1.1, AC1.3" field; tests described by AC reference, not full code
- `writing-implementation-plans`: Task-implementor generates actual test code at execution time with fresh codebase context

**Why:** Test code in plans becomes stale (wrong imports, mock patterns). AC text like "Invalid password returns 401" is already a clear test spec.

## ed3d-plan-and-execute 1.9.1

Strengthens acceptance criteria generation and adds traceability to implementation plans.

**Changed:**
- `writing-design-plans`: Acceptance Criteria now generated inline (no subagent needed) with detailed guidance on enumerating success cases, failure cases, and edge cases for each DoD item
- `writing-design-plans`: AC uses numbered format (AC1, AC1.1, AC1.2) for precise traceability
- `writing-design-plans`: AC section moved to legibility header (between DoD and Glossary)
- `writing-implementation-plans`: Phase headers now include "Acceptance Criteria Coverage" section listing which ACs the phase implements
- `writing-implementation-plans`: AC entries copied literally from design plan—no paraphrasing
- `starting-a-design-plan`: Initial document template includes AC placeholder

**Traceability chain:**
```
Design: AC1.1, AC1.2, AC1.3 → Phase header: "implements AC1.1, AC1.3" → Tasks produce tests for AC1.1, AC1.3
```

## ed3d-plan-and-execute 1.9.0

Adds test planning workflow: acceptance criteria, test requirements, and human test plans.

**New:**
- **Acceptance Criteria** in design plans — Definition of Done translated into specific, verifiable criteria; human validates before design documentation completes
- **Test Requirements** in implementation plans — Acceptance criteria mapped to automated tests (with expected file paths) or documented as requiring human verification; written to `test-requirements.md`
- **test-analyst agent** — Validates test coverage against acceptance criteria after final code review; generates human test plan when coverage passes
- **Human Test Plans** — Written to `docs/test-plans/[design-plan-name].md` with specific verification steps, end-to-end scenarios, and traceability to Definition of Done

**Changed:**
- `writing-design-plans`: New section for generating and validating Acceptance Criteria after Implementation Phases
- `writing-implementation-plans`: New Test Requirements task after Finalization; Opus subagent generates `test-requirements.md`
- `executing-an-implementation-plan`: Final review sequence now includes test-analyst for coverage validation and test plan generation

**Test traceability chain:**
```
Definition of Done → Acceptance Criteria → Test Requirements → Automated Tests → Human Test Plan
```

## ed3d-plan-and-execute 1.8.0

Per-phase code reviews now use project-specific implementation guidance.

**Changed:**
- `executing-an-implementation-plan`: Per-phase code reviews now receive the `.ed3d/implementation-plan-guidance.md` file (when it exists) so reviewers apply project-specific coding standards, testing requirements, and review criteria during each phase—not just during the final all-phases review

## ed3d-plan-and-execute 1.7.2

- `/how-to-customize` given more specific instructions to actually repeat the information verbatim.

## ed3d-plan-and-execute 1.7.0

Adds project-specific guidance files for customizing design and implementation plans.

**New:**
- **Project guidance files**: Create `.ed3d/design-plan-guidance.md` and `.ed3d/implementation-plan-guidance.md` to provide project-specific constraints, terminology, and standards
- **`/how-to-customize` command**: Documents available guidance files with examples
- **Design guidance**: Loaded before clarification phase — defines domain terminology, architectural constraints, technology preferences
- **Implementation guidance**: Loaded when starting implementation plans AND during final code review — specifies coding standards, testing requirements, review criteria

**Changed:**
- `starting-a-design-plan`: Checks for and reads `.ed3d/design-plan-guidance.md` between Phase 1 (Context Gathering) and Phase 2 (Clarification)
- `starting-an-implementation-plan`: Checks for and reads `.ed3d/implementation-plan-guidance.md` after branch setup
- `writing-implementation-plans`: Includes guidance path in Finalization task for code reviewer

## ed3d-plan-and-execute 1.6.2

Fixes "Re-read skill" task dependency ordering.

**Fixed:**
- "Re-read skill" task must be re-pointed to Finalization task after granular tasks are created (was incorrectly blocked by "Create implementation plan")
- Added "After Planning: Update Dependencies" step to ensure correct task ordering

## ed3d-plan-and-execute 1.6.1

Fixes task tracking to include dependencies and absolute paths.

**Fixed:**
- Tasks now use addBlockedBy to enforce execution order (NA→NB→NC→ND, then next phase)
- Task descriptions include absolute paths for design file and output file, so tasks remain actionable after compaction

## ed3d-plan-and-execute 1.6.0

Adds granular task tracking to implementation plan writing to survive context compaction.

**New in `writing-implementation-plans`:**
- **Granular per-phase tasks:** Instead of one task per phase, now creates sub-tasks for each step:
  - Phase NA: Read [Phase Name] from design plan
  - Phase NB: Dispatch codebase-investigator to verify current state
  - Phase NC: Research external dependencies (if applicable)
  - Phase ND: Write phase file to disk
- **Finalization task:** Explicitly states "fix ALL issues including minor ones" — model cannot rationalize skipping minor issues
- **Plan validation as tracked task:** Must complete with zero issues before handoff

**New in `writing-design-plans`:**
- **Phase markers:** Design plans now require `<!-- START_PHASE_N -->` / `<!-- END_PHASE_N -->` markers around each implementation phase, enabling granular parsing

**New in `starting-an-implementation-plan`:**
- **Orchestration tasks:** Tracks Branch setup, Create implementation plan, Re-read skill, Execution handoff
- **Restore context step:** Re-reads skill before handoff to restore instructions post-compaction
- **Terminology clarification:** Renamed "Phase 1/2/3" to descriptive names (Branch Setup, Planning, Execution Handoff) to avoid confusion with implementation plan phases

**Fixed:**
- Code reviewer step was being forgotten after compaction — now tracked as explicit Finalization task
- Minor issues were being skipped — task text now makes fixing them mandatory

## ed3d-plan-and-execute 1.5.1

Updates task tracking references for compatibility with new Claude Code task system.

**Changed:**
- All references to `TodoWrite` now prefer `TaskCreate`/`TaskUpdate`/`TaskList` (the new task tools in Claude Code)
- Backwards-compatibility notes added for older Claude Code versions that still use `TodoWrite`

## ed3d-extending-claude 1.0.1

Updates task tracking references for compatibility with new Claude Code task system.

**Changed:**
- Tool tables and examples now reference `TaskCreate`/`TaskUpdate` instead of `TodoWrite`
- Backwards-compatibility notes added for older Claude Code versions

## ed3d-house-style 1.0.1

Updates task tracking references for compatibility with new Claude Code task system.

**Changed:**
- Persuasion principles documentation now references `TaskCreate`/`TaskUpdate` instead of `TodoWrite`
- Backwards-compatibility notes added for older Claude Code versions

## ed3d-plan-and-execute 1.5.0

Promotes experimental execution workflow to stable.

**Changed:**
- Execution workflow now uses just-in-time phase loading (reads one phase at a time, not all upfront)
- Code review happens once per phase instead of between every task
- TodoWrite structure: three entries per phase (Read, Execute, Code review) with absolute paths and titles
- Subagents receive phase file path and read it themselves

**Removed:**
- Experimental skill and command (merged into stable)
- Task grouping by subcomponent (plan phases now define grouping via markers)
- Task-level code review (replaced with phase-level review)

## ed3d-plan-and-execute 1.4.3

Removes misleading directive from implementation plan header.

**Fixed:**
- Removed "For Claude: REQUIRED SUB-SKILL" directive from plan header template — was being parsed by task-implementor subagent when it should only be used at the top-level orchestrator

## ed3d-plan-and-execute 1.4.2

Simplifies experimental execution workflow.

**Changed:**
- Experimental skill now reads first 10 lines (not 3) to capture Goal in header
- Subagents (task-implementor, bug-fixer) now read entire phase file instead of extracted sections
- Removed context window extraction logic — simpler approach, let subagents see full phase context

## ed3d-plan-and-execute 1.4.1

Adds experimental execution workflow and task markers. (1.4.0 was a buggy mis-push.)

**New:**
- **Task and subcomponent markers** in implementation plans: `<!-- START_TASK_N -->`, `<!-- END_TASK_N -->`, `<!-- START_SUBCOMPONENT_A (tasks 3-5) -->`, etc.
- **Experimental execution skill** (`executing-an-implementation-plan-experimental`) with just-in-time phase loading, context windows for subagents, and marker-based extraction
- **Experimental command** (`/execute-implementation-plan-experimental`) to invoke the experimental workflow

**Changed:**
- `writing-implementation-plans` now generates markers in all task templates (backwards compatible — old execution skill ignores them)

## ed3d-plan-and-execute 1.3.3

Fixes execution handoff to use absolute paths, preventing wrong-directory issues after /clear.

**Fixed:**
- Execution handoff now captures absolute paths via `git rev-parse --show-toplevel` and verifies plan directory exists before outputting command
- After `/clear`, users land in the original session directory (often repo root, not worktree) — absolute paths ensure execution happens in the correct directory regardless

**Changed:**
- `/execute-implementation-plan` command now accepts two arguments: `[absolute-plan-dir]` and `[absolute-working-dir]`
- Command verifies both paths exist and changes to working directory before engaging skill

## ed3d-plan-and-execute 1.3.2

Fixes execution handoff to pass plan directory instead of single phase file.

**Fixed:**
- Execute-implementation-plan instructions now pass the plan directory (e.g., `@docs/implementation-plans/YYYY-MM-DD-feature/`) instead of a single phase file — prevents agent from only implementing the first phase

## ed3d-plan-and-execute 1.3.1

Improves resolution of Definition of Done in design plans.

**Changed:**
- Definition of Done is now written to the design document immediately after user confirmation (Phase 3), rather than being reconstructed later during documentation (Phase 5)
- Design document file is created in Phase 3 with DoD and placeholders for Summary/Glossary
- writing-design-plans skill now appends body sections and generates only Summary/Glossary

**Fixed:**
- Corrected stale skill name references ("subagent-driven-development", "executing-plans") to "executing-an-implementation-plan"
- Reinforced that Minor issues from code review must be fixed (model was skipping them)
- Changed `/compact` to `/clear` between phases, with warning to copy next command first

## ed3d-plan-and-execute 1.3.0

Adds legibility header to design plans for human reviewers.

**New:**
- **Phase 3: Definition of Done** — New checkpoint after clarification to confirm deliverables before brainstorming
- **Legibility header** — Design plans now include Definition of Done, Summary, and Glossary sections at the top
- **Subagent extraction** — Uses fresh-context subagent to generate legibility header after writing body
- **Glossary transparency** — Subagent reports omitted "obvious" terms so user can request additions

**Changed:**
- Phases renumbered 1-6 (was 1, 2, 2b, 3, 4, 5)
- Task invocations in skills now use XML block format

## ed3d-plan-and-execute 1.2.0

Added external dependency research capabilities to implementation planning.

**Changed:**
- **writing-implementation-plans**: Added tiered external dependency research workflow. Phases involving external libraries now trigger research via `internet-researcher` (for docs/standards) with escalation to `remote-code-researcher` (for source code) when documentation is insufficient.

**New capabilities:**
- Decision framework for when to research external dependencies
- Tiered research approach: docs first, source code when needed
- External dependency findings section in phase output templates
- Updated per-phase workflow to include research step
- New rationalizations to prevent skipping external research

## ed3d-plan-and-execute 1.1.0

Corrects design plan level of detail. These changes were a missed port from the internal plugin marketplace and were intended for 1.0.0. This release represents the plugin "as intended."

**Changed:**
- **writing-design-plans**: Design plans now stay at component/module level, not task level. Contracts/interfaces can be fully specified; implementation code cannot.
- **brainstorming**: Added guidance on level of detail in Phase 3. Validates boundaries, not behavior.
- **writing-implementation-plans**: Strengthened codebase verification as source of truth. Implementation plans generate code fresh from investigation, never copy from design.
- **README**: Added "Philosophy: What Each Phase Produces" section explaining archival vs just-in-time distinction.

## ed3d-research-agents 1.1.0

Added `remote-code-researcher` agent for investigating external codebases by cloning and analyzing their source code.

**New agent:**
- `remote-code-researcher` - Answers questions about external libraries/frameworks by cloning repos to temp directories and investigating the actual source code. Combines web search (to find repos) with codebase investigation (to analyze cloned code).

## All plugins 1.0.0

Initial release of ed3d-plugins collection.
