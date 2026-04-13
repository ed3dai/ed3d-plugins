---
name: jackal-design-plan
description: Generic design plan starter with supervisor integration. Runs the conflict gate if the issue hasn't been assigned yet, kicks off the full 6-phase design process, and at completion outputs the exact /jackal-impl-plan command. Use for Complex issues in any Jackal-managed project.
user-invocable: true
---

# Jackal Design Plan

Generic wrapper around `jackal-plan-and-execute:starting-a-design-plan` that integrates the supervisor at both ends of the design phase.

**Announce at start:** "I'm using jackal-design-plan to start design for [ISSUE-ID]."

---

## Step 0: Load Project Config

Read the **## Jackal Config** section from the project's `CLAUDE.md` (already in context when working within a project). Extract:
- `repo_root`, `issue_prefix`, `issue_docs`, `design_plans`, `git_remote`

---

## Where This Fits in the Cycle

```
Supervisor SELECT          ← supervisor assigns issue, creates worktree
      ↓
/jackal-design-plan        ← THIS SKILL
  → Gate: conflict check if supervisor hasn't assigned yet
  → /start-design-plan (6 phases — context, clarify, DoD, brainstorm, document, handoff)
  → At Phase 6: outputs /jackal-impl-plan command (pre-impl check embedded there)
      ↓
/jackal-impl-plan          ← runs pre-impl conflict check, then creates impl plan
      ↓
/execute-implementation-plan
      ↓
/jackal-ui-verify          ← if UI scope (check ui_path in Jackal Config)
      ↓
/jackal-finish-branch      ← supervisor closes out TODO.md
```

---

## Step 1: Resolve Input

Accept:
- An issue ID: `PREFIX-XXX`
- An issue doc path: `$issue_docs/PREFIX-XXX-kebab-title.md`

Find and read the issue doc:
```bash
ls $REPO_ROOT/$ISSUE_DOCS/ | grep -i "PREFIX-XXX"
```

Extract:
- **Status** — determines if supervisor already assigned
- **Complexity** — must be Complex for this skill

**If Complexity is not Complex:** Redirect:
```
PREFIX-XXX is marked [Simple/Standard] — use /jackal-impl-plan instead.
/jackal-impl-plan $ISSUE_DOCS/PREFIX-XXX-title.md
```

---

## Step 2: Supervisor Gate (skip if already assigned)

**Check if supervisor has already assigned this issue:**
```bash
grep "Status:" $REPO_ROOT/$ISSUE_DOCS/PREFIX-XXX-*.md
grep "Worktree:" $REPO_ROOT/$ISSUE_DOCS/PREFIX-XXX-*.md
```

**If Status is "In Progress" AND Worktree is filled** → skip to Step 3.

**If Status is "Ready" or Worktree is blank** → run the conflict gate now.

### Inline Conflict Gate

```bash
cd $REPO_ROOT

for branch in $(git branch --list 'feature/*' | tr -d ' '); do
  echo "=== $branch ==="
  git diff --name-only main...$branch 2>/dev/null
done
```

Extract the issue's scope directories from the **Scope / In scope** section.

**No conflict → create worktree:**
```bash
ISSUE_ID="PREFIX-XXX"
SLUG="kebab-title"       # from issue doc title
MODULE="[module-short]"  # from Module field, cross-referenced to Jackal Config module map

git worktree add .worktrees/${ISSUE_ID}-${SLUG} \
  -b feature/${MODULE}/${ISSUE_ID}-${SLUG} main

# Exclude TODO.md from worktree checkout
git -C .worktrees/${ISSUE_ID}-${SLUG} sparse-checkout set --no-cone '/*' '!TODO.md'
```

Update issue doc: Status → In Progress, fill Worktree and Branch fields.

**Conflict found → stop:**
```
⛔ Cannot start design for PREFIX-XXX — conflict with [branch].
Resolve before proceeding: wait / restructure scope / use integration branch.
```

---

## Step 3: Codebase Investigation

**REQUIRED: Dispatch subagents before asking the user anything about the codebase.**

Do NOT ask the user to describe existing patterns — investigate first.

**Dispatch codebase-investigator** with the issue doc contents as context:
> "Given that the user wants to [issue summary], investigate the current codebase to:
> - Find any existing related functionality or patterns
> - Identify the relevant file structure and conventions
> - Surface any architectural decisions already in place
> - Note constraints apparent from the existing code"

**If the issue involves external technologies** (proper nouns, service names, API names, version numbers), dispatch **combined-researcher** instead.

Carry findings into Step 4 as pre-gathered context.

---

## Step 4: Start Design Planning

**Determine the slug before invoking the sub-skill:**

```bash
grep -i "PREFIX-XXX" $REPO_ROOT/TODO.md | head -1
```

Extract the issue line title, convert to kebab-case, prefix with the issue ID:
```
ISSUE-ID-kebab-title-from-todo
# Example: HCG-123-add-user-authentication-feature
```

**REQUIRED SUB-SKILL:** `jackal-plan-and-execute:starting-a-design-plan`

Announce: "I'm using starting-a-design-plan to run the full 6-phase design process."

**Pass the following overrides in your initial instruction to the sub-skill:**

1. **Phase 1 override — context is pre-gathered. Include this text verbatim:**
   > "Phase 1 context has been pre-gathered from the issue doc and codebase investigation. Do NOT ask the user the Phase 1 freeform context question. Treat Phase 1 as complete. The pre-gathered context is: [issue doc Summary, ACs, Scope, Technical Notes, and codebase findings from Step 3]."

2. **Phase 3 slug override — slug is pre-determined. Include this text verbatim:**
   > "The design plan slug has been pre-determined as [SLUG]. When you reach the slug selection step in Phase 3, use this slug immediately without asking or offering options. Announce it and proceed directly to file creation."

**Why these slugs:**
- Issue ID prefix makes ACs traceable: `HCG-123-add-user-authn.AC1.1` → directly maps to the issue
- Title suffix makes filenames human-readable months later

**Legitimate interaction phases (do not suppress):**
- Phase 3 DoD confirmation — user must validate the Definition of Done
- Phase 4 brainstorming validation — user must approve the design approach
- Phase 5 AC validation — user must sign off on acceptance criteria

**Let all 6 phases run.** Only Phase 1 context gathering and Phase 3 slug selection are overridden.

---

## Step 5: Post-Design Handoff

After Phase 5 commits the design plan, **replace the standard Phase 6 handoff** with:

```
Design complete for PREFIX-XXX.
Design plan committed: $DESIGN_PLANS/[filename]

⚠️  Copy the command below BEFORE running /clear.

Next step — pre-implementation conflict check + implementation plan:

/jackal-impl-plan $DESIGN_PLANS/[YYYY-MM-DD-PREFIX-XXX-slug].md

This will:
1. Re-run the conflict gate against the design plan's exact file paths
2. Create the implementation plan in the existing worktree
3. Hand off to /execute-implementation-plan

Steps:
1. Copy the command above
2. /clear
3. Paste and run
```

**Why the pre-impl check runs again:** Design planning takes time. New issues may have entered Active since this design started, and the design plan names exact files the issue doc didn't.
