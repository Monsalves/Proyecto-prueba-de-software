import pytest
import unittest
from src.server.object_server import _reset_server
from src.server.dispatcher import dispatch
from src.protocol.serializer import deserialize_message, serialize_request, DESER_OK, DESER_ERROR


def _create_via_serializer(obj_type: str, existing_id: int = 0) -> int:
    """
    Función auxiliar: crea una instancia usando el flujo completo
    deserializar → despachar y retorna el instance_id asignado.
    """
    raw = serialize_request(obj_type, "CREATE", existing_id, "")
    code, msg = deserialize_message(raw)
    assert code == DESER_OK, f"No se pudo deserializar: {raw}"
    response = dispatch(msg)
    assert response.startswith("OK|"), f"CREATE falló: {response}"
    return int(response.split("|")[1].strip())


class TestSerlializerDispatcherList(unittest.TestCase):
    """Interfaz Serializer↔Dispatcher — objetos LIST."""

    def setUp(self):
        _reset_server()
        self.list_id = _create_via_serializer("LIST")

    # ─── Mensaje válido ────────────────────────────────────────
    @pytest.mark.test_id("TI-SD-01")
    def test_list_insert_raw_valid(self):
        """Trama cruda INSERT válida parsea y ejecuta correctamente."""
        raw = serialize_request("LIST", "INSERT", self.list_id, "42")
        code, msg = deserialize_message(raw)
        self.assertEqual(code, DESER_OK)
        response = dispatch(msg)
        self.assertTrue(response.startswith("OK|"), msg=response)

    @pytest.mark.test_id("TI-SD-02")
    def test_list_size_raw_valid(self):
        """Trama cruda SIZE válida retorna el tamaño correcto."""
        # Insertar 2 elementos
        dispatch(deserialize_message(serialize_request("LIST", "INSERT", self.list_id, "1"))[1])
        dispatch(deserialize_message(serialize_request("LIST", "INSERT", self.list_id, "2"))[1])
        raw = serialize_request("LIST", "SIZE", self.list_id, "")
        _, msg = deserialize_message(raw)
        response = dispatch(msg)
        self.assertIn("2", response)

    @pytest.mark.test_id("TI-SD-03")
    def test_list_contains_raw_valid(self):
        """Trama cruda CONTAINS retorna resultado correcto después de INSERT."""
        dispatch(deserialize_message(serialize_request("LIST", "INSERT", self.list_id, "99"))[1])
        raw = serialize_request("LIST", "CONTAINS", self.list_id, "99")
        _, msg = deserialize_message(raw)
        response = dispatch(msg)
        self.assertTrue(response.startswith("OK|"))

    # ─── ID inexistente ───────────────────────────────────────
    @pytest.mark.test_id("TI-SD-04")
    def test_list_insert_missing_id_from_raw(self):
        """Trama cruda con ID inexistente produce ERROR|INSTANCE_NOT_FOUND."""
        raw = serialize_request("LIST", "INSERT", 9999, "10")
        _, msg = deserialize_message(raw)
        response = dispatch(msg)
        self.assertTrue(response.startswith("ERROR|"))
        self.assertIn("INSTANCE_NOT_FOUND", response)

    @pytest.mark.test_id("TI-SD-05")
    def test_list_get_missing_id_from_raw(self):
        """GET sobre ID inexistente retorna ERROR."""
        raw = serialize_request("LIST", "GET", 8888, "0")
        _, msg = deserialize_message(raw)
        response = dispatch(msg)
        self.assertTrue(response.startswith("ERROR|"))

    # ─── Mensaje malformado ───────────────────────────────────
    @pytest.mark.test_id("TI-SD-06")
    def test_malformed_missing_newline(self):
        """Trama sin \\n final es rechazada por el deserializador."""
        raw = "LIST|INSERT|1|42"  # Sin \n
        code, msg = deserialize_message(raw)
        self.assertEqual(code, DESER_ERROR)
        self.assertIsNone(msg)

    @pytest.mark.test_id("TI-SD-07")
    def test_malformed_invalid_object_type(self):
        """Trama con tipo de objeto inválido es rechazada por el deserializador."""
        raw = "QUEUE|INSERT|1|42\n"
        code, msg = deserialize_message(raw)
        self.assertEqual(code, DESER_ERROR)
        self.assertIsNone(msg)

    @pytest.mark.test_id("TI-SD-08")
    def test_malformed_invalid_operation(self):
        """Trama con operación desconocida es rechazada por el deserializador."""
        raw = "LIST|VOLAR|1|42\n"
        code, msg = deserialize_message(raw)
        self.assertEqual(code, DESER_ERROR)
        self.assertIsNone(msg)

    @pytest.mark.test_id("TI-SD-09")
    def test_malformed_non_integer_data_for_insert(self):
        """Trama INSERT con dato no numérico es rechazada por el deserializador."""
        raw = f"LIST|INSERT|{self.list_id}|abc\n"
        code, msg = deserialize_message(raw)
        self.assertEqual(code, DESER_ERROR)
        self.assertIsNone(msg)


