---
name: writing-claude-directives
description: Use when writing instructions that guide Claude behavior - skills, CLAUDE.md files, agent prompts, system prompts. Covers token efficiency, compliance techniques, and discovery optimization.
---

# Writing Claude Directives

## Core Principles

**1. Claude is smart.** Only write what it doesn't already know. Challenge each line: does this justify its token cost?

**2. Positive > Negative framing.** "Don't do X" triggers thinking about X (pink elephant problem). Say what TO do, not what to avoid.

```markdown
# Bad: triggers the behavior
Don't create duplicate files

# Good: directs to correct behavior
Update existing files in place
```

**3. Context motivates compliance.** Explain WHY, not just WHAT. Claude generalizes from motivation.

```markdown
# Less effective
NEVER use ellipses

# More effective
Your response will be read aloud by a text-to-speech engine, so never use ellipses since the TTS engine cannot pronounce them.
```

**4. Placement matters.** Instructions at prompt start and end receive higher attention. Critical rules go at boundaries.

**5. ~150 instruction limit.** More instructions = uniform degradation across ALL rules. Prune ruthlessly.

**6. Repetition enforces critical rules.** For high-stakes requirements, repeat with different framings.

## Token Efficiency

**Targets:**
- Frequently-loaded directives: <200 words
- Skills/CLAUDE.md: <500 lines total
- Reference --help instead of documenting flags
- Cross-reference other skills instead of repeating

**Progressive disclosure:** Main file is overview + links. Reference files load on-demand.

## Discovery (for Skills)

The `description` field determines if Claude finds your skill.

**Format:** Start with "Use when..." + specific triggers + what it does.

**Write in third person.** Injected into system prompt.

```yaml
# Bad: vague, first person
description: I help with async testing

# Good: triggers + action, third person
description: Use when tests have race conditions or timing dependencies - replaces arbitrary timeouts with condition polling
```

**Keywords:** Include error messages, symptoms, tool names Claude might search for.

## Compliance Techniques

Claude 4.x models are highly responsive to instructions. Lead with context and motivation; reserve imperatives for critical boundaries.

### Primary: Context + Motivation

Explain WHY the rule exists. Claude generalizes from the explanation:

```markdown
# Instead of raw authority
You MUST run tests before committing.

# Provide motivation
Run tests before committing. Untested commits break CI for the whole team and block other developers from merging their work.
```

### Secondary: Structural Enforcement

Use structure to make compliance the path of least resistance:

| Pattern | Example |
|---------|---------|
| Workflow steps | Numbered steps with verification gates |
| Task tracking (TaskCreate/TaskUpdate) | Checklists without tracking = skipped steps (TodoWrite in older versions) |
| Forced commitment | "Announce: I'm using [skill]" |
| Explicit blocking | "If X happens, stop and do Y instead" |

### Escalation: Imperatives (Use Sparingly)

For Claude 4.x, aggressive language ("YOU MUST", "CRITICAL") can cause overtriggering. Use normal language first:

```markdown
# Often sufficient for 4.x
Use this tool when searching for files.

# Reserve imperatives for true boundaries
Never commit secrets to version control.
```

Close loopholes when needed, but prefer context over authority:

```markdown
# Good: context + loophole closure
Write the test first. Code written before its test tends to test the implementation rather than the behavior, making refactoring harder later. If you find yourself with untested code, delete it and start with the test.
```

### By Skill Type

| Type | Approach |
|------|----------|
| Discipline (TDD, verification) | Context + structural enforcement + loophole closure |
| Technique (patterns, how-to) | Clear steps, "we want quality" framing |
| Reference (documentation) | Clarity only, no persuasion needed |

## Structure Patterns

### XML for Directives and Format Control

Claude parses XML effectively. Use for multi-part directives:

```xml
<task>What to accomplish</task>
<constraints>Hard requirements</constraints>
<output_format>Expected structure</output_format>
<examples>Input/output pairs</examples>
```

XML also works as format indicators:

```xml
<smoothly_flowing_prose>Write report sections here</smoothly_flowing_prose>
<structured_data>JSON or tables here</structured_data>
```

XML outperforms markdown, JSON, or YAML for rule preservation in long prompts.

