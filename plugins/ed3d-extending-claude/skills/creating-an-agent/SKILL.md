---
name: creating-an-agent
description: Use when creating specialized subagents for Claude Code plugins or the Task tool - covers description writing for auto-delegation, tool selection, prompt structure, and testing agents
---

# Creating an Agent

**REQUIRED BACKGROUND:** Read ed3d-extending-claude:writing-claude-directives for foundational guidance on token efficiency, compliance techniques, and directive structure. This skill focuses on agent-specific patterns.

## What is an Agent?

An **agent** is a specialized Claude instance with:
- Defined tools (Read, Edit, Bash, etc.)
- Specific responsibilities (code review, security audit, research)
- A focused system prompt

Agents are spawned via the Task tool or defined in plugin `agents/` directories.

## When to Create an Agent

**Create when:**
- Task requires specialized expertise
- Workflow benefits from tool restrictions
- You want consistent behavior across invocations
- Task is complex enough to warrant context isolation

**Don't create for:**
- Simple, one-off tasks
- Tasks the main Claude handles well
- Purely conversational interactions

## Agent File Structure

```
agents/
  my-agent.md
```

**Template:**
```markdown
---
name: agent-name
description: Use when [specific triggers] - [what agent does]
tools: Read, Grep, Glob, Bash
model: sonnet
---

# Agent Name

[Agent system prompt - who they are, what they do]

## Responsibilities
- Task 1
- Task 2

## Workflow
1. Step 1
2. Step 2
```

## Description: The Critical Field

The `description` field determines when Claude auto-delegates to your agent. It's searched when matching tasks to available agents.

### Writing Effective Descriptions

**Format:** "Use when [specific triggers/symptoms] - [what the agent does]"

**Write in third person.** Injected into system prompt.

```yaml
# Bad: vague, no triggers
description: Helps with code

# Bad: first person
description: I review code for security issues

# Good: specific triggers + action
description: Use when reviewing code for security vulnerabilities, analyzing authentication flows, or checking for common security anti-patterns like SQL injection, XSS, or insecure dependencies
```

**Include:**
- Specific symptoms that trigger use
- Domain keywords (security, performance, testing)
- File types or patterns if relevant
- Actions the agent performs

**Length:** Max 1024 characters. Be specific, not verbose.

## Tool Selection

Choose tools based on agent responsibilities:

| Tool | When to Include |
|------|-----------------|
| Read | Reading files, analyzing code |
| Grep | Searching code patterns |
| Glob | Finding files by pattern |
| Edit | Modifying existing files |
| Write | Creating new files |
| Bash | Running commands, git, tests |
| TaskCreate/TaskUpdate | Tracking multi-step workflows (TodoWrite in older versions) |
| Task | Spawning sub-agents |
| WebFetch/WebSearch | Research tasks |

**Principle:** Include only what the agent needs. Fewer tools = more focused behavior.

**Example restrictions:**
- Code reviewer: `Read, Grep, Glob` (no write access)
- Implementor: `Read, Edit, Write, Bash, Grep, Glob`
- Researcher: `Read, WebFetch, WebSearch, Glob`

## Agent Prompt Structure

### Role Definition

Start with who the agent is:
```markdown
You are a security expert specializing in web application security and secure coding practices.
```

### Responsibilities

Explicit, numbered list:
```markdown
## Your Responsibilities

1. Identify security vulnerabilities
2. Review authentication logic
3. Check for insecure dependencies
4. Report findings with severity ratings
```

### Workflow

Step-by-step process:
```markdown
## Workflow

1. **Scan:** Use Grep to find common vulnerability patterns
2. **Analyze:** Use Read to examine flagged files
3. **Verify:** Use Bash to run security audit tools
4. **Report:** Provide structured findings
```

### Output Format

Define expected structure:
```markdown
## Reporting Format

For each finding:
- **Severity:** Critical/High/Medium/Low
- **Location:** `file:line`
- **Issue:** What's vulnerable
- **Impact:** What attacker could do
- **Fix:** How to remediate
```

### Constraints

What the agent should NOT do:
```markdown
## Constraints

- Report findings only; do not modify code
- Ask for clarification if scope is unclear
- Escalate to human for ambiguous security decisions
```

## Model Selection

| Model | Use For |
|-------|---------|
| haiku | Simple tasks, fast iteration, high volume |
| sonnet | Balanced capability/cost, most tasks |
| opus | Complex reasoning, critical decisions, code review |

Specify in frontmatter:
```yaml
model: opus
```

## Testing Agents

### 1. Baseline Test

Run the task WITHOUT the agent. Document:
- What went wrong
- What was missing
- How long it took

### 2. Agent Test

Run with agent. Verify:
- Agent is auto-delegated (description triggers correctly)
- Workflow is followed
- Output matches expected format
- Tool restrictions are respected

### 3. Edge Case Testing

Test with:
- Ambiguous inputs
- Missing context
- Large/complex inputs
- Tasks outside scope (should refuse gracefully)

### 4. Iteration

If agent fails:
1. Identify root cause (description? workflow? constraints?)
2. Update agent definition
3. Re-test

## Common Patterns

### Code Reviewer

```markdown
---
name: code-reviewer
description: Use when reviewing code changes, pull requests, or verifying implementation quality - analyzes for bugs, style issues, and best practices
tools: Read, Grep, Glob, Bash
model: opus
---

# Code Reviewer

You are a senior engineer reviewing code for correctness, readability, and maintainability.

## Responsibilities
1. Identify bugs and edge cases
2. Check error handling
3. Verify naming and style consistency
4. Suggest improvements

## Workflow
1. Read the changed files
2. Analyze for issues
3. Provide structured feedback

## Output Format
For each issue:
- **File:Line:** location
- **Severity:** Critical/Major/Minor
- **Issue:** description
- **Suggestion:** how to fix
```

### Research Agent

```markdown
---
name: researcher
description: Use when gathering information from the web, investigating APIs, or synthesizing documentation from multiple sources
tools: Read, WebFetch, WebSearch, Glob
model: sonnet
---

# Research Agent

You are a research specialist gathering and synthesizing information.

## Responsibilities
1. Search for relevant sources
2. Extract key information
3. Synthesize findings
4. Cite sources

## Workflow
1. WebSearch for relevant sources
2. WebFetch promising results
3. Extract and organize findings
4. Return structured synthesis with citations
```

### Implementor Agent

```markdown
---
name: task-implementor
description: Use when implementing specific tasks from plans - writes code, runs tests, commits changes following TDD workflow
tools: Read, Edit, Write, Bash, Grep, Glob, TaskCreate, TaskUpdate, TaskList
model: sonnet
---

# Task Implementor

You implement tasks following TDD principles.

## Responsibilities
1. Write failing test first
2. Implement minimal code to pass
3. Refactor if needed
4. Commit with descriptive message

## Constraints
- Never write implementation before test
- Run tests after each change
- Commit atomic, working changes only
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Vague description | Include specific triggers and symptoms |
| Too many tools | Restrict to what's needed |
| No workflow | Add step-by-step process |
| No output format | Define expected structure |
| First-person description | Write in third person |
| Overly broad scope | Narrow to specific responsibility |
| No testing | Test auto-delegation and output quality |

## Checklist

- [ ] Description starts with "Use when...", third person
- [ ] Description includes specific triggers/symptoms
- [ ] Tools restricted to necessary set
- [ ] Model appropriate for task complexity
- [ ] Responsibilities clearly listed
- [ ] Workflow is step-by-step
- [ ] Output format defined
- [ ] Constraints/limitations stated
- [ ] Tested for auto-delegation
- [ ] Tested for output quality
