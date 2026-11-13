/**
 * Módulo para la Gestión y Alta de Clientes (Ejercicio 2B / US-005).
 * Maneja la validación sintáctica de datos, envío a POST /api/clientes/,
 * renderizado del listado de clientes, sincronización del selector de ventas
 * y consulta individual por identificador.
 */

import { api as defaultApi, ApiError } from './api.js';

export const estadoClientes = {
  clientes: [],
  cargando: false,
  enviando: false,
};

const EMAIL_REGEX = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;

/**
 * Valida si una cadena cumple con el formato estándar de correo electrónico.
 * @param {string} email
 * @returns {boolean}
 */
export function validarEmail(email) {
  if (!email || typeof email !== 'string') return false;
  return EMAIL_REGEX.test(email.trim());
}

/**
 * Valida los datos requeridos para el alta de un cliente (RN-CLI-02).
 * @param {Object} datos
 * @param {string} datos.nombre
 * @param {string} datos.email
 * @returns {{ valido: boolean, error: string | null }}
 */
export function validarDatosCliente({ nombre, email }) {
  const nombreLimpio = typeof nombre === 'string' ? nombre.trim() : '';
  const emailLimpio = typeof email === 'string' ? email.trim() : '';

  if (!nombreLimpio) {
    return { valido: false, error: 'El nombre completo es obligatorio.' };
  }

  if (!emailLimpio) {
    return { valido: false, error: 'El correo electrónico es obligatorio.' };
  }

  if (!validarEmail(emailLimpio)) {
    return { valido: false, error: 'El formato de correo electrónico no es válido.' };
  }

  return { valido: true, error: null };
}

/**
 * Renderiza la lista de clientes en la tabla del DOM y gestiona el estado vacío.
 * @param {Array<Object>} clientes
 * @param {Document|Object} doc
 */
export function renderizarTablaClientes(clientes, doc) {
  if (!doc) return;

  const tabla = doc.getElementById('tabla-clientes');
  const avisoVacio = doc.getElementById('clientes-listado-vacio');
  if (!tabla) return;

  const tbody = tabla.querySelector('tbody');
  if (!tbody) return;

  tbody.innerHTML = '';

  if (!clientes || clientes.length === 0) {
    if (avisoVacio) avisoVacio.hidden = false;
    return;
  }

  if (avisoVacio) avisoVacio.hidden = true;

  clientes.forEach((cliente) => {
    const tr = doc.createElement('tr');

    const tdNombre = doc.createElement('td');
    tdNombre.textContent = cliente.nombre;
    tr.appendChild(tdNombre);

    const tdEmail = doc.createElement('td');
    tdEmail.textContent = cliente.email;
    tr.appendChild(tdEmail);

    tbody.appendChild(tr);
  });
}

/**
 * Sincroniza las opciones del selector de clientes en la sección de ventas (#venta-cliente).
 * @param {Array<Object>} clientes
 * @param {Document|Object} doc
 */
export function sincronizarSelectorVentas(clientes, doc) {
  if (!doc) return;
  const selectVentas = doc.getElementById('venta-cliente');
  if (!selectVentas) return;

  selectVentas.innerHTML = '';
  if (Array.isArray(selectVentas.children)) {
    selectVentas.children = [];
  }

  const defaultOpt = doc.createElement('option');
  defaultOpt.value = '';
  defaultOpt.textContent = 'Seleccione un cliente';
  defaultOpt.disabled = true;
  defaultOpt.selected = true;
  selectVentas.appendChild(defaultOpt);

  if (Array.isArray(clientes)) {
    clientes.forEach((cliente) => {
      const opt = doc.createElement('option');
      opt.value = cliente.id;
      opt.textContent = cliente.nombre;
      selectVentas.appendChild(opt);
    });
  }
}

/**
 * Consulta un cliente por su identificador único (GET /api/clientes/{id}).
 * @param {number|string} id
 * @param {Object} [opciones={}]
 * @returns {Promise<Object>}
 */
export async function consultarClientePorId(id, opciones = {}) {
  const client = opciones.apiClient || (typeof window !== 'undefined' ? window.api : defaultApi);
  return await client.get(`/clientes/${id}`);
}

/**
 * Carga el listado de clientes desde la API y actualiza la tabla y selector de ventas.
 * @param {Object} [opciones={}]
 * @param {any} [opciones.apiClient=defaultApi]
 * @param {Document|Object} [opciones.context=document]
 */
