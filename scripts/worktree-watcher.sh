#!/usr/bin/env bash
# worktree-watcher.sh — wake-on-state-change watcher for director-dispatched async work.
#
# Launched as a BACKGROUND task by the director. Polls a worktree's HEAD every
# POLL_INTERVAL seconds. Writes exactly one signal line and exits:
#   NEW_COMMIT <sha>                    — HEAD advanced (qualifying state change); exit 0
#   STALLED <agent> <window> <activity> — EXPECT elapsed with no new commit; exit 0
#
# <activity> is `active` or `idle`. HEAD alone cannot distinguish an agent that died
# from one that is still working but has not committed yet, and treating the two alike
# is what makes a recovery dispatch risk two writers in one worktree. `active` means the
# working tree changed during the window (files being edited, no commit yet) — prefer
# SendMessage over a cold re-dispatch. `idle` means nothing moved at all.
#
# Readers parsing only the first three fields keep working; <activity> is additive.
# The script's completion is the event that generates the director's task-notification.
# The 60s internal poll is NOT a director foreground sleep — the sleep<timeout rule
# (see the execute skill) governs only foreground director sleeps, never this loop.
set -uo pipefail

WORKTREE="${1:?usage: worktree-watcher.sh <worktree-path> <signal-file> <expect-seconds>}"
SIGNAL="${2:?usage: worktree-watcher.sh <worktree-path> <signal-file> <expect-seconds>}"
EXPECT="${3:?usage: worktree-watcher.sh <worktree-path> <signal-file> <expect-seconds>}"

case "$EXPECT" in
  ''|*[!0-9]*|0)
    echo "usage: worktree-watcher.sh <worktree-path> <signal-file> <expect-seconds>" >&2
    echo "error: <expect-seconds> must be a positive integer, got: $EXPECT" >&2
    exit 1
    ;;
esac

POLL_INTERVAL=60
AGENT="$(basename "$WORKTREE")"

head_sha() { git -C "$WORKTREE" rev-parse HEAD 2>/dev/null; }

# Fingerprint of uncommitted work: porcelain status plus the newest mtime among
# modified/untracked files. Changes whenever the agent edits anything, even when it
# never commits — which is precisely the case HEAD comparison misses.
worktree_fingerprint() {
  local status newest
  status="$(git -C "$WORKTREE" status --porcelain 2>/dev/null)"
  newest="$(
    git -C "$WORKTREE" status --porcelain 2>/dev/null |
      sed 's/^...//' |
      while IFS= read -r path; do
        [ -f "$WORKTREE/$path" ] && stat -f %m "$WORKTREE/$path" 2>/dev/null ||
          { [ -f "$WORKTREE/$path" ] && stat -c %Y "$WORKTREE/$path" 2>/dev/null; }
      done | sort -n | tail -1
  )"
  printf '%s|%s' "$(printf '%s' "$status" | cksum)" "${newest:-0}"
}

write_signal() {
  # Atomic write: build the line in a temp file, then mv into place, so any
  # reader of $SIGNAL never observes a zero-length or partially written file.
  printf '%s\n' "$1" > "$SIGNAL.tmp"
  mv "$SIGNAL.tmp" "$SIGNAL"
}

start_sha="$(head_sha)"
last_fingerprint="$(worktree_fingerprint)"
activity="idle"
elapsed=0

while :; do
  sleep "$POLL_INTERVAL"
  elapsed=$((elapsed + POLL_INTERVAL))

  current="$(head_sha)"
  if [ -n "$current" ] && [ "$current" != "$start_sha" ]; then
    write_signal "NEW_COMMIT $current"
    exit 0
  fi

  # Latch on any observed edit: an agent that worked earlier in the window but has
  # since gone quiet is still a different situation from one that never started.
  fingerprint="$(worktree_fingerprint)"
  if [ "$fingerprint" != "$last_fingerprint" ]; then
    activity="active"
    last_fingerprint="$fingerprint"
  fi

  if [ "$elapsed" -ge "$EXPECT" ]; then
    write_signal "STALLED $AGENT $EXPECT $activity"
    exit 0
  fi
done
