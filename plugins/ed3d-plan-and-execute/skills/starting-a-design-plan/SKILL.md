---
name: starting-a-design-plan
description: Use when beginning any design process - orchestrates gathering context, clarifying requirements, brainstorming solutions, and documenting validated designs to create implementation-ready design documents
---

# Starting a Design Plan

## Overview

Orchestrate the complete design workflow from initial idea to implementation-ready documentation through six structured phases: context gathering, clarification, definition of done, brainstorming, design documentation, and planning handoff.

**Core principle:** Progressive information gathering -> clear understanding -> creative exploration -> validated design -> documented plan.

**Announce at start:** "I'm using the starting-a-design-plan skill to guide us through the design process."

## Quick Reference

| Phase | Key Activities | Output |
|-------|---------------|--------|
| **1. Context Gathering** | Ask for freeform description, constraints, goals, URLs, files | Initial context bundle |
| **2. Clarification** | Invoke asking-clarifying-questions skill | Disambiguated requirements |
| **3. Definition of Done** | Synthesize and confirm deliverables before brainstorming | Confirmed success criteria |
| **4. Brainstorming** | Invoke brainstorming skill | Validated design (in conversation) |
| **5. Design Documentation** | Invoke writing-design-plans skill | Committed design document |
| **6. Planning Handoff** | Offer to invoke writing-plans skill | Implementation plan (optional) |

## The Process

**REQUIRED: Create TodoWrite tracker at start**

Use TodoWrite to create todos for each phase:

- Phase 1: Context Gathering (initial information collected)
- Phase 2: Clarification (requirements disambiguated)
- Phase 3: Definition of Done (deliverables confirmed)
- Phase 4: Brainstorming (design validated)
- Phase 5: Design Documentation (design written to docs/design-plans/)
- Phase 6: Planning Handoff (implementation plan offered/created)

Mark each phase as in_progress when working on it, completed when finished.

### Phase 1: Context Gathering

**Never skip this phase.** Even if the user provides detailed information, ask for anything missing.

Mark Phase 1 as in_progress in TodoWrite.

**Ask the user to provide (freeform, not AskUserQuestion):**

"I need some information to start the design process. Please provide what you have:

**What are you designing?**
- High-level description of what you want to build
- Goals or success criteria
- Any known constraints or requirements

**Context materials (very helpful if available):**
- URLs to relevant documentation, APIs, or examples
- File paths to existing code or specifications in this repository
- Any research you've already done

**Project state:**
- Are you starting fresh or extending existing functionality?
- Are there existing patterns in the codebase I should follow?
- Any architectural decisions already made?

Share whatever details you have. We'll clarify anything unclear in the next step."

**Progressive prompting:** If user already provided some of this information, acknowledge what you have and ask only for what's missing.

**Example:**
"You mentioned OAuth2 integration. I have the high-level goal. To help design this effectively, I need:
- Any constraints (regulatory, existing auth system, etc.)
- URLs to the OAuth2 provider's documentation (if you have them)
- Whether this is for human users, service accounts, or both"

Mark Phase 1 as completed when you have initial context.

### Phase 2: Clarification

Mark Phase 2 as in_progress in TodoWrite.

**REQUIRED SUB-SKILL:** Use ed3d-plan-and-execute:asking-clarifying-questions

Announce: "I'm using the asking-clarifying-questions skill to make sure I understand your requirements correctly."

The clarification skill will:
- Use subagents to try to disambiguate before raising questions to the user
- Disambiguate technical terms ("OAuth2" -> which flow?)
- Identify scope boundaries ("users" -> humans? services? both?)
- Clarify assumptions ("integrate with X" -> which version?)
- Understand constraints ("must use Y" -> why?)

**Output:** Clear understanding of what user means, ready to confirm Definition of Done.

Mark Phase 2 as completed when requirements are disambiguated.

### Phase 3: Definition of Done

Before brainstorming the *how*, lock in the *what*. Brainstorming explores texture and approach — it assumes the goal is already clear.

Mark Phase 3 as in_progress in TodoWrite.

**Synthesize the Definition of Done from context gathered so far:**

