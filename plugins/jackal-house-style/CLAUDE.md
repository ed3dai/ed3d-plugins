# ed3d House Style

This repository contains coding standards, patterns, and skills for ed3d projects.

## Purpose

This repository defines:
- **Coding patterns** - FCIS (Functional Core, Imperative Shell) and other architectural patterns
- **Skills** - Reusable techniques and reference guides for Claude instances
- **Standards** - Style guides, conventions, and best practices

## Repository Structure

```
jackal-house-style/
├── skills/           # Skills for Claude instances
├── agents/           # (Reserved for future use)
└── CLAUDE.md         # This file
```

## Working with Skills

### Using Skills in This Repository

When working in this repository to create or modify skills, YOU MUST use the `writing-skills` skill:

```
@skill:writing-skills
```

This skill applies Test-Driven Development principles to documentation and ensures skills are effective and bulletproof.

### What Makes a Good Skill

**Core requirements:**

1. **YAML frontmatter** with exactly two fields:
   ```yaml
   ---
   name: skill-name-with-hyphens
   description: Use when [triggering conditions] - [what it does, third person]
   ---
   ```

2. **Valid UTF-8 encoding** - No fancy Unicode characters that break file parsing
   - Use ASCII arrows: `->` not `→`
   - Use ASCII quotes: `"` not `"`
   - Use ASCII apostrophes: `'` not `'`
   - Use standard ASCII characters throughout

3. **Description optimization**:
   - Start with "Use when..."
   - Include specific triggers and symptoms
   - Write in third person (injected into system prompt)
   - Keep under 500 characters if possible

4. **Concise content**:
   - Target < 500 words for most skills
   - Context window is a public good
   - Every token competes with conversation history

5. **Clear structure**:
   ```markdown
   ## Overview
   Core principle in 1-2 sentences

   ## When to Use
   Bullet list with symptoms and use cases

   ## Core Pattern
   Before/after examples

   ## Common Mistakes
   Rationalization table with corrections

   ## Red Flags
   List of stop-and-refactor signals
   ```

6. **One excellent code example** (not five mediocre ones in different languages)

### Common Pitfalls

**Encoding issues:**
- Test with `file -i SKILL.md` to verify UTF-8
- If you see charset errors, check for non-ASCII characters
- Common culprits: smart quotes, em dashes, Unicode arrows

**Overly verbose:**
- Don't explain what Claude already knows
- Don't write narratives about specific sessions
- Keep it reference-focused, not story-focused

**Weak descriptions:**
- ❌ "Helps with testing" (too vague)
- ✅ "Use when tests have race conditions or timing dependencies - replaces arbitrary timeouts with condition polling"

**Missing persuasion elements for discipline skills:**
- No rationalization table
- No red flags section
- Weak authority language (use "YOU MUST", "NEVER", "No exceptions")

### Testing Skills (Optional but Recommended)

The writing-skills skill emphasizes TDD for documentation:
1. Run baseline scenario WITHOUT skill (document failures)
2. Write skill addressing those failures
3. Run scenario WITH skill (verify compliance)
4. Iterate to close loopholes

For this repository's skills, rigorous testing is optional but encouraged for discipline-enforcing skills.

## Core Patterns

### FCIS (Functional Core, Imperative Shell)

See `skills/howto-functional-vs-imperative/SKILL.md` for complete details.

**Summary:**
- **Functional Core:** Pure functions only. No I/O except logging. Easy to test.
- **Imperative Shell:** I/O coordination only. Minimal logic. Calls Core.
- **Mandatory:** Add pattern classification comment to every application code file.

**Logger exception:** Loggers are explicitly permitted in Functional Core files.

## Contributing

When adding new skills:
1. Use `@skill:writing-skills` for guidance
2. Follow the structure and requirements above
3. Verify UTF-8 encoding
4. Keep descriptions concrete and trigger-focused
5. Test the skill if enforcing discipline

## Questions?

Refer to `@skill:writing-skills` for comprehensive guidance on skill creation.
