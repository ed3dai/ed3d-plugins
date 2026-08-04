---
name: autonomous-mode
description: Use when .ed3d/autonomous-mode.md exists at the project root - replaces human questions with independently researched decisions from an Opus subagent
user-invocable: false
model: fable
---

# Autonomous Mode

## Activation

This mode is active only when `[project-root]/.ed3d/autonomous-mode.md` exists. Read the sentinel file when activating; its contents may provide project-specific autonomous-mode guidance.

Once active, it remains active for the current skill invocation. Every subsequently invoked skill must check the sentinel again rather than relying on conversation memory.

If the workflow changes its project root by creating or entering a git worktree, preserve autonomous mode by creating `.ed3d/autonomous-mode.md` in the new worktree with the same contents before invoking the next skill. Do not commit the sentinel unless it was already tracked by the project.

Announce: "Autonomous mode is active. I will route decisions that normally require human input to an independent Opus subagent."

## Replace Every Human Question

These rules supersede conflicting interactive instructions in every other plan-and-execute skill. Do not use AskUserQuestion and do not pause for freeform human input. This applies to:

- requirement clarification and Definition of Done confirmation
- naming, scope, architecture, and trade-off decisions
- worktree, branch, plan, and completion choices
- approval gates, review escalations, retry limits, and test exceptions
- any other instruction in this plugin that says to ask, confirm with, present to, or escalate to the human

For every would-be question, the Fable orchestrator must first assemble a decision packet, then dispatch `ed3d-basic-agents:opus-general-purpose` to answer it.

Only the Fable orchestrator dispatches decision agents. If a worker, researcher, reviewer, or other first-level subagent encounters a question while using a skill, it must return the question, evidence, options, and blocking consequence to Fable without dispatching another subagent. Fable then researches any missing context, asks Opus, and re-dispatches or resumes the worker with the decision.

## Build an Accurate Decision Packet

Before dispatching Opus, research the question far enough that the answer can be grounded in evidence. Include:

1. The exact question and all real options or constraints.
2. The user's stated goal and relevant decisions already made in this conversation.
3. The current workflow phase and the consequence of the decision.
4. Relevant code, file paths, documentation, command output, git state, and project guidance. Include precise excerpts or direct the subagent to read exact files in the working directory.
5. Findings from codebase or internet research already performed, including competing evidence.
6. Unknowns and uncertainty. Never disguise missing user preference as a fact.
7. A preference for conservative, reversible choices when evidence cannot determine a unique answer.

The orchestrator may dispatch research subagents before the decision subagent. Those research subagents must do their work directly and must not dispatch further subagents.

## Required Opus Dispatch

Use this structure for each decision:

<invoke name="Task">
<parameter name="subagent_type">ed3d-basic-agents:opus-general-purpose</parameter>
<parameter name="description">Independently decide: [short decision name]</parameter>
<parameter name="prompt">
You are the independent decision-maker for an autonomous design-plan-implement workflow.

Answer the decision below only after independently researching and analyzing the supplied evidence. Use your own tools to inspect the referenced code and files when needed. Do not agree with the Fable orchestrator's recommendation merely for the sake of agreement. Challenge framing, assumptions, and preferred options when the evidence warrants it.

Do not dispatch or invoke any subagents.

Return:
1. Decision
2. Evidence
3. Analysis of viable alternatives
4. Risks and mitigations
5. Confidence and unresolved uncertainty

[Insert the complete decision packet here.]
</parameter>
</invoke>

Do not lead the Opus subagent toward a preferred answer. If the orchestrator has a recommendation, label it explicitly as an untrusted proposal and require the subagent to evaluate it critically.

## Continue the Workflow

Print the Opus response for transparency.

### Escalate Selectively to Fable

Accept the Opus decision directly when its evidence is sufficient, alternatives were genuinely compared, confidence is supported, and the decision is readily reversible.

Dispatch `ed3d-plan-and-execute:autonomous-decision-escalator` before proceeding when any of these conditions holds:

- Opus reports low confidence or material unresolved uncertainty.
- Evidence is missing, contradictory, or supports multiple materially different answers.
- Opus and the orchestrator reach different conclusions after independent analysis.
- The choice is destructive, externally visible, security-sensitive, expensive, or otherwise difficult to reverse.
- A wrong choice could invalidate multiple later phases or require substantial rework.

Provide the escalator with the complete original decision packet, the complete Opus response, any new research, and the exact reason escalation was triggered. Print its response and treat its ruling as the workflow decision.

Record the final decision, evidence, assumptions, and whether escalation occurred in the relevant design or plan artifact. Continue exactly as if the human had supplied that answer.

If Opus identifies a factual gap, perform the requested research and re-dispatch with the new evidence. If a fact can only come from unavailable credentials or an external stakeholder, choose the safest reversible option, document the assumption, and continue as far as possible.
