# Proposal: C-02 HTTP Client Base

## Why
En el primer parcial, el frontend operaba de forma aislada simulando la persistencia en memoria local y `localStorage`. Para satisfacer el objetivo fundacional del TPI de conectar las pantallas con la API REST de FastAPI a través del proxy inverso de Nginx, se necesita un módulo cliente HTTP centralizado en JavaScript nativo (`frontend/public/js/api.js`). Este módulo abstrae las peticiones `fetch`, garantiza el prefijo obligatorio `/api/` y la preservación de barras finales (`trailing slash`) en rutas de colección, e implementa el manejo unificado de errores de negocio (`409 Conflict`, `422 Unprocessable Entity`) y fallas de red, evitando código repetitivo y violaciones de contrato en las vistas posteriores.

## What Changes
- **Módulo Cliente HTTP (`frontend/public/js/api.js`)**: Creación de un módulo JavaScript ES6 nativo que encapsula la API `fetch` del navegador bajo una interfaz uniforme (`api.get`, `api.post`, `api.patch`).
- **Enrutamiento y Prefijo `/api/`**: Estandarización de la URL base prefijada en `/api/` para todas las llamadas del frontend, respetando la directiva de proxy de Nginx (`C-08`).
- **Normalización de Barras Finales**: Normalización de endpoints de colección (ej: `/libros/`, `/clientes/`, `/ventas/`) para asegurar que siempre conserven la barra final requerida por FastAPI para evitar redirecciones 307 accidentales.
- **Cabeceras Uniformes**: Configuración automática de cabeceras `Content-Type: application/json` y `Accept: application/json` en todas las solicitudes que envían o reciben payloads.
- **Manejo Centralizado de Respuestas y Errores**: Deserialización automática de JSON y captura estructurada de códigos HTTP de negocio (`409 Conflict` para duplicados, `422 Unprocessable Entity` para errores de validación de esquemas) y errores de servidor o transporte (red desconectada o 502 Bad Gateway), retornando objetos de error claros y amigables para la UI sin arrojar excepciones no controladas.
- **Conjunto de Pruebas Unitarias/Integración**: Validación del módulo `api.js` mediante suite de pruebas en el frontend o runner local comprobando el comportamiento ante respuestas exitosas (200, 201), errores de validación y fallas de transporte.

## Capabilities

### New Capabilities
- `frontend-http-client`: Módulo cliente HTTP centralizado en JavaScript nativo que gestiona peticiones REST mediante `fetch`, control de prefijo `/api/`, preservación de trailing slash, cabeceras estándar y formateo amigable de errores HTTP y de red.

### Modified Capabilities
*(Ninguna)*

## Impact
- **Frontend**: Provee la capa de abstracción HTTP que consumirán las vistas de catálogo (`C-03`), altas (`C-04`, `C-05`) y ventas (`C-06`, `C-07`). Desacopla la lógica de presentación de los detalles de `fetch`.
- **Backend**: Recibe peticiones HTTP con cabeceras y rutas estandarizadas a través del proxy Nginx.
- **Reglas Duras**: Hace cumplir la Regla Dura #1 (no usar localStorage para persistencia confirmada), la Regla Dura #2 (prefijo obligatorio `/api/` y trailing slash) y la Regla Dura #5 (presentación amigable de errores 409 y 422 sin perder datos).
