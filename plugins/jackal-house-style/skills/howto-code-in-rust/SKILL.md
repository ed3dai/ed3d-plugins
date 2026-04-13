---
name: howto-code-in-rust
description: Use when writing Rust code, reviewing Rust implementations, or making decisions about error handling, ownership, or async patterns - covers cargo tooling, thiserror/anyhow error handling, ownership idioms, newtype pattern, and production Rust patterns
user-invocable: false
---

# Rust House Style

## Overview

Rust coding standards for production-quality code.

**Core principles:**
- `thiserror` for library errors; `anyhow` for application errors
- Prefer borrowing (`&str`, `&[T]`) over owned types (`&String`, `&Vec<T>`) in function parameters
- Newtype pattern for domain type safety
- No `.unwrap()` in production code
- `cargo fmt` + `cargo clippy` before every commit

## Quick Self-Check (Use Under Pressure)

When under deadline pressure, STOP and verify:

- [ ] Using `thiserror` for library error types; `anyhow` for application `main`
- [ ] No `.unwrap()` in production code — using `?`, combinators, or explicit handling
- [ ] Function parameters use `&str` not `&String`; `&[T]` not `&Vec<T>`
- [ ] Ran `cargo fmt && cargo clippy` before commit
- [ ] `#[deny(unsafe_code)]` declared in `lib.rs`/`main.rs` unless intentional
- [ ] Not holding `std::sync::Mutex` across `.await` — using `tokio::sync::Mutex` or releasing first
- [ ] Domain IDs wrapped in newtypes (not raw `u64`/`String`)
- [ ] `Cargo.lock` committed for binaries; in `.gitignore` for libraries

## Tooling

### Cargo Commands

```bash
cargo new my-app               # Binary crate
cargo new --lib my-lib         # Library crate
cargo add serde --features derive  # Add dependency
cargo add --dev tokio-test     # Dev dependency
cargo fmt                      # Format (run before commit)
cargo clippy                   # Lint (run before commit)
cargo test                     # Unit + integration + doc tests
cargo test --doc               # Doc tests only
cargo build --release          # Production build
```

### Lint Configuration

In `lib.rs` or `main.rs`:

```rust
#![deny(unsafe_code)]
#![warn(missing_docs)]
#![warn(clippy::all)]
#![warn(clippy::pedantic)]
#![warn(clippy::nursery)]
#![allow(clippy::module_name_repetitions)]  // Disable per-project if noisy
```

Or workspace-wide in `Cargo.toml`:

```toml
[workspace.lints.rust]
unsafe_code = "deny"

[workspace.lints.clippy]
all = "warn"
pedantic = "warn"
nursery = "warn"
```

## Error Handling

### Rule: `thiserror` for libraries, `anyhow` for applications

