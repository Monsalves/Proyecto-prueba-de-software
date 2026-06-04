"""
bus_client.py — Cliente TCP del Bus de Objetos
Proyecto: Bus de Objetos en Python — Etapa 4
Descripción: API de alto nivel que se conecta al BusServer vía TCP.
             Serializa solicitudes, envía por socket, recibe respuestas,
             y las deserializa. Reutiliza serializer.py del protocolo.
"""

import socket

from src.protocol.serializer import serialize_request


class BusClientError(Exception):
    """Error raised by BusClient when the server returns an ERROR response."""
    pass


class BusClient:
    """
    Cliente TCP para el Bus de Objetos.

    Uso:
        client = BusClient()
        client.connect()
        list_id = client.list_create()
        client.list_insert(list_id, 42)
        value = client.list_get(list_id, 0)
        client.close()
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 9999):
        self._host = host
        self._port = port
        self._socket: socket.socket | None = None

    def connect(self) -> None:
        """Establishes a TCP connection to the BusServer."""
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((self._host, self._port))

    def close(self) -> None:
        """Closes the TCP connection."""
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass
            self._socket = None

    def send_raw(self, raw_message: str) -> str:
        """
        Sends a raw protocol message and returns the raw response.
        Useful for testing malformed messages.
        """
        if self._socket is None:
            raise BusClientError("Not connected")
        self._socket.sendall(raw_message.encode("utf-8"))
        return self._recv_response()

    # ─── Internal communication ────────────────────────────────

    def _request(self, obj_type: str, operation: str,
                 instance_id: int, data: str = "") -> str:
        """
        Sends a protocol request and returns the parsed response data.

        Raises:
            BusClientError: if the server returns an ERROR response.
        """
        if self._socket is None:
            raise BusClientError("Not connected")

        message = serialize_request(obj_type, operation, instance_id, data)
        self._socket.sendall(message.encode("utf-8"))

        raw_response = self._recv_response()
        return self._parse_response(raw_response)

    def _recv_response(self) -> str:
        """Reads a complete response from the server (delimited by '\\n')."""
        buffer = ""
        while "\n" not in buffer:
            data = self._socket.recv(4096)
            if not data:
                raise BusClientError("Server closed connection")
            buffer += data.decode("utf-8")
        # Return only the first complete message
        response, _ = buffer.split("\n", 1)
        return response

    @staticmethod
    def _parse_response(raw_response: str) -> str:
        """
        Parses 'OK|data' or 'ERROR|data' response.

        Returns the data portion on OK.
        Raises BusClientError on ERROR.
        """
        if "|" not in raw_response:
            raise BusClientError(f"Invalid response: {raw_response}")

        status, data = raw_response.split("|", 1)

        if status == "OK":
            return data
        raise BusClientError(data)

    # ─── LIST API ──────────────────────────────────────────────

    def list_create(self) -> int:
        """Creates a new List instance. Returns the instance ID."""
        result = self._request("LIST", "CREATE", 0)
        return int(result)

    def list_insert(self, instance_id: int, value: int) -> None:
        """Inserts a value at the end of the list."""
        self._request("LIST", "INSERT", instance_id, str(value))

    def list_get(self, instance_id: int, position: int) -> int:
        """Gets the value at the given position."""
        result = self._request("LIST", "GET", instance_id, str(position))
        return int(result)

    def list_remove(self, instance_id: int, position: int) -> None:
        """Removes the element at the given position."""
        self._request("LIST", "REMOVE", instance_id, str(position))

    def list_size(self, instance_id: int) -> int:
        """Returns the number of elements in the list."""
        result = self._request("LIST", "SIZE", instance_id)
        return int(result)

    def list_contains(self, instance_id: int, value: int) -> bool:
        """Returns True if the value exists in the list."""
        result = self._request("LIST", "CONTAINS", instance_id, str(value))
        return result == "1"

    # ─── STACK API ─────────────────────────────────────────────

    def stack_create(self) -> int:
        """Creates a new Stack instance. Returns the instance ID."""
        result = self._request("STACK", "CREATE", 0)
        return int(result)

    def stack_push(self, instance_id: int, value: int) -> None:
        """Pushes a value onto the stack."""
        self._request("STACK", "PUSH", instance_id, str(value))

    def stack_pop(self, instance_id: int) -> int:
        """Pops and returns the top value from the stack."""
        result = self._request("STACK", "POP", instance_id)
        return int(result)

    def stack_peek(self, instance_id: int) -> int:
        """Returns the top value without removing it."""
        result = self._request("STACK", "PEEK", instance_id)
        return int(result)

    def stack_is_empty(self, instance_id: int) -> bool:
        """Returns True if the stack is empty."""
        result = self._request("STACK", "IS_EMPTY", instance_id)
        return result == "1"

    # ─── TREE API ──────────────────────────────────────────────

    def tree_create(self) -> int:
        """Creates a new Tree instance. Returns the instance ID."""
        result = self._request("TREE", "CREATE", 0)
        return int(result)

    def tree_insert(self, instance_id: int, value: int) -> None:
        """Inserts a value into the BST."""
        self._request("TREE", "INSERT", instance_id, str(value))

    def tree_search(self, instance_id: int, value: int) -> bool:
        """Returns True if the value exists in the tree."""
        try:
            result = self._request("TREE", "SEARCH", instance_id, str(value))
            return result == "FOUND"
        except BusClientError as e:
            if "NOT_FOUND" in str(e):
                return False
            raise

    def tree_delete(self, instance_id: int, value: int) -> None:
        """Deletes a value from the BST."""
        self._request("TREE", "DELETE", instance_id, str(value))

    def tree_inorder(self, instance_id: int) -> list[int]:
        """Returns the inorder traversal as a list of integers."""
        result = self._request("TREE", "INORDER", instance_id)
        if not result:
            return []
        return [int(x) for x in result.split(",")]
