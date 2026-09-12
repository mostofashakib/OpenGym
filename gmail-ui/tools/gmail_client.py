"""Client for the Gmail REST API and socket service.

Provides synchronous and asynchronous calls to the running Gmail Next.js server
or the authoritative Gmail simulator Unix socket (/run/gmail/agent.sock).
Returns the standardized OpenGym envelope:
  {"ok": True, "result": ...} or {"ok": False, "error": ...}
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

DEFAULT_BASE_URL = os.environ.get("GMAIL_BASE_URL", "http://127.0.0.1:3000")
DEFAULT_SOCKET_PATH = os.environ.get("GMAIL_SOCKET", "/run/gmail/agent.sock")


class GmailClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout_sec: float = 30.0,
        socket_path: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec
        self.socket_path = socket_path if socket_path is not None else DEFAULT_SOCKET_PATH

    def _call_socket(self, tool: str, args: dict[str, Any] | None) -> dict[str, Any] | None:
        if self.socket_path and os.path.exists(self.socket_path):
            try:
                from gmail_sim.protocol import request
                return request(self.socket_path, {"tool": tool, "arguments": args or {}})
            except Exception:
                return None
        return None

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: Any = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        if params:
            clean_params = {k: v for k, v in params.items() if v is not None}
            if clean_params:
                url = f"{url}?{urllib.parse.urlencode(clean_params)}"

        data = None
        headers = {
            "Accept": "application/json",
            "Authorization": "Basic YWdlbnQ6d2UtbG92ZS1jdWEh",  # agent:we-love-cua!
        }
        if json_data is not None:
            data = json.dumps(json_data).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                body = resp.read().decode("utf-8")
                try:
                    payload = json.loads(body) if body else {}
                except json.JSONDecodeError:
                    payload = {"text": body}
                return {"ok": True, "result": payload}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            try:
                err_payload = json.loads(err_body)
            except Exception:
                err_payload = {"error": err_body or str(e)}
            return {"ok": False, "error": err_payload}
        except Exception as e:
            return {"ok": False, "error": {"code": "CONNECTION_ERROR", "message": str(e)}}

    # -------------------------------------------------------------------------
    # Tool Dispatcher
    # -------------------------------------------------------------------------
    def execute_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        args: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Dispatch a tool by name to the corresponding tool_<name> implementation."""
        payload = arguments if arguments is not None else (args or kwargs.get("payload") or {})
        method_name = f"tool_{name}"
        method = getattr(self, method_name, None)
        if method and callable(method):
            try:
                res = method(payload)
                if isinstance(res, dict):
                    return res
                return {"ok": True, "result": res}
            except Exception as exc:
                return {"ok": False, "error": str(exc)}
        return {"ok": False, "error": f"Unknown tool: {name}"}

    # -------------------------------------------------------------------------
    # Tool Methods
    # -------------------------------------------------------------------------
    def tool_list_emails(self, args: dict[str, Any] | None = None) -> dict[str, Any]:
        res = self._call_socket("list_emails", args)
        if res is not None:
            return res
        params = {k: v for k, v in (args or {}).items() if v is not None}
        return self._request("GET", "/api/emails", params=params)

    def tool_get_email(self, args: dict[str, Any]) -> dict[str, Any]:
        res = self._call_socket("get_email", args)
        if res is not None:
            return res
        msg_id = args.get("id") or args.get("email_id") or args.get("message_id") or ""
        return self._request("GET", f"/api/emails/{urllib.parse.quote(msg_id)}")

    def tool_send_email(self, args: dict[str, Any]) -> dict[str, Any]:
        res = self._call_socket("send_email", args)
        if res is not None:
            return res
        text = args.get("text") or args.get("body") or args.get("content") or ""
        payload = {
            "to": args.get("to") or args.get("to_addresses") or args.get("recipient"),
            "subject": args.get("subject", ""),
            "text": text,
        }
        if "cc" in args:
            payload["cc"] = args["cc"]
        if "bcc" in args:
            payload["bcc"] = args["bcc"]
        if "attachments" in args:
            payload["attachments"] = args["attachments"]
        return self._request("POST", "/api/emails", json_data=payload)

    def tool_update_email(self, args: dict[str, Any]) -> dict[str, Any]:
        res = self._call_socket("update_email", args)
        if res is not None:
            return res
        msg_id = args.get("id") or args.get("email_id") or args.get("message_id") or ""
        payload: dict[str, Any] = {}
        for key, alt in [("isRead", "is_read"), ("isStarred", "is_starred"), ("isImportant", "is_important")]:
            if key in args:
                payload[key] = args[key]
            elif alt in args:
                payload[key] = args[alt]
        if args.get("isArchived") or args.get("is_archived"):
            payload["action"] = "archive"
        elif args.get("isTrash") or args.get("is_trash"):
            payload["action"] = "trash"
        if "action" in args:
            payload["action"] = args["action"]
        add_lbls = args.get("addLabels") or args.get("add_labels")
        if add_lbls:
            payload["addLabel"] = add_lbls[0] if isinstance(add_lbls, list) and add_lbls else add_lbls
        rm_lbls = args.get("removeLabels") or args.get("remove_labels")
        if rm_lbls:
            payload["removeLabel"] = rm_lbls[0] if isinstance(rm_lbls, list) and rm_lbls else rm_lbls
        return self._request("PUT", f"/api/emails/{urllib.parse.quote(msg_id)}", json_data=payload)

    def tool_list_threads(self, args: dict[str, Any] | None = None) -> dict[str, Any]:
        res = self._call_socket("list_threads", args)
        if res is not None:
            return res
        params = {k: v for k, v in (args or {}).items() if v is not None}
        return self._request("GET", "/api/threads", params=params)

    def tool_get_thread(self, args: dict[str, Any]) -> dict[str, Any]:
        res = self._call_socket("get_thread", args)
        if res is not None:
            return res
        t_id = args.get("id") or args.get("thread_id") or args.get("threadId") or ""
        return self._request("GET", f"/api/threads/{urllib.parse.quote(t_id)}")

    def tool_reply_thread(self, args: dict[str, Any]) -> dict[str, Any]:
        res = self._call_socket("reply_thread", args)
        if res is not None:
            return res
        t_id = args.get("thread_id") or args.get("id") or args.get("threadId") or ""
        text = args.get("text") or args.get("body") or args.get("content") or ""
        payload: dict[str, Any] = {"text": text}
        if "reply_to_id" in args:
            payload["replyToId"] = args["reply_to_id"]
        if "to" in args:
            payload["to"] = args["to"]
        return self._request("POST", f"/api/threads/{urllib.parse.quote(t_id)}/messages", json_data=payload)

    def tool_search_emails(self, args: dict[str, Any]) -> dict[str, Any]:
        res = self._call_socket("search_emails", args)
        if res is not None:
            return res
        query_val = args.get("query") or args.get("q") or args.get("search") or ""
        params = {"q": query_val}
        if "anywhere" in args:
            params["anywhere"] = args["anywhere"]
        return self._request("GET", "/api/search", params=params)

    def tool_list_drafts(self, args: dict[str, Any] | None = None) -> dict[str, Any]:
        res = self._call_socket("list_drafts", args)
        if res is not None:
            return res
        return self._request("GET", "/api/drafts")

    def tool_create_draft(self, args: dict[str, Any]) -> dict[str, Any]:
        res = self._call_socket("create_draft", args)
        if res is not None:
            return res
        text = args.get("text") or args.get("body") or args.get("content") or ""
        to_field = args.get("to") or args.get("to_addresses") or args.get("recipient") or []
        payload = {
            "to": to_field,
            "subject": args.get("subject", ""),
            "text": text,
        }
        if "cc" in args:
            payload["cc"] = args["cc"]
        if "bcc" in args:
            payload["bcc"] = args["bcc"]
        return self._request("POST", "/api/drafts", json_data=payload)

    def tool_update_draft(self, args: dict[str, Any]) -> dict[str, Any]:
        res = self._call_socket("update_draft", args)
        if res is not None:
            return res
        draft_id = args.get("id") or args.get("draft_id") or args.get("draftId") or ""
        payload: dict[str, Any] = {}
        if "to" in args:
            payload["to"] = args["to"]
        if "subject" in args:
            payload["subject"] = args["subject"]
        if "body" in args or "text" in args or "content" in args:
            payload["text"] = args.get("text") or args.get("body") or args.get("content")
        return self._request("PUT", f"/api/drafts/{urllib.parse.quote(draft_id)}", json_data=payload)

    def tool_send_draft(self, args: dict[str, Any]) -> dict[str, Any]:
        res = self._call_socket("send_draft", args)
        if res is not None:
            return res
        draft_id = args.get("id") or args.get("draft_id") or args.get("draftId") or ""
        return self._request("POST", f"/api/drafts/{urllib.parse.quote(draft_id)}/send")

    def tool_delete_draft(self, args: dict[str, Any]) -> dict[str, Any]:
        res = self._call_socket("delete_draft", args)
        if res is not None:
            return res
        draft_id = args.get("id") or args.get("draft_id") or args.get("draftId") or ""
        return self._request("DELETE", f"/api/drafts/{urllib.parse.quote(draft_id)}")

    def tool_list_labels(self, args: dict[str, Any] | None = None) -> dict[str, Any]:
        res = self._call_socket("list_labels", args)
        if res is not None:
            return res
        return self._request("GET", "/api/labels")

    def tool_create_label(self, args: dict[str, Any]) -> dict[str, Any]:
        res = self._call_socket("create_label", args)
        if res is not None:
            return res
        payload = {"name": args["name"]}
        if "color" in args:
            payload["color"] = args["color"]
        return self._request("POST", "/api/labels", json_data=payload)

    def tool_list_contacts(self, args: dict[str, Any] | None = None) -> dict[str, Any]:
        res = self._call_socket("list_contacts", args)
        if res is not None:
            return res
        return self._request("GET", "/api/contacts")

    def tool_get_counters(self, args: dict[str, Any] | None = None) -> dict[str, Any]:
        res = self._call_socket("get_counters", args)
        if res is not None:
            return res
        return self._request("GET", "/api/counters")

    def tool_submit_task(self, args: dict[str, Any]) -> dict[str, Any]:
        res = self._call_socket("submit_task", args)
        if res is not None:
            return res
        return {
            "ok": True,
            "result": {
                "submitted": True,
                "summary": args.get("summary", ""),
                "affected_message_ids": args.get("affected_message_ids", []),
            },
        }

    # State export/import for verifiers
    def get_state(self, ascii_escaped: bool = True) -> dict[str, Any]:
        return self._request("GET", "/api/state", params={"ascii": ascii_escaped})

    def post_state(self, state: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/state", json_data=state)