export async function cargarClientes(opciones = {}) {
  const client = opciones.apiClient || (typeof window !== 'undefined' ? window.api : defaultApi);
  const doc = opciones.context || (typeof document !== 'undefined' ? document : null);

  estadoClientes.cargando = true;
  try {
    const data = await client.get('/clientes/');
    estadoClientes.clientes = Array.isArray(data) ? data : [];
    if (doc) {
      renderizarTablaClientes(estadoClientes.clientes, doc);
      sincronizarSelectorVentas(estadoClientes.clientes, doc);
    }
    return estadoClientes.clientes;
  } catch (err) {
    console.error('Error al cargar clientes:', err);
    throw err;
  } finally {
    estadoClientes.cargando = false;
  }
}

/**
 * Procesa el envío del formulario de alta de cliente con feedback y preservación ante 409/422.
 * @param {Object} [opciones={}]
 * @param {any} [opciones.apiClient=defaultApi]
 * @param {Document|Object} [opciones.context=document]
 * @returns {Promise<{ exito: boolean, error?: string, cliente?: Object }>}
 */
export async function enviarAltaCliente(opciones = {}) {
  const client = opciones.apiClient || (typeof window !== 'undefined' ? window.api : defaultApi);
  const doc = opciones.context || (typeof document !== 'undefined' ? document : null);
  if (!doc) return { exito: false, error: 'No DOM context' };

  const form = doc.getElementById('form-alta-cliente');
  const inputNombre = doc.getElementById('cliente-nombre');
  const inputEmail = doc.getElementById('cliente-email');
  const feedback = doc.getElementById('clientes-feedback');
  const btnSubmit = form ? form.querySelector('button[type="submit"]') : null;

  const nombre = inputNombre ? inputNombre.value.trim() : '';
  const email = inputEmail ? inputEmail.value.trim() : '';

  // 1. Validación en cliente antes del despacho de red (RN-CLI-02)
  const validacion = validarDatosCliente({ nombre, email });
  if (!validacion.valido) {
    if (feedback) {
      feedback.hidden = false;
      feedback.textContent = `Error — ${validacion.error}`;
      feedback.classList.remove('mensaje-exito');
      feedback.classList.add('mensaje-error');
    }
    return { exito: false, error: validacion.error };
  }

  // 2. Despacho HTTP con bloqueo transitorio del botón
  estadoClientes.enviando = true;
  if (btnSubmit) btnSubmit.disabled = true;

  try {
    const nuevoCliente = await client.post('/clientes/', { nombre, email });

    // Éxito (201 Created)
    if (feedback) {
      feedback.hidden = false;
      feedback.textContent = 'OK — Cliente registrado correctamente.';
      feedback.classList.remove('mensaje-error');
      feedback.classList.add('mensaje-exito');
    }

    if (form && typeof form.reset === 'function') {
      form.reset();
    }

    // Refrescar listado y selector de ventas reactivamente
    try {
      await cargarClientes(opciones);
    } catch (_) {
      // Ignorar si falla el refresco en entorno mock
    }

    return { exito: true, cliente: nuevoCliente };
  } catch (err) {
    // Conflicto (409 Conflict) o Validación (422 Unprocessable Entity)
    // PRESERVACIÓN ESTRICTA: los campos no se resetean ni se limpian (RN-CLI-01)
    const mensajeError = err instanceof ApiError ? err.message : (err.message || 'Error desconocido');

    if (feedback) {
      feedback.hidden = false;
      feedback.textContent = `Error — ${mensajeError}`;
      feedback.classList.remove('mensaje-exito');
      feedback.classList.add('mensaje-error');
    }

    return { exito: false, error: mensajeError };
  } finally {
    estadoClientes.enviando = false;
    if (btnSubmit) btnSubmit.disabled = false;
  }
}

/**
 * Inicializa los eventos del módulo de clientes en la interfaz de usuario.
 * @param {Object} [opciones={}]
 */
export function inicializarEventosClientes(opciones = {}) {
  const doc = opciones.context || (typeof document !== 'undefined' ? document : null);
  if (!doc) return;

  const form = doc.getElementById('form-alta-cliente');
  if (form && !form.dataset.initialized) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      await enviarAltaCliente(opciones);
    });
    form.dataset.initialized = 'true';
  }

  // Cargar clientes inicialmente si la vista está activa o al inicializar
  cargarClientes(opciones).catch(() => {});
}
