import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import {
  estadoHistorial,
  formatearPrecioHistorial,
  formatearCodigoVenta,
  cargarHistorialVentas,
  cargarDetalleVenta,
  renderizarDetalleVenta,
  avanzarPaginaHistorial,
  retrocederPaginaHistorial,
  cambiarLimiteHistorial,
  inicializarEventosHistorial,
} from './history.js';
import { ApiError } from './api.js';

function crearMockElement(tag = 'div', id = '') {
  return {
    tagName: tag.toUpperCase(),
    id,
    hidden: false,
    disabled: false,
    value: '',
    textContent: '',
    innerHTML: '',
    dataset: {},
    children: [],
    attributes: {},
    listeners: {},
    setAttribute(k, v) { this.attributes[k] = v; },
    getAttribute(k) { return this.attributes[k]; },
    appendChild(child) {
      this.children.push(child);
      return child;
    },
    addEventListener(type, fn) {
      this.listeners[type] = fn;
    },
  };
}

function crearMockDocument() {
  const tbodyHistorial = crearMockElement('tbody', 'tbody-historial');
  const tablaHistorial = crearMockElement('table', 'tabla-historial');
  tablaHistorial.querySelector = (sel) => (sel === 'tbody' ? tbodyHistorial : null);

  const elements = {
    'historial-cargando': crearMockElement('div', 'historial-cargando'),
    'historial-listado-vacio': crearMockElement('p', 'historial-listado-vacio'),
    'historial-error': crearMockElement('div', 'historial-error'),
    'historial-tabla-contenedor': crearMockElement('div', 'historial-tabla-contenedor'),
    'tabla-historial': tablaHistorial,
    'historial-anterior': crearMockElement('button', 'historial-anterior'),
    'historial-siguiente': crearMockElement('button', 'historial-siguiente'),
    'historial-info-paginacion': crearMockElement('span', 'historial-info-paginacion'),
    'historial-limite': crearMockElement('select', 'historial-limite'),
    'tabla-historial-detalle': crearMockElement('div', 'tabla-historial-detalle'),
  };

  return {
    getElementById(id) {
      return elements[id] || null;
    },
    createElement(tag) {
      return crearMockElement(tag);
    },
    elements,
  };
}

