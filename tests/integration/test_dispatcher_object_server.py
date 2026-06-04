import unittest
import threading
from src.server.object_server import (
    server_get, server_instance_count, _reset_server,
    SERVER_OK, SERVER_NOT_FOUND,
)
from src.server.dispatcher import dispatch
from src.objects.list_obj import List
from src.objects.stack_obj import Stack
from src.objects.tree_obj import Tree
from tests.integration.stubs.serializer_stub import make_create


class TestDispatcherServerCreate(unittest.TestCase):
    """Dispatcher delega CREATE al ObjectServer correctamente."""

    def setUp(self):
        _reset_server()

    def test_create_list_registers_instance(self):
        """CREATE LIST vía Dispatcher registra una instancia List en el servidor."""
        response = dispatch(make_create("LIST"))
        self.assertTrue(response.startswith("OK|"))
        instance_id = int(response.split("|")[1].strip())
        code, obj = server_get(instance_id)
        self.assertEqual(code, SERVER_OK)
        self.assertIsInstance(obj, List)

    def test_create_stack_registers_instance(self):
        """CREATE STACK vía Dispatcher registra una instancia Stack en el servidor."""
        response = dispatch(make_create("STACK"))
        instance_id = int(response.split("|")[1].strip())
        code, obj = server_get(instance_id)
        self.assertEqual(code, SERVER_OK)
        self.assertIsInstance(obj, Stack)

    def test_create_tree_registers_instance(self):
        """CREATE TREE vía Dispatcher registra una instancia Tree en el servidor."""
        response = dispatch(make_create("TREE"))
        instance_id = int(response.split("|")[1].strip())
        code, obj = server_get(instance_id)
        self.assertEqual(code, SERVER_OK)
        self.assertIsInstance(obj, Tree)

    def test_multiple_creates_have_unique_ids(self):
        """Múltiples CREATE seguidos producen IDs únicos en el servidor."""
        ids = set()
        for obj_type in ["LIST", "STACK", "TREE", "LIST", "STACK"]:
            resp = dispatch(make_create(obj_type))
            self.assertTrue(resp.startswith("OK|"))
            ids.add(int(resp.split("|")[1].strip()))
        self.assertEqual(len(ids), 5, "Se detectaron IDs duplicados en creaciones secuenciales")

    def test_create_increments_server_count(self):
        """El conteo de instancias en el servidor sube con cada CREATE."""
        dispatch(make_create("LIST"))
        dispatch(make_create("STACK"))
        dispatch(make_create("TREE"))
        self.assertEqual(server_instance_count(), 3)

    def test_create_invalid_type_does_not_register(self):
        """CREATE con tipo inválido no altera el conteo del servidor."""
        dispatch(make_create("QUEUE"))
        self.assertEqual(server_instance_count(), 0)


class TestDispatcherServerGet(unittest.TestCase):
    """Dispatcher obtiene instancias correctamente por ID."""

    def setUp(self):
        _reset_server()

    def test_get_after_create_via_dispatcher(self):
        """ID retornado por CREATE permite recuperar la instancia desde server_get."""
        resp = dispatch(make_create("LIST"))
        instance_id = int(resp.split("|")[1].strip())
        code, obj = server_get(instance_id)
        self.assertEqual(code, SERVER_OK)
        self.assertIsNotNone(obj)

    def test_get_nonexistent_id_returns_not_found(self):
        """ID que nunca fue creado retorna SERVER_NOT_FOUND."""
        code, obj = server_get(99999)
        self.assertEqual(code, SERVER_NOT_FOUND)
        self.assertIsNone(obj)

    def test_get_after_destroy_returns_not_found(self):
        """Después de DESTROY, server_get devuelve NOT_FOUND para el mismo ID."""
        from tests.integration.stubs.serializer_stub import make_destroy
        resp = dispatch(make_create("STACK"))
        instance_id = int(resp.split("|")[1].strip())
        dispatch(make_destroy(instance_id))
        code, _ = server_get(instance_id)
        self.assertEqual(code, SERVER_NOT_FOUND)

    def test_same_id_returns_same_object_reference(self):
        """server_get retorna siempre la misma referencia de objeto para un ID dado."""
        resp = dispatch(make_create("TREE"))
        instance_id = int(resp.split("|")[1].strip())
        _, obj1 = server_get(instance_id)
        _, obj2 = server_get(instance_id)
        self.assertIs(obj1, obj2)


class TestDispatcherServerConcurrentCreate(unittest.TestCase):
    """Crear múltiples instancias simultáneamente a través del Dispatcher."""

    def setUp(self):
        _reset_server()

    def test_ten_threads_create_unique_ids(self):
        """10 hilos llaman a CREATE vía Dispatcher simultáneamente; todos los IDs son únicos."""
        ids: list = []
        errors: list = []
        lock = threading.Lock()

        def create_one():
            response = dispatch(make_create("LIST"))
            with lock:
                if response.startswith("OK|"):
                    ids.append(int(response.split("|")[1].strip()))
                else:
                    errors.append(response)

        threads = [threading.Thread(target=create_one) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [], f"Hubo errores en creaciones: {errors}")
        self.assertEqual(len(ids), 10)
        self.assertEqual(len(set(ids)), 10, "Se detectaron IDs duplicados en creación concurrente")

    def test_twenty_threads_mixed_types_unique_ids(self):
        """20 hilos crean tipos mixtos; todos los IDs deben ser únicos."""
        types = ["LIST", "STACK", "TREE"] * 6 + ["LIST", "STACK"]
        ids: list = []
        lock = threading.Lock()

        def create_typed(obj_type):
            resp = dispatch(make_create(obj_type))
            with lock:
                if resp.startswith("OK|"):
                    ids.append(int(resp.split("|")[1].strip()))

        threads = [threading.Thread(target=create_typed, args=(t,)) for t in types]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(ids), 20)
        self.assertEqual(len(set(ids)), 20, "IDs duplicados en creación mixta concurrente")

    def test_concurrent_creates_all_retrievable_from_server(self):
        """Todas las instancias creadas concurrentemente son recuperables por ID."""
        ids: list = []
        lock = threading.Lock()

        def create_and_store():
            resp = dispatch(make_create("STACK"))
            with lock:
                if resp.startswith("OK|"):
                    ids.append(int(resp.split("|")[1].strip()))

        threads = [threading.Thread(target=create_and_store) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for instance_id in ids:
            code, obj = server_get(instance_id)
            self.assertEqual(code, SERVER_OK, f"No se pudo recuperar la instancia {instance_id}")
            self.assertIsNotNone(obj)


if __name__ == "__main__":
    unittest.main()
