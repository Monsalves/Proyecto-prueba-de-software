import unittest
from src.server.object_server import _reset_server
from src.server.dispatcher import dispatch
from src.protocol.serializer import deserialize_message, serialize_request, DESER_OK
from tests.integration.stubs.socket_stub import SocketStub


# ─── Helper: flujo completo socket crudo → respuesta ───────────

def _handle_raw(socket_stub: SocketStub) -> str:
    """
    Simula el bucle de un servidor real:
      1. Lee la trama del socket.
      2. Deserializa.
      3. Despacha.
      4. Envía la respuesta de vuelta al socket.
    Retorna la respuesta enviada.
    """
    raw = socket_stub.readline()
    code, msg = deserialize_message(raw)
    if code != DESER_OK:
        response = "ERROR|MALFORMED_MESSAGE\n"
    else:
        response = dispatch(msg)
    socket_stub.send(response)
    return response


def _socket_for(obj_type: str, operation: str,
                instance_id: int, data: str = "") -> SocketStub:
    """Construye un SocketStub pre-cargado con una trama de protocolo."""
    raw = serialize_request(obj_type, operation, instance_id, data)
    return SocketStub(initial_data=raw)


# ─── Pruebas ───────────────────────────────────────────────────

class TestDispatcherSocketCreate(unittest.TestCase):
    """CREATE a través del flujo SocketStub→Serializer→Dispatcher."""

    def setUp(self):
        _reset_server()

    def test_create_list_via_socket_returns_ok(self):
        """Trama CREATE|LIST pasa por el socket y retorna OK con el ID."""
        stub = _socket_for("LIST", "CREATE", 0, "")
        response = _handle_raw(stub)
        self.assertTrue(response.startswith("OK|"), msg=response)
        # El servidor escribió la respuesta en el buffer de envío
        self.assertEqual(stub.get_sent_data(), response)

    def test_create_stack_via_socket_returns_ok(self):
        stub = _socket_for("STACK", "CREATE", 0, "")
        response = _handle_raw(stub)
        self.assertTrue(response.startswith("OK|"), msg=response)

    def test_create_tree_via_socket_returns_ok(self):
        stub = _socket_for("TREE", "CREATE", 0, "")
        response = _handle_raw(stub)
        self.assertTrue(response.startswith("OK|"), msg=response)


class TestDispatcherSocketOperations(unittest.TestCase):
    """Operaciones sobre instancias a través del flujo SocketStub completo."""

    def setUp(self):
        _reset_server()
        # Crear una instancia LIST directamente vía Dispatcher para obtener su ID
        resp = dispatch(deserialize_message(
            serialize_request("LIST", "CREATE", 0, "")
        )[1])
        self.list_id = int(resp.split("|")[1].strip())

        resp = dispatch(deserialize_message(
            serialize_request("STACK", "CREATE", 0, "")
        )[1])
        self.stack_id = int(resp.split("|")[1].strip())

        resp = dispatch(deserialize_message(
            serialize_request("TREE", "CREATE", 0, "")
        )[1])
        self.tree_id = int(resp.split("|")[1].strip())

    def test_list_insert_via_socket(self):
        """INSERT en List retorna OK desde el flujo de socket."""
        stub = _socket_for("LIST", "INSERT", self.list_id, "99")
        response = _handle_raw(stub)
        self.assertTrue(response.startswith("OK|"), msg=response)

    def test_stack_push_via_socket(self):
        """PUSH en Stack retorna OK desde el flujo de socket."""
        stub = _socket_for("STACK", "PUSH", self.stack_id, "42")
        response = _handle_raw(stub)
        self.assertTrue(response.startswith("OK|"), msg=response)

    def test_tree_insert_via_socket(self):
        """INSERT en Tree retorna OK desde el flujo de socket."""
        stub = _socket_for("TREE", "INSERT", self.tree_id, "50")
        response = _handle_raw(stub)
        self.assertTrue(response.startswith("OK|"), msg=response)

    def test_get_sent_data_matches_response(self):
        """Verifica que el buffer de envío del SocketStub contiene la respuesta exacta."""
        stub = _socket_for("LIST", "SIZE", self.list_id, "")
        response = _handle_raw(stub)
        self.assertEqual(stub.get_sent_data(), response)

    def test_missing_instance_id_via_socket(self):
        """ID inexistente en trama cruda retorna ERROR|INSTANCE_NOT_FOUND."""
        stub = _socket_for("STACK", "PUSH", 9999, "1")
        response = _handle_raw(stub)
        self.assertTrue(response.startswith("ERROR|"))
        self.assertIn("INSTANCE_NOT_FOUND", response)


