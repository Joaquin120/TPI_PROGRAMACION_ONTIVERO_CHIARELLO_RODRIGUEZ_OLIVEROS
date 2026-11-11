# Design: C-08 Docker Frontend Nginx

## Context
El monorepo cuenta con los activos web del Parcial 1 en `frontend/public/` y la API REST en `backend/src/`. Siguiendo el Ejercicio 4 y 5 de las consignas oficiales, el frontend debe empaquetarse en un contenedor Nginx autónomo que resuelva peticiones estáticas y redirija las llamadas API hacia el servicio backend, desacoplando dominios, evitando problemas de CORS y preparando los contenedores para el despliegue multi-servicio en Easypanel.

## Goals / Non-Goals

**Goals:**
- Construir una imagen Docker ligera y reproducible para el frontend basada en `nginx:1.26-alpine`.
- Configurar el proxy inverso Nginx con reescritura de prefijo de `/api/` a `/` mediante `proxy_pass http://${API_UPSTREAM}/;`.
- Proteger las variables nativas de configuración de Nginx mediante la directiva `NGINX_ENVSUBST_FILTER=^API_UPSTREAM$`.
- Proporcionar archivos `.dockerignore` estrictos tanto para frontend como backend evitando la inclusión de artefactos no deseados.
- Estandarizar `backend/Dockerfile` con ejecución obligatoria de migraciones automáticas (`alembic upgrade head`) al arrancar el contenedor.
- Crear `docker-compose.yml` para levantar la base de datos PostgreSQL, el backend y el frontend en un entorno integrado reproducible localmente.

**Non-Goals:**
- Despliegue en la VPS productiva o configuración en el panel de Easypanel (objeto del change `C-09`).
- Modificación de contratos de endpoints o lógica de negocio de la API (objeto de `C-02` a `C-07`).
- Configuración de certificados TLS/SSL locales (Easypanel gestiona HTTPS automáticamente en producción).

## Decisions

### 1. Servidor Web: Nginx 1.26 Alpine con templates automáticos
- **Decisión**: Utilizar la imagen base oficial `nginx:1.26-alpine` y colocar la plantilla de configuración en `/etc/nginx/templates/default.conf.template`.
- **Razón**: Las imágenes oficiales de Nginx incluyen un entrypoint que procesa automáticamente archivos `.template` mediante `envsubst` antes de iniciar el daemon de Nginx.
- **Alternativa considerada**: Instalar scripts personalizados de entrypoint con `sed` o `bash`. Se descartó por agregar complejidad y dependencias innecesarias en una imagen Alpine minimalista.

### 2. Filtro estricto de variables con `NGINX_ENVSUBST_FILTER`
- **Decisión**: Declarar `ENV NGINX_ENVSUBST_FILTER=^API_UPSTREAM$` en `frontend/Dockerfile`.
- **Razón**: Por defecto, `envsubst` reemplaza cualquier identificador que comience con `$` (incluyendo directivas nativas como `$uri`, `$host`, `$remote_addr`). El filtro asegura que únicamente se reemplace `${API_UPSTREAM}` preservando la configuración de Nginx intacta.
- **Alternativa considerada**: Escapar los signos de pesos como `\$uri`. Se descartó porque es propenso a errores humanos y no es el estándar recomendado por la imagen oficial ni la consigna.

### 3. Reescritura de URI mediante barra final en `proxy_pass`
- **Decisión**: Configurar el bloque de proxy como:
  ```nginx
  location /api/ {
      proxy_pass http://${API_UPSTREAM}/;
  }
  ```
- **Razón**: En Nginx, si una directiva `proxy_pass` incluye una URI (incluso una sola barra `/`), el prefijo coincidente del `location` (`/api/`) se reemplaza por dicha URI. Por lo tanto, una petición `GET /api/libros/` se reescribe de forma transparente a `GET /libros/` al alcanzar FastAPI, cumpliendo exactamente con las rutas definidas en el backend sin requerir prefijos adicionales en FastAPI.
- **Alternativa considerada**: Usar reglas `rewrite ^/api/(.*)$ /$1 break;`. Se descartó por ser más verbosa e innecesaria frente a la semántica estándar de `proxy_pass`.

### 4. Backend Dockerfile con migraciones al inicio
- **Decisión**: Crear `backend/Dockerfile` basado en `python:3.12-slim` ejecutando `alembic upgrade head && exec uvicorn src.main:app --host 0.0.0.0 --port 8000`.
- **Razón**: Garantiza la idempotencia de la base de datos al encender el contenedor tanto en desarrollo local como en Easypanel, cumpliendo con la Regla Dura #7 del proyecto y las consignas de evaluación.
- **Alternativa considerada**: Ejecutar migraciones en un contenedor temporal previo (init container). Se descartó porque Easypanel opera con servicios App independientes y la ejecución en el CMD es la solución estándar acordada.

### 5. Orquestación local con Docker Compose
- **Decisión**: Crear `docker-compose.yml` en la raíz con servicios `db` (Postgres 16), `backend` (FastAPI) y `frontend` (Nginx expuesto en `127.0.0.1:8080:80`).
- **Razón**: Permite validar de inmediato la interoperabilidad entre los tres contenedores, verificando la resolución de nombres DNS de Docker (`backend:8000`) y la respuesta del proxy sin afectar puertos del sistema anfitrión.

## Risks / Trade-offs

- **[Riesgo: El backend intenta migrar antes de que PostgreSQL acepte conexiones]**  
  → *Mitigación*: En `docker-compose.yml`, configurar un healthcheck en el servicio `db` (`pg_isready -U postgres`) y definir en `backend` la dependencia `depends_on: db: condition: service_healthy`.
- **[Riesgo: Mala interpretación de rutas estáticas vs rutas API]**  
  → *Mitigación*: Mantener el orden estricto de bloques en `default.conf.template`: `location /api/` para el upstream y `location /` con fallback `try_files $uri $uri/ =404;` para archivos estáticos.
- **[Riesgo: Fuga de variables de entorno o archivos pesados en el build]**  
  → *Mitigación*: Incorporar archivos `.dockerignore` estrictos en `frontend/` y `backend/` excluyendo `.env*`, `.git`, `.venv`, cachés de Python y módulos node.

## Migration Plan
1. Crear `frontend/Dockerfile`, `frontend/default.conf.template` y `frontend/.dockerignore`.
2. Crear `backend/Dockerfile` y `backend/.dockerignore`.
3. Crear `docker-compose.yml` en la raíz del proyecto configurando variables de entorno por defecto.
4. Validar sintaxis y configuración con `docker compose config`.
5. Probar compilación del contenedor frontend con `docker build -t libreria-frontend frontend/`.
