# ESPECIFICACIÓN TÉCNICA DEL PARCIAL (CAPÍTULOS 1 A 6 + DESPLIEGUE)
> Documento canónico de requerimientos para el Roadmap Generator y agentes de implementación.

---

## 1. REGLAS ARQUITECTÓNICAS OBLIGATORIAS (NO NEGOCIABLES)

1. **Flujo estricto de capas:**
   `Router -> Service -> Unit of Work -> Repository -> Model`
   - Los **Routers** reciben peticiones, inyectan dependencias y construyen o inyectan el Unit of Work.
   - Los **Services** contienen la lógica de negocio, reciben el Unit of Work y lo abren mediante `async with uow:`. Los servicios **nunca reciben la sesión de base de datos directamente**.
   - Los **Repositories** realizan lecturas y escrituras. Las operaciones `add` y `update` ejecutan exclusivamente `await session.flush()`, **nunca commit()**. Ningún repositorio confirma transacciones.
   - El **Unit of Work (UoW)** gestiona la transacción atómica: confirma (`commit()`) al salir del bloque con éxito y revierte (`rollback()`) ante excepciones.
   - **Gestión de la sesión en el UoW:** El UoW **NO crea ni cierra la sesión física**. Recibe la sesión generada por la dependencia `get_session` de FastAPI. Esto es crítico para que las dependencias de seguridad (`get_usuario_actual`, `requiere_rol`) y el UoW **compartan la misma conexión del pool** y no se agote la base de datos en peticiones concurrentes.

2. **Paginación estándar y uniforme:**
   - Todos los listados deben devolver el envoltorio:
     ```json
     {
       "items": [...],
       "total": 10,
       "page": 1,
       "size": 20,
       "pages": 1
     }
     ```
   - Parámetros: `page` (entero >= 1, default 1), `size` (entero 1 a 100, default 20).
   - Casos borde obligatorios:
     - Con 0 resultados (`total == 0`): debe devolver 1 página vacía (`pages = 1`).
     - Si se solicita una página mayor a la última disponible (`page > pages`): debe responder con **HTTP 422 Unprocessable Entity** (ejemplo: `"La página 4 no existe: hay 3"`).

3. **Contratos estrictos (DTOs):**
   - Todos los esquemas de entrada usan `model_config = ConfigDict(extra="forbid")`.
   - Se rechaza cualquier campo no esperado con **HTTP 422**.
   - Ninguna respuesta incluye `password_hash`.
   - Operaciones `PATCH` aplican solo los campos presentes (`model_dump(exclude_unset=True)`).

---

## 2. SEGURIDAD Y CONTROL DE ACCESO (CAPÍTULO 5)

1. **Hash de Contraseñas con Bcrypt:**
   - Costo configurable en `Settings` (sin valor cableado en código).
   - Todo llamado a bcrypt se ejecuta fuera del event loop principal mediante `await asyncio.to_thread(...)` y bajo un semáforo (`asyncio.Semaphore`) que limita la concurrencia.
   - El hash se calcula **antes** de abrir transacciones de base de datos.
   - **Límite de 72 bytes:** Todos los contratos de entrada que acepten contraseñas deben validar que su longitud en bytes sea `<= 72` (`len(v.encode('utf-8')) <= 72`). Si supera los 72 bytes, responde **HTTP 422** (no 500).

2. **Tokens JWT en Cookie HttpOnly:**
   - El token viaja exclusivamente en la cookie `access_token` con directivas: `HttpOnly=True`, `SameSite="Lax"`, `Max-Age` y `Secure` configurable.
   - El cuerpo de la respuesta de `/auth/login` **no incluye el token**.
   - Si se envía `Authorization: Bearer ...` o no hay cookie, responde **HTTP 401**.

