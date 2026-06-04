import pytest
"""
test_bus_system.py — Pruebas Funcionales End-to-End del Bus de Objetos
Proyecto: Bus de Objetos en Python — Etapa 4
Descripción: Verifica flujos completos a través de TCP real.
             El BusServer se levanta en un hilo y se usa _reset_server()
             para garantizar aislamiento entre clases de prueba.
             4 flujos obligatorios: List, Stack LIFO, Tree BST, Multi-instancia.
"""

import time
import unittest
import threading

from src.server.bus_server import BusServer
from src.client.bus_client import BusClient
from src.server.object_server import _reset_server


# ─── Fixture compartido ──────────────────────────────────────────

_server: BusServer | None = None
_server_port: int = 0


def setUpModule():
    """Levanta un BusServer en un hilo para toda la suite de tests."""
    global _server, _server_port
    _reset_server()
    _server = BusServer(host="127.0.0.1", port=0)  # port=0 → OS asigna libre
    _server.start()
    _server_port = _server.port
    time.sleep(0.1)  # Esperar a que el socket esté listo


def tearDownModule():
    """Detiene el BusServer al finalizar la suite."""
    global _server
    if _server is not None:
        _server.stop()
        _server = None


def _make_client() -> BusClient:
    """Crea y conecta un BusClient al servidor de prueba."""
    client = BusClient(host="127.0.0.1", port=_server_port)
    client.connect()
    return client


# ═══════════════════════════════════════════════════════════════════
# Flujo 1 — LIST completo
# ═══════════════════════════════════════════════════════════════════

class TestFlowList(unittest.TestCase):
    """
    Flujo E2E de List:
    create → insert×5 → get×5 → remove×2 → size == 3
    """

    def setUp(self):
        _reset_server()
        self.client = _make_client()

    def tearDown(self):
        self.client.close()

    @pytest.mark.test_id("TS-BS-01")
    def test_list_full_flow(self):
        # CREATE
        list_id = self.client.list_create()
        self.assertIsInstance(list_id, int)
        self.assertGreater(list_id, 0)

        # INSERT ×5 (valores: 10, 20, 30, 40, 50)
        values = [10, 20, 30, 40, 50]
        for v in values:
            self.client.list_insert(list_id, v)

        # GET ×5 — verificar cada posición
        for i, expected in enumerate(values):
            actual = self.client.list_get(list_id, i)
            self.assertEqual(actual, expected,
                             f"list_get({i}) expected {expected}, got {actual}")

        # REMOVE ×2 — posición 0 dos veces (elimina 10, luego 20)
        self.client.list_remove(list_id, 0)
        self.client.list_remove(list_id, 0)

        # SIZE == 3
        size = self.client.list_size(list_id)
        self.assertEqual(size, 3)

        # Verificar que los valores restantes son 30, 40, 50
        remaining = [self.client.list_get(list_id, i) for i in range(3)]
        self.assertEqual(remaining, [30, 40, 50])

    @pytest.mark.test_id("TS-BS-02")
    def test_list_contains(self):
        list_id = self.client.list_create()
        self.client.list_insert(list_id, 42)
        self.client.list_insert(list_id, 99)

        self.assertTrue(self.client.list_contains(list_id, 42))
        self.assertTrue(self.client.list_contains(list_id, 99))
        self.assertFalse(self.client.list_contains(list_id, 0))


# ═══════════════════════════════════════════════════════════════════
# Flujo 2 — STACK LIFO
# ═══════════════════════════════════════════════════════════════════

class TestFlowStack(unittest.TestCase):
    """
    Flujo E2E de Stack:
    create → push(10, 20, 30) → pop×3 → debe retornar 30, 20, 10 (LIFO)
    """

    def setUp(self):
        _reset_server()
        self.client = _make_client()

    def tearDown(self):
        self.client.close()

    @pytest.mark.test_id("TS-BS-03")
    def test_stack_lifo_order(self):
        stack_id = self.client.stack_create()
        self.assertGreater(stack_id, 0)

        # PUSH: 10, 20, 30
        self.client.stack_push(stack_id, 10)
        self.client.stack_push(stack_id, 20)
        self.client.stack_push(stack_id, 30)

        # POP ×3 — LIFO: 30, 20, 10
        self.assertEqual(self.client.stack_pop(stack_id), 30)
        self.assertEqual(self.client.stack_pop(stack_id), 20)
        self.assertEqual(self.client.stack_pop(stack_id), 10)

    @pytest.mark.test_id("TS-BS-04")
    def test_stack_peek_and_is_empty(self):
        stack_id = self.client.stack_create()

        self.assertTrue(self.client.stack_is_empty(stack_id))

        self.client.stack_push(stack_id, 55)
        self.assertFalse(self.client.stack_is_empty(stack_id))

        # PEEK no modifica la pila
        self.assertEqual(self.client.stack_peek(stack_id), 55)
        self.assertEqual(self.client.stack_peek(stack_id), 55)

        self.assertEqual(self.client.stack_pop(stack_id), 55)
        self.assertTrue(self.client.stack_is_empty(stack_id))


