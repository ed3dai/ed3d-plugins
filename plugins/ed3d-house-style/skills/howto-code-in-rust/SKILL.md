---
name: howto-code-in-rust
description: Use when writing, reviewing, or modifying Rust code - covers error handling with thiserror+miette, type system patterns, async and serde conventions, testing crates, dependency pinning, and module organization
---

# Writing Rust

## Overview

Rust house style. Applies whenever writing, reviewing, or modifying Rust code.

The two governing values: correctness over convenience, and pragmatic incrementalism. Use the type system aggressively to make invalid states unrepresentable, then evolve the design as patterns repeat rather than building speculative abstractions.

## Correctness over convenience

- Model the full error space. No shortcuts or simplified error handling.
- Handle all edge cases: race conditions, signal timing, platform differences.
- Use the type system to encode correctness constraints (newtypes, exhaustive matching, `#[must_use]`).
- Prefer compile-time guarantees over runtime checks where possible.
- When uncertain, explore and iterate rather than assume.

## User-facing error quality

Standard pairing: `thiserror` for structured error enums, `miette` for user-facing diagnostics with source spans, help text, and related errors. They are complementary -- `thiserror` defines the shape, `miette` adds the diagnostic layer on top.

```rust
#[derive(Debug, thiserror::Error, miette::Diagnostic)]
enum ConfigError {
    #[error("failed to parse config at {path}")]
    #[diagnostic(help("check that the file is valid TOML"))]
    Parse { path: String, #[source] source: toml::de::Error },
}
```

Rules:

- Group errors by category with an `ErrorKind` enum when a single error type covers many failure modes.
- Two-tier error model: user-facing errors get semantic exit codes and rich diagnostics; internal errors (programming bugs) may panic or use internal error types.
- Error display messages are lowercase sentence fragments suitable for composing as "failed to {message}".
- Cross-platform consistency. Use OS-native logic rather than emulating Unix on Windows or vice versa.
- User-facing messages in clear, present tense.
- **Never silently drop unsupported content.** When translating or adapting data between formats, return `Err` for content the target format cannot represent. Silent data loss is a correctness bug. If a caller wants to ignore unsupported content, they can explicitly choose to -- but the library must surface the problem.

## Type system patterns

Encode invariants in types:

- **Newtypes** for domain types. Wrap primitive types to prevent misuse: `struct UserId(u64)` instead of bare `u64`.
- **Builder patterns** for complex construction with many optional parameters.
- **Type states** encoded in generics when state transitions matter and invalid states should be unrepresentable.
- **Lifetimes** to avoid unnecessary cloning. Prefer borrows when data has a natural tree structure.
- **Restricted visibility.** Use `pub(crate)` and `pub(super)` liberally. Default to the narrowest visibility that works.
- **`#[non_exhaustive]`** on public types in library crates that have stable APIs. Allows adding variants or fields without a breaking change. Internal crates do not need it.

For concurrent code, use message passing or the actor model to avoid data races rather than shared mutable state behind locks.

## Pragmatic incrementalism

- Prefer specific, composable logic over abstract frameworks. Do not be overly generic.
- Document non-obvious design decisions and trade-offs in code or commit messages.
- Do not build for hypothetical future requirements. Rule of three: do not abstract until you have seen the pattern three times.

## Research before guessing

When you encounter an unfamiliar crate, an unclear API, or a build problem you cannot immediately diagnose, use research agents rather than iterating by trial and error. Speculative iteration wastes build cycles and context.

- `ed3d-research-agents:internet-researcher` for crate documentation, API behavior, and ecosystem conventions.
- `ed3d-research-agents:remote-code-researcher` for examining external repositories for patterns and reference implementations.

These run in isolated context and return summaries, so they do not pollute working context.

## Testing

- Test comprehensively, including edge cases, race conditions, and platform differences.
- Reuse existing test facilities. Before writing new test helpers, check whether the codebase already has what you need.
- Unit tests belong in the same file as the code they test, inside a `#[cfg(test)] mod tests` block.
- Integration tests and fixtures go in `tests/` at the crate root, not mixed with production sources.

### Never skip tests

Tests must never silently skip. If a test requires an environment variable, API key, fixture file, or any other external input, it must **fail with a clear error message** when that input is unavailable. Never use patterns like `let Some(...) = ... else { return }` or `#[ignore]` or early-return guards that turn a missing dependency into a silent pass. A green test suite must mean every test actually ran and verified something. If a test cannot run, it must be red, not invisible.

### Preferred testing crates

| Crate | Purpose |
|-------|---------|
| `test-case` | Parameterized tests. Annotate a single function with multiple input/output cases. |
| `proptest` | Property-based testing. Generates random inputs to find edge cases you would not write by hand. |
| `insta` | Snapshot testing. Captures complex output and diffs against stored snapshots. |
| `pretty_assertions` | Better assertion output. Colored diffs instead of raw `Debug` output on failure. |

## Serde patterns

