# Local Container Orchestration Specification

## Purpose
Orquestar localmente los servicios de base de datos PostgreSQL, backend FastAPI y frontend Nginx mediante contenedores Docker y Docker Compose para garantizar reproducibilidad y conectividad en red aislada.

## Requirements

### Requirement: Orquestación multi-contenedor para desarrollo local
El proyecto SHALL proveer una configuración de Docker Compose que defina los servicios interconectados `db` (PostgreSQL), `backend` (FastAPI) y `frontend` (Nginx) sobre una red común con persistencia de datos.

#### Scenario: Despliegue sincronizado del stack completo
- **WHEN** se ejecuta el comando `docker compose up` con las variables requeridas
- **THEN** los tres servicios se levantan en red interna y el frontend queda accesible en `127.0.0.1:8080:80`

#### Scenario: Conectividad interna entre frontend y backend
- **WHEN** el contenedor frontend envía tráfico de proxy hacia `http://${API_UPSTREAM}`
- **THEN** la red interna resuelve el host `backend` y entrega las peticiones al puerto 8000 sin exposición pública del backend

### Requirement: Migración y arranque automatizado del backend
La imagen estandarizada del backend SHALL ejecutar automáticamente las migraciones pendientes de la base de datos antes de transferir el control al servidor de aplicaciones Uvicorn.

#### Scenario: Inicialización con base de datos configurada
- **WHEN** el contenedor backend arranca con conectividad a PostgreSQL establecida
- **THEN** se ejecuta `alembic upgrade head` exitosamente y de inmediato inicia el proceso de Uvicorn en `0.0.0.0:8000`

### Requirement: Aislamiento e higiene de contexto Docker
Las definiciones de Docker para frontend y backend SHALL mantener archivos `.dockerignore` que excluyan secretos, historiales `.git`, entornos virtuales y archivos temporales del contexto de compilación.

#### Scenario: Compilación limpia de imágenes
- **WHEN** se construye cualquiera de las imágenes del monorepo (`docker build`)
- **THEN** el contexto de construcción excluye `.env`, `.git`, `.venv`, `.DS_Store` y cachés `__pycache__` previniendo fugas y reduciendo el tamaño de imagen
