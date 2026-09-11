#!/usr/bin/env python3

"""
Filter a ready_tasks_state_comparison.jsonl file to exclude tasks tagged with
"safety" in the metadata file (tasks-metadata.json).

Usage:
  python3 containers/gmail/scripts/filter_ready_tasks_state_comparison.py \
    --input /Users/kavya/code/webshites/data/gmail/ready_tasks_state_comparison.jsonl \
    --metadata /Users/kavya/code/webshites/matrices-data-extraction/tasks-metadata.json \
    --output /Users/kavya/code/webshites/data/gmail/ready_tasks_state_comparison_filtered.jsonl

Notes:
  - The script streams input and writes output line-by-line.
  - A task line is excluded if its resolved task_id has the tag "safety"
    according to the metadata file. If the task id cannot be resolved, the
    line is kept by default.
  - ID resolution is robust: it looks for one of the following keys in each
    line's JSON object, in order: metadata.id, id, task_id, metadata.task_id.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, Optional, Set


def load_safety_ids(metadata_path: Path) -> Set[str]:
    """Load task IDs tagged with "safety" from tasks-metadata.json.

    The file is expected to have the structure:
      { "metadata": {...}, "tasks": [ {"task_id": str, "tags": [...]}, ... ] }
    """
    with metadata_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    tasks = data.get("tasks", [])
    safety_ids: Set[str] = set()
    for task in tasks:
        task_id = task.get("task_id")
        tags = task.get("tags", []) or []
        if isinstance(task_id, str) and isinstance(tags, list) and "safety" in tags:
            safety_ids.add(task_id)
    return safety_ids


def iter_jsonl(path: Path) -> Iterable[tuple[Optional[dict], str]]:
    """Yield (parsed_json, raw_line) for each line in a JSONL file.

    If a line cannot be parsed as JSON, (None, raw_line) is yielded.
    """
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            raw = line.rstrip("\n")
            if not raw.strip():
                yield None, raw
                continue
            try:
                yield json.loads(raw), raw
            except Exception:
                # Preserve unparseable lines
                yield None, raw


def resolve_task_id(obj: Optional[dict]) -> Optional[str]:
    """Best-effort task id resolution from a line object.

    Tries the following paths:
      - obj["metadata"]["id"]
      - obj["id"]
      - obj["task_id"]
      - obj["metadata"]["task_id"]
    Returns None if not found or obj is None.
    """
    if not isinstance(obj, dict):
        return None
    md = obj.get("metadata")
    if isinstance(md, dict):
        mid = md.get("id")
        if isinstance(mid, str):
            return mid
        mtask = md.get("task_id")
        if isinstance(mtask, str):
            return mtask
    oid = obj.get("id")
    if isinstance(oid, str):
        return oid
    tid = obj.get("task_id")
    if isinstance(tid, str):
        return tid
    return None


def filter_jsonl(
    input_path: Path,
    safety_ids: Set[str],
    output_path: Optional[Path] = None,
) -> tuple[int, int, int]:
    """Filter lines where resolved task_id is in safety_ids.

    Returns a tuple: (total_lines, kept_lines, filtered_lines)
    """
    total = kept = filtered = 0

    out_f = None
    try:
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            out_f = output_path.open("w", encoding="utf-8")

        for obj, raw in iter_jsonl(input_path):
            total += 1
            task_id = resolve_task_id(obj)
            if task_id is not None and task_id in safety_ids:
                filtered += 1
                continue
            kept += 1
            if out_f is not None:
                if obj is None:
                    out_f.write(raw + "\n")
                else:
                    out_f.write(json.dumps(obj, separators=(",", ":")) + "\n")
            else:
                # Write to stdout if no output path provided
                if obj is None:
                    print(raw)
                else:
                    print(json.dumps(obj, separators=(",", ":")))
    finally:
        if out_f is not None:
            out_f.close()

    return total, kept, filtered


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to ready_tasks_state_comparison.jsonl",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        required=True,
        help="Path to tasks-metadata.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=False,
        help="Optional path to write filtered JSONL. If omitted, prints to stdout.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    if not args.input.exists():
        print(f"Input JSONL not found: {args.input}", file=sys.stderr)
        return 2
    if not args.metadata.exists():
        print(f"Metadata JSON not found: {args.metadata}", file=sys.stderr)
        return 2

    safety_ids = load_safety_ids(args.metadata)
    total, kept, filtered = filter_jsonl(args.input, safety_ids, args.output)

    summary = {
        "input_lines": total,
        "kept_lines": kept,
        "filtered_out": filtered,
        "output": str(args.output) if args.output else "stdout",
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


