# Proposal: C-09 Despliegue en Easypanel y Verificación G-01 a G-07

## Why

Con `C-01` a `C-08` completados, la aplicación está implementada y contenerizada, pero aún carece de un mecanismo idempotente de carga inicial de datos compatible con el esquema unificado (`backend/src/db/`), documentación operativa y de entrega (`README.md`, `DEPLOY.md`) y la verificación end-to-end de los casos `G-01` a `G-07` sobre la URL pública HTTPS en Easypanel. Cerrar `C-09` completa la Fase 5 del roadmap y habilita la entrega final del monorepo según la consigna global.

## What Changes

- **Carga inicial reproducible de datos (`seed`)**: Implementar el script idempotente `backend/src/db/seed.py` (ejecutable por CLI como `python -m src.db.seed` y al arranque tras `alembic upgrade head`) para garantizar al menos 3 editoriales, 3 géneros, 3 autores, 3 libros con stock suficiente y 1 cliente inicial sin sobrescribir datos ni precios modificados posteriormente (`G-05`, `G-07`), junto con pruebas automatizadas en `backend/tests/unit/test_seed.py`.
- **Documentación final del monorepo (`README.md`)**: Crear `README.md` en la raíz con identificación de los integrantes, guía paso a paso para levantar el proyecto localmente con Docker Compose / entorno local, instrucciones de carga de datos iniciales y checklist de entrega.
- **Documentación y configuración de despliegue en Easypanel (`DEPLOY.md`)**: Registrar la configuración de los servicios `backend` (build path `/backend`, Dockerfile, `DATABASE_URL`, puerto privado `8000`) y `frontend` (build path `/frontend`, Dockerfile, `API_UPSTREAM`, dominio HTTPS público en puerto `80`), junto con URL pública definitiva, hash de commit desplegado, mapeo de puertos/variables, migraciones y pasos de actualización y contingencia.
- **Verificación integral y evidencias `G-01` a `G-07` (`evidencia/`)**: Ejecutar y auditar los 7 casos de prueba (`G-01` a `G-07`) sobre el entorno contenerizado y la URL pública HTTPS definitiva, documentando bitácoras Markdown y capturas de DevTools / salidas de terminal en `evidencia/`.
- **Auditoría de higiene y entrega (`.zip`)**: Verificar que los artefactos de entrega respeten estrictamente la exclusión de `.env`, contraseñas reales, `.venv`, `node_modules`, `__pycache__` y `.pytest_cache`.

## Capabilities

### New Capabilities
- `easypanel-deployment-verification`: Orquestación operativa en Easypanel (servicios `backend` privado y `frontend` público con HTTPS), documentación de despliegue y uso (`DEPLOY.md`, `README.md`), auditoría E2E de los casos `G-01` a `G-07` con trazabilidad en `evidencia/`, e higiene del paquete de entrega `.zip`.

### Modified Capabilities
- `backend-core-health`: Se extiende el requisito `Carga de Datos Mínimos Iniciales (Seed Data)` para especificar la ejecución reproducible e idempotente mediante `python -m src.db.seed` (y al iniciar el contenedor backend luego de `alembic upgrade head`) garantizando que no se sobrescriban precios, stocks ni registros ya existentes tras reinicios o cambios de catálogo.

## Impact

- **Backend / Contenedor**: `backend/src/db/seed.py` (nuevo), `backend/tests/unit/test_seed.py` (nuevo), `backend/Dockerfile` (actualización de arranque para ejecutar seed idempotente tras `alembic upgrade head`).
- **Documentación raíz y evidencias**: `README.md` (nuevo), `DEPLOY.md` (nuevo), `evidencia/` (nuevos archivos Markdown y capturas para `G-01`..`G-07`).
- **Especificaciones**: nuevo spec `openspec/specs/easypanel-deployment-verification/spec.md` y actualización de `openspec/specs/backend-core-health/spec.md`.
- **Dependencias operativas**: la compilación local de imágenes requiere Docker/Docker Compose (no instalado actualmente en esta terminal Windows) y la verificación sobre la URL pública requiere el despliegue activo en Easypanel y los datos reales del entorno (URL HTTPS pública, nombre del servicio backend e información completa de integrantes para el `README.md`).
