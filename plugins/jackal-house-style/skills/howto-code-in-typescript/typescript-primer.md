# TypeScript primer

A plain-English explanation of the concepts in `SKILL.md`. Assumes you know basic programming (variables, functions, loops, if/else), but not JavaScript or TypeScript specifically.

---

## `===` vs `==` (triple equals)

JavaScript has two equality operators, and they behave differently.

`==` does **type coercion** — it tries to convert values to the same type before comparing:

```typescript
0 == false    // true  (0 is coerced to false)
"" == false   // true  (empty string coerced to false)
null == undefined  // true
```

`===` checks both the value **and** the type. No coercion:

```typescript
0 === false   // false (different types)
"" === false  // false
null === undefined  // false
```

The coercions `==` applies are surprising and hard to memorize. **Always use `===`** so you know exactly what you're comparing.

---

## `const` and `let`

These replaced the old `var` keyword. You'll rarely see `var` in modern code.

**`const`** means the binding can't be reassigned:

```typescript
const name = "Alice";
name = "Bob";  // ERROR — can't reassign a const
```

Note: `const` doesn't mean the value is frozen. If the value is an object or array, you can still modify its contents — just not replace the whole variable.

**`let`** allows reassignment:

```typescript
let count = 0;
count = 1;  // fine
```

The house style says **use `const` by default**. Only reach for `let` when you actually need to reassign. This makes code easier to follow — when you see `const`, you know that binding never changes.

---

## Arrow functions `=>`

Arrow functions are a shorter way to write functions. They come up constantly in callbacks (functions you pass to other functions).

Classic function syntax:

```typescript
function double(x: number): number {
  return x * 2;
}
```

Arrow function syntax:

```typescript
const double = (x: number): number => {
  return x * 2;
};
```

If the body is a single expression, you can drop the curly braces and `return`:

```typescript
const double = (x: number): number => x * 2;
```

Arrow functions are used as **inline callbacks** — anonymous functions passed into things like `.map()`, `.filter()`, `.then()`:

```typescript
const numbers = [1, 2, 3];
const doubled = numbers.map(n => n * 2);  // [2, 4, 6]
```

**Why two function styles?** Arrow functions and regular `function` declarations handle the `this` keyword differently (more on `this` later). The house style uses regular `function` declarations for top-level named functions, and arrow syntax for inline callbacks.

---

## TypeScript types — what they are and why

TypeScript adds a type system on top of JavaScript. You annotate values with types, and the compiler catches mistakes before your code runs.

```typescript
function greet(name: string): string {
  return "Hello, " + name;
}

greet(42);  // ERROR at compile time — expected string, got number
```

Without TypeScript, `greet(42)` would silently produce `"Hello, 42"` or crash at runtime. With TypeScript, you catch it immediately.

The `: string` after `name` is the type annotation. The `: string` after the parentheses is the return type.

**Types as documentation:** When you read `function processUser(data: Readonly<UserData>): ProcessResult`, you immediately know what goes in and what comes out — no need to read the implementation.

---

## `type` vs `interface`

Both describe the shape of an object. The house style uses `type` for almost everything.

```typescript
type User = {
  id: string;
  name: string;
  email: string | null;
};
```

`interface` is used only for **class contracts** — defining what methods a class must implement:

```typescript
interface IUserRepository {
  findById(id: string): Promise<User | null>;
}

class UserRepository implements IUserRepository {
  // must implement findById
}
```

The practical difference: `type` composes better (you can union and intersect types, do mapped types, etc.). `interface` has a footgun called declaration merging, where two `interface` declarations with the same name silently merge, which can cause confusing bugs.

Short version: when you're describing data shape, use `type`. When you're writing a contract for a class, use `interface`.

---

## Union types `|`

The pipe character `|` means "this OR that":

```typescript
type Status = 'pending' | 'active' | 'complete' | 'failed';

type UserId = string | number;  // either type works

type MaybeUser = User | null;   // a user, or nothing
```

Union types replace the old `enum` construct for most cases. They're simpler (just string values) and don't generate any extra JavaScript code.

---

## Optional properties `?`

A `?` after a property name means it might not be there:

```typescript
type SendEmailOptions = {
  to: string;
  subject: string;
  body?: string;  // this one is optional
};
```

Inside the function, `body` will be either a `string` or `undefined` — TypeScript forces you to handle both cases.

