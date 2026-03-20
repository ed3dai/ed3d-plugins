---
name: export-session-as-markdown
description: Use when the user wants to export a Claude Code session transcript as a readable Markdown file — converts the current session (or a specified transcript path) into GitHub-flavored Markdown with metadata header, collapsible tool results, and thinking blocks
---

# Export Session as Markdown

Export a Claude Code session transcript to a human-readable GitHub-flavored Markdown file.

## Prerequisites

- The `ed3d-session-reflection` plugin must be installed (provides the `reduce-transcript.py` script).
- The current session's transcript path must be available (injected by the SessionStart hook). If it is not available, ask the user for the transcript path.

## Invocation

The user may invoke this as:
- `/export-session-as-markdown` — export the current session
- `/export-session-as-markdown /path/to/transcript.jsonl` — export a specific transcript
- `/export-session-as-markdown /path/to/transcript.jsonl /path/to/output.md` — export to a specific output path

## Steps

### 1. Determine the transcript path

If an argument was provided, use it as the transcript path. Otherwise, use the current session's transcript path from the SessionStart hook injection.

If you cannot determine the transcript path, tell the user:
```
I don't know the current session's transcript path.
Either provide a path: /export-session-as-markdown /path/to/session.jsonl
Or ensure the ed3d-session-reflection SessionStart hook is active.
```

### 2. Determine the output path

If a second argument was provided, use it as the output path. Otherwise, default to the current working directory with a descriptive filename:

```
session-transcript-YYYY-MM-DD.md
```

If a file with that name already exists, append a counter: `session-transcript-YYYY-MM-DD-2.md`.

### 3. Export the transcript

Run the script with the `--markdown` flag:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/reduce-transcript.py" "<transcript_path>" "<output_path>" --markdown
```

### 4. Report the result

Tell the user where the file was written and its size. Example:

```
Exported session transcript to ./session-transcript-2026-03-20.md (346 KB)
```
