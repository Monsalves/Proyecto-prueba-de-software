# Bus de Objetos en Python

Proyecto cliente-servidor para invocar operaciones remotas sobre List, Stack y Tree mediante sockets TCP y un protocolo de texto.

## Como Ejecutar

Abre dos terminales en la raiz del proyecto.

### 1. Servidor

```bash
python -m src.server.bus_server
```

Si tu entorno usa `python3`, ejecuta:

```bash
python3 -m src.server.bus_server
```

El servidor queda escuchando en `127.0.0.1:9999`.

### 2. Cliente Grafico

Tambien hay una interfaz grafica para operar el Bus de Objetos sin escribir comandos manuales:

```bash
python -m src.client.gui_client
```

En la ventana, usa host `127.0.0.1`, puerto `9999` y presiona `Conectar`.

La GUI permite crear y operar listas, pilas y arboles BST; enviar mensajes crudos del protocolo; precargar datos de prueba; ejecutar un chequeo rapido; y ver resultados/errores en un historial legible.

### 3. Cliente de Terminal

El cliente interactivo original sigue disponible:

```bash
python -m src.client.test_client
```

## Uso Rapido de la GUI

1. Iniciar el servidor con `python -m src.server.bus_server`.
2. Abrir la interfaz con `python -m src.client.gui_client`.
3. En la ventana, mantener host `127.0.0.1` y puerto `9999`.
4. Presionar `Conectar`.
5. Usar las pestanas de Lista, Pila, Arbol o Protocolo para ejecutar operaciones.
6. Para probar concurrencia manualmente, abrir una segunda ventana de la GUI y conectarla al mismo servidor.

## Arquitectura

La interfaz grafica esta en `src/client/gui_client.py` y es solo una capa de presentacion. Todas las operaciones se ejecutan mediante `src.client.bus_client.BusClient`, que encapsula conexion TCP, serializacion de solicitudes y lectura de respuestas.

La GUI no modifica el protocolo, no llama directamente a las estructuras de datos y no duplica reglas de negocio.

Formato de solicitud:

```text
OBJETO|OPERACION|ID_INSTANCIA|DATO\n
```

Ejemplos:

```text
LIST|CREATE|0|
LIST|INSERT|1|42
LIST|GET|1|0
STACK|PUSH|2|10
TREE|INORDER|3|
```

Formato de respuesta:

```text
OK|dato\n
ERROR|codigo\n
```

## Estructura del Proyecto

```text
src/
  client/
    bus_client.py      API TCP reutilizable
    test_client.py     Cliente interactivo por terminal
    gui_client.py      Cliente grafico
  objects/
    list_obj.py        Lista enlazada thread-safe
    stack_obj.py       Pila thread-safe
    tree_obj.py        Arbol BST thread-safe
  protocol/
    serializer.py      Serializacion y deserializacion del protocolo
  server/
    bus_server.py      Servidor TCP multi-hilo
    dispatcher.py      Enrutador de operaciones
    object_server.py   Registro thread-safe de instancias
tests/
  unit/                Pruebas unitarias
  integration/         Pruebas de integracion
  system/              Pruebas de sistema
```

## Pruebas

Para ejecutar la suite disponible:

```bash
python -m unittest
```

Tambien puedes ejecutar pruebas especificas, por ejemplo:

```bash
python -m unittest tests.system.test_bus_system
```
