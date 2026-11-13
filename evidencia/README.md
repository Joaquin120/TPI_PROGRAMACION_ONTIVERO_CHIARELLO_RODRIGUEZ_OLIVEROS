# Evidencias de Verificación End-to-End (G-01 a G-07)

Bitácora oficial de auditoría sobre la **URL pública definitiva con HTTPS** en Easypanel, conforme a `knowledge-base/11_despliegue_y_casos_de_prueba.md` y `docs/consignas_global_evaluacion_y_despliegue.md` (§4).

- **URL Pública Auditada:** _completar tras despliegue en Easypanel_
- **Commit Auditado:** _completar tras despliegue en Easypanel_

---

## Resumen de Casos de Prueba

| Caso | Módulo | Estado | Archivo / Capturas Asociadas |
|---|---|---|---|
| **G-01** | Catálogo y Paginación | `[ ] Pendiente de ejecución en URL pública` | `evidencia/g01_*` |
| **G-02** | Alta de Libro | `[ ] Pendiente de ejecución en URL pública` | `evidencia/g02_*` |
| **G-03** | Alta de Cliente | `[ ] Pendiente de ejecución en URL pública` | `evidencia/g03_*` |
| **G-04** | Registro de Venta y Persistencia | `[ ] Pendiente de ejecución en URL pública` | `evidencia/g04_*` |
| **G-05** | Invariante de Precio Histórico | `[ ] Pendiente de ejecución en URL pública` | `evidencia/g05_*` |
| **G-06** | Rechazo y Preservación de Borrador | `[ ] Pendiente de ejecución en URL pública` | `evidencia/g06_*` |
| **G-07** | Infraestructura, Healthcheck y Persistencia Post-Reinicio | `[ ] Pendiente de ejecución en URL pública` | `evidencia/g07_*` |

---

## Bitácora por Caso de Prueba

### G-01 — Catálogo y Paginación
- **Procedimiento:**
  1. Cargar el catálogo inicial en la URL pública HTTPS.
  2. Buscar por un título parcial (sin distinción de mayúsculas/minúsculas).
  3. Probar una búsqueda sin coincidencias.
  4. Avanzar y retroceder páginas usando `limit` y `offset`.
  5. Abrir el detalle de un libro para visualizar autores.
- **Resultado esperado:**
  - El listado muestra título, ISBN, precio, editorial y género (o «Sin clasificar» si `genero_id` es nulo).
  - La búsqueda sin coincidencias activa el estado vacío correspondiente.
  - El modal de detalle muestra los autores asociados consultando `GET /api/libros/{id}`.
- **Evidencia requerida:** Capturas de pantalla con Developer Tools (pestaña **Network** mostrando peticiones `GET /api/libros/`).
- **Resultado observado:** _Pendiente de ejecución en entorno público._

---

### G-02 — Alta de Libro
- **Procedimiento:**
  1. Completar el formulario de alta de libro con título, ISBN único, precio positivo, stock `>= 0`, editorial, género opcional y al menos un autor verificado por ID.
  2. Confirmar el alta y comprobar que aparece en el catálogo.
  3. Reintentar el alta utilizando exactamente el mismo ISBN.
- **Resultado esperado:**
  - La primera petición (`POST /api/libros/`) responde HTTP `201 Created` y el libro queda visible en el catálogo.
  - La segunda petición responde HTTP `409 Conflict` y la UI muestra el error amigable preservando los datos del formulario sin caerse.
- **Evidencia requerida:** Capturas de respuesta `201` y error `409` en pantalla / DevTools Network.
- **Resultado observado:** _Pendiente de ejecución en entorno público._

---

### G-03 — Alta de Cliente
- **Procedimiento:**
  1. Registrar un cliente nuevo con nombre y email válido.
  2. Reintentar el registro utilizando el mismo email.
  3. Consultar un cliente por ID en el buscador/selector de clientes.
