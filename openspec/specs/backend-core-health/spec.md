# backend-core-health Specification

## Purpose
Provee la aplicación base de FastAPI con conexión asíncrona a PostgreSQL, modelos relacionales de datos, soporte de migraciones automáticas mediante Alembic y un endpoint de verificación de salud en `/health/ready`.

## Requirements

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
El sistema SHALL proveer un mecanismo reproducible e idempotente mediante CLI (`python -m src.db.seed`) y ejecución automática tras `alembic upgrade head` al iniciar el contenedor backend para poblar la base de datos con al menos 3 editoriales, 3 géneros, 3 autores, 3 libros con stock y 1 cliente para posibilitar las pruebas de integración sin sobrescribir datos ya persistidos.

#### Scenario: Verificación de seed data
- **WHEN** se consulta la base de datos tras ejecutar el script de seed o iniciar el contenedor backend sobre una base recién migrada
- **THEN** existen registros precargados de editoriales, géneros, autores, libros con autorías/stock y cliente disponibles para operaciones de catálogo, alta y venta

#### Scenario: Idempotencia ante reinicios y cambios posteriores en catálogo
- **WHEN** el proceso de seed vuelve a ejecutarse después de reiniciar el servicio o luego de haber modificado precios de libros con `PATCH /libros/{id}` (`G-05` / `G-07`)
- **THEN** no se generan registros duplicados ni errores de restricción única, y se conservan intactos los precios, stocks y registros creados o editados previamente
