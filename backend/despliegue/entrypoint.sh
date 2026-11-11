#!/bin/sh
set -e

echo "[entrypoint] Iniciando verificacion de disponibilidad de PostgreSQL..."
python - << 'EOF'
import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("[entrypoint] ERROR: La variable DATABASE_URL no esta configurada.", file=sys.stderr)
    sys.exit(1)

async def wait_for_db():
    engine = create_async_engine(db_url, connect_args={"timeout": 5})
    for attempt in range(1, 31):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            print(f"[entrypoint] Conexion a PostgreSQL exitosa (intento {attempt}).")
            await engine.dispose()
            return True
        except Exception as exc:
            print(f"[entrypoint] Esperando base de datos ({attempt}/30): {exc}")
            await asyncio.sleep(1)
    await engine.dispose()
    return False

if not asyncio.run(wait_for_db()):
    print("[entrypoint] ERROR: Tiempo de espera agotado para conectar a PostgreSQL.", file=sys.stderr)
    sys.exit(1)
EOF

echo "[entrypoint] Ejecutando migraciones de base de datos (alembic upgrade head)..."
alembic upgrade head
echo "[entrypoint] Migraciones aplicadas con exito."

echo "[entrypoint] Iniciando servidor Uvicorn en 0.0.0.0:8000..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
