# Sistema de Diseño Visual — Librería Web

## Política Visual: `system-only`
Para el Trabajo Práctico Integrador se conserva y extiende la interfaz gráfica, estructura HTML y estilos CSS originados en el **Primer Parcial** (`REHACER_CHIARELLO_...`), garantizando el uso exclusivo de **HTML5 y CSS3 nativos** sin dependencias externas (Bootstrap, Tailwind, etc.).

---

## Componentes y Pautas de Estilo

### 1. Paleta y Tipografía
- **Tipografía base:** Sistema de fuentes sans-serif legible en entornos de escritorio y móviles (`system-ui`, `-apple-system`, `Segoe UI`, `Roboto`, `sans-serif`).
- **Colores de estado:**
  - **Éxito (201 Created):** Verde suave para banners de confirmación de ventas o altas.
  - **Conflicto (409 Conflict):** Ámbar / Naranja para advertir duplicados (ISBN o email).
  - **Error de Validación (422):** Rojo / Carmesí para señalar campos faltantes o libros repetidos.
  - **Información / Loading:** Azul sutil / gris neutro para spinners y estados de carga.

### 2. Estados Visuales Obligatorios (Consigna Ejercicio 1 y 3)
1. **Estado de Carga (*loading*):**
   - Indicador visual (spinner o texto animado) durante las llamadas `fetch`.
   - Botón de confirmación de venta deshabilitado (`disabled`) con cursor bloqueado para evitar dobles clics.
2. **Lista Vacía y Búsqueda Sin Coincidencias:**
   - Mensaje explícito en el contenedor de tabla: «No se encontraron libros para la búsqueda ingresada» o «No hay libros registrados en el catálogo».
3. **Manejo de Errores de Conexión:**
   - Banner de alerta ante respuestas de error de red o 502 Bad Gateway.
4. **Preservación del Formulario:**
   - En caso de error (409 o 422), los campos y el borrador de venta se mantienen intactos para no forzar al usuario a reescribir.

### 3. Responsividad
- Maquetado con CSS Grid y Flexbox adaptativo para permitir la carga correcta tanto en pantalla completa como en ventanas divididas.
