# EVALUACIÓN GLOBAL INTEGRACIÓN Y DESPLIEGUE — PROGRAMACIÓN III
**Universidad Tecnológica Nacional (UTN) — Tecnicatura Universitaria en Programación**  
*Librería web integrada y desplegada en Easypanel*

---

## 1. Objetivos y Alcance

### Objetivos
- Conectar las pantallas del **Primer Parcial** con la API de la librería mediante **JavaScript nativo**.
- Usar los contratos de **FastAPI** para consultar el catálogo y registrar libros, clientes y ventas.
- Construir una imagen **Docker** del frontend y publicar la aplicación en una **VPS administrada con Easypanel**.
- Verificar desde la URL pública que las operaciones llegan a la API y que los datos quedan persistidos en **PostgreSQL**.

### Contexto y Alcance
- En el primer parcial, el navegador simulaba las altas y ventas (con almacenamiento local en memoria o `localStorage`). En este Global se reutilizan esas pantallas y se conectan al TP *«Librería: catálogo, clientes y ventas con FastAPI y PostgreSQL»* (Capítulos 1 a 4).
- El frontend conserva HTML, CSS y JavaScript nativos y recursos locales. Los registros y los importes confirmados provienen de la API y se guardan en PostgreSQL. La interfaz puede mantener en memoria el borrador de una venta.
- La interfaz obligatoria cubre:
  1. Catálogo de libros.
  2. Alta de libros.
  3. Alta de clientes.
  4. Registro de venta.
  5. Historial de ventas.
- Se deben usar datos ficticios en el despliegue y en las pruebas.

### Qué se Entrega
Una aplicación integrada, el código fuente de ambos componentes (`frontend/` y `backend/`), el Dockerfile del frontend y la configuración necesaria para reproducir el despliegue. Los 5 ejercicios suman 100 puntos.

### Demostración Mínima
Desde la URL desplegada:
1. Consultar el catálogo.
2. Registrar una venta con dos renglones.
3. Volver a abrir el detalle de esa venta después de recargar la página.
4. Los importes del historial deben coincidir exactamente con los que devolvió la API.

---

## 2. Consignas de Integración

### Ejercicio 1: Catálogo y Cliente HTTP (20 Puntos)
- **Cliente HTTP y prefijo `/api`:** Centralizar la URL base y las peticiones con `fetch`. Usar `/api` como prefijo público. Conservar la barra final de las rutas que la traen (ejemplo: `/api/libros/`).
- **Listado y Búsqueda:** Cargar `GET /libros/` y usar el parámetro `titulo` para la búsqueda parcial sin distinguir mayúsculas. El listado devuelve una lista JSON.
- **Paginación:** Para paginar, enviar `limit` (1 a 100, por defecto 20) y `offset` (desde 0). Al cambiar el filtro de búsqueda, reiniciar el desplazamiento (`offset = 0`).
- **Renderizado de Catálogo:** Mostrar: título, ISBN, precio, editorial y género.
  - Para ver los autores, consultar `GET /libros/{id}`.
  - Si el género es nulo, mostrar «Sin clasificar».
- **Estados de la Interfaz:** Diferenciar claramente en la pantalla:
  - Estado de carga (*loading*).
  - Lista vacía.
  - Búsqueda sin coincidencias.
  - Error de conexión.

### Ejercicio 2: Alta de Libros y Clientes (20 Puntos)
- **POST `/libros/`:**
  - Enviar: `titulo`, `isbn`, `precio` (positivo), `stock` (entero desde cero), `editorial_id`, `genero_id` (opcional) y al menos un autor.
  - Cada autoría incluye: `autor_id`, `rol` y `orden`.
  - Roles de autoría válidos: `autor`, `coautor`, `traductor`, `ilustrador`.
  - Cargar las opciones de editorial y género desde `GET /editoriales/` y `GET /generos/`.
  - Para seleccionar autores, verificar cada ID con `GET /autores/{id}` y mostrar su nombre antes de agregarlo.
- **POST `/clientes/`:**
  - Enviar: `nombre` y `email`.
  - Si el backend solo expone la consulta individual, usar `GET /clientes/{id}` para buscar clientes y mostrar su nombre antes de seleccionarlos para una venta.
