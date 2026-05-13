"""
serializer_stub.py — Stub del Serializador para Pruebas de Integración
Proyecto: Bus de Objetos en Python — Etapa 3
Descripción: Proporciona BusMessage pre-construidos, evitando pasar por
             deserialize_message. Permite probar Dispatcher y ObjectServer
             con mensajes controlados sin depender del parser de protocolo.
"""

from src.protocol.serializer import BusMessage


def make_list_insert(instance_id: int, value: int) -> BusMessage:
    """Crea un BusMessage para insertar un valor en una List."""
    return BusMessage(
        obj_type="LIST",
        operation="INSERT",
        instance_id=instance_id,
        data=str(value),
        data_int=value,
        has_data=True,
    )


def make_list_get(instance_id: int, pos: int) -> BusMessage:
    """Crea un BusMessage para obtener el elemento en posición pos de una List."""
    return BusMessage(
        obj_type="LIST",
        operation="GET",
        instance_id=instance_id,
        data=str(pos),
        data_int=pos,
        has_data=True,
    )


def make_list_remove(instance_id: int, pos: int) -> BusMessage:
    """Crea un BusMessage para eliminar el elemento en posición pos de una List."""
    return BusMessage(
        obj_type="LIST",
        operation="REMOVE",
        instance_id=instance_id,
        data=str(pos),
        data_int=pos,
        has_data=True,
    )


def make_list_size(instance_id: int) -> BusMessage:
    """Crea un BusMessage para consultar el tamaño de una List."""
    return BusMessage(
        obj_type="LIST",
        operation="SIZE",
        instance_id=instance_id,
        data="",
        data_int=0,
        has_data=False,
    )


def make_stack_push(instance_id: int, value: int) -> BusMessage:
    """Crea un BusMessage para hacer push sobre una Stack."""
    return BusMessage(
        obj_type="STACK",
        operation="PUSH",
        instance_id=instance_id,
        data=str(value),
        data_int=value,
        has_data=True,
    )


def make_stack_pop(instance_id: int) -> BusMessage:
    """Crea un BusMessage para hacer pop sobre una Stack."""
    return BusMessage(
        obj_type="STACK",
        operation="POP",
        instance_id=instance_id,
        data="",
        data_int=0,
        has_data=False,
    )


def make_stack_peek(instance_id: int) -> BusMessage:
    """Crea un BusMessage para hacer peek sobre una Stack."""
    return BusMessage(
        obj_type="STACK",
        operation="PEEK",
        instance_id=instance_id,
        data="",
        data_int=0,
        has_data=False,
    )


def make_tree_insert(instance_id: int, value: int) -> BusMessage:
    """Crea un BusMessage para insertar un valor en un Tree."""
    return BusMessage(
        obj_type="TREE",
        operation="INSERT",
        instance_id=instance_id,
        data=str(value),
        data_int=value,
        has_data=True,
    )


def make_tree_search(instance_id: int, value: int) -> BusMessage:
    """Crea un BusMessage para buscar un valor en un Tree."""
    return BusMessage(
        obj_type="TREE",
        operation="SEARCH",
        instance_id=instance_id,
        data=str(value),
        data_int=value,
        has_data=True,
    )


def make_tree_delete(instance_id: int, value: int) -> BusMessage:
    """Crea un BusMessage para eliminar un valor de un Tree."""
    return BusMessage(
        obj_type="TREE",
        operation="DELETE",
        instance_id=instance_id,
        data=str(value),
        data_int=value,
        has_data=True,
    )


def make_tree_inorder(instance_id: int) -> BusMessage:
    """Crea un BusMessage para obtener el recorrido inorden de un Tree."""
    return BusMessage(
        obj_type="TREE",
        operation="INORDER",
        instance_id=instance_id,
        data="",
        data_int=0,
        has_data=False,
    )


def make_invalid_instance(obj_type: str, operation: str, bad_id: int) -> BusMessage:
    """
    Crea un BusMessage con un instance_id que NO existe en el ObjectServer.
    Útil para probar el manejo de errores del Dispatcher.
    """
    return BusMessage(
        obj_type=obj_type,
        operation=operation,
        instance_id=bad_id,
        data="",
        data_int=0,
        has_data=False,
    )


def make_malformed(obj_type: str, operation: str, instance_id: int) -> BusMessage:
    """
    Crea un BusMessage con operación incoherente para el tipo de objeto.
    Por ejemplo: PUSH sobre una LIST, útil para probar manejo de operaciones inválidas.
    """
    return BusMessage(
        obj_type=obj_type,
        operation=operation,
        instance_id=instance_id,
        data="",
        data_int=0,
        has_data=False,
    )
