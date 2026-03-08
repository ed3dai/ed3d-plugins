#!/usr/bin/env python3
"""
Fan-out layout calculator for two-stage corpus analysis.

Computes segment counts, agent assignments, and validates that work
fits within agent context windows.

Usage:
    python3 compute_layout.py --corpus-tokens 200000 --segments-per 3 --reviews-per 2
    python3 compute_layout.py --corpus-chars 800000 --segments-per 2 --reviews-per 3
    python3 compute_layout.py --corpus-files file1.txt file2.txt --segments-per 3 --reviews-per 2

Estimation rules (when no tokenizer available):
    1 token ~ 4 characters (English prose)
    1 token ~ 3 characters (source code)
    1 word  ~ 1.33 tokens
"""

import argparse
import math
import os
import sys


# --- Constants ---

# Agent context window (tokens). Conservative estimate for Sonnet.
AGENT_CONTEXT_WINDOW = 200_000

# How much of the context window to reserve for the agent's prompt,
# reasoning, and output. The remainder is available for corpus input.
RESERVED_FRACTION = 0.35  # 35% reserved -> 65% available for input

# Overlap between adjacent segments as a fraction of segment size.
# Prevents losing context at segment boundaries.
OVERLAP_FRACTION = 0.10  # 10% overlap

# Characters per token for estimation
CHARS_PER_TOKEN_PROSE = 4
CHARS_PER_TOKEN_CODE = 3


def estimate_tokens_from_chars(char_count: int, is_code: bool = False) -> int:
    """Estimate token count from character count."""
    divisor = CHARS_PER_TOKEN_CODE if is_code else CHARS_PER_TOKEN_PROSE
    return math.ceil(char_count / divisor)


def estimate_tokens_from_files(file_paths: list[str], is_code: bool = False) -> int:
    """Estimate total token count from a list of files."""
    total_chars = 0
    for path in file_paths:
        try:
            total_chars += os.path.getsize(path)
        except OSError as e:
            print(f"Warning: cannot read {path}: {e}", file=sys.stderr)
    return estimate_tokens_from_chars(total_chars, is_code)


def compute_segment_size(agent_context: int = AGENT_CONTEXT_WINDOW,
                         reserved: float = RESERVED_FRACTION) -> int:
    """Compute the maximum tokens a single segment can contain."""
    return int(agent_context * (1 - reserved))


def compute_layout(corpus_tokens: int,
                   segments_per: int,
                   reviews_per: int,
                   agent_context: int = AGENT_CONTEXT_WINDOW,
                   reserved: float = RESERVED_FRACTION,
                   overlap: float = OVERLAP_FRACTION) -> dict:
    """
    Compute the full fan-out layout.

    Args:
        corpus_tokens: Total tokens in the corpus.
        segments_per: How many segments each Worker processes.
        reviews_per: How many Critic reviews each segment receives.
        agent_context: Agent's context window in tokens.
        reserved: Fraction of context reserved for prompt/output.
        overlap: Fraction of overlap between adjacent segments.

    Returns:
        Dict with all computed values.
    """
    # Available tokens per agent for input
    available_per_agent = compute_segment_size(agent_context, reserved)

    # Each worker handles segments_per segments, so the per-segment budget is:
    segment_budget = available_per_agent // segments_per

    # Effective stride (how far each segment advances)
    stride = int(segment_budget * (1 - overlap))

    # Total segments needed
    if corpus_tokens <= segment_budget:
        segment_count = 1
    else:
        segment_count = math.ceil((corpus_tokens - segment_budget) / stride) + 1

    # Workers
    worker_count = math.ceil(segment_count / segments_per)

    # Critics: each segment gets reviews_per reviews.
    # Each critic reviews all worker reports for a subset of segments.
    # A critic can handle roughly the same number of segments as a worker
    # (reading worker reports is smaller than reading raw corpus).
    critic_segments_per = segments_per  # same grouping size
    total_critic_assignments = segment_count * reviews_per
    critic_count = math.ceil(total_critic_assignments / critic_segments_per)

    # Worker names
    workers = [f"W{i+1:02d}" for i in range(worker_count)]

    # Critic names
    critics = [f"C{i+1:02d}" for i in range(critic_count)]

    # Worker -> segment assignments
    worker_segments = {}
    for i, w in enumerate(workers):
        start = i * segments_per + 1
        end = min(start + segments_per, segment_count + 1)
        worker_segments[w] = list(range(start, end))

    return {
        "corpus_tokens": corpus_tokens,
        "segment_budget": segment_budget,
        "stride": stride,
        "overlap_tokens": segment_budget - stride,
        "segment_count": segment_count,
        "segments_per": segments_per,
        "reviews_per": reviews_per,
        "worker_count": worker_count,
        "critic_count": critic_count,
        "total_critic_assignments": total_critic_assignments,
        "workers": workers,
        "critics": critics,
        "worker_segments": worker_segments,
        "available_per_agent": available_per_agent,
        "agent_context": agent_context,
    }


