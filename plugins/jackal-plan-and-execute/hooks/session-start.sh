#!/usr/bin/env bash
# SessionStart hook for ed3d-plan-and-execute plugin

set -euo pipefail

# Determine plugin root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Read using-plan-and-execute content
using_plan_content=$(cat "${PLUGIN_ROOT}/skills/using-plan-and-execute/SKILL.md" 2>&1 || echo "Error reading using-plan-and-execute skill")

# Escape outputs for JSON
using_plan_escaped=$(echo "$using_plan_content" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | awk '{printf "%s\\n", $0}')

# Output context injection as JSON
cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "<EXTREMELY_IMPORTANT>\n**The content below is from skills/using-plan-and-execute/SKILL.md - your introduction to using skills:**\n\n${using_plan_escaped}\n</EXTREMELY_IMPORTANT>"
  }
}
EOF

exit 0
