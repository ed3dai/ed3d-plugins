# type-fest - TypeScript Types Reference

## Installation
```sh
npm install type-fest
```
Requires TypeScript >=5.9, ESM, strict mode.

## Usage
```ts
import type {Except} from 'type-fest';
```

## Basic Types
- `Primitive` - Matches any primitive value
- `Class` - Matches a class
- `Constructor` - Matches a class constructor
- `AbstractClass` - Matches an abstract class
- `AbstractConstructor` - Matches an abstract class constructor
- `TypedArray` - Matches typed arrays (Uint8Array, Float64Array, etc.)
- `ObservableLike` - Matches Observable-like values
- `LowercaseLetter` - Matches a-z
- `UppercaseLetter` - Matches A-Z
- `DigitCharacter` - Matches '0'-'9'
- `Alphanumeric` - Matches a-z, A-Z, 0-9

## Object Utilities
- `EmptyObject` - Strictly empty plain object `{}`
- `NonEmptyObject` - Object with at least 1 non-optional key
- `UnknownRecord` - Object with unknown values (prefer over `{}`)
- `Except<T, K>` - Stricter version of Omit
- `Writable<T>` - Strips readonly from type
- `WritableDeep<T>` - Deep mutable version of object/Map/Set/Array
- `Merge<T, U>` - Merge two types, U overrides T
- `MergeDeep<T, U>` - Recursively merge objects/arrays
- `MergeExclusive<T, U>` - Mutually exclusive keys
- `OverrideProperties<T, U>` - Override existing properties only
- `RequireAtLeastOne<T, K>` - At least one of given keys required
- `RequireExactlyOne<T, K>` - Exactly one of given keys required
- `RequireAllOrNone<T, K>` - All or none of given keys
- `RequireOneOrNone<T, K>` - Exactly one or none of given keys
- `SingleKeyObject<K, V>` - Object with single key only
- `RequiredDeep<T>` - Deep required version
- `PickDeep<T, P>` - Pick from deeply-nested object
- `OmitDeep<T, P>` - Omit from deeply-nested object
- `OmitIndexSignature<T>` - Omit index signatures, keep explicit properties
- `PickIndexSignature<T>` - Pick only index signatures
- `PartialDeep<T>` - Deep optional version
- `PartialOnUndefinedDeep<T>` - Keys accepting undefined become optional
- `UndefinedOnPartialDeep<T>` - Optional keys also accept undefined
- `ReadonlyDeep<T>` - Deep immutable version
- `SetOptional<T, K>` - Make given keys optional
- `SetReadonly<T, K>` - Make given keys readonly
- `SetRequired<T, K>` - Make given keys required
- `SetRequiredDeep<T, P>` - Deep version of SetRequired
- `SetNonNullable<T, K>` - Make given keys non-nullable
- `SetNonNullableDeep<T, P>` - Deep non-nullable for key paths
- `SetFieldType<T, K, V>` - Change type of given keys
- `Simplify<T>` - Flatten type output for better hints
- `SimplifyDeep<T>` - Deep simplify object type
- `Schema<T, V>` - Replace property values recursively with given type
- `Exact<T>` - Disallow extra properties
- `Spread<T, U>` - Mimic TypeScript spread type inference

## Key Utilities
- `ValueOf<T, K>` - Union of object's values
- `ConditionalKeys<T, Condition>` - Extract keys where values extend Condition
- `ConditionalPick<T, Condition>` - Pick properties where values extend Condition
- `ConditionalPickDeep<T, Condition>` - Deep version of ConditionalPick
- `ConditionalExcept<T, Condition>` - Remove properties where values extend Condition
- `KeysOfUnion<T>` - All keys from union, including exclusive ones
- `OptionalKeysOf<T>` - Extract optional keys
- `HasOptionalKeys<T>` - true/false if type has optional fields
- `RequiredKeysOf<T>` - Extract required keys
- `HasRequiredKeys<T>` - true/false if type has required fields
- `ReadonlyKeysOf<T>` - Extract readonly keys
- `HasReadonlyKeys<T>` - true/false if type has readonly fields
- `WritableKeysOf<T>` - Extract writable keys
- `HasWritableKeys<T>` - true/false if type has writable fields
- `KeyAsString<T>` - Get keys as strings

## Type Transformation
- `UnionToIntersection<T>` - Convert union to intersection
- `LiteralToPrimitive<T>` - Convert literal to primitive type
- `LiteralToPrimitiveDeep<T>` - Deep literal to primitive conversion
- `Stringified<T>` - Change all keys to string type
- `Get<T, Path>` - Get deeply-nested property via key path
- `Paths<T>` - Union of all possible paths to properties
- `IterableElement<T>` - Get element type of Iterable/AsyncIterable
- `Entry<T>` - Type of collection entry
- `Entries<T>` - Type of collection entries
- `InvariantOf<T>` - Create invariant type (no super/subtypes)
- `DistributedOmit<T, K>` - Omit distributing over union
- `DistributedPick<T, K>` - Pick distributing over union

