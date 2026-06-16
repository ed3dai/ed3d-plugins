# Harness Coherence — Test & Dependency-Trace Plan

**Date:** 2026-06-16
**Design plan:** `docs/design-plans/2026-06-16-harness-coherence-and-roar-alignment.md`
**Branch:** `feat/harness-coherence`

Verifies that the harness "everything resolves" claim is a checked fact: no
dangling skill/agent references, a fully-resolving lifecycle, external deps
declared, and a configurable label scheme. The trace is re-runnable as a
pre-release gate (`scripts/trace-deps.sh`) and after any upstream sync.

---

## 1. Static dependency trace (automated)

Run:

```bash
./scripts/trace-deps.sh
```

The script builds the shipped inventory (every `plugins/*/agents/*.md` and
`plugins/*/skills/*/SKILL.md`), reads the declared external deps from
`marketplace.json` `requires`, scans every plugin markdown for `subagent_type`
tags and plugin-qualified `plugin:name` references, and classifies each as
**SHIPPED**, **DECLARED**, or **DANGLING**.

**Gate:** exit 0 iff zero DANGLING. Latest run (2026-06-16):

| Reference | Status |
|-----------|--------|
| ed3d-extending-claude:project-claude-librarian | DECLARED (ed3d-extending-claude) |
| ed3d-playwright:playwright-explorer | DECLARED (ed3d-playwright) |
| ed3d-research-agents:codebase-investigator | DECLARED (ed3d-research-agents) |
| ed3d-research-agents:combined-researcher | DECLARED (ed3d-research-agents) |
| ed3d-research-agents:internet-researcher | DECLARED (ed3d-research-agents) |
| jackal-house-style:coding-effectively | SHIPPED |
| jackal-house-style:howto-code-in-typescript | SHIPPED |
| jackal-plan-and-execute:design | SHIPPED |
| jackal-plan-and-execute:execute | SHIPPED |
| jackal-plan-and-execute:finish | SHIPPED |
| jackal-plan-and-execute:implementor | SHIPPED |
| jackal-plan-and-execute:plan | SHIPPED |
| jackal-plan-and-execute:planner | SHIPPED |
| jackal-plan-and-execute:reviewer | SHIPPED |
| jackal-plan-and-execute:test-driven-development | SHIPPED |
| jackal-plan-and-execute:verification-before-completion | SHIPPED |
| jackal-supervisor:jackal-finish-branch | SHIPPED |

**Result:** `shipped=12  declared=5  dangling=0` → **PASS**.

Compared to the pre-fix state (per the design-plan audit), this closes:
- `jackal-plan-and-execute:test-driven-development` / `:verification-before-completion`
  — were DANGLING (debug skill required them); now SHIPPED (ported in P2).
- the 5 ed3d agent refs — were undeclared external deps; now DECLARED (P3).

---

## 2. Lifecycle simulation (dry trace)

Walk a sample issue through each pipeline and confirm every dispatched
skill/agent exists (SHIPPED) or is a DECLARED dep. Cross-checked against §1.

### Complex issue: design → plan → execute → finish

