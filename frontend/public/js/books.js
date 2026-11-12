/**
 * Módulo para el Alta de Libros (Ejercicio 2A / US-004).
 * Maneja la carga de catálogos auxiliares (editoriales, géneros),
 * verificación y asignación de autores por ID, validaciones y envío a POST /api/libros/.
 */

import { api as defaultApi } from './api.js';

export const estadoAltaLibro = {
  editoriales: [],
  generos: [],
  autorVerificadoActual: null,
  autoresAsignados: [], // Array de { autor_id, nombre, rol, orden }
  enviando: false,
};

/**
 * Carga las editoriales y géneros desde la API y puebla los selectores correspondientes.
 * @param {Object} [opciones={}]
 * @param {any} [opciones.apiClient=defaultApi]
 * @param {Document|HTMLElement} [opciones.context=document]
 */
export async function cargarEditorialesYGeneros(opciones = {}) {
  const client = opciones.apiClient || (typeof window !== 'undefined' ? window.api : defaultApi);
  const doc = opciones.context || (typeof document !== 'undefined' ? document : null);
  if (!doc) return;

  const selectEditorial = doc.getElementById('libro-editorial');
  const selectGenero = doc.getElementById('libro-genero');

  try {
    const [editoriales, generos] = await Promise.all([
      client.get('/editoriales/'),
      client.get('/generos/'),
    ]);

    estadoAltaLibro.editoriales = Array.isArray(editoriales) ? editoriales : [];
    estadoAltaLibro.generos = Array.isArray(generos) ? generos : [];

    if (selectEditorial) {
      selectEditorial.innerHTML = '<option value="" disabled selected>Seleccione una editorial</option>';
      estadoAltaLibro.editoriales.forEach((ed) => {
        const opt = doc.createElement('option');
        opt.value = ed.id;
        opt.textContent = ed.nombre;
        selectEditorial.appendChild(opt);
      });
    }

    if (selectGenero) {
      // Opción nula por defecto (RN-LIB-06)
      selectGenero.innerHTML = '<option value="" selected>Sin clasificar</option>';
      estadoAltaLibro.generos.forEach((gen) => {
        const opt = doc.createElement('option');
        opt.value = gen.id;
        opt.textContent = gen.nombre;
        selectGenero.appendChild(opt);
      });
    }

    return { editoriales: estadoAltaLibro.editoriales, generos: estadoAltaLibro.generos };
  } catch (error) {
    console.error('Error al cargar editoriales y géneros:', error);
    throw error;
  }
}

/**
 * Consulta y verifica la existencia de un autor por su ID consultando GET /api/autores/{id}.
 * @param {number|string} autorId
 * @param {Object} [opciones={}]
 */
export async function verificarAutorPorId(autorId, opciones = {}) {
  const client = opciones.apiClient || (typeof window !== 'undefined' ? window.api : defaultApi);
  const doc = opciones.context || (typeof document !== 'undefined' ? document : null);
  if (!doc) return null;

  const errorEl = doc.getElementById('autor-error-feedback');
  const infoEl = doc.getElementById('autor-verificado-info');
  const nombreEl = doc.getElementById('autor-verificado-nombre');

  if (errorEl) {
    errorEl.hidden = true;
    errorEl.textContent = '';
  }
  if (infoEl) infoEl.hidden = true;
  estadoAltaLibro.autorVerificadoActual = null;

  const idNum = parseInt(autorId, 10);
  if (isNaN(idNum) || idNum <= 0) {
    if (errorEl) {
      errorEl.textContent = 'Ingrese un identificador numérico de autor válido.';
      errorEl.hidden = false;
    }
    return null;
  }

  try {
    const autor = await client.get(`/autores/${idNum}`);
    estadoAltaLibro.autorVerificadoActual = autor;

    if (nombreEl) nombreEl.textContent = autor.nombre;
    if (infoEl) infoEl.hidden = false;
    return autor;
  } catch (error) {
    if (errorEl) {
      errorEl.textContent = error.status === 404
        ? `No existe ningún autor con el ID ${idNum}.`
        : `Error al verificar autor: ${error.message}`;
      errorEl.hidden = false;
    }
    return null;
  }
}

/**
 * Agrega el autor verificado actual a la lista de autorías con su rol y orden correlativo.
 * @param {string} rol
 * @param {Document|HTMLElement} [doc=document]
 */
export function agregarAutorALibro(rol, doc = document) {
  if (!doc || !estadoAltaLibro.autorVerificadoActual) return false;

  const autor = estadoAltaLibro.autorVerificadoActual;
  const yaExiste = estadoAltaLibro.autoresAsignados.some((a) => a.autor_id === autor.id);
  const errorEl = doc.getElementById('autor-error-feedback');

  if (yaExiste) {
    if (errorEl) {
      errorEl.textContent = `El autor "${autor.nombre}" ya está agregado a este libro.`;
      errorEl.hidden = false;
    }
    return false;
  }

  const nuevoOrden = estadoAltaLibro.autoresAsignados.length + 1;
  const nuevaAutoria = {
    autor_id: autor.id,
    nombre: autor.nombre,
    rol: rol || 'autor',
    orden: nuevoOrden,
  };

  estadoAltaLibro.autoresAsignados.push(nuevaAutoria);

  // Ocultar caja de verificación y resetear campo de ID
  const infoEl = doc.getElementById('autor-verificado-info');
  const inputId = doc.getElementById('autor-id-buscar');
  if (infoEl) infoEl.hidden = true;
  if (inputId) inputId.value = '';
  if (errorEl) errorEl.hidden = true;
  estadoAltaLibro.autorVerificadoActual = null;

  renderizarTablaAutoresAgregados(doc);
  return true;
}

