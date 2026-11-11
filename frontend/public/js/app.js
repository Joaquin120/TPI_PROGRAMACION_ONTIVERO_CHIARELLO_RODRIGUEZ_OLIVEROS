// JavaScript nativo del TPI — Librería El Faro de los Libros.
// Ejercicio 3, Ejercicio 4 completo (libros y clientes), Ejercicio 5 (ventas e
// historial) y Ejercicio 6 (persistencia con localStorage). Vanilla JS, sin
// fetch ni librerías. Se abre con doble clic en index.html (file://).

'use strict';

// ============================================================
// 1. MODELO DE DATOS INICIAL (IDs estables, datos ficticios)
// ============================================================

const editoriales = [
  { id: 1, nombre: 'Editorial Sudamericana' },
  { id: 2, nombre: 'Ediciones Horizon' },
  { id: 3, nombre: 'Editorial Técnica UTN' }
];

const generos = [
  { id: 1, nombre: 'Fábula' },
  { id: 2, nombre: 'Terror' },
  { id: 3, nombre: 'Educación' }
];

const autores = [
  { id: 1, nombre: 'Antoine de Saint-Exupéry' },
  { id: 2, nombre: 'Julia M. Peralta' },
  { id: 3, nombre: 'María Gómez' },
  { id: 4, nombre: 'Luis Ramírez' }
];

// idGenero: null = sin género asignado (se muestra «Sin clasificar»).
// autores: array de ids de autores existentes.
const libros = [
  { id: 1, titulo: 'El principito', isbn: '978-84-376-0494-7', precio: 1500, idEditorial: 1, idGenero: 1, autores: [1] },
  { id: 2, titulo: 'Cuentos de terror', isbn: '978-987-1111-22-3', precio: 2000, idEditorial: 2, idGenero: null, autores: [2] },
  { id: 3, titulo: 'Introducción a la programación', isbn: '978-987-550-333-9', precio: 3250.5, idEditorial: 3, idGenero: 3, autores: [3, 4] },
  { id: 4, titulo: 'Manual de JavaScript moderno', isbn: '978-987-550-444-3', precio: 2890, idEditorial: 3, idGenero: 3, autores: [4] },
  { id: 5, titulo: 'Relatos del faro', isbn: '978-987-1111-55-1', precio: 1750, idEditorial: 2, idGenero: 2, autores: [2] },
  { id: 6, titulo: 'Fábulas del río', isbn: '978-84-376-0512-8', precio: 1980.75, idEditorial: 1, idGenero: 1, autores: [1, 2] }
];

const clientes = [
  { id: 1, nombreCompleto: 'Ana Beltrán', email: 'ana.beltran@correo.test' },
  { id: 2, nombreCompleto: 'Carlos Duarte', email: 'carlos.duarte@correo.test' },
  { id: 3, nombreCompleto: 'Elena Fuentes', email: 'elena.fuentes@correo.test' }
];

const ventas = [];

// ============================================================
// 2. PERSISTENCIA (localStorage, clave versionada)
// ============================================================

const CLAVE_ALMACENAMIENTO = 'libreriaElFaro.v1';
const VERSION_DATOS = 1;

function hayAlmacenamiento() {
  try {
    const clavePrueba = '__libreria_el_faro_prueba__';
    window.localStorage.setItem(clavePrueba, '1');
    window.localStorage.removeItem(clavePrueba);
    return true;
  } catch (error) {
    return false;
  }
}

function esModeloValido(modelo) {
  if (!modelo || typeof modelo !== 'object') {
    return false;
  }
  if (modelo.version !== VERSION_DATOS) {
    return false;
  }
  if (!Array.isArray(modelo.libros) || !Array.isArray(modelo.clientes) || !Array.isArray(modelo.ventas)) {
    return false;
  }

  const librosValidos = modelo.libros.every(function (libro) {
    return libro && typeof libro.id === 'number' &&
      typeof libro.titulo === 'string' &&
      typeof libro.isbn === 'string' &&
      typeof libro.precio === 'number' && Number.isFinite(libro.precio) &&
      typeof libro.idEditorial === 'number' &&
      (libro.idGenero === null || typeof libro.idGenero === 'number') &&
      Array.isArray(libro.autores);
  });

  const clientesValidos = modelo.clientes.every(function (cliente) {
    return cliente && typeof cliente.id === 'number' &&
      typeof cliente.nombreCompleto === 'string' &&
      typeof cliente.email === 'string';
  });

  const ventasValidas = modelo.ventas.every(function (venta) {
    return venta && typeof venta.id === 'string' &&
      typeof venta.fecha === 'string' &&
      typeof venta.idCliente === 'number' &&
      typeof venta.nombreCliente === 'string' &&
      typeof venta.total === 'number' && Number.isFinite(venta.total) &&
      Array.isArray(venta.renglones) &&
      venta.renglones.every(function (renglon) {
        return renglon && typeof renglon.idLibro === 'number' &&
          typeof renglon.titulo === 'string' &&
          typeof renglon.cantidad === 'number' &&
          typeof renglon.precioUnitario === 'number' &&
          typeof renglon.subtotal === 'number';
      });
  });

  return librosValidos && clientesValidos && ventasValidas;
}

