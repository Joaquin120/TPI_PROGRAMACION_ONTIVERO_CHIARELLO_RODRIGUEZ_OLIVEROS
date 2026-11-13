/**
 * Módulo de Composición y Registro de Ventas (Ejercicio 5 / C-06).
 * Gestiona el borrador en memoria de la venta, validación de cantidades (RN-VEN-03),
 * unicidad de libros por renglón (RN-VEN-04), cálculo de subtotales y total,
 * renderizado dinámico de la tabla de renglones, y confirmación transaccional
 * vía POST /api/ventas/ con bloqueo del botón (RN-VEN-07) y preservación
 * estricta del borrador ante respuestas 409/422 (RN-VEN-08).
 *
 * REGLA DURA: NUNCA usar localStorage para el borrador de venta.
 * Todo estado de negocio se confirma en backend.
 */

import { api as defaultApi, ApiError } from './api.js';

export const estadoVenta = {
  clienteId: null,
  renglones: [],
  enviando: false,
};

/**
 * Formatea un importe numérico con dos decimales y coma ($1500,00).
 * @param {number|string} valor
 * @returns {string}
 */
export function formatearPrecio(valor) {
  const num = typeof valor === 'number' ? valor : parseFloat(valor);
  if (isNaN(num)) return '$0,00';
  return '$' + num.toFixed(2).replace('.', ',');
}

/**
 * Calcula la suma total de subtotales de los renglones en el borrador.
 * @returns {number}
 */
export function calcularTotalVenta() {
  return estadoVenta.renglones.reduce((acumulado, renglon) => acumulado + renglon.subtotal, 0);
}

/**
 * Agrega un renglón al borrador de la venta.
 * Valida que la cantidad sea un entero >= 1 (RN-VEN-03)
 * y que el libro no esté ya en la venta (RN-VEN-04).
 *
 * @param {Object} datos
 * @param {number|string} datos.libroId
 * @param {string} datos.titulo
 * @param {number|string} datos.precioUnitario
 * @param {number|string} datos.cantidad
 * @returns {{ exito: boolean, error?: string, renglon?: Object }}
 */
export function agregarRenglonVenta({ libroId, titulo, precioUnitario, cantidad }) {
  const idNum = parseInt(libroId, 10);
  const cantNum = parseInt(cantidad, 10);
  const precioNum = parseFloat(precioUnitario);

  if (isNaN(cantNum) || cantNum < 1) {
    return {
      exito: false,
      error: 'La cantidad debe ser un entero mayor o igual a 1.',
    };
  }

  if (isNaN(idNum) || idNum <= 0) {
    return {
      exito: false,
      error: 'Debe seleccionar un libro válido.',
    };
  }

  // RN-VEN-04: Unicidad de libros en la misma venta
  const yaExiste = estadoVenta.renglones.some((r) => r.libroId === idNum);
  if (yaExiste) {
    return {
      exito: false,
      error: 'El libro ya forma parte de la venta. No se permite duplicar libros.',
    };
  }

  const subtotal = cantNum * precioNum;
  const nuevoRenglon = {
    libroId: idNum,
    titulo: titulo || `Libro #${idNum}`,
    precioUnitario: precioNum,
    cantidad: cantNum,
    subtotal: subtotal,
  };

  estadoVenta.renglones.push(nuevoRenglon);

  return {
    exito: true,
    renglon: nuevoRenglon,
  };
}

/**
 * Actualiza la cantidad de un renglón existente en el borrador y recalcula su subtotal.
 * Valida que la cantidad sea un entero >= 1 (RN-VEN-03).
 * @param {number|string} libroId
 * @param {number|string} nuevaCantidad
 * @returns {{ exito: boolean, error?: string, renglon?: Object }}
 */
