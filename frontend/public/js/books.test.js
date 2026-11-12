import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import {
  estadoAltaLibro,
  cargarEditorialesYGeneros,
  verificarAutorPorId,
  agregarAutorALibro,
  quitarAutorDeLibro,
  validarDatosLibro,
  limpiarFormularioLibro,
  enviarAltaLibro,
} from './books.js';

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
      add(c) { this.classes.push(c); },
      contains(c) { return this.classes.includes(c); }
    },
    reset() {
      this.value = '';
    }
  };
}

function crearMockDocument() {
  const elements = {
    'form-alta-libro': crearMockElement('form', 'form-alta-libro'),
    'libro-titulo': crearMockElement('input', 'libro-titulo'),
    'libro-isbn': crearMockElement('input', 'libro-isbn'),
    'libro-precio': crearMockElement('input', 'libro-precio'),
    'libro-stock': crearMockElement('input', 'libro-stock'),
    'libro-editorial': crearMockElement('select', 'libro-editorial'),
    'libro-genero': crearMockElement('select', 'libro-genero'),
    'autor-id-buscar': crearMockElement('input', 'autor-id-buscar'),
    'autor-btn-verificar': crearMockElement('button', 'autor-btn-verificar'),
    'autor-error-feedback': crearMockElement('p', 'autor-error-feedback'),
    'autor-verificado-info': crearMockElement('div', 'autor-verificado-info'),
    'autor-verificado-nombre': crearMockElement('span', 'autor-verificado-nombre'),
    'autor-rol-select': crearMockElement('select', 'autor-rol-select'),
    'autor-btn-agregar': crearMockElement('button', 'autor-btn-agregar'),
    'tabla-autores-agregados': crearMockElement('table', 'tabla-autores-agregados'),
    'cuerpo-autores-agregados': crearMockElement('tbody', 'cuerpo-autores-agregados'),
    'libro-btn-submit': crearMockElement('button', 'libro-btn-submit'),
    'libros-feedback': crearMockElement('div', 'libros-feedback'),
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
    }
  };
}

describe('Alta de Libros: Validaciones de campos (validarDatosLibro)', () => {
  it('valida exitosamente un libro con campos completos y reglas satisfechas', () => {
    const datos = {
      titulo: 'El principito',
      isbn: '978-84-376-0494-7',
      precio: 1500,
      stock: 10,
      editorial_id: 1,
      genero_id: 1,
      autores: [{ autor_id: 1, rol: 'autor', orden: 1 }],
    };
    const res = validarDatosLibro(datos);
    assert.strictEqual(res.valido, true);
    assert.strictEqual(res.errores.length, 0);
  });

  it('rechaza precio no positivo (RN-LIB-02: precio > 0)', () => {
    const datosCero = {
      titulo: 'Gratis',
      isbn: '123',
      precio: 0,
      stock: 5,
      editorial_id: 1,
      autores: [{ autor_id: 1, rol: 'autor', orden: 1 }],
    };
    const resCero = validarDatosLibro(datosCero);
    assert.strictEqual(resCero.valido, false);
    assert.ok(resCero.errores.some((e) => e.includes('precio')));

    const datosNegativo = { ...datosCero, precio: -100 };
    const resNeg = validarDatosLibro(datosNegativo);
    assert.strictEqual(resNeg.valido, false);
  });

  it('rechaza stock negativo (RN-LIB-03: stock >= 0)', () => {
    const datos = {
      titulo: 'Libro',
      isbn: '123',
      precio: 500,
      stock: -1,
      editorial_id: 1,
      autores: [{ autor_id: 1, rol: 'autor', orden: 1 }],
    };
    const res = validarDatosLibro(datos);
    assert.strictEqual(res.valido, false);
    assert.ok(res.errores.some((e) => e.includes('stock')));
  });

  it('rechaza libro sin autores asociados (RN-LIB-04: autores.length >= 1)', () => {
    const datos = {
      titulo: 'Sin autor',
      isbn: '123',
      precio: 500,
      stock: 0,
      editorial_id: 1,
      autores: [],
    };
    const res = validarDatosLibro(datos);
    assert.strictEqual(res.valido, false);
    assert.ok(res.errores.some((e) => e.includes('autor')));
  });
});