## Union/Intersection Utilities
- `SharedUnionFields<T>` - Shared fields from union of objects
- `SharedUnionFieldsDeep<T>` - Deep shared fields from union
- `AllUnionFields<T>` - All fields from union of objects
- `LiteralUnion<T, U>` - Union preserving autocomplete for literals
- `TaggedUnion<T, K>` - Union with common discriminant property

## Type Guards
- `If<Condition, Then, Else>` - If-else type resolution
- `IsLiteral<T>` - true if literal type
- `IsStringLiteral<T>` - true if string literal
- `IsNumericLiteral<T>` - true if number/bigint literal
- `IsBooleanLiteral<T>` - true if true/false literal
- `IsSymbolLiteral<T>` - true if symbol literal
- `IsAny<T>` - true if any
- `IsNever<T>` - true if never
- `IsUnknown<T>` - true if unknown
- `IsEmptyObject<T>` - true if strictly `{}`
- `IsNull<T>` - true if null
- `IsUndefined<T>` - true if undefined
- `IsTuple<T>` - true if tuple
- `IsUnion<T>` - true if union
- `IsLowercase<T>` - true if lowercase string literal
- `IsUppercase<T>` - true if uppercase string literal
- `IsOptional<T>` - true if includes undefined
- `IsNullable<T>` - true if includes null
- `IsOptionalKeyOf<T, K>` - true if key is optional
- `IsRequiredKeyOf<T, K>` - true if key is required
- `IsReadonlyKeyOf<T, K>` - true if key is readonly
- `IsWritableKeyOf<T, K>` - true if key is writable
- `IsEqual<T, U>` - true if types are equal
- `And<A, B>` - Boolean AND for types
- `Or<A, B>` - Boolean OR for types
- `Xor<A, B>` - Boolean XOR for types
- `AllExtend<T[], U>` - true if all elements extend U

## Function Utilities
- `SetReturnType<T, R>` - Function with new return type
- `SetParameterType<T, P>` - Function with replaced parameters
- `Asyncify<T>` - Async version of function
- `AsyncReturnType<T>` - Unwrap Promise return type
- `Promisable<T>` - Value or PromiseLike of value

## String Utilities
- `Trim<T>` - Remove leading/trailing spaces
- `Split<T, Delim>` - Split string by delimiter
- `Words<T>` - Split string into words
- `Replace<T, From, To>` - Replace matches in string
- `StringSlice<T, Start, End>` - String slice like String#slice()
- `StringRepeat<T, N>` - Repeat string N times
- `RemovePrefix<T, Prefix>` - Remove prefix from string start

## Case Conversion
- `CamelCase<T>` - Convert to camelCase
- `CamelCasedProperties<T>` - Object properties to camelCase
- `CamelCasedPropertiesDeep<T>` - Deep camelCase properties
- `KebabCase<T>` - Convert to kebab-case
- `KebabCasedProperties<T>` - Object properties to kebab-case
- `KebabCasedPropertiesDeep<T>` - Deep kebab-case properties
- `PascalCase<T>` - Convert to PascalCase
- `PascalCasedProperties<T>` - Object properties to PascalCase
- `PascalCasedPropertiesDeep<T>` - Deep PascalCase properties
- `SnakeCase<T>` - Convert to snake_case
- `SnakeCasedProperties<T>` - Object properties to snake_case
- `SnakeCasedPropertiesDeep<T>` - Deep snake_case properties
- `ScreamingSnakeCase<T>` - Convert to SCREAMING_SNAKE_CASE
- `DelimiterCase<T, Delim>` - Custom delimiter casing
- `DelimiterCasedProperties<T, Delim>` - Custom delimiter for properties
- `DelimiterCasedPropertiesDeep<T, Delim>` - Deep custom delimiter

## Array/Tuple Utilities
- `UnknownArray` - Array with unknown values
- `Arrayable<T>` - Value or array of value
- `Includes<T[], U>` - Boolean for array includes item
- `Join<T[], Delim>` - Join array with delimiter
- `ArraySlice<T[], Start, End>` - Array slice like Array#slice()
- `ArrayElement<T[]>` - Extract element type
- `LastArrayElement<T[]>` - Type of last element
- `FixedLengthArray<T, N>` - Array of exact length
- `MultidimensionalArray<T, Dims>` - Multidimensional array
- `MultidimensionalReadonlyArray<T, Dims>` - Readonly multidimensional array
- `ReadonlyTuple<T, N>` - Readonly tuple
- `TupleToUnion<T>` - Convert tuple to union
- `UnionToTuple<T>` - Convert union to tuple (unordered)
- `TupleToObject<T>` - Tuple index to key-value pairs
- `TupleOf<T, N>` - Tuple of length N with type T
- `SplitOnRestElement<T>` - Split array at rest element
- `ExtractRestElement<T>` - Extract rest element type
- `ExcludeRestElement<T>` - Remove rest element from tuple
- `NonEmptyTuple` - Matches non-empty tuple
- `ArrayIndices<T>` - Valid indices for array/tuple
- `ArrayValues<T>` - All values for array/tuple
- `ArraySplice<T, Index, Del, Items>` - Add/remove elements at index
- `ArrayTail<T>` - Array minus first element

