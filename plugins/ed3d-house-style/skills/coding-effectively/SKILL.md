---
name: coding-effectively
description: ALWAYS use this skill when writing or refactoring code. Includes context-dependent sub-skills to empower different coding styles across languages and runtimes.
user-invocable: false
---

# Coding Effectively

## Required Sub-Skills

**ALWAYS REQUIRED:**
- `howto-functional-vs-imperative` - Separate pure logic from side effects
- `defense-in-depth` - Validate at every layer data passes through

**CONDITIONAL:** Use these sub-skills when applicable:
- `howto-code-in-typescript` - TypeScript code
- `howto-code-in-rust` - Rust code
- `howto-develop-with-postgres` - PostgreSQL database code
- `programming-in-react` - React frontend code
- `writing-good-tests` - Writing or reviewing tests
- `property-based-testing` - Tests for serialization, validation, normalization, pure functions

## Property-Driven Design

When designing features, think about properties upfront. This surfaces design gaps early.

**Discovery questions:**

| Question | Property Type | Example |
|----------|---------------|---------|
| Does it have an inverse operation? | Roundtrip | `decode(encode(x)) == x` |
| Is applying it twice the same as once? | Idempotence | `f(f(x)) == f(x)` |
| What quantities are preserved? | Invariants | Length, sum, count unchanged |
| Is order of arguments irrelevant? | Commutativity | `f(a, b) == f(b, a)` |
| Can operations be regrouped? | Associativity | `f(f(a,b), c) == f(a, f(b,c))` |
| Is there a neutral element? | Identity | `f(x, 0) == x` |
| Is there a reference implementation? | Oracle | `new(x) == old(x)` |
| Can output be easily verified? | Easy to verify | `is_sorted(sort(x))` |

**Common design questions these reveal:**
- "What about deleted/deactivated entities?"
- "Case-sensitive or not?"
- "Stable sort or not? Tie-breaking rules?"
- "Which algorithm? Configurable?"

Surface these during design, not during debugging.

## Core Engineering Principles

### Correctness Over Convenience

Model the full error space. No shortcuts.

- Handle all edge cases: race conditions, timing issues, partial failures
- Use the type system to encode correctness constraints
- Prefer compile-time guarantees over runtime checks where possible
- When uncertain, explore and iterate rather than assume

**Don't:**
- Simplify error handling to save time
- Ignore edge cases because "they probably won't happen"
- Use `any` or equivalent to bypass type checking

### Error Handling Philosophy

**Two-tier model:**

1. **User-facing errors**: Semantic exit codes, rich diagnostics, actionable messages
2. **Internal errors**: Programming errors that may panic or use internal types

**Error message format:** Lowercase sentence fragments for "failed to {message}".

```
Good: failed to connect to database: connection refused
Bad:  Failed to Connect to Database: Connection Refused

Good: invalid configuration: missing required field 'apiKey'
Bad:  Invalid Configuration: Missing Required Field 'apiKey'
```

Lowercase fragments compose naturally: `"operation failed: " + error.message` reads correctly.

### Pragmatic Incrementalism

- Prefer specific, composable logic over abstract frameworks
- Evolve design incrementally rather than perfect upfront architecture
- Don't build for hypothetical future requirements
- Document design decisions and trade-offs when making non-obvious choices

**The rule of three applies to abstraction:** Don't abstract until you've seen the pattern three times. Three similar lines of code is better than a premature abstraction.

## File Organization

### Descriptive File Names Over Catch-All Files

Name files by what they contain, not by generic categories.

**Don't create:**
- `utils.ts` - Becomes a dumping ground for unrelated functions
- `helpers.ts` - Same problem
- `common.ts` - What isn't common?
- `misc.ts` - Actively unhelpful

**Do create:**
- `string-formatting.ts` - String manipulation utilities
- `date-arithmetic.ts` - Date calculations
- `api-error-handling.ts` - API error utilities
- `user-validation.ts` - User input validation

**Why this matters:**
- Discoverability: Developers find code by scanning file names
- Cohesion: Related code stays together
- Prevents bloat: Hard to add unrelated code to `string-formatting.ts`
- Import clarity: `import { formatDate } from './date-arithmetic'` is self-documenting

**When you're tempted to create utils.ts:** Stop. Ask what the functions have in common. Name the file after that commonality.

### Module Organization

- Keep module boundaries strict with restricted visibility
- Platform-specific code in separate files: `unix.ts`, `windows.ts`, `posix.ts`
- Use conditional compilation or runtime checks for platform branching
- Test helpers in dedicated modules/files, not mixed with production code

## Cross-Platform Principles

### Use OS-Native Logic

Don't emulate Unix on Windows or vice versa. Use each platform's native patterns.

**Bad:** Trying to make Windows paths behave like Unix paths everywhere.

**Good:** Accept platform differences, handle them explicitly.

```typescript
// Platform-specific behavior
if (process.platform === 'win32') {
  // Windows-native approach
} else {
  // POSIX approach
}
```

### Platform-Specific Files

When platform differences are significant, use separate files:

```
process-spawn.ts        // Shared interface and logic
process-spawn-unix.ts   // Unix-specific implementation
process-spawn-windows.ts // Windows-specific implementation
```

### Document Platform Differences

When behavior differs by platform, document it in comments:

```typescript
// On Windows, this returns CRLF line endings.
// On Unix, this returns LF line endings.
// Callers should normalize if consistent output is needed.
function readTextFile(path: string): string { ... }
```

### Test on All Target Platforms

Don't assume Unix behavior works on Windows. Test explicitly:
- CI should run on all supported platforms
- Platform-specific code paths need platform-specific tests
- Document which platforms are supported

## Common Mistakes

| Mistake | Reality | Fix |
|---------|---------|-----|
| "Just put it in utils for now" | utils.ts becomes 2000 lines of unrelated code | Name files by purpose from the start |
| "Edge cases are rare" | Edge cases cause production incidents | Handle them. Model the full error space. |
| "We might need this abstraction later" | Premature abstraction is harder to remove than add | Wait for the third use case |
| "It works on my Mac" | It may not work on Windows or Linux | Test on target platforms |
| "The type system is too strict" | Strictness catches bugs at compile time | Fix the type error, don't bypass it |

## Red Flags

**Stop and refactor when you see:**

- A `utils.ts` or `helpers.ts` file growing beyond 200 lines
- Error handling that swallows errors or uses generic messages
- Platform-specific code mixed with cross-platform code
- Abstractions created for single use cases
- Type assertions (`as any`) to bypass the type system
- Code that "works on my machine" but isn't tested cross-platform

## Commit Hygiene

Applies to all languages. Commits are the unit of review and bisect; treat them with the same care as the code they contain.

- Each commit is a logical, atomic unit of change.
- Every commit must build and pass all checks (bisect-able history).
- Separate concerns: formatting fixes and refactoring go in separate commits from feature changes.
- Use simple past and present tense in bodies: "Previously X happened. With this commit, Y now happens."
- Commit message bodies use markdown. Do not use backticks in commit titles, but do use them in bodies.
