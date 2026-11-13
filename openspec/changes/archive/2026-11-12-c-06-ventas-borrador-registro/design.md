# Design: C-06 Ventas - Borrador y Registro

## Context

Ver `proposal.md` para la motivación y reglas de negocio del cambio (US-006, US-007, RN-VEN-01 a RN-VEN-08 y casos de prueba G-04 y G-06).
El sistema ya cuenta con el catálogo de libros persistido (`libros`, `libros_autores`, `editoriales`, `generos`) y la gestión de clientes (`clientes`). El objetivo de esta fase es implementar el dominio transaccional de ventas, reemplazando la simulación anterior por transacciones atómicas en PostgreSQL y lógica reactiva en JavaScript nativo.

## Goals / Non-Goals

**Goals:**
- Crear los modelos SQLAlchemy `Venta` y `VentaRenglon` con sus restricciones de clave foránea e integridad (`clientes.id`, `libros.id`, `cantidad > 0`, `precio_unitario >= 0.00`).
- Generar la migración Alembic `003_create_ventas.py` para la creación de las tablas `ventas` y `ventas_renglones`.
- Exponer el endpoint transaccional `POST /api/v1/ventas/` (con alias `/ventas/`) que:
  - Verifique la existencia de cliente y libros (retornando `409 Conflict` si alguno no existe, RN-VEN-01).
  - Verifique que la venta no esté vacía y que no existan libros duplicados en renglones (retornando `422 Unprocessable Entity`, RN-VEN-02, RN-VEN-04).
  - Congele inmutablemente el precio unitario del catálogo al momento de la venta y calcule subtotales y total oficial (RN-VEN-05, RN-VEN-06).
  - Persista de manera atómica (commit único o rollback ante error).
- Implementar el módulo frontend `frontend/public/js/sales.js` que gestione el borrador en memoria:
  - Carga dinámica y sincronización de clientes y libros en selectores.
  - Validación local de unicidad de renglón y cantidad positiva.
  - Deshabilitación del botón de confirmación durante la petición de red (RN-VEN-07).
  - Preservación íntegra del borrador ante respuestas de error `409` o `422` (RN-VEN-08).
- Cobertura de pruebas unitarias y de integración bajo Strict TDD.

**Non-Goals:**
- Implementar la consulta paginada del historial de ventas ni el modal de detalle histórico post-recarga (alcance reservado para C-07).
- Modificación o cancelación de ventas registradas (el modelo de ventas es de registro inmutable).

## Decisions

### 1. Transaccionalidad Atómica y Cálculo Oficial en Servidor (RN-VEN-05, RN-VEN-06)
- **Decisión**: El payload de creación de venta enviado por el cliente contendrá exclusivamente los identificadores y cantidades:
  ```json
  {
    "cliente_id": 1,
    "renglones": [
      { "libro_id": 10, "cantidad": 2 },
      { "libro_id": 12, "cantidad": 1 }
    ]
  }
  ```
  El backend será la única autoridad que consulte los precios vigentes en la tabla `libros`, calcule los subtotales (`cantidad * precio_unitario`), compute la suma total y congele estos valores en `ventas_renglones` y `ventas` dentro de una transacción única (`db.begin()` / `commit()`).
- **Alternativas consideradas**:
  - *Permitir que el cliente envíe los precios unitarios*: Descartado rotundamente; viola la seguridad y la integridad del negocio, permitiendo que un cliente altere los precios de compra.

### 2. Diferenciación Estricta de Errores de Negocio (409 Conflict vs 422 Unprocessable Entity)
- **Decisión**:
  - **409 Conflict**: Reservado para inconsistencias de existencia en base de datos (cliente inexistente o libro dado de baja/inexistente según RN-VEN-01).
  - **422 Unprocessable Entity**: Reservado para violaciones estructurales del contrato (venta sin renglones, cantidad <= 0 o libro duplicado en más de un renglón según RN-VEN-02, RN-VEN-03 y RN-VEN-04).
- **Alternativas consideradas**:
  - *Usar 400 Bad Request para todo*: Descartado; las consignas del trabajo práctico y los casos de prueba G-04 y G-06 evalúan explícitamente los códigos `409` y `422`.

### 3. Módulo Frontend `frontend/public/js/sales.js` con Borrador en Memoria (RN-VEN-08)
- **Decisión**: El estado de la composición vivirá en un objeto JavaScript en memoria del navegador:
  ```javascript
  export const estadoVenta = {
    clienteId: null,
    renglones: [], // Array de { libroId, titulo, precioUnitario, cantidad, subtotal }
    enviando: false,
  };
  ```
  No se utilizará `localStorage` para persistir ventas confirmadas ni borradores inconclusos, cumpliendo la Regla Dura #1 del proyecto.
- **Alternativas consideradas**:
  - *Guardar el borrador en `localStorage`*: Descartado por la regla dura que prohíbe el uso de `localStorage` para el flujo de ventas.

### 4. Prevención de Dobles Envíos (RN-VEN-07)
- **Decisión**: Al despachar la petición `POST /api/ventas/`, el botón `#venta-confirmar` se deshabilita de inmediato (`disabled = true`) y su texto o indicador visual muestra el estado de procesamiento. Se rehabilita únicamente en el bloque `finally` de la operación asíncrona.
- **Alternativas consideradas**:
  - *Debounce en el listener*: Insuficiente ante peticiones de red prolongadas. La deshabilitación del botón en el DOM garantiza que no se generen ventas duplicadas concurrentes.

### 5. UI Mockups
- **Decisión**: `Decision: no (project policy)`
- **Justificación**: Conforme a la política del proyecto establecida en `.active-orchestrator-state.json` y `design-system/README.md` (`visual_design.mode: system-only`), los componentes visuales de la vista de ventas reutilizan los estilos CSS nativos y estructura HTML existente sin requerir mockups individuales.

## Risks / Trade-offs

- **[Riesgo: Libro duplicado enviado concurrentemente en diferentes renglones]** → **Mitigación**: Doble barrera de validación: en el frontend `sales.js` se comprueba `some(r => r.libroId === libroId)` antes de insertar, y en el backend Pydantic / router se valida que `len(set(libro_ids)) == len(libro_ids)` retornando `422`.
- **[Riesgo: Fallo a mitad del guardado de renglones]** → **Mitigación**: Transacción ACID en PostgreSQL gestionada por `AsyncSession`. Si cualquier validación de renglón falla, se ejecuta `rollback()` automático, impidiendo registros huérfanos.

## Migration Plan

1. Crear y ejecutar migración Alembic `003_create_ventas.py`.
2. Registrar el router de ventas en `backend/src/api/router.py`.
3. Desplegar módulo frontend `sales.js` y conectar en `app.js`.