From Phases 1-2 (Context Gathering and Clarification), you should be able to infer or extract:
- What the deliverables are (what gets built/changed)
- What success looks like (how we know it's done)
- What's explicitly out of scope

**If the Definition of Done is clear:**

State it back to the user and confirm using AskUserQuestion:

```
Question: "Before we explore approaches, let me confirm what success looks like:"
Options:
  - "Yes, that's right" (Definition of Done is accurate)
  - "Needs adjustment" (User will clarify what's missing or wrong)
```

Present the Definition of Done as a brief statement (2-4 sentences) covering:
- Primary deliverable(s)
- Success criteria
- Key exclusions (if any were discussed)

**If the Definition of Done is unclear:**

Ask targeted questions to nail it down. Use AskUserQuestion when there are discrete options, or open-ended questions when you need the user to describe their vision.

Examples of clarifying questions:
- "What's the primary deliverable here — is it [X] or [Y]?"
- "How will you know this is done? What would you test or demonstrate?"
- "You mentioned [feature]. Is that in scope for this design, or a future addition?"

**Do not proceed to brainstorming until Definition of Done is confirmed.**

The Definition of Done will be included at the top of the design document for reviewer legibility.

Mark Phase 3 as completed when user confirms the Definition of Done.

### Phase 4: Brainstorming

With clear understanding from Phases 1-3, explore design alternatives and validate the approach.

Mark Phase 4 as in_progress in TodoWrite.

**REQUIRED SUB-SKILL:** Use ed3d-plan-and-execute:brainstorming

Announce: "I'm using the brainstorming skill to explore design alternatives and validate the approach."

**Pass context to brainstorming:**
- Information gathered in Phase 1
- Clarifications from Phase 2
- Confirmed Definition of Done from Phase 3
- This reduces Phase 1 of brainstorming (Understanding) since much is already known

The brainstorming skill will:
- Complete any remaining understanding gaps (Phase 1)
- Propose 2-3 architectural approaches (Phase 2)
- Present design incrementally for validation (Phase 3)
- Use research agents for codebase patterns and external knowledge

**Output:** Validated design held in conversation context.

Mark Phase 4 as completed when design is validated.

### Phase 5: Design Documentation

Write the validated design to a permanent, structured document.

Mark Phase 5 as in_progress in TodoWrite.

**REQUIRED SUB-SKILL:** Use ed3d-plan-and-execute:writing-design-plans

Announce: "I'm using the writing-design-plans skill to document the validated design."

The writing-design-plans skill will:
- Write design to `docs/design-plans/YYYY-MM-DD-<topic>.md`
- Structure with implementation phases (<=8 recommended)
  - DO NOT pad out phases in order to reach the number of 8. 8 is the maximum, not the target.
- Document existing patterns followed
- Commit to git

**Output:** Committed design document ready for implementation planning.

Mark Phase 5 as completed when design document is committed.

### Phase 6: Planning Handoff

After design is documented, guide user to create implementation plan in fresh context.

Mark Phase 6 as in_progress in TodoWrite.

**Do NOT create implementation plan directly.** The user needs to compact context first.

Announce design completion and provide next steps:

```
Design complete! Design document committed to `docs/design-plans/[filename]`.

Ready to create the implementation plan? This requires fresh context to work effectively.

Run these commands in sequence:

(1) Compact your context first:
```
/compact
```

(2) Then create the implementation plan:
```
/ed3d-ed3d-plan-and-execute:start-implementation-plan @docs/design-plans/[full-filename].md .
```

(the `.` at the end is necessary or else Claude Code will eat the command and do the wrong thing.)

The start-implementation-plan command will create detailed tasks, set up a branch, and prepare for execution.
```

**Why two separate commands:**
- User can only paste one command at a time
- /compact must run first to free up context
- Implementation planning needs fresh context for codebase investigation

Mark Phase 6 as completed after providing instructions.

## When to Revisit Earlier Phases

You can and should go backward when:
- Phase 2 reveals fundamental gaps -> Return to Phase 1
- Phase 3 reveals unclear deliverables -> Return to Phase 2 for more clarification
- Phase 4 uncovers new constraints -> Return to Phase 1, 2, or 3
- User questions approach during Phase 4 -> Return to Phase 2
- Phase 4 changes the Definition of Done -> Return to Phase 3 to reconfirm
- Design documentation reveals missing details -> Return to Phase 4

**Don't force forward linearly** when going backward gives better results.

## Common Rationalizations - STOP

| Excuse | Reality |
|--------|---------|
| "User provided details, can skip context gathering" | Always run Phase 1. Ask for what's missing. |
| "Requirements are clear, skip clarification" | Clarification prevents misunderstandings. Always run Phase 2. |
| "I know what done looks like, skip confirmation" | Confirm Definition of Done explicitly. Always run Phase 3. |
| "Simple idea, skip brainstorming" | Brainstorming explores alternatives. Always run Phase 4. |
| "Design is in conversation, don't need documentation" | Documentation is contract with writing-implementation-plans. Always run Phase 5. |
| "Can invoke implementation planning directly" | Must compact first. Provide two-command workflow. |
| "I can combine phases for efficiency" | Each phase has distinct purpose. Run all six. |
| "User knows what they want, less structure needed" | Structure ensures nothing is missed. Follow all phases. |

**All of these mean: STOP. Run all six phases in order.**

## Key Principles

| Principle | Application |
|-----------|-------------|
| **Never skip brainstorming** | Even with detailed specs, always run Phase 4 (may be shorter) |
| **Progressive prompting** | Ask for less if user already provided some context |
| **Clarify before ideating** | Phase 2 prevents building the wrong thing |
| **Lock in the goal before exploring** | Phase 3 confirms what "done" means before brainstorming the how |
| **All brains in skills** | This skill orchestrates; sub-skills contain domain expertise |
| **TodoWrite tracking** | YOU MUST create and update todos for all phases |
| **Flexible progression** | Go backward when needed to fill gaps |
