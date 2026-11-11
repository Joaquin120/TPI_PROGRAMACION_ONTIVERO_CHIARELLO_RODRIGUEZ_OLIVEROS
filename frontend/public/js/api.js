/**
 * Cliente HTTP centralizado en JavaScript nativo para la Librería El Faro de los Libros.
 * Provee normalización de URLs con prefijo /api/, manejo de trailing slashes,
 * cabeceras JSON automáticas y tipificación estructurada de errores mediante ApiError.
 */

class ApiError extends Error {
  constructor(message, status = 500, data = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Normaliza y construye URLs para solicitudes a la API.
 * - Asegura prefijo /api/ sin duplicar.
 * - Agrega barra final en endpoints de colección, pero no en IDs numéricos.
 * - Serializa parámetros de consulta (query params).
 *
 * @param {string} endpoint
 * @param {Record<string, any>|null} [params=null]
 * @returns {string}
 */
function buildUrl(endpoint, params = null) {
  if (typeof endpoint !== 'string') {
    throw new TypeError('Endpoint must be a string');
  }

  // Quitar barras iniciales redundantes y prefijo /api redundante
  let cleanPath = endpoint.trim().replace(/^\/+/, '');
  if (cleanPath === 'api') {
    cleanPath = '';
  } else if (cleanPath.startsWith('api/')) {
    cleanPath = cleanPath.slice(4);
  }

  // Prefijo base /api/
  let url = cleanPath ? `/api/${cleanPath}` : '/api/';

  // Evaluar último segmento sin barra final
  const trimmedUrl = url.replace(/\/+$/, '');
  const segments = trimmedUrl.split('/');
  const lastSegment = segments[segments.length - 1];

  // Si el último segmento es puramente numérico (ID de recurso individual), no forzar barra final
  const isNumeric = /^\d+$/.test(lastSegment);

  if (isNumeric) {
    url = trimmedUrl;
  } else if (!url.endsWith('/')) {
    url += '/';
  }

  // Serializar query parameters si fueron provistos
  if (params && typeof params === 'object') {
    const search = new URLSearchParams(params).toString();
    if (search) {
      url += `?${search}`;
    }
  }

  return url;
}

/**
 * Ejecuta una petición HTTP fetch con manejo tipificado de respuestas y errores.
 *
 * @param {string} endpoint
 * @param {RequestInit & { params?: Record<string, any> }} [options={}]
 * @returns {Promise<any>}
 */
async function request(endpoint, options = {}) {
  const {
    params = null,
    body = null,
    method = 'GET',
    headers: customHeaders = {},
    ...restOptions
  } = options;

  const url = buildUrl(endpoint, params);

  const headers = {
    Accept: 'application/json',
    ...customHeaders
  };

  let serializedBody = body;
  if (body !== null && typeof body === 'object') {
    serializedBody = JSON.stringify(body);
    headers['Content-Type'] = 'application/json';
  }

  const fetchOptions = {
    method: method.toUpperCase(),
    headers,
    ...restOptions
  };

  if (serializedBody !== null && serializedBody !== undefined) {
    fetchOptions.body = serializedBody;
  }

  let response;
  try {
    response = await fetch(url, fetchOptions);
  } catch (err) {
    throw new ApiError(
      'No se pudo conectar con el servidor. Verifique su conexión de red.',
      0,
      null
    );
  }

  if (response.status === 204) {
    return null;
  }

  if (response.ok) {
    return await response.json();
  }

  let errorData = null;
  try {
    errorData = await response.json();
  } catch (_) {
    try {
      errorData = await response.text();
    } catch (_) {}
  }

  if (response.status === 409) {
    const message = (errorData && typeof errorData.detail === 'string')
      ? errorData.detail
      : 'Conflicto en la solicitud.';
    throw new ApiError(message, 409, errorData);
  }

  if (response.status === 422) {
    const detail = (errorData && errorData.detail !== undefined)
      ? errorData.detail
      : errorData;
    throw new ApiError('Error de validación en los datos enviados.', 422, detail);
  }

  const detailString = (errorData && typeof errorData.detail === 'string')
    ? errorData.detail
    : (typeof errorData === 'string' && errorData.trim() ? errorData : null);

  const message = detailString || `Error HTTP ${response.status}`;
  throw new ApiError(message, response.status, errorData);
}

const api = {
  ApiError,
  buildUrl,
  request,
  get(endpoint, params = null, options = {}) {
    return request(endpoint, { ...options, method: 'GET', params });
  },
  post(endpoint, body = null, options = {}) {
    return request(endpoint, { ...options, method: 'POST', body });
  },
  patch(endpoint, body = null, options = {}) {
    return request(endpoint, { ...options, method: 'PATCH', body });
  }
};

// Exposición global en navegador
if (typeof window !== 'undefined') {
  window.ApiError = ApiError;
  window.api = api;
}

// Exportación para entornos CommonJS (Node.js)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { ApiError, api };
}

// Exportación modular ES6
export { ApiError, api };
