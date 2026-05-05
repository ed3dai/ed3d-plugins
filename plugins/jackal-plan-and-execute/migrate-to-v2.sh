#!/bin/bash
# Migrate jackal-plan-and-execute from v1 (ed3d fork) to v2 (model-adaptive harness)
# Run from the jackal-plugins repo root.

set -e

PLUGIN_DIR="plugins/jackal-plan-and-execute"

echo "=== Migrating jackal-plan-and-execute to v2 ==="

# 1. Remove old agents
echo "Removing v1 agents..."
rm -f "$PLUGIN_DIR/agents/task-implementor-fast.md"
rm -f "$PLUGIN_DIR/agents/code-reviewer.md"
rm -f "$PLUGIN_DIR/agents/task-bug-fixer.md"
rm -f "$PLUGIN_DIR/agents/test-analyst.md"

# 2. Move v2 agents into place
echo "Installing v2 agents..."
mv "$PLUGIN_DIR/agents-v2/implementor.md" "$PLUGIN_DIR/agents/"
mv "$PLUGIN_DIR/agents-v2/reviewer.md" "$PLUGIN_DIR/agents/"
mv "$PLUGIN_DIR/agents-v2/planner.md" "$PLUGIN_DIR/agents/"

# 3. Install supervisor update (user must manually replace ~/.claude/agents/jackal-supervisor.md)
echo "Supervisor v2 agent written to: $PLUGIN_DIR/agents-v2/supervisor-v2.md"
echo "  → Manually copy to ~/.claude/agents/jackal-supervisor.md when ready"

# 4. Remove old skills
echo "Removing v1 skills..."
rm -rf "$PLUGIN_DIR/skills/asking-clarifying-questions"
rm -rf "$PLUGIN_DIR/skills/brainstorming"
rm -rf "$PLUGIN_DIR/skills/executing-an-implementation-plan"
rm -rf "$PLUGIN_DIR/skills/finishing-a-development-branch"
rm -rf "$PLUGIN_DIR/skills/requesting-code-review"
rm -rf "$PLUGIN_DIR/skills/starting-a-design-plan"
rm -rf "$PLUGIN_DIR/skills/starting-an-implementation-plan"
rm -rf "$PLUGIN_DIR/skills/systematic-debugging"
rm -rf "$PLUGIN_DIR/skills/test-driven-development"
rm -rf "$PLUGIN_DIR/skills/using-git-worktrees"
rm -rf "$PLUGIN_DIR/skills/using-plan-and-execute"
rm -rf "$PLUGIN_DIR/skills/verification-before-completion"
rm -rf "$PLUGIN_DIR/skills/writing-design-plans"
rm -rf "$PLUGIN_DIR/skills/writing-implementation-plans"

# 5. Move v2 skills into place
echo "Installing v2 skills..."
rm -rf "$PLUGIN_DIR/skills"
mv "$PLUGIN_DIR/skills-v2" "$PLUGIN_DIR/skills"

# 6. Install v2 commands
echo "Installing v2 commands..."
rm -rf "$PLUGIN_DIR/commands"
mv "$PLUGIN_DIR/commands-v2" "$PLUGIN_DIR/commands"

# 7. Remove hooks
echo "Removing v1 hooks..."
rm -rf "$PLUGIN_DIR/hooks"

# 8. Swap plugin.json
echo "Updating plugin.json..."
mv "$PLUGIN_DIR/plugin-v2.json" "$PLUGIN_DIR/.claude-plugin/plugin.json"

# 9. Swap README
echo "Updating README..."
mv "$PLUGIN_DIR/README-v2.md" "$PLUGIN_DIR/README.md"

# 10. Clean up v2 staging dirs
rm -rf "$PLUGIN_DIR/agents-v2" 2>/dev/null || true

# 11. Update jackal-supervisor skills
echo "Updating jackal-supervisor skill references..."
SUPERVISOR_DIR="plugins/jackal-supervisor/skills"
mv "$SUPERVISOR_DIR/jackal-design-plan/SKILL-v2.md" "$SUPERVISOR_DIR/jackal-design-plan/SKILL.md"
mv "$SUPERVISOR_DIR/jackal-impl-plan/SKILL-v2.md" "$SUPERVISOR_DIR/jackal-impl-plan/SKILL.md"
mv "$SUPERVISOR_DIR/jackal-finish-branch/SKILL-v2.md" "$SUPERVISOR_DIR/jackal-finish-branch/SKILL.md"

echo ""
echo "=== Migration complete ==="
echo ""
echo "Remaining manual steps:"
echo "  1. Copy agents-v2/supervisor-v2.md → ~/.claude/agents/jackal-supervisor.md"
echo "  2. Update jackal-supervisor plugin skill references"
echo "  3. Update marketplace.json version"
echo "  4. Test with a Simple issue from your backlog"
echo ""
echo "Structure:"
find "$PLUGIN_DIR" -type f -not -path "*/.git/*" | sort