Don't confuse this with `null`. In the house style:
- `?` (optional/undefined) = "this field might not exist at all"
- `| null` = "this field exists but has no value"

---

## `null` vs `undefined`

Both mean "no value" but they're used differently here.

`undefined` is what JavaScript uses when something hasn't been set yet — it's the default state of an uninitialized variable.

`null` is an **intentional** absence. If you look up a user and they don't exist, you return `null`. It's a deliberate "nothing here."

```typescript
function findUser(id: string): User | null {
  const user = database.get(id);
  return user ?? null;  // convert undefined to null
}
```

The `??` is the **nullish coalescing operator** — it returns the right side if the left side is `null` or `undefined`. So `user ?? null` means "return `user`, but if it's undefined, return `null` instead."

---

## `readonly` and immutability

`readonly` prevents a property from being modified after it's set:

```typescript
type User = {
  readonly id: string;  // can't be changed
  name: string;         // can be changed
};

const user: User = { id: "123", name: "Alice" };
user.id = "456";    // ERROR
user.name = "Bob";  // fine
```

`Readonly<T>` applies `readonly` to every property of a type:

```typescript
function processData(data: Readonly<UserData>): void {
  data.name = "x";  // ERROR — data is readonly
}
```

**Why this matters:** Mutating data that gets passed around is a common source of bugs — you change something in one place and it unexpectedly affects something else. Making parameters readonly means a function can read data but not modify it, which eliminates that whole class of bug.

`ReadonlyArray<T>` is the same idea for arrays — you can read items but not push, pop, or sort the array in place.

---

## `any` vs `unknown`

`any` turns off TypeScript's type checking for a value. It's an escape hatch that defeats the purpose of using TypeScript:

```typescript
const x: any = "hello";
x.notARealMethod();  // no error — TypeScript just trusts you
```

`unknown` means "I don't know what type this is yet, but I need to check before I use it." TypeScript forces you to narrow the type before doing anything with it:

```typescript
function process(value: unknown): string {
  if (typeof value === 'string') {
    return value.toUpperCase();  // OK — we checked it's a string
  }
  throw new Error('Expected a string');
}
```

Use `unknown` for truly unknown data (JSON from an API, values from external libraries). Never use `any` — it hides bugs.

---

## `async`/`await` and Promises

Some operations take time — fetching data from a server, reading a file. JavaScript handles these with **Promises**, which represent a value that will exist in the future.

A `Promise<User>` is "a user that will arrive eventually." You `await` it to get the actual value:

```typescript
async function getUser(id: string): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  return response.json();
}
```

The `async` keyword tells JavaScript this function contains async operations. The `await` keyword pauses execution until the Promise resolves. The function returns a `Promise<User>` — callers also need to `await` it.

```typescript
async function showUser(id: string): Promise<void> {
  const user = await getUser(id);  // wait for the fetch
  console.log(user.name);
}
```

**Why `async/await` over `.then()` chains:** `.then()` was the original way to chain Promises, but async/await reads more like normal synchronous code — top to bottom, left to right. Same result, much easier to follow.

---

## Generics `<T>`

Generics let you write a function or type that works with different types, while still being type-safe.

Imagine a function that returns the first item of any array:

```typescript
function first<T>(items: ReadonlyArray<T>): T | null {
  return items[0] ?? null;
}

const name = first(['Alice', 'Bob']);   // TypeScript knows this is string | null
const num = first([1, 2, 3]);           // TypeScript knows this is number | null
```

The `<T>` is a type parameter — a placeholder that gets filled in based on what you pass. You can think of it like a regular parameter, but for types.

Descriptive names are preferred when the meaning is clear:

```typescript
function mapItems<TItem, TResult>(
  items: ReadonlyArray<TItem>,
  mapper: (item: TItem) => TResult,
): Array<TResult> {
  return items.map(mapper);
}
```

---

## Destructuring

Destructuring pulls values out of objects or arrays into named variables:

```typescript
// Without destructuring:
const name = user.name;
const email = user.email;

// With destructuring:
const { name, email } = user;
```

For arrays:

```typescript
const [first, second] = [1, 2, 3];
```

You can also set defaults for values that might be missing:

```typescript
function processUser(options: ProcessUserOptions): void {
  const { name, email, sendWelcome = true } = options;
  // sendWelcome defaults to true if not provided
}
```