describe('Módulo de Historial y Detalle de Ventas (C-07 / US-008)', () => {
  beforeEach(() => {
    estadoHistorial.ventas = [];
    estadoHistorial.ventaSeleccionada = null;
    estadoHistorial.limit = 20;
    estadoHistorial.offset = 0;
    estadoHistorial.cargando = false;
  });

  it('formatea precios y códigos de comprobante correctamente', () => {
    assert.equal(formatearPrecioHistorial(5000), '$5000,00');
    assert.equal(formatearPrecioHistorial('3250.5'), '$3250,50');
    assert.equal(formatearCodigoVenta(1), 'V-0001');
    assert.equal(formatearCodigoVenta(42), 'V-0042');
  });

  it('carga historial paginado desde GET /ventas/?limit=20&offset=0 y muestra aviso vacío si no hay ventas', async () => {
    const mockDoc = crearMockDocument();
    let llamada = null;
    const mockApi = {
      get: async (endpoint, params) => {
        llamada = { endpoint, params };
        return [];
      },
    };

    const res = await cargarHistorialVentas({ apiClient: mockApi, context: mockDoc });
    assert.deepEqual(res, []);
    assert.equal(llamada.endpoint, '/ventas/');
    assert.deepEqual(llamada.params, { limit: 20, offset: 0 });
    assert.equal(mockDoc.getElementById('historial-listado-vacio').hidden, false);
    assert.equal(mockDoc.getElementById('historial-anterior').disabled, true);
    assert.equal(mockDoc.getElementById('historial-siguiente').disabled, true);
  });

  it('soporta paginación con limit y offset (avanzar, retroceder y cambiar límite)', async () => {
    const mockDoc = crearMockDocument();
    const llamadas = [];
    const mockApi = {
      get: async (endpoint, params) => {
        llamadas.push({ endpoint, params });
        // Devuelve exactamente `limit` elementos en página 1 para habilitar Siguiente
        if (params.offset === 0) {
          return Array.from({ length: params.limit }, (_, i) => ({
            id: 100 - i,
            cliente_id: 1,
            cliente_nombre: 'Ana Beltrán',
            fecha: '2026-11-13T10:00:00Z',
            total: 1500,
            renglones: [],
          }));
        }
        return [
          {
            id: 1,
            cliente_id: 1,
            cliente_nombre: 'Ana Beltrán',
            fecha: '2026-11-12T10:00:00Z',
            total: 5000,
            renglones: [],
          },
        ];
      },
    };

    estadoHistorial.limit = 2;
    await cargarHistorialVentas({ apiClient: mockApi, context: mockDoc });
    assert.equal(mockDoc.getElementById('historial-anterior').disabled, true);
    assert.equal(mockDoc.getElementById('historial-siguiente').disabled, false);

    await avanzarPaginaHistorial({ apiClient: mockApi, context: mockDoc });
    assert.equal(llamadas[1].params.offset, 2);
    assert.equal(mockDoc.getElementById('historial-info-paginacion').textContent, 'Página 2');
    assert.equal(mockDoc.getElementById('historial-anterior').disabled, false);
    assert.equal(mockDoc.getElementById('historial-siguiente').disabled, true);

    await retrocederPaginaHistorial({ apiClient: mockApi, context: mockDoc });
    assert.equal(estadoHistorial.offset, 0);

    await cambiarLimiteHistorial(10, { apiClient: mockApi, context: mockDoc });
    assert.equal(estadoHistorial.limit, 10);
    assert.equal(estadoHistorial.offset, 0);
  });

  it('Caso G-04 / G-05: recupera detalle histórico por ID con precios unitarios congelados sobrevivientes a recarga', async () => {
    const mockDoc = crearMockDocument();
    const ventaApi = {
      id: 7,
      cliente_id: 1,
      cliente_nombre: 'Ana Beltrán',
      fecha: '2026-11-13T14:30:00Z',
      total: 5000.0,
      renglones: [
        {
          id: 11,
          libro_id: 1,
          titulo: 'El principito',
          cantidad: 2,
          precio_unitario: 1500.0, // Precio congelado al confirmar venta
          subtotal: 3000.0,
        },
        {
          id: 12,
          libro_id: 2,
          titulo: 'Cuentos de terror',
          cantidad: 1,
          precio_unitario: 2000.0,
          subtotal: 2000.0,
        },
      ],
    };

    let endpointConsultado = '';
    const mockApi = {
      get: async (endpoint) => {
        endpointConsultado = endpoint;
        return ventaApi;
      },
    };

    const detalle = await cargarDetalleVenta(7, { apiClient: mockApi, context: mockDoc });
    assert.equal(endpointConsultado, '/ventas/7');
    assert.equal(detalle.total, 5000.0);

    const panel = mockDoc.getElementById('tabla-historial-detalle');
    assert.equal(panel.children.length, 2); // cabecera + tabla-contenedor
    const cabeceraTexto = panel.children[0].children.map((p) => p.textContent).join(' | ');
    assert.match(cabeceraTexto, /V-0007/);
    assert.match(cabeceraTexto, /Ana Beltrán/);

    const tabla = panel.children[1].children[0];
    const tbody = tabla.children[2];
    assert.equal(tbody.children.length, 2);
    // Verificar precio unitario congelado en la fila del libro 1
    assert.equal(tbody.children[0].children[2].textContent, '$1500,00');
    assert.equal(tbody.children[0].children[3].textContent, '$3000,00');

    const tfoot = tabla.children[3];
    assert.equal(tfoot.children[0].children[1].textContent, '$5000,00');
  });

  it('renderizarDetalleVenta(null) muestra estado vacío sin controles de edición', () => {
    const mockDoc = crearMockDocument();
    renderizarDetalleVenta(null, mockDoc);
    const panel = mockDoc.getElementById('tabla-historial-detalle');
    assert.equal(panel.children.length, 1);
    assert.match(panel.children[0].textContent, /Seleccione una venta del historial/);
  });

  it('muestra #historial-error ante falla de red en cargarHistorialVentas y ante 404 en cargarDetalleVenta', async () => {
    const mockDoc = crearMockDocument();
    const apiFallaRed = {
      get: async () => {
        throw new Error('Falla de red');
      },
    };

    await assert.rejects(
      () => cargarHistorialVentas({ apiClient: apiFallaRed, context: mockDoc }),
      /Falla de red/,
    );
    assert.equal(estadoHistorial.cargando, false);
    assert.equal(mockDoc.getElementById('historial-cargando').hidden, true);
    assert.equal(mockDoc.getElementById('historial-error').hidden, false);
    assert.match(mockDoc.getElementById('historial-error').textContent, /Falla de red/);

    const api404 = {
      get: async () => {
        throw new ApiError('Venta con ID 999 no encontrada', 404);
      },
    };
    await assert.rejects(
      () => cargarDetalleVenta(999, { apiClient: api404, context: mockDoc }),
      /no encontrada/,
    );
    assert.equal(mockDoc.getElementById('historial-error').hidden, false);
    assert.match(mockDoc.getElementById('historial-error').textContent, /#999/);
  });

  it('click en botón Ver detalle de fila y controles de inicializarEventosHistorial disparan consultas API', async () => {
    const mockDoc = crearMockDocument();
    const llamadas = [];
    const ventaLista = {
      id: 15,
      cliente_id: 2,
      cliente_nombre: 'Juan Pérez',
      fecha: '2026-11-13T12:00:00Z',
      total: 3200.0,
      renglones: [],
    };
    const ventaDetalle = {
      ...ventaLista,
      renglones: [
        { id: 1, libro_id: 3, titulo: 'Rayuela', cantidad: 2, precio_unitario: 1600.0, subtotal: 3200.0 },
      ],
    };

    const mockApi = {
      get: async (endpoint, params) => {
        llamadas.push({ endpoint, params });
        if (endpoint === '/ventas/15') return ventaDetalle;
        return [ventaLista];
      },
    };

    await cargarHistorialVentas({ apiClient: mockApi, context: mockDoc });
    const tbody = mockDoc.getElementById('tabla-historial').querySelector('tbody');
    assert.equal(tbody.children.length, 1);

    // Click en el botón "Ver detalle" de la celda 5
    const btnDetalle = tbody.children[0].children[4].children[0];
    await btnDetalle.listeners.click();

    assert.equal(llamadas[1].endpoint, '/ventas/15');
    const panel = mockDoc.getElementById('tabla-historial-detalle');
    const cabeceraTexto = panel.children[0].children.map((p) => p.textContent).join(' | ');
    assert.match(cabeceraTexto, /V-0015/);
    assert.match(cabeceraTexto, /Juan Pérez/);

    // Verificar wiring de paginación en inicializarEventosHistorial
    inicializarEventosHistorial({ apiClient: mockApi, context: mockDoc });
    const selectLimite = mockDoc.getElementById('historial-limite');
    assert.equal(selectLimite.dataset.historyInitialized, 'true');
    await selectLimite.listeners.change({ target: { value: '50' } });
    assert.equal(estadoHistorial.limit, 50);
    assert.equal(llamadas[llamadas.length - 1].params.limit, 50);
  });
});