3. **Rate Limiting y Mitigación de Timing Attacks en Login:**
   - **Orden de evaluación en `/auth/login`:**
     1. Conteo de intentos fallidos en `intento_acceso` para el par `(email, ip)` en los últimos 60 segundos. Si son `>= 5`, responde inmediatamente **HTTP 429 Too Many Requests** con encabezado `Retry-After: 60`, sin calcular bcrypt.
     2. Verificación de credenciales: Si el email no existe, se calcula bcrypt contra `app.state.fictitious_password_hash` (precalculado en startup) para que tarde exactamente lo mismo y responda con el mismo mensaje genérico (**HTTP 401**).
   - **Escritura aislada de `intento_acceso`:** Cada intento de login se persiste en una **sesión y transacción independientes** con commit forzado, de modo que sobreviva al rollback del login fallido.
     - *Comentario obligatorio en el código:* Debe declarar: 1) qué hace distinto, 2) por qué no puede compartir la transacción, y 3) cuál es su costo (deja filas aunque la petición falle).

4. **Autorización Dinámica y Autoprotección:**
   - La autorización (`requiere_rol`) consulta en cada petición los roles vigentes en la tabla `asignacion_rol` (`revocada_en IS NULL` y `(vence_en IS NULL OR vence_en > now())`). Los roles en el JWT son sólo informativos.
   - Revocar un rol surte efecto en la petición inmediata (responde **HTTP 403**).
   - Un administrador no puede auto-revocarse el rol `ADMIN` ni dejar el sistema sin administradores vigentes (**HTTP 409 Conflict**).
   - `vence_en` debe exigir zona horaria y ser futura (si no, responde **HTTP 422**).

5. **Cambio Obligatorio de Contraseña y Grupos de Rutas:**
   - En `main.py` se definen dos grupos de rutas:
     - **Grupo Abierto:** `/health/*`, `/auth/registro`, `/auth/login`, `/auth/logout`, `/auth/yo`, `/auth/cambiar-password` y catálogo público (`GET /libros`, `GET /editoriales`, `GET /generos`).
     - **Grupo Protegido:** Lleva un middleware o dependencia centralizada que verifica `debe_cambiar_password == false`. Si es `true`, responde **HTTP 403 Forbidden**.

6. **Permisos en Detalle de Venta (`GET /ventas/{id}`):**
   - **No lleva `requiere_rol` en el router.**
   - El servicio verifica la pertenencia: si el usuario tiene rol de personal (`ADMIN`/`VENDEDOR`) o es el cliente dueño de la venta, responde `200`; si es un cliente ajeno, responde **HTTP 403**.

---

## 3. DOMINIO, STOCK TRANSACCIONAL Y VENTAS (CAPÍTULO 6)

1. **Evolución del Esquema de Datos:**
   - `usuario`: `id`, `email` (UNIQUE), `nombre`, `password_hash`, `activo`, `debe_cambiar_password`.
   - `asignacion_rol`: `id`, `usuario_id` (FK), `rol`, `desde`, `vence_en`, `revocada_en`, `otorgada_por` (FK).
     - Restricción: `CHECK (rol IN ('ADMIN', 'VENDEDOR', 'CLIENTE'))`.
     - Índice único parcial: `(usuario_id, rol) WHERE revocada_en IS NULL`.
   - `intento_acceso`: `id`, `cuando`, `email`, `ip`, `exito`. Índice compuesto `(email, ip, cuando)`.
   - `evento_seguridad`: `id`, `cuando`, `actor` (texto), `accion`.
   - `cliente`: agrega `usuario_id` (FK nulo permitido, UNIQUE con índice) para relación 1 a 1 opcional con navegación `cliente.usuario`.
   - `libro`: agrega `borrado_en` (timestamptz, nulo). Se elimina el `UNIQUE(isbn)` global y se reemplaza por índice único parcial: `(isbn) WHERE borrado_en IS NULL`.
   - `movimiento_stock`: `id`, `libro_id` (FK), `venta_id` (FK nulo), `usuario_id` (FK), `cantidad` (int, `CHECK cantidad <> 0`), `motivo` (str), `cuando` (timestamptz).