- **Validaciones y Respuestas:**
  - Validar los campos en el formulario antes del envío.
  - El alta exitosa devuelve `201 Created`. Usar el registro devuelto para actualizar las vistas relacionadas.
  - Mostrar el mensaje devuelto por el servidor ante códigos de error `409 Conflict` (datos duplicados como ISBN o email) o `422 Unprocessable Entity` (error de contrato).

### Ejercicio 3: Registrar y Consultar Ventas (25 Puntos)
- **Armar la Venta (Borrador en memoria):**
  - Seleccionar un cliente.
  - Agregar libros del catálogo.
  - Permitir cambiar cantidades y quitar renglones.
  - Reglas de validación para confirmar: exigir al menos un renglón, cantidades enteras positivas y un solo renglón por libro (no duplicar libros en la misma venta).
- **Enviar la Operación (POST `/ventas/`):**
  - Enviar el identificador del cliente y los datos de cada renglón.
  - Estructura exacta del cuerpo:
    ```json
    {
      "cliente_id": 2,
      "renglones": [
        {
          "libro_id": 1,
          "cantidad": 2
        },
        {
          "libro_id": 4,
          "cantidad": 1
        }
      ]
    }
    ```
- **Confirmación:**
  - El backend responde `201` con la venta registrada.
  - Mostrar en pantalla los precios unitarios que copió del catálogo, los subtotales calculados y el total devuelto por la API.
  - Limpiar el formulario luego de confirmar y actualizar el historial.
  - Deshabilitar el botón de confirmación mientras la petición esté en curso (evitar dobles envíos).
- **Consultar el Historial:**
  - Usar `GET /ventas/` con `limit` y `offset`.
  - Usar `GET /ventas/{id}` para mostrar: fecha, cliente, renglones e importes históricos.
  - *Invariante de precio histórico:* Un cambio posterior en el precio de un libro debe conservar intactos los importes de las ventas ya registradas.
- **Manejo de Errores de Negocio:**
  - Si el cliente o el libro dejó de existir, el servidor responde `409`.
  - Si el cuerpo es inválido (ej. libros repetidos en los renglones), devuelve `422`.
  - Conservar el borrador en pantalla si la operación es rechazada.

---

## 3. Guía de Despliegue con Docker y Nginx

### Ejercicio 4: Dockerfile del Frontend y Proxy Nginx (15 Puntos)

#### 1. Estructura de carpetas en `frontend/`
Separar los archivos públicos dentro de `frontend/public/`:
```text
frontend/
├── Dockerfile
├── .dockerignore
├── default.conf.template
└── public/
    ├── index.html
    ├── css/
    ├── js/
    └── img/
```

#### 2. `frontend/Dockerfile`
```dockerfile
FROM nginx:1.26-alpine
ENV NGINX_ENVSUBST_FILTER=^API_UPSTREAM$
COPY public/ /usr/share/nginx/html/
COPY default.conf.template /etc/nginx/templates/default.conf.template
EXPOSE 80
```

#### 3. `frontend/.dockerignore`
```text
.git
**/.env
**/.env.*
**/node_modules
**/.DS_Store
```

#### 4. `frontend/default.conf.template`
```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location /api/ {
        proxy_pass http://${API_UPSTREAM}/;
    }
}
```
*Nota:* La barra final en `proxy_pass http://${API_UPSTREAM}/;` reescribe el prefijo `/api/libros/` para que llegue a FastAPI como `/libros/`. En el código cliente de JavaScript, se utiliza `/api/` como base (ejemplo: `fetch("/api/libros/")`).

#### 5. Prueba local del contenedor Frontend
```bash
docker build -t libreria-frontend .
docker run --rm --name libreria-frontend \
  -p 127.0.0.1:8080:80 \
  --add-host=host.docker.internal:host-gateway \
  -e API_UPSTREAM=host.docker.internal:8000 \
  libreria-frontend
```

---

### Ejercicio 5: Servicios en Easypanel (20 Puntos)

#### 1. Backend Dockerfile (`backend/Dockerfile`)
Si el backend no cuenta con Dockerfile, se utiliza este estándar con migraciones automáticas al inicio:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 2. Backend `.dockerignore` (`backend/.dockerignore`)
```text
.git
**/.env
**/.env.*
**/.venv
**/__pycache__
**/.pytest_cache
```

