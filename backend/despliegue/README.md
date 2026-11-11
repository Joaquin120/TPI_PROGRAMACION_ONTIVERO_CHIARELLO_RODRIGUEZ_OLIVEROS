# Despliegue Containerizado - Backend TP (Capítulos 1 a 4)

Este directorio contiene el empaquetado y la configuración para el despliegue del backend en un VPS utilizando Docker.

## Características Principales
- **Imagen Optimizada (< 100 MB):** Multi-stage build sobre Alpine Linux 3.12 con Python 3.12 (Content Size: 51.6 MB).
- **Seguridad:** El contenedor se ejecuta como usuario no privilegiado `appuser` (UID 1000).
- **Aislamiento de Secretos:** No se incluyen archivos `.env` en la imagen (`.dockerignore`). Toda configuración se inyecta en tiempo de ejecución vía `--env-file`.
- **Resiliencia y Automatización:** `entrypoint.sh` verifica la disponibilidad de PostgreSQL y aplica automáticamente `alembic upgrade head`.
- **Healthcheck Nativo:** Monitor de readiness nativo con `wget` sobre `/health/ready`.

## Compilación de la Imagen

```bash
docker build -t tp-libreria:vps despliegue/
```

Verificar el tamaño de la imagen:
```bash
docker images tp-libreria:vps
```

## Ejecución con Docker

1. Crear un archivo de entorno (por ejemplo, `.env.production`):
```env
APP_NAME=TP_Cap1a4_Backend
ENVIRONMENT=production
LOG_LEVEL=INFO
DATABASE_URL=postgresql+asyncpg://postgres:postgres@<ip_o_host_db>:5432/tp_cap1a4_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=tp_cap1a4_db
POSTGRES_HOST=<ip_o_host_db>
POSTGRES_PORT=5432
DB_ECHO=False
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_TIMEOUT=2.0
```

2. Ejecutar el contenedor:
```bash
docker run -d \
  --name tp-backend \
  --restart unless-stopped \
  --env-file .env.production \
  -p 8000:8000 \
  tp-libreria:vps
```

3. Verificar logs y estado de salud:
```bash
docker logs -f tp-backend
docker inspect --format='{{json .State.Health}}' tp-backend
```

4. Detener el contenedor de forma limpia (Graceful Shutdown):
```bash
docker stop tp-backend
```
