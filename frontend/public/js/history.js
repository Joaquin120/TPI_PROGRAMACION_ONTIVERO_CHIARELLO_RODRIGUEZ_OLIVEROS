/**
 * Módulo de Historial y Detalle Inmutable de Ventas (Ejercicio 3B / C-07 / US-008).
 * Consume GET /api/ventas/?limit=20&offset=0 y GET /api/ventas/{id} sin uso de localStorage.
 * Garantiza la visualización inmutable de precios unitarios congelados, subtotales y total.
 */

import { api as defaultApi, ApiError } from './api.js';

export const estadoHistorial = {
  ventas: [],
  ventaSeleccionada: null,
  limit: 20,
  offset: 0,
  cargando: false,
};

/**
 * Formatea un importe numérico con dos decimales y coma ($1500,00).
 * @param {number|string} valor
 * @returns {string}
 */
export function formatearPrecioHistorial(valor) {
  const num = typeof valor === 'number' ? valor : parseFloat(valor);
  if (isNaN(num)) return '$0,00';
  return '$' + num.toFixed(2).replace('.', ',');
}

/**
 * Formatea una marca de tiempo ISO en fecha y hora legible (dd/mm/yyyy HH:mm).
 * @param {string|Date} fechaIso
 * @returns {string}
 */
