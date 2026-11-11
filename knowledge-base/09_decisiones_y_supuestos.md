# Decisiones y Supuestos

## Decisiones Documentadas

### DD-01 — Uso de Nginx como Reverse Proxy con Enrutamiento `/api/`
- **Decisión:** Emplear una imagen ligera de Nginx (`nginx:1.26-alpine`) que sirve los estáticos en `/` y redirige `/api/` hacia el servicio backend FastAPI mediante `proxy_pass http://${API_UPSTREAM}/;`.
- **Contexto:** En el Parcial 1 el frontend corría localmente y en el Parcial 2 el backend en Uvicorn. Al unificarlos para producción con dominios públicos, se requiere evitar problemas de CORS y no exponer el puerto 8000 directamente a Internet.
- **Alternativas consideradas:** Servir los archivos estáticos montándolos dentro de FastAPI con `StaticFiles`.
- **Justificación:** Nginx es un servidor web altamente optimizado para servir contenido estático con compresión y caché, desacopla el ciclo de vida del frontend y backend, y cumple fielmente la consigna del Ejercicio 4.
- **Trade-offs:** Requiere un contenedor adicional en Docker y configuración de plantillas con `envsubst`.

### DD-02 — Migración total de `localStorage` a `fetch` nativo
- **Decisión:** Eliminar cualquier lectura/escritura de datos de negocio en `localStorage` en favor de llamadas `fetch` asíncronas directas contra la API REST.
- **Contexto:** En el Parcial 1 se utilizaba almacenamiento local en el navegador como simulación. El docente requirió expresamente conectar el frontend a la base de datos real.
- **Alternativas consideradas:** Mantener un modo offline / híbrido con sincronización en `localStorage`.
- **Justificación:** Evita inconsistencias de datos entre múltiples clientes o recargas de página, asegura que la base de datos PostgreSQL sea la única fuente de la verdad (*Single Source of Truth*), y responde al objetivo central del TPI.
- **Trade-offs:** La interfaz ahora depende de la conectividad con la API y debe manejar explícitamente estados de carga, desconexión y errores HTTP.

### DD-03 — Ejecución automática de migraciones Alembic al iniciar el Backend
- **Decisión:** El comando de arranque del contenedor backend es `alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000` (o `src.main:app`).
- **Contexto:** En entornos gestionados como Easypanel, el despliegue debe ser desatendido y tolerante a cambios en el esquema de base de datos sin requerir acceso manual por terminal SSH para correr migraciones.
- **Alternativas consideradas:** Correr migraciones como un job independiente previo al deploy.
- **Justificación:** Cumple con la especificación de la consigna (Sección 3.2 Ejercicio 5) y garantiza que la base de datos esté siempre en su última revisión antes de que Uvicorn comience a atender tráfico.

---

## Supuestos Inferidos

### SU-01 — Identificación del Backend en FastAPI
- **Supuesto:** El backend del Parcial 2 ubicado en `PARCIAL_2_...` posee los routers y modelos correspondientes a `libros`, `clientes`, `ventas`, `editoriales`, `generos` y `autores`, y su módulo principal es ejecutable con Uvicorn.
- **Origen:** Inspección de la estructura de código del Parcial 2 (`src/main.py`, `src/api/`).
- **Riesgo:** Si alguna ruta tuviera un nombre ligeramente distinto (ej. singular vs plural), la integración fallaría con 404.
- **Validación:** Comprobación de contratos en `src/api/` y pruebas locales previas al commit.

### SU-02 — Gestión de Datos Iniciales (Seed Data)
- **Supuesto:** La base de datos debe contener previamente o cargarse al inicio con editoriales, géneros y autores para permitir crear libros desde la interfaz sin que los selects queden vacíos.
- **Origen:** Consignas de evaluación G-02 (Alta de libro requiere seleccionar editorial, género y al menos un autor verificado).
- **Validación:** Verificar la existencia de scripts de seed o migraciones iniciales de datos en `backend/alembic/` o mediante script SQL de inicialización.
