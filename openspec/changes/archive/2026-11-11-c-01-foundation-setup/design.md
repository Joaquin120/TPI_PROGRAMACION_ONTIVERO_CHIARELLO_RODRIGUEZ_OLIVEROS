# Design: C-01 Foundation Setup

## Context
Ver `proposal.md` para la motivación. Actualmente existen en el espacio de trabajo dos carpetas clonadas con sus propios historiales de Git:
1. `REHACER_CHIARELLO_ONTIVEROS_OLIVEROS_RODRIGUEZ_PARCIAL_FRONTEND/` (código web, CSS, JS del Parcial 1).
2. `PARCIAL_2_PROGRAMACION_CHIARELLO_ONTIVERO_RODRIGUEZ_OLIVEROS_COM3/` (código FastAPI, Alembic, tests del Parcial 2).

Para construir el TPI unificado, se requiere reubicar el código en `frontend/public/` y `backend/` dentro de la raíz del monorepo, despojándolos de sus `.git` internos para versionar todo limpiamente en el repositorio del TPI.

## Goals / Non-Goals

**Goals:**
- Establecer la estructura de carpetas canónica del monorepo (`frontend/`, `backend/`, `docs/`, `knowledge-base/`).
- Copiar y organizar los archivos estáticos en `frontend/public/`.
- Copiar el código del backend a `backend/` preservando `src/`, `alembic/`, `requirements.txt` y configuración.
- Asegurar que `.gitignore` contemple todas las exclusiones críticas (archivos `.env`, `__pycache__`, `.venv`, `.pytest_cache`).
- Garantizar que el backend levante y responda a `/health/ready` de forma consistente.
- Dejar el árbol de trabajo limpio para realizar el commit inicial fundacional del TPI.

**Non-Goals:**
- Implementar el cliente `fetch` en `api.js` o modificar la lógica de UI del catálogo (corresponde a `C-02` y `C-03`).
- Crear los contenedores Docker o el proxy Nginx en este change (corresponde a `C-08`).
- Modificar o eliminar endpoints de negocio existentes.

## Decisions

### D1: Estructura Monorepo con `frontend/public/`
- **Decisión**: Los archivos del Parcial 1 (`index.html`, `css/`, `js/`) se moverán a `frontend/public/`.
- **Razón**: El Ejercicio 4 y el Dockerfile estándar de Nginx copian expresamente `public/` a `/usr/share/nginx/html/`. Separar `public/` dentro de `frontend/` permite alojar en `frontend/` los archivos `Dockerfile`, `.dockerignore` y `default.conf.template` sin mezclarlos con los estáticos web.
- **Alternativas**: Dejar los archivos en la raíz de `frontend/`. Descartado porque rompe la plantilla del Dockerfile de la consigna.

### D2: Eliminación de `.git` internos de los parciales
- **Decisión**: Se eliminarán los directorios `.git` y configuraciones locales de los repositorios clonados antes de añadirlos al control de versiones del TPI.
- **Razón**: Git interpreta carpetas con `.git` interno como submódulos o punteros corruptos, impidiendo commitear el código fuente real al repositorio del TPI.
- **Alternativas**: Git submodules. Descartado porque la entrega exige un único repositorio monorepo con un archivo `.zip` consolidado.

### D3: Mantenimiento de `src/` en el backend
- **Decisión**: Se conservará la carpeta `src/` para el código de FastAPI (`src/main.py`, `src/api/`, etc.) y se configurará `PYTHONPATH=.` o imports relativos para compatibilidad con Uvicorn.
- **Razón**: Todo el código probado del Parcial 2 ya utiliza imports basados en `src.*`.

## Risks / Trade-offs

- **[Riesgo] Pérdida accidental de archivos al mover directorios** → **Mitigación**: Usar `rsync` o copia estructurada verificando el árbol de archivos antes de borrar las carpetas viejas.
- **[Riesgo] Conexión a base de datos ausente en pruebas de salud locales** → **Mitigación**: El endpoint `/health/ready` debe manejar excepciones de conexión para devolver un error estructurado si la base PostgreSQL no está encendida en ese momento.