- Use `serde_ignored` to detect unused or typo'd fields in configuration deserialization.
- Never use `#[serde(flatten)]`. The internal buffering breaks `serde_ignored` warnings, silently swallowing typos in config files.
- Never use `#[serde(untagged)]` for deserializers. It produces useless error messages like "data did not match any variant." Write custom visitors with an appropriate `expecting` method instead.

## Serialization format changes

When modifying any struct that is serialized to disk or over the wire, trace the full version matrix:

| Scenario | Question |
|----------|----------|
| Old reader + new data | Can it deserialize? Does it lose information? |
| New reader + old data | Does `#[serde(default)]` produce correct values? |
| Old writer + new data | Can it round-trip without data loss? |

The third case is easy to miss. `#[serde(default)]` allows old readers to deserialize new data, but old writers will still drop unknown fields on write-back, silently corrupting data.

Bump format versions proactively. If adding a field that will be semantically important, bump the version when adding the field, not when first using non-default values. This prevents older versions from silently corrupting data on write-back.

## Configuration and environment

Library crates must never read environment variables. All configuration -- API keys, base URLs, auth modes, feature flags -- must be accepted as parameters (in structs, function arguments, or builder methods). Environment variable reading belongs exclusively to application entry points (`main.rs`, CLI argument parsing, or dedicated configuration loaders). This keeps libraries testable without environment manipulation and prevents hidden coupling to deployment details.

## Async patterns

Be selective with async. Use it for I/O and concurrency; keep all other code synchronous. Async infecting non-I/O code makes testing harder and adds complexity for no benefit.

- **Runtime:** Tokio (multi-threaded). The only production-grade choice.
- **Async traits:** Use native `async fn` in traits directly. The `async_trait` macro is no longer needed on Rust 1.85+.
- **Structured concurrency:** Use `tokio::task::JoinSet` for concurrent task groups that need to be awaited together.
- **Backpressure:** Use bounded `mpsc` channels. Unbounded channels hide backpressure problems.
- **Sync/async boundary:** Isolate async to specific modules. Use `block_on` at application entry points. Do not try to make a single library support both sync and async APIs.

## Lints and formatting

- Enable `clippy::format_push_string`. It catches `push_str(&format!(...))` which allocates unnecessarily. Use the `write!` macro instead.
- Use `#[expect(...)]` instead of `#[allow(...)]` for suppressing lints. `expect` warns when the suppression is no longer needed, preventing stale suppressions from accumulating.

## Memory and performance

- Use `Arc` or borrows for shared immutable data. Avoid cloning when code has a natural tree structure.
- Stream data with iterators where possible rather than buffering into collections.

## Module organization

- Use `mod.rs` files for re-exports only. Put all nontrivial logic in `imp.rs` or a more specific submodule.
- Platform-specific code goes in separate files: `unix.rs`, `windows.rs`. Use `#[cfg(unix)]` and `#[cfg(windows)]` for conditional compilation.
- Import all types and functions at the top of the module. The one exception is `cfg()`-gated imports, which may appear inline.
- Prefer module-level imports over fully qualified paths. Write `use std::fmt` and then `fmt::Display`, not `std::fmt::Display`.
- Importing enum variants for pattern matching is fine.
- Test helpers go in dedicated modules or files, not mixed with production code.

## Documentation and style

- Inline comments explain "why," not "what." Do not add narrative comments in function bodies. Only comment when something is non-obvious or needs a deeper "why" explanation.
- Module-level documentation (`//!`) should explain purpose and responsibilities.
- Periods at the end of code comments.
- Sentence case in headings, never title case.
- Oxford comma. Do not omit articles ("a", "an", "the").

## Dependencies

Pinning strategy depends on what you are building.

**Applications, binaries, and internal/workspace crates: pin exactly.** Cargo's default caret behavior (`serde = "1.0"` resolves to anything `>=1.0.0, <2.0.0`) lets dependency resolution shift between `cargo update` runs. For reproducibility and reviewable bumps, pin exactly:

```toml
[dependencies]
serde = "=1.0.219"
tokio = { version = "=1.43.0", features = ["full"] }
```

**Libraries published to crates.io: use the narrowest range that works.** Exact pins in a published library break diamond-dependency unification for downstream consumers -- if `crate-a` pins `=1.0.219` and `crate-b` pins `=1.0.220`, a consumer depending on both gets two copies of the dependency or a hard resolution failure. Publish caret ranges (or tighter, e.g., `>=1.0.219, <1.1`) and let downstream `Cargo.lock` files do the pinning.

Other dependency rules:

- **Verify latest versions before adding or bumping.** Use `ed3d-research-agents:internet-researcher` to look up the current version on crates.io. Memorized versions go stale quickly.
- Comment on non-obvious dependency choices: `# disable punycode parsing since we only access well-known domains.`
- For workspaces, manage shared versions in the root `Cargo.toml` `[workspace.dependencies]` table and reference with `{ workspace = true }` in member crates.