**Library — `thiserror` (callers can match on variants):**

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ParseError {
    #[error("invalid input: {0}")]
    InvalidInput(String),

    #[error("io error")]
    Io(#[from] std::io::Error),  // ? auto-converts io::Error -> ParseError
}

pub fn parse(input: &str) -> Result<Config, ParseError> {
    if input.is_empty() {
        return Err(ParseError::InvalidInput("empty input".into()));
    }
    // ...
    Ok(Config::default())
}
```

**Application — `anyhow` (uniform error type, rich context):**

```rust
use anyhow::{Context, Result, bail};

fn main() -> Result<()> {
    let config = load_config("config.toml")
        .context("failed to load config")?;
    run(config)?;
    Ok(())
}

fn load_config(path: &str) -> Result<Config> {
    let content = std::fs::read_to_string(path)
        .with_context(|| format!("failed to read {path}"))?;
    toml::from_str(&content).context("invalid TOML")
}

fn validate(value: i32) -> Result<()> {
    if value < 0 {
        bail!("value must be non-negative, got {value}");
    }
    Ok(())
}
```

**Why the distinction:** Libraries expose specific error variants so callers can pattern-match. Applications just need to display and propagate errors — `anyhow` is simpler.

## Ownership Patterns

### Prefer broad input types

```rust
// ❌ Too restrictive — callers must have an owned String/Vec
fn greet(name: &String) {}
fn process(items: &Vec<Item>) {}

// ✅ Accept any string-like or slice-like value
fn greet(name: &str) {}
fn process(items: &[Item]) {}
```

### Clone only when necessary

```rust
// ❌ Takes ownership, forces caller to give up or pre-clone
fn log_config(config: Config) { println!("{config:?}"); }

// ✅ Borrow; caller keeps ownership
fn log_config(config: &Config) { println!("{config:?}"); }
```

### Builder pattern for complex construction

```rust
pub struct ClientBuilder {
    timeout: Duration,
    retries: u32,
}

impl ClientBuilder {
    pub fn timeout(mut self, d: Duration) -> Self { self.timeout = d; self }
    pub fn retries(mut self, n: u32) -> Self { self.retries = n; self }

    pub fn build(self) -> Result<Client, String> {
        Ok(Client { timeout: self.timeout, retries: self.retries })
    }
}

let client = Client::builder()
    .timeout(Duration::from_secs(30))
    .retries(3)
    .build()?;
```

## Type System Idioms

### Newtype Pattern for Domain Safety

```rust
// ❌ Compiler can't distinguish — mixing up IDs is silent
fn find_user(id: u64) -> Option<User> {}
fn find_order(id: u64) -> Option<Order> {}
// find_user(order_id)  ← compiles, wrong, runtime bug

// ✅ Distinct types; mixing up is a compile error
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct UserId(u64);

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct OrderId(u64);

fn find_user(id: UserId) -> Option<User> {}
fn find_order(id: OrderId) -> Option<Order> {}
// find_user(order_id)  ← compile error ✅
```

### Option/Result Combinators — No `.unwrap()`

```rust
let maybe: Option<i32> = Some(5);

// ❌ Panics on None
let x = maybe.unwrap();

// ✅ Provide fallback
let x = maybe.unwrap_or(0);
let x = maybe.unwrap_or_else(|| compute_default());

// ✅ Transform
let doubled = maybe.map(|v| v * 2);          // Some(10)
let filtered = maybe.filter(|v| *v > 3);    // Some(5)
let chained = maybe.and_then(validate);      // None if validate returns None

// ✅ Propagate with ?
fn process() -> Result<i32, MyError> {
    let x = might_fail()?;  // Returns Err early
    Ok(x * 2)
}
```

## Async (Tokio)

### Setup

```toml
[dependencies]
tokio = { version = "1", features = ["full"] }
```

```rust
#[tokio::main]
async fn main() -> anyhow::Result<()> {
    run().await
}
```

### Don't block the async executor

```rust
// ❌ Blocks the entire thread — starves other tasks
async fn bad() {
    std::thread::sleep(Duration::from_secs(1));
}

// ✅ Offload CPU/blocking work to thread pool
async fn good() {
    tokio::task::spawn_blocking(|| {
        std::thread::sleep(Duration::from_secs(1));
    }).await.unwrap();
}

// ✅ Use async sleep for delays
async fn delay() {
    tokio::time::sleep(Duration::from_secs(1)).await;
}
```

### Don't hold `std::sync::Mutex` across `.await`

```rust
// ❌ Lock held during await — can deadlock
async fn bad(state: Arc<Mutex<State>>) {
    let _lock = state.lock().unwrap();
    some_async_fn().await;  // Mutex still held!
}

// ✅ Drop the lock before awaiting
async fn good(state: Arc<Mutex<State>>) {
    {
        let mut lock = state.lock().unwrap();
        lock.update();
    }  // Lock released here
    some_async_fn().await;
}

// ✅ Or use tokio's async-aware Mutex
async fn also_good(state: Arc<tokio::sync::Mutex<State>>) {
    let mut lock = state.lock().await;  // Async lock — safe to hold across await
    some_async_fn().await;
}
```

## Module Organization

```rust
// lib.rs — define the public API explicitly
mod internal;          // Private implementation details
pub mod models;        // Public module

// Re-export commonly used types at crate root
pub use models::{User, Order};
pub use errors::Error;

// pub(crate) for crate-internal-only helpers
pub(crate) fn internal_helper() {}
```

**Prelude pattern for ergonomics (optional):**

```rust
// src/prelude.rs
pub use crate::models::{User, Order};
pub use crate::errors::Error;
pub use anyhow::Result;

// Consumer: use my_crate::prelude::*;
```

## Testing

```rust
// Unit tests live in the same file
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_valid() {
        assert_eq!(parse("hello"), Ok(Config::default()));
    }

    #[test]
    fn test_parse_empty_returns_error() {
        assert!(matches!(parse(""), Err(ParseError::InvalidInput(_))));
    }
}

// Integration tests in tests/
// tests/integration_test.rs
#[test]
fn test_full_flow() {
    let result = my_crate::run("input");
    assert!(result.is_ok());
}
```

Doc tests run with `cargo test --doc`:

```rust
/// Adds two numbers.
///
/// ```
/// assert_eq!(my_crate::add(2, 3), 5);
/// ```
pub fn add(a: i32, b: i32) -> i32 { a + b }
```

## Common Mistakes

| Mistake | Reality | Fix |
|---------|---------|-----|
| `.unwrap()` in production | Panics on unexpected data in prod | Use `?`, combinators, or match explicitly |
| `&String` / `&Vec<T>` parameters | Forces callers to have owned types unnecessarily | Use `&str` / `&[T]` |
| `anyhow` in a library's public API | Callers can't match on error variants | Use `thiserror` for library errors |
| Cloning to avoid borrow issues | Hides design problems; wastes allocation | Restructure ownership or use references |
| `std::sync::Mutex` across `.await` | Deadlock under async executor | Release before `.await` or use `tokio::sync::Mutex` |
| Raw `u64`/`String` as domain IDs | Compiler can't distinguish them | Newtype pattern |
| No clippy in CI | Style drift, easy bugs accumulate | `cargo clippy -- -D warnings` in CI |

## Red Flags

**Stop and fix when you see:**

- `.unwrap()` or `.expect()` outside `#[cfg(test)]` code
- `&String` or `&Vec<T>` as function parameters
- `anyhow::Error` in a library crate's public `Result` return type
- `std::sync::Mutex` guard held across an `.await`
- `unsafe` block without a `// SAFETY:` comment explaining soundness
- Raw primitive types used as domain IDs (no newtype wrapping)
- No `cargo clippy` step in CI