export function formatearFechaHora(fechaIso) {
  if (!fechaIso) return '—';
  const fecha = fechaIso instanceof Date ? fechaIso : new Date(fechaIso);
  if (isNaN(fecha.getTime())) {
    return String(fechaIso);
  }
  try {
    return new Intl.DateTimeFormat('es-AR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).format(fecha);
  } catch (_) {
    return fecha.toISOString();
  }
}

/**
 * Genera el identificador visual estándar de una venta (ej. V-0001).
 * @param {number|string} id
 * @returns {string}
 */
export function formatearCodigoVenta(id) {
  const num = parseInt(id, 10);
  if (isNaN(num)) return String(id || '');
  return `V-${String(num).padStart(4, '0')}`;
}

/**
 * Construye una fila <tr> del historial de ventas con botón para consultar su detalle.
 * @param {Object} venta
 * @param {(ventaId: number) => void} [onVerDetalle]
 * @param {Document|Object} [doc=document]
 * @returns {HTMLTableRowElement}
 */
export function crearFilaVentaHistorial(venta, onVerDetalle, doc = document) {
  const tr = doc.createElement('tr');

  const tdId = doc.createElement('td');
  tdId.textContent = formatearCodigoVenta(venta.id);
  tr.appendChild(tdId);

  const tdFecha = doc.createElement('td');
  tdFecha.textContent = formatearFechaHora(venta.fecha);
  tr.appendChild(tdFecha);

  const tdCliente = doc.createElement('td');
  tdCliente.textContent = venta.cliente_nombre || `Cliente #${venta.cliente_id}`;
  tr.appendChild(tdCliente);

  const tdTotal = doc.createElement('td');
  tdTotal.textContent = formatearPrecioHistorial(venta.total);
  tr.appendChild(tdTotal);

  const tdDetalle = doc.createElement('td');
  const btnDetalle = doc.createElement('button');
  btnDetalle.type = 'button';
  btnDetalle.className = 'historial-ver-detalle';
  btnDetalle.dataset.idVenta = String(venta.id);
  btnDetalle.textContent = `Ver detalle (${formatearCodigoVenta(venta.id)})`;
  btnDetalle.setAttribute('aria-label', `Ver detalle de la venta ${formatearCodigoVenta(venta.id)}`);

  if (typeof onVerDetalle === 'function') {
    btnDetalle.addEventListener('click', () => onVerDetalle(venta.id));
  }

  tdDetalle.appendChild(btnDetalle);
  tr.appendChild(tdDetalle);

  return tr;
}

/**
 * Actualiza los botones e indicador de página de #historial-paginacion.
 * @param {number} cantidadEnPagina
 * @param {Document|Object} [doc=document]
 */
export function actualizarPaginacionHistorialDom(cantidadEnPagina, doc = document) {
  if (!doc) return;

  const btnAnterior = doc.getElementById('historial-anterior');
  const btnSiguiente = doc.getElementById('historial-siguiente');
  const infoEl = doc.getElementById('historial-info-paginacion');
  const selectLimite = doc.getElementById('historial-limite');

  const paginaActual = Math.floor(estadoHistorial.offset / estadoHistorial.limit) + 1;

  if (btnAnterior) {
    btnAnterior.disabled = estadoHistorial.offset <= 0;
  }
  if (btnSiguiente) {
    btnSiguiente.disabled = cantidadEnPagina < estadoHistorial.limit;
  }
  if (infoEl) {
    infoEl.textContent = `Página ${paginaActual}`;
  }
  if (selectLimite) {
    selectLimite.value = String(estadoHistorial.limit);
  }
}

/**
 * Renderiza el panel de detalle histórico e inmutable de una venta seleccionada.
 * Si venta es null o undefined, muestra el estado vacío sin controles de edición/eliminación.
 * @param {Object|null} venta
 * @param {Document|Object} [doc=document]
 */
export function renderizarDetalleVenta(venta, doc = document) {
  if (!doc) return;
  const contenedor = doc.getElementById('tabla-historial-detalle');
  if (!contenedor) return;

  contenedor.innerHTML = '';
  if (Array.isArray(contenedor.children)) {
    contenedor.children = [];
  }

  if (!venta) {
    const aviso = doc.createElement('p');
    aviso.className = 'listado-vacio';
    aviso.textContent = 'Seleccione una venta del historial para ver su detalle.';
    contenedor.appendChild(aviso);
    return;
  }

  // Cabecera resumen de la venta histórica
  const cabecera = doc.createElement('div');
  cabecera.className = 'detalle-venta-cabecera';

  const pVenta = doc.createElement('p');
  pVenta.textContent = `Comprobante: ${formatearCodigoVenta(venta.id)} (ID #${venta.id})`;
  cabecera.appendChild(pVenta);

  const pCliente = doc.createElement('p');
  pCliente.textContent = `Cliente: ${venta.cliente_nombre || `Cliente #${venta.cliente_id}`}`;
  cabecera.appendChild(pCliente);

  const pFecha = doc.createElement('p');
  pFecha.textContent = `Fecha y hora: ${formatearFechaHora(venta.fecha)}`;
  cabecera.appendChild(pFecha);

  contenedor.appendChild(cabecera);

  // Tabla inmutable de renglones históricos
  const tablaContenedor = doc.createElement('div');
  tablaContenedor.className = 'tabla-contenedor';

  const tabla = doc.createElement('table');
  const caption = doc.createElement('caption');
  caption.textContent = `Renglones de la venta ${formatearCodigoVenta(venta.id)} (valores históricos congelados)`;
  tabla.appendChild(caption);

  const thead = doc.createElement('thead');
  const trHead = doc.createElement('tr');
  ['Libro', 'Cantidad', 'Precio unitario', 'Subtotal'].forEach((texto) => {
    const th = doc.createElement('th');
    th.scope = 'col';
    th.textContent = texto;
    trHead.appendChild(th);
  });
  thead.appendChild(trHead);
  tabla.appendChild(thead);

  const tbody = doc.createElement('tbody');
  const renglones = Array.isArray(venta.renglones) ? venta.renglones : [];
  renglones.forEach((renglon) => {
    const tr = doc.createElement('tr');

    const tdLibro = doc.createElement('td');
    tdLibro.textContent = renglon.titulo || `Libro #${renglon.libro_id}`;
    tr.appendChild(tdLibro);

    const tdCant = doc.createElement('td');
    tdCant.textContent = String(renglon.cantidad);
    tr.appendChild(tdCant);

    const tdPrecio = doc.createElement('td');
    tdPrecio.textContent = formatearPrecioHistorial(renglon.precio_unitario);
    tr.appendChild(tdPrecio);

    const tdSub = doc.createElement('td');
    tdSub.textContent = formatearPrecioHistorial(renglon.subtotal);
    tr.appendChild(tdSub);

    tbody.appendChild(tr);
  });
  tabla.appendChild(tbody);

  const tfoot = doc.createElement('tfoot');
  const trFoot = doc.createElement('tr');
  const thTotal = doc.createElement('th');
  thTotal.scope = 'row';
  thTotal.setAttribute('colspan', '3');
  thTotal.textContent = 'Total de la venta';
  trFoot.appendChild(thTotal);

  const tdTotal = doc.createElement('td');
  tdTotal.textContent = formatearPrecioHistorial(venta.total);
  trFoot.appendChild(tdTotal);

  tfoot.appendChild(trFoot);
  tabla.appendChild(tfoot);

  tablaContenedor.appendChild(tabla);
  contenedor.appendChild(tablaContenedor);
}

/**
 * Consulta GET /api/ventas/{id} y renderiza el detalle histórico en pantalla.
 * @param {number|string} ventaId
 * @param {Object} [opciones={}]
 * @returns {Promise<Object|null>}
 */
export async function cargarDetalleVenta(ventaId, opciones = {}) {
  const client = opciones.apiClient || (typeof window !== 'undefined' ? window.api : defaultApi);
  const doc = opciones.context || (typeof document !== 'undefined' ? document : null);
  if (!doc) return null;

  const idNum = parseInt(ventaId, 10);
  if (isNaN(idNum) || idNum <= 0) return null;

  const errorEl = doc.getElementById('historial-error');
  if (errorEl) {
    errorEl.hidden = true;
    errorEl.textContent = '';
  }

  try {
    const venta = await client.get(`/ventas/${idNum}`);
    estadoHistorial.ventaSeleccionada = venta;
    renderizarDetalleVenta(venta, doc);
    return venta;
  } catch (err) {
    const mensaje = err instanceof ApiError ? err.message : (err.message || 'No se pudo obtener el detalle');
    if (errorEl) {
      errorEl.textContent = `Error al consultar detalle de venta #${idNum}: ${mensaje}`;
      errorEl.hidden = false;
    }
    throw err;
  }
}

/**
 * Consulta GET /api/ventas/?limit=&offset= y renderiza la tabla de historial paginada.
 * @param {Object} [opciones={}]
 * @returns {Promise<Array<Object>>}
 */
export async function cargarHistorialVentas(opciones = {}) {
  const client = opciones.apiClient || (typeof window !== 'undefined' ? window.api : defaultApi);
  const doc = opciones.context || (typeof document !== 'undefined' ? document : null);
  if (!doc) return [];

  const loadingEl = doc.getElementById('historial-cargando');
  const vacioEl = doc.getElementById('historial-listado-vacio');
  const errorEl = doc.getElementById('historial-error');
  const tablaContenedor = doc.getElementById('historial-tabla-contenedor');
  const tabla = doc.getElementById('tabla-historial');
  const tbody = tabla && tabla.querySelector ? tabla.querySelector('tbody') : null;

  estadoHistorial.cargando = true;
  if (loadingEl) loadingEl.hidden = false;
  if (vacioEl) vacioEl.hidden = true;
  if (errorEl) {
    errorEl.hidden = true;
    errorEl.textContent = '';
  }
  if (tablaContenedor) tablaContenedor.hidden = true;

  try {
    const data = await client.get('/ventas/', {
      limit: estadoHistorial.limit,
      offset: estadoHistorial.offset,
    });
    estadoHistorial.cargando = false;
    if (loadingEl) loadingEl.hidden = true;

    const lista = Array.isArray(data) ? data : [];
    estadoHistorial.ventas = lista;

    if (tbody) {
      tbody.innerHTML = '';
      if (Array.isArray(tbody.children)) {
        tbody.children = [];
      }
    }

    if (lista.length === 0) {
      if (vacioEl) vacioEl.hidden = false;
      actualizarPaginacionHistorialDom(0, doc);
      return [];
    }

    if (tbody) {
      lista.forEach((venta) => {
        const fila = crearFilaVentaHistorial(
          venta,
          (id) => cargarDetalleVenta(id, { apiClient: client, context: doc }),
          doc,
        );
        tbody.appendChild(fila);
      });
    }

    if (tablaContenedor) tablaContenedor.hidden = false;
    actualizarPaginacionHistorialDom(lista.length, doc);
    return lista;
  } catch (err) {
    estadoHistorial.cargando = false;
    if (loadingEl) loadingEl.hidden = true;
    if (errorEl) {
      errorEl.textContent = 'Error de conexión al cargar el historial de ventas: ' + (err.message || 'Falla de red');
      errorEl.hidden = false;
    }
    actualizarPaginacionHistorialDom(0, doc);
    throw err;
  }
}

export async function avanzarPaginaHistorial(opciones = {}) {
  estadoHistorial.offset += estadoHistorial.limit;
  return cargarHistorialVentas(opciones);
}

export async function retrocederPaginaHistorial(opciones = {}) {
  estadoHistorial.offset = Math.max(0, estadoHistorial.offset - estadoHistorial.limit);
  return cargarHistorialVentas(opciones);
}

export async function cambiarLimiteHistorial(nuevoLimite, opciones = {}) {
  const num = parseInt(nuevoLimite, 10);
  if (!isNaN(num) && num >= 1 && num <= 100) {
    estadoHistorial.limit = num;
    estadoHistorial.offset = 0;
  }
  return cargarHistorialVentas(opciones);
}

/**
 * Inicializa los controles de paginación y panel inicial del historial de ventas.
 * @param {Object} [opciones={}]
 */
export function inicializarEventosHistorial(opciones = {}) {
  const doc = opciones.context || (typeof document !== 'undefined' ? document : null);
  if (!doc) return;

  const btnAnterior = doc.getElementById('historial-anterior');
  const btnSiguiente = doc.getElementById('historial-siguiente');
  const selectLimite = doc.getElementById('historial-limite');

  if (btnAnterior && !btnAnterior.dataset.historyInitialized) {
    btnAnterior.addEventListener('click', () => retrocederPaginaHistorial(opciones));
    btnAnterior.dataset.historyInitialized = 'true';
  }

  if (btnSiguiente && !btnSiguiente.dataset.historyInitialized) {
    btnSiguiente.addEventListener('click', () => avanzarPaginaHistorial(opciones));
    btnSiguiente.dataset.historyInitialized = 'true';
  }

  if (selectLimite && !selectLimite.dataset.historyInitialized) {
    selectLimite.addEventListener('change', (e) => cambiarLimiteHistorial(e.target.value, opciones));
    selectLimite.dataset.historyInitialized = 'true';
  }

  renderizarDetalleVenta(estadoHistorial.ventaSeleccionada, doc);
}

if (typeof window !== 'undefined') {
  window.historyVentas = {
    estadoHistorial,
    formatearPrecioHistorial,
    formatearFechaHora,
    formatearCodigoVenta,
    cargarHistorialVentas,
    cargarDetalleVenta,
    renderizarDetalleVenta,
    avanzarPaginaHistorial,
    retrocederPaginaHistorial,
    cambiarLimiteHistorial,
    inicializarEventosHistorial,
  };
}
