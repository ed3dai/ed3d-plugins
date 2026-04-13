# TypeScript + Drizzle ORM Implementation Guide

Concrete implementation patterns for PostgreSQL development with TypeScript and Drizzle ORM.

## Type Definitions

### Drizzle Client Separation

**Create separate types for read-write and read-only clients:**

```typescript
// File: lib/datastores/postgres/types.ts
import type { drizzle } from "drizzle-orm/node-postgres";

export type Drizzle = Omit<ReturnType<typeof drizzle>, "$client">;

export type DrizzleMutableMethods = "insert" | "update" | "delete";
export type DrizzleRO = Omit<Drizzle, DrizzleMutableMethods>;

export type Executor = Pick<Drizzle, DrizzleMutableMethods | "select">;
export type ExecutorRO = Pick<DrizzleRO, "select">;

export * from "drizzle-orm";
```

**Usage in service classes:**

```typescript
class UserService {
  constructor(
    logger: Logger,
    private readonly db: Drizzle,        // Read-write client
    private readonly dbRO: DrizzleRO,    // Read-only client
  ) {
    this.logger = logger.child({ component: this.constructor.name });
  }

  // Query method defaults to read-only
  async getUser(id: string, executor: DrizzleRO = this.dbRO): Promise<User | null> {
    const result = await executor
      .select()
      .from(USERS)
      .where(eq(USERS.userId, id))
      .limit(1);
    return result[0] ?? null;
  }

  // Mutation method defaults to read-write
  async updateUser(id: string, data: UserUpdate, executor: Drizzle = this.db): Promise<User> {
    const [user] = await executor
      .update(USERS)
      .set(data)
      .where(eq(USERS.userId, id))
      .returning();

    if (!user) throw new Error("User not found");
    return user;
  }
}
```

## Primary Keys - ULID as UUID

### Helper Function

```typescript
// File: _db/schema/index.ts
import { uuid } from "drizzle-orm/pg-core";
import { ulid, ulidToUUID } from "ulidx";
import { type StringUUID } from "../../lib/ext/typebox/index.js";

export const ULIDAsUUID = (columnName?: string) =>
  (columnName ? uuid(columnName) : uuid())
    .$default(() => ulidToUUID(ulid()))
    .$type<StringUUID>();
```

### Usage in Schema

```typescript
export const USERS = pgTable("users", {
  userId: ULIDAsUUID("user_id").primaryKey(),
  tenantId: ULIDAsUUID("tenant_id")
    .references(() => TENANTS.tenantId)
    .notNull(),
  displayName: text("display_name").notNull(),
  // ... other columns
});
```

**StringUUID type:** Should be branded/nominal string type to prevent mixing with regular strings.

## JSONB Type Safety

### Always Use $type<T>()

```typescript
import { type Sensitive } from "../../lib/functional/vault/schemas.js";

export const USERS = pgTable("users", {
  userId: ULIDAsUUID("user_id").primaryKey(),

  // GOOD: Typed JSONB with known structure
  idpUserInfo: jsonb("idp_user_info").$type<Sensitive<IdPUserInfo>>(),

  // GOOD: Typed with explicit structure
  extraAttributes: jsonb("extra_attributes")
    .$type<Record<string, unknown>>()
    .notNull()
    .$default(() => ({})),

  // GOOD: Complex nested structure
  preferences: jsonb("preferences").$type<{
    theme: "light" | "dark" | "auto";
    language: string;
    notifications: {
      email: boolean;
      push: boolean;
    };
  }>().notNull(),

  // BAD: Untyped JSONB
  metadata: jsonb("metadata"), // NO! Always use $type
});
```

### Type Definition Pattern

```typescript
// Define types separately for reusability
type UserPreferences = {
  theme: "light" | "dark" | "auto";
  language: string;
  notifications: {
    email: boolean;
    push: boolean;
  };
};

export const USERS = pgTable("users", {
  preferences: jsonb("preferences").$type<UserPreferences>().notNull(),
});
```

## Schema Patterns

### Standard Mixins

```typescript
// Timestamps mixin - use on ALL tables
export const TIMESTAMPS_MIXIN = {
  createdAt: timestamp("created_at", { withTimezone: true, mode: "date" })
    .notNull()
    .defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true, mode: "date" })
    .$onUpdateFn(() => new Date()),
};

// Apply to tables
export const USERS = pgTable("users", {
  userId: ULIDAsUUID("user_id").primaryKey(),
  displayName: text("display_name").notNull(),
  ...TIMESTAMPS_MIXIN,
});
```

