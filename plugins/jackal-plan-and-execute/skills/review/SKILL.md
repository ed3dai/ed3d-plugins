---
name: review
description: Dispatches the reviewer agent and manages the fix loop. Handles retries, context limits, and escalation.
user-invocable: false
---

# Review

Dispatch the right reviewer agent and handle the result.

## Choose the Tier

- **`reviewer`** (Sonnet) — default: Simple and Standard issues, per-phase reviews. Per-phase
  reviews re-run only the touched-area tests plus verify the implementor's per-phase artifact —
  they do not re-run the full suite.
- **`reviewer-deep`** (Opus) — final review of Complex issues, or any diff
  touching auth, payments, user data, crypto, or the project's contract
  sources (the contracts package, or per-component contract files named in
  `docs/canon/registry.md`). The one full independent suite run is reserved for this tier's
  final/deep review.

## Dispatch

```xml
<invoke name="Agent">
<parameter name="subagent_type">jackal-plan-and-execute:reviewer</parameter>
<parameter name="model">sonnet</parameter>
<parameter name="description">Reviewing [what]</parameter>
<parameter name="prompt">
WHAT_WAS_IMPLEMENTED: [summary]
PLAN_OR_REQUIREMENTS: [path to phase file or issue doc]
BASE_SHA: [commit before work]
HEAD_SHA: [current commit]
Working directory: [path]

[If the plan dir has a test-requirements.md:]
TEST_REQUIREMENTS: [path to <plan-dir>/test-requirements.md]

[If implementation guidance exists:]
GUIDANCE: [path to .jackal/implementation-guidance.md]

[If the diff touches UI files:]
UI_PHASES: [phase numbers, with each phase's Reference: image path if the phase file links one] —
verify each phase report's visual-gate outcome (see reviewer's "Visual-gate verification").

Do not dispatch or invoke any subagents — run all verification directly with your own tools.

You are read-only: never mutate the working tree under review. No Edit/Write/NotebookEdit, no
writing over a tracked file from Bash (`cp`/`mv`/`>`/`sed -i`/`patch`/`rm`), no `git stash` /
`checkout` / `reset` / `apply` / `commit`. Running tests, builds, and read-only git is expected;
if verification needs code changed, copy into a scratch dir under `/tmp` and experiment there.
</parameter>
</invoke>
```

(When the tier calls for the deep reviewer, substitute **both** `subagent_type` → `jackal-plan-and-execute:reviewer-deep` **and** `model` → `opus`. The two must always move together — a `reviewer-deep` dispatch left on `model: sonnet` is a model-tier defect.)

Every Agent dispatch above carries an explicit `<parameter name="model">`; a
model-unspecified dispatch is a defect (see the Model Tier Table in the
`execute` skill and the `jackal-supervisor` agent).

## Handle Response

### PASS (no Critical/Important issues)
Proceed. Note any Minor issues in your report but don't act on them.

### ISSUES_FOUND (Critical or Important)
1. Dispatch `implementor` with the issues list:
   ```
   Fix these review issues:
   [paste issues verbatim]

   Working directory: [path]
   Fix all Critical and Important issues. Verify with tests. Commit.
   Do not dispatch or invoke any subagents — do the work directly with your own tools.
   ```
2. After fix, re-dispatch reviewer with PRIOR_ISSUES added to prompt
3. If same issues persist after 3 cycles → stop, report to human

### BLOCKED (tests fail / build broken)
The implementor left broken code. Dispatch implementor to fix:
```
Tests/build are failing. Fix before we can review.
Error output: [paste]
Working directory: [path]
```

## Context Limit Handling

If reviewer returns empty or truncated response:
1. First retry: narrow scope to changed files only
2. Second retry: split review into two halves (first N/2 commits, then remaining)
3. Third failure: stop, report to human

## When to Skip Review

The `execute` skill decides whether to invoke this skill. This skill itself always runs a full review when called — it doesn't make skip decisions.
