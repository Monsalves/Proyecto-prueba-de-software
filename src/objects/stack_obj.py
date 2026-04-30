"""
stack_obj.py — Implementación de Pila (Stack) Dinámica Thread-Safe
Proyecto: Bus de Objetos en Python — Etapa 2
Descripción: Pila con semántica LIFO. Gestión manual de nodos enlazados.
             Thread-safe mediante threading.Lock por instancia.
"""

import threading

# ─── Códigos de retorno ────────────────────────────────────────
STACK_OK       =  0
STACK_NULL_PTR = -1   # Parámetro None recibido
STACK_EMPTY    = -2   # Operación sobre pila vacía (pop/peek)


class _StackNode:
    """Nodo interno del stack. No debe usarse fuera de este módulo."""
    __slots__ = ("data", "next")

    def __init__(self, data: int):
        self.data: int = data
        self.next: "_StackNode | None" = None


class Stack:
    """
    Pila dinámica con semántica LIFO.
    El tope es el nodo más recientemente insertado (top).
    El acceso concurrente está protegido por un threading.Lock por instancia.
    """
    def __init__(self):
        self._top: _StackNode | None = None
        self._size: int = 0
        self._lock: threading.Lock = threading.Lock()

    @property
    def size(self) -> int:
        return self._size


# ─── Fábrica y destrucción ─────────────────────────────────────

def stack_create() -> Stack:
    """Crea y retorna una nueva instancia de Stack vacía."""
    return Stack()


def stack_destroy(stk: Stack | None) -> int:
    """
    Destruye el stack liberando todos los nodos.
    Retorna STACK_OK en éxito, STACK_NULL_PTR si stk es None.
    """
    if stk is None:
        return STACK_NULL_PTR
    with stk._lock:
        stk._top = None
        stk._size = 0
    return STACK_OK


# ─── Operaciones de mutación ───────────────────────────────────

def stack_push(stk: Stack | None, value: int) -> int:
    """
    Inserta un entero en el tope de la pila.
    Retorna STACK_OK o STACK_NULL_PTR.
    """
    if stk is None:
        return STACK_NULL_PTR
    node = _StackNode(value)
    with stk._lock:
        node.next = stk._top
        stk._top = node
        stk._size += 1
    return STACK_OK


def stack_pop(stk: Stack | None) -> tuple[int, int | None]:
    """
    Extrae y retorna el elemento del tope (LIFO).
    Retorna (código, valor): código es STACK_OK, STACK_NULL_PTR o STACK_EMPTY.
    """
    if stk is None:
        return (STACK_NULL_PTR, None)
    with stk._lock:
        if stk._top is None:
            return (STACK_EMPTY, None)
        value = stk._top.data
        stk._top = stk._top.next
        stk._size -= 1
        return (STACK_OK, value)


# ─── Operaciones de consulta ───────────────────────────────────

def stack_peek(stk: Stack | None) -> tuple[int, int | None]:
    """
    Consulta el valor del tope SIN extraerlo.
    Retorna (código, valor): código es STACK_OK, STACK_NULL_PTR o STACK_EMPTY.
    """
    if stk is None:
        return (STACK_NULL_PTR, None)
    with stk._lock:
        if stk._top is None:
            return (STACK_EMPTY, None)
        return (STACK_OK, stk._top.data)


def stack_is_empty(stk: Stack | None) -> int:
    """
    Retorna 1 (TRUE) si size == 0, 0 (FALSE) si size > 0,
    STACK_NULL_PTR si stk es None.
    """
    if stk is None:
        return STACK_NULL_PTR
    with stk._lock:
        return 1 if stk._size == 0 else 0


def stack_size(stk: Stack | None) -> int:
    """Retorna el número de elementos o STACK_NULL_PTR si stk es None."""
    if stk is None:
        return STACK_NULL_PTR
    with stk._lock:
        return stk._size
