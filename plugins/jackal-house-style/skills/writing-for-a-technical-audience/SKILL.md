---
name: writing-for-a-technical-audience
description: Use when writing documentation, guides, API references, or technical content for developers - enforces clarity, conciseness, and authenticity while avoiding AI writing patterns that signal inauthenticity
user-invocable: false
---

# Writing for a Technical Audience

## Overview

**Core principle:** Technical writing must be clear, concise, and authentic. Clarity and technical depth are not opposites - you can have both. Avoid AI writing patterns that make content feel robotic or inauthentic.
￼
**Why this matters:** Developers value their time. Clear documentation builds trust. AI-like writing patterns (identified through research) make content feel generic and untrustworthy. Technical depth without clarity frustrates users. Clarity without depth leaves them stuck.

## When to Use

**Use this skill when:**
- Writing API documentation or references
- Creating guides, tutorials, or how-to content
- Documenting code, features, or architecture
- Writing technical blog posts or articles
- Reviewing technical content for clarity

**Trigger symptoms:**
- "Does this sound too robotic?"
- Writing feels formal or stiff
- Using phrases like "delve into" or "leverage"
- Explaining obvious things instead of getting to the point
- Uncertain if content is clear enough

## The Three Pillars

### 1. Clarity

Developers should understand on first read. No re-reading required.

**Techniques:**
- Short sentences (15-20 words average)
- Short paragraphs (2-4 sentences)
- Active voice over passive
- One concept per paragraph
- Define technical terms on first use

### 2. Conciseness

Every word serves a purpose. Remove noise and filler.

**Techniques:**
- Delete throat-clearing ("Let me explain," "It's important to note")
- Cut hedging language ("basically," "generally speaking")
- Remove marketing fluff ("powerful," "robust," "seamless")
- Use direct language ("use" not "leverage," "show" not "illuminate")

### 3. Consistency

Same terminology, structure, and voice throughout.

**Techniques:**
- Pick one term and stick to it (not "endpoint," "URL," "route" interchangeably)
- Use consistent code formatting
- Maintain same tone across all content
- Follow established patterns for similar content types

## Avoid AI Writing Patterns

Research shows specific phrases and structures that readers identify as AI-generated. Avoid these to maintain authenticity.

### AI Phrases to Never Use

| AI Phrase | Why It's Bad | Use Instead |
|-----------|-------------|-------------|
| "delve into" | Overly formal, 269x spike post-ChatGPT | "explore," "examine," "look at" |
| "leverage" | Corporate jargon | "use," "take advantage of" |
| "robust" / "seamless" | Vague marketing adjectives | Be specific about what you mean |
| "at its core" | Condescending simplification | "fundamentally" (use rarely) or delete |
| "cutting-edge" / "revolutionary" | Empty hype | Describe actual features |
| "streamline" / "optimize" | Vague promises | "speed up," "reduce," "improve" |
| "foster" / "cultivate" | Bland corporate speak | Use direct action verbs |
| "unlock the potential" | Cliched metaphor | State specific outcome |
| "in today's fast-paced world" | Generic filler | Delete entirely |
| "needless to say" | If needless, don't say it | Delete |

### Throat-Clearing to Delete

**Never start with:**
- "Let me explain..."
- "It's important to note that..."
- "It's worth noting..."
- "In essence..."
- "Let's explore..."

**Fix:** Start with substance. Delete the preamble.

### Hedging Language to Eliminate

| Hedged | Confident |
|--------|-----------|
| "I think we should..." | "We should..." |
| "It would be great if..." | "Please do X" |
| "Should be able to..." | "Can complete..." |
| "Basically..." | Delete it |
| "Generally speaking..." | Be specific or remove |
| "One might argue..." | "This indicates..." |

**Why hedging fails:** Makes you sound uncertain even when you're correct. State facts directly.

### Transition Word Overuse

AI defaults to formal Victorian-era connectors. Use simpler alternatives or break paragraphs.

| Overused AI | Better |
|------------|--------|
| Moreover / Furthermore | Plus, also, and |
| However / Nevertheless | But, though, still |
| Additionally | And, plus |
| Consequently / As a result | So, then |
| That being said | But (or delete) |
| Indeed / Interestingly | Often delete entirely |
| In conclusion | End cleanly without announcing it |

## Technical Writing Patterns

### Explain WHY for These Cases

**ALWAYS explain why when:**

1. **Design decisions with tradeoffs**
   - Good: "We use pagination instead of cursors because it's simpler for most use cases and maintains consistent ordering"
   - Bad: "We use pagination" (no context for when to deviate)

2. **Non-obvious patterns**
   - Good: "Row Level Security must be enabled on all tables exposed via the Data API because it enforces security at the database level, preventing bypass through direct SQL access"
   - Bad: "Enable RLS on all tables" (why?)

