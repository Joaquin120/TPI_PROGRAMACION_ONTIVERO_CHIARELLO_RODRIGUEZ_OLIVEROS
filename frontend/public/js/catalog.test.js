import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import {
  estadoCatalogo,
  formatearPrecio,
  resolverEtiquetaGenero,
  crearFilaLibro,
  cargarCatalogoApi,
  buscarPorTitulo,
  avanzarPagina,
  retrocederPagina,
  cambiarLimite,
  abrirModalDetalleLibro,
  cerrarModalDetalleLibro,
} from './catalog.js';

// Helper para crear un elemento DOM simulado ligero
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
    }
  };
}

// Helper para crear un Document simulado
function crearMockDocument() {
  const elements = {
    'catalogo-cargando': crearMockElement('div', 'catalogo-cargando'),
    'catalogo-sin-resultados': crearMockElement('p', 'catalogo-sin-resultados'),
    'catalogo-listado-vacio': crearMockElement('p', 'catalogo-listado-vacio'),
    'catalogo-error': crearMockElement('div', 'catalogo-error'),
    'catalogo-tabla-contenedor': crearMockElement('div', 'catalogo-tabla-contenedor'),
    'catalogo-cuerpo-tabla': crearMockElement('tbody', 'catalogo-cuerpo-tabla'),
    'catalogo-anterior': crearMockElement('button', 'catalogo-anterior'),
    'catalogo-siguiente': crearMockElement('button', 'catalogo-siguiente'),
    'catalogo-info-paginacion': crearMockElement('span', 'catalogo-info-paginacion'),
    'catalogo-busqueda': crearMockElement('input', 'catalogo-busqueda'),
    'modal-detalle-libro': crearMockElement('div', 'modal-detalle-libro'),
    'modal-libro-titulo': crearMockElement('h3', 'modal-libro-titulo'),
    'modal-libro-isbn': crearMockElement('span', 'modal-libro-isbn'),
    'modal-libro-editorial': crearMockElement('span', 'modal-libro-editorial'),
    'modal-libro-genero': crearMockElement('span', 'modal-libro-genero'),
    'modal-libro-precio': crearMockElement('span', 'modal-libro-precio'),
    'modal-libro-stock': crearMockElement('span', 'modal-libro-stock'),
    'modal-libro-autores': crearMockElement('ul', 'modal-libro-autores'),
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

describe('Catálogo: Funciones de formateo y reglas de presentación', () => {
  it('formatea precios monetarios con dos decimales y coma (formatearPrecio)', () => {
    assert.strictEqual(formatearPrecio(1500), '$1500,00');
    assert.strictEqual(formatearPrecio(3250.5), '$3250,50');
    assert.strictEqual(formatearPrecio('2000.75'), '$2000,75');
    assert.strictEqual(formatearPrecio('invalido'), '$0,00');
  });

  it('resuelve etiqueta de género devolviendo «Sin clasificar» ante valor nulo (RN-LIB-06)', () => {
    assert.strictEqual(resolverEtiquetaGenero(null), 'Sin clasificar');
    assert.strictEqual(resolverEtiquetaGenero(undefined), 'Sin clasificar');
    assert.strictEqual(resolverEtiquetaGenero(''), 'Sin clasificar');
    assert.strictEqual(resolverEtiquetaGenero('   '), 'Sin clasificar');
    assert.strictEqual(resolverEtiquetaGenero('Fábula'), 'Fábula');
    assert.strictEqual(resolverEtiquetaGenero('Terror'), 'Terror');
  });
});

describe('Catálogo: Renderizado de fila de libro (crearFilaLibro)', () => {
  beforeEach(() => {
    globalThis.document = {
      createElement: (tag) => crearMockElement(tag)
    };
  });

  it('genera TR con datos de libro y badge «Sin clasificar» cuando género es null', () => {
    const libro = {
      id: 2,
      titulo: 'Cuentos de terror',
      isbn: '978-987-1111-22-3',
      precio: 2000,
      editorial: 'Ediciones Horizon',
      genero: null
    };

    const fila = crearFilaLibro(libro);
    assert.strictEqual(fila.tagName, 'TR');
    assert.strictEqual(fila.dataset.id, 2);
    assert.strictEqual(fila.children.length, 6);

    // Titulo, ISBN, Editorial, Genero, Precio, Acciones
    assert.strictEqual(fila.children[0].textContent, 'Cuentos de terror');
    assert.strictEqual(fila.children[1].textContent, '978-987-1111-22-3');
    assert.strictEqual(fila.children[2].textContent, 'Ediciones Horizon');

    // Género badge
    const badge = fila.children[3].children[0];
    assert.ok(badge, 'Debe contener un span badge');
    assert.strictEqual(badge.textContent, 'Sin clasificar');

    // Precio
    assert.strictEqual(fila.children[4].textContent, '$2000,00');
  });
});

describe('Catálogo: Carga vía API y gestión de estados (cargarCatalogoApi)', () => {
  let mockDoc;

  beforeEach(() => {
    mockDoc = crearMockDocument();
    globalThis.document = mockDoc;
    estadoCatalogo.offset = 0;
    estadoCatalogo.limit = 20;
    estadoCatalogo.titulo = '';
  });

  it('muestra libros y oculta estados de carga y error en respuesta exitosa 200', async () => {
    const mockApiClient = {
      async get(endpoint, params) {
        assert.strictEqual(endpoint, '/libros/');
        assert.deepStrictEqual(params, { limit: 20, offset: 0 });
        return [
          { id: 1, titulo: 'El principito', isbn: '978-84-376-0494-7', precio: 1500, editorial: 'Sudamericana', genero: 'Fábula' }
        ];
      }
    };

    const resultado = await cargarCatalogoApi({ apiClient: mockApiClient, context: mockDoc });
    assert.strictEqual(resultado.length, 1);
    assert.strictEqual(mockDoc.getElementById('catalogo-cargando').hidden, true);
    assert.strictEqual(mockDoc.getElementById('catalogo-tabla-contenedor').hidden, false);
    assert.strictEqual(mockDoc.getElementById('catalogo-cuerpo-tabla').children.length, 1);
  });

  it('activa estado «Catálogo vacío» cuando el inventario no tiene libros', async () => {
    const mockApiClient = {
      async get() { return []; }
    };

    await cargarCatalogoApi({ apiClient: mockApiClient, context: mockDoc });
    assert.strictEqual(mockDoc.getElementById('catalogo-listado-vacio').hidden, false);
    assert.strictEqual(mockDoc.getElementById('catalogo-sin-resultados').hidden, true);
    assert.strictEqual(mockDoc.getElementById('catalogo-tabla-contenedor').hidden, true);
  });

  it('activa estado «Búsqueda sin coincidencias» cuando hay filtro y lista vacía', async () => {
    const mockApiClient = {
      async get() { return []; }
    };

    estadoCatalogo.titulo = 'inexistente';
    await cargarCatalogoApi({ apiClient: mockApiClient, context: mockDoc });
    assert.strictEqual(mockDoc.getElementById('catalogo-sin-resultados').hidden, false);
    assert.strictEqual(mockDoc.getElementById('catalogo-listado-vacio').hidden, true);
  });

  it('activa estado de error visual cuando la API falla', async () => {
    const mockApiClient = {
      async get() { throw new Error('Falla de conexión 502'); }
    };

    await assert.rejects(async () => {
      await cargarCatalogoApi({ apiClient: mockApiClient, context: mockDoc });
    }, /Falla de conexión 502/);

    const errorEl = mockDoc.getElementById('catalogo-error');
    assert.strictEqual(errorEl.hidden, false);
    assert.ok(errorEl.textContent.includes('Falla de conexión 502'));
  });
});

describe('Catálogo: Búsqueda y Paginación (buscarPorTitulo, avanzar, retroceder, limite)', () => {
  let mockDoc;

  beforeEach(() => {
    mockDoc = crearMockDocument();
    globalThis.document = mockDoc;
    estadoCatalogo.offset = 40;
    estadoCatalogo.limit = 20;
    estadoCatalogo.titulo = '';
  });

  it('reinicia offset = 0 al buscar por título (RN-LIB-07)', async () => {
    let capturedParams = null;
    const mockApiClient = {
      async get(endpoint, params) {
        capturedParams = params;
        return [];
      }
    };

    await buscarPorTitulo('principito', { apiClient: mockApiClient, context: mockDoc });
    assert.strictEqual(estadoCatalogo.offset, 0);
    assert.strictEqual(capturedParams.offset, 0);
    assert.strictEqual(capturedParams.titulo, 'principito');
  });

  it('avanza y retrocede páginas modificando offset de forma consistente', async () => {
    const mockApiClient = { async get() { return [{ id: 1 }]; } };

    estadoCatalogo.offset = 0;
    estadoCatalogo.limit = 20;

    await avanzarPagina({ apiClient: mockApiClient, context: mockDoc });
    assert.strictEqual(estadoCatalogo.offset, 20);

    await retrocederPagina({ apiClient: mockApiClient, context: mockDoc });
    assert.strictEqual(estadoCatalogo.offset, 0);

    // No retrocede por debajo de 0
    await retrocederPagina({ apiClient: mockApiClient, context: mockDoc });
    assert.strictEqual(estadoCatalogo.offset, 0);
  });

  it('cambiarLimite ajusta limit y reinicia offset a 0', async () => {
    const mockApiClient = { async get() { return []; } };
    estadoCatalogo.offset = 60;
    estadoCatalogo.limit = 20;

    await cambiarLimite(50, { apiClient: mockApiClient, context: mockDoc });
    assert.strictEqual(estadoCatalogo.limit, 50);
    assert.strictEqual(estadoCatalogo.offset, 0);
  });
});

describe('Catálogo: Detalle de libro y autores (abrirModalDetalleLibro)', () => {
  let mockDoc;

  beforeEach(() => {
    mockDoc = crearMockDocument();
    globalThis.document = mockDoc;
  });

  it('consulta GET /libros/{id} y renderiza autores con sus roles y orden', async () => {
    const mockApiClient = {
      async get(endpoint) {
        assert.strictEqual(endpoint, '/libros/1');
        return {
          id: 1,
          titulo: 'El principito',
          isbn: '978-84-376-0494-7',
          precio: 1500,
          stock: 8,
          editorial: 'Sudamericana',
          genero: 'Fábula',
          autores: [
            { autor_id: 1, nombre: 'Antoine de Saint-Exupéry', rol: 'autor', orden: 1 }
          ]
        };
      }
    };

    const libro = await abrirModalDetalleLibro(1, { apiClient: mockApiClient, context: mockDoc });
    assert.strictEqual(libro.id, 1);
    assert.strictEqual(mockDoc.getElementById('modal-detalle-libro').hidden, false);
    assert.strictEqual(mockDoc.getElementById('modal-libro-titulo').textContent, 'El principito');
    assert.strictEqual(mockDoc.getElementById('modal-libro-isbn').textContent, '978-84-376-0494-7');
    assert.strictEqual(mockDoc.getElementById('modal-libro-autores').children.length, 1);
    assert.ok(mockDoc.getElementById('modal-libro-autores').children[0].textContent.includes('Antoine de Saint-Exupéry'));
    assert.ok(mockDoc.getElementById('modal-libro-autores').children[0].textContent.includes('Rol: autor'));

    cerrarModalDetalleLibro(mockDoc);
    assert.strictEqual(mockDoc.getElementById('modal-detalle-libro').hidden, true);
  });
});

