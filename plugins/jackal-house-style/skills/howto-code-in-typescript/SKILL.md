---
name: howto-code-in-typescript
description: Use when writing TypeScript code, reviewing TS implementations, or making decisions about type declarations, function styles, or naming conventions - comprehensive house style covering type vs interface rules, function declarations, FCIS integration, immutability patterns, and type safety enforcement
user-invocable: false
---

# TypeScript House Style

## Overview

Comprehensive TypeScript coding standards emphasizing type safety, immutability, and integration with Functional Core, Imperative Shell (FCIS) pattern.

**Core principles:**
- Types as documentation and constraints
- Immutability by default prevents bugs
- Explicit over implicit (especially in function signatures)
- Functional Core returns Results, Imperative Shell may throw
- Configuration over decoration/magic

## Quick Self-Check (Use Under Pressure)

When under deadline pressure or focused on other concerns (performance, accuracy, features), STOP and verify:

- [ ] Using `Array<T>` not `T[]`
- [ ] Using `type` not `interface` (unless class contract)
- [ ] Using math.js for money/currencies/complex math
- [ ] Parameters are `readonly` or `Readonly<T>`
- [ ] Using `unknown` not `any`
- [ ] Using `null` for absent values (not `undefined`)
- [ ] Using function declarations (not const arrow) for top-level functions
- [ ] Using named exports (not default exports)
- [ ] Using `===` not `==`
- [ ] Using `.sort((a, b) => a - b)` for numeric arrays
- [ ] Using `parseInt(x, 10)` with explicit radix

**Why this matters:** Under pressure, you'll default to muscle memory. These checks catch the most common violations.

## Type Declarations

### Type vs Interface

**Always use `type` except for class contracts.**

```typescript
// GOOD: type for object shapes
type UserData = {
  readonly id: string;
  name: string;
  email: string | null;
};

// GOOD: interface for class contract
interface IUserRepository {
  findById(id: string): Promise<User | null>;
}

class UserRepository implements IUserRepository {
  // implementation
}

// BAD: interface for object shape
interface UserData {
  id: string;
  name: string;
}
```

**Rationale:** Types compose better with unions and intersections, support mapped types, and avoid declaration merging surprises. Interfaces are only for defining what a class must implement.

**IMPORTANT:** Even when under deadline pressure, even when focused on other concerns (financial accuracy, performance optimization, bug fixes), take 2 seconds to ask: "Is this a class contract?" If no, use `type`. Don't default to `interface` out of habit.

### Naming Conventions

#### Type Suffixes

| Suffix | Usage | Example |
|--------|-------|---------|
| `FooOptions` | Function parameter objects (3+ args or any optional) | `ProcessUserOptions` |
| `FooConfig` | Persistent configuration from storage | `DatabaseConfig` |
| `FooResult` | Discriminated union return types | `ValidationResult` |
| `FooFn` | Function/callback types | `TransformFn<T>` |
| `FooProps` | React component props | `ButtonProps` |
| `FooState` | State objects (component/application) | `AppState` |

#### General Casing

| Element | Convention | Example |
|---------|-----------|---------|
| Variables & functions | camelCase | `userName`, `getUser()` |
| Types & classes | PascalCase | `UserData`, `UserService` |
| Constants | UPPER_CASE | `MAX_RETRY_COUNT`, `API_ENDPOINT` |
| Files | kebab-case | `user-service.ts`, `process-order.ts` |

#### Boolean Naming

**Use is/has/can/should/will prefixes. Avoid negative names.**

```typescript
// GOOD
const isActive = true;
const hasPermission = checkPermission();
const canEdit = user.role === 'admin';
const shouldRetry = attempts < MAX_RETRIES;
const willTimeout = elapsed > threshold;

// Also acceptable: adjectives for state
type User = {
  active: boolean;
  visible: boolean;
  disabled: boolean;
};

// BAD: negative names
const isDisabled = false; // prefer isEnabled
const notReady = true;    // prefer isReady
```

### Type Suffix Details

#### FooOptions - Parameter Objects

**Use for functions with 3+ arguments OR any optional arguments.**

```typescript
type ProcessUserOptions = {
  readonly name: string;
  readonly email: string;
  readonly age: number;
  readonly sendWelcome?: boolean;
};

// GOOD: destructure in body, not in parameters
function processUser(options: ProcessUserOptions): void {
  const {name, email, age, sendWelcome = true} = options;
  // implementation
}

// BAD: inline destructuring in parameters
function processUser({name, email, age}: {name: string, email: string, age: number}) {
  // causes duplication when destructuring
}

// BAD: not using options pattern for 3+ args
function processUser(name: string, email: string, age: number, sendWelcome?: boolean) {
  // hard to call, positional arguments
}
```

#### FooResult - Discriminated Unions

**Always use discriminated unions for Result types. Integrate with neverthrow.**

