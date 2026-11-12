# Tasks: C-04 Alta de Libros

## 1. Soporte Backend y Contratos REST para Alta de Libros

- [x] 1.1 Modelar endpoints auxiliares `GET /api/v1/editoriales/`, `GET /api/v1/generos/` y `GET /api/v1/autores/{id}` en FastAPI, y verificar con tests unitarios en `backend/tests/`.
- [x] 1.2 Implementar endpoint transaccional `POST /api/v1/libros/` con schema `LibroCreate` (validación de precio > 0, stock >= 0, autorías y control de integridad para emitir 409 Conflict ante ISBN duplicado), y verificar con tests de integración.

## 2. Componente de Formulario y Estructura en Frontend

- [x] 2.1 Actualizar la vista de alta de libros en `frontend/public/index.html` con selectores dinámicos (`#libro-editorial`, `#libro-genero`), buscador/validador de autores por ID con selección de rol y lista visual de autorías agregadas, verificando la estructura del DOM.
- [x] 2.2 Agregar estilos en `frontend/public/css/estilos.css` para el panel de verificación de autor, badges de rol y contenedor de mensajes de error/éxito, verificando accesibilidad y coherencia visual.

## 3. Lógica Cliente en JavaScript y Manejo de Respuestas

- [x] 3.1 Implementar en `frontend/public/js/books.js` la carga de editoriales y géneros desde la API y el poblado de los elementos `<select>` correspondientes, verificando el manejo de género nulo («Sin clasificar»).
- [x] 3.2 Implementar en `frontend/public/js/books.js` la búsqueda de autor por ID consultando `api.get('/autores/' + id)`, visualización del nombre verificado y agregado dinámico al listado de autorías con rol y orden correlativo.
- [x] 3.3 Implementar validaciones en cliente (`precio > 0`, `stock >= 0`, `autores.length >= 1`, formato ISBN) y envío de `POST /api/libros/` mediante el cliente HTTP.
- [x] 3.4 Implementar el tratamiento de respuestas: notificación y reset del formulario ante `201 Created` con refresco reactivo del catálogo, y preservación intacta del formulario ante errores `409 Conflict` (ISBN repetido) o `422`.

## 4. Tests Automatizados y Verificación del Caso G-02

- [x] 4.1 Crear suite de pruebas unitarias en `frontend/public/js/books.test.js` testeando validaciones de formulario, construcción del payload, verificación de autores y preservación ante 409/422.
- [x] 4.2 Ejecutar las suites de pruebas de frontend y backend, comprobando el cumplimiento del caso de prueba G-02 (alta exitosa y rechazo 409 por ISBN duplicado).

