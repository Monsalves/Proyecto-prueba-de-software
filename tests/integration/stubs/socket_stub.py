"""
socket_stub.py — Stub de Socket TCP para Pruebas de Integración
Proyecto: Bus de Objetos en Python — Etapa 3
Descripción: Reemplaza el socket TCP real con un buffer io.StringIO.
             Permite simular el envío y recepción de mensajes del protocolo
             sin levantar conexiones de red reales.
"""

import io


class SocketStub:
    """
    Simula un socket TCP mediante buffers io.StringIO.
    Interfaz compatible con socket.socket: send/recv sobre strings.
    """

    def __init__(self, initial_data: str = ""):
        """
        Args:
            initial_data: Datos que el stub 'recibirá' en el primer recv.
        """
        self._recv_buffer = io.StringIO(initial_data)
        self._send_buffer = io.StringIO()
        self._closed = False

    def send(self, data: str) -> int:
        """
        Escribe datos en el buffer de envío.
        Retorna el número de caracteres escritos.
        """
        if self._closed:
            raise OSError("SocketStub: send on closed socket")
        self._send_buffer.write(data)
        return len(data)

    def recv(self, size: int = 1024) -> str:
        """
        Lee hasta `size` caracteres del buffer de recepción.
        Retorna '' si no hay más datos (simula EOF).
        """
        if self._closed:
            raise OSError("SocketStub: recv on closed socket")
        return self._recv_buffer.read(size)

    def readline(self) -> str:
        """
        Lee una línea completa del buffer de recepción (hasta '\\n' inclusive).
        Retorna '' en EOF.
        """
        if self._closed:
            raise OSError("SocketStub: readline on closed socket")
        return self._recv_buffer.readline()

    def get_sent_data(self) -> str:
        """Retorna todo lo que se ha enviado via send() desde la creación."""
        return self._send_buffer.getvalue()

    def close(self) -> None:
        """Marca el stub como cerrado."""
        self._closed = True

    def is_closed(self) -> bool:
        """Retorna True si el stub fue cerrado."""
        return self._closed

    def reset(self, new_data: str = "") -> None:
        """Reinicia los buffers con nuevos datos de recepción."""
        self._recv_buffer = io.StringIO(new_data)
        self._send_buffer = io.StringIO()
        self._closed = False
