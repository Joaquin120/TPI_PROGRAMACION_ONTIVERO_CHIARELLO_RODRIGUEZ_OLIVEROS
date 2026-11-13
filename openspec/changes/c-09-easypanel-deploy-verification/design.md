# Design: C-09 Despliegue en Easypanel y Verificación G-01 a G-07

## Context

Véase `proposal.md` para la motivación y alcance. Al cierre de `C-08`, el proyecto ya dispone de:
- `docker-compose.yml` con servicios `db` (`postgres:16-alpine`), `backend` (puerto interno `8000`) y `frontend` (`127.0.0.1:8080:80`).
- `frontend/Dockerfile` (`nginx:1.26-alpine`, `NGINX_ENVSUBST_FILTER=^API_UPSTREAM$`) y `frontend/default.conf.template` con `proxy_pass http://${API_UPSTREAM}/;`.
- `backend/Dockerfile` (`python:3.12-slim`) con `CMD alembic upgrade head && exec uvicorn src.main:app --host 0.0.0.0 --port 8000`.
- Endpoints `GET /editoriales/`, `GET /generos/`, `GET /autores/` solo de lectura (`src/api/v1/endpoints/`), sin endpoints `POST` para tablas maestras ni módulo `seed` implementado para el esquema unificado (`backend/src/db/` solo tiene modelos; `backend/parcial/seed.py` corresponde al esquema legado del Parcial 2).

Adicionalmente, en la terminal local actual de Windows no está instalado el binario `docker`, por lo que la compilación/prueba local de contenedores y el despliegue efectivo sobre Easypanel deben quedar limpiamente desacoplados de la preparación del código y plantillas verificables por suite unitaria.

## Goals / Non-Goals

**Goals:**
- Garantizar que toda instancia nueva de PostgreSQL (local o Easypanel) arranque con las tablas migradas y datos maestros/transaccionales mínimos listos para operar `G-01` a `G-07` sin intervención manual obligatoria por SSH.
- Preservar íntegramente los datos modificados por el usuario (incluyendo cambios de precio de `G-05`) tras reinicios o redespliegues del backend (`G-07`).
- Estandarizar `README.md`, `DEPLOY.md` y la estructura de `evidencia/` conforme a `docs/consignas_global_evaluacion_y_despliegue.md` §5 y `knowledge-base/11_despliegue_y_casos_de_prueba.md`.
- Verificar que el paquete final `.zip` cumpla estrictamente con la Regla Dura #4 de `AGENTS.md` (cero `.env`, secretos, `__pycache__`, `.pytest_cache`, `.venv`, `node_modules`).

**Non-Goals:**
- Modificar lógica funcional de catálogo, clientes o ventas ya cerrada y aprobada en `C-03` a `C-07`.
- Alterar `frontend/default.conf.template` o el contrato de proxy reverse establecido en `C-08`, salvo que el entorno real de Easypanel evidencie un fallo concreto durante la verificación.
- Inventar o pre-llenar URLs públicas de Easypanel, hashes de commit o capturas ficticias en `DEPLOY.md` o `evidencia/` antes del despliegue real.

## Decisions

### 1. Módulo `backend/src/db/seed.py` idempotente basado en claves naturales (sin sobrescritura)
- **Decisión**: Implementar `backend/src/db/seed.py` operando sobre los modelos reales (`Editorial`, `Genero`, `Autor`, `Libro`, `LibroAutor`, `Cliente`) mediante búsqueda previa por clave natural (`Editorial.nombre`, `Genero.nombre`, `Autor.nombre`, `Libro.isbn`, `Cliente.email`) y creación solo cuando el registro no existe.
- **Alternativas consideradas**:
  - *Migración Alembic de datos (`004_seed_data.py`)*: acoplaría los datos de muestra al historial de esquema DDL y complicaría `downgrade`/tests de migración existentes (`test_migrations.py`).
  - *UPSERT que actualiza precio/stock en cada arranque*: rompería la verificación `G-05` + `G-07`, porque al reiniciar el contenedor revertiría el nuevo precio `Q` configurado mediante `PATCH /api/libros/{id}`.
