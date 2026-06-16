#!/usr/bin/env bash
# trace-deps.sh — dependency trace / coherence gate for the jackal marketplace.
#
# Scans every plugin for cross-references (subagent_type, plugin-qualified
# skill/agent refs, REQUIRED SUB-SKILL lines) and classifies each as:
#   SHIPPED   — resolves to an agent/skill this marketplace ships
#   DECLARED  — resolves to an ed3d plugin declared in marketplace.json `requires`
#   DANGLING  — resolves to nothing known  → FAILURE
#
# Exit 0 if zero DANGLING refs; exit 1 otherwise. Re-run after any upstream sync.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# --- 1. Build the shipped inventory: "plugin:name" for every agent and skill ---
shipped=$(
  { find plugins -path "*/agents/*.md" 2>/dev/null \
      | sed -E 's|plugins/([^/]+)/agents/(.+)\.md|\1:\2|'
    find plugins -path "*/skills/*/SKILL.md" 2>/dev/null \
      | sed -E 's|plugins/([^/]+)/skills/([^/]+)/SKILL.md|\1:\2|'
  } | sort -u
)

# --- 2. Declared external deps (ed3d plugins named in marketplace.json requires) ---
declared=$(python3 -c '
import json
d = json.load(open(".claude-plugin/marketplace.json"))
deps = set()
for p in d["plugins"]:
    for r in p.get("requires", []):
        deps.add(r)
print("\n".join(sorted(deps)))
')

is_shipped()  { grep -qx "$1" <<<"$shipped"; }
# A ref "plugin:thing" is covered-by-declared if its plugin prefix is a declared dep.
is_declared() { grep -qx "${1%%:*}" <<<"$declared"; }

# --- 3. Collect references across all plugin markdown ---
# Matches: subagent_type tags, and inline plugin-qualified refs of the
# form <plugin>:<name> where <plugin> looks like a jackal-* or ed3d-* plugin.
refs=$(
  grep -rhoE '<parameter name="subagent_type">[^<]+</parameter>' plugins --include="*.md" 2>/dev/null \
    | sed -E 's|.*subagent_type">([^<]+)</.*|\1|'
  grep -rhoE '(jackal|ed3d)-[a-z-]+:[a-z][a-z0-9-]+' plugins --include="*.md" 2>/dev/null
)
refs=$(printf '%s\n' "$refs" | sort -u | grep -vE '^\s*$')

# --- 4. Classify ---
dangling=0; n_shipped=0; n_declared=0
printf '%-55s  %s\n' "REFERENCE" "STATUS"
printf '%-55s  %s\n' "---------" "------"
while IFS= read -r ref; do
  [ -z "$ref" ] && continue
  # skip refs that aren't plugin:thing shaped (e.g. label_style examples)
  case "$ref" in
    *:*) : ;;
    *) continue ;;
  esac
  if is_shipped "$ref"; then
    printf '%-55s  SHIPPED\n' "$ref"; n_shipped=$((n_shipped+1))
  elif is_declared "$ref"; then
    printf '%-55s  DECLARED (%s)\n' "$ref" "${ref%%:*}"; n_declared=$((n_declared+1))
  else
    printf '%-55s  *** DANGLING ***\n' "$ref"; dangling=$((dangling+1))
  fi
done <<<"$refs"

echo
echo "shipped=$n_shipped  declared=$n_declared  dangling=$dangling"
if [ "$dangling" -ne 0 ]; then
  echo "FAIL: $dangling dangling reference(s) — every ref must resolve to a shipped agent/skill or a declared dependency."
  exit 1
fi
echo "PASS: every cross-reference resolves."
