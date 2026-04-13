---
name: howto-develop-with-postgres
description: Use when writing database access code, creating schemas, or managing transactions with PostgreSQL - enforces transaction safety with TX_ naming, read-write separation, type safety for UUIDs/JSONB, and snake_case conventions to prevent data corruption and type errors
user-invocable: false
---

# PostgreSQL Development Patterns

## Overview

Enforce transaction safety, type safety, and naming conventions to prevent data corruption and runtime errors.

**Core principles:**
- Transactions prevent partial updates (data corruption)
- Type safety catches errors at compile time
- Naming conventions ensure consistency
- Read-write separation prevents accidental mutations

**For TypeScript/Drizzle implementations:** See [typescript-drizzle.md](./typescript-drizzle.md) for concrete patterns.

## Transaction Management

### TX_ Prefix Rule (STRICT ENFORCEMENT)

**Methods that START transactions:**
- Prefix method name with `TX_`
- Must NOT accept connection/executor parameter
- Call `connection.transaction()` or `db.transaction()` internally

**Methods that PARTICIPATE in transactions:**
- No `TX_` prefix
- MUST accept connection/executor parameter with default value
- Execute queries using the provided executor

```typescript
// GOOD: Starts transaction, has TX_ prefix, no executor parameter
async TX_createUserWithProfile(userData: UserData, profileData: ProfileData): Promise<User> {
  return this.db.transaction(async (tx) => {
    const user = await this.createUser(userData, tx);
    await this.createProfile(user.id, profileData, tx);
    return user;
  });
}

// GOOD: Participates in transaction, no TX_ prefix, takes executor
async createUser(userData: UserData, executor: Drizzle = this.db): Promise<User> {
  return executor.insert(USERS).values(userData).returning();
}

// BAD: Starts transaction but missing TX_ prefix
async createUserWithProfile(userData: UserData, profileData: ProfileData): Promise<User> {
  return this.db.transaction(async (tx) => { /* ... */ });
}

// BAD: Has TX_ prefix but takes executor parameter (allows nesting)
async TX_createUser(userData: UserData, executor: Drizzle = this.db): Promise<User> {
  return executor.transaction(async (tx) => { /* ... */ });
}
```

**What DOES NOT count as "starting a transaction":**
- Single INSERT/UPDATE/DELETE operations
- Atomic operations like `onConflictDoUpdate`
- SELECT queries

## Type Safety

### Primary Keys

**Default: ULID stored as UUID**
- When in doubt, use ULID: "Most things can leak in some way"
- Prevents ID enumeration attacks
- Time-sortable for indexing efficiency

**Exceptions (context-dependent):**
- Pure join tables (composite PK from both FKs)
- Small lookup tables (serial/identity acceptable)
- Internal-only tables with no user visibility (serial/identity acceptable)

**Rule:** If unsure whether data will be user-visible, use ULID.

### Financial Data

**Use exact decimal types (numeric/decimal) for monetary values:**
- Never use float/double for money (causes rounding errors)
- Use numeric/decimal with appropriate precision and scale
- Example: `numeric(19, 4)` for general financial data

**Why:** Floating-point types accumulate rounding errors. Exact decimal types prevent financial discrepancies.

### JSONB Columns

**ALWAYS type JSONB columns in your ORM/schema:**
- Use typed schema when structure is known
- Use `Record<string, unknown>` if truly schemaless
- Never leave JSONB untyped

**Why:** Prevents runtime errors from accessing undefined properties or wrong types.

### Read-Write Separation

**Maintain separate client types at compile time:**
- Read-write client: Full mutation capabilities
- Read-only client: Mutation methods removed at type level
- Default to read-only for query methods
- Use read-write only when mutations needed

**Why:** Prevents accidental writes to replica, enforces deliberate mutation choices.

## Naming Conventions

### Database Identifiers

**All database objects use snake_case:**
- Tables: `user_preferences`, `order_items`
- Columns: `created_at`, `user_id`, `is_active`
- Indexes: `idx_tablename_columns` (e.g., `idx_users_email`)
- Foreign keys: `fk_tablename_reftable` (e.g., `fk_orders_users`)

**Application code:** Map to idiomatic case (camelCase in TypeScript, etc.)

### Schema Patterns

**Standard mixins:**
- `created_at`, `updated_at` timestamps on all tables
- `deleted_at` for soft deletion when needed
- `tenant_id` for multi-tenant tables (project-dependent)

**Proactive indexing:**
- All foreign key columns
- Columns used in WHERE clauses
- Columns used in JOIN conditions
- Columns used in ORDER BY

## Concurrency

**Default isolation (Read Committed) for most operations.**

**Use stricter isolation when:**
- Financial operations: Serializable isolation
- Inventory/count operations: Serializable isolation
- Critical sections: Pessimistic locking (`SELECT ... FOR UPDATE`)

## Migrations

**Always use generate + migrate workflow:**
1. Change schema in code
2. Generate migration file
3. Review migration SQL
4. Apply migration to database

**Never use auto-push workflow in production.**

## Common Mistakes

| Mistake | Reality | Fix |
|---------|---------|-----|
| "This is one operation, doesn't need transaction" | Multi-step operations without transactions cause partial updates and data corruption | Wrap in transaction with TX_ prefix |
| "Single atomic operation needs TX_ prefix" | TX_ is for explicit transaction blocks, not atomic operations | No TX_ for single INSERT/UPDATE/DELETE |
| "UUID is just a string" | Type confusion causes runtime errors (wrong ID formats, failed lookups) | Use strict UUID type in language |
| "I'll type JSONB later when schema stabilizes" | Untyped JSONB leads to undefined property access and type errors | Type immediately with known fields or Record<string, unknown> |
| "Read client vs write client doesn't matter" | Using wrong client bypasses separation, allows accidental mutations | Use read-only client by default, switch deliberately |
| "I'll add indexes when we see performance issues" | Missing indexes on foreign keys cause slow queries from day one | Add indexes proactively for FKs and common filters |
| "This table won't be user-visible, use serial" | Requirements change, IDs leak in logs/URLs/errors | Use ULID by default unless certain it's internal-only |
| "Float/double is fine for money, close enough" | Rounding errors accumulate, causing financial discrepancies (0.01 differences multiply) | Use numeric/decimal types for exact arithmetic |

## Red Flags - STOP and Refactor

**Transaction management:**
- Method calls `.transaction()` but no `TX_` prefix
- Method has `TX_` prefix but accepts executor parameter
- Multi-step operation without transaction wrapper

**Type safety:**
- JSONB column without type annotation
- UUID/ULID stored as plain string type
- No separation between read and write clients
- Float/double types for monetary values

**Schema:**
- Missing indexes on foreign keys
- No `created_at`/`updated_at` timestamps
- camelCase or PascalCase in database identifiers

**All of these mean: Stop and fix immediately.**

## Reference

For TypeScript/Drizzle concrete implementations: [typescript-drizzle.md](./typescript-drizzle.md)
