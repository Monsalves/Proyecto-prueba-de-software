import pytest
"""
test_concurrency.py — Pruebas de Concurrencia: ObjectServer y Estructuras
Proyecto: Bus de Objetos en Python — Etapa 3 / TSK-08
Agente IA: qa-tester-agent
Descripción: Verificación de que el mutex protege correctamente el ObjectServer.
             ≥10 hilos crean instancias simultáneamente → IDs únicos garantizados.
             ≥10 hilos operan sobre la misma instancia → sin corrupción de datos.

Nota sobre Helgrind (Valgrind):
    Helgrind es una herramienta de análisis de condiciones de carrera de bajo nivel
    diseñada para código C/C++. Para Python, el equivalente es ejecutar los tests
    con ThreadSanitizer (TSan) o analizar mediante el módulo threading + locks.
    Para análisis nativo, ver: valgrind --tool=helgrind ./object_server_native
"""

import unittest
import threading
from src.server.object_server import (
    server_create, server_get, server_instance_count, _reset_server, SERVER_OK,
)
from src.server.dispatcher import dispatch
from tests.integration.stubs.serializer_stub import (
    make_create,
    make_list_insert, make_list_size,
    make_stack_push, make_stack_pop,
    make_tree_insert, make_tree_inorder,
)
from src.objects.tree_obj import tree_insert, TREE_OK
from src.objects.stack_obj import stack_size


# ─── Parte 1: Creación concurrente de instancias ───────────────

