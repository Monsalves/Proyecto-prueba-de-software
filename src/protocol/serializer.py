"""
serializer.py — Serializador/Deserializador del Protocolo Bus de Objetos
Proyecto: Bus de Objetos en Python — Etapa 2
Descripción: Convierte strings del protocolo a BusMessage y viceversa.
             NUNCA hace crash ante entrada malformada: retorna None o ERROR.
             Thread-safe: no usa estado global mutable.

Formato de protocolo:
  Request:  <OBJETO>|<OPERACION>|<ID_INSTANCIA>|<DATO>\n
  Response: OK|<dato>\n  ó  ERROR|<codigo>\n
"""

from __future__ import annotations
from dataclasses import dataclass, field

# ─── Constantes del protocolo ──────────────────────────────────
MAX_MSG_LEN  = 1024
MAX_DATA_LEN = 255

VALID_OBJECTS = frozenset({"LIST", "STACK", "TREE"})

VALID_OPERATIONS = frozenset({
    "CREATE", "INSERT", "GET", "REMOVE", "SIZE", "CONTAINS", "CLEAR",
    "PUSH", "POP", "PEEK", "IS_EMPTY",
    "SEARCH", "DELETE", "INORDER",
})

# Operaciones que requieren dato numérico en <DATO>
OPS_REQUIRE_INT = frozenset({
    "INSERT", "GET", "REMOVE", "CONTAINS",
    "PUSH",
    "SEARCH", "DELETE",
})

# ─── Estructura de mensaje deserializado ───────────────────────

@dataclass
class BusMessage:
    """Representación estructurada de un mensaje de solicitud del protocolo."""
    obj_type:    str        # "LIST" | "STACK" | "TREE"
    operation:   str        # "CREATE" | "INSERT" | etc.
    instance_id: int        # ID numérico de la instancia
    data:        str = ""   # Dato crudo (string)
    data_int:    int = 0    # Dato convertido a entero (si aplica)
    has_data:    bool = False  # True si <DATO> es no vacío


# ─── Códigos de retorno del deserializer ──────────────────────
DESER_OK   =  0
DESER_ERROR = -1


# ─── Funciones principales ─────────────────────────────────────

def deserialize_message(raw: str | None) -> tuple[int, BusMessage | None]:
    """
    Parsea un string de protocolo crudo en un BusMessage estructurado.

    Retorna:
        (DESER_OK, BusMessage) en éxito.
        (DESER_ERROR, None)    ante cualquier error de formato.

    Reglas de validación:
        1. raw no puede ser None ni vacío.
        2. raw debe terminar con '\\n'.
        3. raw (sin \\n) no puede exceder MAX_MSG_LEN chars.
        4. Debe tener exactamente 4 campos separados por '|'.
        5. <OBJETO> debe ser LIST, STACK o TREE.
        6. <OPERACION> debe ser una operación válida.
        7. <ID_INSTANCIA> debe ser un entero no negativo.
        8. <DATO> debe ser entero si la operación lo requiere.
        9. <DATO> no puede superar MAX_DATA_LEN chars.
    """
    # Validación 1: None o vacío
    if not raw:
        return (DESER_ERROR, None)

    # Validación 2: terminador exacto '\n' (0x0A)
    # Se rechaza '\r\n' (CRLF) — el protocolo usa LF puro
    if not raw.endswith("\n") or raw.endswith("\r\n"):
        return (DESER_ERROR, None)

    # Quitar \n y validar longitud (Validación 3)
    body = raw[:-1]
    if len(body) > MAX_MSG_LEN:
        return (DESER_ERROR, None)

    # Validación 4: exactamente 4 campos (3 separadores '|')
    # Usamos split con maxsplit=3 para tolerar '|' dentro del dato
    parts = body.split("|", 3)
    if len(parts) != 4:
        return (DESER_ERROR, None)

    obj_str, op_str, id_str, data_str = parts

    # Validación 5: ObjectType
    obj_str = obj_str.strip().upper()
    if obj_str not in VALID_OBJECTS:
        return (DESER_ERROR, None)

    # Validación 6: Operation
    op_str = op_str.strip().upper()
    if op_str not in VALID_OPERATIONS:
        return (DESER_ERROR, None)

    # Validación 7: InstanceID
    id_str = id_str.strip()
    if not id_str.lstrip("-").isdigit():
        return (DESER_ERROR, None)
    try:
        instance_id = int(id_str)
    except ValueError:
        return (DESER_ERROR, None)
    if instance_id < 0:
        return (DESER_ERROR, None)

    # Validación 8 y 9: Dato
    data_str = data_str  # conservar como está
    has_data = len(data_str) > 0

    if len(data_str) > MAX_DATA_LEN:
        return (DESER_ERROR, None)

    data_int = 0
    if op_str in OPS_REQUIRE_INT:
        if not data_str:
            return (DESER_ERROR, None)
        try:
            data_int = int(data_str.strip())
        except ValueError:
            return (DESER_ERROR, None)
    elif has_data:
        # Para operaciones que no requieren int, intentar convertir si parece numérico
        stripped = data_str.strip()
        if stripped.lstrip("-").isdigit():
            try:
                data_int = int(stripped)
            except ValueError:
                pass

    msg = BusMessage(
        obj_type=obj_str,
        operation=op_str,
        instance_id=instance_id,
        data=data_str,
        data_int=data_int,
        has_data=has_data,
    )
    return (DESER_OK, msg)


def serialize_response(success: bool, data: str = "") -> str:
    """
    Serializa una respuesta del servidor al formato del protocolo.

    Args:
        success: True para respuesta OK, False para ERROR.
        data:    Dato a incluir (ID, valor, código de error, etc.).

    Retorna:
        'OK|<data>\\n'    si success == True.
        'ERROR|<data>\\n' si success == False.

    Nunca retorna None. Si data excede MAX_DATA_LEN es truncado.
    """
    # Truncar dato si excede límite
    if len(data) > MAX_DATA_LEN:
        data = data[:MAX_DATA_LEN]

    prefix = "OK" if success else "ERROR"
    return f"{prefix}|{data}\n"


def serialize_request(obj_type: str, operation: str,
                      instance_id: int, data: str = "") -> str:
    """
    Construye un mensaje de solicitud con el formato del protocolo.

    Retorna: '<OBJ>|<OP>|<ID>|<DATA>\\n'
    No valida los parámetros (es responsabilidad del llamador).
    """
    return f"{obj_type}|{operation}|{instance_id}|{data}\n"
