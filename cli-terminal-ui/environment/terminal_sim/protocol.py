"""Unix socket protocol for terminal environment."""

from __future__ import annotations

import json
import socket
from typing import Any


def send_json(sock: socket.socket, data: dict[str, Any]) -> None:
    payload = json.dumps(data) + "\n"
    sock.sendall(payload.encode("utf-8"))


def recv_json(sock: socket.socket) -> dict[str, Any]:
    buffer = b""
    while b"\n" not in buffer:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buffer += chunk
    if not buffer:
        return {}
    line = buffer.split(b"\n", 1)[0]
    return json.loads(line.decode("utf-8"))


def request(socket_path: str, req: dict[str, Any], timeout: float = 10.0) -> dict[str, Any]:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        sock.connect(socket_path)
        send_json(sock, req)
        return recv_json(sock)