function cargarDatos() {
  if (!hayAlmacenamiento()) {
    return false;
  }

  let crudo = null;
  try {
    crudo = window.localStorage.getItem(CLAVE_ALMACENAMIENTO);
  } catch (error) {
    return false;
  }

  if (crudo === null) {
    return false;
  }

  let modelo = null;
  try {
    modelo = JSON.parse(crudo);
  } catch (error) {
    modelo = null;
  }

  if (!esModeloValido(modelo)) {
    try {
      window.localStorage.removeItem(CLAVE_ALMACENAMIENTO);
    } catch (error) {
      // Sin almacenamiento disponible: se continúa con los ejemplos en memoria.
    }
    return false;
  }

  libros.splice(0, libros.length, ...modelo.libros);
  clientes.splice(0, clientes.length, ...modelo.clientes);
  ventas.splice(0, ventas.length, ...modelo.ventas);
  return true;
}

function guardarDatos() {
  if (!hayAlmacenamiento()) {
    return false;
  }
  try {
    window.localStorage.setItem(CLAVE_ALMACENAMIENTO, JSON.stringify({
      version: VERSION_DATOS,
      libros: libros,
      clientes: clientes,
      ventas: ventas
    }));
    return true;
  } catch (error) {
    return false;
  }
}

// ============================================================
// 3. HELPERS (búsquedas por id, formato y normalización)
// ============================================================

function buscarEditorialPorId(id) {
  return editoriales.find(function (editorial) { return editorial.id === id; }) || null;
}

function buscarGeneroPorId(id) {
  return generos.find(function (genero) { return genero.id === id; }) || null;
}

function buscarAutoresPorIds(ids) {
  return ids
    .map(function (id) { return autores.find(function (autor) { return autor.id === id; }) || null; })
    .filter(function (autor) { return autor !== null; });
}

function buscarLibroPorId(id) {
  return libros.find(function (libro) { return libro.id === id; }) || null;
}

function buscarClientePorId(id) {
  return clientes.find(function (cliente) { return cliente.id === id; }) || null;
}

function buscarVentaPorId(id) {
  return ventas.find(function (venta) { return venta.id === id; }) || null;
}

// «Sin clasificar» es la representación de la ausencia de género.
function describirEditorial(libro) {
  const editorial = buscarEditorialPorId(libro.idEditorial);
  return editorial ? editorial.nombre : '—';
}

function describirGenero(libro) {
  if (libro.idGenero === null || libro.idGenero === undefined) {
    return 'Sin clasificar';
  }
  const genero = buscarGeneroPorId(libro.idGenero);
  return genero ? genero.nombre : 'Sin clasificar';
}

function describirAutores(libro) {
  const nombres = buscarAutoresPorIds(libro.autores).map(function (autor) { return autor.nombre; });
  return nombres.join(', ');
}

// Formato de importes: dos decimales con coma, sin separador de miles,
// igual que la maqueta del HTML: $1500,00 / $3250,50.
function formatearPrecio(valor) {
  return '$' + Number(valor).toFixed(2).replace('.', ',');
}

function formatearFecha(fechaISO) {
  const fecha = new Date(fechaISO);
  if (isNaN(fecha.getTime())) {
    return String(fechaISO);
  }
  const dia = String(fecha.getDate()).padStart(2, '0');
  const mes = String(fecha.getMonth() + 1).padStart(2, '0');
  return dia + '/' + mes + '/' + fecha.getFullYear();
}

