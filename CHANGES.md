# CHANGES — Secuencia de Implementación

> Índice canónico de todos los changes del proyecto **Librería Web — Integración y Despliegue (UTN Programación III)**.
> Cada change es atómico: un agente puede implementarlo en una sesión (~4-6 horas).
> **Leer este archivo antes de ejecutar cualquier `/opsx:propose`.**

---

## Cómo usar este documento

1. Identificar el change a implementar (verificar que sus dependencias están en `openspec/changes/archive/`).
2. Leer los docs de la knowledge-base indicados en "Leer antes".
3. Ejecutar `/opsx:propose <nombre-del-change>`.
4. Al terminar el change, archivarlo con `/opsx:archive <nombre-del-change>`.
5. Marcar el checkbox `[x]` en este archivo.

---

## Árbol de dependencias

```
C-01 foundation-setup
  ├── C-08 docker-frontend-nginx
  └── C-02 http-client-base
        │
        ├── C-03 catalog-view-search
        ├── C-04 alta-libros
        └── C-05 alta-clientes
              │
              └── C-06 ventas-borrador-registro  ← requiere C-03, C-04, C-05
                    └── C-07 ventas-historial-detalle
                          └── C-09 easypanel-deploy-verification  ← requiere C-07, C-08
```

### Paralelismo por fase

> Cada "gate" es un punto de sincronización. Los changes dentro de un grupo pueden ejecutarse en paralelo respetando asignaciones.

```
GATE 0: ninguna
  → C-01 foundation-setup              [Agente A]

GATE 1: C-01 ✓
  → C-02 http-client-base              [Agente C]
  → C-08 docker-frontend-nginx         [Agente A]

GATE 2: C-02 ✓                         ← PRIMER FORK (3 paralelos)
  → C-03 catalog-view-search           [Agente C]
  → C-04 alta-libros                   [Agente A]
  → C-05 alta-clientes                 [Agente B]

GATE 3: C-03 + C-04 + C-05 ✓
  → C-06 ventas-borrador-registro      [Agente A]

GATE 4: C-06 ✓
  → C-07 ventas-historial-detalle      [Agente C]

GATE 5: C-07 + C-08 ✓
  → C-09 easypanel-deploy-verification [Agente A]
```

### Camino crítico (6 changes — mínimo irreducible)

```
C-01 → C-02 → C-03 → C-06 → C-07 → C-09
```

### Plan óptimo con 3 agentes

```
Paso │ Agente A (Backend / Infra)         │ Agente B (Backend Aux / Funcional) │ Agente C (Frontend Core)
─────┼────────────────────────────────────┼────────────────────────────────────┼─────────────────────────
  1  │ C-01 foundation-setup              │                 —                  │           —
  2  │ C-08 docker-frontend-nginx         │                 —                  │ C-02 http-client-base
  3  │ C-04 alta-libros                   │ C-05 alta-clientes                 │ C-03 catalog-view-search
  4  │ C-06 ventas-borrador-registro      │                 —                  │           —
  5  │                 —                  │                 —                  │ C-07 ventas-historial-detalle
  6  │ C-09 easypanel-deploy-verification │                 —                  │           —
```

---

## FASE 0 — Cimientos y Monorepo

### [C-01] `foundation-setup`
- **Estado**: `[x]` completado
- **Scope**: Scaffolding y unificación de la estructura monorepo `backend/` y `frontend/` + infraestructura inicial:
  - Estructuración de directorios raíz del proyecto: `backend/` (FastAPI, SQLAlchemy, Alembic), `frontend/` (Nginx, `public/`), `docs/`, `knowledge-base/` y `design-system/`.
  - Configuración de entornos: creación de plantillas `.env.example` en raíz y subdirectorios con variables `DATABASE_URL`, `API_UPSTREAM` y `ENVIRONMENT` (sin credenciales sensibles quemadas).
  - Verificación del backend FastAPI: inicialización en `backend/src/main.py` con endpoint de diagnóstico `/api/health/ready` retornando `{"status": "ok"}` y comprobación de conexión asíncrona a PostgreSQL.
  - Modelos SQLAlchemy y migraciones Alembic: verificación de esquemas `editoriales`, `generos`, `autores`, `libros`, `libros_autores`, `clientes`, `ventas` y `ventas_renglones`.
  - Seed inicial de datos: script o migración para poblar al menos 3 editoriales, 3 géneros, 3 autores, 3 libros con stock y 1 cliente inicial para permitir pruebas inmediatas.
  - Tests automatizados base: test de conectividad de base de datos y healthcheck con pytest.
