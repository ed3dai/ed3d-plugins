---
name: investigating-a-codebase
description: Searches files by name and content, reads directory structures, traces imports and dependencies, and maps code patterns across a repository. Use when asked to explore a codebase, find where something is defined, check if a file or function exists, verify design assumptions about project structure, or map out how components connect before implementation.
user-invocable: false
---

# Investigating a Codebase

## When to Use

- "Where is user authentication implemented?"
- "Does a rate-limiting middleware already exist?"
- "How do we currently handle API errors?"
- "Verify that the design's assumed file paths are correct"
- "What patterns do existing service modules follow?"

Do NOT use for: external docs lookups, reading a single known file, or general programming questions.

## Core Workflow

1. **Orient** - Read entry points (package.json, main/index files, config) to understand project shape
2. **Search broadly** - Run parallel Glob + Grep to locate candidates
3. **Read and trace** - Read matched files, follow imports and references
4. **Cross-verify** - Confirm findings from multiple angles; never trust a single hit
5. **Report with evidence** - Exact paths and line numbers, or "not found" with search log

## Search Strategies with Examples

### Locating files by name
```
Glob: src/**/auth*.{ts,js,tsx}
Glob: **/middleware/**/*.{ts,js}
Glob: **/*config*.{json,yaml,yml,toml}
```

### Finding definitions and usages
```
Grep: 'export (function|class|const) UserService' --type ts
Grep: 'import.*from.*auth' --type ts
Grep: 'rate.?limit' -i --glob '*.{ts,js}'
```

### Mapping project structure
```
Bash: ls -la src/
Bash: ls -la src/services/
Read: package.json (check dependencies, scripts, entry points)
Read: tsconfig.json / webpack.config.js (check aliases, paths)
```

### Tracing component relationships
1. Find the definition: `Grep: 'export.*PaymentService'`
2. Find all consumers: `Grep: 'import.*PaymentService'`
3. Read both sides to understand the contract

## Verifying Design Assumptions

When a design document claims specific files, functions, or structures exist:

1. **List each assumption** explicitly (file path, function name, pattern)
2. **Search for each** using Glob + Grep
3. **Report per assumption**:
   - Confirmed: `auth.ts:42 exports login()` -- matches design
   - Discrepancy: design says `auth.ts`, actual location is `auth/index.ts`
   - Missing: `resetPassword()` not found anywhere (searched: `Grep: 'resetPassword' --type ts`)
   - Unexpected: found `logout()` at `auth/index.ts:58` not mentioned in design

## Reporting Format

**Lead with the direct answer**, then supporting evidence:

```
## Finding: Authentication is in src/auth/

- Entry point: src/auth/index.ts (exports login, logout, refreshToken)
- JWT handling: src/auth/jwt.ts:15-42
- Middleware: src/middleware/requireAuth.ts
- Tests: src/auth/__tests__/login.test.ts
- Pattern: all auth functions return Promise<AuthResult>

Search strategy: Glob src/**/auth* (4 hits), Grep 'export.*login' (1 hit)
```

**For "not found" results**, always document what was searched:

```
## Finding: No rate-limiting middleware exists

Searched: Glob **/*rate*limit* (0 hits), Grep 'rate.?limit' (0 hits),
Grep 'throttle' (0 hits), Read src/middleware/ directory listing (no candidates).
Closest related: src/middleware/requireAuth.ts (auth only, no rate logic).
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Assuming file locations without checking | Always Glob/Grep before reporting a path |
| Stopping at first search result | Cross-reference with at least one other search |
| Reporting vague locations ("in the auth folder") | Use exact paths with line numbers: `src/auth/index.ts:42` |
| Saying "not found" without search log | List every Glob/Grep query attempted |
| Treating "couldn't locate" as "doesn't exist" | Try alternate names, abbreviations, related terms before concluding |