describe('Alta de Libros: Carga de selectores auxiliares (cargarEditorialesYGeneros)', () => {
  let mockDoc;

  beforeEach(() => {
    mockDoc = crearMockDocument();
    globalThis.document = mockDoc;
  });

  it('puebla editoriales y géneros en el DOM', async () => {
    const mockApiClient = {
      async get(endpoint) {
        if (endpoint === '/editoriales/') {
          return [{ id: 1, nombre: 'Editorial Sudamericana' }];
        }
        if (endpoint === '/generos/') {
          return [{ id: 1, nombre: 'Fábula' }];
        }
        return [];
      }
    };

    const res = await cargarEditorialesYGeneros({ apiClient: mockApiClient, context: mockDoc });
    assert.strictEqual(res.editoriales.length, 1);
    assert.strictEqual(res.generos.length, 1);

    const selectEditorial = mockDoc.getElementById('libro-editorial');
    const selectGenero = mockDoc.getElementById('libro-genero');

    assert.ok(selectEditorial.children.length >= 1);
    assert.ok(selectGenero.children.length >= 1);
  });
});

describe('Alta de Libros: Verificación de autores por ID (verificarAutorPorId, agregarAutorALibro)', () => {
  let mockDoc;

  beforeEach(() => {
    mockDoc = crearMockDocument();
    globalThis.document = mockDoc;
    estadoAltaLibro.autoresAsignados = [];
    estadoAltaLibro.autorVerificadoActual = null;
  });

  it('verifica autor existente consultando GET /autores/{id} y muestra su nombre', async () => {
    const mockApiClient = {
      async get(endpoint) {
        assert.strictEqual(endpoint, '/autores/1');
        return { id: 1, nombre: 'Antoine de Saint-Exupéry' };
      }
    };

    const autor = await verificarAutorPorId(1, { apiClient: mockApiClient, context: mockDoc });
    assert.ok(autor);
    assert.strictEqual(autor.nombre, 'Antoine de Saint-Exupéry');
    assert.strictEqual(mockDoc.getElementById('autor-verificado-nombre').textContent, 'Antoine de Saint-Exupéry');
    assert.strictEqual(mockDoc.getElementById('autor-verificado-info').hidden, false);
  });

  it('muestra mensaje descriptivo ante autor no encontrado (404)', async () => {
    const mockApiClient = {
      async get() {
        const error = new Error('Not found');
        error.status = 404;
        throw error;
      }
    };

    const autor = await verificarAutorPorId(999, { apiClient: mockApiClient, context: mockDoc });
    assert.strictEqual(autor, null);
    const errorEl = mockDoc.getElementById('autor-error-feedback');
    assert.strictEqual(errorEl.hidden, false);
    assert.ok(errorEl.textContent.includes('No existe ningún autor'));
  });

  it('agrega autor a la lista asignando rol y orden secuencial', () => {
    estadoAltaLibro.autorVerificadoActual = { id: 1, nombre: 'Antoine de Saint-Exupéry' };
    const agregado = agregarAutorALibro('autor', mockDoc);

    assert.strictEqual(agregado, true);
    assert.strictEqual(estadoAltaLibro.autoresAsignados.length, 1);
    assert.strictEqual(estadoAltaLibro.autoresAsignados[0].autor_id, 1);
    assert.strictEqual(estadoAltaLibro.autoresAsignados[0].rol, 'autor');
    assert.strictEqual(estadoAltaLibro.autoresAsignados[0].orden, 1);

    // Segundo autor
    estadoAltaLibro.autorVerificadoActual = { id: 2, nombre: 'Julia M. Peralta' };
    agregarAutorALibro('coautor', mockDoc);
    assert.strictEqual(estadoAltaLibro.autoresAsignados.length, 2);
    assert.strictEqual(estadoAltaLibro.autoresAsignados[1].orden, 2);

    // Quitar autor 1 renumera el orden de autor 2 a 1
    quitarAutorDeLibro(1, mockDoc);
    assert.strictEqual(estadoAltaLibro.autoresAsignados.length, 1);
    assert.strictEqual(estadoAltaLibro.autoresAsignados[0].autor_id, 2);
    assert.strictEqual(estadoAltaLibro.autoresAsignados[0].orden, 1);
  });
});