3. **Breaking from conventions**
   - Good: "This API uses POST for reads because GET requests can't include request bodies in some HTTP clients"
   - Bad: "Use POST to fetch data" (violates REST conventions without justification)

**When "how" alone suffices:**
- Mechanical steps with no alternatives ("Click Save")
- Standard practices ("Use npm install")
- When you genuinely don't know why (document behavior, note uncertainty)

### Code Examples: One Excellent Example

**Don't:**
- Implement in 5 languages
- Create fill-in-the-blank templates
- Write perfect-world examples with no error handling

**Do:**
- One complete, runnable example
- Include error handling
- Show realistic usage
- Comment WHY, not what

**Good Example Pattern:**

```python
# Good: Complete, realistic, explains why
try:
    response = await fetch_user(user_id)
    # Check status before assuming success - API returns 200 for "not found"
    if response.status != 200:
        raise APIError(f"Failed to fetch user: {response.status}")
    return response.json()
except NetworkError as e:
    # Network failures are retryable - log and re-raise for retry logic
    logger.warning(f"Network error fetching user {user_id}: {e}")
    raise
```

**Bad Example Pattern:**

```python
# Bad: Perfect world, no context, brittle
response = await fetch_user(user_id)
return response.json()
```

### Progressive Disclosure

Layer complexity. Simple first, then depth.

**Pattern:**
1. **Basic explanation** - what it does, core concept
2. **Simple example** - minimal working code
3. **Advanced section** - edge cases, configuration, tradeoffs
4. **Reference** - complete API surface

**Good:**
```markdown
## Authentication

All API requests require an API key in the Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" https://api.example.com/users
```

### Advanced: Token Rotation

For production systems, rotate API keys every 90 days...
```

**Bad:**
```markdown
## Authentication

Authentication can be performed using several methods including API keys, OAuth 2.0, or JWT tokens. The choice depends on your security requirements, user experience goals, and architectural constraints. Let's explore each option...
```

(Too much upfront. Start simple.)

## Anti-Patterns from Real Documentation

### 1. Assumes Too Much

**Bad:**
> "Simply connect your ETLOrchestrator to the HydraNode endpoint. Once a connection is established, instantiate a DataStream by passing your KinesisConfiguration."

**Why it fails:** Jargon firehose with no definitions, no links, no onramp for beginners.

**Fix:** Define terms, link to prerequisites, provide Getting Started guide.

### 2. Perfect World Examples

**Bad:**
```javascript
const myFile = document.getElementById('file-input').files[0];
const response = await uploadFile('/api/upload', myFile);
console.log('File uploaded successfully!');
```

**Why it fails:** No error handling, ignores edge cases (no file selected, network failure, file too large).

**Fix:** Wrap in try-catch, check response status, handle undefined files.

### 3. Vague and Unhelpful

**Bad:**
- `getUser(userId)`: "Gets a user by their ID."
- `class DataProcessor`: "A class for processing data."
- `processData(data)`: "Processes the data."

**Why it fails:** Tautological. Says nothing beyond the function name.

**Fix:** Describe behavior, parameters, return values, exceptions. "Fetches user record from database, returns null if user doesn't exist. Throws AuthError if API key lacks read permissions."

## Pro-Examples from Industry Leaders

### Supabase (Clarity + Depth)

> "Row Level Security (RLS) is a PostgreSQL feature that allows you to control which rows a user can access in a table. When you enable RLS on a table, all SELECT, INSERT, UPDATE, and DELETE operations are subject to a security policy. A policy is a SQL expression that returns a boolean value. If the expression returns true, the operation is allowed to proceed. If it returns false or null, the operation is denied."

**Why it works:** Defines RLS, explains scope (CRUD operations), defines mechanism (policy = SQL boolean expression). Dense with information, perfectly clear.

### Stripe (Predictable Contract)

> "Stripe uses conventional HTTP response codes to indicate the success or failure of an API request. In general: Codes in the 2xx range indicate success. Codes in the 4xx range indicate an error that failed given the information provided. Codes in the 5xx range indicate an error with Stripe's servers."

**Why it works:** Establishes predictable contract for fundamental API behavior. Technical, precise, immediately useful.

### Astro (Anticipates Questions)

> "You can run create-astro anywhere on your machine, so you don't have to create an empty directory for your project first. If you don't have an empty directory yet, the wizard will help you create one."

**Why it works:** Anticipates common beginner question ("Do I need to make a folder first?") and answers it proactively.

### Tailwind CSS (Teaches Philosophy)

> "The biggest maintainability concern when using a utility-first approach is managing commonly repeated utility combinations. The traditional approach is to extract repeated utilities into a component class. We believe that @apply should be used sparingly. The best way to manage repeated utility combinations is to create reusable components with a templating language."

**Why it works:** Identifies problem, presents common solution, explains why that solution is suboptimal, guides toward better approach. Teaches philosophy, not just features.

## Writing That Feels Human

### Use Contractions

**AI defaults to:**
- "It is important that you do not..."
- "You will need to..."

**Human writing:**
- "It's important that you don't..."
- "You'll need to..."

### Vary Sentence Length

**AI writes:**
Every paragraph is 3-4 sentences. Every sentence is 15-20 words. Everything feels perfectly balanced and rhythmic in an uncanny way.

**Human writes:**
Short sentences create emphasis. Longer sentences provide context, explanation, or explore nuance that requires more breathing room. Mix them. Create rhythm naturally.

### Add Personality

**AI avoids:**
- First person ("I," "we")
- Opinions
- Personal anecdotes
- Humor

**Human includes:**
- "We tried the obvious solution first and it failed"
- "I found this approach more practical because..."
- Opinions grounded in experience
- Self-aware observations

### Break Grammar Rules Intentionally

**AI never:**
- Starts sentences with "And" or "But"
- Uses sentence fragments
- Ends with prepositions

**Human does:**
- "And that's exactly the point." (emphasis)
- "This is what we're dealing with." (natural)

### Be Specific

**AI writes vaguely:**
- "This approach offers significant benefits"
- "Companies have seen improved results"

**Human writes specifically:**
- "We reduced latency from 450ms to 120ms"
- "Three team members raised concerns about X"

## Code Comments and Documentation

### Punctuation

Always use periods at the end of code comments.

```typescript
// Good: Validates user input before processing.
// Bad: validates user input before processing
```

### Headings

Use sentence case in all headings. Never title case.

```markdown
Good: ## Error handling patterns
Bad:  ## Error Handling Patterns

