# Informe de Sistema — Etapa 4: Bus TCP Completo

## Arquitectura

El sistema Bus de Objetos implementa una arquitectura cliente-servidor sobre TCP con la siguiente estructura de capas:

```
┌────────────────────┐
│    Bus Client       │  ← API de alto nivel (list_create, stack_push, etc.)
│  (bus_client.py)    │
├────────────────────┤
│   Serializer        │  ← serialize_request() / _parse_response()
│  (serializer.py)    │
├────────────────────┤
│    TCP Socket       │  ← Comunicación de red real
├────────────────────┤
│    Bus Server       │  ← Capa de comunicación TCP (1 hilo por cliente)
│  (bus_server.py)    │
├────────────────────┤
│   Serializer        │  ← deserialize_message()
│  (serializer.py)    │
├────────────────────┤
│   Dispatcher        │  ← Enrutamiento de operaciones
│  (dispatcher.py)    │
├────────────────────┤
│  Object Server      │  ← Registro global de instancias (thread-safe)
│ (object_server.py)  │
├────────────────────┤
│  List / Stack / Tree│  ← Estructuras de datos (thread-safe)
└────────────────────┘
```

### Principios de diseño respetados

1. **Separación de responsabilidades**: `bus_server.py` SOLO maneja comunicación TCP. Toda la lógica de negocio permanece en `dispatcher.py` y `object_server.py`.
2. **Reutilización**: Se reutiliza 100% del código existente sin modificaciones. El serializer, dispatcher y object_server no fueron alterados.
3. **Thread-safety**: Cada capa protege sus recursos compartidos con `threading.Lock`.

---

## Diseño de Comunicación TCP

### Protocolo

- **Request**: `OBJETO|OPERACION|ID_INSTANCIA|DATO\n`
- **Response**: `OK|dato\n` o `ERROR|codigo\n`
- **Delimitador**: `\n` (LF puro, `0x0A`). `\r\n` es rechazado.
- **Encoding**: UTF-8

### Bus Server

- Socket TCP con `SO_REUSEADDR`
- `threading.Thread(daemon=True)` por cada conexión de cliente
- Buffer de recepción para manejar fragmentación TCP
- Manejo robusto de desconexiones abruptas (`ConnectionResetError`, `BrokenPipeError`)
- Errores internos se traducen a `ERROR|INTERNAL_ERROR\n` — el servidor NUNCA crashea

### Bus Client

- API de alto nivel con métodos tipados por cada operación
- `send_raw()` para testing directo de mensajes malformados
- Manejo de respuestas `ERROR` como excepciones `BusClientError`
- `tree_search()` intercepta `NOT_FOUND` y retorna `False` (no es error de aplicación)

---

## Casos Ejecutados

### Pruebas Funcionales End-to-End (4 flujos)

| Flujo | Operaciones | Resultado |
|-------|-------------|-----------|
| **List completo** | create → insert×5(10,20,30,40,50) → get×5 → remove×2 → size==3 → verificar [30,40,50] | ✅ PASS |
| **Stack LIFO** | create → push(10,20,30) → pop×3 → verificar orden 30,20,10 + peek + is_empty | ✅ PASS |
| **Tree BST** | create → insert(5,3,8,1,4) → search(4)==True → search(9)==False → inorder==[1,3,4,5,8] + delete | ✅ PASS |
| **Multi-instancia** | List1(10,11) + List2(20,21) + Stack1(100,200) → aislamiento total verificado + 2 clientes concurrentes | ✅ PASS |

### Pruebas de Protocolo y Robustez (8 casos)

| Caso | Input | Respuesta esperada | Servidor post-test | Resultado |
|------|-------|--------------------|--------------------|-----------|
| Mensaje sin `\|` | `ESTO_NO_TIENE_SEPARADORES\n` | `ERROR\|...` | Activo | ✅ PASS |
| Objeto inválido | `QUEUE\|CREATE\|0\|\n` | `ERROR\|...` | Activo | ✅ PASS |
| ID inexistente | `LIST\|GET\|999\|0\n` | `ERROR\|...` | Activo | ✅ PASS |
| Estructura vacía | `STACK\|POP\|{id}\|\n` | `ERROR\|STACK_EMPTY` | Activo | ✅ PASS |
| Índice fuera de rango | `LIST\|GET\|{id}\|100\n` | `ERROR\|OUT_OF_BOUNDS` | Activo | ✅ PASS |
| Mensaje vacío | `\n` | `ERROR\|...` | Activo | ✅ PASS |
| Mensaje parcial | `LIST\|CREATE\n` | `ERROR\|...` | Activo | ✅ PASS |
| ID negativo | `LIST\|GET\|-1\|0\n` | `ERROR\|...` | Activo | ✅ PASS |

