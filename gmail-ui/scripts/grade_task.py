#!/usr/bin/env python3
"""
Gmail task grader: compare initial→expected against initial→actual and decide
PASS/FAIL using equality or subset logic, while showing pinpointed differences.

Key ideas:
- Produce atomic, human-readable change tokens (e.g., "message <id> add label STARRED",
  "message <id> set isRead True", "add message {payload}") rather than dumping whole objects.
- Ignore nondeterministic fields (e.g., message dates, colors) and derived labels like ALL.
- Accept success if expected changes are a subset of actual changes (extras allowed).

How to use:
   python containers/gmail/scripts/grade_task.py \
     --jsonl /Users/kavya/code/webshites/data/gmail/ready_tasks_converted.jsonl --index 24 \
     [--actual /path/actual.json]
   - Initial/expected are read from the selected JSONL record (supports --index or --id).
   - If --actual is omitted, the script will GET the current app state from --url/--path.

Output management:
- The script always writes four files under data/gmail/task_[ID]/ when an ID is known
  from JSONL: initial.json, expected.json, actual.json, grade.json (diff/result).
- If no task ID is available, outputs go under data/gmail/task_manual/.
- Passing --output DIR writes the four files under DIR instead of the default
  location (DIR will be created if missing).

Other examples:
  # Strict equality (no extras) with summary to stdout
  python containers/gmail/scripts/grade_task.py --jsonl ... --index 24 --strict

  # Write JSON diff output to a specific file (it will also be saved under task_[ID]/grade.json)
  python containers/gmail/scripts/grade_task.py --jsonl ... --index 24 --output /tmp/grade_task_diff.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from typing import Any, Iterable

# ----------------------------- Normalization ---------------------------------


def _ensure_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _normalize_addresses(addresses: Iterable[str]) -> list[str]:
    seen = set()
    result: list[str] = []
    for a in addresses:
        if not isinstance(a, str):
            continue
        s = a.strip()
        if not s:
            continue
        # Prefer bare email when present; otherwise keep normalized literal (case-insensitive)
        email = None
        if "<" in s and ">" in s:
            import re
            m = re.search(r"<([^>]+)>", s)
            if m:
                email = m.group(1).strip().lower()
        if email is None and "@" in s:
            email = s.strip().lower()
        key = email if email else " ".join(s.split()).lower()
        if key and key not in seen:
            seen.add(key)
            result.append(key)
    result.sort()
    return result


def _html_to_text(html: Any) -> str:
    if not isinstance(html, str) or not html:
        return ""
    try:
        import re
        from html import unescape
        s = html
        # Normalize common line breaks
        s = re.sub(r"<\s*br\s*/?\s*>", "\n", s, flags=re.IGNORECASE)
        s = re.sub(r"<\s*/\s*p\s*>", "\n\n", s, flags=re.IGNORECASE)
        # Strip all tags
        s = re.sub(r"<[^>]+>", "", s)
        # Unescape entities
        s = unescape(s)
        # Collapse excessive whitespace
        s = re.sub(r"\s+", " ", s)
        return s.strip()
    except Exception:
        return ""


def _normalize_participants(participants: Iterable[str]) -> list[str]:
    seen = set()
    result: list[str] = []
    for p in participants:
        if not isinstance(p, str):
            continue
        key = p.strip()
        if key and key not in seen:
            seen.add(key)
            result.append(key)
    result.sort()
    return result


def _normalize_ws(text: Any) -> str:
    if not isinstance(text, str):
        return ""
    import re

    # Collapse all whitespace (including newlines and tabs) to single spaces
    s = re.sub(r"\s+", " ", text).strip()
    # Normalize leading-zero hour times: "07:00 PM" -> "7:00 PM", "09:05" -> "9:05"
    s = re.sub(r"(?<!\d)0([1-9]):([0-5]\d)\s*([AaPp][Mm])\b", r"\1:\2 \3", s)
    s = re.sub(r"(?<!\d)0([0-9]):([0-5]\d)\b", r"\1:\2", s)
    return s


def _canonicalize_label_name(name: Any) -> str:
    if not isinstance(name, str):
        return ""
    # Collapse whitespace and uppercase for stable matching across states
    collapsed = " ".join(name.split())
    return collapsed.strip().upper()


def _normalize_label_ids(labels: Iterable[str]) -> list[str]:
    # Uppercase, unique, drop derived 'ALL' label
    seen = set()
    result: list[str] = []
    for label_value in labels:
        if not isinstance(label_value, str):
            continue
        up = label_value.strip().upper()
        if not up or up == "ALL":
            continue
        if up not in seen:
            seen.add(up)
            result.append(up)
    result.sort()
    return result


def _pick(d: dict[str, Any], keys: Iterable[str]) -> dict[str, Any]:
    return {k: d.get(k) for k in keys}


def _normalize_message(raw: dict[str, Any]) -> dict[str, Any]:
    # Keep only fields we care about for grading; ignore date/id in signature but retain id for identity
    def _extract_email(value: Any) -> str:
        if not isinstance(value, str):
            return ""
        s = value.strip()
        # Prefer address inside angle brackets if present
        if "<" in s and ">" in s:
            import re
            m = re.search(r"<([^>]+)>", s)
            if m:
                return m.group(1).strip().lower()
        # If it looks like an email, lowercase it; else return as-is lowercased
        return s.lower()
    msg = {
        "id": raw.get("id"),
        "threadId": raw.get("threadId"),
        "replyToId": raw.get("replyToId"),
        # Normalize 'from' to bare email (lowercased) so "Name <email>" equals "email"
        "from": _extract_email(raw.get("from")),
        "to": _normalize_addresses(_ensure_list(raw.get("to"))),
        "cc": _normalize_addresses(_ensure_list(raw.get("cc"))),
        "bcc": _normalize_addresses(_ensure_list(raw.get("bcc"))),
        "subject": raw.get("subject") or "",
        # Prefer provided text; if absent, derive from HTML for robust body comparisons
        "text": (raw.get("text") or _html_to_text(raw.get("html")) or ""),
        "html": raw.get("html"),
        "date": raw.get("date"),
        "labelIds": _normalize_label_ids(_ensure_list(raw.get("labelIds"))),
        "isRead": bool(raw.get("isRead", False)),
        "isStarred": bool(raw.get("isStarred", False)),
        "isImportant": bool(raw.get("isImportant", False)),
        "snoozeUntil": raw.get("snoozeUntil"),
        # ignore: attachments, size estimates, etc.
    }
    return msg


def _normalize_thread(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": raw.get("id"),
        "subject": raw.get("subject") or "",
        "isStarred": bool(raw.get("isStarred", False)),
        "participants": _normalize_participants(_ensure_list(raw.get("participants"))),
        # ignore: messageIds (derived)
    }


def _normalize_label(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(raw.get("id")),
        "name": str(raw.get("name")),
        "type": "USER" if raw.get("type") == "USER" else "SYSTEM",
        # ignore: color (auto-filled), visibilities
    }


def canonicalize_state(state: dict[str, Any]) -> dict[str, Any]:
    # 1) Canonicalize labels first to build an id->canonical map so messages can map labelIds
    labels_by_canonical: dict[str, dict[str, Any]] = {}
    label_id_to_canonical: dict[str, str] = {}
    for label_dict in _ensure_list(state.get("labels")):
        if not isinstance(label_dict, dict):
            continue
        nl = _normalize_label(label_dict)
        raw_id = nl.get("id")
        if not isinstance(raw_id, str) or not raw_id:
            continue
        up_id = raw_id.strip().upper()
        ltype = nl.get("type")
        if ltype == "USER":
            cname = _canonicalize_label_name(nl.get("name")) or up_id
            canonical_id = cname
        else:
            canonical_id = up_id
        label_id_to_canonical[up_id] = canonical_id
        # Store registry keyed by canonical id
        labels_by_canonical[canonical_id] = {
            "id": canonical_id,
            "name": nl.get("name"),
            "type": "USER" if ltype == "USER" else "SYSTEM",
        }

    # 2) Canonicalize messages, mapping labelIds to canonical ids
    messages_by_id: dict[str, dict[str, Any]] = {}
    for m in _ensure_list(state.get("messages")):
        if not isinstance(m, dict):
            continue
        nm = _normalize_message(m)
        # Map message labelIds using the registry mapping
        mapped_labels: list[str] = []
        for lid in nm.get("labelIds", []):
            up = str(lid).strip().upper()
            if up == "ALL":
                continue
            mapped_labels.append(label_id_to_canonical.get(up, up))
        # unique + sort
        if mapped_labels:
            ml_set = sorted(set(mapped_labels))
        else:
            ml_set = []
        nm["labelIds"] = ml_set

        mid = nm.get("id")
        if isinstance(mid, str) and mid:
            messages_by_id[mid] = nm

    # 3) Canonicalize threads (participants already normalized in _normalize_thread)
    threads_by_id: dict[str, dict[str, Any]] = {}
    for t in _ensure_list(state.get("threads")):
        if not isinstance(t, dict):
            continue
        nt = _normalize_thread(t)
        tid = nt.get("id")
        if isinstance(tid, str) and tid:
            threads_by_id[tid] = nt

    # 4) Settings
    settings = state.get("settings") or {}
    if not isinstance(settings, dict):
        settings = {}
    settings = _pick(settings, ["displayName", "signature", "email"])  # email is optional

    return {
        "messagesById": messages_by_id,
        "threadsById": threads_by_id,
        "labelsById": labels_by_canonical,
        "settings": settings,
    }


# -------------------------- Tokenization (diff) -------------------------------

Token = tuple[Any, ...]


def _msg_signature_payload(msg: dict[str, Any]) -> dict[str, Any]:
    """Return the normalized payload used for message signature/diff previews.

    Intentionally excludes id/date and attachments to avoid nondeterminism.
    """
    payload: dict[str, Any] = {
        "replyToId": msg.get("replyToId"),
        "from": msg.get("from"),
        "to": msg.get("to"),
        "cc": msg.get("cc"),
        "bcc": msg.get("bcc"),
        "subject": msg.get("subject"),
        # Treat None and empty as equivalent by normalizing earlier; keep string here
        "text": msg.get("text"),
        "hasHtml": bool(msg.get("html")),
        "labelIds": msg.get("labelIds"),
    }
    # Include threadId only when this is a reply/forward (replyToId present).
    # For a brand new compose (no replyToId), allow threadId to differ and omit it from the signature.
    if msg.get("replyToId"):
        payload["threadId"] = msg.get("threadId")
    return payload


# No digesting of message payloads; include a readable JSON payload directly in tokens.


def _compare_scalar(
    field: str, before: Any, after: Any, owner_kind: str, owner_id: str, out: set[Token]
) -> None:
    if before != after:
        # Include both before and after for clarity
        out.add(("SET", owner_kind, owner_id, field, before, after))


def _compare_set(
    field: str,
    before: Iterable[Any],
    after: Iterable[Any],
    owner_kind: str,
    owner_id: str,
    out: set[Token],
) -> None:
    s_before = set(before or [])
    s_after = set(after or [])
    for v in sorted(s_after - s_before):
        out.add(("ADD", owner_kind, owner_id, field, v))
    for v in sorted(s_before - s_after):
        out.add(("REMOVE", owner_kind, owner_id, field, v))


def compute_change_tokens(initial: dict[str, Any], final: dict[str, Any]) -> set[Token]:
    tokens: set[Token] = set()

    # Messages
    m0: dict[str, dict[str, Any]] = initial.get("messagesById", {})
    m1: dict[str, dict[str, Any]] = final.get("messagesById", {})
    ids0 = set(m0.keys())
    ids1 = set(m1.keys())

    # Updates for existing messages
    for mid in sorted(ids0 & ids1):
        b = m0[mid]
        a = m1[mid]
        # Labels (set diff, exclude ALL handled in normalization)
        _compare_set(
            "labelIds", b.get("labelIds", []), a.get("labelIds", []), "message", mid, tokens
        )
        # Flags & fields
        _compare_scalar("isRead", b.get("isRead"), a.get("isRead"), "message", mid, tokens)
        _compare_scalar("isStarred", b.get("isStarred"), a.get("isStarred"), "message", mid, tokens)
        _compare_scalar(
            "isImportant", b.get("isImportant"), a.get("isImportant"), "message", mid, tokens
        )
        _compare_scalar(
            "snoozeUntil", b.get("snoozeUntil"), a.get("snoozeUntil"), "message", mid, tokens
        )
        _compare_scalar("date", b.get("date"), a.get("date"), "message", mid, tokens)
        _compare_scalar("subject", b.get("subject"), a.get("subject"), "message", mid, tokens)
        _compare_scalar("text", b.get("text"), a.get("text"), "message", mid, tokens)
        # Recipients as sets
        _compare_set("to", b.get("to", []), a.get("to", []), "message", mid, tokens)
        _compare_set("cc", b.get("cc", []), a.get("cc", []), "message", mid, tokens)
        _compare_set("bcc", b.get("bcc", []), a.get("bcc", []), "message", mid, tokens)

    # Additions
    for mid in sorted(ids1 - ids0):
        a = m1[mid]
        payload_pretty = json.dumps(_msg_signature_payload(a), sort_keys=True, ensure_ascii=False)
        tokens.add(("ADD_MESSAGE", payload_pretty))

    # Removals
    for mid in sorted(ids0 - ids1):
        b = m0[mid]
        payload_pretty = json.dumps(_msg_signature_payload(b), sort_keys=True, ensure_ascii=False)
        tokens.add(("REMOVE_MESSAGE", payload_pretty))

    # Threads (limited fields)
    t0: dict[str, dict[str, Any]] = initial.get("threadsById", {})
    t1: dict[str, dict[str, Any]] = final.get("threadsById", {})
    tids0 = set(t0.keys())
    tids1 = set(t1.keys())
    for tid in sorted(tids0 & tids1):
        b = t0[tid]
        a = t1[tid]
        _compare_scalar("isStarred", b.get("isStarred"), a.get("isStarred"), "thread", tid, tokens)
        _compare_scalar("subject", b.get("subject"), a.get("subject"), "thread", tid, tokens)
        _compare_set(
            "participants",
            b.get("participants", []),
            a.get("participants", []),
            "thread",
            tid,
            tokens,
        )
    for tid in sorted(tids1 - tids0):
        a = t1[tid]
        tokens.add(("ADD_THREAD", a.get("subject", "")))
    for tid in sorted(tids0 - tids1):
        b = t0[tid]
        tokens.add(("REMOVE_THREAD", b.get("subject", "")))

    # Labels registry (id, name, type) — ignore color
    l0: dict[str, dict[str, Any]] = initial.get("labelsById", {})
    l1: dict[str, dict[str, Any]] = final.get("labelsById", {})
    lids0 = set(l0.keys())
    lids1 = set(l1.keys())
    for lid in sorted(lids0 & lids1):
        b = l0[lid]
        a = l1[lid]
        _compare_scalar("name", b.get("name"), a.get("name"), "label", lid, tokens)
        _compare_scalar("type", b.get("type"), a.get("type"), "label", lid, tokens)
    for lid in sorted(lids1 - lids0):
        a = l1[lid]
        tokens.add(("ADD_LABEL_DEF", a.get("id"), a.get("name"), a.get("type")))
    for lid in sorted(lids0 - lids1):
        b = l0[lid]
        tokens.add(("REMOVE_LABEL_DEF", b.get("id"), b.get("name"), b.get("type")))

    # Settings (displayName, signature, email)
    s0 = initial.get("settings", {}) or {}
    s1 = final.get("settings", {}) or {}
    for key in ["displayName", "signature", "email"]:
        _compare_scalar(key, s0.get(key), s1.get(key), "settings", "root", tokens)

    return tokens


# ------------------------------- Rendering -----------------------------------

def _render_token(t: Token) -> str:
    op = t[0]
    if op == "SET":
        # Accept legacy 5-tuple or new 6-tuple
        if len(t) >= 6:
            _, kind, oid, field, before, after = t
            return (
                f"{kind} {oid} set {field} "
                f"{json.dumps(before, ensure_ascii=False)} -> {json.dumps(after, ensure_ascii=False)}"
            )
        else:
            _, kind, oid, field, val = t
            return f"{kind} {oid} set {field} -> {json.dumps(val, ensure_ascii=False)}"
    if op == "ADD":
        _, kind, oid, field, val = t
        return f"{kind} {oid} add {field} {json.dumps(val, ensure_ascii=False)}"
    if op == "REMOVE":
        _, kind, oid, field, val = t
        return f"{kind} {oid} remove {field} {json.dumps(val, ensure_ascii=False)}"
    if op == "ADD_MESSAGE":
        # Token shape: ("ADD_MESSAGE", payload_json)
        def _compact_payload_json(s: str) -> str:
            try:
                obj = json.loads(s)
            except Exception:
                return s
            compact: dict[str, Any] = {}
            # Always include identity-ish fields when present
            if obj.get("replyToId"):
                compact["replyToId"] = obj.get("replyToId")
            if obj.get("from"):
                compact["from"] = obj.get("from")
            if obj.get("subject"):
                compact["subject"] = obj.get("subject")
            # Recipients: include only when non-empty
            for fld in ["to", "cc", "bcc"]:
                vals = obj.get(fld) or []
                if isinstance(vals, list) and len(vals) > 0:
                    compact[fld] = vals
            # Body: include non-empty text; always include hasHtml when True
            if obj.get("text"):
                compact["text"] = obj.get("text")
            if bool(obj.get("hasHtml")):
                compact["hasHtml"] = True
            # Labels: include when non-empty
            lids = obj.get("labelIds") or []
            if isinstance(lids, list) and len(lids) > 0:
                compact["labelIds"] = lids
            # Thread id is only meaningful for replies
            if obj.get("replyToId") and obj.get("threadId"):
                compact["threadId"] = obj.get("threadId")
            try:
                return json.dumps(compact, sort_keys=True, ensure_ascii=False)
            except Exception:
                return s
        if len(t) >= 2:
            return f"add message {_compact_payload_json(t[1])}"
        return "add message"
    if op == "REMOVE_MESSAGE":
        # Token shape: ("REMOVE_MESSAGE", payload_json)
        def _compact_payload_json(s: str) -> str:
            try:
                obj = json.loads(s)
            except Exception:
                return s
            compact: dict[str, Any] = {}
            if obj.get("from"):
                compact["from"] = obj.get("from")
            if obj.get("subject"):
                compact["subject"] = obj.get("subject")
            for fld in ["to", "cc", "bcc"]:
                vals = obj.get(fld) or []
                if isinstance(vals, list) and len(vals) > 0:
                    compact[fld] = vals
            if obj.get("text"):
                compact["text"] = obj.get("text")
            if bool(obj.get("hasHtml")):
                compact["hasHtml"] = True
            lids = obj.get("labelIds") or []
            if isinstance(lids, list) and len(lids) > 0:
                compact["labelIds"] = lids
            try:
                return json.dumps(compact, sort_keys=True, ensure_ascii=False)
            except Exception:
                return s
        if len(t) >= 2:
            return f"remove message {_compact_payload_json(t[1])}"
        return "remove message"
    if op == "ADD_THREAD":
        return f"add thread subject={json.dumps(t[1], ensure_ascii=False)}"
    if op == "REMOVE_THREAD":
        return f"remove thread subject={json.dumps(t[1], ensure_ascii=False)}"
    if op == "ADD_LABEL_DEF":
        _, lid, name, ltype = t
        return f"add label def id={lid} name={json.dumps(name, ensure_ascii=False)} type={ltype}"
    if op == "REMOVE_LABEL_DEF":
        _, lid, name, ltype = t
        return f"remove label def id={lid} name={json.dumps(name, ensure_ascii=False)} type={ltype}"
    return " ".join(map(str, t))


# ---------------------------- Diff building API -------------------------------


def _parse_payload_json(s: str) -> dict[str, Any]:
    try:
        return json.loads(s)
    except Exception:
        return {}


def _key_for_add_message(payload: dict[str, Any]) -> tuple[Any, ...]:
    to_norm = sorted(payload.get("to") or []) if isinstance(payload.get("to"), list) else []
    cc_norm = sorted(payload.get("cc") or []) if isinstance(payload.get("cc"), list) else []
    bcc_norm = sorted(payload.get("bcc") or []) if isinstance(payload.get("bcc"), list) else []
    return (
        payload.get("replyToId"),
        payload.get("from"),
        payload.get("subject"),
        tuple(to_norm),
        tuple(cc_norm),
        tuple(bcc_norm),
        bool(payload.get("hasHtml")),
    )


def _diff_payloads(exp: dict[str, Any], act: dict[str, Any]) -> dict[str, Any]:
    diff: dict[str, Any] = {}
    # Recipients and labels
    for fld in ["to", "cc", "bcc", "labelIds"]:
        e_vals = exp.get(fld) or []
        a_vals = act.get(fld) or []
        if not isinstance(e_vals, list):
            e_vals = []
        if not isinstance(a_vals, list):
            a_vals = []
        e_set = set(e_vals)
        a_set = set(a_vals)
        added = sorted(a_set - e_set)
        removed = sorted(e_set - a_set)
        if added or removed:
            diff[fld] = {"added": added, "removed": removed}
    # Subject
    if (exp.get("subject") or "") != (act.get("subject") or ""):
        diff["subject"] = {
            "expected": exp.get("subject") or "",
            "actual": act.get("subject") or "",
        }
    # Text body with whitespace-equivalence flag
    e_text = exp.get("text") or ""
    a_text = act.get("text") or ""
    eq_ign_ws = _normalize_ws(e_text) == _normalize_ws(a_text)
    if e_text != a_text:

        def _shorten(s: str, n: int = 160) -> str:
            return s if len(s) <= n else s[: n - 1] + "…"

        diff["text"] = {
            "expectedLen": len(e_text),
            "actualLen": len(a_text),
            "expectedSnippet": _shorten(e_text),
            "actualSnippet": _shorten(a_text),
            "equivalentIgnoringWhitespace": bool(eq_ign_ws),
        }
    # HTML normalized whitespace comparison
    e_html = exp.get("html") or ""
    a_html = act.get("html") or ""
    if isinstance(e_html, str) or isinstance(a_html, str):
        ne = _normalize_ws(e_html)
        na = _normalize_ws(a_html)
        if ne != na:
            diff["html"] = {
                "expectedLen": len(e_html) if isinstance(e_html, str) else 0,
                "actualLen": len(a_html) if isinstance(a_html, str) else 0,
            }
    # HTML presence flag
    if bool(exp.get("hasHtml")) != bool(act.get("hasHtml")):
        diff["hasHtml"] = {
            "expected": bool(exp.get("hasHtml")),
            "actual": bool(act.get("hasHtml")),
        }
    return diff


def compute_human_readable_diff(
    expected_tokens: set[Token], actual_tokens: set[Token]
) -> dict[str, Any]:
    """Build the human-readable diff between expected and actual token sets.

    Returns a dict with keys: expectedOnly, actualOnly, matchedCount, nonBlockingCounts.
    Non-blocking entries are annotated for whitespace-only text differences.
    """
    missing = sorted(expected_tokens - actual_tokens)
    unexpected_all = sorted(actual_tokens - expected_tokens)

    missing_entries: list[dict[str, Any]] = [
        {"token": list(t), "pretty": _render_token(t)} for t in missing
    ]
    unexpected_entries: list[dict[str, Any]] = [
        {"token": list(t), "pretty": _render_token(t)} for t in unexpected_all
    ]

    # Index ADD_MESSAGE in missing/actual-only by pairing key
    exp_add_map: dict[tuple[Any, ...], tuple[int, dict[str, Any]]] = {}
    act_add_map: dict[tuple[Any, ...], tuple[int, dict[str, Any]]] = {}
    for idx, entry in enumerate(missing_entries):
        tok = tuple(entry["token"])  # type: ignore[assignment]
        if len(tok) >= 2 and tok[0] == "ADD_MESSAGE":
            payload = _parse_payload_json(tok[1])
            exp_add_map[_key_for_add_message(payload)] = (idx, payload)
    for idx, entry in enumerate(unexpected_entries):
        tok = tuple(entry["token"])  # type: ignore[assignment]
        if len(tok) >= 2 and tok[0] == "ADD_MESSAGE":
            payload = _parse_payload_json(tok[1])
            act_add_map[_key_for_add_message(payload)] = (idx, payload)

    # Attach field-level diffs where we find pairs
    for key, (e_idx, e_payload) in exp_add_map.items():
        if key in act_add_map:
            a_idx, a_payload = act_add_map[key]
            df = _diff_payloads(e_payload, a_payload)
            if df:
                missing_entries[e_idx]["diffFields"] = df
                unexpected_entries[a_idx]["diffFields"] = df

    # Mark non-blocking pairs for ADD_MESSAGE when only text differs and it's equivalent ignoring whitespace
    for key, (e_idx, _e_payload) in exp_add_map.items():
        if key in act_add_map:
            a_idx, _a_payload = act_add_map[key]
            df = missing_entries[e_idx].get("diffFields") or {}
            other_keys = [k for k in df.keys() if k != "text"]
            text_ok = (
                bool(df.get("text", {}).get("equivalentIgnoringWhitespace"))
                if df.get("text")
                else False
            )
            if text_ok and len(other_keys) == 0:
                missing_entries[e_idx]["nonBlocking"] = True
                unexpected_entries[a_idx]["nonBlocking"] = True

    # Also mark SET text diffs as non-blocking when only whitespace differs
    def _pair_set_text(
        entries: list[dict[str, Any]],
    ) -> dict[tuple[str, str, str], tuple[int, tuple[Any, ...]]]:
        m: dict[tuple[str, str, str], tuple[int, tuple[Any, ...]]] = {}
        for idx, entry in enumerate(entries):
            tok = tuple(entry.get("token") or [])
            if len(tok) >= 6 and tok[0] == "SET" and tok[3] == "text":
                kind = str(tok[1])
                oid = str(tok[2])
                field = str(tok[3])
                m[(kind, oid, field)] = (idx, tok)
        return m
    exp_set_map = _pair_set_text(missing_entries)
    act_set_map = _pair_set_text(unexpected_entries)
    for k, (e_idx, e_tok) in exp_set_map.items():
        if k in act_set_map:
            a_idx, a_tok = act_set_map[k]
            e_after = e_tok[5]
            a_after = a_tok[5]
            if _normalize_ws(e_after) == _normalize_ws(a_after):
                missing_entries[e_idx]["nonBlocking"] = True
                unexpected_entries[a_idx]["nonBlocking"] = True

    matched_count = len(expected_tokens & actual_tokens)
    nonblocking_missing = len([e for e in missing_entries if e.get("nonBlocking")])
    nonblocking_unexpected = len([e for e in unexpected_entries if e.get("nonBlocking")])

    return {
        "expectedOnly": missing_entries,
        "actualOnly": unexpected_entries,
        "matchedCount": matched_count,
        "nonBlockingCounts": {
            "expectedOnly": nonblocking_missing,
            "actualOnly": nonblocking_unexpected,
        },
    }


# ------------------------- Verdict calculation API ----------------------------


def compute_blocking_verdict_from_tokens(
    expected_tokens: set[Token],
    actual_tokens: set[Token],
    strict: bool = False,
) -> tuple[bool, dict[str, Any], int, int]:
    """Compute PASS/FAIL using blocking-only semantics.

    Returns (passed, diff_obj, blocking_missing_count, blocking_unexpected_count).
    """
    diff_obj = compute_human_readable_diff(expected_tokens, actual_tokens)
    missing_entries = list(diff_obj.get("expectedOnly") or [])
    unexpected_entries = list(diff_obj.get("actualOnly") or [])
    blocking_missing = [e for e in missing_entries if not e.get("nonBlocking")]
    blocking_unexpected = [e for e in unexpected_entries if not e.get("nonBlocking")]
    if strict:
        passed = len(blocking_missing) == 0 and len(blocking_unexpected) == 0
    else:
        passed = len(blocking_missing) == 0
    return (
        bool(passed),
        diff_obj,
        int(len(blocking_missing)),
        int(len(blocking_unexpected)),
    )


# --------------------------------- CLI ---------------------------------------


def _load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _read_jsonl_record_by_index(jsonl_path: str, index_1_based: int) -> dict | None:
    if index_1_based <= 0:
        raise ValueError("index must be >= 1")
    with open(jsonl_path, "r", encoding="utf-8") as f:
        idx = 0
        for line in f:
            s = line.strip()
            if not s:
                continue
            idx += 1
            if idx == index_1_based:
                return json.loads(s)
    return None


def _read_jsonl_record_by_id(jsonl_path: str, task_id: str) -> dict | None:
    tid = str(task_id)
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except json.JSONDecodeError:
                continue
            obj_id = obj.get("id")
            if obj_id is None:
                md = obj.get("metadata") if isinstance(obj, dict) else None
                if isinstance(md, dict):
                    obj_id = md.get("id")
            if obj_id is not None and str(obj_id) == tid:
                return obj
    return None


def _extract_states_from_record(obj: dict) -> tuple[str | None, dict | None, dict | None]:
    """
    Returns (task_id, initial_state, expected_state). Supports both new and legacy shapes.
    """
    if not isinstance(obj, dict):
        return None, None, None
    task_id: str | None = None
    md = obj.get("metadata") if isinstance(obj, dict) else None
    if isinstance(md, dict):
        tid = md.get("id")
        task_id = str(tid) if tid is not None else None
        initial = md.get("initial")
        expected = md.get("expected")
    else:
        task_id = str(obj.get("id")) if obj.get("id") is not None else None
        initial = obj.get("initial")
        expected = obj.get("expected")
    return (
        task_id,
        initial if isinstance(initial, dict) else None,
        expected if isinstance(expected, dict) else None,
    )


def _http_get_json(url: str, path: str) -> dict[str, Any]:
    endpoint = f"{url.rstrip('/')}{path}"
    req = urllib.request.Request(endpoint, method="GET")
    req.add_header("accept", "application/json")
    with urllib.request.urlopen(req) as resp:
        data = resp.read()
        return json.loads(data.decode("utf-8", errors="replace"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)

    # JSONL + selector (required)
    ap.add_argument(
        "--actual", help="Path to actual final state JSON; if omitted, GET from --url/--path"
    )
    ap.add_argument(
        "--jsonl",
        default="/Users/kavya/code/webshites/data/gmail/ready_tasks_converted.jsonl",
        help="Converted tasks JSONL path",
    )
    sel = ap.add_mutually_exclusive_group()
    sel.add_argument("--index", type=int, help="1-indexed position in the JSONL file")
    sel.add_argument("--id", help="Task id to select from JSONL")

    # Actual retrieval via API if --actual not provided
    ap.add_argument(
        "--url",
        default="http://localhost:3000",
        help="Base URL of the running env for GET /api/state",
    )
    ap.add_argument("--path", default="/api/state", help="GET path for state endpoint")
    ap.add_argument(
        "--print-actual",
        action="store_true",
        help="Also print the resolved actual state JSON to stdout",
    )
    ap.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed human-readable diff (missing/unexpected) to stdout",
    )

    # Grading options and outputs
    ap.add_argument("--strict", action="store_true", help="Require exact match (no extra changes)")
    ap.add_argument(
        "--output",
        "-o",
        help="Output directory for artifacts (initial/expected/actual/grade). If omitted, defaults to data/gmail/task_[ID]/",
    )

    args = ap.parse_args()

    # Resolve initial/expected/ID from JSONL selection
    selected_task_id: str | None = None
    initial_state: dict[str, Any] | None = None
    expected_state: dict[str, Any] | None = None

    # Require selection via JSONL
    record: dict | None = None
    if args.index is not None:
        record = _read_jsonl_record_by_index(args.jsonl, args.index)
    elif args.id is not None:
        record = _read_jsonl_record_by_id(args.jsonl, args.id)
    else:
        print("Error: provide --index or --id with --jsonl", file=sys.stderr)
        return 2

    if record is None:
        print("Error: could not locate the selected record in JSONL", file=sys.stderr)
        return 2
    selected_task_id, initial_state, expected_state = _extract_states_from_record(record)
    if initial_state is None or expected_state is None:
        print("Error: selected record missing initial/expected states", file=sys.stderr)
        return 2

    # Resolve actual state: file takes precedence, else GET
    if args.actual:
        actual_state = _load_json(args.actual)
    else:
        try:
            actual_state = _http_get_json(args.url, args.path)
        except Exception as e:
            print(
                f"Error: failed to GET actual state from {args.url}{args.path}: {e}",
                file=sys.stderr,
            )
            return 2

    # Optionally print actual state to stdout
    if args.print_actual:
        sys.stdout.write(json.dumps(actual_state, ensure_ascii=False, indent=2))
        sys.stdout.write("\n")

    s_initial = canonicalize_state(initial_state)
    s_expected = canonicalize_state(expected_state)
    s_actual = canonicalize_state(actual_state)

    expected_tokens = compute_change_tokens(s_initial, s_expected)
    actual_tokens = compute_change_tokens(s_initial, s_actual)

    missing = sorted(expected_tokens - actual_tokens)
    # "unexpected_all" are extras present in actual but not in expected regardless of --strict
    unexpected_all = sorted(actual_tokens - expected_tokens)
    # Preserve existing behavior for top-level "unexpected" field which honors --strict
    unexpected = unexpected_all if args.strict else []

    if args.strict:
        passed = len(missing) == 0 and len(unexpected) == 0
        verdict = "PASS" if passed else "FAIL"
    else:
        # Accept extras: only require expected ⊆ actual
        passed = len(missing) == 0
        verdict = "PASS" if passed else "FAIL"

    # Defer summary printing until after non-blocking evaluation

    # Prepare JSON diff object and compute PASS/FAIL using blocking-only entries
    passed, diff_obj, blocking_missing_count, blocking_unexpected_count = (
        compute_blocking_verdict_from_tokens(
            expected_tokens, actual_tokens, strict=bool(args.strict)
        )
    )
    verdict = "PASS" if passed else "FAIL"

    out = {
        "result": verdict,
        "strict": bool(args.strict),
        "expected_change_count": len(expected_tokens),
        "actual_change_count": len(actual_tokens),
        "diff": {
            "expected_only": diff_obj.get("expectedOnly") or [],
            "actual_only": diff_obj.get("actualOnly") or [],
            "matched_count": int(diff_obj.get("matchedCount") or 0),
        },
    }

    # Now print summary with the recomputed verdict
    print(f"Result: {verdict}")
    print(f"Expected changes: {len(expected_tokens)}  Actual changes: {len(actual_tokens)}")

    # Choose output directory: --output (if provided) else default data/gmail/task_[ID]/ (or task_manual)
    script_dir = os.path.dirname(__file__) or "."
    repo_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
    data_gmail_root = os.path.join(repo_root, "data", "gmail")
    folder_name = f"task_{selected_task_id}" if selected_task_id else "task_manual"
    default_out_dir = os.path.join(data_gmail_root, folder_name)
    out_dir = os.path.abspath(args.output) if args.output else default_out_dir
    try:
        os.makedirs(out_dir, exist_ok=True)
        # Save states (raw) and grade diff
        with open(os.path.join(out_dir, "initial.json"), "w", encoding="utf-8") as f:
            json.dump(initial_state, fp=f, ensure_ascii=False, indent=2)
            f.write("\n")
        with open(os.path.join(out_dir, "expected.json"), "w", encoding="utf-8") as f:
            json.dump(expected_state, fp=f, ensure_ascii=False, indent=2)
            f.write("\n")
        with open(os.path.join(out_dir, "actual.json"), "w", encoding="utf-8") as f:
            json.dump(actual_state, fp=f, ensure_ascii=False, indent=2)
            f.write("\n")
        with open(os.path.join(out_dir, "grade.json"), "w", encoding="utf-8") as f:
            json.dump(out, fp=f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"Artifacts written to: {out_dir}")
    except Exception as e:
        print(f"Warning: failed to write outputs to directory '{out_dir}': {e}", file=sys.stderr)

    # Optional detailed text output (kept off by default)
    if args.verbose:
        if missing:
            print("\nMissing expected changes (not found in actual):")
            for t in missing:
                print("  -", _render_token(t))
        if unexpected_all:
            print("\nActual-only extra changes (present in actual, not in expected):")
            for t in unexpected_all:
                print("  -", _render_token(t))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