class TestSerializerDispatcherStack(unittest.TestCase):
    """Interfaz Serializer↔Dispatcher — objetos STACK."""

    def setUp(self):
        _reset_server()
        self.stack_id = _create_via_serializer("STACK")

    @pytest.mark.test_id("TI-SD-10")
    def test_stack_push_raw_valid(self):
        raw = serialize_request("STACK", "PUSH", self.stack_id, "77")
        _, msg = deserialize_message(raw)
        response = dispatch(msg)
        self.assertTrue(response.startswith("OK|"))

    @pytest.mark.test_id("TI-SD-11")
    def test_stack_pop_after_push_raw_valid(self):
        dispatch(deserialize_message(serialize_request("STACK", "PUSH", self.stack_id, "55"))[1])
        raw = serialize_request("STACK", "POP", self.stack_id, "")
        _, msg = deserialize_message(raw)
        response = dispatch(msg)
        self.assertIn("55", response)

    @pytest.mark.test_id("TI-SD-12")
    def test_stack_push_missing_id_from_raw(self):
        raw = serialize_request("STACK", "PUSH", 9999, "10")
        _, msg = deserialize_message(raw)
        response = dispatch(msg)
        self.assertIn("INSTANCE_NOT_FOUND", response)

    @pytest.mark.test_id("TI-SD-13")
    def test_stack_malformed_push_no_data(self):
        """PUSH sin dato numérico es rechazado por el deserializador."""
        raw = f"STACK|PUSH|{self.stack_id}|\n"
        code, _ = deserialize_message(raw)
        self.assertEqual(code, DESER_ERROR)


class TestSerializerDispatcherTree(unittest.TestCase):
    """Interfaz Serializer↔Dispatcher — objetos TREE."""

    def setUp(self):
        _reset_server()
        self.tree_id = _create_via_serializer("TREE")

    @pytest.mark.test_id("TI-SD-14")
    def test_tree_insert_raw_valid(self):
        raw = serialize_request("TREE", "INSERT", self.tree_id, "50")
        _, msg = deserialize_message(raw)
        response = dispatch(msg)
        self.assertTrue(response.startswith("OK|"))

    @pytest.mark.test_id("TI-SD-15")
    def test_tree_search_raw_valid(self):
        dispatch(deserialize_message(serialize_request("TREE", "INSERT", self.tree_id, "30"))[1])
        raw = serialize_request("TREE", "SEARCH", self.tree_id, "30")
        _, msg = deserialize_message(raw)
        response = dispatch(msg)
        self.assertIn("FOUND", response)

    @pytest.mark.test_id("TI-SD-16")
    def test_tree_insert_missing_id_from_raw(self):
        raw = serialize_request("TREE", "INSERT", 9999, "10")
        _, msg = deserialize_message(raw)
        response = dispatch(msg)
        self.assertIn("INSTANCE_NOT_FOUND", response)

    @pytest.mark.test_id("TI-SD-17")
    def test_tree_malformed_negative_id(self):
        """ID negativo es rechazado por el deserializador."""
        raw = "TREE|INSERT|-1|50\n"
        code, _ = deserialize_message(raw)
        self.assertEqual(code, DESER_ERROR)


if __name__ == "__main__":
    unittest.main()