export function actualizarCantidadRenglonVenta(libroId, nuevaCantidad) {
  const idNum = parseInt(libroId, 10);
  const cantNum = parseInt(nuevaCantidad, 10);

  if (isNaN(cantNum) || cantNum < 1) {
    return {
      exito: false,
      error: 'La cantidad debe ser un entero mayor o igual a 1.',
    };
  }

  const renglon = estadoVenta.renglones.find((r) => r.libroId === idNum);
  if (!renglon) {
    return {
      exito: false,
      error: 'El libro no se encuentra en el borrador de venta.',
    };
  }

  renglon.cantidad = cantNum;
  renglon.subtotal = Math.round(cantNum * renglon.precioUnitario * 100) / 100;

  return {
    exito: true,
    renglon,
  };
}

/**
 * Elimina un renglón del borrador de venta según el ID del libro.
 * @param {number|string} libroId
 * @returns {{ exito: boolean }}
 */
export function eliminarRenglonVenta(libroId) {
  const idNum = parseInt(libroId, 10);
  estadoVenta.renglones = estadoVenta.renglones.filter((r) => r.libroId !== idNum);
  return { exito: true };
}

/**
 * Renderiza los renglones actuales del borrador en el DOM.
 * @param {Document|Object} doc
 */
export function renderizarTablaRenglones(doc) {
  if (!doc) return;

  const tabla = doc.getElementById('tabla-renglones');
  const avisoVacio = doc.getElementById('renglones-listado-vacio');
  const totalEl = doc.getElementById('venta-total');

  if (!tabla) return;
  const tbody = tabla.querySelector ? tabla.querySelector('tbody') : null;
  if (!tbody) return;

  tbody.innerHTML = '';
  if (Array.isArray(tbody.children)) {
    tbody.children = [];
  }

  if (estadoVenta.renglones.length === 0) {
    if (avisoVacio) avisoVacio.hidden = false;
    if (totalEl) totalEl.textContent = formatearPrecio(0);
    return;
  }

  if (avisoVacio) avisoVacio.hidden = true;

  estadoVenta.renglones.forEach((renglon) => {
    const tr = doc.createElement('tr');

    const tdLibro = doc.createElement('td');
    tdLibro.textContent = renglon.titulo;
    tr.appendChild(tdLibro);

    const tdCantidad = doc.createElement('td');
    const inputCantidad = doc.createElement('input');
    inputCantidad.type = 'number';
    inputCantidad.className = 'renglon-cantidad';
    inputCantidad.setAttribute('min', '1');
    inputCantidad.setAttribute('step', '1');
    inputCantidad.value = String(renglon.cantidad);
    inputCantidad.setAttribute('aria-label', `Cantidad de ${renglon.titulo}`);
    inputCantidad.dataset.libroId = String(renglon.libroId);

    inputCantidad.addEventListener('change', () => {
      const res = actualizarCantidadRenglonVenta(renglon.libroId, inputCantidad.value);
      const feedback = doc.getElementById('venta-feedback');
      if (!res.exito) {
        inputCantidad.value = String(renglon.cantidad);
        if (feedback) {
          feedback.hidden = false;
          feedback.textContent = `Error — ${res.error}`;
          feedback.classList.remove('mensaje-exito');
          feedback.classList.add('mensaje-error');
        }
        return;
      }
      if (feedback) {
        feedback.hidden = true;
        feedback.textContent = '';
      }
      renderizarTablaRenglones(doc);
    });

    tdCantidad.appendChild(inputCantidad);
    tr.appendChild(tdCantidad);

    const tdPrecio = doc.createElement('td');
    tdPrecio.textContent = formatearPrecio(renglon.precioUnitario);
    tr.appendChild(tdPrecio);

    const tdSubtotal = doc.createElement('td');
    tdSubtotal.textContent = formatearPrecio(renglon.subtotal);
    tr.appendChild(tdSubtotal);

    const tdAcciones = doc.createElement('td');
    const btnQuitar = doc.createElement('button');
    btnQuitar.type = 'button';
    btnQuitar.className = 'renglon-quitar';
    btnQuitar.textContent = 'Quitar';
    btnQuitar.setAttribute('aria-label', `Quitar ${renglon.titulo} de la venta`);
    btnQuitar.dataset.libroId = String(renglon.libroId);

    btnQuitar.addEventListener('click', () => {
      eliminarRenglonVenta(renglon.libroId);
      renderizarTablaRenglones(doc);
    });

    tdAcciones.appendChild(btnQuitar);
    tr.appendChild(tdAcciones);

    tbody.appendChild(tr);
  });

  if (totalEl) {
    totalEl.textContent = formatearPrecio(calcularTotalVenta());
  }
}

