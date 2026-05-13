"""
test_dispatcher.py — Pruebas de Integración: Serializer↔Dispatcher↔Objetos
Proyecto: Bus de Objetos en Python — Etapa 3 / TSK-06
Agente IA: qa-tester-agent
Descripción: Mínimo 3 casos por interfaz: válido, ID inexistente, malformado.
             Usa stubs para aislar de red y de deserialize_message.
"""

import unittest
from src.server.object_server import server_create, _reset_server, SERVER_OK
from src.server.dispatcher import dispatch
from tests.integration.stubs.serializer_stub import (
    make_list_insert, make_list_get, make_list_size, make_list_remove,
    make_stack_push, make_stack_pop, make_stack_peek,
    make_tree_insert, make_tree_search, make_tree_delete, make_tree_inorder,
    make_invalid_instance, make_malformed,
)


class TestDispatcherListInterface(unittest.TestCase):
    """Interfaz Serializer↔Dispatcher para objetos LIST."""

    def setUp(self):
        _reset_server()
        code, self.list_id = server_create("LIST")
        self.assertEqual(code, SERVER_OK)

    # ─── Caso válido ───────────────────────────────────────────
    def test_list_insert_valid(self):
        msg = make_list_insert(self.list_id, 42)
        response = dispatch(msg)
        self.assertTrue(response.startswith("OK|"), msg=response)

    def test_list_get_valid(self):
        dispatch(make_list_insert(self.list_id, 99))
        msg = make_list_get(self.list_id, 0)
        response = dispatch(msg)
        self.assertIn("99", response)

    def test_list_size_valid(self):
        dispatch(make_list_insert(self.list_id, 1))
        dispatch(make_list_insert(self.list_id, 2))
        response = dispatch(make_list_size(self.list_id))
        self.assertIn("2", response)

    # ─── Caso ID inexistente ───────────────────────────────────
    def test_list_insert_missing_id(self):
        msg = make_invalid_instance("LIST", "INSERT", 9999)
        response = dispatch(msg)
        self.assertTrue(response.startswith("ERROR|"), msg=response)
        self.assertIn("INSTANCE_NOT_FOUND", response)

    def test_list_get_missing_id(self):
        msg = make_invalid_instance("LIST", "GET", 8888)
        response = dispatch(msg)
        self.assertTrue(response.startswith("ERROR|"))

    def test_list_remove_missing_id(self):
        msg = make_invalid_instance("LIST", "REMOVE", 7777)
        response = dispatch(msg)
        self.assertTrue(response.startswith("ERROR|"))

    # ─── Caso malformado (operación inválida para el tipo) ─────
    def test_list_with_push_operation(self):
        msg = make_malformed("LIST", "PUSH", self.list_id)
        response = dispatch(msg)
        self.assertTrue(response.startswith("ERROR|"))
        self.assertIn("INVALID_OPERATION_FOR_LIST", response)

    def test_list_with_inorder_operation(self):
        msg = make_malformed("LIST", "INORDER", self.list_id)
        response = dispatch(msg)
        self.assertTrue(response.startswith("ERROR|"))

    def test_dispatch_none_message(self):
        response = dispatch(None)
        self.assertTrue(response.startswith("ERROR|"))
        self.assertIn("NULL_MESSAGE", response)


