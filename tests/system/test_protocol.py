import pytest
"""
test_protocol.py — Pruebas de Protocolo y Robustez del Bus de Objetos
Proyecto: Bus de Objetos en Python — Etapa 4
Descripción: Valida que el servidor responde ERROR correctamente ante
             mensajes malformados, objetos inválidos, IDs inexistentes,
             operaciones sobre estructuras vacías e índices fuera de rango.
             El servidor NUNCA debe crashear ante estas entradas.
"""

import time
import unittest

from src.server.bus_server import BusServer
from src.client.bus_client import BusClient, BusClientError
from src.server.object_server import _reset_server


# ─── Fixture compartido ──────────────────────────────────────────

_server: BusServer | None = None
_server_port: int = 0


def setUpModule():
    global _server, _server_port
    _reset_server()
    _server = BusServer(host="127.0.0.1", port=0)
    _server.start()
    _server_port = _server.port
    time.sleep(0.1)


def tearDownModule():
    global _server
    if _server is not None:
        _server.stop()
        _server = None


def _make_client() -> BusClient:
    client = BusClient(host="127.0.0.1", port=_server_port)
    client.connect()
    return client


# ═══════════════════════════════════════════════════════════════════

class TestProtocolRobustness(unittest.TestCase):
    """
    5 casos de error del protocolo enviados por TCP real.
    En cada caso se verifica:
        1. La respuesta contiene ERROR.
        2. El servidor sigue activo después del error.
    """

    def setUp(self):
        _reset_server()
        self.client = _make_client()

    def tearDown(self):
        self.client.close()

    # ─── Caso 1: Mensaje malformado (sin separadores '|') ─────

    @pytest.mark.test_id("TS-PR-01")
    def test_malformed_message_no_separators(self):
        """Envía un mensaje sin el carácter '|'. Espera ERROR."""
        response = self.client.send_raw("ESTO_NO_TIENE_SEPARADORES\n")
        self.assertIn("ERROR", response)

        # Verificar que el servidor sigue activo
        self._assert_server_alive()

    # ─── Caso 2: Objeto inválido ──────────────────────────────

    @pytest.mark.test_id("TS-PR-02")
    def test_invalid_object_type(self):
        """Envía QUEUE|CREATE|0| — QUEUE no es un tipo válido."""
        response = self.client.send_raw("QUEUE|CREATE|0|\n")
        self.assertIn("ERROR", response)

        self._assert_server_alive()

    # ─── Caso 3: ID de instancia inexistente ──────────────────

    @pytest.mark.test_id("TS-PR-03")
    def test_nonexistent_instance_id(self):
        """Envía LIST|GET|999|0 — el ID 999 no existe."""
        response = self.client.send_raw("LIST|GET|999|0\n")
        self.assertIn("ERROR", response)

        self._assert_server_alive()

    # ─── Caso 4: Operación sobre estructura vacía ─────────────

    @pytest.mark.test_id("TS-PR-04")
    def test_operation_on_empty_structure(self):
        """Crea un Stack y hace POP sin push previo. Espera ERROR."""
        # Crear stack para obtener un ID válido
        stack_id = self.client.stack_create()

        # POP sobre stack vacío
        with self.assertRaises(BusClientError) as ctx:
            self.client.stack_pop(stack_id)
        self.assertIn("STACK_EMPTY", str(ctx.exception))

        self._assert_server_alive()

    # ─── Caso 5: Índice fuera de rango ────────────────────────

    @pytest.mark.test_id("TS-PR-05")
    def test_index_out_of_range(self):
        """Crea una List con 3 elementos e intenta GET en posición 100."""
        list_id = self.client.list_create()
        for v in [10, 20, 30]:
            self.client.list_insert(list_id, v)

        with self.assertRaises(BusClientError) as ctx:
            self.client.list_get(list_id, 100)
        self.assertIn("OUT_OF_BOUNDS", str(ctx.exception))

        self._assert_server_alive()

    # ─── Casos adicionales de robustez ────────────────────────

    @pytest.mark.test_id("TS-PR-06")
    def test_empty_message(self):
        """Envía solo un newline."""
        response = self.client.send_raw("\n")
        self.assertIn("ERROR", response)
        self._assert_server_alive()

    @pytest.mark.test_id("TS-PR-07")
    def test_partial_message(self):
        """Envía un mensaje con solo 2 campos."""
        response = self.client.send_raw("LIST|CREATE\n")
        self.assertIn("ERROR", response)
        self._assert_server_alive()

    @pytest.mark.test_id("TS-PR-08")
    def test_negative_instance_id(self):
        """Envía un ID negativo."""
        response = self.client.send_raw("LIST|GET|-1|0\n")
        self.assertIn("ERROR", response)
        self._assert_server_alive()

    # ─── Helper ───────────────────────────────────────────────

    def _assert_server_alive(self):
        """Verifica que el servidor sigue respondiendo después de un error."""
        # Crear una nueva conexión y hacer una operación válida
        check_client = _make_client()
        try:
            list_id = check_client.list_create()
            self.assertGreater(list_id, 0)
        finally:
            check_client.close()


if __name__ == "__main__":
    unittest.main()
