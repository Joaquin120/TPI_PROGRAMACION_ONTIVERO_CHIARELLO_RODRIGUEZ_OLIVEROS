# Visión y Objetivos

## Propósito del sistema
Integrar las pantallas de gestión de una librería web desarrolladas en JavaScript nativo (Primer Parcial) con una API REST construida con FastAPI y base de datos relacional PostgreSQL (Segundo Parcial), encapsulando ambos componentes en contenedores Docker orquestados por un proxy inverso Nginx y desplegados en una VPS mediante Easypanel.

## Objetivos por actor
| Actor | Objetivo principal | Objetivos secundarios |
|---|---|---|
| **Cliente / Comprador** | Explorar el catálogo de libros y registrar compras de libros con cálculo automático e inmutable de importes. | Búsqueda por título, paginación de resultados, visualización de autores, editorial y género. |
| **Operador / Vendedor** | Registrar nuevos libros, autores y clientes en el sistema; generar ventas con múltiples renglones. | Validar duplicados (ISBN, email), gestionar borrador de venta en memoria, consultar historial y detalle de ventas pasadas. |
| **Docente / Evaluador** | Verificar el cumplimiento de los contratos HTTP, la persistencia en PostgreSQL y la correcta compilación y despliegue del stack web. | Ejecución de casos de prueba G-01 a G-07 sobre la URL pública HTTPS definitiva. |

## Alcance v1.0 (Global Integración y Despliegue)
- **Catálogo de Libros:** Listado paginado (`limit`, `offset`), filtro de búsqueda parcial sin distinguir mayúsculas (`titulo`), visualización de editorial, género y autores asociados vía `GET /libros/{id}`.
- **Alta de Libros:** Formulario validado con selectores dinámicos de editoriales y géneros, verificación de autores por ID, rol de autoría (`autor`, `coautor`, `traductor`, `ilustrador`) y orden.
- **Alta y Consulta de Clientes:** Formulario de alta con nombre y email, validación de conflictos (409) y búsqueda por ID para selección en ventas.
- **Registro de Ventas:** Armado de borrador en memoria (cliente + selección de libros + cantidades), validación de unicidad de libro por renglón, confirmación vía `POST /ventas/` con bloqueo de doble envío y renderizado de subtotales/total calculados por la API.
- **Historial de Ventas:** Consulta paginada de ventas registradas y visualización del detalle histórico congelado (`GET /ventas/{id}`).
- **Invariante de Precio Histórico:** Modificaciones posteriores al precio de un libro no alteran las ventas previamente registradas.
- **Contenerización y Despliegue:** Imagen de frontend (Nginx 1.26-alpine con reverse proxy `/api/`), imagen de backend (FastAPI + Alembic migraciones automáticas), Docker Compose local y configuración de servicios en Easypanel.

## Fuera de alcance
- Pasarelas de pago reales o procesamiento de tarjetas de crédito.
- Autenticación mediante JWT/OAuth o login de usuarios (las rutas son de acceso operativo directo según consigna).
- Bajas físicas (DELETE) de libros o clientes (se prioriza integridad referencial y auditoría de ventas).
- Modificación o edición de ventas ya confirmadas.

## Métricas de éxito
1. **100% de persistencia en PostgreSQL:** Cero uso de `localStorage` para datos de negocio confirmados.
2. **Cumplimiento estricto de casos G-01 a G-07:** Verificación exitosa en la URL pública con HTTPS.
3. **Resiliencia ante errores:** Presentación amigable al usuario de respuestas `409 Conflict` (duplicados) y `422 Unprocessable Entity` (errores de validación).
4. **Despliegue automatizado:** Migraciones Alembic aplicadas automáticamente al arrancar el contenedor backend.
