# Parte 3 — Suite de Pruebas Unitarias con Partición de Equivalencia

Este reporte detalla las clases de equivalencia (CE), los análisis de valores límite (AVL) y el diseño explícito de casos de prueba para cada una de las funciones principales de los módulos de la aplicación, referenciando directamente las funciones de prueba ya implementadas en el código fuente.

---

## 1. Módulo: DoublyLinkedList (`src/objects/list_obj.py`)

### Función: `list_create()`
**Clases de Equivalencia (CE):**
- CE1 (Válida): Llamada a la función de creación.
- CE2 (Inválida): Instanciación incorrecta o referenciada nula.

**Valores Límite (AVL):**
- Tamaño inicial: 0.

**Casos de Prueba:**
- **Clase válida:** `test_list_create_returns_instance` - Llamar a la función y recibir exitosamente una instancia de la clase `List`.
- **Clase inválida:** `test_list_create_multiple_instances` - Verificación de independencia; comprueba que intentar cruzar datos entre listas distintas es bloqueado y mantienen referencias independientes.
- **Valor límite inferior:** `test_list_create_initial_size` - Verifica que la lista recién creada tenga asignada estrictamente la dimensión de tamaño en `0`.
- **Valor límite superior:** `test_list_create_initial_head_tail` - Revisa la integridad de los punteros internos `_head` y `_tail` asegurando que arranquen en `None` sin desbordarse.
- **Casos especiales:** `test_list_create_lock_exists` - Verifica que el candado asíncrono `_lock` se inicie correctamente previniendo fallos de concurrencia inusuales.

### Función: `list_destroy(lst)`
**Clases de Equivalencia (CE):**
- CE1 (Válida): Parámetro de lista instanciada y en uso.
- CE2 (Inválida): Parámetro nulo (`None`).

**Casos de Prueba:**
- **Clase válida:** `test_list_destroy_valid` - Pasar una instancia con datos, devolviendo `LIST_OK` y liberando la memoria satisfactoriamente.
- **Clase inválida:** `test_list_destroy_none` - Llamar a la destrucción enviando `None`. Debe rechazar y devolver error `LIST_NULL_PTR`.
- **Valor límite inferior:** `test_list_destroy_empty` - Destruir una lista que acaba de ser inicializada y no posee elementos internamente, retornando éxito limpio.
- **Valor límite superior:** `test_list_destroy_clears_nodes` - Efectúa la destrucción total garantizando que todos los nodos internos hayan sido puestos en `None` al llegar a su final de capacidad.
- **Casos especiales:** `test_list_destroy_idempotent` - Llamadas dobles seguidas sobre la misma estructura, demostrando su comportamiento idempotente sin *crashes*.

### Función: `list_insert(lst, value)`
**Clases de Equivalencia (CE):**
- CE1 (Válida): Elemento numérico válido o cadena.
- CE2 (Inválida): Puntero `None` en la referencia de estructura.

**Casos de Prueba:**
- **Clase válida:** `test_list_insert_valid` - Inserción normal de un valor, comprobando el éxito en el incremento del tamaño dinámico.
- **Clase inválida:** `test_list_insert_none` - Proveer un valor nulo (`None`) como lista, recibiendo un error protegido en respuesta.
- **Valor límite inferior:** `test_list_insert_multiple` - Inserciones partiendo desde cero (límite inferior de memoria) para construir una estructura secuencial desde vacía.
- **Valor límite superior:** `test_list_insert_large_value` - Inserción del valor numérico límite (`INT_MAX` o gigante) confirmando persistencia de datos pesados sin colapso en la posición final válida.
- **Casos especiales:** `test_list_insert_negative` - Proveer intencionalmente valores negativos para atestiguar que el *type hinting* y la inserción LIFO o secuencial perduran intactos.

### Función: `list_remove(lst, position)`
**Clases de Equivalencia (CE):**
- CE1 (Válida): Posición intermedia.
- CE2 (Inválida): Posición negativa o superior a $size$.

