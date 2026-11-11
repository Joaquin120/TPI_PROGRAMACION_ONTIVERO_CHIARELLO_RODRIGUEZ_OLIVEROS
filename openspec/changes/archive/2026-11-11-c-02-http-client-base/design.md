# Design: C-02 HTTP Client Base

## Context
En el Parcial 1, el frontend interactuaba contra variables locales en memoria y simulaciones en `frontend/public/js/app.js`. En este TPI Integrador, todas las operaciones de catálogo, altas y ventas deben comunicarse con el backend FastAPI a través del proxy Nginx en `/api/`. Crear un cliente HTTP centralizado en JavaScript nativo (`frontend/public/js/api.js`) establece una única fuente de verdad para el manejo de URLs, serialización, cabeceras y control de errores.

## Goals / Non-Goals

**Goals:**
- Implementar `frontend/public/js/api.js` en JavaScript nativo (ES6 Modules) sin dependencias ni librerías de terceros (Vanilla JS).
- Centralizar la URL base en `/api/` y normalizar automáticamente endpoints para respetar la convención de barra final (`trailing slash`) en colecciones (ej: `/api/libros/`).
- Proveer métodos helpers claros: `api.get(endpoint, params)`, `api.post(endpoint, body)` y `api.patch(endpoint, body)`.
- Diseñar una clase estructurada `ApiError` que capture el código HTTP (`400`, `404`, `409`, `422`, `500`), el mensaje del servidor y los detalles de validación de FastAPI.
- Manejar fallas de transporte (red caída, timeout, 502 Bad Gateway) retornando un `ApiError` descriptivo (`status: 0` o `502`) sin romper la ejecución de la UI.
- Diseñar compatibilidad dual: exportación modular ES6 y exposición opcional en `window.api` para facilitar su adopción en `index.html`.

**Non-Goals:**
- Implementar la lógica de negocio visual de catálogo, formularios o carrito (objeto de `C-03` a `C-07`).
- Usar librerías externas como Axios, jQuery o Axios-like bundlers.
- Implementar almacenamiento local o caché en `localStorage` (prohibido por la Regla Dura #1).

## Decisions

### 1. JavaScript Nativo (Vanilla JS) con Compatibilidad Dual (ES6 y Global)
- **Decisión**: Implementar `api.js` usando ES6 (`export const api = ...`) y, al mismo tiempo, asignar condicionalmente `if (typeof window !== 'undefined') window.api = api;`.
- **Razón**: Permite importar el cliente como módulo (`import { api } from './api.js'`) en arquitecturas modulares o consumirlo directamente desde scripts convencionales en `index.html` sin obligar a un bundler ni a refactorizar de golpe todos los scripts.
- **Alternativa considerada**: Exigir bundlers (Webpack, Vite). Se descartó porque la consigna exige explícitamente HTML/JS nativo sin herramientas de compilación.

### 2. Normalización de Endpoints y Trailing Slash
- **Decisión**: El método interno `buildUrl(endpoint, params)`:
  1. Asegura que el prefijo comience con `/api/` (si no lo tiene, lo añade).
  2. Si el endpoint representa una colección (no termina en un ID o subrecurso específico) y no termina en `/`, le agrega automáticamente `/`.
  3. Convierte objetos de parámetros (`params`) en una cadena de búsqueda con `URLSearchParams` (ej: `?limit=20&offset=0`).
- **Razón**: FastAPI implementa redirecciones HTTP 307 hacia la barra final en colecciones. Si el navegador realiza un `POST` o `GET` sin barra final a una colección, puede fallar o perder cabeceras en la redirección. La normalización previene este defecto de raíz.
- **Alternativa considerada**: Dejar la responsabilidad a cada vista de escribir la barra final. Se descartó por ser propensa a omisiones y errores humanos.

### 3. Modelo Estructurado de Errores (`ApiError`)
- **Decisión**: Definir la clase:
  ```javascript
  class ApiError extends Error {
    constructor(message, status, data = null) {
      super(message);
      this.name = 'ApiError';
      this.status = status;
      this.data = data;
    }
  }
  ```
  y capturar los formatos estándar de error de FastAPI (`detail` como string para 409/404 o `detail` como array de errores de validación para 422).
- **Razón**: Cumple con la Regla Dura #5, permitiendo que los formularios posteriores muestren errores amigables (ej: "El ISBN ya se encuentra registrado") sin limpiar los campos ni cerrar modales.
- **Alternativa considerada**: Retornar `null` o booleanos en caso de error. Se descartó porque se pierde el código de estado y el mensaje de error provisto por el backend.

### 4. Cabeceras JSON Predeterminadas
- **Decisión**: Inyectar en cada petición:
  - `Accept: application/json`
  - `Content-Type: application/json` (en peticiones con body: POST, PATCH, PUT).
- **Razón**: Evita que FastAPI interprete el cuerpo como texto plano o formulario codificado en URL.

## Risks / Trade-offs

- **[Riesgo: Fallo de red (Failed to fetch) arroja una excepción nativa no controlada]**  
  → *Mitigación*: Envolver cada llamada `fetch` en un bloque `try/catch` que intercepte excepciones de red y lance un `ApiError("No se pudo conectar con el servidor. Verifique su conexión de red.", 0)`.
- **[Riesgo: Confusión entre endpoints con ID (/libros/1) y endpoints de colección (/libros/)]**  
  → *Mitigación*: La lógica de `buildUrl` analiza el último segmento: si es numérico (un ID), no añade barra final forzada; si es una colección, asegura la barra final.

## Migration Plan
1. Crear `frontend/public/js/api.js` con la clase `ApiError` y los métodos `get`, `post`, `patch`.
2. Crear un script de pruebas unitarias/integración para `api.js` verificando resolución de URLs, cabeceras, respuestas JSON y captura de errores 409/422.
3. Vincular `api.js` en `frontend/public/index.html` asegurando disponibilidad global y modular.
