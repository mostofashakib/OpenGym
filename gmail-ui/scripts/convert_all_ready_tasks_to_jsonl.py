#!/usr/bin/env python3

"""
Stream-convert all tasks whose stage is "ready-to-train" from a large tasks
states file (JSON array or JSONL) to a JSONL file of converted Gmail states.

Ready task detection supports two metadata inputs:
- "Merged" tasks: each task object contains a nested metadata.stage field
- Raw metadata file (pre-merge): an object with a top-level "tasks" array where
  each entry includes fields like task_id, stage, and optionally
  variant_of_task_id. In this case we derive an allowlist of task IDs from
  task_id and variant_of_task_id for entries with stage == "ready-to-train".

Each output line is a JSON object:
{
  "problem": str,                # copied from task.prompt
  "metadata": {
    "id": str,                  # copied from task.id
    "initial": GlobalState,     # converted initial state
    "expected": GlobalState     # converted expected state
  }
}

This script reuses the streaming reader from extract_ready_task.py and the
conversion logic from convert_task_states_to_store.py to avoid duplication.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

try:
    from tqdm import tqdm  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    def tqdm(iterable, *args, **kwargs):  # type: ignore
        return iterable


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--tasks-file',
        default='/Users/kavya/code/webshites/matrices-data-extraction/tasks_states.json',
        help='Path to tasks_states.json (can be JSON array or JSONL)',
    )
    parser.add_argument(
        '--metadata-file',
        default='/Users/kavya/code/webshites/matrices-data-extraction/tasks-metadata.json',
        help='Optional metadata file to filter ready-to-train IDs. Supports merged tasks (array/JSONL with metadata.stage) or raw metadata JSON with a top-level "tasks" array. If missing, include all tasks.',
    )
    parser.add_argument(
        '--output',
        default='/Users/kavya/code/webshites/data/gmail/ready_tasks_converted.jsonl',
        help='Output JSONL file with converted tasks',
    )
    parser.add_argument('--limit', type=int, default=0, help='Optional limit of tasks to convert (0 = no limit)')
    parser.add_argument('--pretty-line', action='store_true', help='Pretty-print each JSONL line (larger file)')
    args = parser.parse_args()

    if not os.path.exists(args.tasks_file):
        print(f"Error: tasks file not found: {args.tasks_file}", file=sys.stderr)
        return 2

    # Add this script directory to sys.path so we can import sibling modules
    script_dir = os.path.dirname(__file__) or '.'
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    # Lazy imports to avoid circulars and keep CLI snappy
    from extract_ready_task import iterate_tasks  # type: ignore
    import convert_task_states_to_store as cts  # type: ignore

    def _maybe_add_ready_ids_from_record(rec: dict, out: set[str]) -> None:
        # Case 1: merged tasks where stage is nested under metadata
        if isinstance(rec, dict):
            md = rec.get('metadata')
            if isinstance(md, dict) and md.get('stage') in ('ready-to-evaluate', 'ready-to-train', 'ready'):
                rid = rec.get('id')
                if isinstance(rid, str):
                    out.add(rid)
                return
            # Case 2: raw metadata entries where stage is top-level
            stage = rec.get('stage')
            if stage in ('ready-to-evaluate', 'ready-to-train', 'ready'):
                tid = rec.get('task_id') or rec.get('id')
                if isinstance(tid, str):
                    out.add(tid)
                alt = rec.get('variant_of_task_id')
                if isinstance(alt, str):
                    out.add(alt)

    # Build allowlist of ready IDs from metadata if present, supporting
    # both merged tasks and raw metadata JSON (object with a top-level tasks array)
    ready_ids: set[str] | None = None
    if args.metadata_file and os.path.exists(args.metadata_file):
        ready_ids = set()
        # First try to load as a full JSON value to handle the raw metadata shape
        loaded = None
        try:
            with open(args.metadata_file, 'r', encoding='utf-8', errors='ignore') as mf:
                loaded = json.load(mf)
        except Exception:
            loaded = None

        if isinstance(loaded, dict):
            tasks_list = loaded.get('tasks')
            if isinstance(tasks_list, list):
                for item in tqdm(tasks_list, desc="Scanning metadata tasks", unit="rec", total=len(tasks_list)):
                    if isinstance(item, dict):
                        _maybe_add_ready_ids_from_record(item, ready_ids)
            else:
                _maybe_add_ready_ids_from_record(loaded, ready_ids)
        elif isinstance(loaded, list):
            for item in tqdm(loaded, desc="Scanning metadata list", unit="rec", total=len(loaded)):
                if isinstance(item, dict):
                    _maybe_add_ready_ids_from_record(item, ready_ids)
        else:
            # Fallback to streaming records (array or JSONL)
            for rec in tqdm(iterate_tasks(args.metadata_file), desc="Scanning metadata (streaming)", unit="rec"):
                if isinstance(rec, dict):
                    _maybe_add_ready_ids_from_record(rec, ready_ids)

    written = 0
    selected = 0
    limit = args.limit if args.limit and args.limit > 0 else None

    with open(args.output, 'w', encoding='utf-8') as out:
        pbar = tqdm(iterate_tasks(args.tasks_file), desc="Converting tasks", unit="task")
        for obj in pbar:
            try:
                if ready_ids is not None:
                    tid = obj.get('id') if isinstance(obj, dict) else None
                    if not isinstance(tid, str) or tid not in ready_ids:
                        continue
                selected += 1
                # Validate presence of states
                if 'initial_state' not in obj or 'expected_state' not in obj:
                    # Skip tasks without both states
                    continue
                initial_conv = cts._convert_gmail_like_state(obj['initial_state'])
                expected_conv = cts._convert_gmail_like_state(obj['expected_state'])
                rec = {
                    'problem': obj.get('prompt'),
                    'metadata': {
                        'id': obj.get('id'),
                        'initial': initial_conv,
                        'expected': expected_conv,
                    },
                }
                if args.pretty_line:
                    out.write(json.dumps(rec, ensure_ascii=False, indent=2))
                else:
                    out.write(json.dumps(rec, ensure_ascii=False))
                out.write('\n')
                written += 1
                if hasattr(pbar, 'set_postfix'):
                    pbar.set_postfix(selected=selected, written=written)
                if limit is not None and written >= limit:
                    break
            except KeyboardInterrupt:
                print('\nInterrupted. Partial output written.', file=sys.stderr)
                break
            except Exception as e:
                # Log and continue
                print(f"Warning: failed to convert a task: {e}", file=sys.stderr)
                continue

    print(f"Converted {written} ready tasks (encountered {selected} ready tasks)")
    print(f"Output: {args.output}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())


