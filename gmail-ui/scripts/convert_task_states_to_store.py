#!/usr/bin/env python3

"""
Convert a task's initial_state and expected_state (Gmail-shaped) into the
Gmail container's GlobalState schema used by containers/gmail/lib/store.ts.

Usage examples:

1) Read the 24th ready-to-train task from the big tasks file and convert:
   python convert_task_states_to_store.py \
     --tasks-file /Users/kavya/code/webshites/matrices-data-extraction/tasks_states_and_metadata.json \
     --index 24 \
     --pretty > converted_24.json

   Output JSON structure:
   { "initial": GlobalState, "expected": GlobalState }

2) Pipe a single task JSON (from extract_ready_task.py) into this script:
   python extract_ready_task.py --index 24 | \
   python convert_task_states_to_store.py --stdin-task --pretty

Notes:
- Handles body content that may be base64-encoded or plaintext.
- Ensures safe JSON output with proper unicode handling (ensure_ascii=False).
- Maps labels and flags (UNREAD -> isRead=false, DRAFT->DRAFTS, STARRED/IMPORTANT).
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import getaddresses
from typing import Any, Dict, Iterable, List, Optional, Tuple
import re


def _load_task_from_tasks_file(tasks_file: str, index_1_based: int) -> dict:
    # Local import to avoid circular dependency and keep this script standalone.
    from extract_ready_task import select_nth_ready_task  # type: ignore

    task = select_nth_ready_task(tasks_file, index_1_based)
    if task is None:
        raise SystemExit(f"Could not find the {index_1_based}th ready task in {tasks_file}")
    return task


def _read_stdin_json() -> dict:
    data = sys.stdin.read()
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        raise SystemExit(f"Failed to parse JSON from stdin: {e}")


def _read_json_file(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.loads(f.read())


def _unwrap_gmail_state(obj: dict) -> dict:
    # Some variants are nested like { stateBySite: { gmail: {...} } }
    if 'stateBySite' in obj and isinstance(obj['stateBySite'], dict):
        gmail = obj['stateBySite'].get('gmail')
        if isinstance(gmail, dict):
            return gmail
    if 'gmail' in obj and isinstance(obj['gmail'], dict):
        return obj['gmail']
    return obj


def _parse_headers(headers_list: Iterable[dict]) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    for h in headers_list or []:
        name = (h.get('name') or '').strip().lower()
        value = (h.get('value') or '').strip()
        if name:
            headers[name] = value
    return headers


def _format_addresses(raw: Optional[str]) -> List[str]:
    if not raw or not isinstance(raw, str):
        return []
    pairs = getaddresses([raw])
    out: List[str] = []
    for display, email in pairs:
        display = display.strip()
        email = email.strip()
        if not email:
            continue
        if display and display != email:
            out.append(f"{display} <{email}>")
        else:
            out.append(email)
    return out


def _is_mostly_base64(s: str) -> bool:
    # Heuristic: if contains characters outside base64-url set, treat as plaintext
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=_-\n\r\t ")
    return all((c in allowed) for c in s)


def _b64decode_maybe(data: str) -> str:
    if not isinstance(data, str):
        return ''
    s = data.strip()
    if not s:
        return ''
    # Try to detect plaintext quickly
    if not _is_mostly_base64(s):
        return s
    # Normalize URL-safe and padding
    s = s.replace('-', '+').replace('_', '/')
    padding = (4 - (len(s) % 4)) % 4
    s = s + ('=' * padding)
    try:
        raw = base64.b64decode(s, validate=False)
        return raw.decode('utf-8', errors='replace')
    except Exception:
        # Fallback to plaintext
        return data


def _sanitize_string(s: Optional[str]) -> Optional[str]:
    """Sanitize arbitrary text for safe JSON transport and UI rendering.

    - Normalize newlines to \n
    - Remove C0/C1 control chars except \n and \t
    - Drop stray backslashes before curly quotes/dashes seen in some datasets
    - Ensure remaining backslashes are represented literally (harmless for JSON)
    """
    if s is None:
        return None
    if not isinstance(s, str):
        s = str(s)
    # Normalize newlines
    s = s.replace('\r\n', '\n').replace('\r', '\n')
    # Remove disallowed control chars (keep \n and \t)
    s = ''.join(ch if (ch == '\n' or ch == '\t' or ord(ch) >= 0x20) else ' ' for ch in s)
    # Decode double-escaped unicode sequences like "\\u2019" -> "’"
    def repl(m: re.Match[str]) -> str:
        try:
            code = int(m.group(1), 16)
            return chr(code)
        except Exception:
            return m.group(0)
    s = re.sub(r"\\u([0-9a-fA-F]{4})", repl, s)
    # Fix common stray backslashes before punctuation
    s = (
        s.replace('\\“', '“')
         .replace('\\”', '”')
         .replace('\\’', '’')
         .replace('\\‘', '‘')
         .replace('\\–', '–')
         .replace('\\—', '—')
    )
    return s


def _extract_body(payload: dict) -> Tuple[Optional[str], Optional[str]]:
    """Return (text, html) strings from a Gmail-like payload.
    Prefers html when available. Decodes base64 or returns plaintext.
    """
    if not isinstance(payload, dict):
        return None, None
    mime = (payload.get('mimeType') or '').lower()
    if mime.startswith('multipart/'):
        # Try parts: prefer html, then text
        parts = payload.get('parts') or []
        html: Optional[str] = None
        text: Optional[str] = None
        for p in parts:
            p_mime = (p.get('mimeType') or '').lower()
            p_text, p_html = _extract_body(p)
            if p_html and not html and 'html' in p_mime:
                html = p_html
            if p_text and not text and 'text' in p_mime:
                text = p_text
        # If still empty, check container body
        if not html and not text:
            body = (payload.get('body') or {}).get('data')
            if isinstance(body, str):
                # We cannot know if this is html or text; assume text
                text = _b64decode_maybe(body)
        return text, html
    # Single part
    body_data = (payload.get('body') or {}).get('data')
    content = _b64decode_maybe(body_data) if isinstance(body_data, str) else ''
    if 'html' in mime:
        return _sanitize_string(None), _sanitize_string(content)
    return _sanitize_string(content), _sanitize_string(None)


def _epoch_ms_to_iso(ms_str: Any) -> str:
    try:
        ms = int(ms_str)
    except Exception:
        return datetime.now(tz=timezone.utc).isoformat().replace('+00:00', 'Z')
    dt = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
    return dt.isoformat().replace('+00:00', 'Z')


KNOWN_SYSTEM_LABELS = {
    'INBOX', 'SENT', 'DRAFTS', 'TRASH', 'SPAM', 'STARRED', 'IMPORTANT', 'ALL'
}


def _normalize_label_id(label_id: str) -> Optional[str]:
    if not label_id:
        return None
    if label_id.upper() == 'DRAFT':
        return 'DRAFTS'
    if label_id.upper() == 'ARCHIVE':
        # Drop ARCHIVE; new semantics rely on absence of INBOX only
        return None
    if label_id.upper() == 'UNREAD':
        return None  # converted into isRead flag
    return label_id


@dataclass
class EmailMessageOut:
    id: str
    threadId: str
    from_: str
    to: List[str]
    cc: Optional[List[str]]
    bcc: Optional[List[str]]
    subject: str
    date: str
    text: Optional[str]
    html: Optional[str]
    attachments: List[dict]
    labelIds: List[str]
    isRead: bool
    isStarred: bool
    isImportant: bool
    snoozeUntil: Optional[str]
    isDraftDeleted: bool

    def to_dict(self) -> dict:
        d = {
            'id': self.id,
            'threadId': self.threadId,
            'from': self.from_,
            'to': self.to,
            'subject': self.subject,
            'date': self.date,
            'labelIds': self.labelIds,
            'isRead': self.isRead,
            'isStarred': self.isStarred,
            'isImportant': self.isImportant,
        }
        if self.cc:
            d['cc'] = self.cc
        if self.bcc:
            d['bcc'] = self.bcc
        if self.text is not None and self.text != '':
            d['text'] = self.text
        if self.html is not None and self.html != '':
            d['html'] = self.html
        if self.attachments:
            d['attachments'] = self.attachments
        if self.snoozeUntil is not None:
            d['snoozeUntil'] = self.snoozeUntil
        if self.isDraftDeleted:
            d['isDraftDeleted'] = self.isDraftDeleted
        return d


def _extract_email_message(m: dict) -> EmailMessageOut:
    msg_id = str(m.get('id') or '')
    thread_id = str(m.get('threadId') or msg_id)
    label_ids_in = [str(x) for x in (m.get('labelIds') or []) if isinstance(x, str)]
    # Flags from labels
    is_unread = any((lid.upper() == 'UNREAD') for lid in label_ids_in)
    is_starred = any((lid.upper() == 'STARRED') for lid in label_ids_in)
    is_important = any((lid.upper() == 'IMPORTANT') for lid in label_ids_in)
    # Normalize labels set
    labels_norm = []
    for lid in label_ids_in:
        mapped = _normalize_label_id(lid)
        if mapped:
            labels_norm.append(mapped)

    payload = m.get('payload') or {}
    headers = _parse_headers(payload.get('headers') or [])
    from_raw = _sanitize_string(headers.get('from') or '') or ''
    to_raw = _sanitize_string(headers.get('to') or '') or ''
    cc_raw = _sanitize_string(headers.get('cc') or '') or ''
    bcc_raw = _sanitize_string(headers.get('bcc') or '') or ''
    subject = _sanitize_string(headers.get('subject') or '') or ''
    text, html = _extract_body(payload)

    # Attachments: best-effort extraction when present
    attachments: List[dict] = []
    def walk_for_attachments(p: dict) -> None:
        if not isinstance(p, dict):
            return
        filename = (p.get('filename') or '').strip()
        if filename:
            mime = (p.get('mimeType') or 'application/octet-stream')
            body = p.get('body') or {}
            data = body.get('data')
            size = body.get('size') or 0
            data_b64: str = ''
            if isinstance(data, str):
                # Ensure it's base64-encoded
                raw = _b64decode_maybe(data)
                # Re-encode as base64 to meet Attachment shape (dataBase64)
                data_b64 = base64.b64encode(raw.encode('utf-8')).decode('ascii')
            attachments.append({
                'id': f"att_{len(attachments)+1}",
                'filename': filename,
                'mimeType': mime,
                'dataBase64': data_b64,
                'size': int(size) if isinstance(size, (int, str)) and str(size).isdigit() else 0,
            })
        for child in (p.get('parts') or []):
            walk_for_attachments(child)

    walk_for_attachments(payload)

    # Snooze mapping: accept either "snoozeUntil" or "snoozedUntil" (matrices shape)
    def _read_snooze_until(source: dict) -> Optional[str]:
        v = source.get('snoozeUntil')
        if v is None:
            v = source.get('snoozedUntil')
        # Matrices often uses an object like { "__matricesDate": "..." }
        if isinstance(v, dict):
            for key in ('__matricesDate', 'iso', 'value', 'date'):
                s = v.get(key)
                if isinstance(s, str) and s.strip():
                    return s.strip()
            return None
        if isinstance(v, str):
            s = v.strip()
            if s:
                # If provided as epoch ms (digits), convert to ISO
                if s.isdigit():
                    return _epoch_ms_to_iso(s)
                return s
        return None

    snooze_until = _read_snooze_until(m)

    return EmailMessageOut(
        id=msg_id,
        threadId=thread_id,
        from_=_sanitize_string(from_raw) or '',
        to=_format_addresses(to_raw),
        cc=_format_addresses(cc_raw) or None,
        bcc=_format_addresses(bcc_raw) or None,
        subject=_sanitize_string(subject) or '',
        date=_epoch_ms_to_iso(m.get('internalDate')),
        text=_sanitize_string(text),
        html=_sanitize_string(html),
        attachments=attachments,
        labelIds=labels_norm,
        isRead=not is_unread,
        isStarred=is_starred,
        isImportant=is_important,
        snoozeUntil=snooze_until,
        isDraftDeleted=False,
    )


def _guess_account_email(messages: List[EmailMessageOut]) -> Optional[str]:
    # Heuristic: pick the address that appears most as sender for SENT or recipient for INBOX
    score: Dict[str, int] = defaultdict(int)
    for m in messages:
        labels = {lid.upper() for lid in m.labelIds}
        if 'SENT' in labels and m.from_:
            # Extract address inside <...> if present
            addr = m.from_.split('<')[-1].split('>')[0].strip() if '<' in m.from_ else m.from_.strip()
            score[addr] += 2
        if 'INBOX' in labels:
            for recip in m.to:
                addr = recip.split('<')[-1].split('>')[0].strip() if '<' in recip else recip.strip()
                score[addr] += 1
    if not score:
        return None
    return max(score.items(), key=lambda kv: kv[1])[0]


def _build_threads(messages: List[EmailMessageOut]) -> List[dict]:
    groups: Dict[str, List[EmailMessageOut]] = defaultdict(list)
    for m in messages:
        groups[m.threadId].append(m)
    threads: List[dict] = []
    for tid, msgs in groups.items():
        msgs_sorted = sorted(msgs, key=lambda x: x.date)
        subject = next((m.subject for m in msgs_sorted if m.subject.strip()), '')
        participants_set = []
        seen = set()
        for m in msgs_sorted:
            from_name = (m.from_.split('<')[0].strip() or m.from_).strip()
            if from_name and from_name not in seen:
                participants_set.append(from_name)
                seen.add(from_name)
            for t in m.to:
                to_name = (t.split('<')[0].strip() or t).strip()
                if to_name and to_name not in seen:
                    participants_set.append(to_name)
                    seen.add(to_name)
            if len(participants_set) >= 5:
                break
        last_activity = max((m.date for m in msgs_sorted), default=datetime.now(tz=timezone.utc).isoformat().replace('+00:00', 'Z'))
        is_starred = any(m.isStarred for m in msgs_sorted)
        threads.append({
            'id': tid,
            'subject': subject,
            'participants': participants_set[:5],
            'messageIds': [m.id for m in msgs_sorted],
            'lastActivity': last_activity,
            'isStarred': is_starred,
            'parentThreadId': tid,
        })
    return threads


def _collect_labels(messages: List[EmailMessageOut], input_labels: Optional[dict]) -> List[dict]:
    result: List[dict] = []
    # Seed core system labels (without ALL; store.ts will ensure ALL exists too)
    core = [
        { 'id': 'INBOX', 'name': 'INBOX', 'type': 'SYSTEM' },
        { 'id': 'SENT', 'name': 'SENT', 'type': 'SYSTEM' },
        { 'id': 'DRAFTS', 'name': 'DRAFTS', 'type': 'SYSTEM' },
        { 'id': 'TRASH', 'name': 'TRASH', 'type': 'SYSTEM' },
        { 'id': 'SPAM', 'name': 'SPAM', 'type': 'SYSTEM' },
        { 'id': 'STARRED', 'name': 'STARRED', 'type': 'SYSTEM' },
        { 'id': 'IMPORTANT', 'name': 'IMPORTANT', 'type': 'SYSTEM' },
        { 'id': 'ALL', 'name': 'ALL MAIL', 'type': 'SYSTEM' },
    ]
    result.extend(core)

    known_ids = {label['id'] for label in result}
    # From input labels map (when present)
    if isinstance(input_labels, dict):
        for lid, meta in input_labels.items():
            if lid.upper() == 'DRAFT':
                lid = 'DRAFTS'
            if lid.upper() == 'UNREAD':
                continue
            if lid in known_ids:
                continue
            ltype = 'USER'
            # If the input label meta declares a system type and it's one we don't explicitly handle,
            # still treat it as USER for our environment
            name = meta.get('name') if isinstance(meta, dict) else lid
            # No direct color in our schema; ignore color metadata
            result.append({ 'id': lid, 'name': name or lid, 'type': ltype })
            known_ids.add(lid)

    # From messages
    for m in messages:
        for lid in m.labelIds:
            if lid.upper() in {'UNREAD'}:
                continue
            if lid.upper() == 'DRAFT':
                lid = 'DRAFTS'
            if lid not in known_ids:
                result.append({ 'id': lid, 'name': lid, 'type': 'USER' })
                known_ids.add(lid)
    return result


def _convert_gmail_like_state(state_obj: dict) -> dict:
    s = _unwrap_gmail_state(state_obj)
    users = s.get('users') or {}
    messages_map = s.get('messages') or {}
    labels_map = s.get('labels') or {}

    # Extract and convert messages
    messages_out: List[EmailMessageOut] = []
    if isinstance(messages_map, dict):
        for m in messages_map.values():
            try:
                messages_out.append(_extract_email_message(m))
            except Exception:
                # Skip malformed message
                continue

    # Build threads, labels and settings
    threads = _build_threads(messages_out)
    labels = _collect_labels(messages_out, labels_map)
    me_email = _guess_account_email(messages_out)
    me_name = None
    if me_email and isinstance(users, dict):
        urec = users.get(me_email)
        if isinstance(urec, dict):
            nm = urec.get('name')
            if isinstance(nm, str) and nm.strip():
                me_name = nm.strip()

    settings = {
        'displayName': me_name or 'User',
        'signature': '',
    }
    if me_email:
        settings['email'] = me_email

    # Build contacts directory from users map when present
    contacts: Dict[str, Dict[str, str]] = {}
    if isinstance(users, dict):
        for key, meta in users.items():
            try:
                email = ''
                if isinstance(meta, dict) and isinstance(meta.get('email'), str):
                    email = meta.get('email') or ''
                elif isinstance(key, str):
                    email = key
                email = (email or '').strip().lower()
                if not email or '@' not in email:
                    continue
                name = None
                if isinstance(meta, dict) and isinstance(meta.get('name'), str) and meta.get('name').strip():
                    name = meta.get('name').strip()
                rec: Dict[str, str] = {'email': email}
                if name:
                    rec['name'] = name  # type: ignore
                contacts[email] = rec
            except Exception:
                continue

    return {
        'messages': [m.to_dict() for m in messages_out],
        'threads': threads,
        'labels': labels,
        'settings': settings,
        # Preserve directory to improve typeahead and search in the app
        'contacts': contacts,
        # Also include legacy 'users' for downstream consumers that expect it
        'users': contacts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tasks-file', default='/Users/kavya/code/webshites/matrices-data-extraction/tasks_states_and_metadata.json', help='Path to tasks_states_and_metadata.json')
    parser.add_argument('--index', type=int, default=24, help='1-indexed ready task position')
    parser.add_argument('--task-file', help='Path to a single task JSON (optional)')
    parser.add_argument('--stdin-task', action='store_true', help='Read a single task object from stdin')
    parser.add_argument('--pretty', action='store_true', help='Pretty-print output JSON')
    parser.add_argument('--out-initial', help='Write converted initial state to this file')
    parser.add_argument('--out-expected', help='Write converted expected state to this file')

    args = parser.parse_args()

    if args.stdin_task:
        task = _read_stdin_json()
    elif args.task_file:
        task = _read_json_file(args.task_file)
    else:
        if not os.path.exists(args.tasks_file):
            print(f"Error: tasks file not found: {args.tasks_file}", file=sys.stderr)
            return 2
        task = _load_task_from_tasks_file(args.tasks_file, args.index)

    # Task shape: expects keys initial_state and expected_state
    if 'initial_state' not in task or 'expected_state' not in task:
        print('Error: task does not contain initial_state and expected_state', file=sys.stderr)
        return 1

    initial_conv = _convert_gmail_like_state(task['initial_state'])
    expected_conv = _convert_gmail_like_state(task['expected_state'])

    # Output
    if args.out_initial:
        with open(args.out_initial, 'w', encoding='utf-8') as f:
            json.dump(initial_conv, f, ensure_ascii=False, indent=2 if args.pretty else None)
            f.write('\n')
    if args.out_expected:
        with open(args.out_expected, 'w', encoding='utf-8') as f:
            json.dump(expected_conv, f, ensure_ascii=False, indent=2 if args.pretty else None)
            f.write('\n')

    if not args.out_initial and not args.out_expected:
        combined = { 'initial': initial_conv, 'expected': expected_conv }
        sys.stdout.write(json.dumps(combined, ensure_ascii=False, indent=2 if args.pretty else None))
        sys.stdout.write('\n')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())


