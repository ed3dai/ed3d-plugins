---
name: doing-a-simple-two-stage-fanout
description: Use when analyzing a large corpus of text, code, or data that exceeds a single agent's effective context - orchestrates parallel Worker subagents, Critic review subagents, and a final Summarizer subagent with task tracking and failure recovery
user-invocable: true
---

# Two-Stage Fan-Out Analysis

Divide a corpus across Worker subagents, review with Critic subagents, synthesize with a Summarizer. Every stage writes to files; every subagent gets its own task.

## Overview

```
Corpus → [Workers] → [Critics] → Summarizer → Report
```

**Workers** each analyze a slice of the corpus. **Critics** each review all Worker reports for a subset of segments, checking for gaps and inconsistencies. A single **Summarizer** reads all Critic reports and produces the final output.

## Step 0: Gather Inputs

If the user's intent is not already clear, ask two questions using AskUserQuestion:

**Question 1: What to analyze.** Ask what corpus to analyze and what the analysis goal is. Skip if obvious from context.

**Question 2: Effort level.** Present these options in this order (do not reorder to put recommended first):

| Level | SEGMENTS_PER | REVIEWS_PER | When to use |
|-------|-------------|-------------|-------------|
| Some effort | 3 | 2 | Default for most analyses |
| A lot of effort | 3 | 3 | When thoroughness matters more than speed |
| Herculean effort | 2 | 3 | When you cannot afford to miss anything |

Recommend one if you have enough context, by appending "(Recommended)" to that option's label. But keep the options in the order shown above regardless.

**Definitions:**
- `SEGMENTS_PER` — how many corpus segments each Worker processes
- `REVIEWS_PER` — how many independent Critic reviews each segment receives

## Step 1: Compute the Layout

You need to determine how many segments, workers, and critics the analysis requires. This depends on corpus size and agent context capacity.

### Estimating Corpus Size

If you have file paths, estimate tokens:
- **Prose**: 1 token per 4 characters
- **Source code**: 1 token per 3 characters
- **By word count**: 1 word is roughly 1.33 tokens

Use the Bash tool to count characters: `wc -c file1 file2 ...` or `find /path -type f -exec cat {} + | wc -c`.

For more precise estimates, run the [compute_layout.py](./compute_layout.py) script bundled with this skill:

```bash
python3 /path/to/compute_layout.py --corpus-chars 800000 --segments-per 3 --reviews-per 2
python3 /path/to/compute_layout.py --corpus-files file1.txt file2.txt --segments-per 3 --reviews-per 2
python3 /path/to/compute_layout.py --corpus-tokens 200000 --segments-per 3 --reviews-per 2 --json
```

### Computing Manually

If you cannot run the script, compute by hand. **Use the Bash tool with `python3 -c "..."` for all arithmetic** — do not compute in your head.

**Agent capacity:**
```
AGENT_CONTEXT  = 200,000 tokens
RESERVED       = 35%  (for prompt, reasoning, output)
AVAILABLE      = AGENT_CONTEXT * 0.65 = 130,000 tokens
SEGMENT_BUDGET = AVAILABLE / SEGMENTS_PER
```

**Segment count:**
```
OVERLAP  = 10% of SEGMENT_BUDGET
STRIDE   = SEGMENT_BUDGET - OVERLAP
SEGMENT_COUNT = ceil((CORPUS_TOKENS - SEGMENT_BUDGET) / STRIDE) + 1
```

If `CORPUS_TOKENS <= SEGMENT_BUDGET`, then `SEGMENT_COUNT = 1` (no fan-out needed).

**Agent counts:**
```
WORKER_COUNT = ceil(SEGMENT_COUNT / SEGMENTS_PER)
TOTAL_CRITIC_ASSIGNMENTS = SEGMENT_COUNT * REVIEWS_PER
CRITIC_COUNT = ceil(TOTAL_CRITIC_ASSIGNMENTS / SEGMENTS_PER)
```

### What These Numbers Mean

- Each **Worker** reads `SEGMENTS_PER` consecutive segments of raw corpus and writes an analysis report.
- Each **Critic** reads all Worker reports that cover a subset of segments and writes a review.
- Each segment gets reviewed by `REVIEWS_PER` different Critics (redundancy for thoroughness).

### Assigning Critics to Segments

The critic count tells you how many critics to create, but you also need to decide which segments each critic reviews. Use round-robin assignment to distribute `REVIEWS_PER` critic passes evenly across segments:

```
For each segment S (1 to SEGMENT_COUNT):
    Assign REVIEWS_PER different critics to review S
    Rotate through critics: critic index = (S * review_pass + offset) % CRITIC_COUNT
```

In practice, use `python3 -c "..."` to generate the assignment table. Example for 6 segments, 4 critics, REVIEWS_PER=2:

```
C01 reviews: S01, S03, S05
C02 reviews: S02, S04, S06
C03 reviews: S01, S04, S06
C04 reviews: S02, S03, S05
```

