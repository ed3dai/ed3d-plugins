---
name: writing-good-tests
description: Use when writing or reviewing tests - covers test philosophy, condition-based waiting, mocking strategy, and test isolation
user-invocable: false
---

# Writing Good Tests

## Philosophy

**"Write tests. Not too many. Mostly integration."** — Kent C. Dodds

Tests verify real behavior, not implementation details. The goal is confidence that your code works, not coverage numbers.

**Core principles:**
1. Test behavior, not implementation — refactoring shouldn't break tests
2. Integration tests provide better confidence-to-cost ratio than unit tests
3. Wait for actual conditions, not arbitrary timeouts
4. Mock strategically — real dependencies when feasible, mocks for external systems
5. Don't pollute production code with test-only methods

## Test Structure

Use **Arrange-Act-Assert** (or Given-When-Then):

```typescript
test('user can cancel reservation', async () => {
  // Arrange
  const reservation = await createReservation({ userId: 'user-1', roomId: 'room-1' });

  // Act
  const result = await cancelReservation(reservation.id);

  // Assert
  expect(result.status).toBe('cancelled');
  expect(await getReservation(reservation.id)).toBeNull();
});
```

**One action per test.** Multiple assertions are fine if they verify the same behavior.

## Condition-Based Waiting

Flaky tests often guess at timing. This creates race conditions where tests pass locally but fail in CI.

**Wait for conditions, not time:**

```typescript
// BAD: Guessing at timing
await new Promise(r => setTimeout(r, 50));
const result = getResult();

// GOOD: Waiting for condition
await waitFor(() => getResult() !== undefined);
const result = getResult();
```

### Generic Polling Function

```typescript
async function waitFor<T>(
  condition: () => T | undefined | null | false,
  description: string,
  timeoutMs = 5000
): Promise<T> {
  const startTime = Date.now();

  while (true) {
    const result = condition();
    if (result) return result;

    if (Date.now() - startTime > timeoutMs) {
      throw new Error(`Timeout waiting for ${description} after ${timeoutMs}ms`);
    }

    await new Promise(r => setTimeout(r, 10)); // Poll every 10ms
  }
}
```

### Quick Patterns

| Scenario | Pattern |
|----------|---------|
| Wait for event | `waitFor(() => events.find(e => e.type === 'DONE'))` |
| Wait for state | `waitFor(() => machine.state === 'ready')` |
| Wait for count | `waitFor(() => items.length >= 5)` |

### When Arbitrary Timeout IS Correct

Only when testing actual timing behavior (debounce, throttle, intervals):

```typescript
// Testing tool that ticks every 100ms
await waitForEvent(manager, 'TOOL_STARTED'); // First: wait for condition
await new Promise(r => setTimeout(r, 200));   // Then: wait for 2 ticks
// Comment explains WHY: 200ms = 2 ticks at 100ms intervals
```

## Mocking Strategy

> "You don't hate mocks; you hate side-effects." — J.B. Rainsberger

Mocks reveal where side-effects complicate your code. Use them strategically, not reflexively.

### Don't Mock What You Don't Own

Create thin wrappers around third-party libraries. Mock YOUR wrapper, not the library.

```typescript
// BAD: Mock the HTTP client directly
const mockClient = vi.mocked(httpx.Client);

// GOOD: Create your own wrapper
class RegistryClient {
  constructor(private client: HttpClient) {}
  async getRepos() {
    return this.client.get('https://registry.example.com/v2/_catalog');
  }
}

// Mock your wrapper
vi.mock('./registry-client');
```

This simplifies tests AND improves your design.

### Managed vs Unmanaged Dependencies

| Dependency Type | Example | Strategy |
|-----------------|---------|----------|
| **Managed** (you control it) | Your database, your file system | Use REAL instances |
| **Unmanaged** (external) | Third-party APIs, SMTP, message bus | Use MOCKS |

Communications with managed dependencies are implementation details — you can refactor them freely. Communications with unmanaged dependencies are observable behavior — mocking protects against external changes.

### Anti-Pattern: Testing Mock Behavior

```typescript
// BAD: Testing that the mock exists
test('renders sidebar', () => {
  render(<Page />);
  expect(screen.getByTestId('sidebar-mock')).toBeInTheDocument();
});

// GOOD: Test real behavior
test('renders sidebar', () => {
  render(<Page />);
  expect(screen.getByRole('navigation')).toBeInTheDocument();
});
```

**Gate:** Before asserting on any mock element, ask: "Am I testing real behavior or mock existence?"

### Anti-Pattern: Mocking Without Understanding

```typescript
// BAD: Mock breaks test logic
test('detects duplicate server', () => {
  // Mock prevents config write that test depends on!
  vi.mock('ToolCatalog', () => ({
    discoverAndCacheTools: vi.fn().mockResolvedValue(undefined)
  }));
  await addServer(config);
  await addServer(config);  // Should throw - but won't!
});

// GOOD: Mock at correct level
test('detects duplicate server', () => {
  vi.mock('MCPServerManager'); // Just mock slow server startup
  await addServer(config);  // Config written
  await addServer(config);  // Duplicate detected
});
```

**Gate:** Before mocking, ask: "What side effects does this have? Does my test depend on them?"

