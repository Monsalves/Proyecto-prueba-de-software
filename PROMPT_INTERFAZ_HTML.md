 Quiero que construyas una interfaz visual local en HTML, CSS y JavaScript para este proyecto, usando como backend exclusivamente el codigo actual
 que ya existe en Python.

  Importante:
  - La interfaz se ejecutara en local.
  - El backend real debe seguir siendo el servidor actual del proyecto.
  - No quiero que reescribas la logica de negocio.
  - No quiero que implementes de nuevo las estructuras de datos en JavaScript.
  - No quiero un backend alternativo con logica nueva.
  - Solo quiero la interfaz visual.

  El sistema actual ya soporta operaciones sobre:
  - LIST
  - STACK
  - TREE

  La interfaz debe permitir:
  - conectar a host y puerto,
  - crear instancias,
  - insertar,
  - leer,
  - eliminar,
  - buscar o consultar segun corresponda,
  - ver respuestas y errores,
  - enviar mensajes crudos del protocolo,
  - precargar datos de prueba,
  - y abrir multiples clientes locales concurrentes, por ejemplo mediante varias pestañas, ventanas o sesiones independientes.

  Operaciones minimas esperadas:
  - LIST: CREATE, INSERT, GET, REMOVE, SIZE, CONTAINS
  - STACK: CREATE, PUSH, POP, PEEK, IS_EMPTY
  - TREE: CREATE, INSERT, SEARCH, DELETE, INORDER