def format_report(layout: dict) -> str:
    """Format the layout as a human-readable report."""
    lines = [
        "# Fan-Out Layout Report",
        "",
        "## Corpus",
        f"- Total tokens: {layout['corpus_tokens']:,}",
        f"- Segment budget: {layout['segment_budget']:,} tokens each",
        f"- Stride: {layout['stride']:,} tokens",
        f"- Overlap: {layout['overlap_tokens']:,} tokens ({layout['overlap_tokens']/layout['segment_budget']*100:.0f}%)",
        f"- Total segments: {layout['segment_count']}",
        "",
        "## Workers",
        f"- Segments per worker: {layout['segments_per']}",
        f"- Total workers: {layout['worker_count']}",
        f"- Names: {', '.join(layout['workers'])}",
        "",
        "## Critics",
        f"- Reviews per segment: {layout['reviews_per']}",
        f"- Total critic assignments: {layout['total_critic_assignments']}",
        f"- Total critics: {layout['critic_count']}",
        f"- Names: {', '.join(layout['critics'])}",
        "",
        "## Agent Context",
        f"- Context window: {layout['agent_context']:,} tokens",
        f"- Available for input: {layout['available_per_agent']:,} tokens ({100*(1-RESERVED_FRACTION):.0f}%)",
        f"- Reserved for prompt/output: {layout['agent_context'] - layout['available_per_agent']:,} tokens ({100*RESERVED_FRACTION:.0f}%)",
        "",
        "## Worker Assignments",
    ]
    for w, segs in layout['worker_segments'].items():
        seg_names = ", ".join(f"S{s:02d}" for s in segs)
        lines.append(f"- {w}: [{seg_names}]")

    lines.extend([
        "",
        "## Total Agents",
        f"- Workers: {layout['worker_count']}",
        f"- Critics: {layout['critic_count']}",
        f"- Summarizer: 1",
        f"- **Total: {layout['worker_count'] + layout['critic_count'] + 1}**",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Compute fan-out layout for two-stage corpus analysis."
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--corpus-tokens", type=int,
                       help="Total corpus size in tokens")
    group.add_argument("--corpus-chars", type=int,
                       help="Total corpus size in characters (estimated at 4 chars/token)")
    group.add_argument("--corpus-files", nargs="+",
                       help="Files to analyze (sizes will be summed)")

    parser.add_argument("--segments-per", type=int, required=True,
                        help="Segments per worker agent")
    parser.add_argument("--reviews-per", type=int, required=True,
                        help="Critic reviews per segment")
    parser.add_argument("--code", action="store_true",
                        help="Corpus is source code (use 3 chars/token instead of 4)")
    parser.add_argument("--context-window", type=int, default=AGENT_CONTEXT_WINDOW,
                        help=f"Agent context window in tokens (default: {AGENT_CONTEXT_WINDOW})")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON instead of human-readable report")

    args = parser.parse_args()

    if args.corpus_tokens:
        corpus_tokens = args.corpus_tokens
    elif args.corpus_chars:
        corpus_tokens = estimate_tokens_from_chars(args.corpus_chars, args.code)
    else:
        corpus_tokens = estimate_tokens_from_files(args.corpus_files, args.code)

    layout = compute_layout(
        corpus_tokens=corpus_tokens,
        segments_per=args.segments_per,
        reviews_per=args.reviews_per,
        agent_context=args.context_window,
    )

    if args.json:
        import json
        print(json.dumps(layout, indent=2))
    else:
        print(format_report(layout))


if __name__ == "__main__":
    main()