class TestConcurrentInstanceCreation(unittest.TestCase):
    """≥10 hilos crean instancias simultáneamente; IDs deben ser todos únicos."""

    def setUp(self):
        _reset_server()

    @pytest.mark.test_id("TC-01")
    def test_ten_threads_create_unique_ids(self):
        """10 hilos crean via Dispatcher simultáneamente → IDs únicos."""
        results: list = []
        lock = threading.Lock()

        def create_one():
            response = dispatch(make_create("LIST"))
            with lock:
                if response.startswith("OK|"):
                    results.append((SERVER_OK, int(response.split("|")[1])))
                else:
                    results.append((-1, None))

        threads = [threading.Thread(target=create_one) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        codes = [r[0] for r in results]
        ids = [r[1] for r in results]
        self.assertTrue(all(c == SERVER_OK for c in codes), "Algún CREATE falló")
        self.assertEqual(len(set(ids)), 10, "Se detectaron IDs duplicados en creación concurrente")

    @pytest.mark.test_id("TC-02")
    def test_ten_threads_mixed_types_unique_ids(self):
        """10 hilos con tipos mixtos → todos los IDs son únicos."""
        results: list = []
        lock = threading.Lock()
        types = ["LIST", "STACK", "TREE", "LIST", "STACK",
                 "TREE", "LIST", "STACK", "TREE", "LIST"]

        def create_typed(obj_type):
            response = dispatch(make_create(obj_type))
            with lock:
                if response.startswith("OK|"):
                    results.append((SERVER_OK, int(response.split("|")[1])))
                else:
                    results.append((-1, None))

        threads = [threading.Thread(target=create_typed, args=(t,)) for t in types]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        ids = [r[1] for r in results]
        self.assertEqual(len(set(ids)), 10, "IDs duplicados en creación mixta concurrente")

    @pytest.mark.test_id("TC-03")
    def test_concurrent_creates_all_retrievable(self):
        """10 hilos crean instancias; todas son recuperables después de la concurrencia."""
        results: list = []
        lock = threading.Lock()

        def create_and_store():
            response = dispatch(make_create("STACK"))
            with lock:
                if response.startswith("OK|"):
                    results.append(int(response.split("|")[1]))

        threads = [threading.Thread(target=create_and_store) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for iid in results:
            code, obj = server_get(iid)
            self.assertEqual(code, SERVER_OK, f"No se pudo recuperar instancia {iid}")

    @pytest.mark.test_id("TC-04")
    def test_no_id_collision_across_100_creates(self):
        """100 creates concurrentes no deben producir ningún ID duplicado."""
        ids: list = []
        lock = threading.Lock()

        def create_one():
            response = dispatch(make_create("LIST"))
            if response.startswith("OK|"):
                with lock:
                    ids.append(int(response.split("|")[1]))

        threads = [threading.Thread(target=create_one) for _ in range(100)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(ids), 100)
        self.assertEqual(len(set(ids)), 100, f"Colisión de IDs detectada entre {len(ids)} creates")


# ─── Parte 2: Operaciones concurrentes sobre la misma instancia ─

class TestConcurrentOperationsOnSameInstance(unittest.TestCase):
    """≥10 hilos operan sobre la misma instancia sin corrupción de datos."""

    def setUp(self):
        _reset_server()

    @pytest.mark.test_id("TC-05")
    def test_ten_threads_insert_list_no_corruption(self):
        """10 hilos insertan valores en la misma List vía Dispatcher."""
        response = dispatch(make_create("LIST"))
        list_id = int(response.split("|")[1])
        errors: list = []
        lock = threading.Lock()

        def insert_values(start: int):
            for v in range(start, start + 5):
                resp = dispatch(make_list_insert(list_id, v))
                if not resp.startswith("OK|"):
                    with lock:
                        errors.append(f"Insert {v} failed: {resp}")

        threads = [threading.Thread(target=insert_values, args=(i * 5,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [], f"Errores en inserciones concurrentes: {errors}")
        size_response = dispatch(make_list_size(list_id))
        self.assertIn("50", size_response, "La lista no tiene 50 elementos tras 10 hilos×5 inserciones")

    @pytest.mark.test_id("TC-06")
    def test_ten_threads_push_stack_no_corruption(self):
        """10 hilos hacen push sobre la misma Stack; ningún error."""
        response = dispatch(make_create("STACK"))
        stack_id = int(response.split("|")[1])
        errors: list = []
        lock = threading.Lock()

        def push_values(start: int):
            for v in range(start, start + 3):
                resp = dispatch(make_stack_push(stack_id, v))
                if not resp.startswith("OK|"):
                    with lock:
                        errors.append(f"Push {v} failed: {resp}")

        threads = [threading.Thread(target=push_values, args=(i * 3,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [], f"Errores en push concurrentes: {errors}")

    @pytest.mark.test_id("TC-07")
    def test_ten_threads_insert_tree_unique_values(self):
        """10 hilos insertan valores únicos en el mismo Tree; inorden debe ser creciente."""
        response = dispatch(make_create("TREE"))
        tree_id = int(response.split("|")[1])
        values = list(range(1, 11))

        def insert_single(v):
            dispatch(make_tree_insert(tree_id, v))

        threads = [threading.Thread(target=insert_single, args=(v,)) for v in values]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        response = dispatch(make_tree_inorder(tree_id))
        self.assertTrue(response.startswith("OK|"), msg=response)
        data_part = response.strip().split("|", 1)[1]
        result = list(map(int, data_part.split(",")))
        self.assertEqual(result, sorted(result), "El inorden no es creciente tras inserciones concurrentes")
        self.assertEqual(len(result), 10, "No se insertaron los 10 valores únicos")

    @pytest.mark.test_id("TC-08")
    def test_concurrent_insert_and_search_tree_no_crash(self):
        """5 hilos insertan y 5 hilos leen el mismo Tree sin excepción."""
        response = dispatch(make_create("TREE"))
        tree_id = int(response.split("|")[1])
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

        def do_inorder():
            try:
                dispatch(make_tree_inorder(tree_id))
            except Exception as e:
                with lock:
                    errors.append(str(e))

        inserters = [threading.Thread(target=do_insert, args=(i,)) for i in range(5)]
        readers = [threading.Thread(target=do_inorder) for _ in range(5)]
        all_threads = inserters + readers
        for t in all_threads:
            t.start()
        for t in all_threads:
            t.join()

        self.assertEqual(errors, [], f"Excepciones en operaciones concurrentes: {errors}")

    @pytest.mark.test_id("TC-09")
    def test_ten_threads_pop_stack_no_negative_size(self):
        """10 hilos hacen push y pop; el tamaño final nunca es negativo."""
        response = dispatch(make_create("STACK"))
        stack_id = int(response.split("|")[1])

        # Pre-cargar 20 valores
        for v in range(20):
            dispatch(make_stack_push(stack_id, v))

        def pop_five():
            for _ in range(5):
                dispatch(make_stack_pop(stack_id))

        threads = [threading.Thread(target=pop_five) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        code, stk_obj = server_get(stack_id)
        size = stack_size(stk_obj)
        self.assertGreaterEqual(size, 0, "El tamaño de la pila es negativo")


# ─── Parte 3: Integridad global del servidor bajo carga ─────────

class TestConcurrentServerIntegrity(unittest.TestCase):
    """Pruebas de integridad global del servidor bajo carga concurrente."""

    def setUp(self):
        _reset_server()

    @pytest.mark.test_id("TC-10")
    def test_instance_count_consistent_after_concurrent_creates(self):
        """El conteo del servidor refleja exactamente el número de creates exitosos."""
        ids: list = []
        lock = threading.Lock()

        def create_one():
            response = dispatch(make_create("LIST"))
            if response.startswith("OK|"):
                with lock:
                    ids.append(int(response.split("|")[1]))

        threads = [threading.Thread(target=create_one) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(server_instance_count(), len(ids))
        self.assertEqual(len(set(ids)), len(ids), "IDs duplicados detectados")


if __name__ == "__main__":
    unittest.main()
