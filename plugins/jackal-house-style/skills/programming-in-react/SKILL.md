---
name: programming-in-react
description: Use when writing or modifying React components, planning React features, or working with .jsx/.tsx files - provides modern React patterns with TypeScript, hooks usage, component composition, and common pitfalls to avoid
user-invocable: false
---

# Programming in React

## Overview

Modern React development using functional components, hooks, and TypeScript. This skill guides you through React workflows from component creation to testing.

**Core principle:** Components are functions that return UI. State and effects are managed through hooks. Composition over inheritance always.

**REQUIRED SUB-SKILL:** Use jackal-house-style:howto-code-in-typescript for general TypeScript patterns. This skill covers React-specific TypeScript usage only.

## When to Use

- Creating or modifying React components
- Working with React hooks (useState, useEffect, custom hooks)
- Planning React features or UI work
- Debugging React-specific issues (hooks errors, render problems)
- When you see .jsx or .tsx files

## Workflow: Creating Components

**Functional components only.** Use `interface` for props, avoid `React.FC`:

```typescript
interface ButtonProps {
  label: string;
  onClick: () => void;
  disabled?: boolean;
}

export function Button({ label, onClick, disabled }: ButtonProps) {
  return <button onClick={onClick} disabled={disabled}>{label}</button>;
}
```

**Event typing:** `React.MouseEvent<HTMLButtonElement>`, `React.ChangeEvent<HTMLInputElement>`. Children: `React.ReactNode`.

## Workflow: Managing State

**useState for simple state:**

```typescript
const [count, setCount] = useState(0);

// Always use functional updates when new state depends on old
setCount(prev => prev + 1); // Good
setCount(count + 1); // Avoid - can be stale in closures
```

**useReducer for complex state:**
When state has multiple related pieces that update together, or next state depends on previous state in complex ways.

**State management decision framework:**
1. **Local component state?** � useState
2. **Multiple related state updates?** � useReducer
3. **Shared across components?** � Context API or custom hook
4. **Need external library?** � Use codebase-investigator to find existing patterns, or internet-researcher to evaluate options (Zustand, Redux Toolkit, TanStack Query)

## Workflow: Handling Side Effects

**useEffect for external systems only** (API calls, subscriptions, browser APIs). NOT for derived state.

**Critical rules:**
- Always include all dependencies (ESLint: react-hooks/exhaustive-deps)
- Always return cleanup function (prevents memory leaks)
- Think "which state does this sync with?" not "when does this run?"

**Common pattern:**
```typescript
useEffect(() => {
  const controller = new AbortController();
  fetch('/api/data', { signal: controller.signal })
    .then(res => res.json())
    .then(data => setData(data));
  return () => controller.abort(); // Cleanup
}, []);
```

For comprehensive useEffect guidance (dependencies, cleanup, when NOT to use, debugging), see [useEffect-deep-dive.md](./useEffect-deep-dive.md).

## Workflow: Component Composition

**Children prop:** Use `children: React.ReactNode` for wrapping components.

**Custom hooks:** Extract reusable stateful logic (prefer over duplicating logic in components).

**Compound components:** For complex APIs like `<Select><Select.Option /></Select>`.

**Render props:** When component controls rendering but parent provides template.

## Workflow: Testing

**ALWAYS use codebase-investigator first** to find existing test patterns. Common approaches: React Testing Library, Playwright, Cypress.

See [react-testing.md](./react-testing.md) for comprehensive guidance.

## Performance

Profile before optimizing. Use `useMemo`, `useCallback`, `React.memo` only when measurements show need. React 19 compiler handles most memoization automatically.

## Common Rationalizations - STOP

| Excuse | Reality |
|--------|---------|
| "useEffect is fine for derived state" | Calculate derived values directly. useEffect for derived state causes extra renders and bugs. |
| "React.FC is the standard way" | Community moved away from React.FC. Use explicit function declarations with typed props. |
| "Cleanup doesn't matter for short operations" | Memory leaks are real. Always cleanup subscriptions, timers, and abort fetch requests. |
| "Missing dependencies is fine, I know what I'm doing" | Stale closures cause bugs. Always include all dependencies. Fix the root cause, don't lie to the linter. |
| "useCallback with all dependencies is correct" | Including state in deps creates new function every render AND stale closures. Use functional setState updates instead. |
| "This is Functional Core because it's pure logic" | Hooks with state are Imperative Shell or Mixed. Only pure functions without hooks are Functional Core. |
| "Array index as key is fine for static lists" | If list ever reorders, filters, or updates, you'll get bugs. Use stable unique IDs. |
| "Mutating state is faster" | React won't detect the change. Always create new objects/arrays. |

## Quick Reference

| Task | Pattern |
|------|---------|
| Props | `interface Props {...}; function Comp({ prop }: Props)` |
| State update | `setState(prev => newValue)` when depends on current |
| Fetch on mount | `useEffect(() => { fetch(...); return cleanup }, [])` |
| Derived value | Calculate directly, NOT useEffect |
| List render | `{items.map(item => <Item key={item.id} />)}` |

## Red Flags - STOP and Refactor

- `React.FC` in new code
- `useEffect` with state as only dependency
- Missing cleanup in useEffect
- Array index as key: `key={index}`
- Direct state mutation: `state.value = x`
- Missing dependencies in useEffect (suppressing ESLint warning)
- `any` type for props or event handlers

When you see these, refactor before proceeding.
