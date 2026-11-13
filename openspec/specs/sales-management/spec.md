# Sales Management Specification

## Purpose

Permite la composición en memoria de borradores de venta y su confirmación transaccional persistente en el backend con congelamiento estricto de precios unitarios de catálogo, validación de integridad y prevención de dobles envíos.

## Requirements

### Requirement: Registro transaccional de venta con congelamiento de precios
El sistema SHALL proveer un endpoint HTTP POST en `/api/ventas/` para persistir atómicamente una nueva venta compuesta por un cliente y una lista de renglones con libros y cantidades. El sistema MUST congelar el precio unitario vigente en catálogo para cada libro vendido al momento de la transacción y calcular los subtotales y el total oficial (RN-VEN-05, RN-VEN-06).

#### Scenario: Registro exitoso de venta con múltiples renglones
- **WHEN** se envía `POST /api/ventas/` con un `cliente_id` existente y un arreglo de 2 o más renglones válidos `{ libro_id, cantidad }`
- **THEN** el sistema persiste la transacción, responde con HTTP `201 Created` y devuelve el objeto venta con su `id`, `fecha`, `cliente_id`, renglones con sus precios unitarios congelados, subtotales calculados y el `total` oficial

#### Scenario: Congelamiento inmutable de precios de catálogo
- **WHEN** se confirma una venta de un libro que tiene un precio de catálogo $P
- **THEN** el renglón de la venta persiste inmutablemente `precio_unitario: P` y `subtotal: cantidad * P`, independientemente de futuras modificaciones posteriores del catálogo

### Requirement: Validación de existencia de clientes y libros en confirmación
El sistema SHALL validar que el cliente y todos los libros involucrados en la venta existan efectivamente en la base de datos al momento del registro. Si alguno no existe, el sistema MUST rechazar la operación con HTTP `409 Conflict` (RN-VEN-01).

#### Scenario: Rechazo por cliente inexistente
- **WHEN** se envía `POST /api/ventas/` con un `cliente_id` que no corresponde a ningún cliente registrado
- **THEN** el sistema responde con HTTP `409 Conflict` y un mensaje descriptivo indicando que el cliente no existe

#### Scenario: Rechazo por libro inexistente
- **WHEN** se envía `POST /api/ventas/` conteniendo al menos un `libro_id` inexistente en el catálogo
- **THEN** el sistema responde con HTTP `409 Conflict` y un mensaje descriptivo indicando que el libro no existe

### Requirement: Control de unicidad de libros y cantidades en renglones
El sistema SHALL validar que una venta contenga al menos un renglón, que las cantidades sean enteros positivos mayores o iguales a 1, y MUST rechazar ventas que contengan el mismo libro duplicado en más de un renglón con HTTP `422 Unprocessable Entity` (RN-VEN-02, RN-VEN-03, RN-VEN-04).

#### Scenario: Rechazo por libro duplicado en la misma venta
- **WHEN** se envía `POST /api/ventas/` con una lista de renglones que repite un mismo `libro_id` en dos posiciones diferentes
- **THEN** el sistema rechaza la transacción con HTTP `422 Unprocessable Entity` señalando la duplicación del libro

#### Scenario: Rechazo por cantidades inválidas o venta vacía
- **WHEN** se envía `POST /api/ventas/` sin renglones o con un renglón cuya `cantidad` sea menor o igual a cero
- **THEN** el sistema responde con HTTP `422 Unprocessable Entity` y el detalle de la violación de contrato

### Requirement: Composición en memoria del borrador de venta en cliente
La interfaz de usuario SHALL mantener en memoria JavaScript el estado del borrador transitorio de la venta (`{ cliente_id, renglones: [] }`) sin persistirlo en el backend ni en `localStorage`, permitiendo agregar libros desde el catálogo, editar cantidades y eliminar renglones con recálculo local de subtotales (RN-VEN-03, RN-VEN-04).

#### Scenario: Agregado y eliminación de renglones en borrador
- **WHEN** el operador selecciona un libro y cantidad válida y presiona «Agregar renglón a la venta»
- **THEN** la tabla `#tabla-renglones` se actualiza agregando la fila correspondiente con su subtotal y botón de eliminación, actualizando `#venta-total`

#### Scenario: Bloqueo de duplicados en la interfaz
- **WHEN** el operador intenta agregar a la venta un libro que ya forma parte de los renglones actuales
- **THEN** la interfaz bloquea la inserción y muestra una advertencia indicando que el libro ya está presente en el borrador

### Requirement: Prevención de doble envío y preservación de borrador ante fallas
La interfaz de usuario SHALL deshabilitar el botón de confirmación `#venta-confirmar` mientras la petición HTTP a la API esté en vuelo (RN-VEN-07), y MUST preservar intactos los renglones del borrador en pantalla ante cualquier rechazo HTTP 409 o 422 para permitir su corrección (RN-VEN-08).

