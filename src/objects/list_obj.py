"""
list_obj.py — Implementación de Lista Enlazada Simple (Thread-Safe)
Proyecto: Bus de Objetos en Python — Etapa 2
Autor: Equipo Bus de Objetos
Descripción: Lista enlazada simple con gestión manual de nodos.
             Todos los parámetros inválidos retornan códigos de error; NUNCA hacen crash.
             Thread-safe mediante threading.Lock por instancia.
"""

import threading

# ─── Códigos de retorno ────────────────────────────────────────
LIST_OK            =  0
LIST_NULL_PTR      = -1   # Parámetro None recibido
LIST_OUT_OF_BOUNDS = -2   # Índice fuera del rango [0, size-1]
LIST_EMPTY         = -3   # Operación sobre lista vacía


class _ListNode:
    """Nodo interno de la lista enlazada. No debe usarse fuera de este módulo."""
    __slots__ = ("data", "next")

    def __init__(self, data: int):
        self.data: int = data
        self.next: "_ListNode | None" = None


class List:
    """
    Lista enlazada simple con semántica de índice 0-based.
    Atributos públicos de solo lectura: size.
    El acceso concurrente está protegido por un threading.Lock por instancia.
    """
    def __init__(self):
        self._head: _ListNode | None = None
        self._tail: _ListNode | None = None
        self._size: int = 0
        self._lock: threading.Lock = threading.Lock()

    @property
    def size(self) -> int:
        return self._size


# ─── Funciones de fábrica y destrucción ───────────────────────

def list_create() -> List:
    """Crea y retorna una nueva instancia de List vacía."""
    return List()


def list_destroy(lst: List | None) -> int:
    """
    Destruye la lista liberando todos los nodos.
    Retorna LIST_OK en éxito, LIST_NULL_PTR si lst es None.
    """
    if lst is None:
        return LIST_NULL_PTR
    with lst._lock:
        _clear_nodes(lst)
    return LIST_OK


# ─── Operaciones de mutación ───────────────────────────────────

def list_insert(lst: List | None, value: int) -> int:
    """
    Agrega un entero al final de la lista.
    Retorna LIST_OK en éxito, LIST_NULL_PTR si lst es None.
    """
    if lst is None:
        return LIST_NULL_PTR
    node = _ListNode(value)
    with lst._lock:
        if lst._head is None:
            lst._head = node
            lst._tail = node
        else:
            lst._tail.next = node
            lst._tail = node
        lst._size += 1
    return LIST_OK


def list_remove(lst: List | None, pos: int) -> int:
    """
    Elimina el nodo en la posición `pos` (0-based).
    Retorna LIST_OK, LIST_NULL_PTR o LIST_OUT_OF_BOUNDS.
    """
    if lst is None:
        return LIST_NULL_PTR
    with lst._lock:
        if pos < 0 or pos >= lst._size:
            return LIST_OUT_OF_BOUNDS
        if pos == 0:
            lst._head = lst._head.next
            if lst._head is None:
                lst._tail = None
        else:
            prev = _node_at_unlocked(lst, pos - 1)
            target = prev.next
            prev.next = target.next
            if prev.next is None:
                lst._tail = prev
        lst._size -= 1
    return LIST_OK


def list_clear(lst: List | None) -> int:
    """
    Vacía completamente la lista. Idempotente si ya está vacía.
    Retorna LIST_OK o LIST_NULL_PTR.
    """
    if lst is None:
        return LIST_NULL_PTR
    with lst._lock:
        _clear_nodes(lst)
    return LIST_OK


# ─── Operaciones de consulta ───────────────────────────────────

def list_get(lst: List | None, pos: int) -> tuple[int, int | None]:
    """
    Retorna (código, valor) donde código es LIST_OK, LIST_NULL_PTR
    o LIST_OUT_OF_BOUNDS, y valor es el entero en `pos` o None si error.
    """
    if lst is None:
        return (LIST_NULL_PTR, None)
    with lst._lock:
        if pos < 0 or pos >= lst._size:
            return (LIST_OUT_OF_BOUNDS, None)
        node = _node_at_unlocked(lst, pos)
        return (LIST_OK, node.data)


def list_size(lst: List | None) -> int:
    """Retorna el número de elementos o LIST_NULL_PTR si lst es None."""
    if lst is None:
        return LIST_NULL_PTR
    with lst._lock:
        return lst._size


def list_contains(lst: List | None, value: int) -> int:
    """
    Retorna 1 (TRUE) si value existe, 0 (FALSE) si no, LIST_NULL_PTR si lst es None.
    Una lista vacía retorna 0 (no es error).
    """
    if lst is None:
        return LIST_NULL_PTR
    with lst._lock:
        current = lst._head
        while current is not None:
            if current.data == value:
                return 1
            current = current.next
        return 0


# ─── Helpers internos (sin lock, deben llamarse dentro de with lst._lock) ──

def _node_at_unlocked(lst: List, pos: int) -> _ListNode:
    """Retorna el nodo en `pos` sin adquirir el lock. Llamar dentro de sección crítica."""
    current = lst._head
    for _ in range(pos):
        current = current.next
    return current


def _clear_nodes(lst: List) -> None:
    """Desvincula todos los nodos. Llamar dentro de sección crítica."""
    lst._head = None
    lst._tail = None
    lst._size = 0