/**
 * Quita una autoría de la lista y renumera el orden correlativo.
 * @param {number} autorId
 * @param {Document|HTMLElement} [doc=document]
 */
export function quitarAutorDeLibro(autorId, doc = document) {
  estadoAltaLibro.autoresAsignados = estadoAltaLibro.autoresAsignados.filter((a) => a.autor_id !== autorId);
  estadoAltaLibro.autoresAsignados.forEach((a, index) => {
    a.orden = index + 1;
  });
  renderizarTablaAutoresAgregados(doc);
}

/**
 * Renderiza visualmente la tabla de autores asignados.
 * @param {Document|HTMLElement} [doc=document]
 */
export function renderizarTablaAutoresAgregados(doc = document) {
  if (!doc) return;
  const tbody = doc.getElementById('cuerpo-autores-agregados');
  if (!tbody) return;

  tbody.innerHTML = '';
  estadoAltaLibro.autoresAsignados.forEach((a) => {
    const tr = doc.createElement('tr');

    const tdOrden = doc.createElement('td');
    tdOrden.textContent = a.orden;
    tr.appendChild(tdOrden);

    const tdId = doc.createElement('td');
    tdId.textContent = a.autor_id;
    tr.appendChild(tdId);

    const tdNombre = doc.createElement('td');
    tdNombre.textContent = a.nombre;
    tr.appendChild(tdNombre);

    const tdRol = doc.createElement('td');
    tdRol.textContent = a.rol;
    tr.appendChild(tdRol);

    const tdAccion = doc.createElement('td');
    const btnQuitar = doc.createElement('button');
    btnQuitar.type = 'button';
    btnQuitar.className = 'boton-quitar-autor';
    btnQuitar.textContent = 'Quitar';
    btnQuitar.addEventListener('click', () => quitarAutorDeLibro(a.autor_id, doc));
    tdAccion.appendChild(btnQuitar);
    tr.appendChild(tdAccion);

    tbody.appendChild(tr);
  });
}

/**
 * Valida los datos del formulario antes del envío.
 * @param {Object} datos
 * @returns {{ valido: boolean, errores: string[] }}
 */
export function validarDatosLibro(datos) {
  const errores = [];

  if (!datos.titulo || String(datos.titulo).trim() === '') {
    errores.push('El título del libro es obligatorio.');
  }

  if (!datos.isbn || String(datos.isbn).trim() === '') {
    errores.push('El ISBN del libro es obligatorio.');
  }

  const precioNum = Number(datos.precio);
  if (isNaN(precioNum) || precioNum <= 0) {
    errores.push('El precio debe ser un número estrictamente positivo (> 0.00).');
  }

  const stockNum = parseInt(datos.stock, 10);
  if (isNaN(stockNum) || stockNum < 0) {
    errores.push('El stock debe ser un número entero mayor o igual a cero.');
  }

  if (!datos.editorial_id || parseInt(datos.editorial_id, 10) <= 0) {
    errores.push('Debe seleccionar una editorial válida.');
  }

  if (!Array.isArray(datos.autores) || datos.autores.length === 0) {
    errores.push('Debe asociar al menos un autor con su rol correspondiente.');
  }

  return {
    valido: errores.length === 0,
    errores,
  };
}

/**
 * Limpia los campos del formulario tras un registro exitoso.
 * @param {Document|HTMLElement} [doc=document]
 */
export function limpiarFormularioLibro(doc = document) {
  if (!doc) return;
  const form = doc.getElementById('form-alta-libro');
  if (form) form.reset();

  estadoAltaLibro.autoresAsignados = [];
  estadoAltaLibro.autorVerificadoActual = null;

  const infoEl = doc.getElementById('autor-verificado-info');
  const errorEl = doc.getElementById('autor-error-feedback');
  if (infoEl) infoEl.hidden = true;
  if (errorEl) {
    errorEl.hidden = true;
    errorEl.textContent = '';
  }

  renderizarTablaAutoresAgregados(doc);
}

/**
 * Maneja el envío del formulario de alta de libro.
 * @param {Event} [evento]
 * @param {Object} [opciones={}]
 */
