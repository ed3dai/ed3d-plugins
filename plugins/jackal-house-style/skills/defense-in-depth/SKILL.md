---
name: defense-in-depth
description: Use when invalid data causes failures deep in execution - validates at every layer data passes through to make bugs structurally impossible rather than temporarily fixed
user-invocable: false
---

# Defense-in-Depth Validation

## Overview

When you fix a bug caused by invalid data, adding validation at one place feels sufficient. But that single check can be bypassed by different code paths, refactoring, or mocks.

**Core principle:** Validate at EVERY layer data passes through. Make the bug structurally impossible.

## When to Use

**Use when:**
- Invalid data caused a bug deep in the call stack
- Data crosses system boundaries (API → service → storage)
- Multiple code paths can reach the same vulnerable code
- Tests mock intermediate layers (bypassing validation)

**Don't use when:**
- Pure internal function with single caller (validate at caller)
- Data already validated by framework/library you trust
- Adding validation would duplicate identical checks at adjacent layers

## The Four Layers

### Layer 1: Entry Point Validation
**Purpose:** Reject invalid input at API/system boundary

```typescript
function createProject(name: string, workingDirectory: string) {
  if (!workingDirectory?.trim()) {
    throw new Error('workingDirectory cannot be empty');
  }
  if (!existsSync(workingDirectory)) {
    throw new Error(`workingDirectory does not exist: ${workingDirectory}`);
  }
  // ... proceed
}
```

**When needed:** Always. This is your first line of defense.

### Layer 2: Business Logic Validation
**Purpose:** Ensure data makes sense for this specific operation

```typescript
function initializeWorkspace(projectDir: string, sessionId: string) {
  if (!projectDir) {
    throw new Error('projectDir required for workspace initialization');
  }
  // ... proceed
}
```

**When needed:** When business rules differ from entry validation, or when mocks might bypass Layer 1.

### Layer 3: Environment Guards
**Purpose:** Prevent dangerous operations in specific contexts

```typescript
async function gitInit(directory: string) {
  if (process.env.NODE_ENV === 'test') {
    const normalized = normalize(resolve(directory));
    if (!normalized.startsWith(tmpdir())) {
      throw new Error(`Refusing git init outside temp dir in tests: ${directory}`);
    }
  }
  // ... proceed
}
```

**When needed:** When operation is destructive/irreversible, especially in test environments.

### Layer 4: Debug Instrumentation
**Purpose:** Capture context for forensics when other layers fail

```typescript
async function gitInit(directory: string) {
  logger.debug('git init', { directory, cwd: process.cwd(), stack: new Error().stack });
  // ... proceed
}
```

**When needed:** When debugging is difficult, or when you need to trace how bad data arrived.

## Decision Heuristic

| Situation | Layers Needed |
|-----------|---------------|
| Public API, simple validation | 1 only |
| Data crosses multiple services | 1 + 2 |
| Destructive operations (delete, init, write) | 1 + 2 + 3 |
| Chasing a hard-to-reproduce bug | 1 + 2 + 3 + 4 |
| Tests mock intermediate layers | At minimum: 1 + 3 |

## Applying the Pattern

When you find a bug caused by invalid data:

1. **Trace the data flow** - Where does the bad value originate? Where is it used?
2. **Map checkpoints** - List every function/layer the data passes through
3. **Decide which layers** - Use heuristic above
4. **Add validation** - Entry → business → environment → debug
5. **Test each layer** - Verify Layer 2 catches what bypasses Layer 1

## Quick Reference

| Layer | Question It Answers | Typical Check |
|-------|---------------------|---------------|
| Entry | Is input valid? | Non-empty, exists, correct type |
| Business | Does it make sense here? | Required for this operation, within bounds |
| Environment | Is this safe in this context? | Not in prod, inside temp dir, etc. |
| Debug | How did we get here? | Log stack, cwd, inputs |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| One validation point, call it done | Add at least entry + business layers |
| Identical checks at adjacent layers | Make each layer check something different |
| Environment guards only in prod | Add them in test too (prevent test pollution) |
| Skipping debug logging | Add it during the bug hunt, keep it |
| Validation but no useful error message | Include the bad value and expected format |

## Key Insight

During testing, each layer catches bugs the others miss:
- Different code paths bypass entry validation
- Mocks bypass business logic checks
- Edge cases need environment guards
- Debug logging identifies structural misuse

**Don't stop at one validation point.** The bug isn't fixed until it's impossible.
