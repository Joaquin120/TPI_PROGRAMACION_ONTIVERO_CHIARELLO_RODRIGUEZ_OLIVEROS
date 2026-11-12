/**
 * Módulo de Catálogo de Libros (Ejercicio 1 / US-001, US-002, US-003).
 * Maneja la interacción con la API REST, paginación, búsqueda por título,
 * renderizado seguro y modal accesible de detalle con autorías.
 */

import { api as defaultApi } from './api.js';

export const estadoCatalogo = {
  offset: 0,
  limit: 20,
  titulo: '',
  cargando: false,
  libros: [],
  total: 0,
  ultimoLibroDetalle: null,
};

/**
 * Formatea un valor numérico como moneda local ($1500,00).
 * @param {number|string} valor
 * @returns {string}
 */
export function formatearPrecio(valor) {
  const num = typeof valor === 'number' ? valor : parseFloat(valor);
  if (isNaN(num)) return '$0,00';
  return '$' + num.toFixed(2).replace('.', ',');
}

/**
 * Devuelve la etiqueta descriptiva del género.
 * Si es nulo o vacío, cumple con la regla RN-LIB-06 retornando «Sin clasificar».
 * @param {string|null|undefined} genero
 * @returns {string}
 */
export function resolverEtiquetaGenero(genero) {
  if (genero === null || genero === undefined || String(genero).trim() === '') {
    return 'Sin clasificar';
  }
  return String(genero).trim();
}

/**
 * Crea un elemento de fila de tabla (TR) seguro para un libro del catálogo.
 * @param {Object} libro
 * @param {(id: number) => void} [onVerDetalle]
 * @returns {HTMLTableRowElement}
 */
export function crearFilaLibro(libro, onVerDetalle) {
  const tr = document.createElement('tr');
  tr.dataset.id = libro.id;

  // Título
  const tdTitulo = document.createElement('td');
  tdTitulo.textContent = libro.titulo;
  tr.appendChild(tdTitulo);

  // ISBN
  const tdIsbn = document.createElement('td');
  tdIsbn.textContent = libro.isbn;
  tr.appendChild(tdIsbn);

  // Editorial
  const tdEditorial = document.createElement('td');
  tdEditorial.textContent = libro.editorial || '—';
  tr.appendChild(tdEditorial);

  // Género (RN-LIB-06)
  const tdGenero = document.createElement('td');
  const etiquetaGenero = resolverEtiquetaGenero(libro.genero);
  if (etiquetaGenero === 'Sin clasificar') {
    const badge = document.createElement('span');
    badge.className = 'badge-sin-clasificar';
    badge.textContent = 'Sin clasificar';
    tdGenero.appendChild(badge);
  } else {
    tdGenero.textContent = etiquetaGenero;
  }
  tr.appendChild(tdGenero);

  // Precio formateado
  const tdPrecio = document.createElement('td');
  tdPrecio.textContent = formatearPrecio(libro.precio);
  tr.appendChild(tdPrecio);

  // Acciones (botón Ver Detalle)
  const tdAcciones = document.createElement('td');
  const btnDetalle = document.createElement('button');
  btnDetalle.type = 'button';
  btnDetalle.className = 'boton-detalle-libro';
  btnDetalle.textContent = 'Ver detalle';
  btnDetalle.setAttribute('aria-label', `Ver detalle y autores de ${libro.titulo}`);
  if (onVerDetalle) {
    btnDetalle.addEventListener('click', () => onVerDetalle(libro.id));
  }
  tdAcciones.appendChild(btnDetalle);
  tr.appendChild(tdAcciones);

  return tr;
}

/**
 * Consulta y renderiza el catálogo de libros aplicando paginación y filtros.
 * @param {Object} [opciones={}]
 * @param {any} [opciones.apiClient=defaultApi]
 * @param {Document|HTMLElement} [opciones.context=document]
 */
