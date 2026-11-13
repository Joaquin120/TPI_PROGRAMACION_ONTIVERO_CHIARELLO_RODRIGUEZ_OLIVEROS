# Spec Delta: Backend Core Health

## MODIFIED Requirements

### Requirement: Carga de Datos Mínimos Iniciales (Seed Data)
El sistema SHALL proveer un mecanismo reproducible e idempotente mediante CLI (`python -m src.db.seed`) y ejecución automática tras `alembic upgrade head` al iniciar el contenedor backend para poblar la base de datos con al menos 3 editoriales, 3 géneros, 3 autores, 3 libros con stock y 1 cliente para posibilitar las pruebas de integración sin sobrescribir datos ya persistidos.

#### Scenario: Verificación de seed data
- **WHEN** se consulta la base de datos tras ejecutar el script de seed o iniciar el contenedor backend sobre una base recién migrada
- **THEN** existen registros precargados de editoriales, géneros, autores, libros con autorías/stock y cliente disponibles para operaciones de catálogo, alta y venta

#### Scenario: Idempotencia ante reinicios y cambios posteriores en catálogo
- **WHEN** el proceso de seed vuelve a ejecutarse después de reiniciar el servicio o luego de haber modificado precios de libros con `PATCH /libros/{id}` (`G-05` / `G-07`)
- **THEN** no se generan registros duplicados ni errores de restricción única, y se conservan intactos los precios, stocks y registros creados o editados previamente
