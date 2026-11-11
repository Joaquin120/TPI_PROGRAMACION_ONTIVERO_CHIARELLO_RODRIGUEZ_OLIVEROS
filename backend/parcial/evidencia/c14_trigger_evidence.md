# Evidencia Caso C-14: Disparador de Solo Agregado (Append-Only)

Demostracion de que la tabla movimiento_stock rechaza cualquier intento de modificacion (UPDATE) o eliminacion (DELETE), garantizando la integridad de solo agregado (RN-12).

## Ejecucion del script solo_agregado.sql

Intento 1: Modificacion de un registro existente
UPDATE movimiento_stock SET cantidad = 999 WHERE id = 1;
Salida: ERROR: movimiento_stock es de solo agregado: no se permite UPDATE ni DELETE

Intento 2: Eliminacion de un registro
DELETE FROM movimiento_stock WHERE id = 1;
Salida: ERROR: movimiento_stock es de solo agregado: no se permite UPDATE ni DELETE

Ambas operaciones fueron rechazadas satisfactoriamente por el disparador instalado en la migracion manual de Alembic.
