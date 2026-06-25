import pytest
"""
test_dispatcher_structures.py — Pruebas de Integración: Dispatcher↔Estructuras
Proyecto: Bus de Objetos en Python — Etapa 3
Descripción: Cubre la interfaz entre Dispatcher y las estructuras de datos
             (List, Stack, Tree): operación válida, operación sobre estructura
             vacía y operación con índice inválido.
"""

import unittest
from src.server.object_server import _reset_server
from src.server.dispatcher import dispatch
from tests.integration.stubs.serializer_stub import (
    make_create,
    make_list_insert, make_list_get, make_list_remove, make_list_size,
    make_list_contains, make_stack_push, make_stack_pop, make_stack_peek,
    make_tree_insert, make_tree_search, make_tree_delete, make_tree_inorder,
)


# ─── Helpers ───────────────────────────────────────────────────

def _dispatch_create(obj_type: str) -> int:
    resp = dispatch(make_create(obj_type))
    assert resp.startswith("OK|"), f"CREATE falló: {resp}"
    return int(resp.split("|")[1].strip())


# ─── LIST ──────────────────────────────────────────────────────

class TestDispatcherList(unittest.TestCase):
    """Interfaz Dispatcher↔List: válido, vacío, índice inválido."""

    def setUp(self):
        _reset_server()
        self.list_id = _dispatch_create("LIST")

    # ─── Operación válida ──────────────────────────────────────
    @pytest.mark.regression
    @pytest.mark.test_id("TI-DS-18")
    def test_insert_valid(self):
        response = dispatch(make_list_insert(self.list_id, 10))
        self.assertTrue(response.startswith("OK|"), msg=response)

    @pytest.mark.test_id("TI-DS-02")
    def test_get_valid_after_insert(self):
        dispatch(make_list_insert(self.list_id, 42))
        response = dispatch(make_list_get(self.list_id, 0))
        self.assertIn("42", response)

    @pytest.mark.test_id("TI-DS-03")
    def test_size_valid(self):
        dispatch(make_list_insert(self.list_id, 1))
        dispatch(make_list_insert(self.list_id, 2))
        dispatch(make_list_insert(self.list_id, 3))
        response = dispatch(make_list_size(self.list_id))
        self.assertIn("3", response)

    @pytest.mark.test_id("TI-DS-04")
    def test_contains_valid_found(self):
        dispatch(make_list_insert(self.list_id, 7))
        response = dispatch(make_list_contains(self.list_id, 7))
        self.assertTrue(response.startswith("OK|"))

    @pytest.mark.test_id("TI-DS-05")
    def test_remove_valid(self):
        dispatch(make_list_insert(self.list_id, 5))
        response = dispatch(make_list_remove(self.list_id, 0))
        self.assertTrue(response.startswith("OK|"))

    # ─── Operación sobre estructura vacía ─────────────────────
    @pytest.mark.test_id("TI-DS-06")
    def test_get_on_empty_list(self):
        """GET sobre lista vacía retorna ERROR de índice fuera de rango."""
        response = dispatch(make_list_get(self.list_id, 0))
        self.assertTrue(response.startswith("ERROR|"), msg=response)

    @pytest.mark.test_id("TI-DS-07")
    def test_remove_on_empty_list(self):
        """REMOVE sobre lista vacía retorna ERROR."""
        response = dispatch(make_list_remove(self.list_id, 0))
        self.assertTrue(response.startswith("ERROR|"))

    @pytest.mark.test_id("TI-DS-08")
    def test_size_on_empty_list_returns_zero(self):
        """SIZE sobre lista vacía retorna 0."""
        response = dispatch(make_list_size(self.list_id))
        self.assertIn("0", response)

    # ─── Índice inválido ──────────────────────────────────────
    @pytest.mark.test_id("TI-DS-09")
    def test_get_out_of_bounds(self):
        """GET en índice fuera de rango retorna ERROR|OUT_OF_BOUNDS."""
        dispatch(make_list_insert(self.list_id, 10))
        response = dispatch(make_list_get(self.list_id, 999))
        self.assertTrue(response.startswith("ERROR|"))
        self.assertIn("OUT_OF_BOUNDS", response)

    @pytest.mark.test_id("TI-DS-10")
    def test_remove_out_of_bounds(self):
        """REMOVE en índice fuera de rango retorna ERROR|OUT_OF_BOUNDS."""
        dispatch(make_list_insert(self.list_id, 10))
        response = dispatch(make_list_remove(self.list_id, 999))
        self.assertTrue(response.startswith("ERROR|"))
        self.assertIn("OUT_OF_BOUNDS", response)

    @pytest.mark.test_id("TI-DS-11")
    def test_get_negative_index(self):
        """GET con índice negativo retorna ERROR."""
        dispatch(make_list_insert(self.list_id, 10))
        response = dispatch(make_list_get(self.list_id, -1))
        self.assertTrue(response.startswith("ERROR|"))


# ─── STACK ─────────────────────────────────────────────────────

