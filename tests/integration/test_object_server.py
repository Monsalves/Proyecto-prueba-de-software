"""
test_object_server.py — Pruebas de Integración: Dispatcher↔ObjectServer
Proyecto: Bus de Objetos en Python — Etapa 3 / TSK-07
Agente IA: qa-tester-agent
Descripción: Crear múltiples instancias simultáneamente, obtener por ID
             correcto e ID inexistente. Valida el registro global del servidor.
"""

import unittest
import threading
from src.server.object_server import (
    server_create, server_get, server_delete,
    server_instance_count, _reset_server,
    SERVER_OK, SERVER_NOT_FOUND, SERVER_NULL_PTR, SERVER_INVALID_TYPE,
)
from src.objects.list_obj import List
from src.objects.stack_obj import Stack
from src.objects.tree_obj import Tree


class TestServerCreate(unittest.TestCase):
    """Pruebas de creación de instancias en el ObjectServer."""

    def setUp(self):
        _reset_server()

    def test_create_list_returns_ok(self):
        code, instance_id = server_create("LIST")
        self.assertEqual(code, SERVER_OK)
        self.assertIsNotNone(instance_id)

    def test_create_stack_returns_ok(self):
        code, instance_id = server_create("STACK")
        self.assertEqual(code, SERVER_OK)
        self.assertIsNotNone(instance_id)

    def test_create_tree_returns_ok(self):
        code, instance_id = server_create("TREE")
        self.assertEqual(code, SERVER_OK)
        self.assertIsNotNone(instance_id)

    def test_create_returns_unique_ids(self):
        _, id1 = server_create("LIST")
        _, id2 = server_create("LIST")
        _, id3 = server_create("STACK")
        ids = {id1, id2, id3}
        self.assertEqual(len(ids), 3)

    def test_create_invalid_type_returns_error(self):
        code, instance_id = server_create("QUEUE")
        self.assertEqual(code, SERVER_INVALID_TYPE)
        self.assertIsNone(instance_id)

    def test_create_none_type_returns_null_ptr(self):
        code, instance_id = server_create(None)
        self.assertEqual(code, SERVER_NULL_PTR)
        self.assertIsNone(instance_id)

    def test_create_increments_instance_count(self):
        server_create("LIST")
        server_create("STACK")
        self.assertEqual(server_instance_count(), 2)


class TestServerGet(unittest.TestCase):
    """Pruebas de recuperación de instancias por ID."""

    def setUp(self):
        _reset_server()

    def test_get_existing_list_instance(self):
        _, list_id = server_create("LIST")
        code, obj = server_get(list_id)
        self.assertEqual(code, SERVER_OK)
        self.assertIsInstance(obj, List)

    def test_get_existing_stack_instance(self):
        _, stack_id = server_create("STACK")
        code, obj = server_get(stack_id)
        self.assertEqual(code, SERVER_OK)
        self.assertIsInstance(obj, Stack)

    def test_get_existing_tree_instance(self):
        _, tree_id = server_create("TREE")
        code, obj = server_get(tree_id)
        self.assertEqual(code, SERVER_OK)
        self.assertIsInstance(obj, Tree)

    def test_get_missing_id_returns_not_found(self):
        code, obj = server_get(9999)
        self.assertEqual(code, SERVER_NOT_FOUND)
        self.assertIsNone(obj)

    def test_get_none_id_returns_null_ptr(self):
        code, obj = server_get(None)
        self.assertEqual(code, SERVER_NULL_PTR)
        self.assertIsNone(obj)

    def test_get_after_delete_returns_not_found(self):
        _, list_id = server_create("LIST")
        server_delete(list_id)
        code, _ = server_get(list_id)
        self.assertEqual(code, SERVER_NOT_FOUND)

    def test_get_returns_same_instance_on_repeated_calls(self):
        _, list_id = server_create("LIST")
        _, obj1 = server_get(list_id)
        _, obj2 = server_get(list_id)
        self.assertIs(obj1, obj2)


class TestServerDelete(unittest.TestCase):
    """Pruebas de eliminación de instancias."""

    def setUp(self):
        _reset_server()

    def test_delete_existing_returns_ok(self):
        _, list_id = server_create("LIST")
        code = server_delete(list_id)
        self.assertEqual(code, SERVER_OK)

    def test_delete_reduces_count(self):
        _, id1 = server_create("LIST")
        server_create("STACK")
        server_delete(id1)
        self.assertEqual(server_instance_count(), 1)

    def test_delete_missing_id_returns_not_found(self):
        code = server_delete(9999)
        self.assertEqual(code, SERVER_NOT_FOUND)

    def test_delete_none_id_returns_null_ptr(self):
        code = server_delete(None)
        self.assertEqual(code, SERVER_NULL_PTR)

    def test_double_delete_second_returns_not_found(self):
        _, list_id = server_create("LIST")
        server_delete(list_id)
        code = server_delete(list_id)
        self.assertEqual(code, SERVER_NOT_FOUND)


class TestServerMultipleInstances(unittest.TestCase):
    """Pruebas de múltiples instancias simultáneas."""

    def setUp(self):
        _reset_server()

    def test_create_ten_lists_unique_ids(self):
        ids = set()
        for _ in range(10):
            _, instance_id = server_create("LIST")
            ids.add(instance_id)
        self.assertEqual(len(ids), 10)

    def test_mixed_types_all_retrievable(self):
        _, lid = server_create("LIST")
        _, sid = server_create("STACK")
        _, tid = server_create("TREE")
        code_l, obj_l = server_get(lid)
        code_s, obj_s = server_get(sid)
        code_t, obj_t = server_get(tid)
        self.assertEqual(code_l, SERVER_OK)
        self.assertEqual(code_s, SERVER_OK)
        self.assertEqual(code_t, SERVER_OK)
        self.assertIsInstance(obj_l, List)
        self.assertIsInstance(obj_s, Stack)
        self.assertIsInstance(obj_t, Tree)

    def test_concurrent_creates_no_duplicate_ids(self):
        """10 hilos crean instancias simultáneamente; todos los IDs deben ser únicos."""
        ids: list[int] = []
        lock = threading.Lock()

        def create_and_collect():
            _, iid = server_create("LIST")
            with lock:
                ids.append(iid)

        threads = [threading.Thread(target=create_and_collect) for _ in range(10)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()

        self.assertEqual(len(ids), 10)
        self.assertEqual(len(set(ids)), 10, "Se detectaron IDs duplicados en creación concurrente")

    def test_instance_count_accurate_after_mixed_ops(self):
        _, id1 = server_create("LIST")
        _, id2 = server_create("STACK")
        server_create("TREE")
        server_delete(id2)
        self.assertEqual(server_instance_count(), 2)


if __name__ == "__main__":
    unittest.main()