// ISBN comparable: se ignoran espacios, guiones y mayúsculas/minúsculas.
function normalizarIsbn(isbn) {
  return String(isbn).replace(/[\s-]/g, '').toUpperCase();
}

function proximoIdLibro() {
  if (libros.length === 0) {
    return 1;
  }
  return Math.max.apply(null, libros.map(function (libro) { return libro.id; })) + 1;
}

function proximoIdCliente() {
  if (clientes.length === 0) {
    return 1;
  }
  return Math.max.apply(null, clientes.map(function (cliente) { return cliente.id; })) + 1;
}

function proximoIdVenta() {
  const numeros = ventas.map(function (venta) {
    const numero = parseInt(String(venta.id).replace(/[^0-9]/g, ''), 10);
    return Number.isNaN(numero) ? 0 : numero;
  });
  const mayor = numeros.length > 0 ? Math.max.apply(null, numeros) : 0;
  return 'V-' + String(mayor + 1).padStart(4, '0');
}

// ============================================================
// 4. RENDERIZADO DE LIBROS Y CATÁLOGO (Ejercicios 3 y 4)
// ============================================================

function crearFilaLibro(libro) {
  const fila = document.createElement('tr');
  const celdas = [
    libro.titulo,
    libro.isbn,
    describirEditorial(libro),
    describirGenero(libro),
    describirAutores(libro),
    formatearPrecio(libro.precio)
  ];
  celdas.forEach(function (texto) {
    const celda = document.createElement('td');
    celda.textContent = texto;
    fila.appendChild(celda);
  });
  return fila;
}

// Reemplaza el tbody de una tabla por una fila por libro.
function renderFilasLibros(tabla, lista) {
  const cuerpo = tabla.querySelector('tbody');
  cuerpo.textContent = '';
  lista.forEach(function (libro) {
    cuerpo.appendChild(crearFilaLibro(libro));
  });
}

function filtrarLibrosPorTitulo(termino) {
  const consulta = String(termino).trim().toLowerCase();
  if (consulta === '') {
    return libros.slice();
  }
  return libros.filter(function (libro) {
    return libro.titulo.toLowerCase().indexOf(consulta) !== -1;
  });
}

function renderCatalogo() {
  const campoBusqueda = document.getElementById('catalogo-busqueda');
  const mensajeSinResultados = document.getElementById('catalogo-sin-resultados');
  const mensajeListadoVacio = document.getElementById('catalogo-listado-vacio');
  const tabla = document.getElementById('tabla-catalogo');
  const contenedorTabla = tabla.closest('.tabla-contenedor');

  if (libros.length === 0) {
    renderFilasLibros(tabla, []);
    contenedorTabla.hidden = true;
    mensajeSinResultados.hidden = true;
    mensajeListadoVacio.hidden = false;
    return;
  }

  mensajeListadoVacio.hidden = true;
  const coincidencias = filtrarLibrosPorTitulo(campoBusqueda.value);

  if (coincidencias.length === 0) {
    renderFilasLibros(tabla, []);
    contenedorTabla.hidden = true;
    mensajeSinResultados.hidden = false;
    return;
  }

  mensajeSinResultados.hidden = true;
  contenedorTabla.hidden = false;
  renderFilasLibros(tabla, coincidencias);
}

function renderTablaLibrosRegistrados() {
  const mensajeVacio = document.getElementById('libros-listado-vacio');
  const tabla = document.getElementById('tabla-libros');
  const contenedorTabla = tabla.closest('.tabla-contenedor');

  if (libros.length === 0) {
    renderFilasLibros(tabla, []);
    contenedorTabla.hidden = true;
    mensajeVacio.hidden = false;
    return;
  }

  mensajeVacio.hidden = true;
  contenedorTabla.hidden = false;
  renderFilasLibros(tabla, libros);
}

// ============================================================
// 5. SELECTORES DINÁMICOS (libros, clientes y venta)
// ============================================================