**Casos de Prueba:**
- **Clase válida:** `test_list_remove_middle` - Remover exactamente el nodo central validando la reconexión de punteros cruzados contiguos.
- **Clase inválida:** `test_list_remove_none` - Uso de un apuntador a la lista origen en nulo deteniendo ejecución temprana.
- **Valor límite inferior:** `test_list_remove_head_and_tail` - Procedimiento al borde cero (`index 0`) forzando reajustes extremos en cabeza y luego extrayendo en cola.
- **Valor límite superior:** `test_list_remove_out_of_bounds_upper` - Consultar un índice estrictamente igual o mayor a `size` retornando el error de salida de límites.
- **Casos especiales:** `test_list_remove_out_of_bounds_negative` - Ingresar índices negativos extraños que pudieran descontrolar iteradores devolviendo el control al sistema de forma segura.

### Función: `list_clear(lst)`
**Clases de Equivalencia (CE):**
- CE1 (Válida): Limpiar datos de una estructura en uso.
- CE2 (Inválida): Instancia en `None`.

**Casos de Prueba:**
- **Clase válida:** `test_list_clear_populated` - Instrucción directa sobre lista poblada llevando a `size` a 0 pero conservando la vida del objeto.
- **Clase inválida:** `test_list_clear_none` - Evaluar instancia nula (`None`), forzando falla `LIST_NULL_PTR`.
- **Valor límite inferior:** `test_list_clear_empty` - Aplicar en una estructura ya en límite 0 de elementos (vacía).
- **Valor límite superior:** `test_list_clear_node_state` - Barrido masivo revisando que cada nodo se ha convertido de verdad en cenizas virtuales (estado limpio total).
- **Casos especiales:** `test_list_clear_insert_after` - Validar que la lista, una vez neutralizada, todavía acepta inserciones sin errores de *memory leak* transicional.

### Función: `list_get(lst, position)`
**Clases de Equivalencia (CE):**
- CE1 (Válida): Índices válidos $0 \le position < size$.
- CE2 (Inválida): Índices fuera del borde matemático.

**Casos de Prueba:**
- **Clase válida:** `test_list_get_valid` - Extracción sin mutación de un valor central exitosamente.
- **Clase inválida:** `test_list_get_none` - Invocación en contexto nulo arrojando un rechazo temprano sin excepciones del entorno.
- **Valor límite inferior:** `test_list_get_empty_list` - Consultar una lista que se encuentra con cero elementos arrojando estructura vacía.
- **Valor límite superior:** `test_list_get_out_of_bounds` - Exceder positivamente el índice al llegar a su final, demostrando prevención perimetral de lecturas de basura de memoria.
- **Casos especiales:** `test_list_get_negative_pos` - Pedir posiciones por debajo del eje cero simulando indexación prohibida.

### Función: `list_size(lst)`
**Clases de Equivalencia (CE):**
- CE1 (Válida): Retornar el contador dinámico exacto de tamaño.
- CE2 (Inválida): Parámetro no instanciado (`None`).

**Casos de Prueba:**
- **Clase válida:** `test_list_size_populated` - Retorna correctamente el tamaño equivalente a varias inserciones ya establecidas.
- **Clase inválida:** `test_list_size_none` - Solicitud desde referencia de memoria nula denegada.
- **Valor límite inferior:** `test_list_size_empty` - La lista está recién iniciada con su cuota fundamental al nivel 0.
- **Valor límite superior:** `test_list_size_after_insert` - Constatar un alza consistente y correcta hacia un límite dinámico incrementado por los métodos mutadores.
- **Casos especiales:** `test_list_size_after_remove` - Asegurar consistencia restando los elementos y verificando desescalamiento de conteo sin subdesbordamientos negativos.

### Función: `list_contains(lst, value)`
**Clases de Equivalencia (CE):**
- CE1 (Válida): Coincidencia real existente.
- CE2 (Válida): Ausencia del valor.
- CE3 (Inválida): Puntero de referencia malo.