export async function enviarAltaLibro(evento, opciones = {}) {
  if (evento) evento.preventDefault();
  const client = opciones.apiClient || (typeof window !== 'undefined' ? window.api : defaultApi);
  const doc = opciones.context || (typeof document !== 'undefined' ? document : null);
  if (!doc) return null;

  const feedbackEl = doc.getElementById('libros-feedback');
  const btnSubmit = doc.getElementById('libro-btn-submit');

  const tituloInput = doc.getElementById('libro-titulo');
  const isbnInput = doc.getElementById('libro-isbn');
  const precioInput = doc.getElementById('libro-precio');
  const stockInput = doc.getElementById('libro-stock');
  const editorialSelect = doc.getElementById('libro-editorial');
  const generoSelect = doc.getElementById('libro-genero');

  const payload = {
    titulo: tituloInput ? tituloInput.value.trim() : '',
    isbn: isbnInput ? isbnInput.value.trim() : '',
    precio: precioInput ? parseFloat(precioInput.value) : 0,
    stock: stockInput ? parseInt(stockInput.value, 10) : 0,
    editorial_id: editorialSelect ? parseInt(editorialSelect.value, 10) : 0,
    genero_id: generoSelect && generoSelect.value !== '' ? parseInt(generoSelect.value, 10) : null,
    autores: estadoAltaLibro.autoresAsignados.map((a) => ({
      autor_id: a.autor_id,
      rol: a.rol,
      orden: a.orden,
    })),
  };

  const validacion = validarDatosLibro(payload);
  if (!validacion.valido) {
    if (feedbackEl) {
      feedbackEl.className = 'mensaje feedback-error';
      feedbackEl.textContent = 'No se pudo registrar el libro: ' + validacion.errores.join(' ');
      feedbackEl.hidden = false;
    }
    return null;
  }

  try {
    estadoAltaLibro.enviando = true;
    if (btnSubmit) btnSubmit.disabled = true;

    const respuesta = await client.post('/libros/', payload);

    estadoAltaLibro.enviando = false;
    if (btnSubmit) btnSubmit.disabled = false;

    // Éxito: 201 Created
    if (feedbackEl) {
      feedbackEl.className = 'mensaje feedback-exito';
      feedbackEl.textContent = `Libro registrado correctamente: «${respuesta.titulo}» (ISBN ${respuesta.isbn}).`;
      feedbackEl.hidden = false;
    }

    limpiarFormularioLibro(doc);

    if (opciones.onExito) {
      opciones.onExito(respuesta);
    }

    return respuesta;
  } catch (error) {
    estadoAltaLibro.enviando = false;
    if (btnSubmit) btnSubmit.disabled = false;

    // Resiliencia: Mostrar mensaje de error 409 Conflict o 422 sin resetear formulario
    if (feedbackEl) {
      feedbackEl.className = 'mensaje feedback-error';
      let mensajeError = error.message;
      if (error.status === 409) {
        mensajeError = error.data && error.data.detail
          ? error.data.detail
          : 'Conflicto: el ISBN ya se encuentra registrado.';
      } else if (error.status === 422) {
        mensajeError = error.data && error.data.detail
          ? (Array.isArray(error.data.detail) ? error.data.detail.map((d) => d.msg || d).join(', ') : error.data.detail)
          : 'Error en los datos enviados (422 Unprocessable Entity).';
      }
      feedbackEl.textContent = `Error al registrar libro: ${mensajeError}`;
      feedbackEl.hidden = false;
    }

    // El formulario NO se limpia para permitir su corrección
    throw error;
  }
}

/**
 * Inicializa todos los eventos y carga de datos para el formulario de alta de libros.
 * @param {Document|HTMLElement} [doc=document]
 * @param {Object} [opciones={}]
 */
export function inicializarEventosAltaLibro(doc = document, opciones = {}) {
  if (!doc) return;

  const form = doc.getElementById('form-alta-libro');
  const btnVerificar = doc.getElementById('autor-btn-verificar');
  const inputAutorId = doc.getElementById('autor-id-buscar');
  const btnAgregarAutor = doc.getElementById('autor-btn-agregar');
  const selectRol = doc.getElementById('autor-rol-select');

  if (form) {
    form.addEventListener('submit', (e) => enviarAltaLibro(e, { ...opciones, context: doc }));
  }

  if (btnVerificar && inputAutorId) {
    btnVerificar.addEventListener('click', () => {
      verificarAutorPorId(inputAutorId.value, { ...opciones, context: doc });
    });
  }

  if (btnAgregarAutor && selectRol) {
    btnAgregarAutor.addEventListener('click', () => {
      agregarAutorALibro(selectRol.value, doc);
    });
  }

  // Carga inicial de editoriales y géneros
  cargarEditorialesYGeneros({ ...opciones, context: doc }).catch((err) => {
    console.error('Error al inicializar editoriales y géneros:', err);
  });
}

// Exposición global para navegador
if (typeof window !== 'undefined') {
  window.books = {
    estadoAltaLibro,
    cargarEditorialesYGeneros,
    verificarAutorPorId,
    agregarAutorALibro,
    quitarAutorDeLibro,
    validarDatosLibro,
    enviarAltaLibro,
    limpiarFormularioLibro,
    inicializarEventosAltaLibro,
  };
}

