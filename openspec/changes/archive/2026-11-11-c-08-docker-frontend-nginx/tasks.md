# Tasks: C-08 Docker Frontend Nginx

## 1. Configuración y Servidor Web del Frontend

- [x] 1.1 Crear `frontend/.dockerignore` excluyendo `.git`, variables `.env*`, dependencias y temporales, y verificar su existencia y contenido con `ls -la frontend/.dockerignore`.
- [x] 1.2 Crear `frontend/default.conf.template` configurando puerto 80, `location /` con `try_files $uri $uri/ =404;` y `location /api/` con `proxy_pass http://${API_UPSTREAM}/;`, y verificar la sintaxis del template.
- [x] 1.3 Crear `frontend/Dockerfile` sobre `nginx:1.26-alpine` con `ENV NGINX_ENVSUBST_FILTER=^API_UPSTREAM$`, copia de `public/` a `/usr/share/nginx/html/` y copia de `default.conf.template` a `/etc/nginx/templates/`, y verificar que el Dockerfile declare el puerto 80.

## 2. Estandarización de Contenedor Backend

- [x] 2.1 Crear `backend/.dockerignore` excluyendo `.venv`, `__pycache__`, `.git`, `.env*` y cachés de pruebas, y verificar con `ls -la backend/.dockerignore`.
- [x] 2.2 Crear `backend/Dockerfile` estandarizado para Python 3.12-slim con instalación de dependencias, copia de código fuente, y comando de inicio `alembic upgrade head && exec uvicorn src.main:app --host 0.0.0.0 --port 8000`, verificando que el comando incluya la migración automática.

## 3. Orquestación Multi-servicio con Docker Compose

- [x] 3.1 Crear `docker-compose.yml` en la raíz del monorepo definiendo los servicios `db` (Postgres 16 con healthcheck), `backend` (puerto interno 8000 y dependencia saludable de `db`) y `frontend` (mapeo `127.0.0.1:8080:80` con variable `API_UPSTREAM=backend:8000`), y verificar la estructura del archivo.
- [x] 3.2 Actualizar las variables de upstream y puertos en `.env.example` en la raíz si aplica, verificando que coincidan con la orquestación.

## 4. Verificación de Compilación y Proxy Nginx

- [x] 4.1 Validar la configuración del compose ejecutando `docker compose config` sin errores de sintaxis.
- [x] 4.2 Probar la compilación limpia de la imagen frontend ejecutando `docker build -t libreria-frontend-test frontend/` y verificando código de salida 0.
- [x] 4.3 Verificar el procesamiento de `API_UPSTREAM` dentro del contenedor frontend confirmando que la configuración generada en `/etc/nginx/conf.d/default.conf` contenga el upstream interpolado correctamente.

## Workflow follow-up

- Archivar el change `c-08-docker-frontend-nginx` tras completar la implementación y verificación.
- Marcar el checkbox correspondiente a `[C-08]` en `CHANGES.md`.