**Casos de Prueba:**
- **Clase válida:** `test_list_contains_true` - Se recorre satisfactoriamente en busca de un número y se confirma existencia.
- **Clase inválida:** `test_list_contains_none` - Invocar contra puntero NULL interrumpe con error pertinente instantáneo.
- **Valor límite inferior:** `test_list_contains_empty` - Llamada contra límite absoluto base de 0 elementos resultando en ausencia (`False`).
- **Valor límite superior:** `test_list_contains_false` - Agotar la iteración completa hasta el máximo final sin producir match confirmando un chequeo exhaustivo en la cola de la lista.
- **Casos especiales:** `test_list_contains_duplicates` - Estructura que tiene un mismo elemento repetido; encuentra el match garantizando el flujo a pesar del ruido en memoria.

---

## 2. Módulo: DynamicStack (`src/objects/stack_obj.py`)

### Función: `stack_create()`
**Clases de Equivalencia (CE):**
- CE1 (Válida): Instanciación.
- CE2 (Inválida): Interacciones aisladas incorrectas.

**Casos de Prueba:**
- **Clase válida:** `test_stack_create_returns_instance` - Emisión del recurso `Stack` correctamente a un entorno asignado.
- **Clase inválida:** `test_stack_create_independent` - Verificar variables desvinculadas entre sí aislando la memoria (no se puede pasar `None` por falta de arg).
- **Valor límite inferior:** `test_stack_create_initial_size` - Creación y revisión inmediata donde se corrobora índice neto equivalente a 0.
- **Valor límite superior:** `test_stack_create_initial_top` - El tope extremo de vida de la estructura comienza fijado en límite absoluto (`None`).
- **Casos especiales:** `test_stack_create_lock_exists` - Habilitación paralela del sistema de exclusión mutua de cerrojos de estado interno.

### Función: `stack_destroy(stk)`
**Casos de Prueba:**
- **Clase válida:** `test_stack_destroy_valid` - Elimina objeto funcional cargado retornando un código base protegido.
- **Clase inválida:** `test_stack_destroy_none` - Suministro de nulo devolviendo el fallo por inyección impropia.
- **Valor límite inferior:** `test_stack_destroy_empty` - Acción sobre una variable no usada de tamaño 0.
- **Valor límite superior:** `test_stack_destroy_state` - Verificación final y general de que tanto `_top` se fue a nulo y el volumen regresó a su mínimo inofensivo.
- **Casos especiales:** `test_stack_destroy_idempotent` - Pila en modo destructivo consecutivo no crashea ni aturde el programa host asumiendo neutralidad.

### Función: `stack_push(stk, value)`
**Casos de Prueba:**
- **Clase válida:** `test_stack_push_valid` - Acomoda y engorda el stack exitosamente.
- **Clase inválida:** `test_stack_push_none` - Ingreso hacia un recipiente inerte (`None`).
- **Valor límite inferior:** `test_stack_push_lifo_order` - Instauración y seguimiento riguroso que marca el orden base al que todo elemento sucesivo deberá subordinarse (Límite dinámico temporal LIFO).
- **Valor límite superior:** `test_stack_push_boundary` - Inclusión lógica extrema pasando un dígito tipo `INT_MAX` gigante `2147483647`.
- **Casos especiales:** `test_stack_push_negative` - Prueba forzosa inyectando un digito negativo (`-5`) testando solidez de las celdillas.

### Función: `stack_pop(stk)`
**Casos de Prueba:**
- **Clase válida:** `test_stack_pop_valid` - Retirada precisa del último dato devuelto al usuario en su `tuple`.
- **Clase inválida:** `test_stack_pop_none` - Pedimento contra estructura disuelta/nula previniendo un traceback feo.
- **Valor límite inferior:** `test_stack_pop_empty` - Tratar de arrancar el último rescoldo a una pila que ostenta de antemano el límite nulo arrojando un error amigable.
- **Valor límite superior:** `test_stack_pop_until_empty` - Iterar de arriba hacia abajo la pirámide total hasta rascar la olla (límite inferior forzado).
- **Casos especiales:** `test_stack_pop_state_logic` - El ciclo esquizofrénico de "sacar, meter, meter, sacar" revalidando robustez en la brújula transicional de punteros de memoria.