- **Dependencias**: ninguna
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/01_vision_y_objetivos.md` §Objetivos y Alcance
  - `knowledge-base/04_modelo_de_datos.md` §Seed Data Inicial Requerido
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura de Directorios del Proyecto Unificado
  - `knowledge-base/09_decisiones_y_supuestos.md` §Supuestos Técnicos

---

## FASE 1 — Ejercicio 1: Catálogo y Cliente HTTP

### [C-02] `http-client-base`
- **Estado**: `[x]` completado
- **Scope**: Módulo de cliente HTTP centralizado en JavaScript nativo (`frontend/public/js/api.js`):
  - Creación de módulo cliente con URL base prefijada obligatoriamente en `/api` para todas las peticiones `fetch`.
  - Normalización de rutas: preservación estricta de barra final en endpoints de colección (ej: `/api/libros/`, `/api/clientes/`, `/api/ventas/`).
  - Cabeceras estándar: configuración uniforme de `Content-Type: application/json` y `Accept: application/json`.
  - Manejo unificado de respuestas HTTP: deserialización de JSON, parsing de errores `400`, `404`, `409 Conflict`, `422 Unprocessable Entity` y `500 Internal Server Error`.
  - Atrapado de fallas de conexión (red caída o error Nginx 502 Bad Gateway) retornando objetos descriptivos para retroalimentar la interfaz de usuario.
  - Métodos helper para verbos HTTP: `api.get(endpoint, params)`, `api.post(endpoint, body)`, `api.patch(endpoint, body)`.
  - Tests y verificación de `api.js` cubriendo respuestas exitosas (200, 201), errores de negocio (409, 422) y fallas de transporte.
- **Dependencias**: C-01
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/02_descripcion_general.md` §Consignas de Integración (Ejercicio 1)
  - `knowledge-base/08_arquitectura_propuesta.md` §Client HTTP Abstraction
  - `knowledge-base/07_flujos_principales.md` §Flujo 1 y Flujo 2
  - `consignas_global_evaluacion_y_despliegue.md` §Ejercicio 1: Catálogo y Cliente HTTP

---

### [C-03] `catalog-view-search`
- **Estado**: `[ ]` pendiente
- **Scope**: Catálogo interactivo con búsqueda por título, paginación y detalle de autores (Ejercicio 1 / US-001, US-002, US-003):
  - Integración en `frontend/public/index.html` y `frontend/public/js/app.js` de la vista de Catálogo.
  - Carga inicial: consulta a `GET /api/libros/?limit=20&offset=0` al montar la vista.
  - Renderizado de tarjetas o filas de libros: título, ISBN, precio formateado, nombre de editorial y género (si es nulo, renderizar etiqueta «Sin clasificar» según RN-LIB-06).
  - Paginación dinámica: controles «Anterior» y «Siguiente», selector de `limit` (1 a 100, default 20) y cálculo de desplazamiento `offset`.
  - Búsqueda por título: campo de texto que dispara `GET /api/libros/?titulo={texto}&offset=0` con filtro insensible a mayúsculas (`ILIKE`) y reinicio automático a `offset = 0` (RN-LIB-07).
  - Gestión de 4 estados visuales diferenciados en UI: estado de carga (*loading spinner*), lista vacía, búsqueda sin coincidencias («No se encontraron libros») y error de conexión.
  - Detalle modal/desplegable de libro: consulta individual `GET /api/libros/{id}` para mostrar lista completa de autores asociados indicando su rol (`autor`, `coautor`, `traductor`, `ilustrador`) y orden.
  - Verificación del caso de prueba G-01 en entorno integrado.
- **Dependencias**: C-02
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §Épica 1: Catálogo y Navegación de Libros (US-001 a US-003)
  - `knowledge-base/05_reglas_de_negocio.md` §Dominio: Catálogo y Libros (RN-LIB-06, RN-LIB-07)
  - `knowledge-base/07_flujos_principales.md` §Flujo 2: Consulta de Catálogo con Búsqueda y Paginación
  - `knowledge-base/11_despliegue_y_casos_de_prueba.md` §Caso G-01