/**
 * Sincroniza las opciones del selector de libros en la sección de ventas (#venta-libro).
 * @param {Array<Object>} libros
 * @param {Document|Object} doc
 */
export function sincronizarSelectorVentaLibros(libros, doc) {
  if (!doc) return;
  const selectLibro = doc.getElementById('venta-libro');
  if (!selectLibro) return;

  selectLibro.innerHTML = '';
  if (Array.isArray(selectLibro.children)) {
    selectLibro.children = [];
  }

  const defaultOpt = doc.createElement('option');
  defaultOpt.value = '';
  defaultOpt.textContent = 'Seleccione un libro';
  defaultOpt.disabled = true;
  defaultOpt.selected = true;
  selectLibro.appendChild(defaultOpt);

  if (Array.isArray(libros)) {
    libros.forEach((libro) => {
      const opt = doc.createElement('option');
      opt.value = String(libro.id);
      opt.dataset.precio = String(libro.precio);
      opt.dataset.titulo = libro.titulo;
      opt.textContent = `${libro.titulo} — ${formatearPrecio(libro.precio)}`;
      selectLibro.appendChild(opt);
    });
  }
}

/**
 * Renderiza el comprobante oficial devuelto por la API tras confirmar una venta (RN-VEN-06).
 * Muestra los precios unitarios copiados del catálogo, los subtotales y el total oficial.
 * @param {Object|null} ventaCreada
 * @param {Document|Object} doc
 */