2. **Trigger Append-Only en `movimiento_stock`:**
   - Migración 4 manual con disparador PL/pgSQL que rechaza cualquier sentencia `UPDATE` o `DELETE`.

3. **Punto Único de Mutación de Stock:**
   - El stock **no se puede editar por PATCH** (rechazo 422).
   - Siempre se cumple: `libro.stock = SUM(movimiento_stock.cantidad)`.
   - Operaciones válidas:
     - Alta de libro (`POST /libros`): crea libro y movimiento con motivo `'Stock inicial'`.
     - Reposición (`POST /libros/{id}/reponer`): incrementa stock y crea movimiento con motivo `'Reposicion'`. Si el libro tiene `borrado_en IS NOT NULL`, responde **409**.
     - Venta (`POST /ventas`): operación atómica en un único UoW.
       - Descuenta stock de cada libro.
       - Crea un `MovimientoStock` negativo por renglón (`motivo = 'Venta'`).
       - Valida que ningún libro esté dado de baja (**409**).
       - Valida stock suficiente en todos los libros: si alguno no alcanza, hace **rollback completo** de venta, renglones, descuentos y movimientos, devolviendo **HTTP 409 Conflict**.
   - Aviso de comprobante simulado con `BackgroundTasks` (`await asyncio.sleep(0.5)`) que corre únicamente tras el commit exitoso de la venta y muestra mensaje en consola.

4. **Borrado Lógico de Libros:**
   - `DELETE /libros/{id}` realiza soft delete (`borrado_en = func.now()`) y responde **HTTP 204 No Content**.
   - El catálogo público excluye libros con `borrado_en IS NOT NULL`.
   - Su ISBN queda liberado para una nueva alta; las ventas históricas siguen referenciando al libro borrado.

5. **Lecturas sin N+1:**
   - Precarga estricta en repositorios con `joinedload` y `selectinload`.
   - `GET /ventas/{id}` resuelve el detalle con una cantidad fija de consultas SQL, sin importar el número de renglones.

---

## 4. CASOS DE PRUEBA Y DATOS INICIALES

1. **Datos Iniciales (`seed.py`):**
   - Usuarios:
     - `admin@example.com` y `admin2@example.com` (`ADMIN`).
     - `vendedor@example.com` (`VENDEDOR`).
     - `ana@example.com` (`CLIENTE`).
     - `nuevo@example.com` (`VENDEDOR`, con `debe_cambiar_password = true`).
   - 5 libros del TP con stock inicial balanceado (`libro.stock == SUM(movimientos)`):
     - `Rayuela` (10), `Antología...` (5), `Ficciones` (8), `Respiración artificial` (3), `Bestiario` (1).
   - Clientes: Lucía Fernández y Tomás Ríos (sin usuario); Ana Paz (con usuario `ana@example.com`).
   - Venta inicial 1: Lucía compra 1 Rayuela y 2 Ficciones (Total: 69000.00).
   - Evento de seguridad inicial con actor `'SISTEMA'`.

2. **Suite de Pruebas Automatizadas:**
   - Casos C-01 a C-16 en archivos `.http` dentro de `parcial/test/`.
   - Script SQL `parcial/test/solo_agregado.sql` para el caso C-14.
   - Captura de consultas fijas para C-15 en `parcial/evidencia/`.

---

## 5. DESPLIEGUE EN EL VPS (`despliegue/`)
- Carpeta independiente `despliegue/` con el código intacto del TP (Capítulos 1 a 4).
- `Dockerfile` basado en `python:3.12-alpine` (< 100 MB).
- Usuario no root (`USER appuser`).
- Sin secretos en la imagen ni archivos `.env`.
- `HEALTHCHECK` sobre `http://127.0.0.1:8000/health/ready`.
- Ejecución con `docker run --env-file`.
- Documento `DEPLOY.md` con comandos y salidas D-01 a D-08 en `despliegue/evidencia/`.