```typescript
// GOOD: discriminated union with success/error
type ValidationResult =
  | { success: true; data: ValidUser }
  | { success: false; error: ValidationError };

// GOOD: use neverthrow for Result types
import {Result, ok, err} from 'neverthrow';

type ValidationError = {
  field: string;
  message: string;
};

function validateUser(data: Readonly<UserData>): Result<ValidUser, ValidationError> {
  if (!data.email) {
    return err({field: 'email', message: 'Email is required'});
  }
  return ok({...data, validated: true});
}

// Usage
const result = validateUser(userData);
if (result.isOk()) {
  console.log(result.value); // ValidUser
} else {
  console.error(result.error); // ValidationError
}
```

**Rule:** Functional Core functions should return `Result<T, E>` types. Imperative Shell functions may throw exceptions for HTTP errors and similar.

## Functions

### Declaration Style

**Use `function` declarations for top-level functions. Use arrow functions for inline callbacks.**

```typescript
// GOOD: function declaration for top-level
function processUser(data: Readonly<UserData>): ProcessResult {
  return {success: true, user: data};
}

// GOOD: arrow functions for inline callbacks
const users = rawData.map(u => transformUser(u));
button.addEventListener('click', (e) => handleClick(e));
fetch(url).then(data => processData(data));

// BAD: const arrow for top-level function
const processUser = (data: UserData): ProcessResult => {
  return {success: true, user: data};
};
```

**Rationale:** Function declarations are hoisted and more visible. Arrow functions capture lexical `this` and are concise for callbacks.

### Const Arrow Functions

**Use `const foo = () => {}` declarations only for stable references.**

```typescript
// GOOD: stable reference for React hooks
const handleSubmit = (event: FormEvent) => {
  event.preventDefault();
  // implementation
};

useEffect(() => {
  // handleSubmit reference is stable
}, [handleSubmit]);

// GOOD: long event listener passed from variable
const handleComplexClick = (event: MouseEvent) => {
  // many lines of logic
};
element.addEventListener('click', handleComplexClick);

// BAD: const arrow for regular top-level function
const calculateTotal = (items: Array<Item>): number => {
  return items.reduce((sum, item) => sum + item.price, 0);
};

// GOOD: use function declaration
function calculateTotal(items: ReadonlyArray<Item>): number {
  return items.reduce((sum, item) => sum + item.price, 0);
}
```

### Parameter Objects

**Use parameter objects for 3+ arguments OR any optional arguments.**

```typescript
// GOOD: options object for 3+ args
type CreateUserOptions = {
  readonly name: string;
  readonly email: string;
  readonly age: number;
  readonly newsletter?: boolean;
};

function createUser(options: CreateUserOptions): User {
  const {name, email, age, newsletter = false} = options;
  // implementation
}

// GOOD: 2 args, but one is optional - use options
type SendEmailOptions = {
  readonly to: string;
  readonly subject: string;
  readonly body?: string;
};

function sendEmail(options: SendEmailOptions): void {
  // implementation
}

// GOOD: 2 required args - no options needed
function divide(numerator: number, denominator: number): number {
  return numerator / denominator;
}
```

### Async Functions

**Always explicitly type Promise returns. Avoid async void.**

```typescript
// GOOD: explicit Promise return type
async function fetchUser(id: string): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  return response.json();
}

// GOOD: Promise<void> for side effects
async function saveUser(user: User): Promise<void> {
  await fetch('/api/users', {
    method: 'POST',
    body: JSON.stringify(user),
  });
}

// BAD: implicit return type
async function fetchUser(id: string) {
  const response = await fetch(`/api/users/${id}`);
  return response.json();
}
```

**Prefer async/await over `.then()` chains.**

```typescript
// GOOD: async/await
async function processUserData(id: string): Promise<ProcessedUser> {
  const user = await fetchUser(id);
  const enriched = await enrichUserData(user);
  return transformUser(enriched);
}

// BAD: promise chains
function processUserData(id: string): Promise<ProcessedUser> {
  return fetchUser(id)
    .then(user => enrichUserData(user))
    .then(enriched => transformUser(enriched));
}
```

### When to Use Async

**Be selective with async.** Not everything needs to be async. Sync code is simpler to reason about and debug.

**Use async for:**
- Network requests, database operations, file I/O
- Operations that benefit from concurrent execution (Promise.all)
- External service calls

**Stay sync for:**
- Pure calculations and transformations
- Simple data structure operations
- Code that doesn't touch external systems

```typescript
// GOOD: sync for pure transformation
function transformUser(user: User): TransformedUser {
  return {
    fullName: `${user.firstName} ${user.lastName}`,
    email: user.email.toLowerCase(),
  };
}

// GOOD: async for I/O
async function loadAndTransformUser(id: string): Promise<TransformedUser> {
  const user = await fetchUser(id);
  return transformUser(user); // Sync call inside async function is fine
}

// BAD: unnecessary async
async function transformUser(user: User): Promise<TransformedUser> {
  return {
    fullName: `${user.firstName} ${user.lastName}`,
    email: user.email.toLowerCase(),
  };
}
```

**Why this matters:** Async adds complexity—error propagation, cleanup, and stack traces become harder to follow. Keep the async boundary as close to the I/O as possible.

## Classes

### When to Use Classes

**Prefer functions over classes, EXCEPT for dependency injection patterns.**

