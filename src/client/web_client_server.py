"""
web_client_server.py - Adaptador HTTP local para la interfaz HTML del Bus.

Este modulo NO reimplementa la logica del backend. Solo:
  - sirve archivos estaticos para la UI local,
  - mantiene sesiones independientes por navegador/pestana,
  - y reenvia operaciones al servidor TCP existente via BusClient.
"""

from __future__ import annotations

import json
import logging
import multiprocessing as mp
import threading
import uuid
from dataclasses import dataclass
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from src.client.bus_client import BusClientError
from src.client.web_session_worker import worker_main


LOGGER = logging.getLogger(__name__)
STATIC_DIR = Path(__file__).resolve().parent / "webui"


@dataclass
class ClientSession:
    session_id: str
    process: mp.Process
    conn: Connection
    host: str | None = None
    port: int | None = None
    connected: bool = False
    _lock: threading.Lock | None = None

    def __post_init__(self) -> None:
        if self._lock is None:
            self._lock = threading.Lock()

    @property
    def pid(self) -> int | None:
        return self.process.pid

    def request(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self.conn.send(payload)
            response = self.conn.recv()
        if payload["action"] == "connect" and response.get("ok"):
            self.host = str(payload["host"])
            self.port = int(payload["port"])
            self.connected = True
        elif payload["action"] == "disconnect" and response.get("ok"):
            self.connected = False
        return response

    def close(self) -> None:
        try:
            self.request({"action": "stop"})
        except Exception:
            pass
        try:
            self.conn.close()
        except OSError:
            pass
        if self.process.is_alive():
            self.process.join(timeout=1)
        if self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=1)


class SessionStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sessions: dict[str, ClientSession] = {}
        self._ctx = mp.get_context("spawn")

    def create(self) -> ClientSession:
        with self._lock:
            parent_conn, child_conn = self._ctx.Pipe()
            process = self._ctx.Process(
                target=worker_main,
                args=(child_conn,),
                daemon=True,
                name=f"bus-web-session-{len(self._sessions) + 1}",
            )
            process.start()
            child_conn.close()
            session = ClientSession(
                session_id=uuid.uuid4().hex,
                process=process,
                conn=parent_conn,
            )
            self._sessions[session.session_id] = session
            return session

    def get(self, session_id: str) -> ClientSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def require(self, session_id: str) -> ClientSession:
        session = self.get(session_id)
        if session is None:
            raise KeyError(f"SESSION_NOT_FOUND:{session_id}")
        return session

    def close_all(self) -> None:
        with self._lock:
            sessions = list(self._sessions.values())
        for session in sessions:
            session.close()


SESSIONS = SessionStore()


def _response_payload(ok: bool, **extra: Any) -> dict[str, Any]:
    payload = {"ok": ok}
    payload.update(extra)
    return payload


def _require_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc

class WebClientRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        LOGGER.info("%s - %s", self.address_string(), format % args)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._write_json(HTTPStatus.OK, _response_payload(True, status="up"))
            return
        if parsed.path == "/api/session":
            session = SESSIONS.create()
            self._write_json(
                HTTPStatus.CREATED,
                _response_payload(True, session_id=session.session_id, pid=session.pid),
            )
            return
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            body = self._read_json_body()
            if parsed.path == "/api/connect":
                payload = self._handle_connect(body)
                self._write_json(HTTPStatus.OK, payload)
                return
            if parsed.path == "/api/disconnect":
                payload = self._handle_disconnect(body)
                self._write_json(HTTPStatus.OK, payload)
                return
            if parsed.path == "/api/request":
                payload = self._handle_request(body)
                self._write_json(HTTPStatus.OK, payload)
                return
            if parsed.path == "/api/raw":
                payload = self._handle_raw(body)
                self._write_json(HTTPStatus.OK, payload)
                return
            if parsed.path == "/api/preload":
                payload = self._handle_preload(body)
                self._write_json(HTTPStatus.OK, payload)
                return
            self._write_json(
                HTTPStatus.NOT_FOUND,
                _response_payload(False, error=f"UNKNOWN_ENDPOINT:{parsed.path}"),
            )
        except BusClientError as exc:
            self._write_json(HTTPStatus.BAD_REQUEST, _response_payload(False, error=str(exc)))
        except KeyError as exc:
            self._write_json(HTTPStatus.NOT_FOUND, _response_payload(False, error=str(exc)))
        except ValueError as exc:
            self._write_json(HTTPStatus.BAD_REQUEST, _response_payload(False, error=str(exc)))
        except json.JSONDecodeError:
            self._write_json(HTTPStatus.BAD_REQUEST, _response_payload(False, error="INVALID_JSON"))
        except OSError as exc:
            self._write_json(HTTPStatus.BAD_GATEWAY, _response_payload(False, error=str(exc)))
        except Exception as exc:  # pragma: no cover - proteccion final
            LOGGER.exception("Unexpected adapter error")
            self._write_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                _response_payload(False, error=f"ADAPTER_ERROR:{exc}"),
            )

    def _handle_connect(self, body: dict[str, Any]) -> dict[str, Any]:
        session = self._require_session(body)
        host = str(body.get("host", "")).strip() or "127.0.0.1"
        port = _require_int(body.get("port"), "port")
        response = session.request({"action": "connect", "host": host, "port": port})
        response["pid"] = session.pid
        return response

    def _handle_disconnect(self, body: dict[str, Any]) -> dict[str, Any]:
        session = self._require_session(body)
        response = session.request({"action": "disconnect"})
        response["pid"] = session.pid
        return response

    def _handle_request(self, body: dict[str, Any]) -> dict[str, Any]:
        session = self._require_session(body)
        obj_type = str(body.get("obj_type", "")).strip().upper()
        operation = str(body.get("operation", "")).strip().upper()
        instance_id = _require_int(body.get("instance_id", 0), "instance_id")
        data = body.get("data", "")
        response = session.request(
            {
                "action": "request",
                "obj_type": obj_type,
                "operation": operation,
                "instance_id": instance_id,
                "data": str(data),
            }
        )
        response["pid"] = session.pid
        return response

    def _handle_raw(self, body: dict[str, Any]) -> dict[str, Any]:
        session = self._require_session(body)
        response = session.request({"action": "raw", "raw_message": str(body.get("raw_message", ""))})
        response["pid"] = session.pid
        return response

    def _handle_preload(self, body: dict[str, Any]) -> dict[str, Any]:
        session = self._require_session(body)
        response = session.request({"action": "preload"})
        response["pid"] = session.pid
        return response

    def _require_session(self, body: dict[str, Any]) -> ClientSession:
        session_id = str(body.get("session_id", "")).strip()
        if not session_id:
            raise ValueError("session_id is required")
        return SESSIONS.require(session_id)

    def _read_json_body(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
        data = json.loads(raw_body)
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    def _write_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    server = ThreadingHTTPServer(("127.0.0.1", 8080), WebClientRequestHandler)
    print("Web UI local en http://127.0.0.1:8080")
    print("Usa el backend TCP existente en el host/puerto que indiques en la interfaz.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down web UI...")
    finally:
        SESSIONS.close_all()
        server.server_close()


if __name__ == "__main__":
    main()
