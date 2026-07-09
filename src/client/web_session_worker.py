"""
web_session_worker.py - Worker de proceso por sesion para la UI web.

Cada sesion del cliente web mantiene su propio proceso Python y su propia
instancia de BusClient. El proceso principal solo coordina via Pipe.
"""

from __future__ import annotations

from multiprocessing.connection import Connection
from typing import Any

from src.client.bus_client import BusClient, BusClientError
from src.protocol.serializer import serialize_request


def _response_payload(ok: bool, **extra: Any) -> dict[str, Any]:
    payload = {"ok": ok}
    payload.update(extra)
    return payload


def _invoke_operation(client: BusClient, obj_type: str, operation: str,
                      instance_id: int, data: str = "") -> dict[str, Any]:
    raw_request = serialize_request(obj_type, operation, instance_id, data)
    raw_response = client.send_raw(raw_request)
    if "|" not in raw_response:
        raise BusClientError(f"Invalid response: {raw_response}")
    status, detail = raw_response.split("|", 1)
    if status == "OK":
        return _response_payload(
            True,
            response=detail,
            raw_request=raw_request.rstrip("\n"),
            raw_response=raw_response,
        )
    return _response_payload(
        False,
        error=detail,
        raw_request=raw_request.rstrip("\n"),
        raw_response=raw_response,
    )


def _preload_data(client: BusClient) -> dict[str, Any]:
    list_id = client.list_create()
    for value in (10, 20, 30):
        client.list_insert(list_id, value)

    stack_id = client.stack_create()
    for value in (1, 2, 3):
        client.stack_push(stack_id, value)

    tree_id = client.tree_create()
    for value in (5, 3, 8, 1, 4):
        client.tree_insert(tree_id, value)

    return _response_payload(
        True,
        response={
            "list_id": list_id,
            "stack_id": stack_id,
            "tree_id": tree_id,
            "list_values": [10, 20, 30],
            "stack_top": 3,
            "tree_inorder": [1, 3, 4, 5, 8],
        },
    )


def worker_main(conn: Connection) -> None:
    client: BusClient | None = None
    host: str | None = None
    port: int | None = None

    while True:
        try:
            command = conn.recv()
        except EOFError:
            break

        action = command.get("action")

        try:
            if action == "stop":
                if client is not None:
                    client.close()
                conn.send(_response_payload(True, stopped=True))
                break

            if action == "connect":
                if client is not None:
                    client.close()
                host = str(command["host"])
                port = int(command["port"])
                client = BusClient(host=host, port=port)
                client.connect()
                conn.send(_response_payload(True, connected=True, host=host, port=port))
                continue

            if action == "disconnect":
                if client is not None:
                    client.close()
                    client = None
                conn.send(_response_payload(True, connected=False))
                continue

            if client is None:
                raise BusClientError("Not connected")

            if action == "request":
                conn.send(
                    _invoke_operation(
                        client=client,
                        obj_type=str(command["obj_type"]),
                        operation=str(command["operation"]),
                        instance_id=int(command["instance_id"]),
                        data=str(command.get("data", "")),
                    )
                )
                continue

            if action == "raw":
                raw_message = str(command.get("raw_message", ""))
                if not raw_message.endswith("\n"):
                    raw_message += "\n"
                raw_response = client.send_raw(raw_message)
                if "|" not in raw_response:
                    raise BusClientError(f"Invalid response: {raw_response}")
                status, detail = raw_response.split("|", 1)
                conn.send(
                    _response_payload(
                        status == "OK",
                        response=detail if status == "OK" else None,
                        error=detail if status != "OK" else None,
                        raw_request=raw_message.rstrip("\n"),
                        raw_response=raw_response,
                    )
                )
                continue

            if action == "preload":
                conn.send(_preload_data(client))
                continue

            conn.send(_response_payload(False, error=f"UNKNOWN_ACTION:{action}"))
        except Exception as exc:
            conn.send(_response_payload(False, error=str(exc), host=host, port=port))

    try:
        conn.close()
    except OSError:
        pass