```typescript
// GOOD: class as dependency container
class UserService {
  constructor(
    private readonly db: Database,
    private readonly logger: Logger,
    private readonly cache: Cache,
  ) {}

  async getUser(id: string): Promise<User | null> {
    this.logger.info(`Fetching user ${id}`);
    const cached = await this.cache.get(`user:${id}`);
    if (cached) return cached;

    const user = await this.db.users.findById(id);
    if (user) await this.cache.set(`user:${id}`, user);
    return user;
  }
}

// BAD: class with no dependencies
class MathUtils {
  add(a: number, b: number): number {
    return a + b;
  }
}

// GOOD: plain functions
function add(a: number, b: number): number {
  return a + b;
}
```

### Class Structure

**Use constructor injection into private readonly fields.**

```typescript
// GOOD: constructor injection, private readonly
class OrderProcessor {
  constructor(
    private readonly orderRepo: OrderRepository,
    private readonly paymentService: PaymentService,
    private readonly notifier: NotificationService,
  ) {}

  async processOrder(orderId: string): Promise<void> {
    const order = await this.orderRepo.findById(orderId);
    // implementation
  }
}

// BAD: public mutable fields
class OrderProcessor {
  public orderRepo: OrderRepository;
  public paymentService: PaymentService;

  constructor(orderRepo: OrderRepository, paymentService: PaymentService) {
    this.orderRepo = orderRepo;
    this.paymentService = paymentService;
  }
}
```

### The 'this' Keyword

**Use `this` only in class methods. Avoid elsewhere.**

```typescript
// GOOD: this in class method
class Counter {
  private count = 0;

  increment(): void {
    this.count++;
  }
}

// BAD: this in object literal
const counter = {
  count: 0,
  increment() {
    this.count++; // fragile, breaks when passed as callback
  },
};

// GOOD: closure over variable
function createCounter() {
  let count = 0;
  return {
    increment: () => count++,
    getCount: () => count,
  };
}
```

## Type Inference

### When Inference is Acceptable

**Always explicit in function signatures. Infer in local variables, loops, destructuring, and intermediate calculations.**

```typescript
// GOOD: explicit function signature, inferred locals
function processUsers(users: ReadonlyArray<User>): Array<ProcessedUser> {
  const results: Array<ProcessedUser> = [];

  for (const user of users) { // user inferred as User
    const name = user.name; // name inferred as string
    const upper = name.toUpperCase(); // upper inferred as string
    const processed = {id: user.id, name: upper}; // processed inferred
    results.push(processed);
  }

  return results;
}

// GOOD: destructuring with inference
function formatUser({name, email}: User): string {
  return `${name} <${email}>`;
}

// BAD: missing return type
function processUsers(users: ReadonlyArray<User>) {
  // ...
}

// BAD: excessive annotations on locals
function processUsers(users: ReadonlyArray<User>): Array<ProcessedUser> {
  const results: Array<ProcessedUser> = [];

  for (const user: User of users) {
    const name: string = user.name;
    const upper: string = name.toUpperCase();
    // ...
  }

  return results;
}
```

## Immutability

### Readonly by Default

**Mark reference type parameters as `Readonly<T>`. Use `const` for all bindings unless mutation needed.**

```typescript
// GOOD: readonly parameters
function processData(
  data: Readonly<UserData>,
  config: Readonly<ProcessConfig>,
): ProcessResult {
  // data and config cannot be mutated
  return {success: true};
}

// GOOD: const bindings
function calculateTotal(items: ReadonlyArray<Item>): number {
  const taxRate = 0.08;
  const subtotal = items.reduce((sum, item) => sum + item.price, 0);
  const tax = subtotal * taxRate;
  return subtotal + tax;
}

// BAD: mutable parameters
function processData(data: UserData, config: ProcessConfig): ProcessResult {
  data.processed = true; // mutation
  return {success: true};
}
```

### Arrays

**ALWAYS use `Array<T>` or `ReadonlyArray<T>`. NEVER use `T[]` syntax.**

```typescript
// GOOD: Array<T> syntax
const numbers: Array<number> = [1, 2, 3];
const roles: Array<UserRole> = ['admin', 'editor'];
function calculateAverage(numbers: ReadonlyArray<number>): number {
  return numbers.reduce((a, b) => a + b, 0) / numbers.length;
}

// BAD: T[] syntax (don't use this even if common in examples)
const numbers: number[] = [1, 2, 3];  // NO
const roles: UserRole[] = ['admin'];   // NO
function calculateAverage(numbers: number[]): number { // NO
  // ...
}
```

**Why:** Consistency with other generic syntax. `Array<T>` is explicit and matches `ReadonlyArray<T>`, `Record<K, V>`, `Promise<T>`, etc. The `T[]` syntax is muscle memory from other languages but inconsistent with TypeScript's generic patterns.

**Prefer readonly outside local scope:**

```typescript
// GOOD: readonly array for function parameter
function calculateAverage(numbers: ReadonlyArray<number>): number {
  return numbers.reduce((a, b) => a + b, 0) / numbers.length;
}

// GOOD: mutable array in local scope
function processItems(items: ReadonlyArray<Item>): Array<ProcessedItem> {
  const results: Array<ProcessedItem> = [];
  for (const item of items) {
    results.push(transformItem(item));
  }
  return results;
}
```

