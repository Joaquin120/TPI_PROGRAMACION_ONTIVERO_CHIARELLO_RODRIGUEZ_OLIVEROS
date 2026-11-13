# Spec Delta: Easypanel Deployment Verification

## Purpose

Garantiza el despliegue productivo reproducible del monorepo en Easypanel (servicios `backend` privado y `frontend` Nginx con HTTPS), su documentación operativa y de entrega, y la verificación trazable end-to-end de los casos `G-01` a `G-07` sobre la URL pública definitiva.

## ADDED Requirements

### Requirement: Configuración de servicios separados en Easypanel
El sistema SHALL desplegarse en Easypanel como dos aplicaciones independientes mediante Dockerfile desde el monorepo: `backend` con build path `/backend`, variable `DATABASE_URL` hacia PostgreSQL y puerto `8000` privado, y `frontend` con build path `/frontend`, variable `API_UPSTREAM=<backend_service_name>:8000` y dominio público HTTPS conectado al puerto `80`.

#### Scenario: Comunicación privada entre frontend HTTPS y backend FastAPI
- **WHEN** un cliente accede a la URL pública HTTPS del servicio `frontend` y ejecuta operaciones `/api/*`
- **THEN** Nginx sirve la SPA con HTTPS válido y reenvía el tráfico API internamente hacia `http://${API_UPSTREAM}/` sin exponer el puerto `8000` a Internet

#### Scenario: Verificación de readiness productivo
- **WHEN** se consulta `GET /api/health/ready` sobre la URL pública HTTPS desplegada
- **THEN** el servicio responde HTTP `200 OK` confirmando conectividad activa con PostgreSQL tras aplicar `alembic upgrade head`

### Requirement: Documentación operativa y guía de entrega
El repositorio SHALL incluir en su raíz los archivos `DEPLOY.md` (con URL pública HTTPS definitiva, hash de commit desplegado, rutas de build, puertos, variables de upstream, migraciones y pasos de actualización/contingencia) y `README.md` (con identificación de integrantes, guía de ejecución local, carga de datos iniciales y checklist de entrega).

#### Scenario: Trazabilidad completa del entorno desplegado en DEPLOY.md
- **WHEN** se inspecciona `DEPLOY.md` después de publicar la versión en Easypanel
- **THEN** contiene la URL pública HTTPS exacta, el hash del commit desplegado, las variables requeridas sin secretos expuestos, la configuración de puertos y el procedimiento de actualización/rollback

#### Scenario: Reproducción local y carga inicial desde README.md
- **WHEN** un evaluador sigue las instrucciones de `README.md` en un entorno limpio
- **THEN** puede levantar el stack con Docker Compose o entorno local, poblar los datos iniciales y verificar el listado completo del checklist de entrega

### Requirement: Auditoría end-to-end G-01 a G-07 con evidencia trazable
La carpeta `evidencia/` SHALL registrar la ejecución verificada de todos los casos de prueba `G-01` a `G-07` sobre la URL pública definitiva HTTPS, incluyendo bitácoras en Markdown y capturas de Developer Tools (pestaña Network/Console) o salidas de terminal reales que demuestren cada resultado esperado y la persistencia tras reinicio o redespliegue.

#### Scenario: Verificación funcional completa sobre URL pública HTTPS (G-01 a G-06)
- **WHEN** se ejecutan los flujos `G-01` a `G-06` en la aplicación desplegada bajo dominio HTTPS
- **THEN** `evidencia/` documenta respuestas HTTP y capturas de catálogo paginado/búsqueda/detalle (`G-01`), alta de libro y rechazo `409` (`G-02`), alta/consulta de cliente y `409` (`G-03`), venta con persistencia post-recarga (`G-04`), invariante de precio histórico tras `PATCH /api/libros/{id}` (`G-05`) y preservación del borrador ante rechazos `422`/`409` (`G-06`)

#### Scenario: Persistencia tras reinicio o redespliegue del servicio (G-07)
- **WHEN** se reinicia o redespliega el servicio en Easypanel luego de haber creado libros, clientes y ventas
- **THEN** `/api/health/ready` vuelve a responder HTTP `200` y al consultar la URL pública los registros previamente creados y los precios actualizados permanecen intactos en PostgreSQL

### Requirement: Higiene e integridad del paquete de entrega
El proyecto entregado y su empaquetado `.zip` SHALL contener únicamente el código fuente, configuración Docker, migraciones, documentación y evidencias requeridas (`frontend/`, `backend/`, `README.md`, `DEPLOY.md`, `evidencia/`), excluyendo estrictamente archivos `.env`, credenciales reales, `node_modules/`, `.venv/`, `__pycache__/` y `.pytest_cache/`.

#### Scenario: Validación previa al empaquetado final
- **WHEN** se audita el árbol del repositorio y el archivo `.zip` generado para la entrega
- **THEN** no existen archivos `.env` con secretos reales ni directorios de dependencias o cachés locales, y solo figuran plantillas `.env.example`
