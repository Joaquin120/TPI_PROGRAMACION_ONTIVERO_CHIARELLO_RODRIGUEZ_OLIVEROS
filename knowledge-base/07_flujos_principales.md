# Flujos Principales

Interacciones extremo a extremo entre el usuario, el navegador (Frontend/JS), el Reverse Proxy (Nginx), el Servidor de Aplicaciones (FastAPI) y la Base de Datos (PostgreSQL).

---

## Flujo 1: Registro y Confirmación de una Venta (Flujo Crítico)

**Disparador:** El operador completa el borrador de venta y presiona «Confirmar Venta».  
**Actor:** Operador de librería.

### Diagrama de Secuencia
```
Operador         Frontend (JS)               Proxy Nginx               FastAPI                PostgreSQL
   │                   │                          │                       │                       │
   │─ Clic Confirmar ─>│                          │                       │                       │
   │                   │── Deshabilita botón ────>│                       │                       │
   │                   │── POST /api/ventas/ ────>│                       │                       │
   │                   │   {cliente_id, renglones}│── POST /ventas/ ─────>│                       │
   │                   │                          │                       │── SELECT cliente,libros─>│
   │                   │                          │                       │<─ Libros y precios ───│
   │                   │                          │                       │                       │
   │                   │                          │                       │── Valida reglas ──────│
   │                   │                          │                       │   (stock, no repetidos)
   │                   │                          │                       │                       │
   │                   │                          │                       │── INSERT venta/rengl──>│
   │                   │                          │                       │<─ Venta persistida ───│
   │                   │                          │<── 201 Created (JSON)─│                       │
   │                   │<─ 201 Created ───────────│                       │                       │
   │                   │── Renderiza total oficial                        │                       │
   │                   │── Limpia borrador en memoria                     │                       │
   │                   │── Refresca lista historial                       │                       │
   │<─ Muestra éxito ──│                                                  │                       │
```

### Casos de Error y Contingencias:
1. **Cliente o libro inexistente:** FastAPI retorna `409 Conflict`. El frontend captura el error, habilita nuevamente el botón y muestra el mensaje al usuario manteniendo el borrador intacto.
2. **Libros repetidos en renglones:** FastAPI retorna `422 Unprocessable Entity`. El frontend muestra la advertencia y solicita consolidar los renglones.
3. **Falla de conexión o Nginx 502:** El frontend atrapa la excepción de red, advierte «Error de comunicación con el servidor» y no descarta los datos del operador.

---

## Flujo 2: Consulta de Catálogo con Búsqueda y Paginación

**Disparador:** Carga inicial de la página o ingreso de término en el buscador.  
**Actor:** Usuario o comprador.

### Pasos:
1. El usuario escribe un título en el input de búsqueda.
2. El frontend actualiza el estado interno: `offset = 0`, `titulo = valor_input`.
3. El frontend activa el estado de carga (muestra spinner / oculta tabla).
4. El frontend dispara `fetch('/api/libros/?limit=20&offset=0&titulo=' + encodeURIComponent(titulo))`.
5. Nginx reenvía la petición al backend (`GET /libros/...`).
6. FastAPI realiza consulta asíncrona a PostgreSQL con filtro `ILIKE %titulo%` y cláusulas `LIMIT 20 OFFSET 0`.
7. Si el resultado es un array con elementos: se renderizan las tarjetas/filas de libros en la tabla.
8. Si el resultado es un array vacío: se renderiza el mensaje «No se encontraron libros para la búsqueda ingresada».
9. El estado de carga se desactiva.

---

## Flujo 3: Demostración del Invariante de Precio Histórico (Caso G-05)

**Disparador:** Auditoría de integridad de ventas históricas.  
**Actor:** Evaluador.

### Pasos:
1. Se registra una venta con el libro X cuyo precio actual es `$1.000,00`. Total registrado: `$2.000,00` (2 unidades).
2. Se consulta la venta recién creada con `GET /api/ventas/{id}`. Subtotal: `$2.000,00`.
3. Se actualiza el precio del libro X mediante `PATCH /api/libros/{id}` fijando su nuevo precio en `$5.000,00`.
4. Se recarga el navegador web o se vuelve a consultar `GET /api/ventas/{id}`.
5. El detalle de la venta histórica sigue mostrando el precio unitario de `$1.000,00` y el total de `$2.000,00`.
6. En el catálogo (`GET /api/libros/`), el libro X ahora se muestra con `$5.000,00`.
7. Se constata la preservación inalterable del registro contable histórico.