### Deep Immutability

**Use `Readonly<T>` for shallow immutability, `ReadonlyDeep<T>` from type-fest when you need immutability all the way down.**

```typescript
import type {ReadonlyDeep} from 'type-fest';

// GOOD: shallow readonly for flat objects
type UserData = Readonly<{
  id: string;
  name: string;
  email: string;
}>;

// GOOD: deep readonly for nested structures
type AppConfig = ReadonlyDeep<{
  database: {
    host: string;
    port: number;
    credentials: {
      username: string;
      password: string;
    };
  };
  features: {
    enabled: Array<string>;
  };
}>;

function loadConfig(config: AppConfig): void {
  // config is deeply immutable
  // config.database.credentials.username = 'x'; // ERROR
}
```

## Mathematics and Currency

### When to Use math.js

**ALWAYS use math.js for:**
- Currency calculations (money)
- Financial calculations (interest, ROI, profit margins)
- Precision-critical percentages
- Complex mathematical operations requiring high precision

**NEVER use JavaScript `number` for:**
- Money / currency amounts
- Financial reporting calculations
- Any calculation where precision errors are unacceptable

```typescript
import { create, all, MathJsInstance } from 'mathjs';

const math: MathJsInstance = create(all);

// GOOD: math.js for currency calculations
function calculateTotal(
  price: number,
  quantity: number,
  taxRate: number
): string {
  const subtotal = math.multiply(
    math.bignumber(price),
    math.bignumber(quantity)
  );
  const tax = math.multiply(subtotal, math.bignumber(taxRate));
  const total = math.add(subtotal, tax);

  return math.format(total, { precision: 14 });
}

// GOOD: math.js for financial calculations
function calculateROI(
  initialInvestment: number,
  finalValue: number
): string {
  const initial = math.bignumber(initialInvestment);
  const final = math.bignumber(finalValue);
  const difference = math.subtract(final, initial);
  const ratio = math.divide(difference, initial);
  const percentage = math.multiply(ratio, 100);

  return math.format(percentage, { precision: 14 });
}

// BAD: JavaScript number for currency
function calculateTotal(price: number, quantity: number, taxRate: number): number {
  const subtotal = price * quantity;          // NO: precision errors
  const tax = subtotal * taxRate;             // NO: compounding errors
  return subtotal + tax;                      // NO: wrong for money
}

// BAD: JavaScript number for percentages in finance
function calculateDiscount(price: number, discountPercent: number): number {
  return price * (discountPercent / 100);     // NO: precision errors
}
```

**Why math.js:**
- JavaScript's native `number` uses IEEE 754 double-precision floating-point
- This causes precision errors: `0.1 + 0.2 !== 0.3`
- For financial calculations, these errors are unacceptable
- math.js BigNumber provides arbitrary precision arithmetic

**When JavaScript number is OK:**
- Counters and indices
- Simple integer math (within safe integer range)
- Display coordinates, dimensions
- Non-critical calculations where precision doesn't matter

## Nullability

### Null vs Undefined

**Use `null` for absent values. `undefined` means uninitialized. Proactively coalesce to null.**

```typescript
// GOOD: null for absent, undefined for uninitialized
type User = {
  name: string;
  email: string;
  phone: string | null; // may be absent
};

function findUser(id: string): User | null {
  const user = database.users.get(id);
  return user ?? null; // coalesce undefined to null
}

// GOOD: optional properties use ?:
type UserOptions = {
  name: string;
  email: string;
  newsletter?: boolean; // may be undefined
};

// BAD: undefined for absent values
function findUser(id: string): User | undefined {
  // prefer null for explicit absence
}

// GOOD: coalescing array access
const arr: Array<number> = [1, 2, 3];
const value: number | null = arr[10] ?? null;
```

## Enums and Unions

### Prefer String Literal Unions

**Avoid enums. Use string literal unions instead.**

```typescript
// GOOD: string literal union
type Status = 'pending' | 'active' | 'complete' | 'failed';

function processStatus(status: Status): void {
  switch (status) {
    case 'pending':
      // handle pending
      break;
    case 'active':
      // handle active
      break;
    case 'complete':
      // handle complete
      break;
    case 'failed':
      // handle failed
      break;
  }
}

// BAD: enum
enum Status {
  Pending = 'pending',
  Active = 'active',
  Complete = 'complete',
  Failed = 'failed',
}
```

**Rationale:** String literal unions are simpler, work better with discriminated unions, and don't generate runtime code.

## Type Safety

### Never Use 'any'

**Always use `unknown` for truly unknown data. If a library forces `any`, escalate to operator for replacement.**

```typescript
// GOOD: unknown with type guard
function parseJSON(json: string): unknown {
  return JSON.parse(json);
}

function processData(json: string): User {
  const data: unknown = parseJSON(json);
  if (isUser(data)) {
    return data;
  }
  throw new Error('Invalid user data');
}

function isUser(value: unknown): value is User {
  return (
    typeof value === 'object' &&
    value !== null &&
    'name' in value &&
    'email' in value
  );
}

// BAD: using any
function parseJSON(json: string): any {
  return JSON.parse(json);
}
```

