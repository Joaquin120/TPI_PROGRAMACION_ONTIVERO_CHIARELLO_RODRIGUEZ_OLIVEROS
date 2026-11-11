# Descripción General

## Stack tecnológico
| Capa | Tecnologías | Versión / Entorno |
|---|---|---|
| **Frontend** | HTML5, CSS3, JavaScript nativo (ES6+ Modules / Fetch API) | Navegadores modernos (sin frameworks externos) |
| **Proxy / Servidor Web** | Nginx con `default.conf.template` | `nginx:1.26-alpine` |
| **Backend / API** | Python, FastAPI, Uvicorn, Pydantic | Python 3.12-slim, FastAPI >= 0.110 |
| **ORM / Migraciones** | SQLAlchemy (Asyncio), Alembic | SQLAlchemy 2.0+, Alembic |
| **Base de Datos** | PostgreSQL con driver `asyncpg` | PostgreSQL 15 / 16 |
| **Contenerización** | Docker, Docker Compose | Docker Engine 24+, Compose v2 |
| **Infraestructura VPS** | Easypanel sobre VPS Linux | Dominio público con SSL/TLS automático |

## Arquitectura general
La solución implementa una arquitectura desacoplada en dos capas principales mediadas por un Reverse Proxy:

```
[ Navegador del Usuario ]
           │ (HTTPS)
           ▼
┌────────────────────────────────────────────────────────┐
│                   Contenedor Frontend                  │
│  ┌────────────────────────┐  ┌───────────────────────┐ │
│  │     Archivos Web       │  │      Proxy Nginx      │ │
│  │ (HTML / CSS / JS / UI) │  │  /    -> static html  │ │
│  │                        │  │  /api -> proxy_pass   │ │
│  └────────────────────────┘  └───────────┬───────────┘ │
└──────────────────────────────────────────┼─────────────┘
                                           │ (HTTP interno puerto 8000)
                                           ▼
┌────────────────────────────────────────────────────────┐
│                   Contenedor Backend                   │
│  FastAPI (Uvicorn) - Endpoints REST en /libros, etc.   │
│  Alembic - Migraciones automáticas al inicio           │
└──────────────────────────┬─────────────────────────────┘
                           │ (Conexión asyncpg: 5432)
                           ▼
┌────────────────────────────────────────────────────────┐
│                   Servicio PostgreSQL                  │
│       Tablas relacionales: libros, ventas, etc.        │
└────────────────────────────────────────────────────────┘
```

### Justificación de decisiones arquitectónicas
1. **Prefijo `/api` y Nginx Reverse Proxy:** El cliente JavaScript utiliza URLs relativas con `/api/` (ej. `fetch('/api/libros/')`). Nginx reescribe y reenvía las peticiones al upstream interno del backend (`http://${API_UPSTREAM}/`), eliminando problemas de CORS (*Cross-Origin Resource Sharing*) y permitiendo exponer un solo puerto público (80/443).
2. **FastAPI Asíncrono + PostgreSQL:** Alta concurrencia y bajo consumo de memoria, ideal para despliegues ligeros en VPS con recursos limitados.
3. **Persistencia inmutable de precios en ventas:** Cada renglón de venta almacena explícitamente el precio unitario pactado al momento de la transacción para garantizar la invariabilidad histórica.

## Integraciones externas
| Servicio | Propósito | Tipo |
|---|---|---|
| **Easypanel PaaS** | Orquestación de contenedores, gestión de variables de entorno y certificados SSL/Let's Encrypt | Plataforma de despliegue sobre VPS |
| **GitHub Container / Git Sync** | Repositorio remoto para build automatizado en Easypanel | Control de versiones |

## API REST — Resumen de endpoints principales
Todas las rutas públicas son accedidas desde el frontend a través del proxy con el prefijo `/api`:

| Método | Ruta Backend | Ruta Frontend (Proxy) | Descripción | Códigos |
|---|---|---|---|---|
| `GET` | `/health/ready` | `/api/health/ready` | Verificación de estado y conexión a DB | `200` |
| `GET` | `/libros/` | `/api/libros/` | Listar catálogo (con `limit`, `offset`, `titulo`) | `200` |
| `GET` | `/libros/{id}` | `/api/libros/{id}` | Detalle de libro y autores | `200`, `404` |
| `POST` | `/libros/` | `/api/libros/` | Alta de nuevo libro con autorías | `201`, `409`, `422` |
| `PATCH`| `/libros/{id}` | `/api/libros/{id}` | Actualizar atributos de libro (ej. precio) | `200`, `404`, `422` |
| `GET` | `/editoriales/`| `/api/editoriales/`| Listar opciones de editorial | `200` |
| `GET` | `/generos/` | `/api/generos/` | Listar opciones de género | `200` |
| `GET` | `/autores/{id}`| `/api/autores/{id}`| Consultar autor por identificador | `200`, `404` |
| `GET` | `/clientes/{id}`| `/api/clientes/{id}`| Consultar cliente por identificador | `200`, `404` |
| `POST` | `/clientes/` | `/api/clientes/` | Registrar nuevo cliente | `201`, `409`, `422` |
| `GET` | `/ventas/` | `/api/ventas/` | Historial paginado de ventas | `200` |
| `GET` | `/ventas/{id}` | `/api/ventas/{id}` | Detalle completo de una venta e importes | `200`, `404` |
| `POST` | `/ventas/` | `/api/ventas/` | Confirmar y persistir una venta | `201`, `409`, `422` |
