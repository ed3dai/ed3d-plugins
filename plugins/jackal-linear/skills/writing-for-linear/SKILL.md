---
name: writing-for-linear
description: Use when composing any text that will appear in Linear - issue descriptions, status-change comments, or inline comments. Provides content standards for each context to ensure clear, consistent, and useful Linear content.
user-invocable: false
---

# writing-for-linear

## Overview

This skill governs three writing contexts in Linear:

1. **Issue descriptions** — written when creating or updating a Linear issue's main body
2. **Status-change comments** — brief updates posted when issue status changes (PR created, merged)
3. **Inline comments** — conversational notes posted mid-work for questions, blockers, or observations

Identify which context applies, then follow the corresponding section.

---

## Context 1: Issue Descriptions

Issue descriptions are the primary record of what needs to be built and why. They are read by engineers, reviewers, and stakeholders.

### Principles

- **Outcome-focused.** Lead with what the user or system will be able to do after this is done. Not what code will be written.
- **Structured.** Use sections to separate context, requirements, and acceptance criteria.
- **Unambiguous.** Every requirement should be verifiable — either passes or fails.

### Template

```markdown
## Summary

One or two sentences describing the feature or fix and its business purpose.

## Background

Why this needs to exist. What problem it solves. What breaks or is missing without it.
Keep to 2-4 sentences. Skip if the Summary is self-explanatory.

## Requirements

- Requirement 1: [observable behavior or outcome]
- Requirement 2: [observable behavior or outcome]
...

## Acceptance Criteria

- [ ] [specific, testable condition that must be true when done]
- [ ] [specific, testable condition that must be true when done]
...

## Out of scope

- [what this issue explicitly does not cover, if clarification is needed]
```

### Rules

- Do not write implementation details in the description (no file names, function names, or code)
- Each acceptance criterion must be independently verifiable
- Use imperative mood for requirements: "The system must...", "Users can..."
- Keep the entire description under 500 words

---

## Context 2: Status-Change Comments

Status-change comments are short automated updates posted when an issue transitions between workflow states. They are read quickly — often in notifications.

### Principles

- **Brief.** One paragraph maximum.
- **Link the work.** Always include a link to the PR or commit.
- **State what changed.** One sentence on what state changed and why.

### Template: PR Created (In Review)

```
PR opened for review: [PR title]
[PR URL]

[One sentence on what this PR implements — the core change in plain English.]
```

**Example:**
```
PR opened for review: feat(jackal-linear): add PostToolUse hook for Linear status reminders
https://github.com/jgreaney-HCG/jackal-plugins/pull/42

Adds a Python hook that detects gh pr create and git merge commands and injects a reminder to update Linear when a .linear-issue file is present.
```

### Template: Merged (Done)

```
Merged to [branch]. Issue complete.
[PR URL or commit hash]

[One sentence on the outcome — what can users or the system now do.]
```

**Example:**
```
Merged to main. Issue complete.
https://github.com/jgreaney-HCG/jackal-plugins/pull/42

The jackal-linear plugin is now installed and ready for use — developers can start design sessions from Linear issues and have status updates synced automatically.
```

### Rules

- Maximum 3-4 sentences total
- The link must appear on its own line (makes it clickable in Linear)
- Do not describe implementation details or file changes
- Present tense for the outcome sentence

---

## Context 3: Inline Comments

Inline comments are conversational notes posted mid-work — questions that need answers, blockers, or observations for the team. They are not status updates.

### Principles

- **Conversational.** Write as if speaking to a colleague. First person is fine.
- **Actionable.** Every inline comment should have a clear ask or point. Don't post observations without a purpose.
- **Scoped.** Inline comments are for things that affect this specific issue. Cross-cutting concerns belong in separate issues.

### Patterns

**Asking a question:**
```
Quick question before I proceed: [specific question]?

Context: [one sentence explaining why this matters for the current work]
```

**Reporting a blocker:**
```
Blocked on [specific thing].

Need: [what would unblock]
Impact: [what is delayed while this is unresolved]
```

**Sharing an observation:**
```
Noticed [observation] while working on [task].

[Whether this needs action: "Flagging in case it affects the timeline" or "No action needed, just noting for the record."]
```

### Rules

- Do not use inline comments to post status updates — use the status-change comment template instead
- Keep to 3-5 sentences
- Tag relevant team members if the comment requires a response from a specific person
- Do not post inline comments that say "working on this" — that information belongs in the status field

---

## Generating a Comment

When invoked by `linear-workflow` to compose a comment:

1. Identify the context (status-change or inline) from the invocation details
2. Apply the corresponding template
3. Fill in the PR URL or commit hash from the context provided
4. Return the composed comment text — do NOT post it yourself; `linear-workflow` will post it via MCP
