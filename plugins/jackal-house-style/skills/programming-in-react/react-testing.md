# React Testing

## Investigate First

**ALWAYS use codebase-investigator to find existing test patterns before writing tests.**

Check for:
- Which testing library is used (React Testing Library, Enzyme, Playwright, Cypress)
- Test file conventions (`*.test.tsx`, `*.spec.tsx`, `__tests__/`)
- How components are tested currently
- Integration vs unit test balance

## React Testing Library (Common Pattern)

**Philosophy: Test user behavior, not implementation**

**Query priority (from react.dev and Kent C. Dodds):**
1. `getByRole` - Accessibility-first, matches how users interact
2. `getByLabelText` - Form fields
3. `getByPlaceholderText` - Last resort for inputs
4. `getByText` - Non-interactive content
5. `getByTestId` - Only when semantic queries fail

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

test('user can submit form', async () => {
  const user = userEvent.setup();
  const handleSubmit = jest.fn();

  render(<LoginForm onSubmit={handleSubmit} />);

  // Query by role and accessible name
  const nameInput = screen.getByRole('textbox', { name: /username/i });
  const submitButton = screen.getByRole('button', { name: /submit/i });

  // Simulate user interaction
  await user.type(nameInput, 'john');
  await user.click(submitButton);

  // Assert on outcomes
  expect(handleSubmit).toHaveBeenCalledWith({ username: 'john' });
});
```

**Good patterns:**
- Use `screen.getByRole` for queries
- Use `userEvent` (not `fireEvent`) for realistic interactions
- Use `findBy` for async elements: `await screen.findByText('Success')`
- Test what users see, not component internals

**Anti-patterns:**
```typescript
// Bad: Testing implementation details
expect(wrapper.state('count')).toBe(1);

// Bad: Using test IDs when semantic query works
screen.getByTestId('submit-button');

// Better: Query by role
screen.getByRole('button', { name: /submit/i });

// Bad: fireEvent (doesn't simulate real events)
fireEvent.click(button);

// Better: userEvent
await userEvent.click(button);
```

## Integration Testing (Playwright/Cypress)

**Better for product applications** - tests entire user flows.

Check codebase for existing patterns with codebase-investigator.

**Playwright example:**
```typescript
test('user can login', async ({ page }) => {
  await page.goto('/login');
  await page.fill('input[name="email"]', 'user@example.com');
  await page.fill('input[name="password"]', 'password');
  await page.click('button[type="submit"]');

  await expect(page).toHaveURL('/dashboard');
  await expect(page.locator('h1')).toContainText('Welcome');
});
```

## Testing Custom Hooks

**Use @testing-library/react-hooks or test through components:**

```typescript
import { renderHook } from '@testing-library/react';
import { useCounter } from './useCounter';

test('increments counter', () => {
  const { result } = renderHook(() => useCounter());

  act(() => {
    result.current.increment();
  });

  expect(result.current.count).toBe(1);
});
```

## Testing Async Components

```typescript
test('displays data after loading', async () => {
  render(<UserList />);

  // Loading state
  expect(screen.getByText(/loading/i)).toBeInTheDocument();

  // Wait for data to appear
  const users = await screen.findAllByRole('listitem');
  expect(users).toHaveLength(3);
});
```

## Error Boundaries

**Test error boundaries with error-throwing components:**

```typescript
test('error boundary catches errors', () => {
  const ThrowError = () => {
    throw new Error('Test error');
  };

  render(
    <ErrorBoundary fallback={<div>Error caught</div>}>
      <ThrowError />
    </ErrorBoundary>
  );

  expect(screen.getByText('Error caught')).toBeInTheDocument();
});
```

## What to Test

**Test user-visible behavior:**
- Can user complete key workflows?
- Do error states display correctly?
- Does loading state appear?
- Are form validations working?

**Don't test:**
- React internals (state, props directly)
- Implementation details (function names, component structure)
- Third-party libraries (assume they work)

## Mocking

**Mock external dependencies, not React:**

```typescript
// Mock API calls
jest.mock('./api', () => ({
  fetchUsers: jest.fn(() => Promise.resolve([{ id: 1, name: 'John' }]))
}));

// Don't mock React hooks or components
```

## Resources

- [React Testing Library docs](https://testing-library.com/react)
- [Common mistakes with RTL](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
- [Playwright docs](https://playwright.dev)
