#!/usr/bin/env python3

"""
Extract a task whose metadata.stage == "ready-to-train" from a potentially huge
JSON file (JSON array or JSONL) and print it to stdout.

Selection:
- By index (1-indexed among ready-to-train): --index N
- By id (overrides --index): --id TASK_ID

Defaults:
- --tasks-file /Users/kavya/code/webshites/matrices-data-extraction/tasks_states_and_metadata.json
- --index 24 (1-indexed)

Outputs the full JSON of the selected task to stdout. Use --pretty to pretty print.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
from typing import Generator, Optional


def _iter_json_array_objects(fp: io.TextIOBase) -> Generator[dict, None, None]:
    """Stream JSON objects from a huge top-level JSON array without loading the whole file.

    This is a minimal stateful parser sufficient for well-formed JSON with a top-level array.
    It tracks string/escape/braces and yields each object as it's completed.
    """

    # Seek to first '['
    # We read in chunks but iterate character-by-character to track string state.
    in_string = False
    escape = False
    depth = 0
    buf_chars: list[str] = []
    obj_started = False
    saw_array_start = False

    while True:
        chunk = fp.read(65536)
        if not chunk:
            break
        for ch in chunk:
            if not saw_array_start:
                if ch.isspace():
                    continue
                if ch == '[':
                    saw_array_start = True
                    continue
                # Not an array; stop and let caller fallback
                raise ValueError("File does not start with a JSON array")

            # Scan until object start
            if not obj_started:
                if ch.isspace() or ch == ',' or ch == ']':
                    # skip commas/whitespace; ']' means array end
                    if ch == ']':
                        return
                    continue
                if ch == '{':
                    obj_started = True
                    depth = 1
                    in_string = False
                    escape = False
                    buf_chars = ['{']
                    continue
                # any other char is unexpected (comments not allowed)
                continue

            # Within object capture
            buf_chars.append(ch)
            if in_string:
                if escape:
                    escape = False
                elif ch == '\\':
                    escape = True
                elif ch == '"':
                    in_string = False
            else:
                if ch == '"':
                    in_string = True
                elif ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        # Complete object
                        text = ''.join(buf_chars)
                        try:
                            obj = json.loads(text)
                        except json.JSONDecodeError as e:
                            raise RuntimeError(f"Failed to parse object: {e}\n{text[:200]}...") from e
                        yield obj
                        # Reset for next
                        obj_started = False
                        buf_chars = []


def _iter_json_lines(fp: io.TextIOBase) -> Generator[dict, None, None]:
    for line in fp:
        s = line.strip()
        if not s:
            continue
        try:
            yield json.loads(s)
        except json.JSONDecodeError:
            # Best effort: some files may have trailing commas or are not JSONL
            continue


def iterate_tasks(file_path: str) -> Generator[dict, None, None]:
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as fp:
        # Peek first non-space char
        pos = fp.tell()
        first_non_ws = ''
        while True:
            c = fp.read(1)
            if not c:
                break
            if not c.isspace():
                first_non_ws = c
                break
        fp.seek(pos)
        if first_non_ws == '[':
            yield from _iter_json_array_objects(fp)
        else:
            yield from _iter_json_lines(fp)


def select_nth_ready_task(file_path: str, index_1_based: int) -> Optional[dict]:
    if index_1_based <= 0:
        raise ValueError("index must be >= 1 (1-indexed)")
    count = 0
    for obj in iterate_tasks(file_path):
        stage = None
        md = obj.get('metadata')
        if isinstance(md, dict):
            stage = md.get('stage')
        # Some datasets may nest under stateBySite/...; we only care about metadata.stage
        if stage in ('ready-to-evaluate', 'ready-to-train', 'ready'):
            count += 1
            if count == index_1_based:
                return obj
    return None


def select_ready_task_by_id(file_path: str, task_id: str) -> Optional[dict]:
    """Return the first ready task matching the provided id.

    The id may appear in multiple common locations; we check a few likely fields
    to be robust across datasets: top-level "id", "task_id", "taskId", and the
    same keys under "metadata".
    """
    target = str(task_id)
    for obj in iterate_tasks(file_path):
        md = obj.get('metadata') if isinstance(obj.get('metadata'), dict) else None
        stage = md.get('stage') if md else None
        if stage not in ('ready-to-evaluate', 'ready-to-train', 'ready'):
            continue

        candidate_values = []
        for key in ('id', 'task_id', 'taskId'):
            if key in obj:
                candidate_values.append(obj.get(key))
        if md:
            for key in ('id', 'task_id', 'taskId'):
                if key in md:
                    candidate_values.append(md.get(key))

        for candidate in candidate_values:
            if candidate is None:
                continue
            if str(candidate) == target:
                return obj
    return None


def main() -> int:
    default_tasks = "/Users/kavya/code/webshites/matrices-data-extraction/tasks_states_and_metadata.json"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tasks-file', default=default_tasks, help='Path to tasks_states_and_metadata.json')
    parser.add_argument('--index', type=int, default=24, help='1-indexed position among ready tasks')
    parser.add_argument('--task-id', type=str, default=None, help='Find ready task by id (matches top-level or metadata id/task_id)')
    parser.add_argument('--pretty', action='store_true', help='Pretty-print JSON output')
    parser.add_argument('--output', '-o', help='Optional output file; defaults to stdout')
    args = parser.parse_args()

    if not os.path.exists(args.tasks_file):
        print(f"Error: tasks file not found: {args.tasks_file}", file=sys.stderr)
        return 2

    if args.task_id is not None:
        task = select_ready_task_by_id(args.tasks_file, args.task_id)
        if task is None:
            print(f"Error: could not find a ready task with id: {args.task_id}", file=sys.stderr)
            return 1
    else:
        task = select_nth_ready_task(args.tasks_file, args.index)
        if task is None:
            print(f"Error: could not find the {args.index}th ready task", file=sys.stderr)
            return 1

    data = json.dumps(task, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(data)
            f.write('\n')
    else:
        sys.stdout.write(data)
        sys.stdout.write('\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())


