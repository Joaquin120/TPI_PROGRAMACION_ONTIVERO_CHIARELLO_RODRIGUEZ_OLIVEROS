# Spec Delta

## Purpose

Provee la interfaz de usuario interactiva y cliente web para consultar, buscar, paginar y visualizar el catálogo completo de libros y el detalle de sus autores desde la API REST.

## ADDED Requirements

### Requirement: Consulta y Paginación del Catálogo de Libros
La interfaz del catálogo SHALL consultar `GET /api/libros/?limit={limit}&offset={offset}` al inicializarse y renderizar el listado tabular de libros con título, ISBN, precio formateado, editorial y género. Si el campo de género es nulo, la interfaz SHALL renderizar explícitamente el texto «Sin clasificar».

#### Scenario: Carga inicial exitosa con valores por defecto
- **WHEN** la aplicación carga o el usuario navega a la vista de Catálogo
- **THEN** el sistema envía una petición `GET /api/libros/?limit=20&offset=0` y renderiza cada libro recibido mostrando título, ISBN, precio, editorial y género («Sin clasificar» si es nulo)

#### Scenario: Paginación dinámica hacia adelante y hacia atrás
- **WHEN** el usuario hace clic en el control «Siguiente» estando en la página inicial con límite de 20
- **THEN** el sistema envía una petición `GET /api/libros/?limit=20&offset=20` y actualiza la tabla con los siguientes registros

#### Scenario: Modificación de cantidad de elementos por página
- **WHEN** el usuario altera el selector de límite a un nuevo valor (por ejemplo 10 o 50)
- **THEN** el sistema recalcula el desplazamiento a `offset=0` y solicita la lista con el nuevo parámetro de límite

### Requirement: Búsqueda Insensible a Mayúsculas por Título
La interfaz SHALL proveer un formulario de búsqueda por título que dispare `GET /api/libros/?titulo={texto}&offset=0` enviando el texto ingresado. El sistema SHALL reiniciar el desplazamiento a `offset=0` ante cualquier cambio de filtro de búsqueda.

#### Scenario: Búsqueda parcial coincidente sin distinción de mayúsculas
- **WHEN** el usuario ingresa «principito» en el campo de búsqueda y ejecuta la consulta
- **THEN** el sistema consulta `GET /api/libros/?titulo=principito&offset=0` y muestra en la tabla los libros cuyos títulos coincidan parcial e insensiblemente a mayúsculas

#### Scenario: Reinicio automático del offset al cambiar el término de búsqueda
- **WHEN** el usuario se encuentra en la página 2 (`offset > 0`) y modifica el texto del buscador
- **THEN** el sistema restablece automáticamente el desplazamiento a `offset=0` para la nueva consulta

### Requirement: Gestión de Cuatro Estados Visuales Diferenciados
La interfaz de catálogo SHALL diferenciar claramente en pantalla cuatro estados visuales mutuamente excluyentes: estado de carga, catálogo vacío, búsqueda sin coincidencias y error de conexión.

#### Scenario: Estado de carga mientras se espera respuesta
- **WHEN** se dispara una petición de catálogo o búsqueda y la promesa de red está en curso
- **THEN** la interfaz muestra visiblemente un indicador de carga y oculta temporalmente los mensajes de error y resultados previos

#### Scenario: Estado de catálogo vacío
- **WHEN** la API responde con una lista vacía sin que medie ningún filtro de búsqueda
- **THEN** la interfaz muestra el mensaje descriptivo «El catálogo no tiene libros para mostrar»

#### Scenario: Búsqueda sin coincidencias
- **WHEN** la API responde con una lista vacía habiéndose enviado un término de búsqueda en `titulo`
- **THEN** la interfaz muestra el mensaje visual «No se encontraron libros»

#### Scenario: Error de conexión o falla de servidor
- **WHEN** la petición HTTP falla por error de red (502, timeout o conexión rechazada)
- **THEN** la interfaz muestra un mensaje de alerta descriptivo indicando el fallo de comunicación sin romper la aplicación

### Requirement: Consulta y Modal de Detalle de Autores
Al solicitar la inspección de un libro, la interfaz SHALL consultar `GET /api/libros/{id}` y desplegar un modal o sección de detalle con la lista completa de autores asociados, indicando nombre, rol (`autor`, `coautor`, `traductor`, `ilustrador`) y orden de autoría.

#### Scenario: Visualización exitosa de autores de un libro
- **WHEN** el usuario hace clic en el botón de ver detalle de un libro con identificador existente
- **THEN** el sistema ejecuta `GET /api/libros/{id}` y abre un panel o modal desplegando todos sus autores con su correspondiente rol y orden de participación

