#!/usr/bin/env python3

"""
Split a converted ready-tasks JSONL into two files based on requires_response
from tasks-metadata.json.

Input lines (from ready_tasks_converted.jsonl) are JSON objects like:
{
  "problem": str,
  "metadata": { "id": str, "initial": ..., "expected": ... }
}

We look up metadata.tasks[].requires_response for that id (or task_id) in
/Users/kavya/code/webshites/matrices-data-extraction/tasks-metadata.json by
default, then write the original line to:
- ready_tasks_state_comparison.jsonl (requires_response == False)
- ready_tasks_response_required.jsonl (requires_response == True)

Outputs are created in the same directory as the input JSONL.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict


def _load_requires_map(metadata_path: str) -> Dict[str, bool]:
    """Return a map of task id -> requires_response (bool).

    Supports the raw metadata shape with top-level { tasks: [...] }.
    """
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"metadata file not found: {metadata_path}")
    with open(metadata_path, 'r', encoding='utf-8', errors='ignore') as f:
        data = json.load(f)

    mapping: Dict[str, bool] = {}

    def _maybe_add(entry: dict) -> None:
        if not isinstance(entry, dict):
            return
        tid = entry.get('task_id') or entry.get('id')
        rr = entry.get('requires_response')
        if isinstance(tid, str) and isinstance(rr, bool):
            mapping[tid] = rr

    if isinstance(data, dict):
        tasks = data.get('tasks')
        if isinstance(tasks, list):
            for item in tasks:
                _maybe_add(item)
        else:
            _maybe_add(data)
    elif isinstance(data, list):
        for item in data:
            _maybe_add(item)
    else:
        raise ValueError('Unsupported metadata file format')

    return mapping


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--input',
        required=True,
        help='Path to ready_tasks_converted.jsonl',
    )
    parser.add_argument(
        '--metadata-file',
        default='/Users/kavya/code/webshites/matrices-data-extraction/tasks-metadata.json',
        help='Path to tasks-metadata.json with a top-level tasks array',
    )
    parser.add_argument('--quiet', action='store_true', help='Reduce warnings to stderr')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: input JSONL not found: {args.input}", file=sys.stderr)
        return 2

    try:
        requires_map = _load_requires_map(args.metadata_file)
    except Exception as e:
        print(f"Error: failed to load metadata: {e}", file=sys.stderr)
        return 3

    in_dir = os.path.dirname(os.path.abspath(args.input))
    out_false = os.path.join(in_dir, 'ready_tasks_state_comparison.jsonl')
    out_true = os.path.join(in_dir, 'ready_tasks_response_required.jsonl')

    processed = 0
    missing = 0
    written_false = 0
    written_true = 0

    with open(args.input, 'r', encoding='utf-8') as fin, \
            open(out_false, 'w', encoding='utf-8') as fout_false, \
            open(out_true, 'w', encoding='utf-8') as fout_true:
        for raw in fin:
            if not raw.strip():
                continue
            try:
                rec = json.loads(raw)
            except Exception as e:
                if not args.quiet:
                    print(f"Warning: skipping invalid JSONL line: {e}", file=sys.stderr)
                continue
            if not isinstance(rec, dict):
                continue
            md = rec.get('metadata')
            tid = md.get('id') if isinstance(md, dict) else None
            if not isinstance(tid, str):
                continue
            processed += 1
            rr = requires_map.get(tid)
            if rr is None:
                missing += 1
                # Skip tasks we cannot classify by requires_response
                continue
            # Preserve original line formatting
            line = raw if raw.endswith('\n') else (raw + '\n')
            if rr:
                fout_true.write(line)
                written_true += 1
            else:
                fout_false.write(line)
                written_false += 1

    if not args.quiet:
        print(
            f"Processed {processed} lines; wrote {written_false} (requires_response=False) to {out_false} "
            f"and {written_true} (requires_response=True) to {out_true}; skipped {missing} without metadata.",
            file=sys.stderr,
        )

    return 0


if __name__ == '__main__':
    raise SystemExit(main())


