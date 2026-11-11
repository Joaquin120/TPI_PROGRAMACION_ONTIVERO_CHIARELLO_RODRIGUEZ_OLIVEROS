# Reglas de Negocio

Cada regla posee un identificador único con prefijo `RN-{DOMINIO}-{NN}` para facilitar su referencia y trazabilidad en el código y en los tests.

---

## Dominio: Catálogo y Libros (RN-LIB)

- **RN-LIB-01 (Identificador ISBN único):** No pueden existir dos libros con el mismo valor de `isbn`. Intentar registrar o actualizar un libro con un ISBN ya existente debe responder HTTP `409 Conflict`.
- **RN-LIB-02 (Precios estrictamente positivos):** El precio de un libro debe ser un número decimal mayor a cero (`precio > 0.00`). No se admiten libros gratuitos ni valores negativos.
- **RN-LIB-03 (Stock no negativo):** El stock disponible debe ser un número entero mayor o igual a cero (`stock >= 0`).
- **RN-LIB-04 (Obligatoriedad de autoría):** Al dar de alta un libro (`POST /libros/`), debe incluirse al menos un autor asociado (`autores.length >= 1`).
- **RN-LIB-05 (Roles de autoría válidos):** Todo autor asociado a un libro debe tener asignado uno de los cuatro roles permitidos: `'autor'`, `'coautor'`, `'traductor'` o `'ilustrador'`. Cualquier otro valor generará HTTP `422 Unprocessable Entity`.
- **RN-LIB-06 (Género opcional y representación de nulo):** El campo `genero_id` es opcional. Si un libro tiene `genero_id: null`, la interfaz del catálogo debe mostrar textualmente la etiqueta «Sin clasificar».
- **RN-LIB-07 (Búsqueda insensible a mayúsculas):** La búsqueda en `GET /libros/?titulo=...` debe realizarse de forma parcial (*case-insensitive* / `ILIKE`).

---

## Dominio: Clientes (RN-CLI)

- **RN-CLI-01 (Email único e intransferible):** No pueden existir dos clientes con la misma dirección de correo electrónico. La repetición de email en `POST /clientes/` devolverá HTTP `409 Conflict`.
- **RN-CLI-02 (Completitud de datos personales):** Los campos `nombre` y `email` son obligatorios y deben superar validación sintáctica de formato de correo.

---

## Dominio: Ventas (RN-VEN)

- **RN-VEN-01 (Existencia de cliente y libros):** Al confirmar una venta (`POST /ventas/`), el `cliente_id` y todos los `libro_id` deben existir en la base de datos. Si alguno fue dado de baja o no existe, la API responderá HTTP `409 Conflict`.
- **RN-VEN-02 (Mínimo de renglones):** Una venta debe contener como mínimo un renglón (`renglones.length >= 1`).
- **RN-VEN-03 (Cantidades enteras positivas):** La cantidad de cada libro en un renglón debe ser un entero estrictamente mayor a cero (`cantidad >= 1`).
- **RN-VEN-04 (Unicidad de libro por venta):** No se permiten libros duplicados en renglones distintos dentro de una misma transacción de venta. Si se envía el mismo `libro_id` en dos renglones, la API responderá HTTP `422 Unprocessable Entity`.
- **RN-VEN-05 (Invariante de precio histórico):** El precio unitario de cada libro vendido se congela en el renglón de venta copiando el valor vigente en el catálogo al momento del `POST`. Cambios posteriores en el precio del catálogo (`PATCH /libros/{id}`) bajo ninguna circunstancia alterarán los valores históricos ya registrados.
- **RN-VEN-06 (Cálculo fidedigno del total):** El subtotal de cada renglón es `cantidad * precio_unitario`. El total de la venta es la sumatoria de todos los subtotales. La interfaz debe mostrar los valores oficiales retornados por el backend.
- **RN-VEN-07 (Idempotencia y prevención de doble clic):** Al oprimir el botón de confirmar venta, la interfaz debe deshabilitar inmediatamente el botón y mostrar un indicador visual hasta recibir la respuesta `201` o error del servidor, evitando dobles envíos.
- **RN-VEN-08 (Preservación del borrador ante error):** Si el envío de la venta falla (error 409, 422 o de conexión), la interfaz no debe limpiar el borrador del carrito para que el usuario pueda corregir el problema sin perder los datos seleccionados.