Good: ### When to use async
Bad:  ### When To Use Async
```

### Error Messages

Format error messages as lowercase sentence fragments. They compose naturally when chained.

```
Good: failed to parse configuration: invalid JSON at line 42
Bad:  Failed to Parse Configuration: Invalid JSON at Line 42
```

The lowercase format works because errors often chain: `"operation failed: " + innerError.message` reads correctly.

## Red Flags - Review Checklist

Before publishing, check for these issues:

- [ ] No AI phrases ("delve," "leverage," "robust," "at its core")
- [ ] No throat-clearing openings ("Let me explain," "It's important to note")
- [ ] No hedging language ("basically," "generally speaking")
- [ ] No marketing fluff ("powerful," "revolutionary," "cutting-edge")
- [ ] Sentence length varies (not all 15-20 words)
- [ ] Paragraph length varies (not all 3-4 sentences)
- [ ] Contractions used naturally ("it's" not "it is")
- [ ] Active voice, clear actors (not "it can be seen that")
- [ ] Code examples include error handling
- [ ] WHY explained for design decisions
- [ ] Technical terms defined on first use
- [ ] Specific numbers/names/details (not vague claims)
- [ ] Read aloud test - does it sound natural?
- [ ] Code comments end with periods
- [ ] Headings use sentence case (not Title Case)
- [ ] Error messages are lowercase sentence fragments

## Common Mistakes and Fixes

| Mistake | Reality | Fix |
|---------|---------|-----|
| "Just being thorough with explanations" | You're explaining obvious things. | Delete explanations of what developers already know. |
| "Keeping it professional with formal language" | Formal = robotic. | Use contractions, conversational tone, natural language. |
| "Covering all the edge cases upfront" | Overwhelms reader. | Basic case first, advanced section for edge cases. |
| "Using precise technical terminology" | Jargon without definitions loses readers. | Define terms on first use, link to glossary. |
| "Being careful with hedging language" | Hedging makes you sound uncertain. | State facts directly. Remove qualifiers. |
| "Perfect code examples look cleaner" | Perfect world examples are brittle in practice. | Include error handling, show realistic usage. |
| "More examples = more helpful" | Too many examples = noise. | One excellent, complete example beats five shallow ones. |

## Summary

**Technical writing in three rules:**

1. **Clear and concise** - Short sentences, short paragraphs, active voice, no filler
2. **Authentic voice** - Contractions, varied rhythm, personality, specific details
3. **Explain why** - Design decisions, tradeoffs, non-obvious patterns need justification

**Avoid AI markers:** No "delve," "leverage," "robust." No throat-clearing. No hedging. No formal transitions.

**One excellent example** beats five mediocre ones. Include error handling. Show realistic usage.

**Technical depth + clarity are not opposites.** You can have both. Supabase, Stripe, and Cloudflare prove this daily.

**Read aloud test:** If it sounds robotic or overly formal, rewrite it.
