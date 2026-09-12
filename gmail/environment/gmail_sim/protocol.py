"""Wire format protocol between the Gmail environment daemon and its clients."""

from __future__ import annotations

import json
import socket
from typing import Any

AGENT_SOCKET = "/run/gmail/agent.sock"
ADMIN_SOCKET = "/run/gmail/admin.sock"
MAX_FRAME_BYTES = 8 * 1024 * 1024


class ProtocolError(RuntimeError):
    """The peer sent something that is not a valid frame."""


def encode(payload: dict[str, Any]) -> bytes:
    frame = json.dumps(payload, sort_keys=True).encode("utf-8")
    if len(frame) > MAX_FRAME_BYTES:
        raise ProtocolError("Frame exceeds the maximum size.")
    return frame + b"\n"


def decode(line: bytes) -> dict[str, Any]:
    if len(line) > MAX_FRAME_BYTES:
        raise ProtocolError("Frame exceeds the maximum size.")
    try:
        payload = json.loads(line.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError(f"Malformed frame: {exc}") from exc
    if not isinstance(payload, dict):
        raise ProtocolError("Frame must be a JSON object.")
    return payload


def request(socket_path: str, payload: dict[str, Any], timeout: float = 30.0) -> dict[str, Any]:
    """Send one request and read one response over Unix domain socket."""
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(timeout)
        client.connect(socket_path)
        client.sendall(encode(payload))
        try:
            client.shutdown(socket.SHUT_WR)
        except OSError:
            pass
        chunks: list[bytes] = []
        size = 0
        while True:
            chunk = client.recv(65536)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_FRAME_BYTES:
                raise ProtocolError("Response exceeds the maximum size.")
            chunks.append(chunk)
    return decode(b"".join(chunks).strip() or b"{}")
