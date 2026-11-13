/**
 * Orquestador principal del frontend — Librería El Faro de los Libros.
 * Conecta todas las vistas con los módulos ES nativos respaldados por la API REST (/api/*).
 * Cumple estrictamente la Regla Dura #1: sin persistencia de negocio en localStorage.
 */

'use strict';

import { api as defaultApi } from './api.js';

import {
  cargarCatalogoApi,
  inicializarEventosCatalogo,
} from './catalog.js';

import {
  inicializarEventosAltaLibro,
  renderizarTablaLibrosRegistrados,
} from './books.js';

import {
  inicializarEventosClientes,
  cargarClientes,
} from './clients.js';

import {
  inicializarEventosVentas,
  sincronizarSelectorVentaLibros,
} from './sales.js';

import {
  estadoHistorial,
  inicializarEventosHistorial,
  cargarHistorialVentas,
  renderizarDetalleVenta,
} from './history.js';

/**
 * Recarga el catálogo respetando su filtro/paginación visual y sincroniza de forma
 * independiente los selectores operativos de Ventas y Actualización de Precio.
 * @param {Object} [opciones={}]
 */
export async function refrescarCatalogoYSelectores(opciones = {}) {
  const client = opciones.apiClient || (typeof window !== 'undefined' ? window.api : defaultApi);
  const doc = opciones.context || (typeof document !== 'undefined' ? document : null);
  if (!doc) return [];

  try {
    await cargarCatalogoApi({ apiClient: client, context: doc });
  } catch (error) {
    console.error('Error actualizando catálogo:', error);
  }

  try {
    const dataOperativa = await client.get('/libros/', { limit: 100, offset: 0 });
    const librosOperativos = Array.isArray(dataOperativa)
      ? dataOperativa
      : (dataOperativa && Array.isArray(dataOperativa.items) ? dataOperativa.items : []);
    renderizarTablaLibrosRegistrados(librosOperativos, doc);
    sincronizarSelectorVentaLibros(librosOperativos, doc);
    return librosOperativos;
  } catch (error) {
    console.error('Error actualizando selectores de libros:', error);
    return [];
  }
}

/**
 * Reinicia el historial en página 1 (offset = 0), recarga la tabla desde la API
 * y muestra el detalle inmutable de la venta recién confirmada.
 * @param {Object|null} ventaConfirmada
 * @param {Object} [opciones={}]
 */
export async function manejarVentaConfirmada(ventaConfirmada, opciones = {}) {
  const client = opciones.apiClient || (typeof window !== 'undefined' ? window.api : defaultApi);
  const doc = opciones.context || (typeof document !== 'undefined' ? document : null);
  if (!doc) return;

  estadoHistorial.offset = 0;
  try {
    await cargarHistorialVentas({ apiClient: client, context: doc });
  } catch (error) {
    console.error('Error refrescando historial tras venta:', error);
  }

  if (ventaConfirmada) {
    estadoHistorial.ventaSeleccionada = ventaConfirmada;
    renderizarDetalleVenta(ventaConfirmada, doc);
  }
}

/**
 * Actualiza el atributo aria-current="page" en la navegación superior según el enlace activo.
 */
function inicializarNavegacionActiva() {
  const enlaces = document.querySelectorAll('.navegacion a');
  if (!enlaces || enlaces.length === 0) return;

  const marcarActivo = (hashActual) => {
    const destino = hashActual || '#vista-catalogo';
    enlaces.forEach((enlace) => {
      if (enlace.getAttribute('href') === destino) {
        enlace.setAttribute('aria-current', 'page');
      } else {
        enlace.removeAttribute('aria-current');
      }
    });
  };

  window.addEventListener('hashchange', () => marcarActivo(window.location.hash));
  marcarActivo(window.location.hash);
}

/**
 * Punto de entrada de inicialización de eventos y carga inicial vía API REST.
 */
function inicializar() {
  inicializarNavegacionActiva();

  // 1. Catálogo y selectores dependientes de libros
  inicializarEventosCatalogo(document);
  refrescarCatalogoYSelectores();

  // 2. Alta de libros y ajuste de precio en catálogo (PATCH /api/libros/{id})
  inicializarEventosAltaLibro(document, {
    onExito: () => {
      refrescarCatalogoYSelectores();
    },
  });

  // 3. Clientes (listado, alta y selector en Ventas)
  inicializarEventosClientes({ context: document });
  cargarClientes({ context: document }).catch((error) => {
    console.error('Error inicializando clientes:', error);
  });

  // 4. Ventas (borrador en memoria y confirmación transaccional)
  inicializarEventosVentas({
    context: document,
    onExito: (ventaConfirmada) => manejarVentaConfirmada(ventaConfirmada, { context: document }),
  });

  // 5. Historial de ventas paginado y detalle histórico inmutable (C-07)
  inicializarEventosHistorial({ context: document });
  cargarHistorialVentas({ context: document }).catch((error) => {
    console.error('Error inicializando historial de ventas:', error);
  });
}

if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inicializar);
  } else {
    inicializar();
  }
}