class TestDispatcherSocketMalformed(unittest.TestCase):
    """Tramas malformadas detectadas en el flujo SocketStub→Serializer."""

    def setUp(self):
        _reset_server()

    def test_malformed_no_newline(self):
        """Trama sin \\n produce ERROR|MALFORMED_MESSAGE."""
        stub = SocketStub(initial_data="LIST|INSERT|1|42")  # Sin \n
        response = _handle_raw(stub)
        self.assertTrue(response.startswith("ERROR|"))
        self.assertIn("MALFORMED", response)

    def test_malformed_bad_object_type(self):
        """Tipo de objeto inválido produce ERROR|MALFORMED_MESSAGE."""
        stub = SocketStub(initial_data="QUEUE|INSERT|1|42\n")
        response = _handle_raw(stub)
        self.assertTrue(response.startswith("ERROR|"))
        self.assertIn("MALFORMED", response)

    def test_malformed_bad_operation(self):
        """Operación desconocida produce ERROR|MALFORMED_MESSAGE."""
        stub = SocketStub(initial_data="LIST|VOLAR|1|42\n")
        response = _handle_raw(stub)
        self.assertTrue(response.startswith("ERROR|"))

    def test_socket_send_buffer_is_empty_before_call(self):
        """El buffer de envío del stub está vacío antes de cualquier send()."""
        stub = SocketStub(initial_data="LIST|SIZE|1|\n")
        self.assertEqual(stub.get_sent_data(), "")

    def test_socket_closed_raises_on_send(self):
        """Un socket cerrado lanza OSError al intentar enviar."""
        stub = SocketStub()
        stub.close()
        self.assertTrue(stub.is_closed())
        with self.assertRaises(OSError):
            stub.send("OK|0\n")


class TestDispatcherSocketFullWorkflow(unittest.TestCase):
    """Flujo completo: CREATE → OP → DESTROY a través del SocketStub."""

    def setUp(self):
        _reset_server()

    def _create_via_socket(self, obj_type: str) -> int:
        stub = _socket_for(obj_type, "CREATE", 0, "")
        response = _handle_raw(stub)
        self.assertTrue(response.startswith("OK|"), msg=response)
        return int(response.split("|")[1].strip())

    def test_full_workflow_list_via_socket(self):
        # CREATE
        list_id = self._create_via_socket("LIST")
        # INSERT
        stub = _socket_for("LIST", "INSERT", list_id, "10")
        self.assertTrue(_handle_raw(stub).startswith("OK|"))
        # SIZE
        stub = _socket_for("LIST", "SIZE", list_id, "")
        self.assertIn("1", _handle_raw(stub))
        # DESTROY
        stub = SocketStub(initial_data=f"LIST|DESTROY|{list_id}|\n")
        # DESTROY no es parte del protocolo serializer, lo despachamos directo
        from tests.integration.stubs.serializer_stub import make_destroy
        resp_destroy = dispatch(make_destroy(list_id, "LIST"))
        self.assertEqual(resp_destroy.strip(), "OK|DESTROYED")

    def test_full_workflow_tree_via_socket(self):
        # CREATE
        tree_id = self._create_via_socket("TREE")
        # INSERT
        for v in [30, 10, 20]:
            stub = _socket_for("TREE", "INSERT", tree_id, str(v))
            self.assertTrue(_handle_raw(stub).startswith("OK|"))
        # INORDER
        stub = _socket_for("TREE", "INORDER", tree_id, "")
        response = _handle_raw(stub)
        self.assertIn("10,20,30", response)


if __name__ == "__main__":
    unittest.main()