#### 3. Configuración en Easypanel
- **Servicio Backend:**
  - Tipo: `App`. Nombre: `backend`.
  - Build Path: `/backend` (si conviven en el mismo repo) o raíz si es repositorio exclusivo.
  - Builder: `Dockerfile`.
  - Variables de entorno (`Environment`): `DATABASE_URL=postgresql+asyncpg://<usuario>:<password>@<host_postgres>:5432/<database>`
  - Puerto interno: `8000`.
  - Red: Mantener privado en la red interna de Docker.
- **Servicio Frontend:**
  - Tipo: `App`. Nombre: `frontend`.
  - Build Path: `/frontend`.
  - Builder: `Dockerfile`.
  - Variables de entorno (`Environment`):  
    `API_UPSTREAM=<nombre_servicio_backend>:8000` (ej: `proyecto_backend:8000`).
  - Dominios (`Domains`): Asociar el dominio público HTTPS asignado, enrutado al puerto `80` (HTTP).

#### 4. Tabla de Diagnóstico Rápido
| Síntoma | Causa probable y solución |
| :--- | :--- |
| **Falla un `COPY` en el build** | Verificar `Build Path`, nombres exactos de archivos y carpeta `public/`. |
| **Nginx no arranca o `/api/` da 502** | Revisar logs del frontend, variable `API_UPSTREAM`, nombre interno del servicio backend y puerto 8000. |
| **`/api/health/ready` da error** | Revisar logs del backend, variable `DATABASE_URL`, estado de PostgreSQL y migraciones Alembic. |
| **Una petición devuelve 404** | Revisar en la pestaña Red del navegador si falta el prefijo `/api` o la barra final (`/`) de la ruta. |

---

## 4. Casos de Prueba (G-01 a G-07)

Todas las pruebas se ejecutan sobre la **URL pública definitiva** con datos de muestra:

| Caso | Módulo | Procedimiento y Resultado Esperado |
| :--- | :--- | :--- |
| **G-01** | Catálogo | Buscar por título, avanzar con `limit` y `offset`, y probar una búsqueda sin coincidencias. Abrir el detalle de un libro. |
| **G-02** | Alta de libro | Crear un libro con stock, género opcional y autorías. Consultar el detalle. Repetir el mismo ISBN y verificar la respuesta `409 Conflict`. |
| **G-03** | Alta de cliente | Crear un cliente y recuperarlo por ID. Repetir el mismo email y verificar la respuesta `409 Conflict`. |
| **G-04** | Venta | Registrar una venta válida con dos renglones. Verificar `201 Created` y consultar el detalle histórico tras recargar el navegador. |
| **G-05** | Precio histórico | Modificar el precio de un libro con `PATCH /libros/{id}` y verificar que la venta registrada previamente conserva sus importes intactos. |
| **G-06** | Rechazo | Probar una venta con un ID de cliente/libro inexistente (`409`) y renglones con libros repetidos (`422`). El historial no debe modificarse. |
| **G-07** | Despliegue | La imagen de frontend compila. La URL pública abre con HTTPS, `/api/health/ready` devuelve `200` y los datos persisten tras un redespliegue. |

---

## 5. Criterios de Evaluación y Formato de Entrega

### Ponderación de Notas (Total: 100 puntos)
- **Catálogo y cliente HTTP:** 20 puntos
- **Alta de libros y clientes:** 20 puntos
- **Ventas e historial:** 25 puntos
- **Imagen del frontend (Nginx/Docker):** 15 puntos
- **Despliegue y verificación (Easypanel/VPS):** 20 puntos

### Formato de Entrega
Se entrega un único archivo comprimido `.zip` por grupo que contiene:
- `frontend/` (código fuente web, `public/`, `Dockerfile`, `.dockerignore`, `default.conf.template`).
- `backend/` (API FastAPI, `Dockerfile`, `.dockerignore`, migraciones Alembic, `requirements.txt`).
- `README.md` (identificación de integrantes, guía para levantar localmente y cómo cargar datos iniciales).
- `DEPLOY.md` (URL pública HTTPS, revisión de commit, rutas de build, puertos, upstream proxy, migraciones y pasos de actualización).
- `evidencia/` (capturas o salidas de terminal de los casos G-01 a G-07).
- **Prohibiciones estrictas:** Sin archivos `.env`, sin contraseñas reales quemadas, sin dependencias instaladas (`node_modules`, `.venv`), y sin `__pycache__`.