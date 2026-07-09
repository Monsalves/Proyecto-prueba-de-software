#!/usr/bin/env python3
"""
gui_client.py - Interfaz grafica UAT del Bus de Objetos.

La interfaz reutiliza src.client.bus_client.BusClient como unica puerta de
entrada a la logica remota. No implementa estructuras, protocolo ni reglas de
negocio: solo valida entradas de usuario, invoca la API cliente existente y
presenta resultados comprensibles.
"""

from __future__ import annotations

import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.client.bus_client import BusClient, BusClientError


class BusGuiApp(tk.Tk):
    """Aplicacion Tkinter para operar el Bus de Objetos durante UAT."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Bus de Objetos - Cliente UAT")
        self.geometry("1040x720")
        self.minsize(920, 640)

        self.client: BusClient | None = None
        self.host_var = tk.StringVar(value="127.0.0.1")
        self.port_var = tk.StringVar(value="9999")
        self.status_var = tk.StringVar(value="Desconectado")
        self.status_color = "#b42318"

        self.entries: dict[str, tk.Entry] = {}
        self._build_styles()
        self._build_layout()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f6f7f9")
        style.configure("Panel.TFrame", background="#ffffff", borderwidth=1, relief="solid")
        style.configure("TLabel", background="#f6f7f9", foreground="#1f2937", font=("Segoe UI", 10))
        style.configure("Panel.TLabel", background="#ffffff")
        style.configure("Title.TLabel", background="#f6f7f9", font=("Segoe UI", 18, "bold"))
        style.configure("Section.TLabel", background="#ffffff", font=("Segoe UI", 12, "bold"))
        style.configure("Status.TLabel", background="#ffffff", font=("Segoe UI", 10, "bold"))
        style.configure("TButton", font=("Segoe UI", 10), padding=(10, 6))
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        header = ttk.Frame(self, padding=(18, 16, 18, 8))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Bus de Objetos - Cliente UAT", style="Title.TLabel").grid(row=0, column=0, sticky="w")

        connection = ttk.Frame(self, style="Panel.TFrame", padding=14)
        connection.grid(row=1, column=0, padx=18, pady=8, sticky="ew")
        connection.columnconfigure(8, weight=1)

        ttk.Label(connection, text="Host", style="Panel.TLabel").grid(row=0, column=0, padx=(0, 6))
        ttk.Entry(connection, textvariable=self.host_var, width=18).grid(row=0, column=1, padx=(0, 14))
        ttk.Label(connection, text="Puerto", style="Panel.TLabel").grid(row=0, column=2, padx=(0, 6))
        ttk.Entry(connection, textvariable=self.port_var, width=8).grid(row=0, column=3, padx=(0, 14))
        ttk.Button(connection, text="Conectar", style="Primary.TButton", command=self.connect).grid(row=0, column=4, padx=(0, 8))
        ttk.Button(connection, text="Desconectar", command=self.disconnect).grid(row=0, column=5, padx=(0, 14))
        ttk.Label(connection, text="Estado:", style="Panel.TLabel").grid(row=0, column=6, padx=(0, 6))
        self.status_label = ttk.Label(connection, textvariable=self.status_var, style="Status.TLabel")
        self.status_label.grid(row=0, column=7, sticky="w")

        body = ttk.Frame(self, padding=(18, 8, 18, 18))
        body.grid(row=2, column=0, sticky="nsew")
        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        operations = ttk.Notebook(body)
        operations.grid(row=0, column=0, sticky="nsw", padx=(0, 12))
        operations.add(self._build_list_tab(operations), text="Lista")
        operations.add(self._build_stack_tab(operations), text="Pila")
        operations.add(self._build_tree_tab(operations), text="Arbol")
        operations.add(self._build_protocol_tab(operations), text="Protocolo")
        operations.add(self._build_uat_tab(operations), text="UAT")

        results = ttk.Frame(body, style="Panel.TFrame", padding=12)
        results.grid(row=0, column=1, sticky="nsew")
        results.rowconfigure(1, weight=1)
        results.columnconfigure(0, weight=1)
        ttk.Label(results, text="Resultados e historial", style="Section.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.history = tk.Text(results, height=18, wrap="word", state="disabled", font=("Consolas", 10), bg="#111827", fg="#f9fafb", insertbackground="#f9fafb")
        self.history.grid(row=1, column=0, sticky="nsew")
        ttk.Button(results, text="Limpiar historial", command=self.clear_history).grid(row=2, column=0, sticky="e", pady=(10, 0))

    def _build_list_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = self._tab_frame(parent)
        self._section(frame, "Operaciones de lista", 0)
        self._button(frame, "Crear lista", 1, lambda: self._run("LIST CREATE", lambda c: f"ID = {c.list_create()}"))
        self._form(frame, "list_insert", 2, "Insertar", ["ID", "Valor"], lambda c, v: self._ok(c.list_insert(v["ID"], v["Valor"])))
        self._form(frame, "list_get", 3, "Obtener", ["ID", "Posicion"], lambda c, v: c.list_get(v["ID"], v["Posicion"]))
        self._form(frame, "list_remove", 4, "Eliminar", ["ID", "Posicion"], lambda c, v: self._ok(c.list_remove(v["ID"], v["Posicion"])))
        self._form(frame, "list_size", 5, "Tamano", ["ID"], lambda c, v: c.list_size(v["ID"]))
        self._form(frame, "list_contains", 6, "Contiene", ["ID", "Valor"], lambda c, v: "True" if c.list_contains(v["ID"], v["Valor"]) else "False")
        return frame

    def _build_stack_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = self._tab_frame(parent)
        self._section(frame, "Operaciones de pila", 0)
        self._button(frame, "Crear pila", 1, lambda: self._run("STACK CREATE", lambda c: f"ID = {c.stack_create()}"))
        self._form(frame, "stack_push", 2, "Apilar", ["ID", "Valor"], lambda c, v: self._ok(c.stack_push(v["ID"], v["Valor"])))
        self._form(frame, "stack_pop", 3, "Desapilar", ["ID"], lambda c, v: c.stack_pop(v["ID"]))
        self._form(frame, "stack_peek", 4, "Ver tope", ["ID"], lambda c, v: c.stack_peek(v["ID"]))
        self._form(frame, "stack_empty", 5, "Esta vacia", ["ID"], lambda c, v: "True" if c.stack_is_empty(v["ID"]) else "False")
        return frame

    def _build_tree_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = self._tab_frame(parent)
        self._section(frame, "Operaciones de arbol BST", 0)
        self._button(frame, "Crear arbol", 1, lambda: self._run("TREE CREATE", lambda c: f"ID = {c.tree_create()}"))
        self._form(frame, "tree_insert", 2, "Insertar", ["ID", "Valor"], lambda c, v: self._ok(c.tree_insert(v["ID"], v["Valor"])))
        self._form(frame, "tree_search", 3, "Buscar", ["ID", "Valor"], lambda c, v: "True" if c.tree_search(v["ID"], v["Valor"]) else "False")
        self._form(frame, "tree_delete", 4, "Eliminar", ["ID", "Valor"], lambda c, v: self._ok(c.tree_delete(v["ID"], v["Valor"])))
        self._form(frame, "tree_inorder", 5, "Inorden", ["ID"], lambda c, v: c.tree_inorder(v["ID"]))
        return frame

    def _build_protocol_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = self._tab_frame(parent)
        self._section(frame, "Mensaje crudo", 0)
        ttk.Label(frame, text="Solicitud", style="Panel.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 2))
        self.raw_text = tk.Text(frame, height=5, width=42, wrap="word", font=("Consolas", 10))
        self.raw_text.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        self.raw_text.insert("1.0", "LIST|CREATE|0|\n")
        ttk.Button(frame, text="Enviar mensaje", command=self.send_raw).grid(row=3, column=0, sticky="ew", pady=4)
        return frame

    def _build_uat_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = self._tab_frame(parent)
        self._section(frame, "Preparacion UAT", 0)
        self._button(frame, "Precargar datos", 1, self.preload_data)
        self._button(frame, "Ejecutar chequeo rapido", 2, self.run_smoke_uat)
        return frame

    def _tab_frame(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = ttk.Frame(parent, style="Panel.TFrame", padding=14)
        frame.columnconfigure(0, weight=1)
        return frame

    def _section(self, frame: ttk.Frame, text: str, row: int) -> None:
        ttk.Label(frame, text=text, style="Section.TLabel").grid(row=row, column=0, sticky="w", pady=(0, 10))

    def _button(self, frame: ttk.Frame, text: str, row: int, command) -> None:
        ttk.Button(frame, text=text, command=command).grid(row=row, column=0, sticky="ew", pady=5)

    def _form(self, frame: ttk.Frame, key: str, row: int, label: str, fields: list[str], action) -> None:
        group = ttk.Frame(frame, style="Panel.TFrame", padding=(0, 8, 0, 4))
        group.grid(row=row, column=0, sticky="ew", pady=4)
        group.columnconfigure(len(fields), weight=1)
        ttk.Label(group, text=label, style="Panel.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8))
        for index, field in enumerate(fields, start=1):
            entry_key = f"{key}_{field}"
            ttk.Label(group, text=field, style="Panel.TLabel").grid(row=0, column=index * 2 - 1, padx=(4, 4))
            entry = ttk.Entry(group, width=8)
            entry.grid(row=0, column=index * 2, padx=(0, 6))
            self.entries[entry_key] = entry
        ttk.Button(group, text="Ejecutar", command=lambda: self._submit_form(key, label, fields, action)).grid(row=0, column=len(fields) * 2 + 1, padx=(6, 0))

    def _submit_form(self, key: str, label: str, fields: list[str], action) -> None:
        values: dict[str, int] = {}
        for field in fields:
            raw = self.entries[f"{key}_{field}"].get().strip()
            if raw == "":
                self._show_error(f"El campo {field} es obligatorio.")
                return
            try:
                values[field] = int(raw)
            except ValueError:
                self._show_error(f"El campo {field} debe ser un numero entero.")
                return
        self._run(label.upper(), lambda client: action(client, values))

    def connect(self) -> None:
        if self.client is not None:
            self.disconnect()
        host = self.host_var.get().strip() or "127.0.0.1"
        try:
            port = int(self.port_var.get().strip())
        except ValueError:
            self._show_error("El puerto debe ser un numero entero.")
            return
        client = BusClient(host=host, port=port)
        try:
            client.connect()
        except OSError as exc:
            self._show_error(f"No se pudo conectar a {host}:{port}: {exc}")
            return
        self.client = client
        self.status_var.set(f"Conectado a {host}:{port}")
        self.status_label.configure(foreground="#067647")
        self._append("CONEXION", "OK", f"{host}:{port}")

    def disconnect(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None
        self.status_var.set("Desconectado")
        self.status_label.configure(foreground="#b42318")
        self._append("CONEXION", "OK", "desconectado")

    def send_raw(self) -> None:
        raw = self.raw_text.get("1.0", "end").strip("\n")
        if not raw.endswith("\n"):
            raw += "\n"
        self._run("RAW", lambda client: client.send_raw(raw))

    def preload_data(self) -> None:
        def action(client: BusClient) -> str:
            list_id = client.list_create()
            for value in (10, 20, 30):
                client.list_insert(list_id, value)
            stack_id = client.stack_create()
            for value in (1, 2, 3):
                client.stack_push(stack_id, value)
            tree_id = client.tree_create()
            for value in (5, 3, 8, 1, 4):
                client.tree_insert(tree_id, value)
            return f"Lista ID {list_id}: [10, 20, 30]\nPila ID {stack_id}: top=3\nArbol ID {tree_id}: [1, 3, 4, 5, 8]"

        self._run("PRECARGA UAT", action)

    def run_smoke_uat(self) -> None:
        def action(client: BusClient) -> str:
            list_id = client.list_create()
            for value in (7, 8, 9):
                client.list_insert(list_id, value)
            list_values = [client.list_get(list_id, i) for i in range(3)]

            stack_id = client.stack_create()
            for value in (1, 2, 3):
                client.stack_push(stack_id, value)
            stack_values = [client.stack_pop(stack_id) for _ in range(3)]

            tree_id = client.tree_create()
            for value in (5, 3, 8, 1, 4):
                client.tree_insert(tree_id, value)
            tree_found = client.tree_search(tree_id, 4)
            tree_missing = client.tree_search(tree_id, 9)
            inorder = client.tree_inorder(tree_id)

            passed = (
                list_values == [7, 8, 9]
                and stack_values == [3, 2, 1]
                and tree_found is True
                and tree_missing is False
                and inorder == [1, 3, 4, 5, 8]
            )
            status = "PASA" if passed else "FALLA"
            return f"{status}\nLista: {list_values}\nPila: {stack_values}\nArbol search(4)={tree_found}, search(9)={tree_missing}, inorder={inorder}"

        self._run("SMOKE UAT", action)

    def _run(self, operation: str, action) -> None:
        if self.client is None:
            self._show_error("Conecta el cliente antes de ejecutar operaciones.")
            return
        try:
            result = action(self.client)
        except BusClientError as exc:
            self._append(operation, "ERROR", str(exc))
            messagebox.showerror("Error del bus", str(exc))
            return
        except OSError as exc:
            self._append(operation, "ERROR", str(exc))
            self.disconnect()
            messagebox.showerror("Error de conexion", str(exc))
            return
        except Exception as exc:
            self._append(operation, "ERROR", str(exc))
            messagebox.showerror("Error inesperado", str(exc))
            return
        self._append(operation, "OK", str(result))

    @staticmethod
    def _ok(value) -> str:
        return "OK"

    def _show_error(self, message: str) -> None:
        self._append("VALIDACION", "ERROR", message)
        messagebox.showwarning("Validacion", message)

    def _append(self, operation: str, status: str, detail: str) -> None:
        self.history.configure(state="normal")
        self.history.insert("end", f"[{status}] {operation}\n{detail}\n\n")
        self.history.see("end")
        self.history.configure(state="disabled")

    def clear_history(self) -> None:
        self.history.configure(state="normal")
        self.history.delete("1.0", "end")
        self.history.configure(state="disabled")

    def _on_close(self) -> None:
        if self.client is not None:
            self.client.close()
        self.destroy()


def main() -> None:
    app = BusGuiApp()
    app.mainloop()


if __name__ == "__main__":
    main()