Each segment appears in exactly 2 critics' lists. Each critic reads the Worker reports that cover its assigned segments. Include this assignment table in the orchestration plan so the mapping is explicit and verifiable.

## Step 2: Set Up the Temp Directory

If the user specified a working directory, use it. Otherwise, create one:

```bash
WORK_DIR=$(mktemp -d -t fanout-XXXXXX)
mkdir -p "$WORK_DIR/segments" "$WORK_DIR/workers" "$WORK_DIR/critics"
```

All paths in prompts and file references are **absolute paths**. Subagents cannot resolve relative paths reliably.

## Step 3: Enter Plan Mode and Write the Orchestration Plan

Enter plan mode. Write a plan document that includes:

1. **Layout summary**: corpus size, segment count, worker count, critic count, effort level
2. **Fan-out diagram**: a Mermaid diagram showing the pipeline (see [diagram-templates.md](./diagram-templates.md) for syntax). For large layouts (>10 workers), collapse worker ranges (e.g., `W01-W10`) into summary nodes. If the user requests Graphviz instead, use the DOT template from the same file.
3. **Worker assignment table**: which segments each Worker handles (e.g., `W01: S01-S03`)
4. **Critic assignment table**: which segments each Critic reviews, generated using the round-robin method from Step 1. Verify that each segment appears exactly `REVIEWS_PER` times across all critics.
5. **Stage descriptions**: for each stage (Workers, Critics, Summarizer), describe what agents will do, their input/output paths, and which agents run in parallel
6. **File layout**: show the directory tree that will be produced

Do not include time estimates in the plan. Agent execution time is unpredictable and estimates are misleading.

Exit plan mode. Do not proceed until the user approves the plan.

### Diagram Guidelines

Worker nodes should show their segment assignments: `W01<br/>S01-S03`. Critic nodes show their review scope. Cap visible nodes at ~15; collapse ranges for larger layouts. See [diagram-templates.md](./diagram-templates.md) for full Mermaid and Graphviz templates with styling.

## Step 4: Create All Tasks

Before launching any subagents, create ALL tasks upfront using TaskCreate:

- One task per Worker (`W01`, `W02`, ...)
- One task per Critic (`C01`, `C02`, ...)
- One task for the Summarizer

Then set up dependencies with TaskUpdate `addBlockedBy`:
- Each Critic task is blocked by the Worker tasks whose segments it reviews
- The Summarizer task is blocked by all Critic tasks

This creates the full dependency graph before any work starts.

## Step 5: Launch Workers

Mark Worker tasks as `in_progress`, then launch all Workers in parallel (one Task tool call per worker, all in the same message).

### Worker Prompt Template

Each Worker gets a prompt structured like this:

```
You are {WORKER_NAME}, a corpus analysis worker.

## Your Assignment
Analyze segments {FIRST_SEG} through {LAST_SEG} of the corpus.

## Input
Read these files:
- {ABSOLUTE_PATH_TO_SEGMENT_FILE_1}
- {ABSOLUTE_PATH_TO_SEGMENT_FILE_2}
- ...

## Analysis Goal
{WHAT_THE_USER_WANTS_ANALYZED}

## Output Format
Write your report to: {ABSOLUTE_PATH_TO_WORK_DIR}/workers/{WORKER_NAME}.md

Structure your report as:

### Summary
2-3 sentence overview of findings for your segments.

### Detailed Findings
For each significant finding:
- **Finding**: one-line description
- **Location**: file/section where found
- **Evidence**: relevant quote or reference
- **Significance**: why this matters

### Segment Coverage
List each segment you analyzed and confirm you read it completely.
If any segment was too large to process fully, state which parts you skipped.
```

Adapt the analysis goal and output format to match what the user asked for. The template above is a starting point — be specific about what constitutes a "finding" for this particular analysis.

### After Workers Complete

Verify each worker wrote its output file:

```bash
ls -la "$WORK_DIR/workers/"
```

Mark completed Worker tasks as `completed`. If any Worker failed or did not produce output, see **Failure Recovery** below.

## Step 6: Launch Critics

Mark Critic tasks as `in_progress`, then launch all Critics in parallel.

### Critic Prompt Template

```
You are {CRITIC_NAME}, reviewing Worker analyses for segments {SEG_RANGE}.

## Input
Read these Worker reports:
- {ABSOLUTE_PATH_TO_WORK_DIR}/workers/{WORKER_1}.md
- {ABSOLUTE_PATH_TO_WORK_DIR}/workers/{WORKER_2}.md
- ...

## Your Task
1. Read all Worker reports listed above.
2. Evaluate completeness: did the Workers cover their segments thoroughly?
3. Identify cross-segment patterns the Workers may have missed individually.
4. Flag contradictions between Worker reports.
5. Note any gaps — segments or topics that were under-analyzed.

## Output Format
Write your review to: {ABSOLUTE_PATH_TO_WORK_DIR}/critics/{CRITIC_NAME}.md

Structure your review as:

### Cross-Segment Patterns
Themes or findings that span multiple Workers' segments.

### Quality Assessment
For each Worker report you reviewed:
- Coverage: complete / partial / insufficient
- Accuracy: any factual issues or misinterpretations

### Gaps and Contradictions
Anything missing or conflicting across reports.

### Consolidated Key Findings
The most important findings from the segments you reviewed, after accounting for quality.
```

