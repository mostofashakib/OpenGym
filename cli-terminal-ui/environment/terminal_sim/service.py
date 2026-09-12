"""Service logic and virtual bash interpreter for terminal environment."""

from __future__ import annotations

import json
import re
import shlex
import sqlite3
from pathlib import Path
from typing import Any

from terminal_sim.clock import VIRTUAL_CLOCK
from terminal_sim.sqlite_common import get_connection
from terminal_sim.tracker import TerminalTracker


def export_state(conn: sqlite3.Connection) -> dict[str, Any]:
    """Export complete environment state for verifiers."""
    files = [dict(r) for r in conn.execute("SELECT * FROM files").fetchall()]
    processes = [dict(r) for r in conn.execute("SELECT * FROM processes").fetchall()]
    services = [dict(r) for r in conn.execute("SELECT * FROM services").fetchall()]
    metrics_row = conn.execute("SELECT * FROM system_metrics WHERE id = 1").fetchone()
    metrics = dict(metrics_row) if metrics_row else {}
    action_log = [dict(r) for r in conn.execute("SELECT * FROM action_log ORDER BY id ASC").fetchall()]
    sub_row = conn.execute("SELECT * FROM task_submission WHERE id = 1").fetchone()
    submission = dict(sub_row) if sub_row else None
    traces = [dict(r) for r in conn.execute("SELECT * FROM event_traces ORDER BY id ASC").fetchall()]

    return {
        "files": files,
        "processes": processes,
        "services": services,
        "system_metrics": metrics,
        "action_log": action_log,
        "task_submission": submission,
        "event_traces": traces,
    }


def _resolve_path(path: str, cwd: str = "/home/admin") -> str:
    path = path.strip()
    if not path.startswith("/"):
        path = f"{cwd.rstrip('/')}/{path}"
    import posixpath
    return posixpath.normpath(path)