---

## FASE 2 — Ejercicio 2: Alta de Libros y Clientes

### [C-04] `alta-libros`
- **Estado**: `[ ]` pendiente
- **Scope**: Formulario de alta de libros con validación y autorías dinámicas (Ejercicio 2A / US-004):
  - Formulario de alta en `frontend/public/index.html` y lógica de controladores en `frontend/public/js/app.js`.
  - Carga dinámica de opciones: obtención de editoriales vía `GET /api/editoriales/` y géneros vía `GET /api/generos/`.
  - Selector y verificación de autores: búsqueda o selección por ID consultando `GET /api/autores/{id}` y mostrando el nombre verificado del autor antes de agregarlo al listado.
  - Configuración de autorías múltiples: selección obligatoria de rol (`autor`, `coautor`, `traductor`, `ilustrador`) y orden secuencial (RN-LIB-04, RN-LIB-05).
  - Validaciones locales antes del envío: campos obligatorios completos, `precio > 0` (RN-LIB-02), `stock >= 0` (RN-LIB-03) y al menos un autor asociado.
  - Envío de `POST /api/libros/` con payload estructurado conteniendo metadatos y arreglo de autorías.
  - Manejo de respuestas: ante `201 Created`, mensaje de confirmación, reset del formulario y refresco reactivo del catálogo; ante `409 Conflict` (ISBN duplicado) o `422`, visualización clara del mensaje devuelto por el servidor sin cerrar el formulario.
  - Verificación del caso de prueba G-02 (alta exitosa y rechazo 409 por ISBN duplicado).
- **Dependencias**: C-02
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-004 — Alta de Nuevos Libros
  - `knowledge-base/04_modelo_de_datos.md` §libros y §libros_autores
  - `knowledge-base/05_reglas_de_negocio.md` §Dominio: Catálogo y Libros (RN-LIB-01 a RN-LIB-05)
  - `knowledge-base/11_despliegue_y_casos_de_prueba.md` §Caso G-02

---

### [C-05] `alta-clientes`
- **Estado**: `[ ]` pendiente
- **Scope**: Formulario de alta de clientes y consulta por identificador (Ejercicio 2B / US-005):
  - Formulario de alta de clientes en `frontend/public/index.html` con campos obligatorios `nombre` y `email`.
  - Validación sintáctica en cliente del formato de correo electrónico y completitud de datos (RN-CLI-02).
  - Envío de `POST /api/clientes/` mediante el cliente HTTP unificado.
  - Tratamiento de respuesta `201 Created`: notificación de éxito y actualización de la lista de clientes disponibles para ventas.
  - Tratamiento de respuesta `409 Conflict`: visualización de mensaje de advertencia («El correo ya se encuentra registrado») manteniendo el formulario intacto (RN-CLI-01).
  - Función de búsqueda y validación de cliente por ID: consulta `GET /api/clientes/{id}` para verificar nombre y existencia antes de seleccionarlo en operaciones de venta.
  - Verificación del caso de prueba G-03 (alta exitosa, rechazo 409 por email repetido y consulta por ID).
- **Dependencias**: C-02
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-005 — Alta de Clientes
  - `knowledge-base/04_modelo_de_datos.md` §clientes
  - `knowledge-base/05_reglas_de_negocio.md` §Dominio: Clientes (RN-CLI-01, RN-CLI-02)
  - `knowledge-base/11_despliegue_y_casos_de_prueba.md` §Caso G-03

---

## FASE 3 — Ejercicio 3: Registrar y Consultar Ventas