#### Scenario: Deshabilitación de botón durante vuelo de red
- **WHEN** el operador pulsa el botón «Confirmar venta» con un borrador válido
- **THEN** el botón se deshabilita de inmediato con cursor de espera y solo se rehabilita al finalizar la respuesta del servidor

#### Scenario: Preservación intacta del borrador ante error
- **WHEN** la confirmación de la venta es rechazada por el backend con HTTP 409 o 422
- **THEN** la interfaz muestra el error en `#venta-feedback` y mantiene todos los renglones en la tabla `#tabla-renglones` sin borrarlos ni recargar la página

#### Scenario: Reseteo de borrador tras confirmación exitosa
- **WHEN** el backend responde con HTTP `201 Created`
- **THEN** la interfaz muestra el mensaje de confirmación oficial con el total devuelto, renderiza el comprobante en `#venta-confirmada-detalle` con precios unitarios y subtotales congelados, limpia el borrador en memoria, reinicia el historial en `offset=0` refrescando `#tabla-historial` y muestra el detalle de la venta confirmada

### Requirement: Consulta paginada de historial de ventas (US-008)
El sistema SHALL exponer `GET /api/ventas/` con parámetros `limit` (`1..100`, por defecto `20`) y `offset` (`>= 0`) devolviendo las ventas ordenadas de la más reciente a la más antigua. La interfaz `#vista-historial` MUST consumir exclusivamente la API REST sin `localStorage` y ofrecer navegación por páginas y tamaño de página.

#### Scenario: Listado paginado y recuperación tras recarga
- **WHEN** se inicializa o recarga la página o el usuario navega páginas en `#vista-historial` usando `limit` y `offset`
- **THEN** `#tabla-historial` solicita `GET /api/ventas/?limit={limit}&offset={offset}` y renderiza cada venta con código, fecha y hora, cliente y total oficial

#### Scenario: Rechazo por parámetros de paginación inválidos
- **WHEN** se solicita `GET /api/ventas/` con `limit` menor a `1` o mayor a `100`, o con `offset` negativo
- **THEN** el backend responde con HTTP `422 Unprocessable Entity`

### Requirement: Detalle histórico inmutable de venta por identificador (US-008)
El sistema SHALL exponer `GET /api/ventas/{id}` retornando encabezado (`id`, `cliente_id`, `cliente_nombre`, `fecha`, `total`) y `renglones` con `precio_unitario` y `subtotal` congelados (`200 OK`), o `404 Not Found` si no existe. La vista de detalle MUST ser de solo lectura, sin controles de edición ni eliminación.

#### Scenario: Visualización de detalle histórico tras selección o recarga
- **WHEN** el usuario selecciona una venta del historial después de una recarga completa (`F5`)
- **THEN** la interfaz consulta `GET /api/ventas/{id}` y muestra cliente, fecha y hora, listado de libros, cantidades, precios unitarios congelados, subtotales y total oficial sin botones de edición o borrado

#### Scenario: Consulta de venta inexistente
- **WHEN** se consulta `GET /api/ventas/{id}` con un identificador inexistente
- **THEN** el backend responde con HTTP `404 Not Found` y la interfaz informa el error sin romper el estado visible

### Requirement: Actualización parcial de libro sin alterar ventas históricas (G-05 / RN-VEN-05)
El sistema SHALL proveer `PATCH /api/libros/{id}` para actualizar atributos del catálogo (`titulo`, `isbn`, `precio`, `stock`, `editorial_id`, `genero_id`) validando reglas de negocio (`404`, `409` por ISBN duplicado y `422` por contrato). Toda modificación posterior MUST afectar solo a futuras ventas sin alterar ventas ya confirmadas.

#### Scenario: Cambio de precio en catálogo no modifica ventas anteriores
- **WHEN** se confirma una venta de un libro con precio `P` y luego se ejecuta `PATCH /api/libros/{id}` actualizando su precio a `Q` distinto de `P`
- **THEN** `GET /api/ventas/{id}` de la venta previa sigue devolviendo `precio_unitario: P`, `subtotal` y `total` originales intactos, mientras que una nueva venta aplica `Q`

#### Scenario: Rechazo ante identificador inexistente o conflicto de ISBN
- **WHEN** se envía `PATCH /api/libros/{id}` para un libro inexistente o asignando un `isbn` ya perteneciente a otro libro
- **THEN** el sistema responde con HTTP `404 Not Found` o HTTP `409 Conflict` respectivamente

#### Scenario: Independencia de selectores de libros frente a filtros del catálogo
- **WHEN** el operador aplica un filtro de búsqueda por título o cambia de página en el catálogo y luego utiliza el selector de libros de Ventas o el formulario de actualización de precio
- **THEN** los selectores de Ventas y de edición de precio conservan el listado operativo de libros sin quedar vacíos ni recortados por el filtro visual del catálogo
