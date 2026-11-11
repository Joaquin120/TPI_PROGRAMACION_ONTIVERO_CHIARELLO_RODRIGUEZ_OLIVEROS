# Arquitectura Propuesta

## Patrones aplicados
| Patrón | Dónde se aplica | Justificación |
|---|---|---|
| **Reverse Proxy / API Gateway** | Nginx (`default.conf.template`) | Centraliza la entrada HTTP, mapea `/api/` hacia el servicio FastAPI interno y sirve el bundle estático en `/`. Elimina problemas de CORS. |
| **Separación de Responsabilidades (Layered)** | Backend FastAPI (`api/`, `core/`, `db/`, `schemas/`) | Separa los controladores HTTP (routers), los esquemas de validación (Pydantic), y la capa de acceso a datos (SQLAlchemy). |
| **Snapshot / Historical Copy** | Renglón de venta (`ventas_renglones.precio_unitario`) | Congela el valor del activo en el momento de la transacción para asegurar inmutabilidad financiera. |
| **Client HTTP Abstraction** | Frontend (`js/api.js`) | Encapsula todas las llamadas `fetch` nativas con manejo de cabeceras JSON, deserialización de errores y prefijo `/api/`. |

## Estructura de Directorios del Proyecto Unificado
```text
TPI_PROGRAMACION_ONTIVERO_CHIARELLO_RODRIGUEZ_OLIVEROS/
├── frontend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── default.conf.template
│   └── public/
│       ├── index.html
│       ├── css/
│       │   └── style.css
│       ├── js/
│       │   ├── api.js                # Cliente HTTP unificado (fetch /api)
│       │   └── app.js                # Renderizado, eventos y borrador de venta
│       └── img/
├── backend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/                 # Scripts de migración SQL
│   └── src/
│       ├── main.py                   # Inicialización de FastAPI y routers
│       ├── api/                      # Routers: libros, clientes, ventas, etc.
│       ├── core/                     # Configuración (pydantic-settings)
│       ├── db/                       # Sesión asíncrona y modelos SQLAlchemy
│       └── schemas/                  # Modelos Pydantic de entrada/salida
├── docker-compose.yml                # Orquestación local para desarrollo
├── docs/
│   └── consignas_global_evaluacion_y_despliegue.md
├── knowledge-base/                   # Documentación canónica generada
├── openspec/                         # Especificaciones y roadmap
├── README.md
└── DEPLOY.md
```

## Configuración y Variables de Entorno

### Backend
| Variable | Descripción | Ejemplo | Sensible |
|---|---|---|---|
| `DATABASE_URL` | URI de conexión asíncrona a PostgreSQL | `postgresql+asyncpg://libreria_user:secreto@db:5432/libreria_db` | **SÍ** |
| `ENVIRONMENT` | Entorno de ejecución (`development`, `production`) | `production` | NO |

### Frontend (Nginx)
| Variable | Descripción | Ejemplo | Sensible |
|---|---|---|---|
| `API_UPSTREAM` | Host y puerto del servicio backend accesible en la red Docker | `backend:8000` (Easypanel) / `host.docker.internal:8000` (Local) | NO |
| `NGINX_ENVSUBST_FILTER` | Filtro para evitar que envsubst toque variables internas de Nginx | `^API_UPSTREAM$` | NO |

## Seguridad e Higiene del Repositorio
1. **Regla de oro de credenciales:** Prohibido subir archivos `.env` reales al repositorio. Se proveen exclusivamente archivos `.env.example`.
2. **Prohibición de binarios y dependencias:** No versionar carpetas `__pycache__`, `.venv`, `.pytest_cache`, ni `node_modules`.
3. **Validación de entradas:** Esquemas Pydantic rigurosos en FastAPI para sanitizar y tipar cada payload recibido.
