# Bus de Objetos en Python

## Estructura del Proyecto

La estructura del código está dividida lógicamente en código fuente, pruebas automatizadas y scripts de utilería, siguiendo el principio de responsabilidad única.

### 📦 `src/` - Código Fuente Principal

Contiene toda la lógica de negocio, manejo de red y estructuras de datos.

- **`objects/`**: Estructuras de datos soportadas por el bus.
  - `list_obj.py`: Implementación de una lista enlazada (List).
  - `stack_obj.py`: Implementación de una pila (Stack).
  - `tree_obj.py`: Implementación de un árbol binario (Tree).

- **`protocol/`**: Protocolo de comunicación.
  - `serializer.py`: Lógica para transformar comandos en texto plano ("serializar") y texto a objetos/comandos ("deserializar") para que viajen a través de la red (ej. `CREATE|LIST` o `INSERT|1|42`).

- **`server/`**: Orquestación y Conectividad.
  - `object_server.py`: Servidor principal que expone las estructuras y maneja el estado general (instancias creadas, ciclo de vida).
  - `dispatcher.py`: Enrutador de mensajes. Recibe un comando ya "deserializado" y decide a qué estructura (`objects/`) llamar o si delegarlo al servidor (`object_server.py`).

---

### 🧪 `tests/` - Pruebas y Aseguramiento de Calidad

Incluye una exhaustiva suite de pruebas para asegurar el correcto funcionamiento del bus en todo nivel. Todas las pruebas contienen IDs específicos en sus comentarios para trazabilidad.

- **`unit/`**: Pruebas Unitarias aisladas.
  - Prueban individualmente las estructuras de datos (`test_list.py`, `test_stack.py`, `test_tree.py`) y el motor de parseo (`test_serializer.py`).

- **`integration/`**: Pruebas de Integración (bottom-up).
  - Evalúan cómo interactúan los diferentes módulos entre sí.
  - `test_serializer_dispatcher.py`: Evalúa el pase de mensajes entre Protocolo ↔ Dispatcher.
  - `test_dispatcher_structures.py`: Evalúa el pase de mensajes entre Dispatcher ↔ Estructuras.
  - `test_dispatcher_socket.py`: Evalúa el flujo de red (Sockets) ↔ Dispatcher.
  - `test_dispatcher_object_server.py`: Evalúa el Dispatcher ↔ Creación de instancias.
  - **`stubs/`**: Mocks de bajo nivel (`socket_stub.py`, `serializer_stub.py`) para falsificar la red durante las pruebas locales.
  - **`concurrency/`**: Pruebas enfocadas en hilos (threads) y exclusión mutua para evitar condiciones de carrera.

---

### 🛠️ `scripts/` - Utilidades

Herramientas de automatización ajenas a la ejecución primaria del servidor.

- `publish_test_results.py`: Script utilizado por GitHub Actions para extraer los `# ID` de las pruebas y crear/actualizar un _Issue_ con el resultado en GitHub.

---

### ⚙️ Otros Archivos Importantes

- `.github/workflows/ci.yml`: Archivo de configuración de Integración Continua. Define qué pasos ejecuta GitHub al hacer _push_, instalando `pytest`, generando el JSON e invocando el script de resultados.
- `reporte_particion_equivalencia.md`: Documento de análisis y diseño de pruebas.
