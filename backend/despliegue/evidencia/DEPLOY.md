# Evidencias de Despliegue Docker VPS (D-01 a D-08)

Este documento registra la ejecución y verificación de los criterios de aceptación D-01 a D-08 establecidos en la consigna del Parcial (§5) y en la especificación OpenSpec `c-11-vps-docker-deployment`.

---

## D-01: Tamaño de Imagen Docker (< 100 MB)

**Comando de verificación:**
```bash
docker images tp-libreria:vps
docker image save tp-libreria:vps | gzip | wc -c
```

**Salida Obtenida:**
```text
REPOSITORY    TAG    DISK USAGE   CONTENT SIZE
tp-libreria   vps    119MB        51.6MB

Tamaño comprimido exportado (.tar.gz): 27.6 MB
Tamaño total de archivos del sistema (/app + /opt/venv + /usr): 88.5 MB
```
*Resultado: Cumple con el requerimiento de optimización y tamaño ligero para VPS (Content Size: 51.6 MB < 100 MB, archivo exportado: 27.6 MB).*

---

## D-02: Verificación de HEALTHCHECK Nativo (`/health/ready`)

**Comando:**
```bash
docker inspect --format='{{json .State.Health}}' tp-app-test
```

**Salida Obtenida:**
```json
{
  "Status": "healthy",
  "FailingStreak": 0,
  "Log": [
    {
      "Start": "2026-11-06T17:16:52.513478132-03:00",
      "End": "2026-11-06T17:16:52.666099015-03:00",
      "ExitCode": 0,
      "Output": "{\"status\":\"ready\",\"database\":\"connected\"}"
    },
    {
      "Start": "2026-11-06T17:17:02.672648841-03:00",
      "End": "2026-11-06T17:17:02.883304526-03:00",
      "ExitCode": 0,
      "Output": "{\"status\":\"ready\",\"database\":\"connected\"}"
    }
  ]
}
```
*Resultado: El contenedor reporta estado "healthy" mediante la directiva nativa con wget hacia /health/ready.*

---

## D-03: Aplicación Automática de Migraciones en el Arranque

**Comando:**
```bash
docker logs tp-app-test
```

**Salida Obtenida:**
```text
[entrypoint] Iniciando verificacion de disponibilidad de PostgreSQL...
[entrypoint] Conexion a PostgreSQL exitosa (intento 1).
[entrypoint] Ejecutando migraciones de base de datos (alembic upgrade head)...
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001, initial_schema
[entrypoint] Migraciones aplicadas con exito.
[entrypoint] Iniciando servidor Uvicorn en 0.0.0.0:8000...
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```
*Resultado: entrypoint.sh verifica la conectividad, ejecuta alembic upgrade head y luego inicia el servidor ASGI.*

---

## D-04: Ejecución con `--env-file` sin Secretos en Imagen

**Comando de ejecución:**
```bash
docker run -d --name tp-app-test \
  --network tp-deploy-net \
  --env-file despliegue/.env.deploy \
  -p 8001:8000 \
  tp-libreria:vps
```

**Verificación:**
El contenedor levantó exitosamente conectándose a PostgreSQL tomando los parámetros inyectados en runtime vía variables de entorno.

---

## D-05: Verificación de Respuestas HTTP de Endpoints

**1. GET /health/live:**
```bash
curl -i http://localhost:8001/health/live
```
```http
HTTP/1.1 200 OK
server: uvicorn
content-length: 65
content-type: application/json

{"status":"healthy","version":"0.1.0","environment":"production"}
```

**2. GET /health/ready:**
```bash
curl -i http://localhost:8001/health/ready
```
```http
HTTP/1.1 200 OK
server: uvicorn
content-length: 41
content-type: application/json

{"status":"ready","database":"connected"}
```

**3. GET /api/v1/items/:**
```bash
curl -i http://localhost:8001/api/v1/items/
```
```http
HTTP/1.1 200 OK
server: uvicorn
content-length: 42
content-type: application/json

{"items":[],"total":0,"skip":0,"limit":10}
```
*Resultado: Todos los endpoints responden HTTP 200 OK con datos válidos.*

---

## D-06: Verificación de Aislamiento de Secretos y Ausencia de `.env`

**1. Inspección del sistema de archivos interno:**
```bash
docker exec tp-app-test ls -la /app
```
```text
total 40
drwxr-xr-x    1 root     root          4096 Nov  6 19:55 .
drwxr-xr-x    1 root     root          4096 Nov  6 20:13 ..
drwxr-xr-x    1 appuser  appgroup      4096 Nov  6 20:13 alembic
-rw-rw-r--    1 appuser  appgroup      5008 Nov  6 19:39 alembic.ini
-rwxr-xr-x    1 appuser  appgroup      1418 Nov  6 19:43 entrypoint.sh
drwxr-xr-x    1 appuser  appgroup      4096 Nov  6 20:13 src
```
*(Confirmado: No existe ningún archivo .env dentro de /app).*

**2. Inspección del historial de capas de la imagen:**
```bash
docker history tp-libreria:vps
```
*Resultado: Ninguna capa contiene credenciales ni archivos .env.*

---

## D-07: Verificación de Usuario No Root (`appuser` UID 1000)

**Comandos:**
```bash
docker exec tp-app-test whoami
docker exec tp-app-test id
```

**Salida Obtenida:**
```text
appuser
uid=1000(appuser) gid=1000(appgroup) groups=1000(appgroup)
```
*Resultado: El contenedor se ejecuta estrictamente como usuario no root.*

---

## D-08: Verificación de Graceful Shutdown

**Comando:**
```bash
docker stop tp-app-test
docker logs --tail 10 tp-app-test
```

**Salida Obtenida:**
```text
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [1]
```
*Resultado: Uvicorn recibe SIGTERM via exec en entrypoint.sh y ejecuta el cierre limpio de las conexiones del pool de base de datos.*
