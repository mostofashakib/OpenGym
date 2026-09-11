#!/usr/bin/env python3

"""
Post a converted task state (initial or expected) from a JSONL file to the
running Gmail env's /api/state endpoint.

The JSONL lines are expected to be in the shape produced by
convert_ready_tasks_to_jsonl.py:
{
  "problem": str,
  "metadata": { "id": str, "initial": GlobalState, "expected": GlobalState }
}

Usage examples:

Post the first task's initial state (1-indexed):
  python post_converted_state.py \
    --jsonl /Users/kavya/code/webshites/data/gmail/ready_tasks_converted.jsonl \
    --index 1 --which initial --url http://localhost:3000 --path /api/state

Post by id, expected state:
  python post_converted_state.py --jsonl ... --id c89c... --which expected
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from typing import Optional
import base64


def _read_line_by_index(jsonl_path: str, index_1_based: int) -> Optional[dict]:
    if index_1_based <= 0:
        raise ValueError('index must be >= 1')
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        idx = 0
        for line in f:
            s = line.strip()
            if not s:
                continue
            idx += 1
            if idx == index_1_based:
                return json.loads(s)
    return None


def _read_line_by_id(jsonl_path: str, task_id: str) -> Optional[dict]:
    tid = str(task_id)
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except json.JSONDecodeError:
                continue
            # Support both new shape (metadata.id) and legacy (top-level id)
            obj_id = obj.get('id')
            if obj_id is None:
                md = obj.get('metadata') if isinstance(obj, dict) else None
                if isinstance(md, dict):
                    obj_id = md.get('id')
            if obj_id is not None and str(obj_id) == tid:
                return obj
    return None


def _post_json(url: str, path: str, body: dict, auth: Optional[tuple[str, str]] = None) -> str:
    endpoint = f"{url.rstrip('/')}{path}"
    data = json.dumps(body, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(endpoint, data=data, method='POST')
    req.add_header('content-type', 'application/json')
    if auth is not None:
        username, password = auth
        token = base64.b64encode(f"{username}:{password}".encode('utf-8')).decode('ascii')
        req.add_header('authorization', f'Basic {token}')
    with urllib.request.urlopen(req) as resp:
        content = resp.read()
        return content.decode('utf-8', errors='replace')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jsonl', default='/Users/kavya/code/webshites/data/gmail/ready_tasks_converted.jsonl', help='Converted tasks JSONL path')
    sel = parser.add_mutually_exclusive_group(required=True)
    sel.add_argument('--index', type=int, help='1-indexed position in the JSONL file')
    sel.add_argument('--id', help='Task id to select')
    parser.add_argument('--which', choices=['initial', 'expected'], default='initial', help='Which state to POST')
    parser.add_argument('--url', default='http://localhost:3000', help='Base URL of the running env')
    parser.add_argument('--path', default='/api/state', help='POST path for state endpoint')
    parser.add_argument('--basic-auth-username', default='agent', help='Basic auth username')
    parser.add_argument('--basic-auth-password', default='we-love-cua!', help='Basic auth password')
    args = parser.parse_args()

    if args.index is not None:
        obj = _read_line_by_index(args.jsonl, args.index)
    else:
        obj = _read_line_by_id(args.jsonl, args.id)

    if obj is None:
        print('Error: could not locate the selected record in JSONL', file=sys.stderr)
        return 1

    # Look for the state under metadata first (new shape), then fallback to top-level
    md = obj.get('metadata') if isinstance(obj, dict) else None
    state = None
    if isinstance(md, dict):
        state = md.get(args.which)
    if state is None:
        state = obj.get(args.which)
    if not isinstance(state, dict):
        print(f"Error: selected record missing '{args.which}' state", file=sys.stderr)
        return 1

    resp = _post_json(
        args.url,
        args.path,
        state,
        auth=(args.basic_auth_username, args.basic_auth_password),
    )
    sys.stdout.write(resp)
    sys.stdout.write('\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())


