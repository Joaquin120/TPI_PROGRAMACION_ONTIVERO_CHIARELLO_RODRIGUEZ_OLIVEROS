# Despliegue y Casos de Prueba (G-01 a G-07)

## Protocolo de Ejecución de Pruebas en URL Pública

Todas las pruebas se ejecutan sobre la **URL pública definitiva con HTTPS** provista por Easypanel:

| Caso | Módulo | Procedimiento | Resultado Esperado | Evidencia Requerida |
|---|---|---|---|---|
| **G-01** | Catálogo y Paginación | 1. Cargar el catálogo.<br>2. Buscar por un título parcial.<br>3. Probar búsqueda sin coincidencias.<br>4. Avanzar y retroceder con `limit` y `offset`.<br>5. Abrir detalle de libro. | - Listado renderiza libros con editorial y género.<br>- Si no coincide, muestra estado vacío.<br>- Detalle muestra autores asociados. | Capturas de pantalla con Developer Tools (pestaña Red). |
| **G-02** | Alta de Libro | 1. Completar formulario de libro con stock, editorial, género y al menos un autor.<br>2. Confirmar alta.<br>3. Intentar dar de alta otro libro con el mismo ISBN. | - Primera petición retorna `201 Created` y se ve en el catálogo.<br>- Segunda petición retorna `409 Conflict` y la UI muestra el error sin caerse. | Captura de respuesta 201 y mensaje de error 409. |
| **G-03** | Alta de Cliente | 1. Registrar cliente con nombre y email.<br>2. Reintentar con el mismo email.<br>3. Consultar cliente por ID. | - Primera petición retorna `201 Created`.<br>- Segunda retorna `409 Conflict` con mensaje claro.<br>- Consulta por ID devuelve los datos. | Captura de formulario con 201 y 409. |
| **G-04** | Registro de Venta | 1. Armar venta con cliente y al menos 2 renglones de libros diferentes.<br>2. Confirmar venta.<br>3. Recargar la página y abrir el detalle en el historial. | - Retorna `201 Created`.<br>- Subtotales y total calculados por la API coinciden.<br>- Tras recarga, el detalle de la venta persiste intacto. | Captura de confirmación y detalle post-reload. |
| **G-05** | Invariante de Precio Histórico | 1. Registrar una venta con libro A a precio $X.<br>2. Modificar el precio del libro A con `PATCH /api/libros/{id}` a precio $Y.<br>3. Consultar la venta registrada previamente. | - El catálogo muestra el nuevo precio $Y.<br>- La venta histórica conserva el precio original $X y sus importes intactos. | Capturas comparativas de catálogo vs detalle histórico. |
| **G-06** | Rechazo y Preservación de Borrador | 1. Intentar registrar una venta con libros duplicados en renglones.<br>2. Intentar registrar con cliente inexistente. | - Venta duplicada responde `422 Unprocessable Entity`.<br>- Cliente inexistente responde `409 Conflict`.<br>- El borrador en pantalla no se borra. | Captura de UI conservando los renglones ante error. |
| **G-07** | Infraestructura y Despliegue | 1. La imagen de frontend compila limpiamente.<br>2. La URL abre con HTTPS válido.<br>3. `/api/health/ready` devuelve HTTP 200.<br>4. Se reinicia el servicio y los datos siguen persistidos en PostgreSQL. | - Servicio 100% operativo y datos persistentes tras reinicio de contenedores. | Captura de terminal / logs de Easypanel y `/health/ready`. |

---

## Estructura de Documentación de Entrega Requerida
En la entrega final deben estar presentes:
- `DEPLOY.md`: URL pública, revisión de commit, configuración de puertos y variables de entorno.
- `evidencia/`: Carpeta con los archivos Markdown y capturas correspondientes a cada caso `G-01` a `G-07`.
