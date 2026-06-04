"""
tree_obj.py — Implementación de Árbol Binario de Búsqueda (BST) Thread-Safe
Proyecto: Bus de Objetos en Python — Etapa 3
Descripción: BST con gestión manual de nodos.
             Todos los parámetros inválidos retornan códigos de error; NUNCA hacen crash.
             Thread-safe mediante threading.Lock por instancia.
             Delete usa sucesor inorden para nodos con 2 hijos.
"""

import threading

# ─── Códigos de retorno ────────────────────────────────────────
TREE_OK        =  0
TREE_NULL_PTR  = -1   # Parámetro None recibido
TREE_NOT_FOUND = -2   # Valor no encontrado
TREE_EMPTY     = -3   # Operación sobre árbol vacío


class _TreeNode:
    """Nodo interno del BST. No debe usarse fuera de este módulo."""
    __slots__ = ("data", "left", "right")

    def __init__(self, data: int):
        self.data: int = data
        self.left: "_TreeNode | None" = None
        self.right: "_TreeNode | None" = None


class Tree:
    """
    Árbol Binario de Búsqueda con operaciones thread-safe.
    El acceso concurrente está protegido por un threading.Lock por instancia.
    """
    def __init__(self):
        self._root: _TreeNode | None = None
        self._size: int = 0
        self._lock: threading.Lock = threading.Lock()

    @property
    def size(self) -> int:
        return self._size


# ─── Fábrica y destrucción ─────────────────────────────────────

def tree_create() -> Tree:
    """Crea y retorna una nueva instancia de Tree vacía."""
    return Tree()


def tree_destroy(tree: Tree | None) -> int:
    """
    Destruye el árbol liberando todos los nodos.
    Retorna TREE_OK en éxito, TREE_NULL_PTR si tree es None.
    """
    if tree is None:
        return TREE_NULL_PTR
    with tree._lock:
        tree._root = None
        tree._size = 0
    return TREE_OK


# ─── Operaciones de mutación ───────────────────────────────────

def tree_insert(tree: Tree | None, value: int) -> int:
    """
    Inserta un entero en el BST. Ignora duplicados (retorna TREE_OK igualmente).
    Retorna TREE_OK en éxito, TREE_NULL_PTR si tree es None.
    """
    if tree is None:
        return TREE_NULL_PTR
    new_node = _TreeNode(value)
    with tree._lock:
        if tree._root is None:
            tree._root = new_node
            tree._size += 1
        else:
            inserted = _insert_unlocked(tree._root, new_node)
            if inserted:
                tree._size += 1
    return TREE_OK


def _insert_unlocked(current: _TreeNode, new_node: _TreeNode) -> bool:
    """Inserta recursivamente sin lock. Retorna True si se insertó, False si era duplicado."""
    if new_node.data < current.data:
        if current.left is None:
            current.left = new_node
            return True
        return _insert_unlocked(current.left, new_node)
    elif new_node.data > current.data:
        if current.right is None:
            current.right = new_node
            return True
        return _insert_unlocked(current.right, new_node)
    # Duplicado: no insertar
    return False


def tree_delete(tree: Tree | None, value: int) -> int:
    """
    Elimina el nodo con el valor dado del BST.
    Para nodos con 2 hijos, usa el sucesor inorden (mínimo del subárbol derecho).
    Retorna TREE_OK, TREE_NULL_PTR o TREE_NOT_FOUND.
    """
    if tree is None:
        return TREE_NULL_PTR
    with tree._lock:
        if tree._root is None:
            return TREE_NOT_FOUND
        new_root, deleted = _delete_unlocked(tree._root, value)
        if not deleted:
            return TREE_NOT_FOUND
        tree._root = new_root
        tree._size -= 1
    return TREE_OK


def _delete_unlocked(
    node: _TreeNode | None, value: int
) -> tuple["_TreeNode | None", bool]:
    """Elimina un valor del subárbol. Retorna (nuevo_nodo_raiz, fue_eliminado)."""
    if node is None:
        return (None, False)
    if value < node.data:
        node.left, deleted = _delete_unlocked(node.left, value)
        return (node, deleted)
    elif value > node.data:
        node.right, deleted = _delete_unlocked(node.right, value)
        return (node, deleted)
    # Nodo encontrado
    # Caso 0 hijos o 1 hijo izquierdo
    if node.right is None:
        return (node.left, True)
    # Caso 1 hijo derecho
    if node.left is None:
        return (node.right, True)
    # Caso 2 hijos: sucesor inorden (mínimo del subárbol derecho)
    successor = _min_node_unlocked(node.right)
    node.data = successor.data
    node.right, _ = _delete_unlocked(node.right, successor.data)
    return (node, True)


def _min_node_unlocked(node: _TreeNode) -> _TreeNode:
    """Retorna el nodo con el valor mínimo a partir de node (más a la izquierda)."""
    current = node
    while current.left is not None:
        current = current.left
    return current


# ─── Operaciones de consulta ───────────────────────────────────

def tree_search(tree: Tree | None, value: int) -> int:
    """
    Busca un valor en el BST.
    Retorna TREE_OK si encontrado, TREE_NOT_FOUND si no, TREE_NULL_PTR si tree es None.
    """
    if tree is None:
        return TREE_NULL_PTR
    with tree._lock:
        return TREE_OK if _search_unlocked(tree._root, value) else TREE_NOT_FOUND


def _search_unlocked(node: _TreeNode | None, value: int) -> bool:
    """Busca un valor de forma iterativa sin lock."""
    current = node
    while current is not None:
        if value == current.data:
            return True
        elif value < current.data:
            current = current.left
        else:
            current = current.right
    return False


def tree_inorder(tree: Tree | None) -> tuple[int, list[int]]:
    """
    Retorna (código, lista) donde lista es el recorrido inorden del árbol.
    Retorna (TREE_NULL_PTR, []) si tree es None.
    Retorna (TREE_EMPTY, []) si el árbol está vacío.
    Retorna (TREE_OK, [valores...]) en éxito.
    """
    if tree is None:
        return (TREE_NULL_PTR, [])
    with tree._lock:
        if tree._root is None:
            return (TREE_EMPTY, [])
        result: list[int] = []
        _inorder_unlocked(tree._root, result)
        return (TREE_OK, result)


def _inorder_unlocked(node: _TreeNode | None, result: list[int]) -> None:
    """Recorrido inorden recursivo sin lock."""
    if node is None:
        return
    _inorder_unlocked(node.left, result)
    result.append(node.data)
    _inorder_unlocked(node.right, result)


def tree_size(tree: Tree | None) -> int:
    """Retorna el número de nodos o TREE_NULL_PTR si tree es None."""
    if tree is None:
        return TREE_NULL_PTR
    with tree._lock:
        return tree._size