### Match Prompt Style to Desired Output

The formatting style in your prompt influences Claude's response. Include markdown formatting in your prompts when you want markdown output. Remove markdown from prompts if you want plain text output.

### Workflows

Break complex tasks into checkable steps:

```markdown
## Workflow
- [ ] Step 1: Analyze inputs
- [ ] Step 2: Generate plan
- [ ] Step 3: Validate plan
- [ ] Step 4: Execute
- [ ] Step 5: Verify output
```

### Feedback Loops

Validate → fix → repeat:

```markdown
1. Generate output
2. Run validator
3. If errors: fix and go to step 2
4. Only proceed when validation passes
```

### Degrees of Freedom

Match specificity to fragility:

| Task Type | Freedom | Style |
|-----------|---------|-------|
| Fragile operations | Low | Exact scripts, no modifications |
| Preferred patterns | Medium | Templates with parameters |
| Context-dependent | High | Principles and heuristics |

## Action Bias Templates

### Proactive (Default to Action)

```xml
<default_to_action>
By default, implement changes rather than only suggesting them. If the user's intent is unclear, infer the most useful likely action and proceed, using tools to discover any missing details instead of guessing. Try to infer the user's intent about whether a tool call is intended or not, and act accordingly.
</default_to_action>
```

### Conservative (Research First)

```xml
<do_not_act_before_instructions>
Do not jump into implementation or change files unless clearly instructed. When the user's intent is ambiguous, default to providing information, doing research, and providing recommendations rather than taking action. Only proceed with edits when the user explicitly requests them.
</do_not_act_before_instructions>
```

## Overengineering Prevention

Claude 4.x tends to overengineer. Include this when needed:

```markdown
Avoid over-engineering. Only make changes that are directly requested or clearly necessary. Keep solutions simple and focused.

Don't add features, refactor code, or make "improvements" beyond what was asked. A bug fix doesn't need surrounding code cleaned up. A simple feature doesn't need extra configurability.

Don't add error handling, fallbacks, or validation for scenarios that can't happen. Trust internal code and framework guarantees. Only validate at system boundaries (user input, external APIs). Don't use backwards-compatibility shims when you can just change the code.

Don't create helpers, utilities, or abstractions for one-time operations. Don't design for hypothetical future requirements. The right amount of complexity is the minimum needed for the current task. Reuse existing abstractions where possible and follow DRY.
```

## Model-Specific Notes

### Opus 4.5: "Think" Sensitivity

When extended thinking is disabled, Opus 4.5 is sensitive to the word "think" and variants. Replace with:
- "consider" instead of "think about"
- "evaluate" instead of "think through"
- "determine" instead of "think whether"

## Naming (for Skills)

**Gerund form (verb + -ing):** `writing-skills`, `testing-code`, `debugging-errors`

**Name by action or insight:** `condition-based-waiting` not `async-helpers`

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Verbose explanations | Claude knows basics - omit |
| Multiple valid approaches | Pick one default, escape hatch for edge cases |
| Vague triggers | Specific symptoms: "tests flaky", "race condition" |
| Deeply nested references | Keep one level deep from main file |
| Windows paths | Always forward slashes |
| Aggressive language for 4.x | Lead with context, reserve imperatives for boundaries |

## Anti-Rationalization

For discipline-enforcing directives, anticipate excuses:

```markdown
## Red Flags - STOP
If you find yourself reasoning any of these, you're rationalizing:
- "This is simple enough to skip"
- "I already tested manually"
- "The spirit not the letter"
- "This case is different"

All mean: Follow the process.
```

## Testing Directives

1. **Baseline:** Run scenario WITHOUT directive, document failures
2. **Apply:** Add directive, verify compliance
3. **Iterate:** Find new loopholes → add counters → re-test

## Long-Running Tasks

For multi-context-window workflows and state management across sessions, see long-running-state-patterns.md in this directory.

## Graphviz (for Process Flows)

See graphviz-conventions.dot for flowchart style guide.

**Use flowcharts for:** Non-obvious decisions, process loops, "when to use A vs B"

**Don't use for:** Reference material (use tables), linear steps (use lists)
