# useEffect Deep Dive

## Mental Model (Dan Abramov)

**Effects synchronize with state, not with lifecycle.**

Don't think: "When does this run?" (componentDidMount mindset)
Think: "Which state does this effect sync with?"

## Dependency Array Rules

**Include ALL dependencies - no exceptions:**

```typescript
// Bad: Missing dependency causes stale closure
const [count, setCount] = useState(0);
useEffect(() => {
  const timer = setInterval(() => {
    console.log(count); // Always logs initial count!
  }, 1000);
  return () => clearInterval(timer);
}, []); // Missing 'count'

// Good: Include all dependencies
useEffect(() => {
  const timer = setInterval(() => {
    console.log(count);
  }, 1000);
  return () => clearInterval(timer);
}, [count]);
```

## When NOT to Use useEffect

**1. Derived values - calculate directly:**
```typescript
// Bad
const [items, setItems] = useState([]);
const [count, setCount] = useState(0);
useEffect(() => {
  setCount(items.length);
}, [items]);

// Good
const [items, setItems] = useState([]);
const count = items.length; // Just calculate it
```

**2. Event handlers - use callbacks:**
```typescript
// Bad
useEffect(() => {
  if (shouldSubmit) {
    submitForm();
  }
}, [shouldSubmit]);

// Good
function handleClick() {
  submitForm();
}
```

**3. Initializing app state - calculate during render:**
```typescript
// Bad
const [data, setData] = useState(null);
useEffect(() => {
  setData(expensiveOperation());
}, []);

// Good - lazy initialization
const [data, setData] = useState(() => expensiveOperation());
```

## Cleanup Functions

**Always cleanup subscriptions, timers, and async operations:**

```typescript
// Network request
useEffect(() => {
  const controller = new AbortController();

  fetch('/api/data', { signal: controller.signal })
    .then(res => res.json())
    .then(data => setData(data))
    .catch(err => {
      if (err.name !== 'AbortError') {
        setError(err);
      }
    });

  return () => controller.abort();
}, []);

// Event listener
useEffect(() => {
  function handleResize() {
    setWidth(window.innerWidth);
  }

  window.addEventListener('resize', handleResize);
  return () => window.removeEventListener('resize', handleResize);
}, []);

// Subscription
useEffect(() => {
  const subscription = dataSource.subscribe(data => setData(data));
  return () => subscription.unsubscribe();
}, [dataSource]);
```

## Function Dependencies

**Problem: Functions in dependencies cause re-runs:**

```typescript
// Bad: onSave changes every render, effect runs constantly
function MyComponent({ onSave }) {
  useEffect(() => {
    onSave();
  }, [onSave]);
}

// Solution 1: Wrap parent function in useCallback
function Parent() {
  const handleSave = useCallback(() => {
    saveToServer();
  }, []);

  return <MyComponent onSave={handleSave} />;
}

// Solution 2: Define function inside effect
useEffect(() => {
  function handleSave() {
    saveToServer();
  }
  handleSave();
}, []); // No dependencies needed
```

## Common Patterns

**Fetch data on mount:**
```typescript
useEffect(() => {
  let ignore = false;
  const controller = new AbortController();

  async function fetchData() {
    try {
      const res = await fetch(url, { signal: controller.signal });
      const data = await res.json();
      if (!ignore) setData(data);
    } catch (err) {
      if (!ignore && err.name !== 'AbortError') setError(err);
    }
  }

  fetchData();

  return () => {
    ignore = true;
    controller.abort();
  };
}, [url]);
```

**Debounce:**
```typescript
useEffect(() => {
  const timer = setTimeout(() => {
    searchAPI(searchTerm);
  }, 500);

  return () => clearTimeout(timer);
}, [searchTerm]);
```

**Sync with external store:**
```typescript
useEffect(() => {
  function handleChange() {
    setSnapshot(store.getSnapshot());
  }

  const unsubscribe = store.subscribe(handleChange);
  return unsubscribe;
}, [store]);
```

## Debugging useEffect

**Effect runs too often?**
- Check dependency array - might include objects/functions that change every render
- Use `useCallback` or `useMemo` to stabilize dependencies
- Consider if you actually need the effect (might be derived state)

**Effect has stale values?**
- Missing dependency in array
- Fix: add the dependency (don't suppress ESLint warning)
- Or use functional setState: `setState(prev => prev + 1)`

**Effect runs twice in development?**
- React Strict Mode intentionally runs effects twice to catch bugs
- This is expected and helpful - fix your cleanup function
- Production only runs once

## Resources

- [Dan Abramov's Complete Guide to useEffect](https://overreacted.io/a-complete-guide-to-useeffect/)
- [React docs: useEffect](https://react.dev/reference/react/useEffect)
