#!/usr/bin/env python3
# pattern: Mixed (unavoidable)
# Reason: CLI entry point — parses args, reads JSONL, writes output.
# Pure transformation logic is separated into functions below.
"""
Process Claude Code JSONL transcripts into different output formats.

Usage:
    python3 reduce-transcript.py <input.jsonl> [output]              # reduced text (default)
    python3 reduce-transcript.py <input.jsonl> [output] --markdown   # full Markdown export

Strips metadata (UUIDs, permissionMode, version, gitBranch, etc.)
and retains: role, message content, tool names, tool inputs, tool results,
and timestamps.
"""

import json
import sys
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Functional Core — pure transformation, no I/O
# ---------------------------------------------------------------------------

SKIP_TYPES = {"file-history-snapshot", "queue-operation", "progress"}

TOOL_RESULT_LIMIT_REDUCED = 2000
THINKING_LIMIT_REDUCED = 1000
TOOL_INPUT_LIMIT_REDUCED = 200
TOOL_RESULT_LIMIT_MARKDOWN = 10000


def extract_content_blocks(content):
    """Extract structured content blocks from a message content field.

    Returns a list of dicts with 'kind' and 'text' keys, plus optional
    'tool_name' and 'tool_input' for tool_use blocks.
    """
    if isinstance(content, str):
        return [{"kind": "text", "text": content}] if content.strip() else []

    if not isinstance(content, list):
        return []

    blocks = []
    for block in content:
        if not isinstance(block, dict):
            continue

        block_type = block.get("type", "")

        if block_type == "text":
            text = block.get("text", "")
            if text.strip():
                blocks.append({"kind": "text", "text": text})

        elif block_type == "tool_use":
            blocks.append({
                "kind": "tool_use",
                "tool_name": block.get("name", "unknown"),
                "tool_input": block.get("input", {}),
                "text": "",
            })

        elif block_type == "tool_result":
            result_content = block.get("content", "")
            inner = extract_content_blocks(result_content)
            result_text = "\n".join(b["text"] for b in inner if b["text"])
            if result_text.strip():
                blocks.append({"kind": "tool_result", "text": result_text})

        elif block_type == "thinking":
            text = block.get("thinking", "")
            if text.strip():
                blocks.append({"kind": "thinking", "text": text})

    return blocks