export async function cargarCatalogoApi(opciones = {}) {
  const client = opciones.apiClient || (typeof window !== 'undefined' ? window.api : defaultApi);
  const doc = opciones.context || (typeof document !== 'undefined' ? document : null);
  if (!doc) return [];

  const loadingEl = doc.getElementById('catalogo-cargando');
  const sinResultadosEl = doc.getElementById('catalogo-sin-resultados');
  const listadoVacioEl = doc.getElementById('catalogo-listado-vacio');
  const errorEl = doc.getElementById('catalogo-error');
  const tablaContenedor = doc.getElementById('catalogo-tabla-contenedor');
  const cuerpoTabla = doc.getElementById('catalogo-cuerpo-tabla');

  // 1. Activar estado de carga y ocultar otros estados
  estadoCatalogo.cargando = true;
  if (loadingEl) loadingEl.hidden = false;
  if (sinResultadosEl) sinResultadosEl.hidden = true;
  if (listadoVacioEl) listadoVacioEl.hidden = true;
  if (errorEl) {
    errorEl.hidden = true;
    errorEl.textContent = '';
  }
  if (tablaContenedor) tablaContenedor.hidden = true;

  const params = {
    limit: estadoCatalogo.limit,
    offset: estadoCatalogo.offset,
  };
  if (estadoCatalogo.titulo && estadoCatalogo.titulo.trim() !== '') {
    params.titulo = estadoCatalogo.titulo.trim();
  }

  try {
    const data = await client.get('/libros/', params);
    estadoCatalogo.cargando = false;
    if (loadingEl) loadingEl.hidden = true;

    const lista = Array.isArray(data) ? data : (data && Array.isArray(data.items) ? data.items : []);
    estadoCatalogo.libros = lista;

    if (lista.length === 0) {
      if (cuerpoTabla) cuerpoTabla.innerHTML = '';
      if (estadoCatalogo.titulo && estadoCatalogo.titulo.trim() !== '') {
        // Búsqueda sin coincidencias
        if (sinResultadosEl) sinResultadosEl.hidden = false;
      } else {
        // Catálogo completamente vacío
        if (listadoVacioEl) listadoVacioEl.hidden = false;
      }
      actualizarPaginacionDom(0, doc);
      return [];
    }

    // Renderizar filas dinámicamente
    if (cuerpoTabla) {
      cuerpoTabla.innerHTML = '';
      lista.forEach((libro) => {
        const fila = crearFilaLibro(libro, (id) => abrirModalDetalleLibro(id, { apiClient: client, context: doc }));
        cuerpoTabla.appendChild(fila);
      });
    }

    if (tablaContenedor) tablaContenedor.hidden = false;
    actualizarPaginacionDom(lista.length, doc);
    return lista;
  } catch (error) {
    estadoCatalogo.cargando = false;
    if (loadingEl) loadingEl.hidden = true;
    if (errorEl) {
      errorEl.textContent = 'Error de conexión al cargar el catálogo: ' + (error.message || 'Falla de red');
      errorEl.hidden = false;
    }
    actualizarPaginacionDom(0, doc);
    throw error;
  }
}

/**
 * Actualiza los controles del DOM para paginación (botones e indicador).
 * @param {number} cantidadEnPagina
 * @param {Document|HTMLElement} doc
 */
export function actualizarPaginacionDom(cantidadEnPagina, doc = document) {
  if (!doc) return;
  const btnAnterior = doc.getElementById('catalogo-anterior');
  const btnSiguiente = doc.getElementById('catalogo-siguiente');
  const infoPaginacion = doc.getElementById('catalogo-info-paginacion');

  const paginaActual = Math.floor(estadoCatalogo.offset / estadoCatalogo.limit) + 1;
  if (infoPaginacion) {
    infoPaginacion.textContent = `Página ${paginaActual}`;
  }
  if (btnAnterior) {
    btnAnterior.disabled = estadoCatalogo.offset === 0;
  }
  if (btnSiguiente) {
    // Si la cantidad de libros recibida es menor que el límite, no hay página siguiente
    btnSiguiente.disabled = cantidadEnPagina < estadoCatalogo.limit;
  }
}

/**
 * Ejecuta búsqueda por título con reinicio automático de offset = 0 (RN-LIB-07).
 * @param {string} termino
 * @param {Object} [opciones={}]
 */
export async function buscarPorTitulo(termino, opciones = {}) {
  estadoCatalogo.titulo = typeof termino === 'string' ? termino : '';
  estadoCatalogo.offset = 0; // RN-LIB-07: siempre reiniciar offset a 0
  return cargarCatalogoApi(opciones);
}

/**
 * Avanza una página en la paginación.
 * @param {Object} [opciones={}]
 */
export async function avanzarPagina(opciones = {}) {
  estadoCatalogo.offset += estadoCatalogo.limit;
  return cargarCatalogoApi(opciones);
}

/**
 * Retrocede una página en la paginación.
 * @param {Object} [opciones={}]
 */
export async function retrocederPagina(opciones = {}) {
  if (estadoCatalogo.offset >= estadoCatalogo.limit) {
    estadoCatalogo.offset -= estadoCatalogo.limit;
  } else {
    estadoCatalogo.offset = 0;
  }
  return cargarCatalogoApi(opciones);
}

/**
 * Cambia el tamaño de página y reinicia el desplazamiento a 0.
 * @param {number} nuevoLimite
 * @param {Object} [opciones={}]
 */
