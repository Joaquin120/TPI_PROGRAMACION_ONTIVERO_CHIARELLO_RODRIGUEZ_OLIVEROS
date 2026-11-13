# client-management Specification

## Purpose

Permite el registro, validación y consulta de clientes compradores en el sistema de librería web tanto a través de la API REST como mediante la interfaz de usuario en JavaScript nativo.

## Requirements

### Requirement: Registro de clientes con email único
El sistema SHALL permitir registrar un nuevo cliente mediante una petición HTTP POST a `/api/clientes/` enviando `nombre` y `email`. La dirección de correo electrónico MUST ser única e intransferible en la base de datos (RN-CLI-01, RN-CLI-02).

#### Scenario: Registro exitoso de cliente
- **WHEN** se envía `POST /api/clientes/` con un payload JSON conteniendo `nombre: "Carlos Gómez"` y `email: "carlos.gomez@example.com"` no registrado previamente
- **THEN** el sistema responde con HTTP status `201 Created` y devuelve un objeto JSON con `id`, `nombre` y `email` persistidos en la base de datos

#### Scenario: Rechazo por email duplicado
- **WHEN** se envía `POST /api/clientes/` con un `email` que ya se encuentra registrado en el sistema
- **THEN** el sistema responde con HTTP status `409 Conflict` y un mensaje descriptivo indicando que el correo electrónico ya se encuentra registrado

#### Scenario: Validación de campos obligatorios y formato
- **WHEN** se envía `POST /api/clientes/` omitiendo el campo `nombre` o enviando un `email` con formato sintáctico inválido
- **THEN** el sistema responde con HTTP status `422 Unprocessable Entity` y el detalle de los errores de validación del contrato

### Requirement: Consulta individual de clientes por identificador
El sistema SHALL permitir la consulta de un cliente existente por su identificador numérico mediante una petición HTTP GET a `/api/clientes/{id}`.

#### Scenario: Consulta de cliente existente por ID
- **WHEN** se envía `GET /api/clientes/{id}` con un identificador válido correspondiente a un cliente persistido
- **THEN** el sistema responde con HTTP status `200 OK` y devuelve el objeto JSON con `id`, `nombre` y `email` del cliente

#### Scenario: Consulta de cliente inexistente por ID
- **WHEN** se envía `GET /api/clientes/{id}` con un identificador que no existe en el sistema
- **THEN** el sistema responde con HTTP status `404 Not Found` y un mensaje indicando que el cliente no fue encontrado

### Requirement: Listado de clientes registrados
El sistema SHALL proveer un endpoint HTTP GET a `/api/clientes/` para obtener la colección de todos los clientes registrados en el sistema, ordenados por identificador o nombre.

#### Scenario: Obtención de listado de clientes
- **WHEN** se envía `GET /api/clientes/`
- **THEN** el sistema responde con HTTP status `200 OK` y un arreglo JSON con todos los clientes registrados conteniendo sus campos `id`, `nombre` y `email`

### Requirement: Formulario interactivo y preservación ante errores
La interfaz de usuario SHALL capturar el envío del formulario `#form-alta-cliente`, validar la completitud y el formato de correo en cliente antes del despacho de red, y MUST preservar todos los datos ingresados ante cualquier rechazo HTTP 409 o 422.

#### Scenario: Envío de formulario exitoso
- **WHEN** el operador completa `nombre` y un `email` válido en `#form-alta-cliente` y confirma el formulario
- **THEN** la interfaz despacha `POST /api/clientes/`, muestra un mensaje de confirmación exitosa en `#clientes-feedback`, resetea los campos del formulario y actualiza la tabla de clientes registrados

#### Scenario: Preservación de campos ante conflicto 409
- **WHEN** el operador intenta registrar un cliente cuyo email ya existe y el servidor responde `409 Conflict`
- **THEN** la interfaz muestra el mensaje de error en `#clientes-feedback` y mantiene intactos los valores en los campos de entrada sin resetear ni cerrar el formulario

#### Scenario: Validación sintáctica en cliente
- **WHEN** el operador intenta enviar el formulario con un email vacío o que no cumple con el formato estándar `usuario@dominio.ext`
- **THEN** la interfaz bloquea el envío de red y muestra un mensaje de error solicitando corregir el formato del correo electrónico

### Requirement: Renderizado de directorio y sincronización de selector de ventas
La interfaz de usuario SHALL renderizar los clientes registrados en la tabla `#tabla-clientes`, gestionar el estado de lista vacía `#clientes-listado-vacio`, y MUST sincronizar las opciones del selector `#venta-cliente` en la sección de ventas.

#### Scenario: Renderizado de clientes en tabla
- **WHEN** existen clientes registrados y se carga la vista de clientes
- **THEN** la tabla `#tabla-clientes` despliega una fila por cliente mostrando su identificador, nombre y correo electrónico, ocultando el aviso de listado vacío

#### Scenario: Estado de listado vacío
- **WHEN** no existen clientes registrados en la base de datos
- **THEN** la tabla de clientes se oculta o permanece sin filas y se hace visible el mensaje `#clientes-listado-vacio`

#### Scenario: Sincronización reactiva con selector de ventas
- **WHEN** se registra con éxito un nuevo cliente o se actualiza la lista de clientes
- **THEN** el elemento `<select id="venta-cliente">` actualiza sus opciones para incluir al nuevo cliente permitiendo su selección inmediata para transacciones