### Type Assertions

**Only for TypeScript system limitations. Always include comment explaining why.**

```typescript
// OK: DOM API limitation
const input = document.getElementById('email') as HTMLInputElement;
// DOM API returns HTMLElement, but we know it's an input

// OK: after runtime validation
const data: unknown = JSON.parse(jsonString);
if (isUser(data)) {
  const user = data; // type guard narrows to User
}

// BAD: assertion without validation
const user = data as User; // no runtime check

// BAD: assertion to avoid type error
const value = (someValue as any) as TargetType;
```

### Non-null Assertion (!)

**Same rules as type assertions - sparingly, with justification.**

```typescript
// OK: after explicit check
const user = users.find(u => u.id === targetId);
if (user) {
  processUser(user); // user is non-null here, no need for !
}

// OK (with comment): known initialization pattern
class Service {
  private connection!: Connection;
  // connection initialized in async init() called by constructor

  constructor() {
    this.init();
  }

  private async init(): Promise<void> {
    this.connection = await createConnection();
  }
}

// BAD: hiding real potential null
const value = map.get(key)!; // what if key doesn't exist?
```

### Type Guards

**Use type guards to narrow unknown types. Prefer built-in checks when possible.**

```typescript
// GOOD: typeof/instanceof for primitives/classes
function processValue(value: unknown): string {
  if (typeof value === 'string') {
    return value.toUpperCase();
  }
  if (typeof value === 'number') {
    return value.toString();
  }
  throw new Error('Unsupported type');
}

// GOOD: custom type guard with 'is'
function isUser(value: unknown): value is User {
  return (
    typeof value === 'object' &&
    value !== null &&
    'name' in value &&
    typeof (value as any).name === 'string' &&
    'email' in value &&
    typeof (value as any).email === 'string'
  );
}

// GOOD: discriminated union
type Result =
  | {type: 'success'; data: string}
  | {type: 'error'; message: string};

function handleResult(result: Result): void {
  if (result.type === 'success') {
    console.log(result.data); // narrowed to success
  } else {
    console.error(result.message); // narrowed to error
  }
}

// GOOD: schema validation (TypeBox preferred)
import {Type, Static} from '@sinclair/typebox';

const UserSchema = Type.Object({
  name: Type.String(),
  email: Type.String(),
  age: Type.Number(),
});

type User = Static<typeof UserSchema>;

function validateUser(data: unknown): data is User {
  return Value.Check(UserSchema, data);
}
```

## Generics

### Generic Constraints

**Always constrain generics when possible. Use descriptive names.**

```typescript
// GOOD: constrained with descriptive name
function mapItems<TItem, TResult>(
  items: ReadonlyArray<TItem>,
  mapper: (item: TItem) => TResult,
): Array<TResult> {
  return items.map(mapper);
}

// GOOD: constraint on generic
function getProperty<TObj extends object, TKey extends keyof TObj>(
  obj: TObj,
  key: TKey,
): TObj[TKey] {
  return obj[key];
}

// BAD: unconstrained, single-letter names
function getProperty<T, K>(obj: T, key: K): any {
  return (obj as any)[key];
}
```

### Avoid Over-Generalization

**Don't make things generic unless multiple concrete types will use it.**

```typescript
// GOOD: specific types for single use case
function formatUser(user: User): string {
  return `${user.name} <${user.email}>`;
}

// BAD: unnecessary generic
function format<T extends {name: string; email: string}>(item: T): string {
  return `${item.name} <${item.email}>`;
}
```

## Utility Types

### Built-in vs type-fest

**Use built-in utilities when available. Use type-fest for deep operations and specialized needs.**

```typescript
// GOOD: built-in utilities
type PartialUser = Partial<User>;
type RequiredUser = Required<User>;
type UserKeys = keyof User;
type UserValues = User[keyof User];

// GOOD: type-fest for deep operations
import type {PartialDeep, RequiredDeep, ReadonlyDeep} from 'type-fest';

type DeepPartialConfig = PartialDeep<AppConfig>;
type DeepRequiredConfig = RequiredDeep<AppConfig>;
```

### Object Property Access

**Use `Record<K, V>` for objects with dynamic keys.**

```typescript
// GOOD: Record for dynamic keys
type UserCache = Record<string, User>;

function getUser(cache: UserCache, id: string): User | null {
  return cache[id] ?? null;
}

// BAD: index signature
type UserCache = {
  [key: string]: User;
};
```

### Derived Types

**Use mapped types for transformations. Create explicit types for complex derivations.**

```typescript
// GOOD: mapped type for simple transformation
type Nullable<T> = {
  [K in keyof T]: T[K] | null;
};

type NullableUser = Nullable<User>;

// GOOD: explicit type for complex case
type UserUpdateData = {
  name?: string;
  email?: string;
  // exclude id and other immutable fields explicitly
};

// BAD: overly clever utility type usage
type UserUpdateData = Omit<Partial<User>, 'id' | 'createdAt' | 'updatedAt'>;
```

## Module Organization

### Exports

**Use named exports only. No default exports.**