### After Critics Complete

Verify output files and mark tasks `completed`. Handle failures per **Failure Recovery**.

## Step 7: Launch Summarizer

Mark the Summarizer task as `in_progress`. Launch a single Summarizer subagent.

### Summarizer Prompt Template

```
You are the Summarizer, producing the final analysis report.

## Input
Read all Critic reviews:
- {ABSOLUTE_PATH_TO_WORK_DIR}/critics/{CRITIC_1}.md
- {ABSOLUTE_PATH_TO_WORK_DIR}/critics/{CRITIC_2}.md
- ...

You may also reference Worker reports for detail:
- {ABSOLUTE_PATH_TO_WORK_DIR}/workers/*.md

## Your Task
Synthesize all Critic reviews into a single cohesive report. Prioritize the Critics' consolidated findings and cross-segment patterns.

## Output
Write the final report to: {ABSOLUTE_PATH_TO_WORK_DIR}/final-report.md

Structure:

### Executive Summary
3-5 sentences: what was analyzed, what was found, what matters most.

### Key Findings
The most significant findings, ordered by importance. Each finding should include supporting evidence from the Critic and Worker reports.

### Detailed Analysis
Full narrative organized by theme or topic.

### Methodology Notes
- Corpus size, segment count, agent layout
- Any gaps, failures, or limitations encountered during analysis

### Appendix
- List of all Worker and Critic reports with paths
```

The Summarizer should return a brief (2-3 sentence) summary of findings to you, and defer the full explanation to the written file. Return the file path to the user.

## Failure Recovery

### Context Limit Failures

If a subagent fails because it hit its context limit:

1. Split its work in half.
2. For Workers: create two new workers with half the segments each. Name them by appending a letter: `W03a`, `W03b`.
3. For Critics: create two new critics with half the review scope. Name them `C01a`, `C01b`.
4. Create new tasks for the split agents, with the same dependencies as the original.
5. Mark the original task as `completed` (it was replaced, not failed).
6. Launch the new agents.

### Missing Output Files

If a subagent completes but its output file does not exist:
1. Retry once with the same prompt.
2. If it fails again, note the gap in the Summarizer prompt so it can account for missing coverage.

### Stuck Detection

If you have retried the same agent 3 times with similar failures, stop. Report what you expected, what happened, and what assumption might be wrong. Do not keep retrying.

## Quick Reference

| Parameter | Some Effort | A Lot of Effort | Herculean |
|-----------|-------------|-----------------|-----------|
| SEGMENTS_PER | 3 | 3 | 2 |
| REVIEWS_PER | 2 | 3 | 3 |
| Agent context reserved | 35% | 35% | 35% |
| Segment overlap | 10% | 10% | 10% |
| Default agent type | sonnet-general-purpose | sonnet-general-purpose | sonnet-general-purpose |

| Agent Naming | Convention |
|-------------|------------|
| Workers | W01, W02, ... W99 |
| Split workers | W03a, W03b |
| Critics | C01, C02, ... C99 |
| Split critics | C01a, C01b |
| Summarizer | (just "Summarizer") |

## Absolute Path Rule

Every file path in every subagent prompt is an absolute path. Subagents do not inherit your working directory. If you write `/tmp/fanout-abc123/workers/W01.md`, that exact string appears in the prompt — never `./workers/W01.md` or `workers/W01.md`.

## Checklist

Create a task (TaskCreate) for every item below. Mark each `in_progress` before starting it, `completed` after finishing. Do not skip items or batch them.

- [ ] Ask user for analysis goal (or confirm from context)
- [ ] Ask user for effort level
- [ ] Estimate corpus size (use Bash `wc -c` for character counts)
- [ ] Compute layout (run compute_layout.py or use Bash `python3 -c "..."` — never mental math)
- [ ] Generate critic-to-segment assignment table (use `python3 -c "..."`)
- [ ] Create temp directory with `segments/`, `workers/`, `critics/` subdirectories
- [ ] Enter plan mode and write orchestration plan with diagram, assignment tables, and file layout
- [ ] Exit plan mode and get user approval
- [ ] Create all subagent tasks (one per Worker, Critic, Summarizer) with dependencies
- [ ] Launch Workers in parallel; verify output files exist with `ls`
- [ ] Launch Critics in parallel; verify output files exist with `ls`
- [ ] Launch Summarizer; verify output file exists
- [ ] Return report path to user