- **Justificación**: La inserción condicional por clave natural es 100% idempotente, no pisa cambios posteriores en catálogo y permite ejecutarse tanto vía CLI (`python -m src.db.seed`) como automáticamente tras `alembic upgrade head` en `backend/Dockerfile`:
  `CMD alembic upgrade head && python -m src.db.seed && exec uvicorn src.main:app --host 0.0.0.0 --port 8000`.
- **Datos iniciales mínimos**: Al menos 3 editoriales, 3 géneros, 3 autores, 3 libros con stock suficiente (`>= 10`) y relaciones `libros_autores` (`rol="autor"`, `orden=1`), y 1 cliente inicial de prueba.

### 2. Pruebas unitarias aisladas para `seed.py`
- **Decisión**: Agregar `backend/tests/unit/test_seed.py` usando sesión asíncrona mockeada/fake (consistente con `tests/unit/` y `tests/integration/test_ventas_api.py`) para verificar: (a) creación completa en BD vacía respetando mínimos (`>=3` editoriales/géneros/autores/libros y `>=1` cliente), y (b) segunda ejecución idempotente sin duplicados ni modificación de precios existentes.

### 3. Separación clara entre preparación en repositorio y evidencia real de Easypanel
- **Decisión**: Dividir la ejecución de `C-09` en dos bloques dentro de `tasks.md`:
  1. **Preparación verificable en repo**: `src/db/seed.py`, `backend/Dockerfile`, `test_seed.py`, `README.md`, estructura base de `DEPLOY.md` y bitácora guía en `evidencia/`, junto con la verificación por suites unitarias/integración.
  2. **Despliegue efectivo en Easypanel y auditoría `G-01`–`G-07`**: configuración real y compilación de ambos servicios en Easypanel (`/backend` privado + `/frontend` HTTPS), captura de URL pública y commit real en `DEPLOY.md`, ejecución en vivo de `G-01` a `G-07` con capturas DevTools / salidas reales en `evidencia/`, y empaquetado final `.zip` auditado.

### 4. Estructura de `DEPLOY.md`, `README.md` y `evidencia/`
- **`README.md`**: Presentación del sistema, integrantes del grupo (`Ontivero`, `Chiarello`, `Rodriguez`, `Oliveros`), arquitectura de servicios, requisitos, guía de arranque con `docker compose up --build` y en local, comando de seed (`python -m src.db.seed`) y checklist de entrega.
- **`DEPLOY.md`**: Sección de entorno productivo en Easypanel (URL pública HTTPS, hash de commit desplegado, servicio `backend` con build path `/backend`, puerto `8000` privado y `DATABASE_URL`; servicio `frontend` con build path `/frontend`, puerto `80` HTTPS y `API_UPSTREAM=<backend_service>:8000`), flujo automático de migraciones + seed, diagnóstico rápido y procedimiento de actualización/rollback.
- **`evidencia/`**: Bitácora Markdown por cada caso (`G-01` a `G-07`) enlazando capturas reales de navegador (DevTools Network/Console) y salidas de `curl`/`health/ready`/logs de Easypanel.

## Risks / Trade-offs

- **[Arranque paralelo en Easypanel entre PostgreSQL y Backend]** → Si PostgreSQL tarda más que el inicio de `backend`, `alembic upgrade head` puede fallar en el primer intento; se mitiga documentando el orden de creación en Easypanel (`PostgreSQL` previo + política de reinicio automático) y validando en logs al desplegar.
- **[Validación de compilación Docker y despliegue real diferida a Easypanel]** → Dado que no se requiere Docker Desktop local en Windows para cumplir el Ejercicio 5 y que Easypanel construye `/backend` y `/frontend` en el VPS, la verificación de los `Dockerfile` en runtime y las capturas de `G-01`–`G-07` sobre HTTPS público quedan como gate operativo previo al archivo de `C-09`, evitando fabricar evidencias o URLs ficticias.
- **[Exposición accidental de `.env` o cachés locales en el `.zip` de entrega]** → Se incluye una tarea explícita de auditoría de exclusiones (`.env`, `.venv`, `__pycache__`, `.pytest_cache`, `node_modules`) antes de comprimir el entregable.

## Open Questions

- Confirmar la URL pública HTTPS asignada en Easypanel y el nombre interno del servicio backend para `API_UPSTREAM` (ej. `<proyecto>_backend:8000`) al momento de desplegar en infraestructura real.
