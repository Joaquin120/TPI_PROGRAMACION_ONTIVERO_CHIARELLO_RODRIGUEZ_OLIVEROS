# Tasks: C-01 Foundation Setup

## 1. Scaffolding Monorepo y Limpieza de Git

- [x] 1.1 Crear directorio `frontend/public/` y migrar los archivos de `REHACER_CHIARELLO_ONTIVEROS_OLIVEROS_RODRIGUEZ_PARCIAL_FRONTEND` (`index.html`, `css/`, `js/`), verificando que los archivos queden correctamente ubicados.
- [x] 1.2 Crear directorio `backend/` y migrar los componentes de `PARCIAL_2_PROGRAMACION_CHIARELLO_ONTIVERO_RODRIGUEZ_OLIVEROS_COM3` (`src/`, `alembic/`, `requirements.txt`, `pyproject.toml`, `alembic.ini`), verificando la presencia completa del código sin `.git` anidados.
- [x] 1.3 Eliminar las carpetas temporales de los parciales 1 y 2 una vez constatada la integridad de los directorios `frontend/` y `backend/`.
- [x] 1.4 Configurar el archivo `.gitignore` en la raíz asegurando la exclusión estricta de archivos `.env`, `.venv`, `__pycache__`, `.pytest_cache` y `node_modules`.

## 2. Configuración de Entornos y Plantillas

- [x] 2.1 Crear plantillas `.env.example` en la raíz y en `backend/` con las variables canónicas `DATABASE_URL`, `API_UPSTREAM` y `ENVIRONMENT`.
- [x] 2.2 Revisar y validar que `backend/alembic.ini` y la configuración en `backend/src/` carguen la variable `DATABASE_URL` dinámicamente desde el entorno.

## 3. Verificación de Backend y Modelos

- [x] 3.1 Verificar que `backend/src/main.py` exponga el endpoint de diagnóstico `/health/ready` (o `/api/health/ready`) respondiendo con código HTTP 200 y JSON `{"status": "ok"}`.
- [x] 3.2 Constatar que los modelos SQLAlchemy y las migraciones de Alembic en `backend/alembic/` cubran las tablas de catálogo, clientes y ventas con sus restricciones.
- [x] 3.3 Verificar la existencia del script o migración de seed de datos para poblar editoriales, géneros, autores y libros iniciales.

## 4. Consolidación y Verificación de Control de Versiones

- [x] 4.1 Comprobar el estado del árbol de trabajo con `git status` constatando que no existan submódulos corruptos ni rastros de carpetas anidadas.
- [x] 4.2 Preparar el área de staging (`git add`) para el commit fundacional del monorepo del TPI.

## Workflow follow-up

- Ejecutar `/opsx:apply c-01-foundation-setup` para implementar las tareas planificadas.
- Una vez completadas y verificadas las tareas, archivar el change con `/opsx:archive c-01-foundation-setup`.
- Marcar `[x]` en `CHANGES.md`.
