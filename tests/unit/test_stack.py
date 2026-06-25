import pytest
import unittest
import sys
import os

# Ajustar PYTHONPATH para permitir la importación desde src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from objects.stack_obj import (
    Stack,
    stack_create, stack_destroy, stack_push, stack_pop,
    stack_peek, stack_is_empty, stack_size,
    STACK_OK, STACK_NULL_PTR, STACK_EMPTY
)

class TestStackCreate(unittest.TestCase):
    @pytest.mark.regression
    @pytest.mark.test_id("TU-S-01")
    def test_stack_create_returns_instance(self):
        """[Clase Válida] Verifica el retorno de instancia Stack."""
        stk = stack_create()
        self.assertIsInstance(stk, Stack)

    @pytest.mark.test_id("TU-S-02")
    def test_stack_create_initial_size(self):
        """[Límite Inferior] Verifica el tamaño en 0."""
        stk = stack_create()
        self.assertEqual(stk.size, 0)

    @pytest.mark.test_id("TU-S-03")
    def test_stack_create_initial_top(self):
        """[Estado Interno] El tope inicial debe ser None."""
        stk = stack_create()
        self.assertIsNone(stk._top)

    @pytest.mark.test_id("TU-S-04")
    def test_stack_create_lock_exists(self):
        """[Concurrencia] Revisa la creación del cerrojo."""
        stk = stack_create()
        self.assertTrue(hasattr(stk, '_lock'))

    @pytest.mark.test_id("TU-S-05")
    def test_stack_create_independent(self):
        """[Clase Válida] Instancias independientes."""
        stk1 = stack_create()
        stk2 = stack_create()
        self.assertIsNot(stk1, stk2)

class TestStackDestroy(unittest.TestCase):
    @pytest.mark.test_id("TU-S-06")
    def test_stack_destroy_valid(self):
        """[Clase Válida] Destruir pila con datos."""
        stk = stack_create()
        stack_push(stk, 50)
        self.assertEqual(stack_destroy(stk), STACK_OK)

    @pytest.mark.test_id("TU-S-07")
    def test_stack_destroy_empty(self):
        """[Límite Inferior] Destruir pila vacía."""
        stk = stack_create()
        self.assertEqual(stack_destroy(stk), STACK_OK)

    @pytest.mark.test_id("TU-S-08")
    def test_stack_destroy_none(self):
        """[Clase Inválida] Parámetro None."""
        self.assertEqual(stack_destroy(None), STACK_NULL_PTR)

    @pytest.mark.test_id("TU-S-09")
    def test_stack_destroy_state(self):
        """[Estado Interno] Verifica nodos en None tras destruir."""
        stk = stack_create()
        stack_push(stk, 10)
        stack_destroy(stk)
        self.assertIsNone(stk._top)
        self.assertEqual(stk.size, 0)

    @pytest.mark.test_id("TU-S-10")
    def test_stack_destroy_idempotent(self):
        """[Caso Especial] Doble llamada."""
        stk = stack_create()
        stack_destroy(stk)
        self.assertEqual(stack_destroy(stk), STACK_OK)

class TestStackPush(unittest.TestCase):
    @pytest.mark.regression
    @pytest.mark.test_id("TU-S-11")
    def test_stack_push_valid(self):
        """[Clase Válida] Inserción normal."""
        stk = stack_create()
        self.assertEqual(stack_push(stk, 7), STACK_OK)
        self.assertEqual(stk.size, 1)

    @pytest.mark.test_id("TU-S-12")
    def test_stack_push_none(self):
        """[Clase Inválida] Push en None."""
        self.assertEqual(stack_push(None, 7), STACK_NULL_PTR)

    @pytest.mark.regression
    @pytest.mark.test_id("TU-S-13")
    def test_stack_push_lifo_order(self):
        """[Clase Válida] Múltiples ingresos para LIFO."""
        stk = stack_create()
        stack_push(stk, 1)
        stack_push(stk, 2)
        self.assertEqual(stk._top.data, 2)

    @pytest.mark.test_id("TU-S-14")
    def test_stack_push_negative(self):
        """[Caso Especial] Push de negativo."""
        stk = stack_create()
        stack_push(stk, -5)
        self.assertEqual(stk._top.data, -5)

    @pytest.mark.test_id("TU-S-15")
    def test_stack_push_boundary(self):
        """[Límite Superior] Número gigante."""
        stk = stack_create()
        stack_push(stk, 2147483647)
        self.assertEqual(stk._top.data, 2147483647)

