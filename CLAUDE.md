# Librería Web — Instrucciones para Agentes

> Este archivo (y su copia `CLAUDE.md`) es lo PRIMERO que todo agente lee al entrar al repo.
> Generado a partir de `knowledge-base/` y `CHANGES.md`. No editar a mano sin re-sincronizar ambos archivos.

---

## Stack Tecnológico

| Capa | Tecnologías | Versión / Entorno |
|---|---|---|
| **Frontend** | HTML5, CSS3, JavaScript nativo (ES6+ Modules / Fetch API) | Navegadores modernos (sin frameworks externos) |
| **Proxy / Servidor Web** | Nginx con `default.conf.template` | `nginx:1.26-alpine` |
| **Backend / API** | Python, FastAPI, Uvicorn, Pydantic | Python 3.12-slim, FastAPI >= 0.110 |
| **ORM / Migraciones** | SQLAlchemy (Asyncio), Alembic | SQLAlchemy 2.0+, Alembic |
| **Base de Datos** | PostgreSQL con driver `asyncpg` | PostgreSQL 15 / 16 |
| **Contenerización** | Docker, Docker Compose | Docker Engine 24+, Compose v2 |
| **Infraestructura VPS** | Easypanel sobre VPS Linux | Dominio público con SSL/TLS automático |

Detalle completo: [knowledge-base/02_descripcion_general.md](knowledge-base/02_descripcion_general.md)

---

## Base de Conocimiento

La fuente de verdad del dominio vive en `knowledge-base/`. **Leé el archivo relevante ANTES de implementar.**

| Archivo | Cuándo leerlo |
|---|---|
| [01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) | Propósito del sistema, objetivos por actor y alcance |
| [02_descripcion_general.md](knowledge-base/02_descripcion_general.md) | Arquitectura general, proxy Nginx y contratos REST |
| [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) | Roles de autoría (`autor`, `coautor`, etc.) y matriz de permisos |
| [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) | Entidades, ERD, relaciones y seed data inicial |
| [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) | Reglas duras codificadas (`RN-LIB-XX`, `RN-CLI-XX`, `RN-VEN-XX`) |
| [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) | Historias de usuario por épica y criterios de aceptación |
| [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) | Flujos E2E de venta, catálogo e invariante de precios |
| [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) | Patrones, monorepo, variables de entorno y proxy |
| [09_decisiones_y_supuestos.md](knowledge-base/09_decisiones_y_supuestos.md) | Registro de decisiones arquitectónicas y supuestos |
| [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) | Inconsistencias a resolver antes de codificar |
| [11_despliegue_y_casos_de_prueba.md](knowledge-base/11_despliegue_y_casos_de_prueba.md) | Protocolo de validación de casos G-01 a G-07 en la URL pública |

---

## Skills Disponibles

| Agente | Rol | Skills que carga |
|---|---|---|
| **Backend / DB** | FastAPI, SQLAlchemy, Alembic, PostgreSQL | `poteto-mode`, `loop` |
| **Frontend / Web** | HTML5, CSS3, JavaScript nativo, Fetch API | `poteto-mode` |
| **DevOps / Infra** | Docker, Nginx proxy, Easypanel, despliegue | `poteto-mode` |
| **Orquestación** | SDD, OpenSpec, Roadmap y Foundation | `kb-creator`, `roadmap-generator`, `agents-md-generator`, `active-orchestrator` |

> Los compact rules de cada skill los resuelve el orquestador desde `.atl/skill-registry.md` (generado por `skill-registry`; no versionado — no está en el repo). Esta tabla solo mapea skill→rol.

---

## Roadmap de Changes

El plan de implementación completo está en [CHANGES.md](CHANGES.md). Resumen:

- **Total**: 9 changes (`C-01` a `C-09`) organizados en 6 fases.
- **Camino crítico** (6 changes): `C-01 → C-02 → C-03 → C-06 → C-07 → C-09`.
- **Primer change**: `C-01` (`foundation-setup`).

**Antes de cualquier `/opsx:propose`**: leé [CHANGES.md](CHANGES.md), identificá las dependencias del change y los archivos de "Leer antes".

---

## Reglas Duras (específicas del proyecto)

> Reglas globales ya definidas en `~/.claude/CLAUDE.md` (orquestador, governance, TDD, engram): el proyecto las hereda.

1. **NUNCA usar `localStorage` para persistencia de negocio confirmada → todo pasa por la API REST vía `fetch` nativo.** En memoria del navegador solo se mantiene el borrador transitorio de la venta.
2. **SIEMPRE usar el prefijo `/api/` en las peticiones del frontend y conservar la barra final (`trailing slash`) en rutas de colección (`/api/libros/`, `/api/ventas/`, `/api/clientes/`).**
3. **NUNCA alterar precios de ventas ya registradas → el precio unitario se congela inmutablemente en `ventas_renglones` al momento del `POST /ventas/`.**
4. **NUNCA commitear archivos `.env` reales, contraseñas quemadas, carpetas `__pycache__`, `.venv`, `.pytest_cache` ni `node_modules` → proveer exclusivamente `.env.example`.**
5. **SIEMPRE capturar y presentar amigablemente los errores de negocio `409 Conflict` (duplicados de ISBN o email, cliente/libro inexistente) y `422 Unprocessable Entity` (violación de contrato) sin cerrar ni borrar los formularios o el carrito.**
6. **NUNCA permitir dobles envíos de ventas → deshabilitar el botón de confirmación en la UI mientras la promesa de red esté pendiente.**
7. **SIEMPRE ejecutar migraciones de base de datos automáticamente al arrancar el contenedor backend con `alembic upgrade head`.**

---

## Flujo de Trabajo

```
1. Leer la KB relevante (knowledge-base/)        → entender el dominio
2. Identificar el change en CHANGES.md           → respetar dependencias
3. /opsx:propose C-NN-nombre                     → proposal + design + specs + tasks
4. Implementar las tasks                         → respetando las reglas duras
5. /opsx:archive C-NN-nombre + marcar [x]        → cerrar el change
```

Aplicar TODAS las reglas duras en cada paso. Ante conflicto entre la KB y este archivo, las reglas duras prevalecen.
