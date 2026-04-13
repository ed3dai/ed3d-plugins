---
name: asking-clarifying-questions
description: Use after initial design context is gathered, before brainstorming - resolves contradictions in requirements, disambiguates terminology, clarifies scope boundaries, and verifies assumptions to prevent building the wrong solution
user-invocable: false
---

# Asking Clarifying Questions

## Overview

Bridge the gap between raw user input and structured brainstorming by understanding what the user actually means, not what they said.

**Core principle:** Resolve contradictions first, then disambiguate. Conflicting goals must be reconciled before technical clarification - otherwise you're precisely defining the wrong thing.

**Announce at start:** "I'm using the asking-clarifying-questions skill to make sure I understand your requirements correctly."

## When to Use

Use this skill:
- After gathering initial context from user
- Before starting brainstorming or design exploration
- When user mentions technical terms that could mean multiple things
- When scope boundaries are unclear
- When assumptions need verification

Do NOT use for:
- Exploring design alternatives (that's brainstorming)
- Proposing architectures (that's brainstorming)
- Validating completed designs (that's brainstorming Phase 3)
- Asking for initial requirements (that's starting-a-design-plan Phase 1)

## Before Clarifying

Try to answer your own questions and disambiguate from the context of the working directory. Use available subagents, such as `codebase-investigator`, to explore for existing work that can help explain the the subject under clarification. When you recognize elements such as common technologies or proper nouns, use `combined-researcher` instead to synthesize both the codebase and internet searches.

You may have other skills or MCPs containing useful information, such as connections to remote datastores used for product management purposes. You should send out `haiku-general-purpose` subagents to investigate them when they're appropriate.

## What to Clarify

### 0. Contradictions (First Pass)

Before disambiguating technical details, scan for logical contradictions in requirements. If the user has stated mutually exclusive goals, resolve these first - technical clarification is wasted effort if the foundation shifts.

**Look for:**

Explicit contradictions (user stated both):
- "Real-time updates" + "batch processing is fine" → Which is the actual need?
- "Keep it simple" + "handle every edge case" → Trade-off not acknowledged
- "Use existing patterns" + "complete rewrite" → Mutually exclusive approaches
- "No external dependencies" + "integrate with Stripe" → Implicit contradiction

Impossible combinations:
- "Offline-first" + "always-current data" → Physics problem
- "Fast to build" + "infinitely extensible" → Classic impossible triangle
- "Zero latency" + "synchronous validation" → Can't have both
- "No breaking changes" + "fundamental redesign" → Pick one

Unacknowledged trade-offs:
- "Simple" often conflicts with "flexible"
- "Fast" often conflicts with "thorough"
- "Cheap" often conflicts with "custom"
- "Secure" often conflicts with "convenient"

**How to surface:**

Don't accuse - illuminate the tension:
- "I notice you mentioned X and Y - these can pull in different directions. Which takes priority?"
- "There's a trade-off between A and B here. Which matters more for this project?"
- "These two goals sometimes conflict - how should I balance them when they do?"

**Why first:**
- Contradictions reveal unconfronted trade-offs
- Resolving them changes what "right" means
- Technical disambiguation without this = building the wrong thing precisely

**After contradictions are resolved**, proceed to technical clarification.

### 1. Technical Terminology

When user mentions technical terms, disambiguate what they actually mean.

**Examples:**

User says "OAuth2" -> Ask: Which flow?
- Authorization code flow (for human users with browser redirect)
- Client credentials flow (for service-to-service auth)
- Both, depending on the use case

User says "database" -> Ask: Which kind?
- SQL (PostgreSQL, MySQL) for structured data
- NoSQL (MongoDB, DynamoDB) for flexible schema
- Already determined by existing infrastructure

User says "caching" -> Ask: What layer?
- Application-level (Redis, Memcached)
- HTTP caching (CDN, browser cache)
- Database query caching

**Use AskUserQuestion for these** - present specific options with trade-offs.

### 2. Scope Boundaries

When user mentions broad concepts, identify what's included and excluded.

**Examples:**

User says "users" -> Ask: Who exactly?
- Human users logging in via web browser
- Service accounts for API access
- Both, with different authentication flows
- Internal employees vs external customers

User says "integrate with X" -> Ask: What parts?
- Just authentication
- Full data sync
- Specific API endpoints
- Real-time webhooks vs batch imports

User says "reporting" -> Ask: What scope?
- Basic data export (CSV, Excel)
- Interactive dashboards
- Scheduled automated reports
- Real-time analytics

**Use AskUserQuestion** - present distinct scope options.

### 3. Assumptions and Constraints

When user states requirements, verify the underlying reasons and constraints.

**Examples:**

User says "must use library X" -> Ask: Why?
- Regulatory requirement (cannot change)
- Existing team expertise (preference, not hard requirement)
- Already in use elsewhere (consistency benefit)
- Misconception (might have better options)

User says "needs to be fast" -> Ask: How fast?
- Sub-100ms response time (hard requirement)
- Faster than current implementation (relative improvement)
- Perception of speed (optimistic UI, loading states)
- Actual performance bottleneck identified

User says "should follow pattern Y" -> Ask: Which aspect?
- Exact implementation (strict consistency)
- General approach (flexible adaptation)
- Just using same libraries (tooling consistency)
- Not actually required (outdated guideline)

**Use open-ended questions** for understanding "why" - allows user to explain context.

### 4. Version and API Specifics

When user mentions external services or libraries, verify current state.

**Examples:**

User says "integrate with Stripe" -> Check:
- Which Stripe API version (latest? specific?)
- Payment Intents API or older Charges API
- Which features needed (one-time, subscriptions, both)
- Already have Stripe account setup

User says "use React Router" -> Check:
- React Router v5 or v6 (breaking changes between versions)
- Already in use in codebase (follow existing patterns)
- Browser Router vs Hash Router vs Memory Router

**Quick agent queries for factual checks:**
- "What version of X exists?" -> Quick web search or codebase check
- "What's the current API?" -> Internet research for docs
- "Is Y already in use?" -> Codebase investigation

**Don't do deep research** - save that for brainstorming. Just verify basics.

### 5. Definition of Done (Required Final Step)

**Before handing off to brainstorming, you MUST establish the Definition of Done.**

The Definition of Done answers: "What does success look like? What are the deliverables?"

**After resolving contradictions and clarifying requirements:**

1. **Infer the Definition of Done** from context gathered so far:
   - What will exist when this is complete?
   - What will users/systems be able to do?
   - What are the concrete deliverables?

2. **If you have a firm grasp**, state it back and confirm:
   ```
   Use AskUserQuestion:
   "Based on our discussion, here's what I understand success looks like:

   [State the definition of done in 2-4 bullet points]

   Does this capture what you're trying to achieve?"

   Options:
   - "Yes, that's right" (proceed to brainstorming)
   - "Partially, but..." (user will clarify)
   - "No, let me explain..." (user will reframe)
   ```

3. **If the deliverables are still ambiguous**, ask targeted questions:
   - "What should exist when this is done?"
   - "How will you know this succeeded?"
   - "What's the minimum viable deliverable?"

**Why this matters:** Brainstorming explores *how* to achieve the goal. The goal must be locked in first. Otherwise you're exploring texture without knowing what shape you're filling.

**The Definition of Done becomes part of the output bundle** and will appear prominently at the top of the final design document.

## Question Techniques

### Use AskUserQuestion for Choices

When there are 2-4 distinct options with trade-offs:

```
Question: "Which OAuth2 flow are you targeting?"
Options:
  - "Authorization code flow" (human users with browser redirect)
  - "Client credentials flow" (service-to-service automated auth)
  - "Both flows" (supports human users AND service accounts)
```

**Benefits:**
- Forces explicit choice
- Shows trade-offs clearly
- Prevents vague "maybe both" responses
- Structured for decision-making

### Use Open-Ended Questions for Why

When you need to understand reasoning or context:

"Why is X a requirement?"
"What problem does Y solve?"
"What happens if we don't include Z?"

**Benefits:**
- Uncovers hidden constraints
- Reveals user's mental model
- Identifies assumptions to challenge
- Provides context for brainstorming

### Use Quick Queries for Facts

When you need to verify something factual:

- Dispatch codebase-investigator: "Is library X already in use?"
- Quick web search: "What's the current version of API Y?"
- File read: "Check package.json for existing auth dependencies"

**Don't get distracted** - these are quick checks, not research projects.

## Output: Context Bundle for Brainstorming

After clarification, create a clear summary to pass to brainstorming:

**Resolved trade-offs:**
- Speed over flexibility (chose simple implementation, accept less configurability)
- Security over convenience (chose strict validation, accept more friction)
- Consistency over ideal (chose existing patterns, accept suboptimal in isolation)

**Clarified requirements:**
- OAuth2 client credentials flow (service-to-service)
- External customers only (not internal employees)
- Stripe Payment Intents API (latest version)
- Must comply with PCI DSS Level 1 (regulatory constraint)
- "Fast" means sub-200ms p99 response time (measured requirement)

**Verified assumptions:**
- React Router v6 already in use (follow existing patterns)
- PostgreSQL database (existing infrastructure)
- No existing auth system (greenfield)

**Scope boundaries:**
- IN: Service account creation, token issuance, token validation
- OUT: Human user login, SSO integration, password management

This bundle gives brainstorming a concrete, unambiguous starting point.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Ignoring contradictions in requirements | Surface conflicting goals before technical clarification |
| Accepting vague terms at face value | Disambiguate every technical term |
| Assuming scope without verification | Ask explicit boundary questions |
| Not questioning "must have" requirements | Understand WHY behind constraints |
| Doing deep research during clarification | Quick checks only, save research for brainstorming |
| Proposing solutions while clarifying | Stay in understanding mode, no design yet |
| Skipping clarification when "seems clear" | Always clarify, assumptions are dangerous |

## When to Stop Clarifying

Stop and move to brainstorming when:
- Contradictions are resolved (trade-offs explicitly chosen)
- Technical terms are disambiguated
- Scope boundaries are explicit
- Constraints are understood (not just stated)
- Assumptions are verified
- No major ambiguities remain

**You don't need perfect information** - just enough to brainstorm effectively.

If brainstorming reveals new ambiguities, you can return to clarification.

## Integration with Design Workflow

This skill sits between context gathering and brainstorming:

```
Context Gathering (starting-a-design-plan Phase 1)
  -> User provides: "Build OAuth2 integration for our API"

Clarification (this skill)
  -> Disambiguate: Which OAuth2 flow? What scope? Why OAuth2?
  -> Output: Service accounts, client credentials, PCI compliance

Brainstorming (starting-a-design-plan Phase 3)
  -> Explore: Architecture options, library choices, implementation phases
  -> Uses clarified requirements as foundation
```

**Purpose:** Ensure brainstorming builds the right thing, not the wrong thing well.