### [C-06] `ventas-borrador-registro`
- **Estado**: `[ ]` pendiente
- **Scope**: Borrador de venta en memoria y confirmación transaccional (Ejercicio 3A / US-006, US-007):
  - Estado del borrador en memoria JavaScript (`app.js`): estructura `{ cliente_id: null, renglones: [] }` sin persistencia prematura en backend.
  - Selección de cliente con validación visual consultando `GET /api/clientes/{id}`.
  - Incorporación de libros desde el catálogo: verificación estricta de unicidad por renglón (RN-VEN-04 — prohibido duplicar el mismo `libro_id` en múltiples renglones).
  - Edición del borrador: modificación de cantidades (`cantidad >= 1`, entero positivo según RN-VEN-03) y eliminación de renglones individuales.
  - Cálculo local informativo de subtotales y total provisorio mientras se compone la venta.
  - Control de confirmación: exigencia de al menos un renglón (RN-VEN-02); deshabilitación inmediata del botón «Confirmar Venta» durante el vuelo de la petición HTTP para evitar dobles envíos (RN-VEN-07).
  - Petición HTTP: envío de `POST /api/ventas/` con `{ cliente_id, renglones: [{ libro_id, cantidad }, ...] }`.
  - Tratamiento de éxito `201 Created`: renderizado en pantalla de los precios unitarios, subtotales y total oficial devueltos por la API (RN-VEN-06), reseteo del borrador en memoria y refresco del historial.
  - Tratamiento de errores de negocio: ante `409 Conflict` (cliente o libro inexistente) o `422 Unprocessable Entity` (libro duplicado o datos inválidos), mostrar mensaje de error del servidor y PRESERVAR intacto el borrador en pantalla para su corrección (RN-VEN-08).
  - Verificación de casos de prueba G-04 (venta válida con 2 renglones) y G-06 (rechazos 409/422 y preservación del borrador).
- **Dependencias**: C-03, C-04, C-05
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-006 y §US-007
  - `knowledge-base/05_reglas_de_negocio.md` §Dominio: Ventas (RN-VEN-01 a RN-VEN-04, RN-VEN-06 a RN-VEN-08)
  - `knowledge-base/07_flujos_principales.md` §Flujo 1: Registro y Confirmación de una Venta
  - `knowledge-base/11_despliegue_y_casos_de_prueba.md` §Casos G-04 y G-06

---

### [C-07] `ventas-historial-detalle`
- **Estado**: `[ ]` pendiente
- **Scope**: Historial de ventas, detalle de transacciones y verificación de invariante de precio histórico (Ejercicio 3B / US-008):
  - Pantalla de historial en `frontend/public/index.html`: tabla de ventas paginada consumiendo `GET /api/ventas/?limit=20&offset=0`.
  - Controles de paginación para el historial (`limit`, `offset`).
  - Modal o vista de detalle de venta: llamada a `GET /api/ventas/{id}` renderizando id de venta, nombre del cliente, fecha y hora formateada, lista de renglones con precio unitario congelado, subtotales y total oficial.
  - Persistencia post-recarga: comprobación de que al recargar la página (`F5`), el historial conserva las operaciones y el modal de detalle reproduce exactamente los mismos importes devueltos por la API.
  - Verificación del invariante de precio histórico: flujo de prueba ejecutando `PATCH /api/libros/{id}` para alterar el precio de catálogo de un libro vendido, constatando que `GET /api/ventas/{id}` mantiene inalterado el `precio_unitario` y el subtotal original del renglón (RN-VEN-05).
  - Verificación del caso de prueba G-05 (invariante de precio histórico comprobado).
- **Dependencias**: C-06
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-008 — Historial y Detalle de Ventas
  - `knowledge-base/05_reglas_de_negocio.md` §RN-VEN-05 (Invariante de precio histórico)
  - `knowledge-base/07_flujos_principales.md` §Flujo 3: Demostración del Invariante de Precio Histórico
  - `knowledge-base/11_despliegue_y_casos_de_prueba.md` §Caso G-05

---

## FASE 4 — Ejercicio 4: Dockerfile del Frontend y Proxy Nginx

