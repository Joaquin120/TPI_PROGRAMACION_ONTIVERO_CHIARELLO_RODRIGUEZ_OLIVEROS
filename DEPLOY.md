# Despliegue Productivo en Easypanel (`DEPLOY.md`)

Registro técnico de infraestructura, variables de entorno, mapeo de puertos, migraciones y procedimientos operativos del despliegue del monorepo en **Easypanel**.

---

## 1. Datos del Despliegue Público

- **URL Pública HTTPS (Frontend):** https://jjoc-libreria-tpi-frontend.oyerue.easypanel.host/
- **Commit Hash Desplegado y Verificado (G-01..G-07):** `ef80ead594ecd8e99977b70ededb2c07235e40df` *(rama `feat/c07-c09` lista para promoción a `main`)*
- **Rama Configurada Durante Verificación E2E:** `feat/c07-c09`
- **Endpoint de Readiness Público:** `https://jjoc-libreria-tpi-frontend.oyerue.easypanel.host/api/health/ready` → HTTP `200` (`{"status":"ready","database":"connected"}`)
- **Endpoint de Liveness Público:** `https://jjoc-libreria-tpi-frontend.oyerue.easypanel.host/api/health/live` → HTTP `200` (`{"status":"healthy","version":"0.1.0","environment":"production"}`)

---

## 2. Arquitectura y Configuración de Servicios en Easypanel

### 2.1 Base de Datos (`libreria-tpi-db`)
- **Motor:** PostgreSQL 16 (servicio gestionado en Easypanel dentro de la red privada del proyecto `jjoc`).
- **Host interno observado:** `jjoc_libreria-tpi-db` (puerto interno `5432`).
- **Credenciales y conexión:** provistas únicamente mediante la variable de entorno `DATABASE_URL` en el servicio `libreria-tpi-backend` (nunca versionar secretos reales en el repositorio).

### 2.2 Servicio Backend (`libreria-tpi-backend`)
- **Tipo de servicio:** `App`
- **Host interno / referencia en red privada:** `jjoc_libreria-tpi-backend`
- **Build Path:** `/backend`
- **Builder:** `Dockerfile` (`backend/Dockerfile`)
- **Puerto interno:** `8000` (aislado en red privada Docker, sin dominio público expuesto)
- **Variables de entorno requeridas:**
  - `DATABASE_URL=postgresql+asyncpg://<usuario>:<password>@jjoc_libreria-tpi-db:5432/<nombre_db>` *(reemplazar el esquema inicial de Easypanel por `postgresql+asyncpg://` y quitar parámetros `?sslmode=...` al final porque `asyncpg` no acepta `sslmode` como argumento)*
  - `ENVIRONMENT=production`
- **Comando de arranque del contenedor:**
  ```sh
  alembic upgrade head && python -m src.db.seed && exec uvicorn src.main:app --host 0.0.0.0 --port 8000
  ```

### 2.3 Servicio Frontend (`libreria-tpi-frontend`)
- **Tipo de servicio:** `App`
- **Build Path:** `/frontend`
- **Builder:** `Dockerfile` (`frontend/Dockerfile` basado en `nginx:1.26-alpine`)
- **Puerto interno:** `80`
- **Dominios (Domains):** `https://jjoc-libreria-tpi-frontend.oyerue.easypanel.host/` → `http://jjoc_libreria-tpi-frontend:80/` (HTTPS gestionado por Easypanel).
- **Variables de entorno requeridas:**
  - `API_UPSTREAM=jjoc_libreria-tpi-backend:8000` *(sin prefijo `http://` ni barra `/` final)*
  - `NGINX_ENVSUBST_FILTER=^API_UPSTREAM$` *(definida en `frontend/Dockerfile` para no sobrescribir `$uri` en `default.conf.template`)*

---

## 3. Proxy Inverso y Flujo de Peticiones

El archivo `frontend/default.conf.template` sirve la SPA estática desde `/usr/share/nginx/html` en `/` y enruta todo el tráfico `/api/` hacia el backend privado:

```nginx
location /api/ {
    proxy_pass http://${API_UPSTREAM}/;
}
```

La barra final en `proxy_pass http://${API_UPSTREAM}/;` reescribe `/api/libros/` → `/libros/`, evitando problemas de CORS y manteniendo privado el puerto `8000` de FastAPI.

---

## 4. Migraciones Automáticas y Seed Idempotente

1. **Migraciones de esquema (`alembic upgrade head`)**: se ejecutan automáticamente en cada arranque de `backend` antes de iniciar Uvicorn (`001` → `002` → `002b` → `003`), creando tablas, índices, constraints y llaves foráneas.
2. **Carga inicial (`python -m src.db.seed`)**: corre inmediatamente después de `alembic upgrade head`. Inserta registros mínimos (3 editoriales, 3 géneros, 3 autores, 3 libros y 1 cliente) únicamente si no existen por clave natural (`nombre`, `isbn`, `email`), preservando intactos los precios, stocks y ventas ya persistidos en reinicios o redespliegues (`G-05` y `G-07`).

---

## 5. Diagnóstico Rápido

| Síntoma | Causa probable y solución |
|---|---|
| **Falla un `COPY` en el build** | Verificar `Build Path` (`/backend` o `/frontend`), presencia de `public/` y exclusiones en `.dockerignore`. |
| **Nginx no arranca o `/api/` devuelve `502`** | Revisar logs de `frontend` y `backend`, confirmar que `API_UPSTREAM` coincida con `<nombre_servicio_backend>:8000` en la misma red interna. |
| **`/api/health/ready` falla (`503` o error de arranque)** | Verificar `DATABASE_URL` con esquema `postgresql+asyncpg://`, disponibilidad del servicio PostgreSQL y logs de `alembic upgrade head`. |
| **Una petición devuelve `404`** | Revisar en DevTools (Network) que el frontend use prefijo `/api/` y conserve barra final (`/`) en rutas de colección (`/api/libros/`, `/api/ventas/`, `/api/clientes/`). |

---

## 6. Actualización y Contingencia / Rollback

### Pasos de actualización
1. Pushear los cambios validados al repositorio conectado en Easypanel.
2. En Easypanel, ejecutar **Deploy** en el servicio modificado (`backend` y/o `frontend`).
3. Confirmar en logs de `backend` la finalización correcta de `alembic upgrade head`, `[seed] Datos iniciales procesados` y `Uvicorn running on http://0.0.0.0:8000`.
4. Validar `GET <URL_PUBLICA_HTTPS>/api/health/ready` → HTTP `200` (`{"status":"ready","database":"connected"}`).

### Pasos de contingencia / rollback
- **Rollback de código**: revertir al commit estable anterior en la rama desplegada o seleccionar el despliegue previo en Easypanel y redeployar.
- **Rollback de migración (si aplicara una nueva revisión Alembic)**: ejecutar en consola de `backend` `alembic downgrade -1` antes de restaurar la versión anterior de la imagen.
- **Persistencia**: validar que el volumen de PostgreSQL en Easypanel permanezca adjunto al servicio `db` antes de reiniciar o redesplegar aplicaciones.
