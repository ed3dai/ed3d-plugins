---
name: review
description: Dispatches the reviewer agent and manages the fix loop. Handles retries, context limits, and escalation.
user-invocable: false
---

# Review

Dispatch the `reviewer` agent and handle the result.

## Dispatch

```xml
<invoke name="Agent">
<parameter name="subagent_type">jackal-plan-and-execute:reviewer</parameter>
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
GUIDANCE: [path to .jackal/implementation-guidance.md or .ed3d/implementation-plan-guidance.md]
</parameter>
</invoke>
```

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