- **Resultado esperado:**
  - El primer registro (`POST /api/clientes/`) responde HTTP `201 Created`.
  - El reintento con email duplicado responde HTTP `409 Conflict` con mensaje claro y sin perder los inputs.
  - La consulta `GET /api/clientes/{id}` devuelve los datos del cliente.
- **Evidencia requerida:** Captura del formulario mostrando alta exitosa (`201`), error `409` y consulta por ID.
- **Resultado observado:** _Pendiente de ejecución en entorno público._

---

### G-04 — Registro de Venta y Persistencia Post-Recarga
- **Procedimiento:**
  1. Seleccionar un cliente y armar un borrador con al menos 2 renglones de libros distintos.
  2. Confirmar la venta.
  3. Recargar completamente la página (`F5`) y abrir el detalle de la venta desde el historial.
- **Resultado esperado:**
  - `POST /api/ventas/` responde HTTP `201 Created`.
  - Los precios unitarios, subtotales y total oficial calculados por la API coinciden exactamente en pantalla.
  - Tras recargar la página, el historial (`GET /api/ventas/`) y el detalle (`GET /api/ventas/{id}`) conservan intactos los importes y renglones.
- **Evidencia requerida:** Captura de confirmación `201` y detalle histórico tras `F5`.
- **Resultado observado:** _Pendiente de ejecución en entorno público._

---

### G-05 — Invariante de Precio Histórico
- **Procedimiento:**
  1. Verificar una venta ya registrada de un libro A al precio original $X.
  2. Actualizar el precio del libro A mediante el formulario / `PATCH /api/libros/{id}` a un nuevo precio $Y.
  3. Consultar nuevamente el catálogo y el detalle de la venta histórica previa en el historial.
- **Resultado esperado:**
  - El catálogo y futuros borradores reflejan el nuevo precio $Y.
  - La venta histórica consultada en `GET /api/ventas/{id}` conserva intactos el `precio_unitario` original $X, su `subtotal` y el `total`.
- **Evidencia requerida:** Capturas comparativas del precio actualizado en el catálogo vs. el detalle histórico inmutable de la venta previa.
- **Resultado observado:** _Pendiente de ejecución en entorno público._

---

### G-06 — Rechazo y Preservación de Borrador
- **Procedimiento:**
  1. Probar una confirmación con libros duplicados en los renglones (`422 Unprocessable Entity`, vía petición o validación contractual).
  2. Probar una confirmación contra un `cliente_id` o `libro_id` inexistente (`409 Conflict`).
- **Resultado esperado:**
  - La venta con libro duplicado retorna `422 Unprocessable Entity`.
  - La venta con cliente/libro inexistente retorna `409 Conflict`.
  - El historial no se modifica y el borrador visible en pantalla conserva todos sus renglones intactos.
- **Evidencia requerida:** Captura de la interfaz conservando los renglones junto al mensaje de error y código HTTP en DevTools Network.
- **Resultado observado:** _Pendiente de ejecución en entorno público._

---

### G-07 — Infraestructura, HTTPS, Readiness y Persistencia Tras Reinicio
- **Procedimiento:**
  1. Verificar en Easypanel la compilación limpia de las imágenes `frontend` y `backend`.
  2. Acceder a la URL pública confirmando certificado HTTPS válido.
  3. Consultar `GET <URL_PUBLICA_HTTPS>/api/health/ready`.
  4. Reiniciar / redesplegar los servicios en Easypanel y volver a consultar los datos creados en `G-01`..`G-05`.
- **Resultado esperado:**
  - Imágenes compiladas sin errores y aplicación accesible vía HTTPS.
  - `/api/health/ready` devuelve HTTP `200` (`{"status":"ready","database":"connected"}`).
  - Los libros, precios modificados, clientes y ventas siguen persistidos en PostgreSQL tras el reinicio.
- **Evidencia requerida:** Captura/salida de logs de build/arranque en Easypanel, salida `200` de `/api/health/ready` y verificación post-reinicio en UI.
- **Resultado observado:** _Pendiente de ejecución en entorno público._