```typescript
// GOOD: named exports
export function processUser(user: User): ProcessedUser {
  // implementation
}

export type ProcessedUser = {
  id: string;
  name: string;
};

// BAD: default export
export default function processUser(user: User): ProcessedUser {
  // implementation
}
```

### Barrel Exports

**Use index.ts to re-export from directories.**

```typescript
// src/users/index.ts
export * from './user-service';
export * from './user-repository';
export * from './types';

// consumers can import from directory
import {UserService, type User} from './users';
```

### Import Organization

**Group by source type, alphabetize within groups. Use destructuring for fewer than 3 imports.**

```typescript
// GOOD: organized imports
// External dependencies
import {Result, ok, err} from 'neverthrow';
import type {ReadonlyDeep} from 'type-fest';

// Internal modules
import {DatabaseService} from '@/services/database';
import {Logger} from '@/services/logger';

// Relative imports
import {UserRepository} from './user-repository';
import type {User, UserData} from './types';

// GOOD: destructure for < 3 imports
import {foo, bar} from './utils';

// GOOD: namespace for 3+ imports
import * as utils from './utils';
utils.foo();
utils.bar();
utils.baz();
```

**Note:** eslint-import plugin should be configured to enforce import ordering.

## FCIS Integration

**Note:** `// pattern:` comments apply only to files with runtime behavior. Type-only files, constants/enum files, barrel re-exports, tests, and generated files are exempt from classification.

### Functional Core Patterns

**Return Result types. Never throw exceptions. Pure functions only.**

```typescript
// pattern: Functional Core
import {Result, ok, err} from 'neverthrow';

type ValidationError = {
  field: string;
  message: string;
};

// GOOD: returns Result, pure function
function validateUser(
  data: Readonly<UserData>,
): Result<ValidUser, ValidationError> {
  if (!data.email) {
    return err({field: 'email', message: 'Email required'});
  }
  if (!data.name) {
    return err({field: 'name', message: 'Name required'});
  }
  return ok({...data, validated: true});
}

// GOOD: transformation with Result
function transformUser(
  user: Readonly<User>,
  config: Readonly<TransformConfig>,
): Result<TransformedUser, TransformError> {
  // pure transformation logic
  return ok(transformed);
}
```

### Imperative Shell Patterns

**May throw exceptions. Orchestrate I/O. Minimal business logic.**

```typescript
// pattern: Imperative Shell
import {HttpException} from './exceptions';

class UserController {
  constructor(
    private readonly userRepo: UserRepository,
    private readonly logger: Logger,
  ) {}

  // GOOD: orchestrates I/O, delegates to Core, may throw
  async createUser(data: UserData): Promise<User> {
    this.logger.info('Creating user', {email: data.email});

    // Delegate validation to Functional Core
    const validationResult = validateUser(data);
    if (validationResult.isErr()) {
      throw new HttpException(400, validationResult.error.message);
    }

    // I/O operation
    const user = await this.userRepo.create(validationResult.value);

    this.logger.info('User created', {id: user.id});
    return user;
  }
}
```

## Compiler Configuration

### Strictness

**Full strict mode plus additional checks.**

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noPropertyAccessFromIndexSignature": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "alwaysStrict": true
  }
}
```

**All strict options are mandatory. No exceptions.**

## Testing

### Test Type Safety

**Allow type assertions in tests for test data setup.**

```typescript
// OK in tests: type assertions for test data
const mockUser = {
  id: '123',
  name: 'Test User',
} as User;

// GOOD: factory functions
function createTestUser(overrides?: Partial<User>): User {
  return {
    id: '123',
    name: 'Test User',
    email: 'test@example.com',
    ...overrides,
  };
}
```

## Tools and Libraries

### Standard Stack

- **Type utilities:** [type-fest](./type-fest.md) for deep operations and specialized utilities
- **Validation:** TypeBox preferred over zod (avoid decorator-based libraries)
- **Result types:** neverthrow for functional error handling
- **Linting:** eslint-import for import ordering

### Library Selection

**When choosing between libraries, ALWAYS prefer the one without decorators.**

```typescript
// AVOID: decorator-based libraries
import {IsEmail, IsString} from 'class-validator';

class CreateUserDto {
  @IsString()
  name: string;

  @IsEmail()
  email: string;
}

// PREFER: schema-based validation
import {Type} from '@sinclair/typebox';

const CreateUserSchema = Type.Object({
  name: Type.String(),
  email: Type.String({format: 'email'}),
});
```

## Documentation

### JSDoc for Public APIs

**Use JSDoc comments for exported functions and types.**

```typescript
/**
 * Processes user data and returns a validated user object.
 *
 * @param data - Raw user data to process
 * @returns Result containing validated user or validation error
 */
export function validateUser(
  data: Readonly<UserData>,
): Result<ValidUser, ValidationError> {
  // implementation
}

/**
 * Configuration options for user processing.
 */
export type ProcessUserOptions = {
  /** User's full name */
  readonly name: string;
  /** User's email address */
  readonly email: string;
  /** Whether to send welcome email (default: true) */
  readonly sendWelcome?: boolean;
};
```

## Abstraction Guidelines

### When to Abstract

**Follow rule of three. Abstract when types become complex (3+ properties/levels).**

```typescript
// GOOD: abstract after third repetition
// First use
const user1 = {id: '1', name: 'Alice', email: 'alice@example.com'};

