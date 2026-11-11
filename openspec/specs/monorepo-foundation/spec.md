# monorepo-foundation Specification

## Purpose
Establece la estructura canónica monorepo del proyecto separando frontend, backend y documentación, garantizando la higiene del repositorio y la configuración estandarizada de variables de entorno sin credenciales reales.

## Requirements

### Requirement: Estructura Monorepo Canónica
El repositorio SHALL estructurarse con carpetas de primer nivel `frontend/` (con subdirectorio `public/` para estáticos web) y `backend/` (con código fuente de la API FastAPI y migraciones Alembic), desvinculadas de cualquier repositorio Git anidado.

#### Scenario: Organización de directorios en el repositorio raíz
- **WHEN** un desarrollador clona o inspecciona el proyecto
- **THEN** encuentra exclusivamente las carpetas `frontend/` y `backend/` como componentes del monorepo, sin subcarpetas `.git` internas.

### Requirement: Configuración de Variables de Entorno Seguras
El proyecto SHALL proveer plantillas `.env.example` en la raíz y en `backend/` con las claves requeridas para la conexión a la base de datos y upstream de Nginx, prohibiendo el rastreo de archivos `.env` reales en el control de versiones.

#### Scenario: Presencia de plantillas de entorno sin credenciales
- **WHEN** se revisan los archivos de configuración del repositorio
- **THEN** existe `.env.example` documentando `DATABASE_URL`, `API_UPSTREAM` y `ENVIRONMENT`, y el archivo `.gitignore` ignora cualquier archivo `.env`.
