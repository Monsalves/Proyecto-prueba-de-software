"""
dispatcher.py — Enrutador de BusMessage al Objeto e Instancia Correctos
Proyecto: Bus de Objetos en Python — Etapa 3
Descripción: Recibe un BusMessage, consulta el ObjectServer, y despacha
             la operación al objeto correcto. Retorna respuesta serializada.
             Maneja: ID inexistente, operación inválida, estructura vacía.
"""

from src.protocol.serializer import (
    BusMessage,
    serialize_response,
)
from src.server.object_server import (
    server_get,
    server_create,
    server_destroy,
    SERVER_OK,
    SERVER_NOT_FOUND,
)
from src.objects.list_obj import (
    List,
    list_insert, list_remove, list_get, list_size, list_contains, list_clear,
    LIST_OK, LIST_NULL_PTR, LIST_OUT_OF_BOUNDS, LIST_EMPTY,
)
from src.objects.stack_obj import (
    Stack,
    stack_push, stack_pop, stack_peek, stack_is_empty, stack_size,
    STACK_OK, STACK_NULL_PTR, STACK_EMPTY,
)
from src.objects.tree_obj import (
    Tree,
    tree_insert, tree_search, tree_delete, tree_inorder, tree_size,
    TREE_OK, TREE_NULL_PTR, TREE_NOT_FOUND, TREE_EMPTY,
)


def dispatch(msg: BusMessage | None) -> str:
    """
    Enruta un BusMessage al objeto e instancia correctos.

    Retorna:
        Respuesta serializada en formato de protocolo ('OK|...\n' o 'ERROR|...\n').
        Si msg es None retorna 'ERROR|NULL_MESSAGE\n'.
    """
    if msg is None:
        return serialize_response(False, "NULL_MESSAGE")

    obj_type = msg.obj_type
    operation = msg.operation

    # ─── Operaciones a nivel de servidor ──────────────────────────
    if operation == "CREATE":
        code, instance_id = server_create(obj_type)
        if code == SERVER_OK:
            return serialize_response(True, str(instance_id))
        return serialize_response(False, f"CREATE_ERROR:{code}")

    if operation == "DESTROY":
        code = server_destroy(msg.instance_id)
        if code == SERVER_OK:
            return serialize_response(True, "DESTROYED")
        if code == SERVER_NOT_FOUND:
            return serialize_response(False, f"INSTANCE_NOT_FOUND:{msg.instance_id}")
        return serialize_response(False, f"DESTROY_ERROR:{code}")

    # Resolver instancia en el servidor para operaciones de objeto
    code, instance = server_get(msg.instance_id)
    if code == SERVER_NOT_FOUND:
        return serialize_response(False, f"INSTANCE_NOT_FOUND:{msg.instance_id}")

    # ─── Despacho a LIST ──────────────────────────────────────
    if obj_type == "LIST":
        if not isinstance(instance, List):
            return serialize_response(False, "TYPE_MISMATCH:expected_LIST")
        return _dispatch_list(instance, operation, msg)

    # ─── Despacho a STACK ─────────────────────────────────────
    if obj_type == "STACK":
        if not isinstance(instance, Stack):
            return serialize_response(False, "TYPE_MISMATCH:expected_STACK")
        return _dispatch_stack(instance, operation, msg)

    # ─── Despacho a TREE ──────────────────────────────────────
    if obj_type == "TREE":
        if not isinstance(instance, Tree):
            return serialize_response(False, "TYPE_MISMATCH:expected_TREE")
        return _dispatch_tree(instance, operation, msg)

    return serialize_response(False, f"INVALID_OBJECT_TYPE:{obj_type}")


# ─── Handlers por tipo ─────────────────────────────────────────

def _dispatch_list(lst: List, operation: str, msg: BusMessage) -> str:
    """Despacha operaciones sobre instancias de List."""
    if operation == "INSERT":
        code = list_insert(lst, msg.data_int)
        return serialize_response(code == LIST_OK, str(code))

    if operation == "REMOVE":
        code = list_remove(lst, msg.data_int)
        if code == LIST_OUT_OF_BOUNDS:
            return serialize_response(False, "OUT_OF_BOUNDS")
        return serialize_response(code == LIST_OK, str(code))

    if operation == "GET":
        code, value = list_get(lst, msg.data_int)
        if code == LIST_OUT_OF_BOUNDS:
            return serialize_response(False, "OUT_OF_BOUNDS")
        if code == LIST_OK:
            return serialize_response(True, str(value))
        return serialize_response(False, str(code))

    if operation == "SIZE":
        size = list_size(lst)
        return serialize_response(True, str(size))

    if operation == "CONTAINS":
        result = list_contains(lst, msg.data_int)
        return serialize_response(True, str(result))

    if operation == "CLEAR":
        code = list_clear(lst)
        return serialize_response(code == LIST_OK, str(code))

    return serialize_response(False, f"INVALID_OPERATION_FOR_LIST:{operation}")


def _dispatch_stack(stk: Stack, operation: str, msg: BusMessage) -> str:
    """Despacha operaciones sobre instancias de Stack."""
    if operation == "PUSH":
        code = stack_push(stk, msg.data_int)
        return serialize_response(code == STACK_OK, str(code))

    if operation == "POP":
        code, value = stack_pop(stk)
        if code == STACK_EMPTY:
            return serialize_response(False, "STACK_EMPTY")
        return serialize_response(code == STACK_OK, str(value))

    if operation == "PEEK":
        code, value = stack_peek(stk)
        if code == STACK_EMPTY:
            return serialize_response(False, "STACK_EMPTY")
        return serialize_response(code == STACK_OK, str(value))

    if operation == "IS_EMPTY":
        result = stack_is_empty(stk)
        return serialize_response(True, str(result))

    if operation == "SIZE":
        size = stack_size(stk)
        return serialize_response(True, str(size))

    return serialize_response(False, f"INVALID_OPERATION_FOR_STACK:{operation}")


def _dispatch_tree(tree: Tree, operation: str, msg: BusMessage) -> str:
    """Despacha operaciones sobre instancias de Tree."""
    if operation == "INSERT":
        code = tree_insert(tree, msg.data_int)
        return serialize_response(code == TREE_OK, str(code))

    if operation == "SEARCH":
        code = tree_search(tree, msg.data_int)
        if code == TREE_NOT_FOUND:
            return serialize_response(False, "NOT_FOUND")
        return serialize_response(code == TREE_OK, "FOUND")

    if operation == "DELETE":
        code = tree_delete(tree, msg.data_int)
        if code == TREE_NOT_FOUND:
            return serialize_response(False, "NOT_FOUND")
        return serialize_response(code == TREE_OK, str(code))

    if operation == "INORDER":
        code, values = tree_inorder(tree)
        if code == TREE_EMPTY:
            return serialize_response(False, "TREE_EMPTY")
        return serialize_response(code == TREE_OK, ",".join(str(v) for v in values))

    if operation == "SIZE":
        size = tree_size(tree)
        return serialize_response(True, str(size))

    return serialize_response(False, f"INVALID_OPERATION_FOR_TREE:{operation}")
