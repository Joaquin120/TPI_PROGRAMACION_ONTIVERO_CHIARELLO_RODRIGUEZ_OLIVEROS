# Funcionalidades

Historias de usuario estructuradas por épica con criterios de aceptación verificables.

---

## Épica 1: Catálogo y Navegación de Libros (EP-CAT)

### US-001 — Exploración y Paginación del Catálogo
**Como** usuario del sistema  
**Quiero** ver la lista de libros en el catálogo con paginación  
**Para** navegar por el inventario sin sobrecargar la página ni la red.

**Criterios de aceptación:**
- [ ] La pantalla solicita `GET /api/libros/?limit=20&offset=0` al cargar.
- [ ] Muestra para cada libro: Título, ISBN, Precio, Editorial y Género (o «Sin clasificar» si es nulo).
- [ ] Dispone de controles para avanzar o retroceder páginas (`limit`, `offset`).
- [ ] Muestra spinner de carga mientras se espera respuesta.
- [ ] Reglas asociadas: RN-LIB-06.

### US-002 — Búsqueda de Libros por Título
**Como** usuario del sistema  
**Quiero** filtrar los libros escribiendo parte de su título  
**Para** encontrar rápidamente el ejemplar que busco.

**Criterios de aceptación:**
- [ ] Al escribir en el buscador y confirmar o escribir tras un debounce, se consulta `GET /api/libros/?titulo={texto}&offset=0`.
- [ ] El desplazamiento se reinicia automáticamente a `offset = 0` al alterar el filtro.
- [ ] Si no hay coincidencias, muestra un estado visual claro: «No se encontraron libros».
- [ ] Reglas asociadas: RN-LIB-07.

### US-003 — Consulta de Detalle y Autores de un Libro
**Como** usuario del sistema  
**Quiero** consultar el detalle completo de un libro  
**Para** conocer todos sus autores, su orden y su rol de participación.

**Criterios de aceptación:**
- [ ] Al hacer clic en un libro, se realiza `GET /api/libros/{id}`.
- [ ] Se despliega la lista de autores indicando nombre y rol (`autor`, `coautor`, etc.).

---

## Épica 2: Altas de Entidades (EP-ALT)

### US-004 — Alta de Nuevos Libros
**Como** operador de librería  
**Quiero** registrar un nuevo libro asociando sus datos y autorías  
**Para** incorporarlo al catálogo disponible para la venta.

**Criterios de aceptación:**
- [ ] Los selectores de editorial y género se cargan desde `GET /api/editoriales/` y `GET /api/generos/`.
- [ ] Permite buscar o validar autores por ID con `GET /api/autores/{id}` antes de agregarlos a la lista de autorías con su rol y orden.
- [ ] Valida localmente campos obligatorios antes de disparar el `POST`.
- [ ] Al recibir `201 Created`, notifica éxito y actualiza la vista del catálogo.
- [ ] Si la API responde `409 Conflict` (ISBN repetido) o `422`, muestra el mensaje descriptivo en pantalla.
- [ ] Reglas asociadas: RN-LIB-01 a RN-LIB-05.

### US-005 — Alta de Clientes
**Como** operador de librería  
**Quiero** registrar un nuevo cliente con su nombre y correo  
**Para** asociarlo posteriormente a una venta.

**Criterios de aceptación:**
- [ ] Formulario con campos `nombre` y `email`.
- [ ] Valida formato de email antes del envío.
- [ ] Envía `POST /api/clientes/`.
- [ ] Si responde `409 Conflict` por email duplicado, informa claramente al operador sin cerrar el formulario.
- [ ] Reglas asociadas: RN-CLI-01, RN-CLI-02.

---

## Épica 3: Gestión de Ventas (EP-VEN)

### US-006 — Construcción de Borrador de Venta en Memoria
**Como** operador de librería  
**Quiero** seleccionar un cliente y agregar múltiples libros con sus cantidades en un borrador temporal  
**Para** preparar la orden antes de confirmarla de forma definitiva.

**Criterios de aceptación:**
- [ ] El borrador vive en la memoria de JavaScript (no persiste en backend hasta confirmar).
- [ ] Permite buscar cliente por ID (`GET /api/clientes/{id}`) y verificar su nombre.
- [ ] Permite agregar libros desde el catálogo.
- [ ] Permite cambiar cantidades y remover renglones.
- [ ] No permite agregar el mismo libro más de una vez (un único renglón por libro).
- [ ] Reglas asociadas: RN-VEN-02 a RN-VEN-04.

### US-007 — Confirmación y Persistencia de la Venta
**Como** operador de librería  
**Quiero** confirmar el borrador de venta  
**Para** que la API registre la transacción en la base de datos y descuente/calcule los importes oficiales.

**Criterios de aceptación:**
- [ ] El botón de confirmación se deshabilita mientras la solicitud esté en curso.
- [ ] Envía `POST /api/ventas/` con `{ cliente_id, renglones: [...] }`.
- [ ] Al recibir `201 Created`, renderiza el total y subtotales confirmados por la API, limpia el borrador y refresca el historial.
- [ ] Ante error (409 o 422), preserva el borrador intacto para corrección.
- [ ] Reglas asociadas: RN-VEN-01, RN-VEN-06, RN-VEN-07, RN-VEN-08.

### US-008 — Historial y Detalle de Ventas
**Como** operador o evaluador  
**Quiero** visualizar las ventas pasadas y abrir su detalle  
**Para** auditar las operaciones y constatar la inmutabilidad de los precios históricos.

**Criterios de aceptación:**
- [ ] Lista de ventas paginada obtenida de `GET /api/ventas/?limit=20&offset=0`.
- [ ] Al seleccionar una venta, consulta `GET /api/ventas/{id}` y muestra fecha, cliente, renglones con precio unitario, subtotales y total.
- [ ] Permite recargar la página y volver a consultar exactamente la misma información.
- [ ] Reglas asociadas: RN-VEN-05.
