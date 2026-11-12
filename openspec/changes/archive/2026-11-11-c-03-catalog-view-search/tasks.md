# Tasks: C-03 Catalog View and Search

## 1. Soporte de Backend y Contratos REST para Libros

- [x] 1.1 Modelar entidades y schemas Pydantic para `Editorial`, `Genero`, `Autor`, `Libro` y `LibroAutor` en `backend/src/`, y verificar que las definiciones de tipo y campos reflejen el modelo de datos.
- [x] 1.2 Implementar endpoints `GET /api/v1/libros/` (con paginación `limit`/`offset` y filtro parcial `titulo` insensible a mayúsculas) y `GET /api/v1/libros/{id}` con lista de autores asociados en `backend/src/api/v1/endpoints/libros.py`, y verificar con tests automatizados en `backend/tests/`.

## 2. Estructura HTML y Estilos Visuales del Catálogo

- [x] 2.1 Actualizar `frontend/public/index.html` integrando los 4 contenedores de estado (`#catalogo-cargando`, `#catalogo-listado-vacio`, `#catalogo-sin-resultados`, `#catalogo-error`), barra de paginación con selector de límite y modal accesible de autores, verificando la estructura del DOM.
- [x] 2.2 Extender `frontend/public/css/estilos.css` con estilos para el spinner de carga, estados de alerta, controles de paginación y modal accesible de detalle de autores, verificando coherencia con el sistema de diseño.

## 3. Lógica Cliente en JavaScript y Manejo de Estados

- [x] 3.1 Implementar en `frontend/public/js/app.js` la función de consulta inicial a `api.get('/libros/', { limit, offset })` y renderizado seguro del catálogo en la tabla con precio formateado y etiqueta «Sin clasificar» cuando `genero` es nulo (RN-LIB-06), verificando su ejecución al montar la vista.
- [x] 3.2 Implementar en `frontend/public/js/app.js` la búsqueda por título con reinicio automático a `offset = 0` (RN-LIB-07) y alternancia reactiva de los estados «Búsqueda sin coincidencias» y «Catálogo vacío», verificando el comportamiento ante consultas vacías y con texto.
- [x] 3.3 Implementar en `frontend/public/js/app.js` los controles de paginación interactiva (botones Anterior/Siguiente y selector de límite entre 1 y 100), verificando la actualización dinámica de filas y estado de los botones.
- [x] 3.4 Implementar en `frontend/public/js/app.js` la consulta individual `api.get('/libros/' + id)` al seleccionar un libro para desplegar el modal con autores, roles y orden de autoría, verificando la carga y cierre del modal.

## 4. Tests Automatizados y Verificación Integral

- [x] 4.1 Crear suite de pruebas unitarias para la lógica de renderizado, búsqueda y paginación del catálogo en `frontend/public/js/catalog.test.js` (o suite integrada), verificando que pasen al 100%.
- [x] 4.2 Ejecutar las pruebas completas de integración validando el cumplimiento del caso de prueba G-01 (búsqueda parcial, paginación, catálogo vacío y detalle de autores).

