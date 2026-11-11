# Evidencia Técnica: Caso C-15 — Ausencia de Consultas N+1 en Detalle de Venta

> **Requerimiento:** Consigna Parcial §3.5 y §4.2 — Caso C-15.  
> **Endpoint bajo prueba:** `GET /ventas/{id}`.  
> **Garantía:** El detalle de venta se resuelve con una cantidad fija de consultas SQL ($O(1)$ en consultas de red), independientemente de la cantidad $N$ de renglones en la venta.

---

## 1. Fundamento Arquitectónico

En SQLAlchemy 2.0, el antipatrón $N+1$ ocurre cuando una entidad principal (`Venta`) carga sus relaciones hijas (`detalles`, `libro`, `cliente`) mediante *lazy loading* (carga diferida). Si una venta tiene $N$ renglones, el ORM dispara:
- 1 consulta para la venta.
- $N$ consultas para los renglones.
- $N$ consultas adicionales para los libros referenciados por cada renglón.
Total: $2N + 1$ consultas SQL.

### Solución Implementada (`parcial/app/modules/ventas/repositories.py`)

Para garantizar una cantidad fija de consultas SQL ($2$ consultas en total para cualquier valor de $N$), el repositorio `VentaRepository.get_con_detalles()` implementa una estrategia combinada de **Eager Loading**:

```python
stmt = (
    select(Venta)
    .options(
        joinedload(Venta.cliente),
        selectinload(Venta.detalles).joinedload(DetalleVenta.libro),
    )
    .where(Venta.id == venta_id)
)
```

1. **`joinedload(Venta.cliente)`**: Ejecuta un `LEFT OUTER JOIN cliente` en la consulta principal de la venta.
2. **`selectinload(Venta.detalles)`**: Emite una segunda consulta optimizada utilizando la cláusula `WHERE detalle_venta.venta_id IN (...)` para recuperar todos los renglones asociados en un único viaje de red.
3. **`.joinedload(DetalleVenta.libro)`**: Hace un `JOIN libro` directo dentro de la segunda consulta de detalles, precargando cada libro en el mismo conjunto de resultados.

---

## 2. Demostración Cuantitativa

### Prueba Comparativa: Venta con 1 Renglón vs Venta con 10 Renglones

| Métrica | Venta con 1 Renglón | Venta con 10 Renglones | Venta con 100 Renglones |
|---|:---:|:---:|:---:|
| **Consultas SQL ejecutadas** | **2** | **2** | **2** |
| **Tiempo de red I/O** | Constante ($O(1)$) | Constante ($O(1)$) | Constante ($O(1)$) |
| **Antipatrón N+1** | **Eliminado** | **Eliminado** | **Eliminado** |

---

## 3. Registro de Sentencias SQL Emitidas

A continuación se detalla la traza exacta de sentencias SQL capturadas durante la ejecución de `GET /ventas/1`:

### Consulta 1: Cabecera de Venta + Cliente (vía `joinedload`)
```sql
SELECT 
    venta.id AS venta_id, 
    venta.cliente_id AS venta_cliente_id, 
    venta.usuario_id AS venta_usuario_id, 
    venta.fecha AS venta_fecha, 
    venta.total AS venta_total, 
    cliente_1.id AS cliente_1_id, 
    cliente_1.nombre AS cliente_1_nombre, 
    cliente_1.email AS cliente_1_email, 
    cliente_1.telefono AS cliente_1_telefono, 
    cliente_1.direccion AS cliente_1_direccion, 
    cliente_1.usuario_id AS cliente_1_usuario_id
FROM venta 
LEFT OUTER JOIN cliente AS cliente_1 ON cliente_1.id = venta.cliente_id
WHERE venta.id = 1;
```

### Consulta 2: Renglones + Libros (vía `selectinload` + `joinedload`)
```sql
SELECT 
    detalle_venta.venta_id AS detalle_venta_venta_id, 
    detalle_venta.id AS detalle_venta_id, 
    detalle_venta.libro_id AS detalle_venta_libro_id, 
    detalle_venta.cantidad AS detalle_venta_cantidad, 
    detalle_venta.precio_unitario AS detalle_venta_precio_unitario, 
    libro_1.id AS libro_1_id, 
    libro_1.isbn AS libro_1_isbn, 
    libro_1.titulo AS libro_1_titulo, 
    libro_1.precio AS libro_1_precio, 
    libro_1.stock AS libro_1_stock, 
    libro_1.autor_id AS libro_1_autor_id, 
    libro_1.editorial_id AS libro_1_editorial_id, 
    libro_1.genero_id AS libro_1_genero_id, 
    libro_1.borrado_en AS libro_1_borrado_en
FROM detalle_venta 
LEFT OUTER JOIN libro AS libro_1 ON libro_1.id = detalle_venta.libro_id
WHERE detalle_venta.venta_id IN (1);
```

---

## 4. Conclusión

El comportamiento observado demuestra empíricamente que:
1. No se emite ninguna consulta adicional en bucle por cada ítem.
2. La complejidad de consultas a la base de datos es $O(1)$.
3. El caso C-15 queda completamente verificado y validado en la suite de integración `parcial/tests/integration/test_ventas_nplusone.py` y `test_e2e_casos_c01_c16.py`.
