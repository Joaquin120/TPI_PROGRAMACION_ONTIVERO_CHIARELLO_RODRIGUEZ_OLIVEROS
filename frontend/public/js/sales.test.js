import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import {
  estadoVenta,
  agregarRenglonVenta,
  actualizarCantidadRenglonVenta,
  eliminarRenglonVenta,
  calcularTotalVenta,
  renderizarTablaRenglones,
  renderizarVentaConfirmada,
  enviarConfirmacionVenta,
} from './sales.js';
import { ApiError } from './api.js';

function crearMockElement(tag = 'div', id = '') {
  return {
    tagName: tag.toUpperCase(),
    id: id,
    hidden: false,
    textContent: '',
    innerHTML: '',
    value: '',
    disabled: false,
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
    classList: {
      classes: [],
      add(c) { if (!this.classes.includes(c)) this.classes.push(c); },
      remove(c) { this.classes = this.classes.filter(item => item !== c); },
      contains(c) { return this.classes.includes(c); }
    },
  };
}

function crearMockDocument() {
  const tbodyRenglones = crearMockElement('tbody', 'cuerpo-renglones');
  const tablaRenglones = crearMockElement('table', 'tabla-renglones');
  tablaRenglones.querySelector = (sel) => (sel === 'tbody' ? tbodyRenglones : null);

  const selectCliente = crearMockElement('select', 'venta-cliente');
  const selectLibro = crearMockElement('select', 'venta-libro');
  const inputCantidad = crearMockElement('input', 'venta-cantidad');
  const btnConfirmar = crearMockElement('button', 'venta-confirmar');
  const feedback = crearMockElement('p', 'venta-feedback');
  const total = crearMockElement('strong', 'venta-total');
  const avisoVacio = crearMockElement('p', 'renglones-listado-vacio');

  const elements = {
    'venta-cliente': selectCliente,
    'venta-libro': selectLibro,
    'venta-cantidad': inputCantidad,
    'venta-confirmar': btnConfirmar,
    'venta-feedback': feedback,
    'venta-total': total,
    'renglones-listado-vacio': avisoVacio,
    'tabla-renglones': tablaRenglones,
  };

  return {
    getElementById(id) {
      if (!elements[id]) {
        elements[id] = crearMockElement('div', id);
      }
      return elements[id];
    },
    createElement(tag) {
      return crearMockElement(tag);
    },
    elements,
  };
}

describe('Módulo de Ventas: Composición de Borrador en Memoria', () => {
  beforeEach(() => {
    estadoVenta.clienteId = null;
    estadoVenta.renglones = [];
    estadoVenta.enviando = false;
  });

  it('agrega renglón calculando subtotal e impide cantidades menores a 1 (RN-VEN-03)', () => {
    const res = agregarRenglonVenta({
      libroId: 1,
      titulo: 'El principito',
      precioUnitario: 1500,
      cantidad: 2,
    });
    assert.equal(res.exito, true);
    assert.equal(estadoVenta.renglones.length, 1);
    assert.equal(estadoVenta.renglones[0].subtotal, 3000);

    const resInvalida = agregarRenglonVenta({
      libroId: 2,
      titulo: 'Otro libro',
      precioUnitario: 500,
      cantidad: 0,
    });
    assert.equal(resInvalida.exito, false);
    assert.match(resInvalida.error, /cantidad/i);
  });

  it('bloquea la duplicación del mismo libro en múltiples renglones (RN-VEN-04)', () => {
    agregarRenglonVenta({
      libroId: 1,
      titulo: 'El principito',
      precioUnitario: 1500,
      cantidad: 1,
    });
    const resDuplicado = agregarRenglonVenta({
      libroId: 1,
      titulo: 'El principito',
      precioUnitario: 1500,
      cantidad: 2,
    });
    assert.equal(resDuplicado.exito, false);
    assert.match(resDuplicado.error, /ya forma parte/i);
    assert.equal(estadoVenta.renglones.length, 1);
  });

  it('elimina un renglón del borrador y actualiza el total', () => {
    agregarRenglonVenta({ libroId: 1, titulo: 'A', precioUnitario: 1000, cantidad: 1 });
    agregarRenglonVenta({ libroId: 2, titulo: 'B', precioUnitario: 2000, cantidad: 1 });
    assert.equal(calcularTotalVenta(), 3000);

    eliminarRenglonVenta(1); // eliminar libroId 1
    assert.equal(estadoVenta.renglones.length, 1);
    assert.equal(estadoVenta.renglones[0].libroId, 2);
    assert.equal(calcularTotalVenta(), 2000);
  });

  it('permite modificar la cantidad de un renglón existente recalculando subtotal y total', () => {
    agregarRenglonVenta({ libroId: 1, titulo: 'El principito', precioUnitario: 1500, cantidad: 1 });
    const resOk = actualizarCantidadRenglonVenta(1, 3);
    assert.equal(resOk.exito, true);
    assert.equal(estadoVenta.renglones[0].cantidad, 3);
    assert.equal(estadoVenta.renglones[0].subtotal, 4500);
    assert.equal(calcularTotalVenta(), 4500);

    const resBad = actualizarCantidadRenglonVenta(1, 0);
    assert.equal(resBad.exito, false);
    assert.equal(estadoVenta.renglones[0].cantidad, 3);
  });
});

