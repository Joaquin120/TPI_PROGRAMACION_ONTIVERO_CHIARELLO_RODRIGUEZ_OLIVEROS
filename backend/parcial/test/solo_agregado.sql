-- =============================================================================
-- CASO C-14: Verificación de Trigger de Sólo Agregado en movimiento_stock
-- Consigna Parcial §3.2 y §4.2
-- =============================================================================

-- 1. Intentar actualizar una fila existente en movimiento_stock (debe fallar con excepción)
DO $$
BEGIN
    UPDATE movimiento_stock
    SET cantidad = 999
    WHERE id = 1;
    
    RAISE EXCEPTION 'ERROR: El UPDATE en movimiento_stock debió ser rechazado por el trigger.';
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'ÉXITO C-14 (UPDATE): El trigger rechazó la modificación correctamente: %', SQLERRM;
END $$;

-- 2. Intentar eliminar una fila existente en movimiento_stock (debe fallar con excepción)
DO $$
BEGIN
    DELETE FROM movimiento_stock
    WHERE id = 1;
    
    RAISE EXCEPTION 'ERROR: El DELETE en movimiento_stock debió ser rechazado por el trigger.';
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'ÉXITO C-14 (DELETE): El trigger rechazó la eliminación correctamente: %', SQLERRM;
END $$;
