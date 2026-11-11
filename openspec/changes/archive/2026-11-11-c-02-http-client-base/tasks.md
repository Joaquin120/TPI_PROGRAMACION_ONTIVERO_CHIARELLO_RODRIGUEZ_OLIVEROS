# Tasks: C-02 HTTP Client Base

## 1. Clase de Error y Estructura Base

- [x] 1.1 Crear la clase `ApiError` en `frontend/public/js/api.js` conteniendo propiedades `message`, `status` y `data`, y verificar su instanciación y herencia de `Error`.
- [x] 1.2 Definir la estructura base del módulo `api` con soporte para exportación ES6 (`export const api`) y registro global en `window.api` si `window` está definido, y verificar que no arroje errores de sintaxis.

## 2. Normalización de Endpoints y Construcción de URLs

- [x] 2.1 Implementar la función de normalización de URLs asegurando el prefijo obligatorio `/api/` y la preservación de barra final en colecciones, verificando casos sin barra, con barra y con identificadores numéricos.
- [x] 2.2 Incorporar serialización de parámetros de consulta (`query params`) utilizando `URLSearchParams`, verificando que parámetros como `{ limit: 20, offset: 0, titulo: "faro" }` generen la query string correspondiente.

## 3. Métodos HTTP y Deserialización de Respuestas

- [x] 3.1 Implementar `api.get(endpoint, params)` configurando método GET y cabecera `Accept: application/json`, verificando la deserialización automática del JSON devuelto en respuestas exitosas (200 OK).
- [x] 3.2 Implementar `api.post(endpoint, body)` y `api.patch(endpoint, body)` inyectando cabeceras `Content-Type: application/json` y serializando el cuerpo con `JSON.stringify`, verificando la recepción de respuestas exitosas (201 Created y 200 OK).

## 4. Captura y Tipificación de Errores HTTP y de Red

- [x] 4.1 Implementar el interceptor de errores HTTP extrayendo el mensaje de `detail` para respuestas `409 Conflict` (duplicados de ISBN/email) y `404 Not Found`, verificando que lance `ApiError` con status y mensaje exacto.
- [x] 4.2 Implementar el formateo de errores de validación de contrato `422 Unprocessable Entity` extrayendo la lista de fallos de campo, verificando que `ApiError.data` contenga el detalle estructurado.
- [x] 4.3 Implementar la captura de fallas de conexión (red caída, timeout o 502 Bad Gateway) retornando un `ApiError` con status 0 y mensaje descriptivo sin romper la interfaz.

## 5. Verificación Automatizada y Vinculación

- [x] 5.1 Crear script de pruebas unitarias/integración en `frontend/public/js/api.test.js` o runner local cubriendo los casos de URLs, métodos GET/POST/PATCH y errores 409/422/red, y verificar ejecución exitosa de todos los casos.
- [x] 5.2 Incluir `api.js` en `frontend/public/index.html` asegurando disponibilidad para las pantallas del catálogo y formularios, y verificar la carga limpia en el navegador.

## Workflow follow-up

- Archivar el change `c-02-http-client-base` tras completar la implementación y verificación.
- Marcar el checkbox correspondiente a `[C-02]` en `CHANGES.md`.
