# Proposal: C-08 Docker Frontend Nginx

## Why
Para cumplir con los requerimientos del Trabajo Práctico Integrador (Ejercicio 4) y preparar el monorepo para el despliegue productivo en VPS administrada con Easypanel (Ejercicio 5), se requiere contenerizar el frontend web con un servidor de alto rendimiento y bajo consumo (Nginx). Dado que el frontend consume la API REST del backend en un entorno multi-contenedor, se necesita un reverse proxy que capture todas las peticiones con prefijo `/api/`, las reescriba de forma transparente hacia el contenedor backend y evite bloqueos de CORS, permitiendo además configurar dinámicamente el destino upstream mediante la variable de entorno `API_UPSTREAM`.

## What Changes
- **Contenerización del Frontend (`frontend/Dockerfile`)**: Definición de imagen basada en `nginx:1.26-alpine` con filtro de sustitución de entorno `ENV NGINX_ENVSUBST_FILTER=^API_UPSTREAM$`, copia del árbol estático de `frontend/public/` en `/usr/share/nginx/html/` y copia de la plantilla `default.conf.template` en `/etc/nginx/templates/default.conf.template`.
- **Plantilla de Servidor y Proxy (`frontend/default.conf.template`)**: Servidor Nginx en puerto 80 con bloque `location /` sirviendo `index.html` y activos con directiva `try_files $uri $uri/ =404;`, y bloque `location /api/` actuando como proxy reverso hacia `http://${API_UPSTREAM}/` (reescribiendo `/api/` con la barra final).
- **Higiene Docker (`frontend/.dockerignore` y `backend/.dockerignore`)**: Reglas de exclusión para no transferir `.git`, `.env*`, `.DS_Store`, cachés de Python ni carpetas temporales a los contextos de construcción Docker.
- **Estandarización del Backend (`backend/Dockerfile`)**: Imagen estándar en `python:3.12-slim` con ejecución de migraciones automáticas (`alembic upgrade head`) y ejecución de Uvicorn en el puerto interno 8000.
- **Orquestación Multi-contenedor (`docker-compose.yml`)**: Archivo de orquestación en la raíz con servicios `db` (PostgreSQL 16 en red interna), `backend` (FastAPI en puerto interno 8000) y `frontend` (Nginx expuesto en `127.0.0.1:8080:80` con enlace a `API_UPSTREAM=backend:8000`).

## Capabilities

### New Capabilities
- `frontend-nginx-proxy`: Servidor web Nginx en contenedor Alpine para servir el cliente estático nativo y rutear transparentemente peticiones `/api/` hacia el servicio backend con reescritura de prefijo y soporte para `API_UPSTREAM`.
- `local-container-orchestration`: Orquestación multi-servicio en Docker Compose para levantar y sincronizar la red entre PostgreSQL, backend FastAPI y proxy Nginx localmente.

### Modified Capabilities
*(Ninguna)*

## Impact
- **Frontend**: El cliente web se sirve formalmente desde Nginx en el puerto 8080 local y todas las llamadas HTTP nativas van al mismo origen bajo `/api/`.
- **Backend**: Expone su puerto 8000 de forma controlada dentro de la red interna de contenedores.
- **Despliegue**: Satisface el entregable de Dockerfile y proxy del Ejercicio 4, desbloqueando el despliegue directo en Easypanel (C-09).