### Anti-Pattern: Incomplete Mocks

Mock the COMPLETE data structure as it exists in reality:

```typescript
// BAD: Partial mock
const mockResponse = {
  status: 'success',
  data: { userId: '123' }
  // Missing: metadata that downstream code uses
};

// GOOD: Mirror real API
const mockResponse = {
  status: 'success',
  data: { userId: '123', name: 'Alice' },
  metadata: { requestId: 'req-789', timestamp: 1234567890 }
};
```

### When Mocks Become Too Complex

Warning signs:
- Mock setup longer than test logic
- Mocking everything to make test pass
- Test breaks when mock changes

> "As the number of mocks grows, the probability of testing the mock instead of the desired code goes up." — Codurance

Consider integration tests with real components — often simpler than elaborate mocks.

### Anti-Pattern: Test-Only Methods in Production

```typescript
// BAD: destroy() only used in tests
class Session {
  async destroy() { /* cleanup */ }
}

// GOOD: Test utilities handle cleanup
// test-utils/session-helpers.ts
export async function cleanupSession(session: Session) {
  const workspace = session.getWorkspaceInfo();
  if (workspace) {
    await workspaceManager.destroyWorkspace(workspace.id);
  }
}
```

**Gate:** Before adding any method to production class, ask: "Is this only used by tests?" If yes, put it in test utilities.

## Test Isolation

Tests should not depend on execution order. But isolation doesn't mean cleaning up everything.

### What to Clean Up

**Long-lived resources MUST be cleaned up:**
- Virtual machines, containers
- Kubernetes jobs, pods, deployments
- Cloud resources (instances, buckets)
- Background processes, daemons

**Prefer product tools for cleanup** when possible:
```typescript
afterAll(async () => {
  // Use the product's own cleanup mechanisms
  await deployment.delete();
  await job.terminate();
});
```

**Side-channel cleanup** when product tools aren't available:
```typescript
afterAll(async () => {
  // Direct cleanup when product doesn't provide it
  await exec('kubectl delete job test-job-123');
});
```

### What's OK to Leave

**Database artifacts are fine to leave around.** Trying to clean up test data perfectly is a fool's errand and makes multi-step integration tests nearly impossible.

- Test records in databases
- Log entries
- Cached data that expires

The database should handle its own lifecycle. Tests that require pristine state should create unique identifiers, not depend on cleanup.

### Preventing Order Dependencies

```typescript
// Use unique identifiers instead of depending on clean state
const testId = `test-${Date.now()}-${Math.random()}`;
const user = await createUser({ email: `${testId}@test.com` });
```

## Quick Reference

| Problem | Fix |
|---------|-----|
| Arbitrary setTimeout in tests | Use condition-based waiting |
| Assert on mock elements | Test real component or unmock |
| Mock third-party directly | Create wrapper, mock wrapper |
| Test-only methods in production | Move to test utilities |
| Mock without understanding | Understand dependencies first |
| Incomplete mocks | Mirror real API completely |
| Over-complex mocks | Consider integration tests |
| Long-lived resources left running | Clean up VMs, k8s jobs, cloud resources |

## Red Flags

**Stop and reconsider when you see:**
- Arbitrary `setTimeout`/`sleep` without justification
- Assertions on mock elements or test IDs
- Methods only called in test files
- Mock setup is >50% of test code
- "Mocking just to be safe"
- Test depends on another test running first
- Long-lived resources not cleaned up

## TDD Connection

TDD prevents most testing anti-patterns:
- Write test first → forces thinking about what you're testing
- Watch it fail → confirms test tests real behavior, not mocks
- Minimal implementation → no test-only methods creep in
- Real dependencies first → you see what test needs before mocking

## Property-Based Testing

For certain patterns, property-based testing provides stronger coverage than example-based tests. See `property-based-testing` skill for complete reference.

### When to Use PBT

| Pattern | Example | Why PBT |
|---------|---------|---------|
| Serialization pairs | `encode`/`decode`, `toJSON`/`fromJSON` | Roundtrip property catches edge cases |
| Normalizers | `sanitize`, `canonicalize`, `format` | Idempotence property ensures stability |
| Validators | `is_valid`, `validate` | Valid-after-normalize property |
| Pure functions | Business logic, calculations | Multiple properties verify contract |
| Sorting/ordering | `sort`, `rank`, `compare` | Ordering + idempotence properties |

### When NOT to Use PBT

- Simple CRUD without transformation
- UI/presentation logic
- Integration tests requiring external setup
- When specific examples suffice and edge cases are well-understood
- Prototyping with fluid requirements

### PBT Quality Gates

Before committing property-based tests:

- [ ] **Not tautological:** Assertion doesn't compare same expression (`sorted(xs) == sorted(xs)` tests nothing)
- [ ] **Strong property:** Not just "no crash" - aim for roundtrip, idempotence, or invariants
- [ ] **Not vacuous:** `assume()` calls don't filter out most inputs
- [ ] **Edge cases explicit:** Include `@example([])`, `@example([1])` decorators
- [ ] **No reimplementation:** Don't restate function logic in assertion (`assert add(a,b) == a+b`)
- [ ] **Realistic constraints:** Strategy matches real-world input constraints