The house style says: destructure inside the function body, not in the parameter list. This is cleaner and avoids repeating the type inline.

---

## `Array<T>` vs `T[]`

Both mean the same thing — an array of items of type T. The house style requires `Array<T>`:

```typescript
// Use this:
const names: Array<string> = ['Alice', 'Bob'];

// Not this:
const names: string[] = ['Alice', 'Bob'];
```

**Why:** Consistency. TypeScript's other generic types all use angle brackets — `ReadonlyArray<T>`, `Promise<T>`, `Record<K, V>`. Using `Array<T>` keeps the pattern consistent.

---

## Named exports vs default exports

Every file can export values for other files to use. There are two styles:

```typescript
// Default export — only one per file:
export default function processUser() { ... }

// Named export — as many as you want:
export function processUser() { ... }
export type User = { ... }
```

When you import a default export, you can name it anything:

```typescript
import processUser from './user-service';    // could call it anything
import myFunc from './user-service';         // same thing, different name
```

When you import named exports, the name must match:

```typescript
import { processUser, User } from './user-service';
```

The house style requires **named exports only**. Default exports make it easy to accidentally rename things inconsistently across a codebase, and they're harder to find when grepping.

---

## The `this` keyword

`this` refers to the object a method is called on. It's a notorious source of confusion in JavaScript.

```typescript
class Counter {
  private count = 0;

  increment(): void {
    this.count++;  // 'this' is the Counter instance
  }
}
```

The problem: `this` changes depending on how a function is called. If you pass a method as a callback, `this` can become something unexpected.

Arrow functions don't have their own `this` — they inherit it from the surrounding scope, which makes them safer for callbacks. That's one reason they're preferred for inline functions.

The house style says: use `this` only inside class methods. Avoid it in object literals and standalone functions.

---

## Template literals

Backtick strings (`` ` ``) let you embed expressions directly:

```typescript
const name = "Alice";
const greeting = `Hello, ${name}!`;  // "Hello, Alice!"

const url = `/api/users/${userId}/profile`;
```

Anything inside `${}` is evaluated as an expression. Much cleaner than string concatenation with `+`.

---

## Type guards and narrowing

TypeScript tracks what you know about a type as code executes. When you check a type, TypeScript "narrows" it:

```typescript
function process(value: string | number): string {
  if (typeof value === 'string') {
    // TypeScript knows value is string here
    return value.toUpperCase();
  }
  // TypeScript knows value is number here
  return value.toString();
}
```

For your own types, you write a **type guard** function:

```typescript
function isUser(value: unknown): value is User {
  return (
    typeof value === 'object' &&
    value !== null &&
    'name' in value &&
    'email' in value
  );
}
```

The `value is User` return type tells TypeScript: if this function returns `true`, treat `value` as a `User` from that point on.

---

## Discriminated unions

A discriminated union is a union type where each variant has a shared field (the "discriminant") with a unique value. TypeScript uses that field to figure out which variant you're dealing with:

```typescript
type Result =
  | { type: 'success'; data: string }
  | { type: 'error'; message: string };

function handle(result: Result): void {
  if (result.type === 'success') {
    console.log(result.data);     // TypeScript knows .data exists
  } else {
    console.error(result.message); // TypeScript knows .message exists
  }
}
```

This is safer than trying to access `.data` and `.message` without checking — TypeScript won't let you access a field that might not exist.

---

## Floating-point math and money

This one is a quirk of how computers store numbers. JavaScript (and most languages) represent decimal numbers in binary, which can't perfectly represent values like 0.1:

```typescript
0.1 + 0.2  // 0.30000000000000004, not 0.3
```

For most things this doesn't matter. But for money, it does — tiny errors compound into real discrepancies.

That's why the house style uses `math.js` for any financial calculation. It provides arbitrary-precision arithmetic that doesn't have this problem.

---

## `Promise.all` — parallel async work

When you need to do multiple async things and don't need to wait for one before starting the next, `Promise.all` runs them in parallel:

```typescript
// Sequential — slow (waits for each):
const user = await fetchUser(id);
const orders = await fetchOrders(id);

// Parallel — fast (both requests in flight at once):
const [user, orders] = await Promise.all([
  fetchUser(id),
  fetchOrders(id),
]);
```

Use parallel when the operations are independent of each other.