export function renderizarVentaConfirmada(ventaCreada, doc) {
  if (!doc) return;
  const panel = doc.getElementById('venta-confirmada-detalle');
  if (!panel) return;

  panel.innerHTML = '';
  if (Array.isArray(panel.children)) {
    panel.children = [];
  }

  if (!ventaCreada) {
    panel.hidden = true;
    return;
  }

  const titulo = doc.createElement('h3');
  titulo.textContent = `Comprobante de Venta #${ventaCreada.id} (${ventaCreada.cliente_nombre || `Cliente #${ventaCreada.cliente_id}`})`;
  panel.appendChild(titulo);

  const tablaContenedor = doc.createElement('div');
  tablaContenedor.className = 'tabla-contenedor';

  const tabla = doc.createElement('table');
  const thead = doc.createElement('thead');
  const trHead = doc.createElement('tr');
  ['Libro', 'Cantidad', 'Precio unitario (catálogo)', 'Subtotal'].forEach((col) => {
    const th = doc.createElement('th');
    th.scope = 'col';
    th.textContent = col;
    trHead.appendChild(th);
  });
  thead.appendChild(trHead);
  tabla.appendChild(thead);

  const tbody = doc.createElement('tbody');
  const renglones = Array.isArray(ventaCreada.renglones) ? ventaCreada.renglones : [];
  renglones.forEach((r) => {
    const tr = doc.createElement('tr');
    [
      r.titulo || `Libro #${r.libro_id}`,
      String(r.cantidad),
      formatearPrecio(r.precio_unitario),
      formatearPrecio(r.subtotal),
    ].forEach((valor) => {
      const td = doc.createElement('td');
      td.textContent = valor;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  tabla.appendChild(tbody);

  const tfoot = doc.createElement('tfoot');
  const trFoot = doc.createElement('tr');
  const thTotal = doc.createElement('th');
  thTotal.scope = 'row';
  thTotal.setAttribute('colspan', '3');
  thTotal.textContent = 'Total oficial confirmado';
  trFoot.appendChild(thTotal);
  const tdTotal = doc.createElement('td');
  tdTotal.textContent = formatearPrecio(ventaCreada.total);
  trFoot.appendChild(tdTotal);
  tfoot.appendChild(trFoot);
  tabla.appendChild(tfoot);

  tablaContenedor.appendChild(tabla);
  panel.appendChild(tablaContenedor);
  panel.hidden = false;
}

/**
 * Envía la confirmación transaccional de la venta al endpoint POST /api/ventas/.
 * Deshabilita el botón durante el vuelo (RN-VEN-07).
 * Si hay error 409 o 422, preserva intactos los renglones y la selección (RN-VEN-08).
 *
 * @param {Object} [opciones={}]
 * @param {any} [opciones.apiClient=defaultApi]
 * @param {Document|Object} [opciones.context=document]
 * @param {(venta: Object) => void} [opciones.onExito]
 * @returns {Promise<{ exito: boolean, error?: string, venta?: Object }>}
 */
export async function enviarConfirmacionVenta(opciones = {}) {
  const client = opciones.apiClient || (typeof window !== 'undefined' ? window.api : defaultApi);
  const doc = opciones.context || (typeof document !== 'undefined' ? document : null);
  if (!doc) return { exito: false, error: 'No DOM context' };

  const selectCliente = doc.getElementById('venta-cliente');
  const btnConfirmar = doc.getElementById('venta-confirmar');
  const feedback = doc.getElementById('venta-feedback');
  const selectLibro = doc.getElementById('venta-libro');
  const inputCantidad = doc.getElementById('venta-cantidad');

  // Determinar cliente seleccionado
  let clienteId = estadoVenta.clienteId;
  if (!clienteId && selectCliente && selectCliente.value) {
    clienteId = parseInt(selectCliente.value, 10);
  }

  if (!clienteId || isNaN(clienteId)) {
    if (feedback) {
      feedback.hidden = false;
      feedback.textContent = 'Error — Debe seleccionar un cliente registrado para confirmar la venta.';
      feedback.classList.remove('mensaje-exito');
      feedback.classList.add('mensaje-error');
    }
    return { exito: false, error: 'Debe seleccionar un cliente registrado.' };
  }

  // RN-VEN-02: Al menos un renglón
  if (!estadoVenta.renglones || estadoVenta.renglones.length === 0) {
    if (feedback) {
      feedback.hidden = false;
      feedback.textContent = 'Error — La venta debe contener al menos un libro en el borrador.';
      feedback.classList.remove('mensaje-exito');
      feedback.classList.add('mensaje-error');
    }
    return { exito: false, error: 'La venta debe contener al menos un renglón.' };
  }

  // Preparar payload oficial
  const payload = {
    cliente_id: clienteId,
    renglones: estadoVenta.renglones.map((r) => ({
      libro_id: r.libroId,
      cantidad: r.cantidad,
    })),
  };

  // RN-VEN-07: Bloqueo transitorio del botón de confirmación
  estadoVenta.enviando = true;
  if (btnConfirmar) btnConfirmar.disabled = true;

  try {
    const ventaCreada = await client.post('/ventas/', payload);

    // Éxito (201 Created)
    if (feedback) {
      feedback.hidden = false;
      feedback.textContent = `OK — Venta #${ventaCreada.id} confirmada por ${formatearPrecio(ventaCreada.total)}.`;
      feedback.classList.remove('mensaje-error');
      feedback.classList.add('mensaje-exito');
    }

    // Limpiar borrador tras confirmación exitosa
    estadoVenta.renglones = [];
    estadoVenta.clienteId = null;

    if (selectCliente) selectCliente.value = '';
    if (selectLibro) selectLibro.value = '';
    if (inputCantidad) inputCantidad.value = '1';

    renderizarTablaRenglones(doc);
    renderizarVentaConfirmada(ventaCreada, doc);

    if (typeof opciones.onExito === 'function') {
      opciones.onExito(ventaCreada);
    }

    return { exito: true, venta: ventaCreada };
  } catch (err) {
    // RN-VEN-08: En respuestas de conflicto (409) o validación (422),
    // PRESERVAR ESTRICTAMENTE los renglones y la selección en pantalla.
    const mensajeError = err instanceof ApiError ? err.message : (err.message || 'Error al procesar la venta');

    if (feedback) {
      feedback.hidden = false;
      feedback.textContent = `Error — ${mensajeError}`;
      feedback.classList.remove('mensaje-exito');
      feedback.classList.add('mensaje-error');
    }

    return { exito: false, error: mensajeError };
  } finally {
    estadoVenta.enviando = false;
    if (btnConfirmar) btnConfirmar.disabled = false;
  }
}

/**
 * Inicializa los manejadores de eventos del módulo de ventas en la interfaz.
 * @param {Object} [opciones={}]
 * @param {any} [opciones.apiClient=defaultApi]
 * @param {Document|Object} [opciones.context=document]
 * @param {(venta: Object) => void} [opciones.onExito]
 */
export function inicializarEventosVentas(opciones = {}) {
  const doc = opciones.context || (typeof document !== 'undefined' ? document : null);
  if (!doc) return;

  const btnAgregar = doc.getElementById('venta-agregar');
  const btnConfirmar = doc.getElementById('venta-confirmar');
  const selectLibro = doc.getElementById('venta-libro');
  const inputCantidad = doc.getElementById('venta-cantidad');
  const selectCliente = doc.getElementById('venta-cliente');
  const feedback = doc.getElementById('venta-feedback');

  if (selectCliente && !selectCliente.dataset.salesInitialized) {
    selectCliente.addEventListener('change', () => {
      const val = parseInt(selectCliente.value, 10);
      estadoVenta.clienteId = isNaN(val) ? null : val;
    });
    selectCliente.dataset.salesInitialized = 'true';
  }

  if (btnAgregar && !btnAgregar.dataset.salesInitialized) {
    btnAgregar.addEventListener('click', () => {
      if (!selectLibro || !selectLibro.value) {
        if (feedback) {
          feedback.hidden = false;
          feedback.textContent = 'Error — Debe seleccionar un libro para agregar.';
          feedback.classList.remove('mensaje-exito');
          feedback.classList.add('mensaje-error');
        }
        return;
      }

      const libroId = parseInt(selectLibro.value, 10);
      const selectedOpt = selectLibro.options
        ? selectLibro.options[selectLibro.selectedIndex]
        : null;

      let titulo = selectedOpt ? (selectedOpt.dataset?.titulo || selectedOpt.textContent.split(' — ')[0]) : `Libro #${libroId}`;
      let precio = selectedOpt ? parseFloat(selectedOpt.dataset?.precio) : NaN;

      if (isNaN(precio) && selectedOpt) {
        const match = selectedOpt.textContent.match(/\$([0-9.,]+)/);
        if (match) {
          precio = parseFloat(match[1].replace(',', '.'));
        }
      }

      const cantidad = inputCantidad ? inputCantidad.value : '1';

      const res = agregarRenglonVenta({
        libroId,
        titulo,
        precioUnitario: isNaN(precio) ? 0 : precio,
        cantidad,
      });

      if (!res.exito) {
        if (feedback) {
          feedback.hidden = false;
          feedback.textContent = `Error — ${res.error}`;
          feedback.classList.remove('mensaje-exito');
          feedback.classList.add('mensaje-error');
        }
        return;
      }

      // Éxito al agregar renglón
      renderizarTablaRenglones(doc);
      if (feedback) {
        feedback.hidden = true;
        feedback.textContent = '';
      }
      selectLibro.value = '';
      if (inputCantidad) inputCantidad.value = '1';
    });
    btnAgregar.dataset.salesInitialized = 'true';
  }

  if (btnConfirmar && !btnConfirmar.dataset.salesInitialized) {
    btnConfirmar.addEventListener('click', async () => {
      await enviarConfirmacionVenta(opciones);
    });
    btnConfirmar.dataset.salesInitialized = 'true';
  }

  // Renderizar estado inicial de la tabla
  renderizarTablaRenglones(doc);
}
