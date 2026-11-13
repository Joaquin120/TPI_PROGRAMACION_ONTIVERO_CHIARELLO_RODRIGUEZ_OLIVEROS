import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import {
  estadoClientes,
  validarEmail,
  validarDatosCliente,
  cargarClientes,
  renderizarTablaClientes,
  sincronizarSelectorVentas,
  consultarClientePorId,
  enviarAltaCliente,
} from './clients.js';
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
    setAttribute(k, v) { this.attributes[k] = v; },
    getAttribute(k) { return this.attributes[k]; },
    appendChild(child) {
      this.children.push(child);
      return child;
    },
    addEventListener() {},
    classList: {
      classes: [],
      add(c) { if (!this.classes.includes(c)) this.classes.push(c); },
      remove(c) { this.classes = this.classes.filter(item => item !== c); },
      contains(c) { return this.classes.includes(c); }
    },
    reset() {
      this.value = '';
    }
  };
}

function crearMockDocument() {
  const tbodyClientes = crearMockElement('tbody', 'cuerpo-clientes');
  const tablaClientes = crearMockElement('table', 'tabla-clientes');
  tablaClientes.querySelector = (sel) => (sel === 'tbody' ? tbodyClientes : null);

  const formAltaCliente = crearMockElement('form', 'form-alta-cliente');
  const inputNombre = crearMockElement('input', 'cliente-nombre');
  const inputEmail = crearMockElement('input', 'cliente-email');
  const btnSubmit = crearMockElement('button', 'btn-submit-cliente');
  formAltaCliente.querySelector = (sel) => {
    if (sel === 'button[type="submit"]') return btnSubmit;
    return null;
  };
  formAltaCliente.reset = () => {
    inputNombre.value = '';
    inputEmail.value = '';
  };

  const elements = {
    'form-alta-cliente': formAltaCliente,
    'cliente-nombre': inputNombre,
    'cliente-email': inputEmail,
    'clientes-feedback': crearMockElement('p', 'clientes-feedback'),
    'clientes-listado-vacio': crearMockElement('p', 'clientes-listado-vacio'),
    'tabla-clientes': tablaClientes,
    'venta-cliente': crearMockElement('select', 'venta-cliente'),
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

describe('Módulo de Clientes: Validación de datos (validarEmail, validarDatosCliente)', () => {
  it('valida correctamente correos electrónicos válidos', () => {
    assert.equal(validarEmail('usuario@dominio.com'), true);
    assert.equal(validarEmail('juan.perez@sub.empresa.org'), true);
  });

  it('rechaza correos con formato inválido', () => {
    assert.equal(validarEmail(''), false);
    assert.equal(validarEmail('sin-arroba.com'), false);
    assert.equal(validarEmail('usuario@sin-punto'), false);
    assert.equal(validarEmail('@dominio.com'), false);
  });

  it('valida exitosamente datos de cliente completos', () => {
    const res = validarDatosCliente({ nombre: 'Juan Pérez', email: 'juan@example.com' });
    assert.equal(res.valido, true);
    assert.equal(res.error, null);
  });

  it('rechaza nombre vacío (RN-CLI-02)', () => {
    const res = validarDatosCliente({ nombre: '   ', email: 'juan@example.com' });
    assert.equal(res.valido, false);
    assert.match(res.error, /nombre/i);
  });

  it('rechaza email inválido (RN-CLI-02)', () => {
    const res = validarDatosCliente({ nombre: 'Juan', email: 'invalido' });
    assert.equal(res.valido, false);
    assert.match(res.error, /correo|email/i);
  });
});

describe('Módulo de Clientes: Renderizado y Carga de Clientes', () => {
  beforeEach(() => {
    estadoClientes.clientes = [];
    estadoClientes.cargando = false;
  });

  it('carga clientes desde la API y actualiza tabla y selector de ventas', async () => {
    const mockDoc = crearMockDocument();
    const mockApi = {
      get: async (endpoint) => {
        if (endpoint === '/clientes/') {
          return [
            { id: 1, nombre: 'Ana Beltrán', email: 'ana@example.com' },
            { id: 2, nombre: 'Carlos Duarte', email: 'carlos@example.com' },
          ];
        }
        throw new Error('Not found');
      }
    };

    await cargarClientes({ apiClient: mockApi, context: mockDoc });

    assert.equal(estadoClientes.clientes.length, 2);
    const tbody = mockDoc.getElementById('tabla-clientes').querySelector('tbody');
    assert.equal(tbody.children.length, 2);
    assert.equal(mockDoc.getElementById('clientes-listado-vacio').hidden, true);

    const selectVentas = mockDoc.getElementById('venta-cliente');
    // 1 opción placeholder + 2 clientes
    assert.equal(selectVentas.children.length, 3);
  });

  it('muestra estado listado vacío cuando no hay clientes', async () => {
    const mockDoc = crearMockDocument();
    const mockApi = {
      get: async () => []
    };

    await cargarClientes({ apiClient: mockApi, context: mockDoc });

    assert.equal(estadoClientes.clientes.length, 0);
    assert.equal(mockDoc.getElementById('clientes-listado-vacio').hidden, false);
  });

  it('consulta cliente existente por ID mediante consultarClientePorId', async () => {
    const mockApi = {
      get: async (endpoint) => {
        if (endpoint === '/clientes/1') {
          return { id: 1, nombre: 'Ana Beltrán', email: 'ana@example.com' };
        }
        throw new ApiError('Not found', 404);
      }
    };

    const cliente = await consultarClientePorId(1, { apiClient: mockApi });
    assert.equal(cliente.id, 1);
    assert.equal(cliente.nombre, 'Ana Beltrán');
  });
});

describe('Módulo de Clientes: Envío de Alta y Resiliencia (Caso G-03)', () => {
  beforeEach(() => {
    estadoClientes.clientes = [];
    estadoClientes.enviando = false;
  });

  it('Caso G-03 Exitoso: envía POST /clientes/, recibe 201 Created y resetea formulario', async () => {
    const mockDoc = crearMockDocument();
    mockDoc.getElementById('cliente-nombre').value = 'Mariana López';
    mockDoc.getElementById('cliente-email').value = 'mariana@example.com';

    const mockApi = {
      post: async (endpoint, body) => {
        assert.equal(endpoint, '/clientes/');
        assert.equal(body.nombre, 'Mariana López');
        assert.equal(body.email, 'mariana@example.com');
        return { id: 3, nombre: body.nombre, email: body.email };
      },
      get: async () => [{ id: 3, nombre: 'Mariana López', email: 'mariana@example.com' }]
    };

    const res = await enviarAltaCliente({ apiClient: mockApi, context: mockDoc });
    assert.equal(res.exito, true);

    const feedback = mockDoc.getElementById('clientes-feedback');
    assert.equal(feedback.hidden, false);
    assert.match(feedback.textContent, /OK|correctamente/i);

    // Formulario reseteado
    assert.equal(mockDoc.getElementById('cliente-nombre').value, '');
    assert.equal(mockDoc.getElementById('cliente-email').value, '');
  });

  it('Caso G-03 Rechazo 409 Conflict: ante email duplicado, muestra error y PRESERVA los inputs', async () => {
    const mockDoc = crearMockDocument();
    mockDoc.getElementById('cliente-nombre').value = 'Nombre Preservado';
    mockDoc.getElementById('cliente-email').value = 'duplicado@example.com';

    const mockApi = {
      post: async () => {
        throw new ApiError('El correo electrónico ya se encuentra registrado', 409);
      }
    };

    const res = await enviarAltaCliente({ apiClient: mockApi, context: mockDoc });
    assert.equal(res.exito, false);

    const feedback = mockDoc.getElementById('clientes-feedback');
    assert.equal(feedback.hidden, false);
    assert.match(feedback.textContent, /Error|ya se encuentra registrado/i);

    // INVARIANTE: Los inputs no se borran (RN-CLI-01)
    assert.equal(mockDoc.getElementById('cliente-nombre').value, 'Nombre Preservado');
    assert.equal(mockDoc.getElementById('cliente-email').value, 'duplicado@example.com');
  });
});