class TestStackPop(unittest.TestCase):
    def setUp(self):
        self.stk = stack_create()
        stack_push(self.stk, 100)
        stack_push(self.stk, 200)

    @pytest.mark.regression
    @pytest.mark.test_id("TU-S-16")
    def test_stack_pop_valid(self):
        """[Clase Válida] Extraer último insertado."""
        code, val = stack_pop(self.stk)
        self.assertEqual(code, STACK_OK)
        self.assertEqual(val, 200)

    @pytest.mark.test_id("TU-S-17")
    def test_stack_pop_none(self):
        """[Clase Inválida] Pop desde None."""
        code, val = stack_pop(None)
        self.assertEqual(code, STACK_NULL_PTR)

    @pytest.mark.regression
    @pytest.mark.test_id("TU-S-18")
    def test_stack_pop_empty(self):
        """[Límite Inferior] Pop desde pila vacía."""
        empty_stk = stack_create()
        code, val = stack_pop(empty_stk)
        self.assertEqual(code, STACK_EMPTY)

    @pytest.mark.test_id("TU-S-19")
    def test_stack_pop_until_empty(self):
        """[Límite Inferior] Vaciar la pila completa con pop."""
        stack_pop(self.stk)
        stack_pop(self.stk)
        self.assertEqual(self.stk.size, 0)
        code, val = stack_pop(self.stk)
        self.assertEqual(code, STACK_EMPTY)

    @pytest.mark.test_id("TU-S-20")
    def test_stack_pop_state_logic(self):
        """[Estado Transicional] Push, Pop, Push repetitivo."""
        stack_pop(self.stk) # queda 100
        stack_push(self.stk, 300)
        code, val = stack_pop(self.stk)
        self.assertEqual(val, 300)

class TestStackPeek(unittest.TestCase):
    def setUp(self):
        self.stk = stack_create()
        stack_push(self.stk, 99)

    @pytest.mark.test_id("TU-S-21")
    def test_stack_peek_valid(self):
        """[Clase Válida] Revisar tope normal."""
        code, val = stack_peek(self.stk)
        self.assertEqual(code, STACK_OK)
        self.assertEqual(val, 99)

    @pytest.mark.test_id("TU-S-22")
    def test_stack_peek_none(self):
        """[Clase Inválida] Revisar None."""
        code, val = stack_peek(None)
        self.assertEqual(code, STACK_NULL_PTR)

    @pytest.mark.test_id("TU-S-23")
    def test_stack_peek_empty(self):
        """[Límite Inferior] Peek de vacía."""
        empty = stack_create()
        code, val = stack_peek(empty)
        self.assertEqual(code, STACK_EMPTY)

    @pytest.mark.test_id("TU-S-24")
    def test_stack_peek_idempotent(self):
        """[Estado Interno] Múltiples peeks no cambian tamaño."""
        stack_peek(self.stk)
        stack_peek(self.stk)
        self.assertEqual(self.stk.size, 1)

    @pytest.mark.test_id("TU-S-25")
    def test_stack_peek_after_pop(self):
        """[Estado Transicional] Reflejo del nuevo tope."""
        stack_push(self.stk, 88)
        stack_pop(self.stk)
        code, val = stack_peek(self.stk)
        self.assertEqual(val, 99)

class TestStackIsEmpty(unittest.TestCase):
    @pytest.mark.test_id("TU-S-26")
    def test_stack_is_empty_true(self):
        """[Límite Inferior] Recién creada es 1."""
        self.assertEqual(stack_is_empty(stack_create()), 1)

    @pytest.mark.test_id("TU-S-27")
    def test_stack_is_empty_false(self):
        """[Clase Válida] Poblada es 0."""
        stk = stack_create()
        stack_push(stk, 1)
        self.assertEqual(stack_is_empty(stk), 0)

    @pytest.mark.test_id("TU-S-28")
    def test_stack_is_empty_none(self):
        """[Clase Inválida] Parámetro None."""
        self.assertEqual(stack_is_empty(None), STACK_NULL_PTR)

    @pytest.mark.test_id("TU-S-29")
    def test_stack_is_empty_after_pop(self):
        """[Estado Transicional] Retorno a vacía."""
        stk = stack_create()
        stack_push(stk, 1)
        stack_pop(stk)
        self.assertEqual(stack_is_empty(stk), 1)

    @pytest.mark.test_id("TU-S-30")
    def test_stack_is_empty_clear(self):
        """[Estado Transicional] Validar tras limpiar."""
        stk = stack_create()
        stack_push(stk, 1)
        stack_destroy(stk)
        self.assertEqual(stack_is_empty(stk), 1)

class TestStackSize(unittest.TestCase):
    @pytest.mark.test_id("TU-S-31")
    def test_stack_size_empty(self):
        """[Límite Inferior] Vacía es 0."""
        self.assertEqual(stack_size(stack_create()), 0)

    @pytest.mark.test_id("TU-S-32")
    def test_stack_size_populated(self):
        """[Clase Válida] Varios items."""
        stk = stack_create()
        stack_push(stk, 1)
        stack_push(stk, 2)
        self.assertEqual(stack_size(stk), 2)

    @pytest.mark.test_id("TU-S-33")
    def test_stack_size_none(self):
        """[Clase Inválida] Parámetro None."""
        self.assertEqual(stack_size(None), STACK_NULL_PTR)

    @pytest.mark.test_id("TU-S-34")
    def test_stack_size_increase(self):
        """[Estado Transicional] Incremento con push."""
        stk = stack_create()
        stack_push(stk, 1)
        self.assertEqual(stack_size(stk), 1)

    @pytest.mark.test_id("TU-S-35")
    def test_stack_size_decrease(self):
        """[Estado Transicional] Decremento con pop."""
        stk = stack_create()
        stack_push(stk, 1)
        stack_pop(stk)
        self.assertEqual(stack_size(stk), 0)

if __name__ == '__main__':
    unittest.main()
