"""
test_tree.py — Pruebas Unitarias para tree_obj.py
Proyecto: Bus de Objetos en Python — Etapa 3 / TSK-05
Agente IA: qa-tester-agent
Descripción: Mínimo 5 casos por función cubierta: insert, search, delete,
             inorder, size, árbol vacío y parámetros None.
"""

import unittest
from src.objects.tree_obj import (
    Tree,
    tree_create, tree_destroy,
    tree_insert, tree_search, tree_delete,
    tree_inorder, tree_size,
    TREE_OK, TREE_NULL_PTR, TREE_NOT_FOUND, TREE_EMPTY,
)


class TestTreeCreate(unittest.TestCase):
    """Pruebas de creación y destrucción."""

    def test_create_returns_tree_instance(self):
        t = tree_create()
        self.assertIsInstance(t, Tree)

    def test_new_tree_size_is_zero(self):
        t = tree_create()
        self.assertEqual(tree_size(t), 0)

    def test_destroy_ok(self):
        t = tree_create()
        tree_insert(t, 10)
        result = tree_destroy(t)
        self.assertEqual(result, TREE_OK)

    def test_destroy_clears_size(self):
        t = tree_create()
        tree_insert(t, 5)
        tree_destroy(t)
        self.assertEqual(tree_size(t), 0)

    def test_destroy_none_returns_null_ptr(self):
        result = tree_destroy(None)
        self.assertEqual(result, TREE_NULL_PTR)


class TestTreeInsert(unittest.TestCase):
    """Pruebas de inserción."""

    def setUp(self):
        self.t = tree_create()

    def test_insert_single_element(self):
        result = tree_insert(self.t, 10)
        self.assertEqual(result, TREE_OK)

    def test_insert_increments_size(self):
        tree_insert(self.t, 5)
        self.assertEqual(tree_size(self.t), 1)

    def test_insert_multiple_elements(self):
        for v in [10, 5, 15, 3, 7]:
            tree_insert(self.t, v)
        self.assertEqual(tree_size(self.t), 5)

    def test_insert_duplicate_does_not_increase_size(self):
        tree_insert(self.t, 10)
        tree_insert(self.t, 10)
        self.assertEqual(tree_size(self.t), 1)

    def test_insert_none_tree_returns_null_ptr(self):
        result = tree_insert(None, 10)
        self.assertEqual(result, TREE_NULL_PTR)

    def test_insert_negative_value(self):
        result = tree_insert(self.t, -5)
        self.assertEqual(result, TREE_OK)
        self.assertEqual(tree_size(self.t), 1)

    def test_insert_zero(self):
        result = tree_insert(self.t, 0)
        self.assertEqual(result, TREE_OK)


class TestTreeSearch(unittest.TestCase):
    """Pruebas de búsqueda."""

    def setUp(self):
        self.t = tree_create()
        for v in [10, 5, 15, 3, 7, 12, 20]:
            tree_insert(self.t, v)

    def test_search_existing_root(self):
        self.assertEqual(tree_search(self.t, 10), TREE_OK)

    def test_search_existing_left_leaf(self):
        self.assertEqual(tree_search(self.t, 3), TREE_OK)

    def test_search_existing_right_subtree(self):
        self.assertEqual(tree_search(self.t, 20), TREE_OK)

    def test_search_nonexistent_value(self):
        self.assertEqual(tree_search(self.t, 99), TREE_NOT_FOUND)

    def test_search_empty_tree(self):
        empty = tree_create()
        self.assertEqual(tree_search(empty, 5), TREE_NOT_FOUND)

    def test_search_none_tree(self):
        self.assertEqual(tree_search(None, 5), TREE_NULL_PTR)

    def test_search_after_delete(self):
        tree_delete(self.t, 7)
        self.assertEqual(tree_search(self.t, 7), TREE_NOT_FOUND)


class TestTreeDeleteNoChildren(unittest.TestCase):
    """Pruebas de eliminación — nodo hoja (0 hijos)."""

    def setUp(self):
        self.t = tree_create()
        for v in [10, 5, 15]:
            tree_insert(self.t, v)

    def test_delete_leaf_ok(self):
        self.assertEqual(tree_delete(self.t, 5), TREE_OK)

    def test_delete_leaf_reduces_size(self):
        tree_delete(self.t, 15)
        self.assertEqual(tree_size(self.t), 2)

    def test_delete_leaf_no_longer_found(self):
        tree_delete(self.t, 5)
        self.assertEqual(tree_search(self.t, 5), TREE_NOT_FOUND)

    def test_delete_nonexistent_returns_not_found(self):
        self.assertEqual(tree_delete(self.t, 99), TREE_NOT_FOUND)

    def test_delete_from_empty_tree(self):
        empty = tree_create()
        self.assertEqual(tree_delete(empty, 10), TREE_NOT_FOUND)

    def test_delete_none_tree(self):
        self.assertEqual(tree_delete(None, 10), TREE_NULL_PTR)