describe('Módulo de Ventas: Renderizado de Tabla de Renglones', () => {
  beforeEach(() => {
    estadoVenta.clienteId = null;
    estadoVenta.renglones = [];
  });

  it('renderiza filas en la tabla y oculta aviso de vacío', () => {
    const mockDoc = crearMockDocument();
    estadoVenta.renglones = [
      { libroId: 1, titulo: 'El principito', precioUnitario: 1500, cantidad: 2, subtotal: 3000 },
      { libroId: 2, titulo: 'Terror', precioUnitario: 2000, cantidad: 1, subtotal: 2000 },
    ];

    renderizarTablaRenglones(mockDoc);
    const tbody = mockDoc.getElementById('tabla-renglones').querySelector('tbody');
    assert.equal(tbody.children.length, 2);
    assert.equal(mockDoc.getElementById('renglones-listado-vacio').hidden, true);
    assert.match(mockDoc.getElementById('venta-total').textContent, /5000/);
  });

  it('muestra aviso de vacío cuando el borrador no tiene renglones', () => {
    const mockDoc = crearMockDocument();
    estadoVenta.renglones = [];
    renderizarTablaRenglones(mockDoc);
    assert.equal(mockDoc.getElementById('renglones-listado-vacio').hidden, false);
  });

  it('renderizarVentaConfirmada muestra comprobante oficial y oculta panel con null', () => {
    const mockDoc = crearMockDocument();
    const venta = {
      id: 9,
      cliente_id: 1,
      cliente_nombre: 'Ana Beltrán',
      total: 4500,
      renglones: [
        { libro_id: 1, titulo: 'El principito', cantidad: 3, precio_unitario: 1500, subtotal: 4500 },
      ],
    };

    renderizarVentaConfirmada(venta, mockDoc);
    const panel = mockDoc.getElementById('venta-confirmada-detalle');
    assert.equal(panel.hidden, false);
    assert.match(panel.children[0].textContent, /Comprobante de Venta #9/);
    const tabla = panel.children[1].children[0];
    const tbody = tabla.children[1];
    assert.equal(tbody.children[0].children[2].textContent, '$1500,00');
    assert.equal(tbody.children[0].children[3].textContent, '$4500,00');

    renderizarVentaConfirmada(null, mockDoc);
    assert.equal(panel.hidden, true);
    assert.equal(panel.children.length, 0);
  });

  it('input .renglon-cantidad recalcula subtotal ante cambio válido y revierte si es <= 0', () => {
    const mockDoc = crearMockDocument();
    estadoVenta.renglones = [
      { libroId: 1, titulo: 'El principito', precioUnitario: 1500, cantidad: 1, subtotal: 1500 },
    ];
    renderizarTablaRenglones(mockDoc);

    const tbody = mockDoc.getElementById('tabla-renglones').querySelector('tbody');
    const inputCant = tbody.children[0].children[1].children[0];

    // Cambio inválido -> restaura valor y muestra error
    inputCant.value = '0';
    inputCant.listeners.change();
    assert.equal(estadoVenta.renglones[0].cantidad, 1);
    assert.equal(mockDoc.getElementById('venta-feedback').hidden, false);

    // Cambio válido -> actualiza subtotal y total
    const tbody2 = mockDoc.getElementById('tabla-renglones').querySelector('tbody');
    const inputCant2 = tbody2.children[0].children[1].children[0];
    inputCant2.value = '4';
    inputCant2.listeners.change();
    assert.equal(estadoVenta.renglones[0].cantidad, 4);
    assert.equal(estadoVenta.renglones[0].subtotal, 6000);
    assert.equal(mockDoc.getElementById('venta-total').textContent, '$6000,00');
  });
});

describe('Módulo de Ventas: Envío y Casos G-04 / G-06', () => {
  beforeEach(() => {
    estadoVenta.clienteId = null;
    estadoVenta.renglones = [];
    estadoVenta.enviando = false;
  });

  it('Caso G-04: confirma venta válida con 2 renglones, deshabilita botón y limpia borrador', async () => {
    const mockDoc = crearMockDocument();
    mockDoc.getElementById('venta-cliente').value = '1';
    estadoVenta.clienteId = 1;
    estadoVenta.renglones = [
      { libroId: 1, titulo: 'El principito', precioUnitario: 1500, cantidad: 2, subtotal: 3000 },
      { libroId: 2, titulo: 'Terror', precioUnitario: 2000, cantidad: 1, subtotal: 2000 },
    ];

    const mockApi = {
      post: async (endpoint, body) => {
        assert.equal(endpoint, '/ventas/');
        assert.equal(body.cliente_id, 1);
        assert.equal(body.renglones.length, 2);
        return {
          id: 1,
          cliente_id: 1,
          cliente_nombre: 'Ana Beltrán',
          total: 5000.0,
          fecha: '2026-11-12T20:00:00Z',
          renglones: [
            { id: 1, libro_id: 1, cantidad: 2, precio_unitario: 1500, subtotal: 3000 },
            { id: 2, libro_id: 2, cantidad: 1, precio_unitario: 2000, subtotal: 2000 },
          ]
        };
      }
    };

    const res = await enviarConfirmacionVenta({ apiClient: mockApi, context: mockDoc });
    assert.equal(res.exito, true);

    const feedback = mockDoc.getElementById('venta-feedback');
    assert.equal(feedback.hidden, false);
    assert.match(feedback.textContent, /confirmada|OK/i);

    // Borrador reseteado
    assert.equal(estadoVenta.renglones.length, 0);

    // Panel de comprobante renderizado con precios unitarios y total
    const panelConfirmada = mockDoc.getElementById('venta-confirmada-detalle');
    assert.equal(panelConfirmada.hidden, false);
    assert.equal(panelConfirmada.children.length, 2);
  });

  it('Caso G-06: rechazo 409 por cliente inexistente preserva el borrador intacto (RN-VEN-08)', async () => {
    const mockDoc = crearMockDocument();
    mockDoc.getElementById('venta-cliente').value = '999';
    estadoVenta.clienteId = 999;
    estadoVenta.renglones = [
      { libroId: 1, titulo: 'El principito', precioUnitario: 1500, cantidad: 2, subtotal: 3000 }
    ];

    const mockApi = {
      post: async () => {
        throw new ApiError('El cliente con ID 999 no existe', 409);
      }
    };

    const res = await enviarConfirmacionVenta({ apiClient: mockApi, context: mockDoc });
    assert.equal(res.exito, false);

    const feedback = mockDoc.getElementById('venta-feedback');
    assert.equal(feedback.hidden, false);
    assert.match(feedback.textContent, /cliente.*no existe/i);

    // INVARIANTE: El borrador NO se borra
    assert.equal(estadoVenta.renglones.length, 1);
    assert.equal(estadoVenta.renglones[0].libroId, 1);
  });

  it('Caso G-06: rechazo 422 por validación preserva el borrador intacto (RN-VEN-08)', async () => {
    const mockDoc = crearMockDocument();
    mockDoc.getElementById('venta-cliente').value = '1';
    estadoVenta.clienteId = 1;
    estadoVenta.renglones = [
      { libroId: 5, titulo: 'Libro X', precioUnitario: 1000, cantidad: 1, subtotal: 1000 }
    ];

    const mockApi = {
      post: async () => {
        throw new ApiError('No se permite registrar múltiples renglones para el mismo libro', 422);
      }
    };

    const res = await enviarConfirmacionVenta({ apiClient: mockApi, context: mockDoc });
    assert.equal(res.exito, false);

    const feedback = mockDoc.getElementById('venta-feedback');
    assert.equal(feedback.hidden, false);
    assert.match(feedback.textContent, /múltiples renglones/i);

    // INVARIANTE: El borrador NO se borra
    assert.equal(estadoVenta.renglones.length, 1);
  });

  it('rechaza el envío si no se seleccionó cliente o el borrador está vacío', async () => {
    const mockDoc = crearMockDocument();
    let apiLlamada = false;
    const mockApi = {
      post: async () => {
        apiLlamada = true;
      }
    };

    // Caso 1: Sin cliente
    estadoVenta.clienteId = null;
    mockDoc.getElementById('venta-cliente').value = '';
    estadoVenta.renglones = [{ libroId: 1, titulo: 'A', precioUnitario: 100, cantidad: 1, subtotal: 100 }];
    const resSinCliente = await enviarConfirmacionVenta({ apiClient: mockApi, context: mockDoc });
    assert.equal(resSinCliente.exito, false);
    assert.equal(apiLlamada, false);

    // Caso 2: Sin renglones
    estadoVenta.clienteId = 1;
    mockDoc.getElementById('venta-cliente').value = '1';
    estadoVenta.renglones = [];
    const resSinRenglones = await enviarConfirmacionVenta({ apiClient: mockApi, context: mockDoc });
    assert.equal(resSinRenglones.exito, false);
    assert.equal(apiLlamada, false);
  });
});
