import unittest
import sys
import os

# Ajustar PYTHONPATH para permitir la importación desde src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from objects.list_obj import (
    List,
    list_create, list_destroy, list_insert, list_remove,
    list_clear, list_get, list_size, list_contains,
    LIST_OK, LIST_NULL_PTR, LIST_OUT_OF_BOUNDS
)

class TestListCreate(unittest.TestCase):
    def test_list_create_returns_instance(self):
        """[Clase Válida] Verifica que retorne una instancia de List."""
        lst = list_create()
        self.assertIsInstance(lst, List)

    def test_list_create_initial_size(self):
        """[Límite Inferior] Verifica que el tamaño inicial sea 0."""
        lst = list_create()
        self.assertEqual(lst.size, 0)

    def test_list_create_initial_head_tail(self):
        """[Estado Interno] Verifica que cabeza y cola estén limpios."""
        lst = list_create()
        self.assertIsNone(lst._head)
        self.assertIsNone(lst._tail)

    def test_list_create_lock_exists(self):
        """[Concurrencia] Verifica la existencia del cerrojo (Lock)."""
        lst = list_create()
        self.assertTrue(hasattr(lst, '_lock'))

    def test_list_create_multiple_instances(self):
        """[Clase Válida] Verifica que instancias distintas sean independientes."""
        lst1 = list_create()
        lst2 = list_create()
        self.assertIsNot(lst1, lst2)

class TestListDestroy(unittest.TestCase):
    def test_list_destroy_valid(self):
        """[Clase Válida] Destruir una lista con elementos."""
        lst = list_create()
        list_insert(lst, 10)
        ret = list_destroy(lst)
        self.assertEqual(ret, LIST_OK)

    def test_list_destroy_empty(self):
        """[Límite Inferior] Destruir una lista vacía."""
        lst = list_create()
        ret = list_destroy(lst)
        self.assertEqual(ret, LIST_OK)

    def test_list_destroy_none(self):
        """[Clase Inválida] Pasar None como parámetro."""
        ret = list_destroy(None)
        self.assertEqual(ret, LIST_NULL_PTR)

    def test_list_destroy_clears_nodes(self):
        """[Estado Interno] Verifica que los nodos queden en None tras destrucción."""
        lst = list_create()
        list_insert(lst, 10)
        list_destroy(lst)
        self.assertIsNone(lst._head)
        self.assertIsNone(lst._tail)
        self.assertEqual(lst.size, 0)

    def test_list_destroy_idempotent(self):
        """[Caso Especial] Destruir repetidas veces la misma lista."""
        lst = list_create()
        list_destroy(lst)
        ret = list_destroy(lst)
        self.assertEqual(ret, LIST_OK)

class TestListInsert(unittest.TestCase):
    def test_list_insert_valid(self):
        """[Clase Válida] Inserción simple de un elemento."""
        lst = list_create()
        ret = list_insert(lst, 42)
        self.assertEqual(ret, LIST_OK)
        self.assertEqual(lst.size, 1)

    def test_list_insert_none(self):
        """[Clase Inválida] Inserción en parámetro None."""
        ret = list_insert(None, 42)
        self.assertEqual(ret, LIST_NULL_PTR)

    def test_list_insert_multiple(self):
        """[Clase Válida] Inserción de múltiples elementos en orden."""
        lst = list_create()
        list_insert(lst, 1)
        list_insert(lst, 2)
        list_insert(lst, 3)
        self.assertEqual(lst.size, 3)
        self.assertEqual(lst._tail.data, 3)

    def test_list_insert_negative(self):
        """[Caso Especial] Inserción de un número negativo."""
        lst = list_create()
        list_insert(lst, -99)
        self.assertEqual(lst._head.data, -99)

    def test_list_insert_large_value(self):
        """[Límite Superior] Inserción de un valor extremo simulado (INT_MAX)."""
        lst = list_create()
        val = 2147483647
        list_insert(lst, val)
        self.assertEqual(lst._head.data, val)

class TestListRemove(unittest.TestCase):
    def setUp(self):
        self.lst = list_create()
        list_insert(self.lst, 10)
        list_insert(self.lst, 20)
        list_insert(self.lst, 30)

    def test_list_remove_middle(self):
        """[Clase Válida] Remover el elemento central."""
        ret = list_remove(self.lst, 1)
        self.assertEqual(ret, LIST_OK)
        self.assertEqual(self.lst.size, 2)

    def test_list_remove_none(self):
        """[Clase Inválida] Remover usando parámetro None."""
        ret = list_remove(None, 0)
        self.assertEqual(ret, LIST_NULL_PTR)

    def test_list_remove_out_of_bounds_negative(self):
        """[Límite Inferior] Remover índice negativo."""
        ret = list_remove(self.lst, -1)
        self.assertEqual(ret, LIST_OUT_OF_BOUNDS)

    def test_list_remove_out_of_bounds_upper(self):
        """[Límite Superior] Remover índice igual o mayor al tamaño."""
        ret = list_remove(self.lst, 3)
        self.assertEqual(ret, LIST_OUT_OF_BOUNDS)

    def test_list_remove_head_and_tail(self):
        """[Caso Especial] Remover inicio y luego el final."""
        list_remove(self.lst, 0)
        self.assertEqual(self.lst._head.data, 20)
        list_remove(self.lst, 1)
        self.assertEqual(self.lst._tail.data, 20)
        self.assertEqual(self.lst.size, 1)