## Numeric Utilities
- `PositiveInfinity` - Matches Infinity
- `NegativeInfinity` - Matches -Infinity
- `Finite` - Finite number
- `Integer` - Integer number
- `Float` - Non-integer number
- `NegativeFloat` - Negative non-integer
- `Negative` - Negative number/bigint
- `NonNegative` - Non-negative number/bigint
- `NegativeInteger` - Negative integer
- `NonNegativeInteger` - Non-negative integer
- `IsNegative<T>` - true if negative number
- `IsFloat<T>` - true if float
- `IsInteger<T>` - true if integer
- `GreaterThan<A, B>` - true if A > B
- `GreaterThanOrEqual<A, B>` - true if A >= B
- `LessThan<A, B>` - true if A < B
- `LessThanOrEqual<A, B>` - true if A <= B
- `Sum<A, B>` - Sum of two numbers
- `Subtract<A, B>` - Difference of two numbers
- `IntRange<Start, End>` - Union of integers [Start, End)
- `IntClosedRange<Start, End>` - Union of integers [Start, End]

## JSON Utilities
- `Jsonify<T>` - Transform to JsonValue-assignable type
- `Jsonifiable` - Matches losslessly JSON-convertible values
- `JsonPrimitive` - JSON primitive
- `JsonObject` - JSON object
- `JsonArray` - JSON array
- `JsonValue` - Any valid JSON value

## Other Utilities
- `UnknownMap` - Map with unknown key/value
- `UnknownSet` - Set with unknown value
- `StructuredCloneable` - Matches structuredClone-compatible values
- `Tagged<Base, Tag>` - Tagged type with metadata support
- `UnwrapTagged<T>` - Get untagged portion
- `GlobalThis` - Declare properties on globalThis
- `PackageJson` - Type for package.json
- `TsConfigJson` - Type for tsconfig.json
- `NonEmptyString` - Matches non-empty string
- `FindGlobalType<Name>` - Find global type by name
- `FindGlobalInstanceType<Names>` - Find types from global constructors
- `ConditionalSimplify<T, Include, Exclude>` - Selective simplification
- `ConditionalSimplifyDeep<T, Include, Exclude>` - Deep selective simplification
- `ExtendsStrict<T, U>` - Non-distributive extends check
- `ExtractStrict<T, U>` - Strict Extract ensuring all U members extract
- `ExcludeStrict<T, U>` - Strict Exclude ensuring all U members exclude

## TypeScript Built-in Utilities (for reference)
- `Awaited<T>` - Extract Promise resolved type
- `Partial<T>` - All properties optional
- `Required<T>` - All properties required
- `Readonly<T>` - All properties readonly
- `Pick<T, K>` - Subset of properties
- `Record<K, T>` - Object type with keys K of type T
- `Exclude<T, U>` - Remove types assignable to U
- `Extract<T, U>` - Extract types assignable to U
- `NonNullable<T>` - Exclude null/undefined
- `Parameters<T>` - Function parameters as tuple
- `ConstructorParameters<T>` - Constructor parameters as tuple
- `ReturnType<T>` - Function return type
- `InstanceType<T>` - Constructor instance type
- `Omit<T, K>` - Remove properties K from T
- `Uppercase<S>` - Transform to uppercase
- `Lowercase<S>` - Transform to lowercase
- `Capitalize<S>` - Capitalize first character
- `Uncapitalize<S>` - Lowercase first character

## Alternative Names
- `Prettify` / `Expand` -> Use `Simplify`
- `PartialBy` -> Use `SetOptional`
- `RecordDeep` -> Use `Schema`
- `Mutable` -> Use `Writable`
- `RequireOnlyOne` / `OneOf` -> Use `RequireExactlyOne`
- `AtMostOne` -> Use `RequireOneOrNone`
- `AllKeys` -> Use `KeysOfUnion`
- `Branded` / `Opaque` -> Use `Tagged`
- `SetElement` / `SetEntry` / `SetValues` -> Use `IterableElement`
- `PickByTypes` -> Use `ConditionalPick`
- `HomomorphicOmit` -> Use `Except`
- `IfAny` / `IfNever` / `If*` -> Use `If`
- `MaybePromise` -> Use `Promisable`