// Second use
const user2 = {id: '2', name: 'Bob', email: 'bob@example.com'};

// Third use - now abstract
type User = {
  id: string;
  name: string;
  email: string;
};

// GOOD: abstract complex inline types
// Before
function process(data: {
  user: {name: string; email: string};
  settings: {theme: string; notifications: boolean};
}): void {}

// After - extract when > 3 properties or nested
type UserInfo = {
  name: string;
  email: string;
};

type UserSettings = {
  theme: string;
  notifications: boolean;
};

type ProcessData = {
  user: UserInfo;
  settings: UserSettings;
};

function process(data: Readonly<ProcessData>): void {}
```

## Sharp Edges

Runtime hazards that TypeScript doesn't catch. Know these cold.

### Equality

**Always use `===`. Never use `==`.**

```typescript
// BAD: loose equality has surprising coercion
"0" == false;   // true
[] == ![];      // true
null == undefined; // true

// GOOD: strict equality
"0" === false;  // false
[] === ![];     // false
null === undefined; // false
```

TypeScript won't save you here—both are valid syntax.

### Prototype Pollution

**Never merge untrusted objects into plain objects.**

```typescript
// DANGEROUS: merging user input
const userInput = JSON.parse('{"__proto__": {"isAdmin": true}}');
Object.assign({}, userInput); // pollutes Object.prototype

// SAFE: use Map for dynamic keys from untrusted sources
const safeStore = new Map<string, unknown>();
safeStore.set(key, value);

// SAFE: null-prototype object
const safeObj = Object.create(null) as Record<string, unknown>;

// SAFE: validate keys before merge
function safeMerge<T extends object>(target: T, source: unknown): T {
  if (typeof source !== 'object' || source === null) return target;
  for (const key of Object.keys(source)) {
    if (key === '__proto__' || key === 'constructor' || key === 'prototype') {
      continue; // skip dangerous keys
    }
    (target as Record<string, unknown>)[key] = (source as Record<string, unknown>)[key];
  }
  return target;
}
```

### Regular Expression DoS (ReDoS)

**Avoid nested quantifiers and overlapping alternatives.**

```typescript
// DANGEROUS: catastrophic backtracking
const bad1 = /(a+)+$/;           // nested quantifiers
const bad2 = /(a|a)+$/;          // overlapping alternatives
const bad3 = /(\w+)*$/;          // greedy quantifier in group with quantifier

// These can freeze the event loop on crafted input like "aaaaaaaaaaaaaaaaaaaaaaaa!"

// SAFER: avoid nesting, use possessive-like patterns
const safer = /a+$/;             // no nesting
const safest = /^[a-z]+$/;       // anchored, simple character class
```

When accepting user-provided regex patterns, use a timeout or run in a worker.

### parseInt Radix

**Always specify the radix parameter.**

```typescript
// BAD: radix varies by engine/input
parseInt("08");     // 0 or 8 depending on engine
parseInt("0x10");   // 16 (hex prefix always recognized)

// GOOD: explicit radix
parseInt("08", 10);   // 8
parseInt("10", 16);   // 16
parseInt("1010", 2);  // 10

// BETTER: use Number() for decimal
Number("08");         // 8
Number.parseInt("08", 10); // 8
```

### Array Mutations

**Know which methods mutate in place.**

| Mutates | Returns new array |
|---------|-------------------|
| `.sort()` | `.toSorted()` (ES2023) |
| `.reverse()` | `.toReversed()` (ES2023) |
| `.splice()` | `.toSpliced()` (ES2023) |
| `.push()`, `.pop()` | `.concat()`, `.slice()` |
| `.shift()`, `.unshift()` | spread: `[first, ...rest]` |
| `.fill()` | - |

```typescript
// BAD: mutates original
const original = [3, 1, 2];
const sorted = original.sort(); // original is now [1, 2, 3]

// GOOD: copy first (pre-ES2023)
const sorted = [...original].sort();
const sorted = original.slice().sort();

// GOOD: use non-mutating methods (ES2023+)
const sorted = original.toSorted();
const reversed = original.toReversed();
```

### Numeric Sort

**Default sort is lexicographic, not numeric.**

```typescript
// WRONG: sorts as strings
[10, 2, 1].sort();  // [1, 10, 2]

// CORRECT: numeric comparator
[10, 2, 1].sort((a, b) => a - b);  // [1, 2, 10]

// Descending
[10, 2, 1].sort((a, b) => b - a);  // [10, 2, 1]
```

### eval and Function Constructor

**Never use eval() or new Function() with untrusted input.**

```typescript
// DANGEROUS: code injection
eval(userInput);                    // arbitrary code execution
new Function('return ' + userInput)(); // same risk

// If you need dynamic evaluation, use a sandboxed environment or parser
```

### JSON Precision Loss

**JSON.parse loses precision for large integers and BigInt.**

```typescript
// PROBLEM: JavaScript numbers lose precision > 2^53
JSON.parse('{"id": 9007199254740993}'); // id becomes 9007199254740992