class TestListClear(unittest.TestCase):
    def test_list_clear_populated(self):
        """[Clase Válida] Limpiar lista poblada."""
        lst = list_create()
        list_insert(lst, 1)
        list_clear(lst)
        self.assertEqual(lst.size, 0)

    def test_list_clear_empty(self):
        """[Límite Inferior] Limpiar lista que ya estaba vacía."""
        lst = list_create()
        ret = list_clear(lst)
        self.assertEqual(ret, LIST_OK)

    def test_list_clear_none(self):
        """[Clase Inválida] Limpiar con parámetro None."""
        ret = list_clear(None)
        self.assertEqual(ret, LIST_NULL_PTR)

    def test_list_clear_node_state(self):
        """[Estado Interno] Verificación de punteros en NULL tras limpieza."""
        lst = list_create()
        list_insert(lst, 1)
        list_clear(lst)
        self.assertIsNone(lst._head)
        self.assertIsNone(lst._tail)

    def test_list_clear_insert_after(self):
        """[Caso Especial] Inserción en lista recién limpiada."""
        lst = list_create()
        list_insert(lst, 1)
        list_clear(lst)
        list_insert(lst, 2)
        self.assertEqual(lst.size, 1)
        self.assertEqual(lst._head.data, 2)

class TestListGet(unittest.TestCase):
    def setUp(self):
        self.lst = list_create()
        list_insert(self.lst, 100)
        list_insert(self.lst, 200)

    def test_list_get_valid(self):
        """[Clase Válida] Obtener un valor existente."""
        code, val = list_get(self.lst, 1)
        self.assertEqual(code, LIST_OK)
        self.assertEqual(val, 200)

    def test_list_get_none(self):
        """[Clase Inválida] Obtener usando None."""
        code, val = list_get(None, 0)
        self.assertEqual(code, LIST_NULL_PTR)

    def test_list_get_negative_pos(self):
        """[Límite Inferior] Obtener con índice negativo."""
        code, val = list_get(self.lst, -5)
        self.assertEqual(code, LIST_OUT_OF_BOUNDS)

    def test_list_get_out_of_bounds(self):
        """[Límite Superior] Obtener con índice fuera de rango."""
        code, val = list_get(self.lst, 2)
        self.assertEqual(code, LIST_OUT_OF_BOUNDS)

    def test_list_get_empty_list(self):
        """[Caso Especial] Obtener desde una lista vacía."""
        empty_lst = list_create()
        code, val = list_get(empty_lst, 0)
        self.assertEqual(code, LIST_OUT_OF_BOUNDS)

class TestListSize(unittest.TestCase):
    def test_list_size_empty(self):
        """[Límite Inferior] Tamaño de lista vacía."""
        lst = list_create()
        self.assertEqual(list_size(lst), 0)

    def test_list_size_populated(self):
        """[Clase Válida] Tamaño tras inserciones."""
        lst = list_create()
        list_insert(lst, 1)
        self.assertEqual(list_size(lst), 1)

    def test_list_size_none(self):
        """[Clase Inválida] Tamaño con parámetro None."""
        self.assertEqual(list_size(None), LIST_NULL_PTR)

    def test_list_size_after_insert(self):
        """[Estado Transicional] Incremento progresivo de tamaño."""
        lst = list_create()
        list_insert(lst, 1)
        list_insert(lst, 2)
        self.assertEqual(list_size(lst), 2)

    def test_list_size_after_remove(self):
        """[Estado Transicional] Decremento progresivo de tamaño."""
        lst = list_create()
        list_insert(lst, 1)
        list_remove(lst, 0)
        self.assertEqual(list_size(lst), 0)

class TestListContains(unittest.TestCase):
    def setUp(self):
        self.lst = list_create()
        list_insert(self.lst, 55)
        list_insert(self.lst, 66)

    def test_list_contains_true(self):
        """[Clase Válida] Buscar elemento existente."""
        self.assertEqual(list_contains(self.lst, 66), 1)

    def test_list_contains_false(self):
        """[Clase Válida] Buscar elemento no existente."""
        self.assertEqual(list_contains(self.lst, 99), 0)

    def test_list_contains_none(self):
        """[Clase Inválida] Buscar en lista None."""
        self.assertEqual(list_contains(None, 55), LIST_NULL_PTR)

    def test_list_contains_empty(self):
        """[Límite Inferior] Buscar en lista vacía."""
        empty_lst = list_create()
        self.assertEqual(list_contains(empty_lst, 55), 0)

    def test_list_contains_duplicates(self):
        """[Caso Especial] Buscar cuando el valor está duplicado."""
        list_insert(self.lst, 55)
        self.assertEqual(list_contains(self.lst, 55), 1)

if __name__ == '__main__':
    unittest.main()
