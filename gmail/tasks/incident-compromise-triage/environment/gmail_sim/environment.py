"""RL and agent lifecycle contract for the Gmail environment."""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gmail_sim.clock import now
from gmail_sim.seed import seed_database
from gmail_sim.service import (
    DEFAULT_DB_PATH,
    DEFAULT_SNAPSHOT_PATH,
    execute_tool,
    export_state,
)
from gmail_sim.sqlite_common import get_connection, storage_errors
from gmail_sim.tool_definitions import get_tool_definitions

CONTRACT_VERSION = "1.0"
DEFAULT_MAX_TURNS = 100
DEFAULT_PROMPT_ID = "gmail_assistant"
SESSION_COOKIE_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


class GmailEnvironment:
    """RL and agent environment contract managing session state and tool executions."""

    def __init__(
        self,
        db_path: str | Path = DEFAULT_DB_PATH,
        snapshot_path: str | Path = DEFAULT_SNAPSHOT_PATH,
    ) -> None:
        self.db_path = Path(db_path)
        self.snapshot_path = Path(snapshot_path)

    def _ensure_session_schema(self) -> None:
        with get_connection(self.db_path) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_cookie TEXT PRIMARY KEY,
                    prompt_id TEXT NOT NULL,
                    user_instruction TEXT NOT NULL,
                    prompt_context_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    max_turns INTEGER NOT NULL,
                    turns_taken INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS session_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_cookie TEXT NOT NULL,
                    turn INTEGER NOT NULL,
                    tool_name TEXT NOT NULL,
                    input_json TEXT NOT NULL,
                    output_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_cookie) REFERENCES sessions (session_cookie)
                );
                """
            )

    def setup(self) -> dict[str, Any]:
        if not self.db_path.exists():
            self.setup_state(seed=0)
        self._ensure_session_schema()
        return {
            "contract_version": CONTRACT_VERSION,
            "persistent": True,
            "prompt_count": len(self.prompts()),
            "tool_count": len(get_tool_definitions()),
        }

    def setup_state(self, seed: int = 0) -> None:
        seed_database(self.db_path, self.snapshot_path)
        self._ensure_session_schema()

    def prompts(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "gmail_assistant",
                "name": "Gmail Assistant Operator",
                "description": "System operator responsible for managing inbox, replying to requests, and triaging emails.",
            }
        ]

    def render_prompt(
        self,
        prompt_id: str,
        instruction: str = "",
        context: dict[str, Any] | None = None,
    ) -> str:
        ctx_str = json.dumps(context or {})
        return (
            f"You are the autonomous Gmail Assistant Operator.\n"
            f"Instruction: {instruction or 'Triage unread emails and process urgent requests.'}\n"
            f"Context: {ctx_str}\n"
            f"Available tools allow listing emails, reading threads, sending messages, and organizing labels."
        )

    def seed_session(
        self,
        *,
        session_cookie: str = "default",
        user_instruction: str = "",
        prompt_id: str = DEFAULT_PROMPT_ID,
        prompt_context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        max_turns: int = DEFAULT_MAX_TURNS,
    ) -> dict[str, Any]:
        if not SESSION_COOKIE_PATTERN.match(session_cookie):
            raise ValueError(f"Invalid session cookie: {session_cookie}")

        self._ensure_session_schema()
        ts = datetime.now(timezone.utc).isoformat()
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO sessions (
                    session_cookie, prompt_id, user_instruction,
                    prompt_context_json, metadata_json, max_turns, turns_taken,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (
                    session_cookie,
                    prompt_id,
                    user_instruction,
                    json.dumps(prompt_context or {}),
                    json.dumps(metadata or {}),
                    max_turns,
                    ts,
                    ts,
                ),
            )
        return self.state(session_cookie=session_cookie)

    def reset(
        self,
        *,
        session_cookie: str = "default",
        seed: int = 0,
        user_instruction: str = "",
        prompt_id: str = DEFAULT_PROMPT_ID,
        prompt_context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        max_turns: int = DEFAULT_MAX_TURNS,
    ) -> dict[str, Any]:
        self.setup_state(seed=seed)
        return self.seed_session(
            session_cookie=session_cookie,
            user_instruction=user_instruction,
            prompt_id=prompt_id,
            prompt_context=prompt_context,
            metadata=metadata,
            max_turns=max_turns,
        )

    def tool_definitions(self) -> tuple[dict[str, Any], ...]:
        return get_tool_definitions()

    def step(
        self,
        session_cookie: str,
        tool_name: str,
        input_payload: dict[str, Any],
    ) -> dict[str, Any]:
        with get_connection(self.db_path) as conn:
            s_row = conn.execute(
                "SELECT * FROM sessions WHERE session_cookie = ?", (session_cookie,)
            ).fetchone()
            if not s_row:
                raise ValueError(f"Session '{session_cookie}' not found.")

            turns_taken = s_row["turns_taken"] + 1
            max_turns = s_row["max_turns"]
            ts = datetime.now(timezone.utc).isoformat()

            try:
                output = execute_tool(self.db_path, tool_name, input_payload)
                ok = True
                err = None
            except Exception as exc:
                output = {}
                ok = False
                err = str(exc)

            step_record = {
                "ok": ok,
                "output": output,
                "error": err,
            }

            conn.execute(
                """
                INSERT INTO session_history (session_cookie, turn, tool_name, input_json, output_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_cookie,
                    turns_taken,
                    tool_name,
                    json.dumps(input_payload),
                    json.dumps(step_record),
                    ts,
                ),
            )
            conn.execute(
                "UPDATE sessions SET turns_taken = ?, updated_at = ? WHERE session_cookie = ?",
                (turns_taken, ts, session_cookie),
            )

        done = turns_taken >= max_turns or tool_name == "submit_task"
        return {
            "session_cookie": session_cookie,
            "turn": turns_taken,
            "turns_taken": turns_taken,
            "done": done,
            "result": step_record,
            "observation": {"ok": ok, "result": output, "error": err},
            "state": self.state(session_cookie),
        }

    def state(self, session_cookie: str, history_limit: int | None = 10) -> dict[str, Any]:
        with get_connection(self.db_path) as conn:
            s_row = conn.execute(
                "SELECT * FROM sessions WHERE session_cookie = ?", (session_cookie,)
            ).fetchone()
            counters = execute_tool(self.db_path, "get_counters", {})
            clock_ts = now(conn)

        history_items = self.history(session_cookie, limit=history_limit)

        return {
            "session_cookie": session_cookie,
            "turn": s_row["turns_taken"] if s_row else 0,
            "turns_taken": s_row["turns_taken"] if s_row else 0,
            "max_turns": s_row["max_turns"] if s_row else DEFAULT_MAX_TURNS,
            "clock": clock_ts,
            "counters": counters,
            "history": history_items,
        }

    def history(self, session_cookie: str, limit: int | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM session_history WHERE session_cookie = ? ORDER BY turn ASC"
        params: list[Any] = [session_cookie]
        if limit is not None:
            query = "SELECT * FROM session_history WHERE session_cookie = ? ORDER BY turn DESC LIMIT ?"
            params.append(limit)

        with get_connection(self.db_path) as conn:
            rows = conn.execute(query, params).fetchall()

        if limit is not None:
            rows = list(reversed(rows))

        return [
            {
                "turn": r["turn"],
                "tool_name": r["tool_name"],
                "input": json.loads(r["input_json"]),
                "output": json.loads(r["output_json"]),
                "created_at": r["created_at"],
            }
            for r in rows
        ]
