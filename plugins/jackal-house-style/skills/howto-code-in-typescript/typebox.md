# TypeBox - JSON Schema Type Builder

Runtime type system creating JSON Schema objects that infer as TypeScript types.

## Installation
```bash
npm install typebox
```

## Core Concept
```typescript
import Type from 'typebox'

const T = Type.Object({
  x: Type.Number(),
  y: Type.Number()
})

type T = Type.Static<typeof T>  // Infer TypeScript type from schema
```

## Primary Modules

### Type Builder (`typebox`)
Creates JSON Schema types that match TypeScript static checking rules.

**Constraints/metadata:** Pass as last argument to any type function
```typescript
Type.Number({ minimum: 0, maximum: 100 })
Type.String({ format: 'email' })
Type.Object({ id: Type.String() }, { description: 'A message' })
```

### Script (`typebox`)
Type-safe translation of TypeScript syntax to JSON Schema
```typescript
const T = Type.Script(`{ x: number, y: number }`)

const S = Type.Script({ T }, `{
  [K in keyof T]: T[K] | null
}`)

type S = Type.Static<typeof S>  // { x: number | null, y: number | null }
```

### Value (`typebox/value`)
Runtime operations on JavaScript values
```typescript
import Value from 'typebox/value'

Value.Check(T, value)     // Boolean validation
Value.Parse(T, value)     // Parse and return typed value
Value.Clone(value)        // Deep clone
Value.Repair(T, value)    // Fix value to match schema
Value.Encode(T, value)    // Encode value
Value.Decode(T, value)    // Decode value
Value.Diff(left, right)   // Structural diff
Value.Patch(value, diff)  // Apply diff
```

### Compile (`typebox/compile`)
High-performance compiled validators
```typescript
import { Compile } from 'typebox/compile'

const C = Compile(Type.Object({
  x: Type.Number(),
  y: Type.Number()
}))

C.Check(value)  // Fast validation
C.Parse(value)  // Fast parsing
```

## Type Functions

All functions create JSON Schema fragments corresponding to TypeScript types.

### Primitives
- `Type.Any()` - any
- `Type.Unknown()` - unknown
- `Type.String()` - string
- `Type.Number()` - number
- `Type.Integer()` - integer
- `Type.Boolean()` - boolean
- `Type.Null()` - null
- `Type.Void()` - void
- `Type.Undefined()` - undefined
- `Type.Symbol()` - symbol
- `Type.BigInt()` - bigint
- `Type.Never()` - never

### Objects & Records
- `Type.Object({ ... })` - Object with properties
- `Type.Record(K, V)` - Record<K, V>
- `Type.Partial(T)` - Partial<T>
- `Type.Required(T)` - Required<T>
- `Type.Pick(T, [...keys])` - Pick<T, K>
- `Type.Omit(T, [...keys])` - Omit<T, K>

### Arrays & Tuples
- `Type.Array(T)` - T[]
- `Type.Tuple([...types])` - [T, U, V]
- `Type.Rest(T)` - ...T[]

### Union & Intersection
- `Type.Union([...types])` - T | U | V
- `Type.Intersect([...types])` - T & U & V
- `Type.Enum({ A: 1, B: 2 })` - enum
- `Type.Literal(value)` - literal type

### Functions & Constructors
- `Type.Function([...params], returns)` - Function signature
- `Type.Constructor([...params], returns)` - Constructor signature

### Template & Patterns
- `Type.TemplateLiteral('prefix-${string}')` - Template literal type
- `Type.Pattern(/regex/)` - String matching pattern

### Special Types
- `Type.Promise(T)` - Promise<T>
- `Type.Awaited(T)` - Awaited<T>
- `Type.Date()` - Date
- `Type.Uint8Array()` - Uint8Array
- `Type.RegExp()` - RegExp

### Modifiers
- `Type.Optional(T)` - T?
- `Type.Readonly(T)` - Readonly<T>
- `Type.ReadonlyOptional(T)` - readonly T?

### Conditionals & Mapped
- `Type.Extends(L, R, T, F)` - L extends R ? T : F
- `Type.Mapped(T, fn)` - { [K in keyof T]: ... }
- `Type.Index(T, K)` - T[K]
- `Type.KeyOf(T)` - keyof T

### Recursive
- `Type.Recursive(fn)` - Self-referential types
```typescript
const Node = Type.Recursive(Self => Type.Object({
  value: Type.Number(),
  left: Type.Optional(Self),
  right: Type.Optional(Self)
}))
```

### Unsafe & References
- `Type.Unsafe({ ... })` - Custom JSON Schema
- `Type.Ref(T)` - $ref to reusable schema

## Common Patterns

### Optional Properties
```typescript
Type.Object({
  required: Type.String(),
  optional: Type.Optional(Type.String())
})
```

### Nullable Types
```typescript
Type.Union([Type.String(), Type.Null()])
```

### Discriminated Unions
```typescript
Type.Union([
  Type.Object({ type: Type.Literal('A'), value: Type.Number() }),
  Type.Object({ type: Type.Literal('B'), value: Type.String() })
])
```

### Generic-like Types
```typescript
const Generic = <T extends TSchema>(T: T) => Type.Object({
  data: T,
  meta: Type.String()
})

const StringData = Generic(Type.String())
```

## Performance Notes
- Compile module provides fastest validation (~100x faster than Value.Check in benchmarks)
- Use compiled validators for hot paths
- Script adds compilation overhead, use sparingly