### Soft Deletes

```typescript
export const POSTS = pgTable("posts", {
  postId: ULIDAsUUID("post_id").primaryKey(),
  title: text("title").notNull(),
  deletedAt: timestamp("deleted_at", { withTimezone: true, mode: "date" }),
  ...TIMESTAMPS_MIXIN,
});
```

### Indexes and Constraints

```typescript
export const USER_EMAILS = pgTable(
  "user_emails",
  {
    userId: ULIDAsUUID("user_id")
      .references(() => USERS.userId)
      .notNull(),
    email: text("email").notNull(),
    isPrimary: boolean("is_primary").notNull().default(false),
    ...TIMESTAMPS_MIXIN,
  },
  (t) => [
    {
      // Composite primary key
      pk: primaryKey({ columns: [t.userId, t.email] }),

      // Indexes following naming convention
      userIdx: index("user_emails_user_idx").on(t.userId),
      emailIdx: index("user_emails_lookup_idx").on(t.email),

      // Unique constraints
      uniqueEmail: unique("user_emails_tenant_email_unique").on(t.email),
    },
  ],
);
```

## Financial Data Types

### Use numeric() for Money

**MANDATORY: Use numeric type for all monetary values.**

```typescript
import { numeric } from "drizzle-orm/pg-core";

// GOOD: numeric with string defaults (preserves precision)
export const WALLETS = pgTable("wallets", {
  walletId: ULIDAsUUID("wallet_id").primaryKey(),
  balance: numeric("balance", { precision: 19, scale: 4 })
    .notNull()
    .default("0.0000"),  // String default - preserves precision
});

export const TRANSACTIONS = pgTable("transactions", {
  transactionId: ULIDAsUUID("transaction_id").primaryKey(),
  amount: numeric("amount", { precision: 19, scale: 4 }).notNull(),
});

// BAD: doublePrecision causes rounding errors
export const WALLETS_BAD = pgTable("wallets", {
  balance: doublePrecision("balance"), // NO! Floating point errors
});

// BAD: number defaults lose precision
balance: numeric("balance", { precision: 19, scale: 4 }).default(0)  // NO! Use string
```

**Why numeric:**
- Exact decimal arithmetic (no floating-point rounding)
- Database enforces precision
- String mode (default) prevents JS number precision loss

**Common precision/scale values:**
- `{ precision: 19, scale: 4 }` - general purpose (up to 15 integer digits, 4 decimal)
- `{ precision: 10, scale: 2 }` - most currencies (cents precision)
- `{ precision: 19, scale: 8 }` - cryptocurrency (satoshi-level)

**Note:** `decimal()` is an alias for `numeric()` - both work identically.

## Transaction Patterns

### TX_ Methods (Transaction Starters)

```typescript
class UserService {
  constructor(
    logger: Logger,
    private readonly db: Drizzle,
    private readonly dbRO: DrizzleRO,
    private readonly events: EventService,
  ) {}

  // GOOD: Starts transaction, has TX_ prefix, no executor parameter
  async TX_createUserWithProfile(
    userData: CreateUserInput,
    profileData: ProfileData,
  ): Promise<User> {
    return this.db.transaction(async (tx) => {
      // Call participant methods with tx
      const user = await this.createUser(userData, tx);
      await this.createProfile(user.id, profileData, tx);
      await this.events.dispatchEvent({
        type: "UserCreated",
        userId: user.id,
      });
      return user;
    });
  }
}
```

### Participant Methods (No TX_ Prefix)

```typescript
class UserService {
  // GOOD: Participates in transaction, takes executor with default
  async createUser(
    input: CreateUserInput,
    executor: Drizzle = this.db,
  ): Promise<User> {
    const [user] = await executor
      .insert(USERS)
      .values({
        displayName: input.name,
        email: input.email,
      })
      .returning();

    if (!user) throw new Error("Failed to create user");
    return user;
  }

  // GOOD: Read operation, uses read-only by default
  async getUserById(
    userId: string,
    executor: DrizzleRO = this.dbRO,
  ): Promise<User | null> {
    const result = await executor
      .select()
      .from(USERS)
      .where(eq(USERS.userId, userId))
      .limit(1);

    return result[0] ?? null;
  }
}
```

### Transaction Isolation Levels

**Use SERIALIZABLE isolation for financial operations:**

