# Proposal: C-01 Foundation Setup

## Why
El Trabajo Práctico Integrador requiere unificar los desarrollos previos del Parcial 1 (Frontend en JS nativo) y Parcial 2 (Backend en FastAPI + PostgreSQL) bajo una arquitectura monorepo contenerizada. Actualmente, los componentes se encuentran en carpetas de repositorio anidadas con historiales desvinculados, lo que impide un versionado unificado, una ejecución local estándar y el despliegue coordinado en Easypanel. Establecer la estructura monorepo, los contratos de entorno y la verificación del backend con base de datos es el cimiento indispensable antes de encarar cualquier cambio de integración HTTP o de interfaz.

## What Changes
- **Unificación de directorios en Monorepo**: Organización de la raíz en carpetas de primer nivel `frontend/` (con `public/` para recursos web del Parcial 1), `backend/` (código fuente FastAPI, Alembic, tests del Parcial 2) y `docs/` con las consignas oficiales.
- **Configuración de Entorno e Higiene Git**: Creación de plantillas `.env.example` en la raíz y en `backend/` con variables estandarizadas (`DATABASE_URL`, `API_UPSTREAM`, `ENVIRONMENT`). Configuración de `.gitignore` global para prohibir estrictamente credenciales reales, `.venv`, `__pycache__` y dependencias temporales.
- **Scaffolding y Verificación del Backend**: Consolidación de `backend/src/main.py` asegurando la inicialización del router con el endpoint de diagnóstico `/api/health/ready` (o `/health/ready` reescrito por proxy) retornando HTTP 200 y comprobación de conectividad a PostgreSQL.
- **Modelos y Migraciones Alembic**: Verificación de los esquemas relacionales de base de datos (`editoriales`, `generos`, `autores`, `libros`, `libros_autores`, `clientes`, `ventas`, `ventas_renglones`) con soporte asíncrono (`asyncpg`).
- **Seed Inicial de Datos**: Inicialización de script de carga de datos mínimos indispensables (al menos 3 editoriales, 3 géneros, 3 autores, 3 libros con stock y 1 cliente) para habilitar las pruebas locales de los ejercicios posteriores.

## Capabilities

### New Capabilities
- `monorepo-foundation`: Estructura unificada del proyecto monorepo (`frontend/`, `backend/`, `docs/`), higiene de repositorios Git anidados y gestión de variables de entorno mediante `.env.example`.
- `backend-core-health`: Aplicación base de FastAPI, modelos SQLAlchemy con migraciones Alembic, seed inicial de datos y endpoint de verificación de salud y conectividad a base de datos en `/health/ready`.

### Modified Capabilities
*(Ninguna; este es el change fundacional inicial)*

## Impact
- **Estructura de archivos**: Reorganiza las carpetas existentes `PARCIAL_2_...` y `REHACER_...` en `backend/` y `frontend/`, eliminando sus `.git` internos para versionar todo en el repositorio raíz del TPI.
- **APIs**: Expone y verifica `/health/ready` para el posterior proxy Nginx y chequeo en Easypanel.
- **Dependencias**: Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, asyncpg, psycopg2-binary/asyncpg, pytest.