### [C-08] `docker-frontend-nginx`
- **Estado**: `[x]` completado
- **Scope**: Contenerización del frontend con Nginx alpine y orquestación con Docker Compose (Ejercicio 4):
  - Creación de `frontend/Dockerfile` basado en `nginx:1.26-alpine`: configuración de `ENV NGINX_ENVSUBST_FILTER=^API_UPSTREAM$`, copia de carpeta `public/` a `/usr/share/nginx/html/` y copia de plantilla `default.conf.template` a `/etc/nginx/templates/default.conf.template`.
  - Creación de `frontend/default.conf.template`: configuración de servidor Nginx en puerto 80, bloque `location /` con `try_files $uri $uri/ =404;` y proxy reverso en `location /api/` con directiva `proxy_pass http://${API_UPSTREAM}/;` (reescritura de prefijo con barra final).
  - Creación de `frontend/.dockerignore`: exclusión de `.git`, `**/.env*`, `**/node_modules`, `**/.DS_Store`.
  - Estandarización de `backend/Dockerfile` (`python:3.12-slim`, migraciones automáticas con `alembic upgrade head && exec uvicorn ...`) y `backend/.dockerignore`.
  - Creación de `docker-compose.yml` en la raíz del proyecto: servicios `db` (PostgreSQL 16), `backend` (FastAPI en puerto interno 8000) y `frontend` (Nginx expuesto en `127.0.0.1:8080:80` con `API_UPSTREAM=backend:8000`).
  - Pruebas locales de build y ejecución del contenedor frontend comprobando el reenvío transparente de peticiones `/api/` hacia el backend.
- **Dependencias**: C-01
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/08_arquitectura_propuesta.md` §Reverse Proxy / API Gateway y §Configuración y Variables de Entorno
  - `consignas_global_evaluacion_y_despliegue.md` §Ejercicio 4: Dockerfile del Frontend y Proxy Nginx
  - `knowledge-base/11_despliegue_y_casos_de_prueba.md` §Caso G-07

---

## FASE 5 — Ejercicio 5: Servicios en Easypanel y Verificación G-01 a G-07

### [C-09] `easypanel-deploy-verification`
- **Estado**: `[ ]` pendiente
- **Scope**: Despliegue en VPS con Easypanel, documentación operativa y verificación de casos G-01 a G-07 (Ejercicio 5):
  - Configuración del servicio `backend` en Easypanel: tipo App, build path `/backend`, builder Dockerfile, variable `DATABASE_URL` conectada a PostgreSQL, puerto interno 8000 aislado en red privada.
  - Configuración del servicio `frontend` en Easypanel: tipo App, build path `/frontend`, builder Dockerfile, variable `API_UPSTREAM=<backend_service_name>:8000`, dominio público con HTTPS forzado apuntando al puerto 80.
  - Creación del archivo `DEPLOY.md` en la raíz del proyecto: registro de URL pública HTTPS, commit hash desplegado, mapeo de rutas de build, puertos, variables de upstream y pasos de contingencia.
  - Ejecución integral y auditoría de los 7 casos de prueba sobre la URL pública definitiva:
    - **G-01**: Búsqueda por título, paginación con `limit`/`offset`, búsqueda vacía y detalle de autores.
    - **G-02**: Alta de libro con autorías y confirmación de error `409 Conflict` por ISBN duplicado.
    - **G-03**: Alta de cliente, verificación de error `409 Conflict` por email duplicado y consulta por ID.
    - **G-04**: Registro de venta válida con dos renglones, cálculo oficial y persistencia tras recargar página.
    - **G-05**: Invariante de precio histórico comprobado tras modificación con `PATCH /api/libros/{id}`.
    - **G-06**: Rechazo de venta con libros duplicados (`422`) o cliente inexistente (`409`) y preservación del borrador.
    - **G-07**: Verificación de compilación limpia de imágenes, HTTPS operativo, `/api/health/ready` en 200 y persistencia de datos tras reinicio de contenedores.
  - Generación de la carpeta `evidencia/` conteniendo capturas de pantalla de DevTools (Network/Console) y bitácora Markdown de cada caso de prueba.
  - Elaboración de `README.md` final del monorepo con datos de integrantes, guía para levantar localmente y checklist de entrega.
- **Dependencias**: C-07, C-08
- **Governance**: CRITICO
- **Leer antes**:
  - `consignas_global_evaluacion_y_despliegue.md` §Ejercicio 5: Servicios en Easypanel y §4. Casos de Prueba (G-01 a G-07)
  - `knowledge-base/11_despliegue_y_casos_de_prueba.md` §Protocolo de Ejecución de Pruebas en URL Pública
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura de Directorios del Proyecto Unificado
  - `knowledge-base/09_decisiones_y_supuestos.md` §Decisiones de Arquitectura
