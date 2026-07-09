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

### 2.b Interfaz Web Local

Tambien puedes usar una interfaz local en HTML/CSS/JavaScript, servida por un adaptador Python minimo que solo actua como puente hacia el backend TCP existente:

```bash
python -m src.client.web_client_server
```

Luego abre `http://127.0.0.1:8080` en el navegador.

Si quieres dejar todo listo con un solo comando, incluyendo arranque de servidor e interfaz:

```bash
bash scripts/start_local_ui.sh
```

La primera sesion que abra el navegador se conectara automaticamente a `127.0.0.1:9999` y ejecutara una precarga de datos.

Notas:

- La UI web no reimplementa estructuras ni logica de negocio.
- El backend real sigue siendo `src.server.bus_server`.
- Cada pestaña crea su propia sesion local, por lo que puedes abrir multiples clientes concurrentes.
- Si quieres apuntar a otro host o puerto del servidor TCP, configuralo en la pantalla de conexion.

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

## Uso Rapido de la Interfaz Web

1. Iniciar el servidor con `python -m src.server.bus_server`.
2. Iniciar la UI web con `python -m src.client.web_client_server`.
3. Abrir `http://127.0.0.1:8080`.
4. Conectar al host y puerto del backend TCP.
5. Operar LIST, STACK, TREE, protocolo crudo o usar la precarga.

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