def _get_file(conn: sqlite3.Connection, path: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM files WHERE path = ?", (path,)).fetchone()


def _recalc_disk_usage(conn: sqlite3.Connection) -> None:
    total_file_size = conn.execute("SELECT SUM(size) FROM files").fetchone()[0] or 0
    # Base OS size ~1000MB + files size in MB
    used_mb = 1000 + int(total_file_size / (1024 * 1024))
    conn.execute(
        "UPDATE system_metrics SET disk_used_mb = ? WHERE id = 1",
        (used_mb,),
    )


class TerminalService:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.tracker = TerminalTracker(conn)

    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        handler = getattr(self, f"_tool_{tool_name}", None)
        if handler is None:
            res = {"error": f"Unknown tool: {tool_name}"}
        else:
            try:
                res = handler(arguments)
            except Exception as exc:
                res = {"error": str(exc)}

        self.tracker.record_action(tool_name, arguments, res)
        return res

    # -------------------------------------------------------------
    # Tool Handlers
    # -------------------------------------------------------------

    def _tool_read_file(self, args: dict[str, Any]) -> dict[str, Any]:
        path = _resolve_path(args["path"])
        offset = int(args.get("offset", 0))
        limit = int(args.get("limit", 100))

        row = _get_file(self.conn, path)
        if not row:
            return {"error": f"No such file or directory: {path}"}

        lines = row["content"].splitlines(keepends=True)
        total_lines = len(lines)
        selected = lines[offset : offset + limit]

        return {
            "path": path,
            "total_lines": total_lines,
            "offset": offset,
            "content": "".join(selected),
            "permissions": row["permissions"],
            "owner": row["owner"],
            "size": row["size"],
        }

    def _tool_write_file(self, args: dict[str, Any]) -> dict[str, Any]:
        path = _resolve_path(args["path"])
        content = args["content"]
        mode = args.get("mode", "write")
        now = VIRTUAL_CLOCK.now()

        row = _get_file(self.conn, path)
        if row:
            new_content = (row["content"] + content) if mode == "append" else content
            size = len(new_content.encode("utf-8"))
            self.conn.execute(
                """
                UPDATE files
                SET content = ?, size = ?, modified_at = ?
                WHERE path = ?
                """,
                (new_content, size, now, path),
            )
        else:
            size = len(content.encode("utf-8"))
            self.conn.execute(
                """
                INSERT INTO files (path, content, owner, group_owner, permissions, file_type, size, modified_at)
                VALUES (?, ?, 'admin', 'admin', '0644', 'file', ?, ?)
                """,
                (path, content, size, now),
            )

        _recalc_disk_usage(self.conn)
        return {"success": True, "path": path, "size": size, "mode": mode}

    def _tool_list_processes(self, args: dict[str, Any]) -> dict[str, Any]:
        status = args.get("status")
        if status:
            rows = self.conn.execute(
                "SELECT * FROM processes WHERE status = ? ORDER BY pid ASC", (status,)
            ).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM processes ORDER BY pid ASC").fetchall()

        return {"processes": [dict(r) for r in rows]}

    def _tool_inspect_system(self, args: dict[str, Any]) -> dict[str, Any]:
        metrics = dict(self.conn.execute("SELECT * FROM system_metrics WHERE id = 1").fetchone())
        services = [dict(r) for r in self.conn.execute("SELECT * FROM services").fetchall()]
        running_procs = self.conn.execute(
            "SELECT count(*) FROM processes WHERE status = 'running'"
        ).fetchone()[0]

        free_mb = metrics["disk_total_mb"] - metrics["disk_used_mb"]
        disk_pct = round((metrics["disk_used_mb"] / metrics["disk_total_mb"]) * 100, 1)

        return {
            "hostname": "app-node-04.prod.corp",
            "uptime": "14 days, 3 hours",
            "disk": {
                "total_mb": metrics["disk_total_mb"],
                "used_mb": metrics["disk_used_mb"],
                "free_mb": free_mb,
                "used_percent": disk_pct,
            },
            "memory": {
                "total_mb": metrics["memory_total_mb"],
                "used_mb": metrics["memory_used_mb"],
            },
            "services": services,
            "running_processes_count": running_procs,
        }

    def _tool_submit_task(self, args: dict[str, Any]) -> dict[str, Any]:
        now = VIRTUAL_CLOCK.now()
        summary = args["summary"]
        actions = json.dumps(args.get("actions_taken", []))

        self.conn.execute("DELETE FROM task_submission")
        self.conn.execute(
            """
            INSERT INTO task_submission (id, timestamp, summary, actions_taken)
            VALUES (1, ?, ?, ?)
            """,
            (now, summary, actions),
        )
        return {"success": True, "message": "Remediation report successfully recorded."}

    # -------------------------------------------------------------
    # POSIX Command Interpreter for run_command
    # -------------------------------------------------------------

    def _tool_run_command(self, args: dict[str, Any]) -> dict[str, Any]:
        raw_cmd = args["command"].strip()
        cwd = args.get("cwd", "/home/admin")

        # Support compound commands separated by ';' or '&&'
        if "&&" in raw_cmd:
            parts = raw_cmd.split("&&")
            out_parts, err_parts = [], []
            for p in parts:
                r = self._dispatch_single_command(p.strip(), cwd)
                if r.get("stdout"):
                    out_parts.append(r["stdout"])
                if r.get("stderr"):
                    err_parts.append(r["stderr"])
                if r.get("exit_code", 0) != 0:
                    return {
                        "command": raw_cmd,
                        "stdout": "\n".join(out_parts),
                        "stderr": "\n".join(err_parts),
                        "exit_code": r["exit_code"],
                    }
            return {
                "command": raw_cmd,
                "stdout": "\n".join(out_parts),
                "stderr": "\n".join(err_parts),
                "exit_code": 0,
            }

        return self._dispatch_single_command(raw_cmd, cwd)

    def _dispatch_single_command(self, cmd: str, cwd: str) -> dict[str, Any]:
        try:
            tokens = shlex.split(cmd)
        except Exception:
            tokens = cmd.split()

        if not tokens:
            return {"command": cmd, "stdout": "", "stderr": "", "exit_code": 0}

        prog = tokens[0]

        if prog in ("ps", "/bin/ps"):
            return self._cmd_ps(tokens)
        elif prog in ("kill", "/bin/kill", "pkill"):
            return self._cmd_kill(tokens)
        elif prog in ("df", "/bin/df"):
            return self._cmd_df(tokens)
        elif prog in ("ls", "/bin/ls"):
            return self._cmd_ls(tokens, cwd)
        elif prog in ("cat", "/bin/cat"):
            return self._cmd_cat(tokens, cwd)
        elif prog in ("grep", "/bin/grep"):
            return self._cmd_grep(tokens, cwd)
        elif prog in ("find", "/usr/bin/find"):
            return self._cmd_find(tokens, cwd)
        elif prog in ("chmod", "/bin/chmod"):
            return self._cmd_chmod(tokens, cwd)
        elif prog in ("rm", "/bin/rm"):
            return self._cmd_rm(tokens, cwd)
        elif prog in ("truncate", "/usr/bin/truncate"):
            return self._cmd_truncate(tokens, cwd)
        elif prog in ("head", "/usr/bin/head"):
            return self._cmd_head(tokens, cwd)
        elif prog in ("tail", "/usr/bin/tail"):
            return self._cmd_tail(tokens, cwd)
        elif prog in ("wc", "/usr/bin/wc"):
            return self._cmd_wc(tokens, cwd)
        elif prog in ("systemctl", "/bin/systemctl", "service"):
            return self._cmd_systemctl(tokens)
        elif prog in ("sed", "/bin/sed"):
            return self._cmd_sed(tokens, cwd)
        elif prog == "pwd":
            return {"command": cmd, "stdout": cwd, "stderr": "", "exit_code": 0}
        elif prog == "echo":
            # Check redirection
            if ">" in tokens:
                idx = tokens.index(">")
                text = " ".join(tokens[1:idx]).strip("'\"") + "\n"
                target_path = _resolve_path(tokens[idx + 1], cwd)
                return self._tool_write_file({"path": target_path, "content": text, "mode": "write"})
            elif ">>" in tokens:
                idx = tokens.index(">>")
                text = " ".join(tokens[1:idx]).strip("'\"") + "\n"
                target_path = _resolve_path(tokens[idx + 1], cwd)
                return self._tool_write_file({"path": target_path, "content": text, "mode": "append"})
            else:
                return {"command": cmd, "stdout": " ".join(tokens[1:]), "stderr": "", "exit_code": 0}
        else:
            return {
                "command": cmd,
                "stdout": "",
                "stderr": f"bash: {prog}: command executed in simulated environment",
                "exit_code": 0,
            }

    # -------------------------------------------------------------
    # Specific Command Implementations
    # -------------------------------------------------------------

    def _cmd_ps(self, tokens: list[str]) -> dict[str, Any]:
        rows = self.conn.execute("SELECT * FROM processes WHERE status = 'running' ORDER BY pid ASC").fetchall()
        lines = ["USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND"]
        for r in rows:
            lines.append(
                f"{r['user']:<8} {r['pid']:>5} {r['cpu_percent']:>4.1f} {r['memory_mb']:>4.1f} 104856 24500 ?        S    02:10   0:05 {r['command']}"
            )
        return {"command": " ".join(tokens), "stdout": "\n".join(lines), "stderr": "", "exit_code": 0}

    def _cmd_kill(self, tokens: list[str]) -> dict[str, Any]:
        pids = []
        for t in tokens[1:]:
            if t.startswith("-"):
                continue
            if t.isdigit():
                pids.append(int(t))

        if not pids:
            return {"command": " ".join(tokens), "stdout": "", "stderr": "kill: usage: kill [-s sigspec | -n signum | -sigspec] pid | jobspec ...", "exit_code": 1}

        for pid in pids:
            row = self.conn.execute("SELECT * FROM processes WHERE pid = ?", (pid,)).fetchone()
            if row:
                self.conn.execute("UPDATE processes SET status = 'terminated', cpu_percent = 0.0 WHERE pid = ?", (pid,))
                if pid == 4921:
                    # Halt memory pressure
                    self.conn.execute("UPDATE system_metrics SET memory_used_mb = 2200 WHERE id = 1")
            else:
                return {"command": " ".join(tokens), "stdout": "", "stderr": f"kill: ({pid}) - No such process", "exit_code": 1}

        self.conn.commit()
        return {"command": " ".join(tokens), "stdout": "", "stderr": "", "exit_code": 0}

    def _cmd_df(self, tokens: list[str]) -> dict[str, Any]:
        metrics = self.conn.execute("SELECT * FROM system_metrics WHERE id = 1").fetchone()
        tot = metrics["disk_total_mb"]
        used = metrics["disk_used_mb"]
        free = tot - used
        pct = int((used / tot) * 100)

        lines = [
            "Filesystem     1M-blocks  Used Available Use% Mounted on",
            f"/dev/sda1          {tot} {used}      {free}  {pct}% /",
            "tmpfs               4096     8      4088   1% /run",
            "/dev/sda2            512    64       448  13% /boot",
        ]
        return {"command": " ".join(tokens), "stdout": "\n".join(lines), "stderr": "", "exit_code": 0}

    def _cmd_ls(self, tokens: list[str], cwd: str) -> dict[str, Any]:
        args = [t for t in tokens[1:] if not t.startswith("-")]
        flags = [t for t in tokens[1:] if t.startswith("-")]
        is_long = any("l" in f for f in flags)
        target = _resolve_path(args[0], cwd) if args else cwd

        rows = self.conn.execute("SELECT * FROM files").fetchall()
        matches = []
        for r in rows:
            p = r["path"]
            if p == target:
                matches.append(r)
            elif p.startswith(target.rstrip("/") + "/"):
                sub = p[len(target.rstrip("/")) + 1 :]
                if "/" not in sub:
                    matches.append(r)

        if not matches:
            # Check if directory exists conceptually
            return {"command": " ".join(tokens), "stdout": "", "stderr": f"ls: cannot access '{target}': No such file or directory", "exit_code": 2}

        if is_long:
            lines = ["total " + str(len(matches) * 4)]
            for m in matches:
                name = Path(m["path"]).name
                lines.append(f"-rw-r--r-- 1 {m['owner']} {m['group_owner']} {m['size']:>8} Sep 12 02:10 {name}")
            return {"command": " ".join(tokens), "stdout": "\n".join(lines), "stderr": "", "exit_code": 0}
        else:
            names = [Path(m["path"]).name for m in matches]
            return {"command": " ".join(tokens), "stdout": "  ".join(names), "stderr": "", "exit_code": 0}

    def _cmd_cat(self, tokens: list[str], cwd: str) -> dict[str, Any]:
        targets = [t for t in tokens[1:] if not t.startswith("-")]
        if not targets:
            return {"command": " ".join(tokens), "stdout": "", "stderr": "cat: missing file operand", "exit_code": 1}

        out = []
        for t in targets:
            path = _resolve_path(t, cwd)
            r = _get_file(self.conn, path)
            if r:
                out.append(r["content"])
            else:
                return {"command": " ".join(tokens), "stdout": "", "stderr": f"cat: {t}: No such file or directory", "exit_code": 1}

        return {"command": " ".join(tokens), "stdout": "\n".join(out), "stderr": "", "exit_code": 0}

    def _cmd_grep(self, tokens: list[str], cwd: str) -> dict[str, Any]:
        args = [t for t in tokens[1:] if not t.startswith("-")]
        if len(args) < 2:
            return {"command": " ".join(tokens), "stdout": "", "stderr": "grep: usage: grep [pattern] [file]", "exit_code": 2}

        pattern = args[0]
        target = _resolve_path(args[1], cwd)
        r = _get_file(self.conn, target)
        if not r:
            return {"command": " ".join(tokens), "stdout": "", "stderr": f"grep: {args[1]}: No such file or directory", "exit_code": 2}

        matching_lines = [line for line in r["content"].splitlines() if re.search(pattern, line)]
        exit_code = 0 if matching_lines else 1
        return {"command": " ".join(tokens), "stdout": "\n".join(matching_lines), "stderr": "", "exit_code": exit_code}

    def _cmd_find(self, tokens: list[str], cwd: str) -> dict[str, Any]:
        target = cwd
        name_filter = None
        for i, t in enumerate(tokens[1:]):
            if t == "-name" and i + 2 < len(tokens):
                name_filter = tokens[i + 2].strip("'\"")
            elif not t.startswith("-"):
                target = _resolve_path(t, cwd)

        rows = self.conn.execute("SELECT path FROM files").fetchall()
        results = []
        for r in rows:
            p = r["path"]
            if p.startswith(target.rstrip("/")):
                if name_filter:
                    if re.search(name_filter.replace("*", ".*"), Path(p).name):
                        results.append(p)
                else:
                    results.append(p)

        return {"command": " ".join(tokens), "stdout": "\n".join(results), "stderr": "", "exit_code": 0}

    def _cmd_chmod(self, tokens: list[str], cwd: str) -> dict[str, Any]:
        args = [t for t in tokens[1:] if not t.startswith("-")]
        if len(args) < 2:
            return {"command": " ".join(tokens), "stdout": "", "stderr": "chmod: missing operand", "exit_code": 1}

        mode = args[0]
        target = _resolve_path(args[1], cwd)
        r = _get_file(self.conn, target)
        if not r:
            return {"command": " ".join(tokens), "stdout": "", "stderr": f"chmod: cannot access '{args[1]}': No such file or directory", "exit_code": 1}

        self.conn.execute("UPDATE files SET permissions = ? WHERE path = ?", (mode, target))
        self.conn.commit()
        return {"command": " ".join(tokens), "stdout": "", "stderr": "", "exit_code": 0}

    def _cmd_rm(self, tokens: list[str], cwd: str) -> dict[str, Any]:
        targets = [t for t in tokens[1:] if not t.startswith("-")]
        for t in targets:
            path = _resolve_path(t, cwd)
            self.conn.execute("DELETE FROM files WHERE path = ?", (path,))

        _recalc_disk_usage(self.conn)
        self.conn.commit()
        return {"command": " ".join(tokens), "stdout": "", "stderr": "", "exit_code": 0}

    def _cmd_truncate(self, tokens: list[str], cwd: str) -> dict[str, Any]:
        targets = [t for t in tokens[1:] if not t.startswith("-")]
        for t in targets:
            path = _resolve_path(t, cwd)
            self.conn.execute(
                "UPDATE files SET content = '', size = 0, modified_at = ? WHERE path = ?",
                (VIRTUAL_CLOCK.now(), path),
            )

        _recalc_disk_usage(self.conn)
        self.conn.commit()
        return {"command": " ".join(tokens), "stdout": "", "stderr": "", "exit_code": 0}

    def _cmd_head(self, tokens: list[str], cwd: str) -> dict[str, Any]:
        targets = [t for t in tokens[1:] if not t.startswith("-")]
        if not targets:
            return {"command": " ".join(tokens), "stdout": "", "stderr": "head: missing file", "exit_code": 1}
        path = _resolve_path(targets[0], cwd)
        r = _get_file(self.conn, path)
        if not r:
            return {"command": " ".join(tokens), "stdout": "", "stderr": f"head: {targets[0]}: No such file", "exit_code": 1}
        lines = r["content"].splitlines()[:10]
        return {"command": " ".join(tokens), "stdout": "\n".join(lines), "stderr": "", "exit_code": 0}

    def _cmd_tail(self, tokens: list[str], cwd: str) -> dict[str, Any]:
        targets = [t for t in tokens[1:] if not t.startswith("-")]
        if not targets:
            return {"command": " ".join(tokens), "stdout": "", "stderr": "tail: missing file", "exit_code": 1}
        path = _resolve_path(targets[0], cwd)
        r = _get_file(self.conn, path)
        if not r:
            return {"command": " ".join(tokens), "stdout": "", "stderr": f"tail: {targets[0]}: No such file", "exit_code": 1}
        lines = r["content"].splitlines()[-10:]
        return {"command": " ".join(tokens), "stdout": "\n".join(lines), "stderr": "", "exit_code": 0}

    def _cmd_wc(self, tokens: list[str], cwd: str) -> dict[str, Any]:
        targets = [t for t in tokens[1:] if not t.startswith("-")]
        if not targets:
            return {"command": " ".join(tokens), "stdout": "", "stderr": "wc: missing file", "exit_code": 1}
        path = _resolve_path(targets[0], cwd)
        r = _get_file(self.conn, path)
        if not r:
            return {"command": " ".join(tokens), "stdout": "", "stderr": f"wc: {targets[0]}: No such file", "exit_code": 1}
        c = r["content"]
        lines = len(c.splitlines())
        words = len(c.split())
        chars = len(c)
        return {"command": " ".join(tokens), "stdout": f"{lines:>7} {words:>7} {chars:>7} {targets[0]}", "stderr": "", "exit_code": 0}

    def _cmd_sed(self, tokens: list[str], cwd: str) -> dict[str, Any]:
        # Handle simple s/foo/bar/ pattern
        pattern = None
        target = None
        for t in tokens[1:]:
            if t.startswith("s/") or t.startswith("'s/") or t.startswith('"s/'):
                pattern = t.strip("'\"")
            elif not t.startswith("-"):
                target = _resolve_path(t, cwd)

        if not pattern or not target:
            return {"command": " ".join(tokens), "stdout": "", "stderr": "sed: invalid arguments", "exit_code": 1}

        r = _get_file(self.conn, target)
        if not r:
            return {"command": " ".join(tokens), "stdout": "", "stderr": f"sed: {target}: No such file", "exit_code": 1}

        parts = pattern.split("/")
        if len(parts) >= 3:
            old_str, new_str = parts[1], parts[2]
            new_content = r["content"].replace(old_str, new_str)
            self.conn.execute("UPDATE files SET content = ?, size = ? WHERE path = ?", (new_content, len(new_content), target))
            self.conn.commit()
            return {"command": " ".join(tokens), "stdout": "", "stderr": "", "exit_code": 0}

        return {"command": " ".join(tokens), "stdout": "", "stderr": "sed: unsupported pattern", "exit_code": 1}

    def _cmd_systemctl(self, tokens: list[str]) -> dict[str, Any]:
        # systemctl status <service> OR systemctl restart <service>
        action = "status"
        service = "payment-processor"

        for i, t in enumerate(tokens):
            if t in ("status", "restart", "start", "stop"):
                action = t
                if i + 1 < len(tokens):
                    service = tokens[i + 1].replace(".service", "")

        svc_row = self.conn.execute("SELECT * FROM services WHERE name = ?", (service,)).fetchone()
        if not svc_row:
            return {"command": " ".join(tokens), "stdout": "", "stderr": f"Unit {service}.service could not be found.", "exit_code": 4}

        cfg_file = _get_file(self.conn, "/etc/payment-processor/config.yaml")
        key_file = _get_file(self.conn, "/etc/ssl/certs/payment-api.key")

        cfg_valid = (
            cfg_file is not None
            and "db-primary.internal" in cfg_file["content"]
            and "5432" in cfg_file["content"]
            and "db-replica-invalid" not in cfg_file["content"]
        )

        key_valid = key_file is not None and str(key_file["permissions"]).lstrip("0") in ("600", "400")

        if action in ("restart", "start"):
            if cfg_valid and key_valid:
                self.conn.execute(
                    "UPDATE services SET status = 'active', pid = 5200 WHERE name = 'payment-processor'"
                )
                self.conn.commit()
                return {
                    "command": " ".join(tokens),
                    "stdout": f"[ OK ] Started {service}.service - Production Payment Processing Engine.",
                    "stderr": "",
                    "exit_code": 0,
                }
            else:
                self.conn.execute("UPDATE services SET status = 'failed' WHERE name = 'payment-processor'")
                self.conn.commit()
                err_msg = (
                    f"Job for {service}.service failed because the control process exited with error code.\n"
                    f"See \"systemctl status {service}.service\" and \"journalctl -xeu {service}.service\" for details."
                )
                return {"command": " ".join(tokens), "stdout": "", "stderr": err_msg, "exit_code": 1}

        elif action == "status":
            curr_status = svc_row["status"]
            if curr_status == "active":
                out = (
                    f"● {service}.service - Production Payment Processing Engine\n"
                    f"     Loaded: loaded (/etc/systemd/system/{service}.service; enabled; vendor preset: enabled)\n"
                    f"     Active: active (running) since Sat 2026-09-12 02:30:12 UTC; 2min ago\n"
                    f"   Main PID: 5200 (payment-process)\n"
                    f"      Tasks: 4 (limit: 4915)\n"
                    f"     Memory: 64.2M\n"
                    f"        CPU: 120ms\n"
                    f"     CGroup: /system.slice/{service}.service\n"
                    f"             └─5200 /opt/payment-processor/bin/payment-processor --config /etc/payment-processor/config.yaml"
                )
                return {"command": " ".join(tokens), "stdout": out, "stderr": "", "exit_code": 0}
            else:
                reason = "Database connection failed" if not cfg_valid else "Insecure key permissions"
                out = (
                    f"● {service}.service - Production Payment Processing Engine\n"
                    f"     Loaded: loaded (/etc/systemd/system/{service}.service; enabled; vendor preset: enabled)\n"
                    f"     Active: failed (Result: exit-code) since Sat 2026-09-12 02:14:19 UTC; 16min ago\n"
                    f"    Process: 3102 ExecStart=/opt/payment-processor/bin/payment-processor (code=exited, status=1/FAILURE)\n"
                    f"   Main PID: 3102 (code=exited, status=1/FAILURE)\n\n"
                    f"Sep 12 02:14:19 app-node-04 payment-processor[3102]: [ERROR] {reason}\n"
                    f"Sep 12 02:14:19 app-node-04 systemd[1]: payment-processor.service: Failed with result 'exit-code'."
                )
                return {"command": " ".join(tokens), "stdout": out, "stderr": "", "exit_code": 3}

        return {"command": " ".join(tokens), "stdout": "", "stderr": f"Unsupported action: {action}", "exit_code": 1}


def execute_tool(db_path: Path | str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    with get_connection(db_path) as conn:
        svc = TerminalService(conn)
        return svc.execute_tool(tool_name, arguments)
