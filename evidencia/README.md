# Evidencias de Verificación End-to-End (G-01 a G-07)

Bitácora oficial de auditoría sobre la **URL pública definitiva con HTTPS** en Easypanel, conforme a `knowledge-base/11_despliegue_y_casos_de_prueba.md` y `docs/consignas_global_evaluacion_y_despliegue.md` (§4).

- **URL Pública Auditada:** `https://jjoc-libreria-tpi-frontend.oyerue.easypanel.host/`
- **Commit Auditado:** `ef80ead594ecd8e99977b70ededb2c07235e40df`
- **Bitácora de respuestas HTTP verificadas:** [`evidencia/verificacion_api_g01_g07.txt`](verificacion_api_g01_g07.txt)

---

## Resumen de Casos de Prueba

| Caso | Módulo | Estado | Archivo / Capturas Asociadas |
|---|---|---|---|
| **G-01** | Catálogo y Paginación | `[x] Aprobado en URL pública` | [`evidencia/g01_catalogo_detalle.png`](g01_catalogo_detalle.png), [`verificacion_api_g01_g07.txt`](verificacion_api_g01_g07.txt) |
| **G-02** | Alta de Libro | `[x] Aprobado en URL pública` | [`evidencia/g02_alta_libro_409.png`](g02_alta_libro_409.png) |
| **G-03** | Alta de Cliente | `[x] Aprobado en URL pública` | [`evidencia/g03_alta_cliente_409.png`](g03_alta_cliente_409.png), [`verificacion_api_g01_g07.txt`](verificacion_api_g01_g07.txt) |
| **G-04** | Registro de Venta y Persistencia | `[x] Aprobado en URL pública` | [`evidencia/g04_venta_201_historial.png`](g04_venta_201_historial.png) |
| **G-05** | Invariante de Precio Histórico | `[x] Aprobado en URL pública` | [`evidencia/g05_precio_invariante.png`](g05_precio_invariante.png), [`verificacion_api_g01_g07.txt`](verificacion_api_g01_g07.txt) |
| **G-06** | Rechazo y Preservación de Borrador | `[x] Aprobado en URL pública` | [`evidencia/g06_rechazo_borrador.png`](g06_rechazo_borrador.png), [`verificacion_api_g01_g07.txt`](verificacion_api_g01_g07.txt) |
| **G-07** | Infraestructura, Healthcheck y Persistencia Post-Reinicio | `[x] Aprobado en URL pública` | [`evidencia/g07_post_reinicio.png`](g07_post_reinicio.png), [`verificacion_api_g01_g07.txt`](verificacion_api_g01_g07.txt) |

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
- **Resultado observado:** **APROBADO** (`2026-11-13`). `GET /api/libros/?limit=20&offset=0` devolvió `200 OK` con los 3 libros iniciales (`Cien años de soledad`, `Ficciones`, `Rayuela`); búsqueda parcial `"soledad"` filtró correctamente; búsqueda `"NOEXISTE_XYZ_999"` activó el estado vacío en UI y devolvió `[]` en API; detalle `GET /api/libros/1` devolvió `200 OK` mostrando autor `Gabriel García Márquez (rol: autor, orden: 1)` en el modal (`g01_catalogo_detalle.png`). Como el catálogo tiene 4 libros (menor al mínimo visual de 10 por página), los botones UI de paginación permanecen deshabilitados y la paginación `limit=2&offset=0` / `offset=2` se verificó vía HTTP devolviendo páginas disjuntas `[id 1, 2]` y `[id 3, 4]` (con `genero: null` renderizado como «Sin clasificar»). Zero errores de consola.

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
- **Resultado observado:** **APROBADO** (`2026-11-13`). Alta exitosa (`POST /api/libros/` → HTTP `201 Created`) de «El Aleph E2E» (ID `4`, ISBN `9789875669901`, editorial `Alianza`, género `null` → «Sin clasificar», autor verificado ID `2` Jorge Luis Borges). Al reintentar con el mismo ISBN `9789875669901`, respondió HTTP `409 Conflict` (`{"detail":"El ISBN '9789875669901' ya se encuentra registrado"}`), mostrando el error en `#libros-feedback` y preservando todos los campos y autores asignados (`g02_alta_libro_409.png`).

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
- **Resultado observado:** **APROBADO** (`2026-11-13`). Alta exitosa (`POST /api/clientes/` → HTTP `201 Created`) de «Ana Gómez E2E» (`id: 2`, `ana.gomez.e2e@example.com`), agregado automáticamente a `#tabla-clientes` y al selector `#venta-cliente`. Consulta `GET /api/clientes/2` → HTTP `200 OK`. Al reintentar con el mismo email, `POST /api/clientes/` devolvió HTTP `409 Conflict` mostrando `Error — El correo electrónico 'ana.gomez.e2e@example.com' ya se encuentra registrado` y conservando los inputs intactos (`g03_alta_cliente_409.png`).

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
- **Resultado observado:** **APROBADO** (`2026-11-13`). *(Nota de diagnóstico: en la primera corrida E2E `POST /api/ventas/` devolvió HTTP 500 al intentar leer la relación lazy `Venta.cliente` tras `commit/refresh`; se corrigió en `ef80ead` agregando `lazy="selectin"` en `Venta.cliente` y recarga explícita con `selectinload` en `create_venta` + test de regresión).* Tras redesplegar en Easypanel, `POST /api/ventas/` devolvió HTTP `201 Created` para `V-0003` (`El Aleph E2E` × 1 @ `$21000,00` + `Cien años de soledad` × 1 @ `$25000,00` = **`$46000,00`**) con `0` errores de consola. Luego de recarga completa (`F5`), `GET /api/ventas/` (`200`) y `GET /api/ventas/3` (`200`) mantuvieron intactos ambos renglones y total (`g04_venta_201_historial.png`).

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
- **Resultado observado:** **APROBADO** (`2026-11-13`). Se actualizó el precio de «El Aleph E2E» (ID `4`) mediante el formulario `PATCH /api/libros/4` (`200 OK`) hasta `$24500,00`, reflejándose inmediatamente en `#tabla-catalogo`, `#tabla-libros` y `#venta-libro` (`g05_precio_invariante.png`). Al consultar el historial (`GET /api/ventas/1` y `GET /api/ventas/3`), `V-0001` conservó `$15000,00` (subtotal `$30000,00`, total `$48500,00`) y `V-0003` conservó `$21000,00` (subtotal `$21000,00`, total `$46000,00`). Zero errores de consola.

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
- **Resultado observado:** **APROBADO** (`2026-11-13`). En navegador, al armar borrador (`Ficciones` + `Rayuela` = `$40500,00`) e intentar duplicar `Ficciones`, la UI bloqueó el agregado mostrando `Error — El libro ya forma parte de la venta. No se permite duplicar libros.` manteniendo ambos renglones y el historial intactos (`g06_rechazo_borrador.png`). Sobre la API HTTPS (`verificacion_api_g01_g07.txt`), `POST /api/ventas/` devolvió HTTP `422 Unprocessable Entity` por libro duplicado (`RN-VEN-04`) y HTTP `409 Conflict` ante `cliente_id: 999999` o `libro_id: 999999`, manteniendo sin cambios las `3` ventas del historial. *(Observación menor: `/api/docs` pide `/openapi.json` en la raíz debido al recorte de `/api/` en Nginx, sin afectar la SPA ni `/api/*`).*

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
- **Resultado observado:** **APROBADO** (`2026-11-13`).
  1. Compilación y arranque limpios en Easypanel: logs de `libreria-tpi-backend` confirmaron `Running upgrade 001 -> 002 -> 002b -> 003`, `[seed] Datos iniciales procesados: {'editoriales_creadas': 3, 'generos_creados': 3, 'autores_creados': 3, 'libros_creados': 3, 'clientes_creados': 1}` y segunda pasada en `0` (idempotente), y `Uvicorn running on http://0.0.0.0:8000`; logs de `libreria-tpi-frontend` confirmaron `20-envsubst-on-templates.sh`, `nginx/1.26.3` y `start worker process 36`.
  2. Tras redesplegar/reiniciar ambos servicios en Easypanel (`2026-11-13 20:43`), `GET https://jjoc-libreria-tpi-frontend.oyerue.easypanel.host/api/health/ready` respondió HTTP `200` (`{"status":"ready","database":"connected"}`) y `/api/health/live` HTTP `200` (`{"status":"healthy","version":"0.1.0","environment":"production"}`).
  3. La verificación post-reinicio en navegador (`g07_post_reinicio.png`, `0` errores de consola) y API (`verificacion_api_g01_g07.txt`) confirmó persistencia íntegra en PostgreSQL sin duplicar datos seed: `4` libros (con «El Aleph E2E» a `$24500,00`), `2` clientes («Lucía Fernández» y «Ana Gómez E2E») y las `3` ventas (`V-0001` `$48500,00`, `V-0002` `$48500,00`, `V-0003` `$46000,00` con precio unitario histórico congelado en `$21000,00`).