| Step | Invokes | Resolves to | Status |
|------|---------|-------------|--------|
| `/jackal-design-plan` | `jackal-supervisor:jackal-design-plan` skill | supervisor skill | SHIPPED |
| ↳ research | `ed3d-research-agents:codebase-investigator` / `combined-researcher` | ed3d dep | DECLARED |
| ↳ design doc | `jackal-plan-and-execute:design` skill | core skill | SHIPPED |
| `/jackal-impl-plan` | `jackal-supervisor:jackal-impl-plan` → `jackal-plan-and-execute:plan` | supervisor + core | SHIPPED |
| ↳ phase files | `jackal-plan-and-execute:planner` agent | core agent | SHIPPED |
| `/execute` | `jackal-plan-and-execute:execute` skill | core skill | SHIPPED |
| ↳ implement | `jackal-plan-and-execute:implementor` agent | core agent | SHIPPED |
| ↳ review | `jackal-plan-and-execute:review` → `:reviewer` agent | core skill + agent | SHIPPED |
| ↳ on failure | `jackal-plan-and-execute:debug` (+ TDD / verification sub-skills) | core skills | SHIPPED |
| `/jackal-finish-branch` | `jackal-supervisor:jackal-finish-branch` → `jackal-plan-and-execute:finish` | supervisor + core | SHIPPED |
| ↳ UI gate (if UI touched) | `jackal-supervisor:jackal-ui-verify` → `ed3d-playwright:playwright-explorer` | supervisor + ed3d dep | SHIPPED + DECLARED |
| ↳ doc closeout | `ed3d-extending-claude:project-claude-librarian` | ed3d dep | DECLARED |

### Standard issue: plan → execute → finish
Same as above minus the design step. The planner generates a mini design inline.
All steps SHIPPED/DECLARED.

### Simple issue: implementor direct
`jackal-supervisor` dispatches `jackal-plan-and-execute:implementor` directly,
then `/jackal-finish-branch`. All SHIPPED.

**Result:** every lifecycle step resolves. No dead dispatch.

---

## 3. Declared-dependency absence test

Confirms the harness fails **loudly**, not silently, when a declared dep is
missing (design-plan F12). Manual check, since it depends on which plugins are
installed:

| Missing dep | Expected behavior | Where enforced |
|-------------|-------------------|----------------|
| `ed3d-extending-claude` | `finish` step 5 emits a visible ⚠️ warning that CLAUDE.md freshness re-verification was skipped, naming the missing plugin and telling the user to update docs manually. | `jackal-plan-and-execute/skills/finish/SKILL.md` step 5 |
| `ed3d-research-agents` | design/plan research dispatch fails; the `requires` declaration + README "Required dependencies" tell the user to install it. | marketplace.json `requires`, README |
| `ed3d-playwright` | `jackal-ui-verify` can't dispatch `playwright-explorer`; declared in `requires` for `jackal-supervisor`. | marketplace.json `requires` |

**Result:** no declared dep is silently skipped — finish's warning is the
explicit guard; the rest are surfaced via `requires` + README.

---

## 4. Label-scheme resolution check (F15)

The harness defaults to slash-style labels (`status/ready`) and exposes
`label_style: slash|colon` in Jackal Config. Verify against a target repo's real
labels:

```bash
# default (slash) — matches ROAR:
gh label list --repo HCG-EDR-C-ROAR/roar | grep -E 'status/(ready|in-progress|paused|blocked)'
```

Confirm every status/complexity label the skills reference exists in the target
repo. ROAR uses slash labels, so the default scheme resolves with no config.
A colon-style project sets `label_style: colon` and the same labels resolve with
`:`.

**Pre-fix state:** skills hard-coded `status:ready` (colon), which would miss
against ROAR's `status/ready`. Now configurable, default slash. **PASS.**

---

## 5. Hierarchical `.jackal/` resolution (F16)

`design`/`plan`/`execute`/`jackal-ui-verify` resolve `.jackal/harness-guidance.md`
by walking up from the working directory to repo root (nearest-wins). Verify:

- Single-package repo with only a root `.jackal/` → reads the root file (unchanged
  behavior).
- Monorepo with `packages/modules/x/.jackal/harness-guidance.md` → a dispatch with
  working dir inside that module reads both, module overriding root key-by-key.

Canonical resolution snippet lives in `jackal-plan-and-execute:execute`; the other
skills reference it. **Behavioral spec verified by reading; live monorepo test
deferred until a consumer adopts module-level guidance.**

---

## Re-run policy

Run `./scripts/trace-deps.sh` before any marketplace version bump and after every
`git rebase ed3d-upstream/main`. A non-zero exit means a reference broke — fix
before release.