describe('Alta de Libros: Envío de formulario y resiliencia ante errores (enviarAltaLibro, G-02)', () => {
  let mockDoc;

  beforeEach(() => {
    mockDoc = crearMockDocument();
    globalThis.document = mockDoc;
    estadoAltaLibro.autoresAsignados = [{ autor_id: 1, nombre: 'Antoine de Saint-Exupéry', rol: 'autor', orden: 1 }];

    mockDoc.getElementById('libro-titulo').value = 'El principito';
    mockDoc.getElementById('libro-isbn').value = '978-84-376-0494-7';
    mockDoc.getElementById('libro-precio').value = '1500.00';
    mockDoc.getElementById('libro-stock').value = '10';
    mockDoc.getElementById('libro-editorial').value = '1';
    mockDoc.getElementById('libro-genero').value = '1';
  });

  it('Caso G-02 Exitoso: envía POST /libros/, recibe 201 Created y muestra feedback', async () => {
    let payloadEnviado = null;
    let callbackEjecutado = false;

    const mockApiClient = {
      async post(endpoint, body) {
        assert.strictEqual(endpoint, '/libros/');
        payloadEnviado = body;
        return {
          id: 1,
          titulo: body.titulo,
          isbn: body.isbn,
          precio: body.precio,
          stock: body.stock
        };
      }
    };

    const res = await enviarAltaLibro(null, {
      apiClient: mockApiClient,
      context: mockDoc,
      onExito: () => { callbackEjecutado = true; }
    });

    assert.ok(res);
    assert.strictEqual(payloadEnviado.titulo, 'El principito');
    assert.strictEqual(payloadEnviado.isbn, '978-84-376-0494-7');
    assert.strictEqual(payloadEnviado.autores.length, 1);
    assert.strictEqual(callbackEjecutado, true);

    const feedback = mockDoc.getElementById('libros-feedback');
    assert.strictEqual(feedback.hidden, false);
    assert.ok(feedback.textContent.includes('registrado correctamente'));
  });

  it('Caso G-02 Rechazo 409 Conflict: ante ISBN duplicado, muestra error y PRESERVA el formulario intacto', async () => {
    const mockApiClient = {
      async post() {
        const error = new Error('Conflict');
        error.status = 409;
        error.data = { detail: "El ISBN '978-84-376-0494-7' ya se encuentra registrado" };
        throw error;
      }
    };

    await assert.rejects(async () => {
      await enviarAltaLibro(null, { apiClient: mockApiClient, context: mockDoc });
    }, /Conflict/);

    // Verificación de resiliencia: Formulario intacto
    assert.strictEqual(mockDoc.getElementById('libro-titulo').value, 'El principito');
    assert.strictEqual(mockDoc.getElementById('libro-isbn').value, '978-84-376-0494-7');
    assert.strictEqual(estadoAltaLibro.autoresAsignados.length, 1);

    // Mensaje de conflicto mostrado al usuario
    const feedback = mockDoc.getElementById('libros-feedback');
    assert.strictEqual(feedback.hidden, false);
    assert.ok(feedback.textContent.includes('ya se encuentra registrado'));
  });
});