# ═══════════════════════════════════════════════════════════════════
# Flujo 3 — TREE BST
# ═══════════════════════════════════════════════════════════════════

class TestFlowTree(unittest.TestCase):
    """
    Flujo E2E de Tree:
    create → insert(5,3,8,1,4) → search(4)==True → search(9)==False
    → inorder == [1,3,4,5,8]
    """

    def setUp(self):
        _reset_server()
        self.client = _make_client()

    def tearDown(self):
        self.client.close()

    @pytest.mark.test_id("TS-BS-05")
    def test_tree_bst_flow(self):
        tree_id = self.client.tree_create()
        self.assertGreater(tree_id, 0)

        # INSERT: 5, 3, 8, 1, 4
        for v in [5, 3, 8, 1, 4]:
            self.client.tree_insert(tree_id, v)

        # SEARCH
        self.assertTrue(self.client.tree_search(tree_id, 4))
        self.assertFalse(self.client.tree_search(tree_id, 9))

        # INORDER → [1, 3, 4, 5, 8]
        inorder = self.client.tree_inorder(tree_id)
        self.assertEqual(inorder, [1, 3, 4, 5, 8])

    @pytest.mark.test_id("TS-BS-06")
    def test_tree_delete(self):
        tree_id = self.client.tree_create()
        for v in [5, 3, 8]:
            self.client.tree_insert(tree_id, v)

        self.client.tree_delete(tree_id, 3)
        self.assertFalse(self.client.tree_search(tree_id, 3))
        self.assertTrue(self.client.tree_search(tree_id, 5))

        inorder = self.client.tree_inorder(tree_id)
        self.assertEqual(inorder, [5, 8])


# ═══════════════════════════════════════════════════════════════════
# Flujo 4 — MULTI-INSTANCIA
# ═══════════════════════════════════════════════════════════════════

class TestFlowMultiInstance(unittest.TestCase):
    """
    Flujo E2E Multi-instancia:
    Crear List1, List2, Stack1. Insertar datos distintos.
    Verificar aislamiento total entre instancias.
    """

    def setUp(self):
        _reset_server()
        self.client = _make_client()

    def tearDown(self):
        self.client.close()

    @pytest.mark.test_id("TS-BS-07")
    def test_multi_instance_isolation(self):
        # Crear instancias
        list1 = self.client.list_create()
        list2 = self.client.list_create()
        stack1 = self.client.stack_create()

        # Verificar IDs distintos
        self.assertNotEqual(list1, list2)
        self.assertNotEqual(list1, stack1)
        self.assertNotEqual(list2, stack1)

        # Insertar datos distintos
        self.client.list_insert(list1, 10)
        self.client.list_insert(list1, 11)

        self.client.list_insert(list2, 20)
        self.client.list_insert(list2, 21)

        self.client.stack_push(stack1, 100)
        self.client.stack_push(stack1, 200)

        # Verificar aislamiento LIST1
        self.assertEqual(self.client.list_get(list1, 0), 10)
        self.assertEqual(self.client.list_get(list1, 1), 11)
        self.assertEqual(self.client.list_size(list1), 2)

        # Verificar aislamiento LIST2
        self.assertEqual(self.client.list_get(list2, 0), 20)
        self.assertEqual(self.client.list_get(list2, 1), 21)
        self.assertEqual(self.client.list_size(list2), 2)

        # Verificar aislamiento STACK1
        self.assertEqual(self.client.stack_pop(stack1), 200)
        self.assertEqual(self.client.stack_pop(stack1), 100)

    @pytest.mark.test_id("TS-BS-08")
    def test_multi_client_concurrent(self):
        """Verificar que dos clientes pueden operar simultáneamente."""
        client2 = _make_client()
        try:
            list1 = self.client.list_create()
            list2 = client2.list_create()

            self.client.list_insert(list1, 111)
            client2.list_insert(list2, 222)

            self.assertEqual(self.client.list_get(list1, 0), 111)
            self.assertEqual(client2.list_get(list2, 0), 222)
        finally:
            client2.close()


if __name__ == "__main__":
    unittest.main()
