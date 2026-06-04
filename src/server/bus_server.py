"""
bus_server.py — Servidor TCP del Bus de Objetos
Proyecto: Bus de Objetos en Python — Etapa 4
Descripción: Capa de comunicación TCP que acepta múltiples clientes
             concurrentes usando threading.Thread. Delega TODA la lógica
             de negocio a dispatcher.py y object_server.py.
             Maneja desconexiones abruptas y errores sin terminar el servidor.
"""

import socket
import threading
import logging

from src.protocol.serializer import deserialize_message, serialize_response, DESER_OK
from src.server.dispatcher import dispatch

logger = logging.getLogger(__name__)


class BusServer:
    """
    Servidor TCP multi-hilo para el Bus de Objetos.

    Responsabilidades (solo comunicación):
        - Abrir socket TCP y escuchar conexiones.
        - Crear un hilo daemon por cada cliente.
        - Recibir mensajes del protocolo (delimitados por '\\n').
        - Invocar deserialize_message() + dispatch().
        - Enviar la respuesta al cliente.
        - Manejar desconexiones abruptas sin crash.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 9999,
                 backlog: int = 10):
        self._host = host
        self._port = port
        self._backlog = backlog
        self._server_socket: socket.socket | None = None
        self._accept_thread: threading.Thread | None = None
        self._running = False
        self._lock = threading.Lock()

    @property
    def port(self) -> int:
        """Returns the actual port the server is listening on."""
        if self._server_socket is not None:
            return self._server_socket.getsockname()[1]
        return self._port

    def start(self) -> None:
        """Inicia el servidor TCP en un hilo separado."""
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self._host, self._port))
        self._server_socket.listen(self._backlog)
        self._running = True

        self._accept_thread = threading.Thread(
            target=self._accept_loop, daemon=True
        )
        self._accept_thread.start()
        logger.info("BusServer listening on %s:%d", self._host, self.port)

    def stop(self) -> None:
        """Detiene el servidor cerrando el socket de escucha."""
        self._running = False
        if self._server_socket is not None:
            try:
                self._server_socket.close()
            except OSError:
                pass
            self._server_socket = None
        logger.info("BusServer stopped")

    def _accept_loop(self) -> None:
        """Bucle principal: acepta conexiones y crea un hilo por cliente."""
        while self._running:
            try:
                client_socket, addr = self._server_socket.accept()
                logger.info("Client connected: %s", addr)
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr),
                    daemon=True,
                )
                client_thread.start()
            except OSError:
                # Socket cerrado durante stop()
                break
            except Exception as e:
                if self._running:
                    logger.error("Accept error: %s", e)

    def _handle_client(self, client_socket: socket.socket,
                       addr: tuple) -> None:
        """
        Maneja la comunicación con un cliente individual.

        Lee mensajes delimitados por '\\n' usando un buffer para manejar
        la naturaleza stream de TCP (mensajes parciales o múltiples en
        un solo recv).
        """
        buffer = ""
        try:
            while self._running:
                data = client_socket.recv(4096)
                if not data:
                    # Cliente desconectado normalmente
                    break

                buffer += data.decode("utf-8", errors="replace")

                # Procesar todos los mensajes completos en el buffer
                while "\n" in buffer:
                    message, buffer = buffer.split("\n", 1)
                    message += "\n"  # Restaurar el delimitador para el protocolo

                    response = self._process_message(message)
                    try:
                        client_socket.sendall(response.encode("utf-8"))
                    except (BrokenPipeError, ConnectionResetError):
                        return

        except (ConnectionResetError, BrokenPipeError):
            logger.info("Client %s disconnected abruptly", addr)
        except Exception as e:
            logger.error("Error handling client %s: %s", addr, e)
        finally:
            try:
                client_socket.close()
            except OSError:
                pass
            logger.info("Client %s disconnected", addr)

    @staticmethod
    def _process_message(raw_message: str) -> str:
        """
        Procesa un mensaje crudo del protocolo.

        Deserializa → despacha → retorna respuesta serializada.
        NUNCA lanza excepción: cualquier error se traduce a ERROR|...\n.
        """
        try:
            code, msg = deserialize_message(raw_message)
            if code != DESER_OK or msg is None:
                return serialize_response(False, "MALFORMED_MESSAGE")
            return dispatch(msg)
        except Exception as e:
            logger.error("Unexpected error processing message: %s", e)
            return serialize_response(False, f"INTERNAL_ERROR:{e}")


def main():
    """Entry point para ejecutar el servidor standalone."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    server = BusServer()
    server.start()
    print(f"Bus Server running on 127.0.0.1:{server.port}")
    print("Press Ctrl+C to stop.")
    try:
        # Mantener vivo el hilo principal
        server._accept_thread.join()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.stop()


if __name__ == "__main__":
    main()
