# Changelog

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