```typescript
// GOOD: SERIALIZABLE isolation for financial operations
async TX_deductCredits(userId: string, amount: number): Promise<Result> {
  return this.db.transaction(async (tx) => {
    // SELECT FOR UPDATE pattern (undocumented, use with caution)
    const [wallet] = await tx
      .select()
      .from(WALLETS)
      .where(eq(WALLETS.userId, userId))
      .for("update")  // Locks row for exclusive access
      .limit(1);

    if (wallet.balance < amount) {
      throw new Error("Insufficient balance");
    }

    // Deduct and update
    await tx
      .update(WALLETS)
      .set({ balance: wallet.balance - amount })
      .where(eq(WALLETS.walletId, wallet.walletId));

    return { success: true };
  }, {
    isolationLevel: "serializable"  // Prevents race conditions
  });
}
```

**Supported isolation levels:**
```typescript
interface PgTransactionConfig {
  isolationLevel?: "read uncommitted" | "read committed" | "repeatable read" | "serializable";
}
```

**When to use each:**
- **"read committed"** (default) - Most operations
- **"repeatable read"** - Need consistent snapshot across queries
- **"serializable"** - Financial operations, inventory counts (prevents all anomalies)

**Important:**
- Applications using SERIALIZABLE must implement retry logic for serialization failures
- Use connection pooling (Pool), not single Client connections

### Atomic Operations (No TX_ Prefix)

```typescript
// GOOD: Single atomic operation, no explicit transaction needed
async upsertUserPreferences(
  userId: string,
  preferences: UserPreferences,
  executor: Drizzle = this.db,
): Promise<UserPreferencesRow> {
  const [result] = await executor
    .insert(USER_PREFERENCES)
    .values({ userId, preferences })
    .onConflictDoUpdate({
      target: [USER_PREFERENCES.userId],
      set: { preferences },
    })
    .returning();

  if (!result) throw new Error("Failed to upsert preferences");
  return result;
}
```

## Migration Workflow

### Generate Migrations

```bash
# 1. Update schema in code (src/_db/schema/index.ts)

# 2. Generate migration
npm run db:generate
# or
drizzle-kit generate

# This creates: drizzle/0001_migration_name.sql
```

### Review Migration

```sql
-- drizzle/0001_add_user_preferences.sql
CREATE TABLE IF NOT EXISTS "user_preferences" (
  "user_id" uuid PRIMARY KEY NOT NULL,
  "preferences" jsonb NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone
);

CREATE INDEX IF NOT EXISTS "user_preferences_user_idx"
  ON "user_preferences" ("user_id");

ALTER TABLE "user_preferences"
  ADD CONSTRAINT "user_preferences_user_id_users_user_id_fk"
  FOREIGN KEY ("user_id") REFERENCES "users"("user_id");
```

### Apply Migration

```bash
# Development
npm run db:migrate

# Production (via CI/CD)
npm run db:migrate:prod

# NEVER use db:push in production
```

### Drizzle Config

```typescript
// drizzle.config.ts
import { defineConfig } from 'drizzle-kit';

export default defineConfig({
  dialect: 'postgresql',
  schema: './src/_db/schema/index.ts',
  out: './drizzle',
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
});
```

## Enums

```typescript
// Use pgEnum for database enums
export const USER_ROLE = pgEnum("user_role", ["admin", "user", "guest"]);

export const USERS = pgTable("users", {
  userId: ULIDAsUUID("user_id").primaryKey(),
  role: USER_ROLE("role").notNull().default("user"),
});
```

## Pattern Comments

**Add pattern classification to every file:**

```typescript
// pattern: Imperative Shell
// Orchestrates database operations and handles I/O

import { eq } from "drizzle-orm";
import { type Logger } from "pino";

export class UserService {
  // ... implementation
}
```

## Common Patterns Summary

| Pattern | Implementation |
|---------|---------------|
| Primary key | `ULIDAsUUID("column_name").primaryKey()` |
| Foreign key | `ULIDAsUUID("col").references(() => TABLE.col)` |
| JSONB typed | `jsonb("col").$type<Type>().notNull()` |
| Timestamps | `...TIMESTAMPS_MIXIN` |
| Index | `index("idx_table_col").on(t.col)` |
| Unique | `unique("uniq_table_col").on(t.col)` |
| Soft delete | `deletedAt: timestamp("deleted_at")` |
| Read method | `executor: DrizzleRO = this.dbRO` |
| Write method | `executor: Drizzle = this.db` |
| TX starter | `TX_methodName()` - no executor param |
| TX participant | `methodName(executor: Drizzle = this.db)` |
