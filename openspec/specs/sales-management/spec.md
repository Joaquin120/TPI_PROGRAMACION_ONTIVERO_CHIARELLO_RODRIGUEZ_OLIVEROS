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
- **THEN** la interfaz muestra el mensaje de confirmación oficial con el total devuelto, limpia el borrador en memoria y restablece la tabla de renglones a su estado inicial
