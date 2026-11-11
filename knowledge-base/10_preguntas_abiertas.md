# Preguntas Abiertas

## Inconsistencias o Puntos de Atención Detectados

### IN-01 — Nombre del módulo de FastAPI en el Dockerfile de Producción
- **Documento de Consignas dice:** `CMD alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000` (referenciando `app.main:app`).
- **Código real del Parcial 2 tiene:** La carpeta raíz del código Python se llama `src/` (con `src/main.py`), no `app/`.
- **Impacto:** Si se copia el Dockerfile textual de la consigna con `app.main:app`, el contenedor fallará al arrancar con `ModuleNotFoundError: No module named 'app'`.
- **Resolución propuesta:** Configurar el comando como `exec uvicorn src.main:app --host 0.0.0.0 --port 8000` o asegurar que `WORKDIR /app` contenga el paquete correcto configurando `PYTHONPATH=.`.

### IN-02 — Rutas del backend con o sin barra final (`trailing slash`)
- **Documento de Consignas destaca:** *"Conservar la barra final de las rutas que la traen (ejemplo: `/api/libros/`)"*.
- **Impacto:** FastAPI genera redirecciones HTTP 307 cuando una ruta definida con `/` se consulta sin ella, y el proxy de Nginx podría reescribir incorrectamente la cabecera si no se respeta la barra.
- **Resolución propuesta:** Asegurar que el cliente `api.js` use rutas consistentes con barra final para todos los endpoints de colección (`/libros/`, `/ventas/`, `/clientes/`).

---

## Preguntas Abiertas Priorizadas

| Prioridad | Pregunta / Decisión | Bloquea | Decisor |
|---|---|---|---|
| **Alta** | ¿El backend del Parcial 2 ya cuenta con el script de seed de datos (editoriales, géneros, autores) o debemos incluirlo en una migración de Alembic? | Pruebas de integración del alta de libros | Equipo de desarrollo |
| **Media** | ¿La VPS de Easypanel para el despliegue final ya está aprovisionada y accesible para el equipo? | Ejercicio 5 y evidencias G-01 a G-07 | Integrante 4 (DevOps) |
| **Baja** | ¿Se mantendrá algún estilo CSS adicional del Parcial 1 o se conservará exactamente la maqueta previa? | Diseño visual | Equipo de desarrollo |