function cargarSelectoresLibro() {
  const selectEditorial = document.getElementById('libro-editorial');
  const selectGenero = document.getElementById('libro-genero');
  const selectAutores = document.getElementById('libro-autores');

  // Editorial: placeholder deshabilitado + editoriales existentes.
  selectEditorial.textContent = '';
  const placeholderEditorial = new Option('Seleccione una editorial', '');
  placeholderEditorial.disabled = true;
  placeholderEditorial.selected = true;
  selectEditorial.appendChild(placeholderEditorial);
  editoriales.forEach(function (editorial) {
    selectEditorial.appendChild(new Option(editorial.nombre, String(editorial.id)));
  });

  // Género: «Sin clasificar» (valor vacío) seleccionado por defecto.
  selectGenero.textContent = '';
  selectGenero.appendChild(new Option('Sin clasificar', ''));
  generos.forEach(function (genero) {
    selectGenero.appendChild(new Option(genero.nombre, String(genero.id)));
  });

  // Autores: selector múltiple con todos los autores existentes.
  selectAutores.textContent = '';
  autores.forEach(function (autor) {
    selectAutores.appendChild(new Option(autor.nombre, String(autor.id)));
  });
}

function actualizarSelectorVentaLibro() {
  const selectVentaLibro = document.getElementById('venta-libro');
  selectVentaLibro.textContent = '';
  const placeholder = new Option('Seleccione un libro', '');
  placeholder.disabled = true;
  placeholder.selected = true;
  selectVentaLibro.appendChild(placeholder);
  libros.forEach(function (libro) {
    selectVentaLibro.appendChild(new Option(libro.titulo + ' — ' + formatearPrecio(libro.precio), String(libro.id)));
  });
}

function actualizarSelectorVentaCliente() {
  const selectVentaCliente = document.getElementById('venta-cliente');
  selectVentaCliente.textContent = '';
  const placeholder = new Option('Seleccione un cliente', '');
  placeholder.disabled = true;
  placeholder.selected = true;
  selectVentaCliente.appendChild(placeholder);
  clientes.forEach(function (cliente) {
    selectVentaCliente.appendChild(new Option(cliente.nombreCompleto + ' — ' + cliente.email, String(cliente.id)));
  });
}

function cargarSelectoresVenta() {
  actualizarSelectorVentaCliente();
  actualizarSelectorVentaLibro();
}

// ============================================================
// 6. CLIENTES (Ejercicio 4)
// ============================================================

function crearFilaCliente(cliente) {
  const fila = document.createElement('tr');
  [cliente.nombreCompleto, cliente.email].forEach(function (texto) {
    const celda = document.createElement('td');
    celda.textContent = texto;
    fila.appendChild(celda);
  });
  return fila;
}

function renderTablaClientes() {
  const tabla = document.getElementById('tabla-clientes');
  const cuerpo = tabla.querySelector('tbody');
  const contenedorTabla = tabla.closest('.tabla-contenedor');
  const mensajeVacio = document.getElementById('clientes-listado-vacio');

  cuerpo.textContent = '';

  if (clientes.length === 0) {
    contenedorTabla.hidden = true;
    mensajeVacio.hidden = false;
    return;
  }

  mensajeVacio.hidden = true;
  contenedorTabla.hidden = false;
  clientes.forEach(function (cliente) {
    cuerpo.appendChild(crearFilaCliente(cliente));
  });
}

