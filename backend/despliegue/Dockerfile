# Multi-stage build para TP (Capítulos 1 a 4) - Despliegue VPS
# Etapa 1: Builder (compilación de dependencias C con musl-dev/gcc y optimización de tamaño)
FROM python:3.12-alpine AS builder

WORKDIR /build

RUN apk add --no-cache gcc musl-dev libpq-dev python3-dev binutils

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    find /opt/venv -name "*.so*" -exec strip --strip-unneeded {} + 2>/dev/null || true && \
    find /opt/venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type f -name "*.pyc" -delete 2>/dev/null || true && \
    find /opt/venv -type f -name "*.pyo" -delete 2>/dev/null || true && \
    find /opt/venv -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type d -name "testing" -exec rm -rf {} + 2>/dev/null || true && \
    rm -rf /opt/venv/lib/python3.12/site-packages/pip \
           /opt/venv/lib/python3.12/site-packages/setuptools \
           /opt/venv/bin/pip*

# Etapa 2: Runner minimal para producción (< 100 MB)
FROM python:3.12-alpine

# Instalar bibliotecas de runtime y crear usuario no root
RUN apk add --no-cache libpq wget && \
    addgroup -g 1000 appgroup && \
    adduser -u 1000 -G appgroup -s /bin/sh -D appuser

# Copiar entorno virtual optimizado
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1

WORKDIR /app

# Copiar archivos fuente del TP asignando propiedad a appuser
COPY --chown=appuser:appgroup src/ ./src/
COPY --chown=appuser:appgroup alembic/ ./alembic/
COPY --chown=appuser:appgroup alembic.ini ./alembic.ini
COPY --chown=appuser:appgroup entrypoint.sh ./entrypoint.sh

RUN chmod +x ./entrypoint.sh

USER appuser

EXPOSE 8000

# Healthcheck nativo consultando /health/ready mediante wget
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1:8000/health/ready || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
