# frontend-book-creation Specification

## Purpose

Provee la interfaz y cliente web para el alta de nuevos libros con carga dinámica de catálogos auxiliares, verificación de autores con roles y orden, y registro persistente mediante la API REST.

## Requirements

### Requirement: Carga Dinámica de Editoriales y Géneros
La interfaz de alta de libros SHALL consultar `GET /api/editoriales/` y `GET /api/generos/` al inicializarse y poblar los selectores correspondientes del formulario. El selector de género SHALL incluir una opción vacía que represente la ausencia de género («Sin clasificar», RN-LIB-06).

#### Scenario: Poblado exitoso de listas desplegables
- **WHEN** el usuario accede al formulario de alta de libros
- **THEN** el sistema envía peticiones a `/api/editoriales/` y `/api/generos/` e inserta las opciones disponibles en sus respectivos elementos `<select>`

### Requirement: Verificación y Asignación de Autores con Rol y Orden
La interfaz SHALL permitir agregar autores al libro verificando previamente su identificador mediante `GET /api/autores/{id}`, desplegando el nombre del autor verificado antes de asociarlo con un rol obligatorio (`autor`, `coautor`, `traductor`, `ilustrador`) y un número de orden correlativo.

#### Scenario: Verificación y agregado de autor válido
- **WHEN** el operador ingresa un ID de autor y solicita verificarlo
- **THEN** el sistema consulta `GET /api/autores/{id}`, muestra el nombre del autor verificado y habilita su incorporación al listado de autorías con rol y orden

#### Scenario: Rechazo ante autor inexistente
- **WHEN** el operador intenta verificar un ID de autor que no existe en la base de datos
- **THEN** el sistema detecta el error 404 y muestra un mensaje de advertencia impidiendo agregar dicho autor al formulario

### Requirement: Validación Local de Campos y Reglas de Negocio
Antes de despachar la petición de alta, el formulario SHALL validar que el título no esté vacío, el ISBN contenga formato válido, el precio sea un número estrictamente positivo (`precio > 0.00`, RN-LIB-02), el stock sea un entero mayor o igual a cero (`stock >= 0`, RN-LIB-03) y exista al menos un autor asociado (`autores.length >= 1`, RN-LIB-04).

#### Scenario: Validación exitosa de datos requeridos
- **WHEN** el operador completa todos los campos cumpliendo con precio positivo, stock no negativo y al menos un autor
- **THEN** la validación local resulta exitosa y se procede con el envío de la petición HTTP

#### Scenario: Bloqueo de envío ante precio no positivo
- **WHEN** el operador ingresa un precio menor o igual a cero (ej. `0.00` o negativo) y presiona registrar
- **THEN** el sistema detiene el envío y resalta el mensaje de error indicando que el precio debe ser mayor a cero

#### Scenario: Bloqueo de envío sin autores asociados
- **WHEN** el operador intenta registrar un libro sin haber agregado ningún autor a la lista
- **THEN** el sistema detiene el envío y advierte que debe asociar al menos un autor con su rol

### Requirement: Confirmación de Alta Exitosa (201 Created)
Al recibir una respuesta HTTP `201 Created` desde `POST /api/libros/`, el sistema SHALL desplegar un mensaje visual de éxito, restablecer todos los campos del formulario y refrescar la vista del catálogo para reflejar inmediatamente el nuevo libro.

#### Scenario: Registro exitoso de libro en backend
- **WHEN** se envía un payload válido a `POST /api/libros/` y el backend responde con código 201
- **THEN** la interfaz muestra el banner de éxito con título e ISBN, limpia los campos del formulario y refresca el catálogo

### Requirement: Preservación del Formulario ante Errores 409 y 422
Si el backend responde con HTTP `409 Conflict` (por ejemplo ante un ISBN ya registrado en la base de datos, RN-LIB-01) o HTTP `422 Unprocessable Entity` (error de validación de contrato), la interfaz SHALL mostrar el mensaje devuelto por el servidor y PRESERVAR todos los datos ingresados en el formulario sin limpiarlo.

#### Scenario: Rechazo por ISBN duplicado (409 Conflict)
- **WHEN** se envía un libro cuyo ISBN ya pertenece a otro libro existente en la base de datos
- **THEN** el servidor responde 409 Conflict, la interfaz muestra el mensaje de conflicto y todos los campos del formulario se mantienen intactos para permitir su corrección

#### Scenario: Rechazo por error de validación de contrato (422)
- **WHEN** el backend rechaza los datos con código 422 Unprocessable Entity
- **THEN** la interfaz presenta los detalles del error recibido manteniendo el formulario en su estado actual
