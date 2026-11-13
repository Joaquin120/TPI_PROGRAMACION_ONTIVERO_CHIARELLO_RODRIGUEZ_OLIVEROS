import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import {
  refrescarCatalogoYSelectores,
  manejarVentaConfirmada,
} from './app.js';
import { estadoCatalogo } from './catalog.js';
import { estadoHistorial } from './history.js';

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
    setAttribute(k, v) { this.attributes[k] = v; },
    getAttribute(k) { return this.attributes[k]; },
    appendChild(child) {
      this.children.push(child);
      return child;
    },
    addEventListener() {},
  };
}

function crearMockDocumentOrquestador() {
  const tbodyTablaLibros = crearMockElement('tbody', 'tbody-libros');
  const tablaLibros = crearMockElement('table', 'tabla-libros');
  tablaLibros.querySelector = (sel) => (sel === 'tbody' ? tbodyTablaLibros : null);

  const tbodyHistorial = crearMockElement('tbody', 'tbody-historial');
  const tablaHistorial = crearMockElement('table', 'tabla-historial');
  tablaHistorial.querySelector = (sel) => (sel === 'tbody' ? tbodyHistorial : null);

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
    'tabla-libros': tablaLibros,
    'libros-listado-vacio': crearMockElement('p', 'libros-listado-vacio'),
    'libro-precio-editar-id': crearMockElement('select', 'libro-precio-editar-id'),
    'venta-libro': crearMockElement('select', 'venta-libro'),
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
  };
}

describe('Orquestador principal (app.js / C-07)', () => {
  beforeEach(() => {
    estadoCatalogo.offset = 0;
    estadoCatalogo.limit = 20;
    estadoCatalogo.titulo = '';
    estadoCatalogo.libros = [];
    estadoHistorial.offset = 0;
    estadoHistorial.limit = 20;
    estadoHistorial.ventas = [];
    estadoHistorial.ventaSeleccionada = null;
  });

  it('refrescarCatalogoYSelectores mantiene los selectores de Ventas y Precio aunque el Catálogo esté filtrado o paginado', async () => {
    const mockDoc = crearMockDocumentOrquestador();
    estadoCatalogo.titulo = 'busqueda-sin-coincidencias';
    estadoCatalogo.offset = 40;

    const llamadas = [];
    const mockApi = {
      get: async (endpoint, params) => {
        llamadas.push({ endpoint, params });
        if (params.titulo) {
          return [];
        }
        return [
          {
            id: 1,
            titulo: 'El principito',
            isbn: '978-84-376-0494-7',
            editorial: 'Planeta',
            genero: 'Ficción',
            stock: 10,
            precio: 1500,
          },
        ];
      },
    };

    const librosSelectores = await refrescarCatalogoYSelectores({
      apiClient: mockApi,
      context: mockDoc,
    });

    // Catálogo respeta su filtro y página, mostrando sin resultados
    assert.equal(llamadas[0].endpoint, '/libros/');
    assert.equal(llamadas[0].params.titulo, 'busqueda-sin-coincidencias');
    assert.equal(mockDoc.getElementById('catalogo-sin-resultados').hidden, false);

    // Selectores operativos reciben la consulta independiente sin filtro ni offset
    assert.equal(llamadas[1].endpoint, '/libros/');
    assert.deepEqual(llamadas[1].params, { limit: 100, offset: 0 });
    assert.equal(librosSelectores.length, 1);
    assert.equal(mockDoc.getElementById('libro-precio-editar-id').children.length, 1);
    assert.equal(mockDoc.getElementById('venta-libro').children.length, 2);
  });

  it('manejarVentaConfirmada reinicia estadoHistorial.offset = 0 y muestra el comprobante en detalle', async () => {
    const mockDoc = crearMockDocumentOrquestador();
    estadoHistorial.offset = 20;

    const ventaConfirmada = {
      id: 25,
      cliente_id: 1,
      cliente_nombre: 'Ana Beltrán',
      fecha: '2026-11-13T15:00:00Z',
      total: 3000,
      renglones: [
        { id: 1, libro_id: 1, titulo: 'El principito', cantidad: 2, precio_unitario: 1500, subtotal: 3000 },
      ],
    };

    const llamadas = [];
    const mockApi = {
      get: async (endpoint, params) => {
        llamadas.push({ endpoint, params });
        return [ventaConfirmada];
      },
    };

    await manejarVentaConfirmada(ventaConfirmada, {
      apiClient: mockApi,
      context: mockDoc,
    });

    assert.equal(estadoHistorial.offset, 0);
    assert.equal(llamadas[0].endpoint, '/ventas/');
    assert.equal(llamadas[0].params.offset, 0);
    assert.equal(estadoHistorial.ventaSeleccionada.id, 25);
    assert.equal(mockDoc.getElementById('historial-info-paginacion').textContent, 'Página 1');

    const panel = mockDoc.getElementById('tabla-historial-detalle');
    const cabeceraTexto = panel.children[0].children.map((p) => p.textContent).join(' | ');
    assert.match(cabeceraTexto, /V-0025/);
  });
});
