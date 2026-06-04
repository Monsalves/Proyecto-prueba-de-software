#!/usr/bin/env python3
"""
test_client.py — Cliente Interactivo del Bus de Objetos
Proyecto: Bus de Objetos en Python — Etapa 4
Descripción: Cliente interactivo para verificar el funcionamiento del bus TCP.
             Usa BusClient como API, que internamente usa serialize_request()
             y deserializa las respuestas del servidor.
Uso: python3 src/client/test_client.py [host] [port]
"""

import sys
import os

# Project root must be on sys.path so 'src' package resolves
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.client.bus_client import BusClient, BusClientError


HELP_TEXT = """
Comandos disponibles:

  list create
  list insert <id> <valor>
  list get    <id> <posicion>
  list remove <id> <posicion>
  list size   <id>
  list contains <id> <valor>

  stack create
  stack push  <id> <valor>
  stack pop   <id>
  stack peek  <id>
  stack isempty <id>

  tree create
  tree insert <id> <valor>
  tree search <id> <valor>
  tree delete <id> <valor>
  tree inorder <id>

  help   — muestra este menu
  quit   — desconecta y sale
"""


def handle(client: BusClient, parts: list[str]) -> str:
    """Executes a parsed command using BusClient. Returns result string."""
    if not parts:
        return ""

    obj = parts[0].lower()

    # ── LIST ──────────────────────────────────────────────────────────
    if obj == "list":
        if len(parts) < 2:
            return "Uso: list <create|insert|get|remove|size|contains>"
        sub = parts[1].lower()

        if sub == "create":
            return f"ID = {client.list_create()}"

        if sub == "insert" and len(parts) == 4:
            client.list_insert(int(parts[2]), int(parts[3]))
            return "OK"

        if sub == "get" and len(parts) == 4:
            return f"{client.list_get(int(parts[2]), int(parts[3]))}"

        if sub == "remove" and len(parts) == 4:
            client.list_remove(int(parts[2]), int(parts[3]))
            return "OK"

        if sub == "size" and len(parts) == 3:
            return f"size = {client.list_size(int(parts[2]))}"

        if sub == "contains" and len(parts) == 4:
            found = client.list_contains(int(parts[2]), int(parts[3]))
            return "True" if found else "False"

        return "Argumento invalido. Escribi 'help' para ver la sintaxis."

    # ── STACK ─────────────────────────────────────────────────────────
    if obj == "stack":
        if len(parts) < 2:
            return "Uso: stack <create|push|pop|peek|isempty>"
        sub = parts[1].lower()

        if sub == "create":
            return f"ID = {client.stack_create()}"

        if sub == "push" and len(parts) == 4:
            client.stack_push(int(parts[2]), int(parts[3]))
            return "OK"

        if sub == "pop" and len(parts) == 3:
            return f"{client.stack_pop(int(parts[2]))}"

        if sub == "peek" and len(parts) == 3:
            return f"{client.stack_peek(int(parts[2]))}"

        if sub in ("isempty", "is_empty") and len(parts) == 3:
            return "True (vacio)" if client.stack_is_empty(int(parts[2])) else "False (tiene elementos)"

        return "Argumento invalido. Escribi 'help' para ver la sintaxis."

    # ── TREE ──────────────────────────────────────────────────────────
    if obj == "tree":
        if len(parts) < 2:
            return "Uso: tree <create|insert|search|delete|inorder>"
        sub = parts[1].lower()

        if sub == "create":
            return f"ID = {client.tree_create()}"

        if sub == "insert" and len(parts) == 4:
            client.tree_insert(int(parts[2]), int(parts[3]))
            return "OK"

        if sub == "search" and len(parts) == 4:
            return "True" if client.tree_search(int(parts[2]), int(parts[3])) else "False"

        if sub == "delete" and len(parts) == 4:
            client.tree_delete(int(parts[2]), int(parts[3]))
            return "OK"

        if sub == "inorder" and len(parts) == 3:
            return str(client.tree_inorder(int(parts[2])))

        return "Argumento invalido. Escribi 'help' para ver la sintaxis."

    return f"Objeto desconocido: '{obj}'. Usa list, stack o tree."


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9999

    client = BusClient(host=host, port=port)

    try:
        client.connect()
    except ConnectionRefusedError:
        print(f"No se pudo conectar a {host}:{port}")
        print("Ejecuta primero: python3 -m src.server.bus_server")
        sys.exit(1)

    print(f"Conectado a {host}:{port}  |  'help' para ver comandos, 'quit' para salir.\n")

    while True:
        try:
            line = input("bus> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue

        if line.lower() in ("quit", "exit", "q"):
            break

        if line.lower() == "help":
            print(HELP_TEXT)
            continue

        try:
            result = handle(client, line.split())
            if result:
                print(f"  {result}")
        except BusClientError as e:
            print(f"  ERROR: {e}")
        except ValueError:
            print("  Error: ID y valores deben ser numeros enteros.")

    client.close()
    print("Desconectado.")


if __name__ == "__main__":
    main()