---

## Resultados Obtenidos

| Suite | Tests | Pasaron | Fallaron |
|-------|-------|---------|----------|
| Unit tests (Etapa 2+3) | 219 | 219 | 0 |
| E2E — test_bus_system.py | 8 | 8 | 0 |
| Protocolo — test_protocol.py | 8 | 8 | 0 |
| **TOTAL** | **235** | **235** | **0** |

**Tiempo total de ejecución**: 0.65 segundos

---

## Benchmark

### Resultados de rendimiento

| Clientes | Total Ops | Tiempo (s) | Min (µs) | Avg (µs) | P95 (µs) | Max (µs) | Throughput |
|----------|-----------|------------|----------|----------|----------|----------|------------|
| 1 | 1,000 | 0.107 | 58.57 | 103.71 | 163.06 | 815.37 | 9,388.6 ops/s |
| 5 | 5,000 | 0.970 | 85.93 | 952.75 | 1,744.06 | 3,380.12 | 5,156.9 ops/s |
| 10 | 10,000 | 1.883 | 86.20 | 1,852.27 | 3,582.27 | 7,906.25 | 5,310.8 ops/s |

### Análisis de degradación

- **5 clientes vs 1**: latencia promedio ×9.19 (degradación super-lineal)
- **10 clientes vs 1**: latencia promedio ×17.86 (degradación super-lineal)

La degradación super-lineal se explica por:
1. **GIL de Python**: solo un hilo ejecuta Python a la vez, los demás esperan
2. **Lock en object_server**: serializa acceso al registro de instancias
3. **Lock en estructuras**: serializa acceso a cada instancia de datos

### Análisis de concurrencia

- **P95/Avg ratio estable** (~1.6x a 1.9x): la distribución de latencias es consistente
- **Throughput se estabiliza** entre 5 y 10 clientes (~5,200 ops/s): cuello de botella en GIL
- **Servidor estable**: todos los escenarios completados sin crash ni errores

---

## Cobertura de Requisitos

Los requisitos funcionales relacionados con la Etapa 4 están cubiertos por:

- **Comunicación TCP real**: BusServer + BusClient con sockets reales
- **Múltiples clientes concurrentes**: threading.Thread por cliente, verificado en Flujo 4
- **Todas las operaciones**: List (6 ops), Stack (5 ops), Tree (5 ops) verificadas E2E
- **Robustez del protocolo**: 8 casos de error verificados, servidor nunca crashea
- **Rendimiento**: medido con 1, 5 y 10 clientes, min/max/avg/P95 reportados

---

## Defectos Encontrados

| # | Módulo | Descripción | Severidad | Estado |
|---|--------|-------------|-----------|--------|
| 1 | `bus_client.py` | `tree_search()` lanzaba excepción en `NOT_FOUND` en vez de retornar `False` | Media | ✅ Corregido |

**Total defectos**: 1 encontrado, 1 corregido

---

## Acciones Correctivas

1. **Defecto #1**: Se modificó `tree_search()` en `bus_client.py` para interceptar `BusClientError` con `NOT_FOUND` y retornar `False`. La causa raíz es que el dispatcher trata "no encontrado" como un ERROR del protocolo, lo cual es correcto a nivel de protocolo pero el cliente de alto nivel debe traducirlo a semántica booleana.

---

## Conclusiones

1. **La arquitectura existente era sólida**: no fue necesario modificar ningún módulo previo (dispatcher, object_server, serializer). La Etapa 4 se construyó 100% encima de lo existente.

2. **El diseño thread-safe de las etapas anteriores fue acertado**: el Lock en object_server y las estructuras permitió implementar el servidor TCP multi-hilo sin bugs de concurrencia.

3. **El protocolo basado en texto con delimitador `\n` funciona bien sobre TCP**: el buffer de recepción maneja correctamente la fragmentación de paquetes.

4. **La degradación de rendimiento bajo carga es esperable para Python con GIL**: el throughput se estabiliza alrededor de 5,000 ops/s independientemente del número de clientes, lo cual es consistente con la serialización del GIL.

5. **El servidor es robusto**: 8 tipos de mensajes malformados probados, 0 crashes. Las desconexiones abruptas se manejan limpiamente.

6. **235 tests pasan sin regresiones**: la suite completa (unit + integration + system) se ejecuta en menos de 1 segundo.