class TestTreeDeleteOneChild(unittest.TestCase):
    """Pruebas de eliminación — nodo con 1 hijo."""

    def setUp(self):
        self.t = tree_create()
        # Árbol: 10 → 5 (izq) → 3 (izq de 5, sin hermano)
        for v in [10, 5, 3]:
            tree_insert(self.t, v)

    def test_delete_node_with_left_child(self):
        result = tree_delete(self.t, 5)
        self.assertEqual(result, TREE_OK)

    def test_child_still_accessible_after_parent_deletion(self):
        tree_delete(self.t, 5)
        self.assertEqual(tree_search(self.t, 3), TREE_OK)

    def test_size_decreases_by_one(self):
        tree_delete(self.t, 5)
        self.assertEqual(tree_size(self.t), 2)

    def test_deleted_node_not_found(self):
        tree_delete(self.t, 5)
        self.assertEqual(tree_search(self.t, 5), TREE_NOT_FOUND)

    def test_inorder_correct_after_deletion(self):
        tree_delete(self.t, 5)
        _, result = tree_inorder(self.t)
        self.assertEqual(result, [3, 10])


class TestTreeDeleteTwoChildren(unittest.TestCase):
    """Pruebas de eliminación — nodo con 2 hijos (sucesor inorden)."""

    def setUp(self):
        self.t = tree_create()
        for v in [10, 5, 15, 3, 7, 12, 20]:
            tree_insert(self.t, v)

    def test_delete_root_with_two_children(self):
        result = tree_delete(self.t, 10)
        self.assertEqual(result, TREE_OK)

    def test_inorder_still_sorted_after_root_deletion(self):
        tree_delete(self.t, 10)
        _, result = tree_inorder(self.t)
        self.assertEqual(result, sorted(result))

    def test_deleted_root_not_found(self):
        tree_delete(self.t, 10)
        self.assertEqual(tree_search(self.t, 10), TREE_NOT_FOUND)

    def test_size_correct_after_internal_node_deletion(self):
        tree_delete(self.t, 5)
        self.assertEqual(tree_size(self.t), 6)

    def test_internal_subtree_intact_after_deletion(self):
        tree_delete(self.t, 15)
        self.assertEqual(tree_search(self.t, 12), TREE_OK)
        self.assertEqual(tree_search(self.t, 20), TREE_OK)


class TestTreeInorder(unittest.TestCase):
    """Pruebas de recorrido inorden."""

    def setUp(self):
        self.t = tree_create()

    def test_inorder_empty_tree(self):
        code, result = tree_inorder(self.t)
        self.assertEqual(code, TREE_EMPTY)
        self.assertEqual(result, [])

    def test_inorder_none_tree(self):
        code, result = tree_inorder(None)
        self.assertEqual(code, TREE_NULL_PTR)
        self.assertEqual(result, [])

    def test_inorder_single_element(self):
        tree_insert(self.t, 42)
        code, result = tree_inorder(self.t)
        self.assertEqual(code, TREE_OK)
        self.assertEqual(result, [42])

    def test_inorder_sorted_output(self):
        for v in [10, 5, 15, 3, 7, 12, 20]:
            tree_insert(self.t, v)
        _, result = tree_inorder(self.t)
        self.assertEqual(result, [3, 5, 7, 10, 12, 15, 20])

    def test_inorder_after_deletion(self):
        for v in [10, 5, 15]:
            tree_insert(self.t, v)
        tree_delete(self.t, 5)
        _, result = tree_inorder(self.t)
        self.assertEqual(result, [10, 15])

    def test_inorder_with_negatives(self):
        for v in [-5, 0, 5]:
            tree_insert(self.t, v)
        _, result = tree_inorder(self.t)
        self.assertEqual(result, [-5, 0, 5])


class TestTreeSize(unittest.TestCase):
    """Pruebas de tamaño."""

    def test_size_empty(self):
        t = tree_create()
        self.assertEqual(tree_size(t), 0)

    def test_size_after_inserts(self):
        t = tree_create()
        for v in [1, 2, 3, 4, 5]:
            tree_insert(t, v)
        self.assertEqual(tree_size(t), 5)

    def test_size_after_delete(self):
        t = tree_create()
        tree_insert(t, 10)
        tree_insert(t, 20)
        tree_delete(t, 10)
        self.assertEqual(tree_size(t), 1)

    def test_size_none_tree(self):
        self.assertEqual(tree_size(None), TREE_NULL_PTR)

    def test_size_after_destroy(self):
        t = tree_create()
        tree_insert(t, 7)
        tree_destroy(t)
        self.assertEqual(tree_size(t), 0)


if __name__ == "__main__":
    unittest.main()