class TestDispatcherStackInterface(unittest.TestCase):
    """Interfaz Serializer↔Dispatcher para objetos STACK."""

    def setUp(self):
        _reset_server()
        code, self.stack_id = server_create("STACK")
        self.assertEqual(code, SERVER_OK)

    # ─── Caso válido ───────────────────────────────────────────
    def test_stack_push_valid(self):
        msg = make_stack_push(self.stack_id, 10)
        response = dispatch(msg)
        self.assertTrue(response.startswith("OK|"), msg=response)

    def test_stack_pop_valid(self):
        dispatch(make_stack_push(self.stack_id, 55))
        response = dispatch(make_stack_pop(self.stack_id))
        self.assertIn("55", response)

    def test_stack_peek_valid(self):
        dispatch(make_stack_push(self.stack_id, 77))
        response = dispatch(make_stack_peek(self.stack_id))
        self.assertIn("77", response)
        # Peek no destruye el elemento
        response2 = dispatch(make_stack_peek(self.stack_id))
        self.assertIn("77", response2)

    # ─── Caso ID inexistente ───────────────────────────────────
    def test_stack_push_missing_id(self):
        msg = make_invalid_instance("STACK", "PUSH", 9999)
        response = dispatch(msg)
        self.assertTrue(response.startswith("ERROR|"))
        self.assertIn("INSTANCE_NOT_FOUND", response)

    def test_stack_pop_missing_id(self):
        response = dispatch(make_invalid_instance("STACK", "POP", 8888))
        self.assertTrue(response.startswith("ERROR|"))

    def test_stack_peek_missing_id(self):
        response = dispatch(make_invalid_instance("STACK", "PEEK", 7777))
        self.assertTrue(response.startswith("ERROR|"))

    # ─── Caso malformado ──────────────────────────────────────
    def test_stack_pop_empty_returns_error(self):
        response = dispatch(make_stack_pop(self.stack_id))
        self.assertTrue(response.startswith("ERROR|"))
        self.assertIn("STACK_EMPTY", response)

    def test_stack_with_insert_operation(self):
        msg = make_malformed("STACK", "INSERT", self.stack_id)
        response = dispatch(msg)
        self.assertTrue(response.startswith("ERROR|"))

    def test_stack_with_search_operation(self):
        msg = make_malformed("STACK", "SEARCH", self.stack_id)
        response = dispatch(msg)
        self.assertTrue(response.startswith("ERROR|"))


class TestDispatcherTreeInterface(unittest.TestCase):
    """Interfaz Dispatcher↔Tree."""

    def setUp(self):
        _reset_server()
        code, self.tree_id = server_create("TREE")
        self.assertEqual(code, SERVER_OK)

    # ─── Caso válido ───────────────────────────────────────────
    def test_tree_insert_valid(self):
        response = dispatch(make_tree_insert(self.tree_id, 50))
        self.assertTrue(response.startswith("OK|"), msg=response)

    def test_tree_search_found(self):
        dispatch(make_tree_insert(self.tree_id, 30))
        response = dispatch(make_tree_search(self.tree_id, 30))
        self.assertIn("FOUND", response)

    def test_tree_inorder_sorted(self):
        for v in [20, 10, 30]:
            dispatch(make_tree_insert(self.tree_id, v))
        response = dispatch(make_tree_inorder(self.tree_id))
        self.assertIn("10,20,30", response)

    # ─── Caso ID inexistente ───────────────────────────────────
    def test_tree_insert_missing_id(self):
        response = dispatch(make_invalid_instance("TREE", "INSERT", 9999))
        self.assertTrue(response.startswith("ERROR|"))
        self.assertIn("INSTANCE_NOT_FOUND", response)

    def test_tree_search_missing_id(self):
        response = dispatch(make_invalid_instance("TREE", "SEARCH", 8888))
        self.assertTrue(response.startswith("ERROR|"))

    def test_tree_inorder_missing_id(self):
        response = dispatch(make_invalid_instance("TREE", "INORDER", 7777))
        self.assertTrue(response.startswith("ERROR|"))

    # ─── Caso malformado ──────────────────────────────────────
    def test_tree_search_not_found(self):
        response = dispatch(make_tree_search(self.tree_id, 999))
        self.assertTrue(response.startswith("ERROR|"))
        self.assertIn("NOT_FOUND", response)

    def test_tree_delete_not_found(self):
        response = dispatch(make_tree_delete(self.tree_id, 999))
        self.assertTrue(response.startswith("ERROR|"))

    def test_tree_inorder_empty_tree(self):
        response = dispatch(make_tree_inorder(self.tree_id))
        self.assertTrue(response.startswith("ERROR|"))
        self.assertIn("TREE_EMPTY", response)


if __name__ == "__main__":
    unittest.main()