export async function cambiarLimite(nuevoLimite, opciones = {}) {
  const limite = parseInt(nuevoLimite, 10);
  if (!isNaN(limite) && limite >= 1 && limite <= 100) {
    estadoCatalogo.limit = limite;
    estadoCatalogo.offset = 0;
    return cargarCatalogoApi(opciones);
  }
}

/**
 * Abre el modal accesible de detalle de libro consultando GET /api/libros/{id}.
 * @param {number} libroId
 * @param {Object} [opciones={}]
 */
export async function abrirModalDetalleLibro(libroId, opciones = {}) {
  const client = opciones.apiClient || (typeof window !== 'undefined' ? window.api : defaultApi);
  const doc = opciones.context || (typeof document !== 'undefined' ? document : null);
  if (!doc) return;

  const modal = doc.getElementById('modal-detalle-libro');
  if (!modal) return;

  const tituloEl = doc.getElementById('modal-libro-titulo');
  const isbnEl = doc.getElementById('modal-libro-isbn');
  const editorialEl = doc.getElementById('modal-libro-editorial');
  const generoEl = doc.getElementById('modal-libro-genero');
  const precioEl = doc.getElementById('modal-libro-precio');
  const stockEl = doc.getElementById('modal-libro-stock');
  const autoresEl = doc.getElementById('modal-libro-autores');

  if (autoresEl) autoresEl.innerHTML = '<li>Cargando autores...</li>';
  modal.hidden = false;

  try {
    const libro = await client.get(`/libros/${libroId}`);
    estadoCatalogo.ultimoLibroDetalle = libro;

    if (tituloEl) tituloEl.textContent = libro.titulo;
    if (isbnEl) isbnEl.textContent = libro.isbn;
    if (editorialEl) editorialEl.textContent = libro.editorial || '—';
    if (generoEl) generoEl.textContent = resolverEtiquetaGenero(libro.genero);
    if (precioEl) precioEl.textContent = formatearPrecio(libro.precio);
    if (stockEl) stockEl.textContent = libro.stock !== undefined ? String(libro.stock) : '0';

    if (autoresEl) {
      autoresEl.innerHTML = '';
      if (!libro.autores || libro.autores.length === 0) {
        const li = document.createElement('li');
        li.textContent = 'Sin autores registrados';
        autoresEl.appendChild(li);
      } else {
        libro.autores.forEach((a) => {
          const li = document.createElement('li');
          li.textContent = `${a.nombre} — Rol: ${a.rol} (Orden ${a.orden})`;
          autoresEl.appendChild(li);
        });
      }
    }
    return libro;
  } catch (error) {
    if (autoresEl) {
      autoresEl.innerHTML = `<li class="error">Error al cargar autores: ${error.message}</li>`;
    }
    throw error;
  }
}

/**
 * Cierra el modal de detalle de libro.
 * @param {Document|HTMLElement} [doc=document]
 */
export function cerrarModalDetalleLibro(doc = document) {
  if (!doc) return;
  const modal = doc.getElementById('modal-detalle-libro');
  if (modal) modal.hidden = true;
}

// Inicialización de eventos del DOM para el catálogo
export function inicializarEventosCatalogo(doc = document) {
  if (!doc) return;

  const formBusqueda = doc.getElementById('form-catalogo-buscar');
  const inputBusqueda = doc.getElementById('catalogo-busqueda');
  const btnAnterior = doc.getElementById('catalogo-anterior');
  const btnSiguiente = doc.getElementById('catalogo-siguiente');
  const selectLimite = doc.getElementById('catalogo-limite');
  const btnCerrarModal = doc.getElementById('modal-libro-cerrar');
  const modal = doc.getElementById('modal-detalle-libro');

  if (formBusqueda) {
    formBusqueda.addEventListener('submit', (e) => {
      e.preventDefault();
      buscarPorTitulo(inputBusqueda ? inputBusqueda.value : '', { context: doc });
    });
  }

  if (inputBusqueda) {
    let timeoutId;
    inputBusqueda.addEventListener('input', () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        buscarPorTitulo(inputBusqueda.value, { context: doc });
      }, 300);
    });
  }

  if (btnAnterior) {
    btnAnterior.addEventListener('click', () => retrocederPagina({ context: doc }));
  }

  if (btnSiguiente) {
    btnSiguiente.addEventListener('click', () => avanzarPagina({ context: doc }));
  }

  if (selectLimite) {
    selectLimite.addEventListener('change', (e) => cambiarLimite(e.target.value, { context: doc }));
  }

  if (btnCerrarModal) {
    btnCerrarModal.addEventListener('click', () => cerrarModalDetalleLibro(doc));
  }

  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        cerrarModalDetalleLibro(doc);
      }
    });
  }
}

// Exposición global para navegador
if (typeof window !== 'undefined') {
  window.catalogo = {
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
    inicializarEventosCatalogo,
  };
}