// PROBLEM: BigInt not supported
JSON.parse('{"value": 123n}'); // SyntaxError

// SOLUTION: use string representation for large IDs
type ApiResponse = {
  id: string; // "9007199254740993" - keep as string
};

// SOLUTION: use a BigInt-aware parser for financial data
// Or use string fields and parse with BigInt() after
```

### Promise.all vs Promise.allSettled

**Promise.all fails fast; Promise.allSettled waits for all.**

```typescript
// Promise.all: rejects immediately on first failure
// Use when: all must succeed, fail fast is desired
async function fetchAllRequired(ids: ReadonlyArray<string>): Promise<Array<User>> {
  const promises = ids.map(id => fetchUser(id));
  return Promise.all(promises); // throws on first failure
}

// Promise.allSettled: waits for all, never rejects
// Use when: need results from successful ones even if some fail
async function fetchAllBestEffort(
  ids: ReadonlyArray<string>,
): Promise<Array<User>> {
  const promises = ids.map(id => fetchUser(id));
  const results = await Promise.allSettled(promises);

  return results
    .filter((r): r is PromiseFulfilledResult<User> => r.status === 'fulfilled')
    .map(r => r.value);
}

// Common patterns with allSettled
const results = await Promise.allSettled(promises);

const succeeded = results.filter(r => r.status === 'fulfilled');
const failed = results.filter(r => r.status === 'rejected');

// Log failures, return successes
for (const failure of failed) {
  if (failure.status === 'rejected') {
    logger.error('Operation failed', {reason: failure.reason});
  }
}
```

| Method | Behavior | Use when |
|--------|----------|----------|
| `Promise.all` | Rejects on first failure | All must succeed |
| `Promise.allSettled` | Always resolves with status array | Need partial results |
| `Promise.race` | Resolves/rejects with first to complete | Timeout patterns |
| `Promise.any` | Resolves with first success, rejects if all fail | First success wins |

### Unsafe Property Access

**Bracket notation with user input is dangerous.**

```typescript
// DANGEROUS: arbitrary property access
function getValue(obj: object, key: string): unknown {
  return (obj as Record<string, unknown>)[key]; // could access __proto__, constructor
}

// SAFER: validate or use Map
function safeGetValue(obj: Record<string, unknown>, key: string): unknown {
  if (!Object.hasOwn(obj, key)) return undefined;
  if (key === '__proto__' || key === 'constructor') return undefined;
  return obj[key];
}
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using `interface` for data shapes | Use `type` instead |
| Using `any` in business logic | Use `unknown` + type guards |
| `const foo = () => {}` top-level declarations | Use `function foo() {}` |
| Type assertions without validation | Add runtime validation or type guard |
| Mutable parameters | Mark as `Readonly<T>` for reference types |
| `undefined` for absent values | Use `null`; coalesce with `?? null` |
| Enums | Use string literal unions |
| Missing return types on exports | Always type function returns |
| Using `T[]` for arrays | Use `Array<T>` or `ReadonlyArray<T>` |
| JavaScript `number` for money/currency | Use math.js with BigNumber |
| Decorators (unless framework requires) | Use functions or type-based solutions |
| Default exports | Use named exports only |
| Over-abstraction before third use | Wait for pattern to emerge |
| Title Case error messages | Use lowercase fragments: `failed to connect: timeout` |
| Unnecessary async on pure functions | Keep sync unless I/O is involved |
| `==` for comparisons | Use `===` always |
| `parseInt()` without radix | Use `parseInt(str, 10)` or `Number()` |
| `.sort()` on numeric arrays without comparator | Use `.sort((a, b) => a - b)` |
| `Object.assign()` with untrusted input | Validate keys or use `Map` |
| Nested regex quantifiers `(a+)+` | Refactor to avoid ReDoS |
| `Promise.all` when partial results acceptable | Use `Promise.allSettled` |

## Red Flags

**STOP and refactor when you see:**

- `any` keyword in business logic
- `interface` for data shapes (not class contracts)
- JavaScript `number` for money, currency, or financial calculations
- `T[]` instead of `Array<T>` syntax
- Decorators in library selection
- Type assertions without explanatory comments
- Missing return types on exported functions
- Mutable class fields (should be `readonly`)
- `undefined` used for explicitly absent values
- Enums instead of string literal unions
- Default exports
- Functions with 4+ positional parameters
- Complex inline types used repeatedly
- Async functions that don't perform I/O
- Error messages in Title Case
- `==` instead of `===`
- `eval()` or `new Function()` with any dynamic input
- Regex patterns with nested quantifiers `(x+)+` or `(x|x)+`
- `Object.assign()` or spread with user-controlled objects
- `parseInt()` without explicit radix
- `.sort()` on numbers without comparator function
- `JSON.parse()` on data with large integer IDs (use string IDs)

## Reference

For comprehensive type-fest utilities documentation, see [type-fest.md](./type-fest.md).

For comprehensive TypeBox validator documentation, see [typebox.md](./typebox.md). Please note that we generally use AJV as the canonical validator, but TypeBox is the schema generator.
