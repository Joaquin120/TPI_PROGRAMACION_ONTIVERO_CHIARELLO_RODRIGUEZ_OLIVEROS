# Tasks: C-09 Despliegue en Easypanel y Verificación G-01 a G-07

## 1. Carga Inicial de Datos (Seed Idempotente) y Arranque Backend

- [x] 1.1 Implementar `backend/src/db/seed.py` con carga idempotente por clave natural (`>= 3` editoriales, `>= 3` géneros, `>= 3` autores, `>= 3` libros con stock `>= 10` y relaciones `libros_autores`, y `>= 1` cliente inicial) preservando registros y precios ya existentes, y crear `backend/tests/unit/test_seed.py`; verificar ejecutando `python -m pytest -p no:cacheprovider tests/unit/test_seed.py -v` con `0` fallos.
- [x] 1.2 Actualizar `backend/Dockerfile` para ejecutar `python -m src.db.seed` automáticamente después de `alembic upgrade head` y antes de `exec uvicorn src.main:app --host 0.0.0.0 --port 8000`; verificar ejecutando las suites completas `python -m pytest -p no:cacheprovider tests -v` (en `backend/`) y `node --test frontend/public/js/*.test.js` con `0` fallos.

## 2. Documentación Operativa y Estructura de Evidencias

- [x] 2.1 Crear `README.md` en la raíz del proyecto con identificación de integrantes (`Ontivero`, `Chiarello`, `Rodriguez`, `Oliveros`), guía para levantar el sistema localmente con Docker Compose y entorno local, instrucciones de carga de datos iniciales (`python -m src.db.seed`) y checklist de entrega; verificar cobertura completa frente a `docs/consignas_global_evaluacion_y_despliegue.md` §5.
- [x] 2.2 Crear `DEPLOY.md` en la raíz documentando la arquitectura de servicios en Easypanel (`/backend` privado en puerto `8000` con `DATABASE_URL` y `/frontend` público HTTPS en puerto `80` con `API_UPSTREAM=<backend_service_name>:8000`), flujo de migraciones/seed, tabla de diagnóstico rápido, y pasos de actualización y contingencia (dejando identificados los campos de URL pública HTTPS real, `API_UPSTREAM` final y commit hash para completar tras desplegar); verificar coherencia de variables y puertos contra `.env.example`, `docker-compose.yml` y `frontend/default.conf.template`.
- [x] 2.3 Crear la estructura base de `evidencia/` (`README.md` / bitácoras para `G-01` a `G-07`) siguiendo los procedimientos, resultados esperados y evidencias requeridas en `knowledge-base/11_despliegue_y_casos_de_prueba.md`; verificar que estén incluidos los 7 casos `G-01` a `G-07`.

## 3. Despliegue en Easypanel y Auditoría G-01 a G-07

- [ ] 3.1 Configurar y desplegar los servicios `backend` (build path `/backend`, builder Dockerfile, `DATABASE_URL`, red privada puerto `8000`) y `frontend` (build path `/frontend`, builder Dockerfile, `API_UPSTREAM=<nombre_servicio_backend>:8000`, dominio público HTTPS al puerto `80`) en Easypanel; verificar en logs de Easypanel la compilación limpia de ambas imágenes y la ejecución de `alembic upgrade head` + `python -m src.db.seed`, registrar la URL pública HTTPS definitiva y el hash de commit real en `DEPLOY.md`, y comprobar HTTP `200` en `https://<dominio>/api/health/ready`.
- [ ] 3.2 Ejecutar end-to-end los casos de prueba `G-01` a `G-07` sobre la URL pública definitiva HTTPS (incluyendo `PATCH /api/libros/{id}` en `G-05` y reinicio/redespliegue en Easypanel verificando persistencia en `G-07`), guardando capturas reales de DevTools (`Network`/`Console`), salidas de terminal/logs de Easypanel y resultados verificados en `evidencia/`.

## 4. Auditoría Final de Higiene y Empaquetado (.zip)

- [ ] 4.1 Auditar la estructura entregable y generar/verificar el paquete `.zip` final comprobando la inclusión de `frontend/`, `backend/`, `README.md`, `DEPLOY.md` y `evidencia/`, la ausencia estricta de `.env`, contraseñas reales, `node_modules/`, `.venv/`, `__pycache__/` y `.pytest_cache/`, y validar `openspec validate "c-09-easypanel-deploy-verification" --strict --json` (`passed: 1, failed: 0`).

## Workflow follow-up

- Sincronizar los delta specs (`backend-core-health` y `easypanel-deployment-verification`) hacia `openspec/specs/` mediante `/opsx-sync`.
- Archivar el change mediante `/opsx-archive c-09-easypanel-deploy-verification`, marcar `[x]` únicamente `C-09` en `CHANGES.md` y realizar el commit final / merge a `main` cuando el usuario lo indique.