### Función: `stack_peek(stk)`
**Casos de Prueba:**
- **Clase válida:** `test_stack_peek_valid` - Visibilidad normal sin efecto secundario colateral del valor en cúspide.
- **Clase inválida:** `test_stack_peek_none` - Consultar con un mal puntero devolviendo `STACK_NULL_PTR`.
- **Valor límite inferior:** `test_stack_peek_empty` - Inspeccionar un stack vació previene y deniega la manipulación alertando que no hay cúspide a revelar.
- **Valor límite superior:** `test_stack_peek_after_pop` - Luego de mutar en la frontera LIFO de máxima altura de memoria, releer que la brújula retrocedió correctamente.
- **Casos especiales:** `test_stack_peek_idempotent` - Multiplicidad de peeks con conteo estricto del tamaño reasegurando que ninguna de ellas disminuye el `size` ocultamente.

### Función: `stack_is_empty(stk)`
**Casos de Prueba:**
- **Clase válida:** `test_stack_is_empty_false` - Reafirma una base alimentada denotando Falso o `0`.
- **Clase inválida:** `test_stack_is_empty_none` - Maneja con presteza un entorno nulo.
- **Valor límite inferior:** `test_stack_is_empty_true` - Se expone recién nacida afirmando positivamente su vacuidad inmaculada.
- **Valor límite superior:** `test_stack_is_empty_after_pop` - Reestructurar el ciclo sacando su último componente volviendo nuevamente a afirmar vacío en frontera.
- **Casos especiales:** `test_stack_is_empty_clear` - Validar que la instrucción destructiva rinde a la entidad sin errores devolviéndole su estatus neutral asertivo de ser vacía en absoluto.

### Función: `stack_size(stk)`
**Casos de Prueba:**
- **Clase válida:** `test_stack_size_populated` - Confiabilidad aritmética frente a elementos añadidos empíricamente devolviendo el N° acertado.
- **Clase inválida:** `test_stack_size_none` - Evaluación interceptada en referenciado vacío rehusando operación.
- **Valor límite inferior:** `test_stack_size_empty` - Reporte escrupuloso de frontera cero frente a nacimiento de pila.
- **Valor límite superior:** `test_stack_size_increase` - Sopeso y comprobante de que cada aumento estira positivamente hacia infinito numérico admisible de la estructura.
- **Casos especiales:** `test_stack_size_decrease` - Retiro comprobado atajando descensos y constando coherencia concurrente del des-apilado.

---

## 3. Módulo: Serializer (`src/protocol/serializer.py`)

### Función: `deserialize(message)`
**Casos de Prueba:**
- **Clase válida:** `test_deserialize_valid_with_data` - Compila la trama serializada originando de manera fiel un set predecible decodificado dict.
- **Clase inválida:** `test_deserialize_invalid_separators` - Atiende cadenas que usan basuras delimitantes renegando un parsing sucio.
- **Valor límite inferior:** `test_deserialize_none_or_empty` - Una nada algorítmica expuesta como cadena abortada en su paso originario de validación por vacuidad total de string `""`.
- **Valor límite superior:** `test_deserialize_max_length` - Lecturas inmensas logran encausarse previniendo estiramientos de cuelgue asumiendo la línea máxima dictaminada.
- **Casos especiales:** `test_deserialize_missing_terminator` - La ausencia del mítico salto de línea `\n` desencadena fallos alertando la rotura inmanente del diseño de la API en el socket.

### Función: `serialize(response_dict)`
**Casos de Prueba:**
- **Clase válida:** `test_serialize_response_success` - Diccionario bien conformado engendra una string literal de bus pura y apta.
- **Clase inválida:** `test_serialize_response_error` - Falla inyectada reportando carencia de formato en la recolección original repeliendo caídas de sistema.
- **Valor límite inferior:** `test_serialize_response_empty_data` - Soportar el dict transicional sin datos pesados devolviendo una cadena simplificada lícita vacía de carga.
- **Valor límite superior:** `test_serialize_response_truncation` - Sobrecarga expuesta al truncado logrando encapsulamiento con límites de datos que sobrepasan márgenes teóricos o strings altísimos.
- **Casos especiales:** `test_serialize_response_special_chars` - Engendro dict con caracteres ilegales en la data interna que la string final debe tolerar, rechazar u ofuscar elegantemente sin corromper sus propios delimitadores `|`.
