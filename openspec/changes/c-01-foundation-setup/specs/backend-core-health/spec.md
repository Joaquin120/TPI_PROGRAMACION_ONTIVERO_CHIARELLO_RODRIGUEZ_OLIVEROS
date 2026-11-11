# Spec Delta: backend-core-health

## Purpose
Provee la aplicación base de FastAPI con conexión asíncrona a PostgreSQL, modelos relacionales de datos, soporte de migraciones automáticas mediante Alembic y un endpoint de verificación de salud en `/health/ready`.

## ADDED Requirements

### Requirement: Endpoint de Diagnóstico de Salud
La API SHALL responder en la ruta `/health/ready` (o `/api/health/ready` a través del proxy inverso) indicando el estado de operatividad del servicio y verificando la conexión activa con la base de datos PostgreSQL.

#### Scenario: Consulta de salud exitosa
- **WHEN** se envía una petición `GET` a `/health/ready`
- **THEN** el servidor responde con código HTTP 200 y un cuerpo JSON con status positivo (`{"status": "ok"}`).

### Requirement: Modelos de Datos y Migraciones Alembic
El backend SHALL definir los modelos relacionales de `editoriales`, `generos`, `autores`, `libros`, `libros_autores`, `clientes`, `ventas` y `ventas_renglones`, y contar con el entorno de migraciones Alembic configurado para actualizar el esquema a su última versión.

#### Scenario: Ejecución de migraciones al inicio
- **WHEN** se ejecuta el comando de actualización de migraciones `alembic upgrade head`
- **THEN** todas las tablas relacionales y sus restricciones de clave foránea y unicidad quedan creadas en la base de datos sin errores.

### Requirement: Carga de Datos Mínimos Iniciales (Seed Data)
El sistema SHALL proveer un mecanismo reproducible para poblar la base de datos con al menos 3 editoriales, 3 géneros, 3 autores, 3 libros con stock y 1 cliente para posibilitar las pruebas de integración.

#### Scenario: Verificación de seed data
- **WHEN** se consulta la base de datos tras ejecutar el script o migración de seed
- **THEN** existen registros precargados de editoriales, géneros, autores y libros disponibles para operaciones de venta.
