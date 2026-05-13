"""
object_server.py — Registro Global de Instancias de Objetos (Thread-Safe)
Proyecto: Bus de Objetos en Python — Etapa 3
Descripción: Mantiene un registro global de instancias (List, Stack, Tree).
             El diccionario y el contador de IDs están protegidos por threading.Lock.
             Funciones: create, get, delete.
"""

import threading
from src.objects.list_obj import List, list_create
from src.objects.stack_obj import Stack, stack_create
from src.objects.tree_obj import Tree, tree_create

# ─── Códigos de retorno ────────────────────────────────────────
SERVER_OK          =  0
SERVER_NULL_PTR    = -1   # Parámetro None recibido
SERVER_NOT_FOUND   = -2   # ID de instancia no registrado
SERVER_INVALID_TYPE = -3  # Tipo de objeto desconocido

# ─── Tipos de objeto válidos ───────────────────────────────────
VALID_TYPES = frozenset({"LIST", "STACK", "TREE"})


class ObjectServer:
    """
    Registro global de instancias de objetos.
    El acceso al diccionario y al contador está protegido por threading.Lock.
    """
    def __init__(self):
        self._instances: dict[int, object] = {}
        self._counter: int = 0
        self._lock: threading.Lock = threading.Lock()


# ─── Instancia global del servidor ────────────────────────────
_server = ObjectServer()


def _reset_server() -> None:
    """Reinicia el servidor. Exclusivo para uso en pruebas."""
    global _server
    _server = ObjectServer()


# ─── Operaciones principales ───────────────────────────────────

def server_create(obj_type: str | None) -> tuple[int, int | None]:
    """
    Crea una nueva instancia del tipo especificado y la registra.

    Args:
        obj_type: "LIST", "STACK" o "TREE".

    Retorna:
        (SERVER_OK, instance_id) en éxito.
        (SERVER_NULL_PTR, None) si obj_type es None.
        (SERVER_INVALID_TYPE, None) si el tipo no es válido.
    """
    if obj_type is None:
        return (SERVER_NULL_PTR, None)
    obj_type_upper = obj_type.strip().upper()
    if obj_type_upper not in VALID_TYPES:
        return (SERVER_INVALID_TYPE, None)

    if obj_type_upper == "LIST":
        instance = list_create()
    elif obj_type_upper == "STACK":
        instance = stack_create()
    else:  # TREE
        instance = tree_create()

    with _server._lock:
        _server._counter += 1
        instance_id = _server._counter
        _server._instances[instance_id] = instance

    return (SERVER_OK, instance_id)


def server_get(instance_id: int | None) -> tuple[int, object | None]:
    """
    Recupera la instancia por su ID.

    Retorna:
        (SERVER_OK, instancia) si existe.
        (SERVER_NULL_PTR, None) si instance_id es None.
        (SERVER_NOT_FOUND, None) si el ID no está registrado.
    """
    if instance_id is None:
        return (SERVER_NULL_PTR, None)
    with _server._lock:
        instance = _server._instances.get(instance_id)
    if instance is None:
        return (SERVER_NOT_FOUND, None)
    return (SERVER_OK, instance)


def server_delete(instance_id: int | None) -> int:
    """
    Elimina la instancia registrada bajo el ID dado.

    Retorna:
        SERVER_OK si se eliminó correctamente.
        SERVER_NULL_PTR si instance_id es None.
        SERVER_NOT_FOUND si el ID no existe.
    """
    if instance_id is None:
        return SERVER_NULL_PTR
    with _server._lock:
        if instance_id not in _server._instances:
            return SERVER_NOT_FOUND
        del _server._instances[instance_id]
    return SERVER_OK


def server_instance_count() -> int:
    """Retorna el número de instancias actualmente registradas."""
    with _server._lock:
        return len(_server._instances)
