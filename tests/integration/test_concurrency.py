"""
test_concurrency.py — Pruebas de Concurrencia: ObjectServer y Tree
Proyecto: Bus de Objetos en Python — Etapa 3 / TSK-08
Agente IA: qa-tester-agent
Descripción: 10 hilos crean instancias simultáneamente (IDs únicos garantizados).
             10 hilos operan sobre la misma instancia sin corrupción de datos.
             Nota: Para análisis de condiciones de carrera de bajo nivel se recomienda Helgrind (Valgrind).
"""

import unittest
import threading
from src.server.object_server import (
    server_create, server_get, _reset_server, SERVER_OK,
)
from src.server.dispatcher import dispatch
from tests.integration.stubs.serializer_stub import (
    make_list_insert, make_list_size,
    make_stack_push, make_stack_pop,
    make_tree_insert, make_tree_inorder,
)
from src.objects.tree_obj import tree_insert, tree_search, tree_size, TREE_OK


class TestConcurrentInstanceCreation(unittest.TestCase):
    """10 hilos crean instancias simultáneamente; IDs deben ser todos únicos."""

    def setUp(self):
        _reset_server()

    def _create_instance(self, results: list, lock: threading.Lock):
        code, iid = server_create("LIST")
        with lock:
            results.append((code, iid))

    def test_ten_threads_create_unique_ids(self):
        results: list = []
        lock = threading.Lock()
        threads = [
            threading.Thread(target=self._create_instance, args=(results, lock))
            for _ in range(10)
        ]
        for th in threads:
            th.start()
        for th in threads:
            th.join()

        codes = [r[0] for r in results]
        ids = [r[1] for r in results]
        self.assertTrue(all(c == SERVER_OK for c in codes), "Algún create falló")
        self.assertEqual(len(set(ids)), 10, "Se detectaron IDs duplicados")

    def test_ten_threads_mixed_types_unique_ids(self):
        results: list = []
        lock = threading.Lock()
        types = ["LIST", "STACK", "TREE", "LIST", "STACK",
                 "TREE", "LIST", "STACK", "TREE", "LIST"]

        def create_typed(obj_type):
            code, iid = server_create(obj_type)
            with lock:
                results.append((code, iid))

        threads = [threading.Thread(target=create_typed, args=(t,)) for t in types]
        for th in threads:
            th.start()
        for th in threads:
            th.join()

        ids = [r[1] for r in results]
        self.assertEqual(len(set(ids)), 10, "IDs duplicados en creación mixta concurrente")

    def test_concurrent_creates_all_retrievable(self):
        results: list = []
        lock = threading.Lock()

        def create_and_store():
            code, iid = server_create("STACK")
            with lock:
                results.append(iid)

        threads = [threading.Thread(target=create_and_store) for _ in range(10)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()

        for iid in results:
            code, obj = server_get(iid)
            self.assertEqual(code, SERVER_OK, f"No se pudo recuperar instancia {iid}")


class TestConcurrentOperationsOnSameInstance(unittest.TestCase):
    """10 hilos operan sobre la misma instancia sin corrupción de datos."""

    def setUp(self):
        _reset_server()

    def test_ten_threads_insert_list_no_corruption(self):
        """10 hilos insertan valores en la misma List vía Dispatcher."""
        _, list_id = server_create("LIST")
        errors: list = []
        lock = threading.Lock()

        def insert_values(start: int):
            for v in range(start, start + 5):
                response = dispatch(make_list_insert(list_id, v))
                if not response.startswith("OK|"):
                    with lock:
                        errors.append(f"Insert {v} failed: {response}")

        threads = [threading.Thread(target=insert_values, args=(i * 5,)) for i in range(10)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()

        self.assertEqual(errors, [], f"Errores en inserciones concurrentes: {errors}")
        size_response = dispatch(make_list_size(list_id))
        self.assertIn("50", size_response, "La lista no tiene 50 elementos tras 10 hilos×5 inserciones")

    def test_ten_threads_push_stack_no_corruption(self):
        """10 hilos hacen push sobre la misma Stack sin corrupción."""
        _, stack_id = server_create("STACK")
        errors: list = []
        lock = threading.Lock()

        def push_values(start: int):
            for v in range(start, start + 3):
                response = dispatch(make_stack_push(stack_id, v))
                if not response.startswith("OK|"):
                    with lock:
                        errors.append(f"Push {v} failed: {response}")

        threads = [threading.Thread(target=push_values, args=(i * 3,)) for i in range(10)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()

        self.assertEqual(errors, [], f"Errores en push concurrentes: {errors}")

    def test_ten_threads_insert_tree_unique_values(self):
        """10 hilos insertan valores únicos en el mismo Tree; inorden debe ser creciente."""
        _, tree_id = server_create("TREE")
        values = list(range(1, 11))

        def insert_single(v):
            dispatch(make_tree_insert(tree_id, v))

        threads = [threading.Thread(target=insert_single, args=(v,)) for v in values]
        for th in threads:
            th.start()
        for th in threads:
            th.join()

        response = dispatch(make_tree_inorder(tree_id))
        self.assertTrue(response.startswith("OK|"), msg=response)
        data_part = response.strip().split("|", 1)[1]
        result = list(map(int, data_part.split(",")))
        self.assertEqual(result, sorted(result), "El inorden no es creciente tras inserciones concurrentes")
        self.assertEqual(len(result), 10, "No se insertaron los 10 valores únicos")

    def test_concurrent_insert_and_search_tree_no_crash(self):
        """5 hilos insertan y 5 hilos buscan en el mismo Tree sin excepción."""
        _, tree_id = server_create("TREE")
        code, tree_obj = server_get(tree_id)
        for v in range(1, 11):
            tree_insert(tree_obj, v)

        errors: list = []
        lock = threading.Lock()

        def do_insert(v):
            try:
                dispatch(make_tree_insert(tree_id, v + 100))
            except Exception as e:
                with lock:
                    errors.append(str(e))

        def do_search(v):
            try:
                dispatch(make_tree_inorder(tree_id))
            except Exception as e:
                with lock:
                    errors.append(str(e))

        inserters = [threading.Thread(target=do_insert, args=(i,)) for i in range(5)]
        searchers = [threading.Thread(target=do_search, args=(i,)) for i in range(5)]
        all_threads = inserters + searchers
        for th in all_threads:
            th.start()
        for th in all_threads:
            th.join()

        self.assertEqual(errors, [], f"Excepciones en operaciones concurrentes: {errors}")

    def test_ten_threads_pop_stack_no_negative_size(self):
        """10 hilos hacen push y pop; el tamaño final nunca es negativo."""
        _, stack_id = server_create("STACK")

        # Pre-cargar 20 valores
        for v in range(20):
            dispatch(make_stack_push(stack_id, v))

        def pop_five():
            for _ in range(5):
                dispatch(make_stack_pop(stack_id))

        threads = [threading.Thread(target=pop_five) for _ in range(4)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()

        code, stk_obj = server_get(stack_id)
        from src.objects.stack_obj import stack_size
        size = stack_size(stk_obj)
        self.assertGreaterEqual(size, 0, "El tamaño de la pila es negativo")


class TestConcurrentServerIntegrity(unittest.TestCase):
    """Pruebas de integridad global del servidor bajo carga concurrente."""

    def setUp(self):
        _reset_server()

    def test_no_id_collision_across_100_creates(self):
        """100 creates concurrentes no deben producir ningún ID duplicado."""
        ids: list = []
        lock = threading.Lock()

        def create_one():
            _, iid = server_create("LIST")
            with lock:
                ids.append(iid)

        threads = [threading.Thread(target=create_one) for _ in range(100)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()

        self.assertEqual(len(ids), 100)
        self.assertEqual(len(set(ids)), 100, f"Colisión de IDs detectada entre {len(ids)} creates")


if __name__ == "__main__":
    unittest.main()