def _truncate(text, max_len):
    """Truncate text with ellipsis indicator."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "...[truncated]"


def _summarize_tool_input(tool_input, max_value_len=200):
    """Produce a concise summary of tool input."""
    if isinstance(tool_input, str):
        return _truncate(tool_input, 500)

    if not isinstance(tool_input, dict):
        return str(tool_input)[:500]

    parts = []
    for key, value in tool_input.items():
        if isinstance(value, str) and len(value) > max_value_len:
            parts.append(f"{key}: {_truncate(value, max_value_len)}")
        else:
            parts.append(f"{key}: {value}")

    return "; ".join(parts)


def parse_line(line_data):
    """Parse a JSONL line into a normalized structure, or None to skip.

    Returns a dict with keys: role, timestamp, blocks, line_type.
    """
    line_type = line_data.get("type", "")

    if line_type in SKIP_TYPES:
        return None

    timestamp = line_data.get("timestamp", "")

    if line_type in ("user", "assistant"):
        message = line_data.get("message", {})
        role = message.get("role", line_type)
        content = message.get("content", "")
        blocks = extract_content_blocks(content)
        if not blocks:
            return None
        return {"role": role, "timestamp": timestamp, "blocks": blocks, "line_type": line_type}

    if line_type == "tool_use":
        tool_name = line_data.get("tool_name", line_data.get("name", "unknown"))
        tool_input = line_data.get("input", line_data.get("tool_input", {}))
        blocks = [{"kind": "tool_use", "tool_name": tool_name, "tool_input": tool_input, "text": ""}]
        return {"role": "assistant", "timestamp": timestamp, "blocks": blocks, "line_type": line_type}

    if line_type == "tool_result":
        result = line_data.get("output", line_data.get("tool_response", ""))
        if isinstance(result, dict):
            result = json.dumps(result, indent=2)
        result_text = str(result)
        if not result_text.strip():
            return None
        blocks = [{"kind": "tool_result", "text": result_text}]
        return {"role": "tool", "timestamp": timestamp, "blocks": blocks, "line_type": line_type}

    # Fallback: check for message with content
    message = line_data.get("message", {})
    if message and isinstance(message, dict):
        content = message.get("content", "")
        blocks = extract_content_blocks(content)
        if blocks:
            role = message.get("role", line_type)
            return {"role": role, "timestamp": timestamp, "blocks": blocks, "line_type": line_type}

    return None


def extract_metadata(lines_iter):
    """Extract session metadata from the first few JSONL lines.

    Returns (metadata_dict, list_of_all_parsed_lines).
    Consumes the iterator fully.
    """
    metadata = {}
    parsed = []

    for line_data in lines_iter:
        if not metadata.get("session_id"):
            metadata["session_id"] = line_data.get("sessionId", "")
        if not metadata.get("cwd"):
            metadata["cwd"] = line_data.get("cwd", "")
        if not metadata.get("model"):
            msg = line_data.get("message", {})
            if isinstance(msg, dict):
                metadata["model"] = msg.get("model", "")
        if not metadata.get("first_timestamp"):
            ts = line_data.get("timestamp", "")
            if ts:
                metadata["first_timestamp"] = ts
        metadata["last_timestamp"] = line_data.get("timestamp", "") or metadata.get("last_timestamp", "")

        parsed.append(line_data)

    return metadata, parsed


def _format_timestamp_human(iso_ts):
    """Convert ISO timestamp to human-readable format."""
    if not iso_ts:
        return ""
    try:
        dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y %I:%M %p")
    except (ValueError, AttributeError):
        return iso_ts


# ---------------------------------------------------------------------------
# Formatters — pure functions producing output strings
# ---------------------------------------------------------------------------

def format_reduced(parsed_lines):
    """Format parsed lines as token-efficient reduced text."""
    results = []
    for line_data in parsed_lines:
        entry = parse_line(line_data)
        if not entry:
            continue

        parts = []
        role = entry["role"]
        ts = entry["timestamp"]
        ts_suffix = f" ({ts})" if ts else ""

        for block in entry["blocks"]:
            kind = block["kind"]
            if kind == "text":
                parts.append(block["text"])
            elif kind == "tool_use":
                summary = _summarize_tool_input(block["tool_input"], TOOL_INPUT_LIMIT_REDUCED)
                parts.append(f"[tool_use:{block['tool_name']}] {summary}")
            elif kind == "tool_result":
                parts.append(f"[tool_result] {_truncate(block['text'], TOOL_RESULT_LIMIT_REDUCED)}")
            elif kind == "thinking":
                parts.append(f"[thinking] {_truncate(block['text'], THINKING_LIMIT_REDUCED)}")

        if parts:
            text = "\n".join(parts)
            results.append(f"[{role}]{ts_suffix}\n{text}")

    return "\n\n---\n\n".join(results)


def format_markdown(metadata, parsed_lines):
    """Format parsed lines as a full Markdown document."""
    sections = []

    # Header
    header_parts = ["# Session Transcript", ""]
    session_id = metadata.get("session_id", "")
    if session_id:
        header_parts.append(f"**Session:** `{session_id}`")
    cwd = metadata.get("cwd", "")
    if cwd:
        header_parts.append(f"**Project:** `{cwd}`")
    first_ts = metadata.get("first_timestamp", "")
    if first_ts:
        header_parts.append(f"**Started:** {_format_timestamp_human(first_ts)}")
    last_ts = metadata.get("last_timestamp", "")
    if last_ts:
        header_parts.append(f"**Ended:** {_format_timestamp_human(last_ts)}")
    model = metadata.get("model", "")
    if model:
        header_parts.append(f"**Model:** {model}")
    header_parts.append("")
    header_parts.append("---")
    header_parts.append("")
    sections.append("\n".join(header_parts))

    # Messages
    for line_data in parsed_lines:
        entry = parse_line(line_data)
        if not entry:
            continue

        role = entry["role"]
        ts = _format_timestamp_human(entry["timestamp"])
        ts_suffix = f" ({ts})" if ts else ""

        msg_parts = []

        if role == "user":
            msg_parts.append(f"**human**{ts_suffix}\n")
        elif role == "assistant":
            msg_parts.append(f"**assistant**{ts_suffix}\n")
        elif role == "tool":
            # Tool results rendered inline, no separate header
            pass
        else:
            msg_parts.append(f"**{role}**{ts_suffix}\n")

        for block in entry["blocks"]:
            kind = block["kind"]

            if kind == "text":
                msg_parts.append(block["text"])

            elif kind == "tool_use":
                tool_name = block["tool_name"]
                tool_input = block["tool_input"]
                input_text = _format_tool_input_markdown(tool_input)
                msg_parts.append(f"#### Tool: {tool_name}\n")
                msg_parts.append(input_text)

            elif kind == "tool_result":
                result_text = block["text"]
                if len(result_text) > 500:
                    msg_parts.append(
                        "<details>\n<summary>Tool Result</summary>\n\n"
                        f"```\n{_truncate(result_text, TOOL_RESULT_LIMIT_MARKDOWN)}\n```\n"
                        "</details>"
                    )
                else:
                    msg_parts.append(f"```\n{result_text}\n```")

            elif kind == "thinking":
                msg_parts.append(
                    "<details>\n<summary>Thinking</summary>\n\n"
                    f"{block['text']}\n"
                    "</details>"
                )

        if msg_parts:
            sections.append("\n".join(msg_parts))

    return "\n\n---\n\n".join(sections)


def _format_tool_input_markdown(tool_input):
    """Format tool input for Markdown display."""
    if isinstance(tool_input, str):
        return f"```\n{tool_input}\n```"

    if not isinstance(tool_input, dict):
        return f"```\n{tool_input}\n```"

    # Show each field cleanly
    parts = []
    for key, value in tool_input.items():
        if isinstance(value, str) and "\n" in value:
            parts.append(f"**{key}:**\n```\n{value}\n```")
        elif isinstance(value, str) and len(value) > 100:
            parts.append(f"**{key}:** `{_truncate(value, 200)}`")
        else:
            parts.append(f"**{key}:** `{value}`")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Imperative Shell — I/O only
# ---------------------------------------------------------------------------

def parse_jsonl_file(path):
    """Read a JSONL file and yield parsed JSON objects, skipping bad lines."""
    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                yield json.loads(raw_line)
            except json.JSONDecodeError:
                pass


def main():
    if len(sys.argv) < 2:
        print(
            f"Usage: {sys.argv[0]} <input.jsonl> [output] [--markdown]",
            file=sys.stderr,
        )
        sys.exit(1)

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    use_markdown = "--markdown" in flags

    input_path = Path(args[0])
    if not input_path.exists():
        print(f"error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args[1]) if len(args) >= 2 else None

    lines_iter = parse_jsonl_file(input_path)
    metadata, parsed_lines = extract_metadata(lines_iter)

    if use_markdown:
        output_text = format_markdown(metadata, parsed_lines)
    else:
        output_text = format_reduced(parsed_lines)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_text, encoding="utf-8")
    else:
        print(output_text)


if __name__ == "__main__":
    main()
