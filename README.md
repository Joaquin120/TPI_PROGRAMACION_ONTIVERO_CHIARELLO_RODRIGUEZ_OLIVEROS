# Librería Web — Integración y Despliegue (TPI Programación III)

Aplicación web full-stack para la gestión de catálogo de libros, alta de clientes, registro de ventas transaccionales con invariante de precio histórico y consulta de historial, desplegada en contenedores Docker (Nginx + FastAPI + PostgreSQL).

## Integrantes

- **Santiago Ontivero**
- **Joaquín Chiarello**
- **Cristian Rodriguez**
- **Joseph Oliveros**

Universidad Tecnológica Nacional (UTN) — Tecnicatura Universitaria en Programación — Programación III (Comisión 3).

---

## Arquitectura del Monorepo

```text
TPI_PROGRAMACION_ONTIVERO_CHIARELLO_RODRIGUEZ_OLIVEROS/
├── frontend/                  # Nginx 1.26-alpine + SPA nativa (HTML5, CSS3, JS ES6+ Modules)
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── default.conf.template  # Reverse proxy /api/ -> http://${API_UPSTREAM}/
│   └── public/
├── backend/                   # API REST FastAPI + SQLAlchemy Async + Alembic + PostgreSQL
│   ├── Dockerfile             # Arranque: alembic upgrade head && python -m src.db.seed && uvicorn
│   ├── .dockerignore
│   ├── requirements.txt
│   ├── alembic/
│   └── src/
├── docker-compose.yml         # Orquestación local (db, backend, frontend)
├── .env.example               # Plantilla de variables sin credenciales reales
├── DEPLOY.md                  # Configuración y trazabilidad del despliegue en Easypanel
└── evidencia/                 # Bitácora y capturas de verificación G-01 a G-07
```

---

## Cómo Levantar el Proyecto Localmente

### Opción 1: Con Docker Compose (stack completo)

1. Crear el archivo de variables de entorno a partir de la plantilla (sin commitear `.env`):
   ```bash
   cp .env.example .env
   ```
2. Construir y levantar los tres servicios (`db`, `backend` y `frontend`):
   ```bash
   docker compose up --build -d
   ```
   Al iniciar el contenedor `backend`, se ejecutan automáticamente las migraciones (`alembic upgrade head`) y la carga inicial idempotente (`python -m src.db.seed`).
3. Verificar que el servicio responda correctamente:
   - **Frontend SPA**: `http://127.0.0.1:8080`
   - **Healthcheck a través de Nginx**: `GET http://127.0.0.1:8080/api/health/ready` → HTTP `200` (`{"status":"ready","database":"connected"}`)

Para detener el entorno conservando los datos en PostgreSQL:
```bash
docker compose down
```

### Opción 2: Desarrollo local sin Docker (Backend + Frontend + Tests)

1. **Base de datos**: contar con una instancia de PostgreSQL 15/16 accesible y configurar `backend/.env` tomando como base `backend/.env.example`.
2. **Backend**:
   ```bash
   cd backend
   python -m venv .venv
   # Windows: .venv\Scripts\activate  |  Linux/macOS: source .venv/bin/activate
   pip install -r requirements.txt
   alembic upgrade head
   python -m src.db.seed
   uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   ```
3. **Tests automatizados** (no requieren PostgreSQL activo; usan sesiones aisladas en memoria):
   ```bash
   # Desde backend/
   python -m pytest -p no:cacheprovider tests -v

   # Desde la raíz del monorepo (Node.js >= 20)
   node --test frontend/public/js/*.test.js
   ```

---

## Cómo Cargar Datos Iniciales (Seed)

El proyecto incluye el script idempotente `backend/src/db/seed.py`, que puebla la base de datos con registros iniciales mínimos sin duplicar filas ni sobrescribir precios o stocks modificados posteriormente:

- **Editoriales (3)**: *Sudamericana*, *Planeta*, *Alianza*.
- **Géneros (3)**: *Ficción*, *Ciencia Ficción*, *Ensayo*.
- **Autores (3)**: *Gabriel García Márquez*, *Jorge Luis Borges*, *Julio Cortázar*.
- **Libros (3)** con stock inicial (`>= 12`) y su autoría vinculada en `libros_autores`: *Cien años de soledad*, *Ficciones*, *Rayuela*.
- **Cliente inicial (1)**: *Lucía Fernández* (`lucia.fernandez@ejemplo.com`).

Ejecución manual desde `backend/`:
```bash
python -m src.db.seed
```

En entornos contenerizados (`backend/Dockerfile`), este comando corre automáticamente inmediatamente después de `alembic upgrade head` en cada arranque del contenedor.

---

## Checklist de Entrega

- [x] `frontend/` con código web nativo en `public/`, `Dockerfile`, `.dockerignore` y `default.conf.template`.
- [x] `backend/` con API FastAPI, `Dockerfile`, `.dockerignore`, `requirements.txt`, migraciones Alembic (`alembic/`) y carga inicial (`src/db/seed.py`).
- [x] `README.md` con identificación de integrantes, guía de ejecución local y carga de datos iniciales.
- [x] `DEPLOY.md` completado con la URL pública HTTPS definitiva y el hash de commit desplegado en Easypanel.
- [x] `evidencia/` completada con bitácoras y capturas reales de los casos `G-01` a `G-07` sobre la URL pública.
- [x] Empaquetado `.zip` final libre de archivos `.env`, credenciales reales, `node_modules/`, `.venv/`, `__pycache__/` y `.pytest_cache/`.