class TestDispatcherStack(unittest.TestCase):
    """Interfaz Dispatcher↔Stack: válido, vacío, borde."""

    def setUp(self):
        _reset_server()
        self.stack_id = _dispatch_create("STACK")

    # ─── Operación válida ──────────────────────────────────────
    @pytest.mark.test_id("TI-DS-12")
    def test_push_valid(self):
        response = dispatch(make_stack_push(self.stack_id, 100))
        self.assertTrue(response.startswith("OK|"))

    @pytest.mark.test_id("TI-DS-13")
    def test_pop_valid_after_push(self):
        dispatch(make_stack_push(self.stack_id, 55))
        response = dispatch(make_stack_pop(self.stack_id))
        self.assertIn("55", response)

    @pytest.mark.test_id("TI-DS-14")
    def test_peek_does_not_remove_element(self):
        dispatch(make_stack_push(self.stack_id, 77))
        response1 = dispatch(make_stack_peek(self.stack_id))
        response2 = dispatch(make_stack_peek(self.stack_id))
        self.assertIn("77", response1)
        self.assertIn("77", response2)

    @pytest.mark.test_id("TI-DS-15")
    def test_push_multiple_pop_lifo_order(self):
        """Verifica orden LIFO: último en entrar, primero en salir."""
        for v in [1, 2, 3]:
            dispatch(make_stack_push(self.stack_id, v))
        resp = dispatch(make_stack_pop(self.stack_id))
        self.assertIn("3", resp)

    # ─── Operación sobre estructura vacía ─────────────────────
    @pytest.mark.test_id("TI-DS-16")
    def test_pop_on_empty_stack(self):
        """POP sobre pila vacía retorna ERROR|STACK_EMPTY."""
        response = dispatch(make_stack_pop(self.stack_id))
        self.assertTrue(response.startswith("ERROR|"))
        self.assertIn("STACK_EMPTY", response)

    @pytest.mark.test_id("TI-DS-17")
    def test_peek_on_empty_stack(self):
        """PEEK sobre pila vacía retorna ERROR|STACK_EMPTY."""
        response = dispatch(make_stack_peek(self.stack_id))
        self.assertTrue(response.startswith("ERROR|"))
        self.assertIn("STACK_EMPTY", response)


# ─── TREE ──────────────────────────────────────────────────────

class TestDispatcherTree(unittest.TestCase):
    """Interfaz Dispatcher↔Tree: válido, vacío, elemento inexistente."""

    def setUp(self):
        _reset_server()
        self.tree_id = _dispatch_create("TREE")

    # ─── Operación válida ──────────────────────────────────────
    @pytest.mark.test_id("TI-DS-18")
    def test_insert_valid(self):
        response = dispatch(make_tree_insert(self.tree_id, 50))
        self.assertTrue(response.startswith("OK|"))

    @pytest.mark.test_id("TI-DS-19")
    def test_search_found(self):
        dispatch(make_tree_insert(self.tree_id, 30))
        response = dispatch(make_tree_search(self.tree_id, 30))
        self.assertIn("FOUND", response)

    @pytest.mark.test_id("TI-DS-20")
    def test_delete_valid(self):
        dispatch(make_tree_insert(self.tree_id, 20))
        response = dispatch(make_tree_delete(self.tree_id, 20))
        self.assertTrue(response.startswith("OK|"))

    @pytest.mark.test_id("TI-DS-21")
    def test_inorder_sorted(self):
        for v in [30, 10, 20]:
            dispatch(make_tree_insert(self.tree_id, v))
        response = dispatch(make_tree_inorder(self.tree_id))
        self.assertIn("10,20,30", response)

    # ─── Operación sobre estructura vacía ─────────────────────
    @pytest.mark.test_id("TI-DS-22")
    def test_inorder_on_empty_tree(self):
        """INORDER sobre árbol vacío retorna ERROR|TREE_EMPTY."""
        response = dispatch(make_tree_inorder(self.tree_id))
        self.assertTrue(response.startswith("ERROR|"))
        self.assertIn("TREE_EMPTY", response)

    @pytest.mark.test_id("TI-DS-23")
    def test_delete_on_empty_tree(self):
        """DELETE en árbol vacío retorna ERROR|NOT_FOUND."""
        response = dispatch(make_tree_delete(self.tree_id, 999))
        self.assertTrue(response.startswith("ERROR|"))
        self.assertIn("NOT_FOUND", response)

    # ─── Elemento inexistente / índice inválido ────────────────
    @pytest.mark.test_id("TI-DS-24")
    def test_search_not_found(self):
        """SEARCH de un valor no insertado retorna ERROR|NOT_FOUND."""
        dispatch(make_tree_insert(self.tree_id, 10))
        response = dispatch(make_tree_search(self.tree_id, 999))
        self.assertTrue(response.startswith("ERROR|"))
        self.assertIn("NOT_FOUND", response)

    @pytest.mark.test_id("TI-DS-25")
    def test_delete_not_found(self):
        """DELETE de un valor no insertado retorna ERROR|NOT_FOUND."""
        dispatch(make_tree_insert(self.tree_id, 10))
        response = dispatch(make_tree_delete(self.tree_id, 999))
        self.assertTrue(response.startswith("ERROR|"))
        self.assertIn("NOT_FOUND", response)

    @pytest.mark.test_id("TI-DS-26")
    def test_size_after_inserts_and_deletes(self):
        """SIZE refleja correctamente las mutaciones de inserción y borrado."""
        for v in [5, 10, 15]:
            dispatch(make_tree_insert(self.tree_id, v))
        dispatch(make_tree_delete(self.tree_id, 10))
        from tests.integration.stubs.serializer_stub import make_tree_size
        response = dispatch(make_tree_size(self.tree_id))
        self.assertIn("2", response)


if __name__ == "__main__":
    unittest.main()