function emailValido(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function manejarAltaCliente(evento) {
  evento.preventDefault();
  const feedback = document.getElementById('clientes-feedback');
  const formulario = document.getElementById('form-alta-cliente');
  const nombre = document.getElementById('cliente-nombre').value.trim();
  const email = document.getElementById('cliente-email').value.trim();
  const errores = [];

  if (nombre === '') {
    errores.push('El nombre completo es obligatorio.');
  }

  if (email === '') {
    errores.push('El email es obligatorio.');
  } else if (!emailValido(email)) {
    errores.push('El email debe tener un formato válido.');
  } else {
    const emailNormalizado = email.toLowerCase();
    const duplicado = clientes.some(function (cliente) {
      return cliente.email.trim().toLowerCase() === emailNormalizado;
    });
    if (duplicado) {
      errores.push('El email ya está registrado (se compara sin espacios exteriores y sin distinguir mayúsculas de minúsculas).');
    }
  }

  if (errores.length > 0) {
    mostrarFeedback(feedback, false, 'No se pudo registrar el cliente. ' + errores.join(' '));
    return;
  }

  clientes.push({
    id: proximoIdCliente(),
    nombreCompleto: nombre,
    email: email
  });

  mostrarFeedback(feedback, true, 'Cliente registrado correctamente: «' + nombre + '» (' + email + ').');
  formulario.reset();

  renderTablaClientes();
  actualizarSelectorVentaCliente();
  guardarDatos();
}

// ============================================================
// 7. VENTAS (Ejercicio 5)
// ============================================================

let renglonesVenta = [];

function calcularSubtotalRenglon(renglon) {
  return renglon.cantidad * renglon.precioUnitario;
}

function calcularTotalVenta() {
  return renglonesVenta.reduce(function (total, renglon) {
    return total + renglon.subtotal;
  }, 0);
}

function actualizarTotalVenta() {
  document.getElementById('venta-total').textContent = formatearPrecio(calcularTotalVenta());
}

function validarCantidad(valor) {
  const cantidad = Number(valor);
  if (!Number.isInteger(cantidad) || cantidad <= 0) {
    return null;
  }
  return cantidad;
}

function renderRenglonesVenta() {
  const tabla = document.getElementById('tabla-renglones');
  const cuerpo = tabla.querySelector('tbody');
  const contenedorTabla = tabla.closest('.tabla-contenedor');
  const mensajeVacio = document.getElementById('renglones-listado-vacio');

  cuerpo.textContent = '';

  if (renglonesVenta.length === 0) {
    contenedorTabla.hidden = true;
    mensajeVacio.hidden = false;
    actualizarTotalVenta();
    return;
  }

  mensajeVacio.hidden = true;
  contenedorTabla.hidden = false;

  renglonesVenta.forEach(function (renglon) {
    const fila = document.createElement('tr');

    const celdaLibro = document.createElement('td');
    celdaLibro.textContent = renglon.titulo;
    fila.appendChild(celdaLibro);

    const celdaCantidad = document.createElement('td');
    const entradaCantidad = document.createElement('input');
    entradaCantidad.type = 'number';
    entradaCantidad.min = '1';
    entradaCantidad.step = '1';
    entradaCantidad.value = String(renglon.cantidad);
    entradaCantidad.className = 'renglon-cantidad';
    entradaCantidad.setAttribute('aria-label', 'Cantidad de ' + renglon.titulo + ' en la venta');
    entradaCantidad.dataset.idLibro = String(renglon.idLibro);
    entradaCantidad.addEventListener('change', function () {
      manejarCambioCantidad(renglon.idLibro, entradaCantidad);
    });
    celdaCantidad.appendChild(entradaCantidad);
    fila.appendChild(celdaCantidad);

    const celdaPrecio = document.createElement('td');
    celdaPrecio.textContent = formatearPrecio(renglon.precioUnitario);
    fila.appendChild(celdaPrecio);

    const celdaSubtotal = document.createElement('td');
    celdaSubtotal.textContent = formatearPrecio(renglon.subtotal);
    fila.appendChild(celdaSubtotal);

    const celdaAcciones = document.createElement('td');
    const botonQuitar = document.createElement('button');
    botonQuitar.type = 'button';
    botonQuitar.className = 'renglon-quitar';
    botonQuitar.textContent = 'Quitar ' + renglon.titulo + ' de la venta';
    botonQuitar.addEventListener('click', function () {
      manejarQuitarRenglon(renglon.idLibro);
    });
    celdaAcciones.appendChild(botonQuitar);
    fila.appendChild(celdaAcciones);

    cuerpo.appendChild(fila);
  });

  actualizarTotalVenta();
}

function manejarAgregarRenglon() {
  const feedback = document.getElementById('venta-feedback');
  const selectLibro = document.getElementById('venta-libro');
  const campoCantidad = document.getElementById('venta-cantidad');
  const idLibro = parseInt(selectLibro.value, 10);
  const libro = buscarLibroPorId(idLibro);

  if (!libro) {
    mostrarFeedback(feedback, false, 'Debe seleccionar un libro existente para agregar el renglón.');
    return;
  }

  const cantidad = validarCantidad(campoCantidad.value);
  if (cantidad === null) {
    mostrarFeedback(feedback, false, 'La cantidad debe ser un número entero mayor que cero.');
    return;
  }

  if (renglonesVenta.some(function (renglon) { return renglon.idLibro === idLibro; })) {
    mostrarFeedback(feedback, false, 'El libro ya está en la venta. Modificá la cantidad del renglón existente o quitalo para volver a agregarlo.');
    return;
  }

  renglonesVenta.push({
    idLibro: libro.id,
    titulo: libro.titulo,
    cantidad: cantidad,
    precioUnitario: libro.precio,
    subtotal: cantidad * libro.precio
  });

  renderRenglonesVenta();
  mostrarFeedback(feedback, true, 'Renglón agregado: «' + libro.titulo + '» × ' + cantidad + '.');

  selectLibro.selectedIndex = 0;
  campoCantidad.value = '1';
}

function manejarCambioCantidad(idLibro, entrada) {
  const feedback = document.getElementById('venta-feedback');
  const renglon = renglonesVenta.find(function (item) { return item.idLibro === idLibro; });

  if (!renglon) {
    return;
  }

  const cantidad = validarCantidad(entrada.value);
  if (cantidad === null) {
    mostrarFeedback(feedback, false, 'La cantidad debe ser un número entero mayor que cero. Se conservó el valor anterior.');
    entrada.value = String(renglon.cantidad);
    return;
  }

  renglon.cantidad = cantidad;
  renglon.subtotal = calcularSubtotalRenglon(renglon);
  renderRenglonesVenta();
  mostrarFeedback(feedback, true, 'Cantidad actualizada para «' + renglon.titulo + '».');
}

function manejarQuitarRenglon(idLibro) {
  const feedback = document.getElementById('venta-feedback');
  const renglon = renglonesVenta.find(function (item) { return item.idLibro === idLibro; });

  renglonesVenta = renglonesVenta.filter(function (item) { return item.idLibro !== idLibro; });
  renderRenglonesVenta();

  if (renglon) {
    mostrarFeedback(feedback, true, 'Renglón quitado: «' + renglon.titulo + '».');
  }
}

function manejarConfirmarVenta() {
  const feedback = document.getElementById('venta-feedback');
  const selectCliente = document.getElementById('venta-cliente');
  const idCliente = parseInt(selectCliente.value, 10);
  const cliente = buscarClientePorId(idCliente);

  if (!cliente) {
    mostrarFeedback(feedback, false, 'Debe seleccionar un cliente existente para confirmar la venta.');
    return;
  }

  if (renglonesVenta.length === 0) {
    mostrarFeedback(feedback, false, 'La venta debe tener al menos un renglón para confirmarse.');
    return;
  }

  const cantidadesValidas = renglonesVenta.every(function (renglon) {
    return Number.isInteger(renglon.cantidad) && renglon.cantidad > 0;
  });

  if (!cantidadesValidas) {
    mostrarFeedback(feedback, false, 'Todas las cantidades deben ser números enteros mayores que cero.');
    return;
  }

  const renglonesHistoricos = renglonesVenta.map(function (renglon) {
    return {
      idLibro: renglon.idLibro,
      titulo: renglon.titulo,
      cantidad: renglon.cantidad,
      precioUnitario: renglon.precioUnitario,
      subtotal: renglon.cantidad * renglon.precioUnitario
    };
  });

  const total = renglonesHistoricos.reduce(function (suma, renglon) {
    return suma + renglon.subtotal;
  }, 0);

  const venta = {
    id: proximoIdVenta(),
    fecha: new Date().toISOString(),
    idCliente: cliente.id,
    nombreCliente: cliente.nombreCompleto,
    renglones: renglonesHistoricos,
    total: total
  };

  ventas.push(venta);
  guardarDatos();
  renderHistorial();
  renderDetalleVenta(venta.id);

  renglonesVenta = [];
  selectCliente.selectedIndex = 0;
  document.getElementById('venta-libro').selectedIndex = 0;
  document.getElementById('venta-cantidad').value = '1';
  renderRenglonesVenta();

  mostrarFeedback(feedback, true, 'Venta ' + venta.id + ' confirmada por ' + formatearPrecio(total) + '.');
}

// ============================================================
// 8. HISTORIAL Y DETALLE INMUTABLE (Ejercicio 5)
// ============================================================

function renderHistorial() {
  const tabla = document.getElementById('tabla-historial');
  const cuerpo = tabla.querySelector('tbody');
  const contenedorTabla = tabla.closest('.tabla-contenedor');
  const mensajeVacio = document.getElementById('historial-listado-vacio');

  cuerpo.textContent = '';

  if (ventas.length === 0) {
    contenedorTabla.hidden = true;
    mensajeVacio.hidden = false;
    return;
  }

  mensajeVacio.hidden = true;
  contenedorTabla.hidden = false;

  ventas.forEach(function (venta) {
    const fila = document.createElement('tr');
    [venta.id, formatearFecha(venta.fecha), venta.nombreCliente, formatearPrecio(venta.total)].forEach(function (texto) {
      const celda = document.createElement('td');
      celda.textContent = texto;
      fila.appendChild(celda);
    });

    const celdaDetalle = document.createElement('td');
    const botonDetalle = document.createElement('button');
    botonDetalle.type = 'button';
    botonDetalle.className = 'historial-ver-detalle';
    botonDetalle.dataset.idVenta = venta.id;
    botonDetalle.textContent = 'Ver detalle de la venta ' + venta.id;
    celdaDetalle.appendChild(botonDetalle);
    fila.appendChild(celdaDetalle);

    cuerpo.appendChild(fila);
  });
}

function renderDetalleVenta(idVenta) {
  const contenedor = document.getElementById('tabla-historial-detalle');
  const venta = buscarVentaPorId(idVenta);
  contenedor.textContent = '';

  if (!venta) {
    renderDetalleVacio();
    return;
  }

  const contenedorTabla = document.createElement('div');
  contenedorTabla.className = 'tabla-contenedor';

  const tabla = document.createElement('table');
  const caption = document.createElement('caption');
  caption.textContent = 'Renglones de la venta ' + venta.id + ' (valores históricos)';
  tabla.appendChild(caption);

  const thead = document.createElement('thead');
  const filaEncabezado = document.createElement('tr');
  ['Libro', 'Cantidad', 'Precio unitario', 'Subtotal'].forEach(function (texto) {
    const th = document.createElement('th');
    th.scope = 'col';
    th.textContent = texto;
    filaEncabezado.appendChild(th);
  });
  thead.appendChild(filaEncabezado);
  tabla.appendChild(thead);

  const tbody = document.createElement('tbody');
  venta.renglones.forEach(function (renglon) {
    const fila = document.createElement('tr');
    [renglon.titulo, String(renglon.cantidad), formatearPrecio(renglon.precioUnitario), formatearPrecio(renglon.subtotal)].forEach(function (texto) {
      const celda = document.createElement('td');
      celda.textContent = texto;
      fila.appendChild(celda);
    });
    tbody.appendChild(fila);
  });
  tabla.appendChild(tbody);

  const tfoot = document.createElement('tfoot');
  const filaTotal = document.createElement('tr');
  const thTotal = document.createElement('th');
  thTotal.scope = 'row';
  thTotal.colSpan = 3;
  thTotal.textContent = 'Total de la venta';
  filaTotal.appendChild(thTotal);
  const tdTotal = document.createElement('td');
  tdTotal.textContent = formatearPrecio(venta.total);
  filaTotal.appendChild(tdTotal);
  tfoot.appendChild(filaTotal);
  tabla.appendChild(tfoot);

  contenedorTabla.appendChild(tabla);
  contenedor.appendChild(contenedorTabla);
}

function renderDetalleVacio() {
  const contenedor = document.getElementById('tabla-historial-detalle');
  contenedor.textContent = '';
  const mensaje = document.createElement('p');
  mensaje.className = 'listado-vacio';
  mensaje.textContent = 'Seleccione una venta del historial para ver su detalle.';
  contenedor.appendChild(mensaje);
}

function manejarClicHistorial(evento) {
  const boton = evento.target.closest('.historial-ver-detalle');
  if (!boton) {
    return;
  }
  renderDetalleVenta(boton.dataset.idVenta);
}

// ============================================================
// 9. ALTA DE LIBROS (Ejercicio 4, parte libros)
// ============================================================

function validarLibro(datos) {
  const errores = [];

  if (String(datos.titulo).trim() === '') {
    errores.push('El título es obligatorio.');
  }

  if (String(datos.isbn).trim() === '') {
    errores.push('El ISBN es obligatorio.');
  } else {
    const isbnNormalizado = normalizarIsbn(datos.isbn);
    const duplicado = libros.some(function (libro) {
      return normalizarIsbn(libro.isbn) === isbnNormalizado;
    });
    if (duplicado) {
      errores.push('El ISBN ya existe en el catálogo (se compara sin espacios ni guiones).');
    }
  }

  if (!Number.isFinite(datos.precio) || datos.precio <= 0) {
    errores.push('El precio debe ser un número mayor que cero.');
  }

  if (!editoriales.some(function (editorial) { return editorial.id === datos.idEditorial; })) {
    errores.push('La editorial seleccionada debe existir en los datos locales.');
  }

  if (datos.idAutores.length === 0) {
    errores.push('Debe seleccionar al menos un autor.');
  } else {
    const todosExisten = datos.idAutores.every(function (id) {
      return autores.some(function (autor) { return autor.id === id; });
    });
    if (!todosExisten) {
      errores.push('Todos los autores seleccionados deben existir en los datos locales.');
    }
  }

  // El género es opcional: solo se valida si se asignó (llega como string del select).
  if (datos.idGenero !== '' && !generos.some(function (genero) { return String(genero.id) === String(datos.idGenero); })) {
    errores.push('El género seleccionado debe existir en los datos locales.');
  }

  return errores;
}

function mostrarFeedback(elemento, esOk, texto) {
  elemento.textContent = (esOk ? 'OK — ' : 'Error — ') + texto;
  elemento.hidden = false;
}

function limpiarFormularioLibro() {
  const formulario = document.getElementById('form-alta-libro');
  formulario.reset();
  // reset() no garantiza el estado de options creados por JS: se fija explícitamente.
  document.getElementById('libro-editorial').selectedIndex = 0; // placeholder
  document.getElementById('libro-genero').value = ''; // «Sin clasificar»
  document.getElementById('libro-autores').selectedIndex = -1; // nada seleccionado
}

function manejarAltaLibro(evento) {
  evento.preventDefault();
  const feedback = document.getElementById('libros-feedback');

  const datos = {
    titulo: document.getElementById('libro-titulo').value.trim(),
    isbn: document.getElementById('libro-isbn').value.trim(),
    precio: parseFloat(document.getElementById('libro-precio').value),
    idEditorial: parseInt(document.getElementById('libro-editorial').value, 10),
    idGenero: document.getElementById('libro-genero').value === '' ? null : parseInt(document.getElementById('libro-genero').value, 10),
    idAutores: Array.prototype.map.call(
      document.getElementById('libro-autores').selectedOptions,
      function (opcion) { return parseInt(opcion.value, 10); }
    )
  };

  // validarLibro espera idGenero como string crudo ('' = sin asignar).
  const errores = validarLibro(Object.assign({}, datos, {
    idGenero: document.getElementById('libro-genero').value
  }));

  if (errores.length > 0) {
    mostrarFeedback(feedback, false, 'No se pudo registrar el libro. ' + errores.join(' '));
    return;
  }

  libros.push({
    id: proximoIdLibro(),
    titulo: datos.titulo,
    isbn: datos.isbn,
    precio: datos.precio,
    idEditorial: datos.idEditorial,
    idGenero: datos.idGenero,
    autores: datos.idAutores
  });

  mostrarFeedback(feedback, true, 'Libro registrado correctamente: «' + datos.titulo + '» (ISBN ' + datos.isbn + ').');
  limpiarFormularioLibro();

  // Actualización en vivo: catálogo, listado de libros y selector de ventas.
  renderCatalogo();
  renderTablaLibrosRegistrados();
  actualizarSelectorVentaLibro();
  guardarDatos();
}

// ============================================================
// 10. INICIALIZACIÓN Y EVENTOS
// ============================================================

function inicializar() {
  if (!cargarDatos()) {
    guardarDatos();
  }

  cargarSelectoresLibro();
  cargarSelectoresVenta();
  renderTablaLibrosRegistrados();
  renderTablaClientes();
  renderRenglonesVenta();
  renderHistorial();
  renderDetalleVacio();

  const campoBusqueda = document.getElementById('catalogo-busqueda');
  campoBusqueda.value = '';
  renderCatalogo();

  // Buscador: submit (botón/Enter) y actualización en vivo con `input`.
  document.querySelector('.buscador').addEventListener('submit', function (evento) {
    evento.preventDefault();
    renderCatalogo();
  });
  campoBusqueda.addEventListener('input', renderCatalogo);

  // Alta de libros y clientes.
  document.getElementById('form-alta-libro').addEventListener('submit', manejarAltaLibro);
  document.getElementById('form-alta-cliente').addEventListener('submit', manejarAltaCliente);

  // Composición y confirmación de la venta.
  document.getElementById('venta-agregar').addEventListener('click', manejarAgregarRenglon);
  document.getElementById('venta-confirmar').addEventListener('click', manejarConfirmarVenta);

  // Acceso al detalle desde el historial (delegación sobre el tbody).
  document.getElementById('tabla-historial').querySelector('tbody').addEventListener('click', manejarClicHistorial);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', inicializar);
} else {
  inicializar();
}
