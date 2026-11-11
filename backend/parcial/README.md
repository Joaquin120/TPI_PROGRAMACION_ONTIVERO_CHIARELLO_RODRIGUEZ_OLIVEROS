# Parcial 2 Programación — Backend (Capítulos 1 a 6)

Backend asíncrono para la gestión de catálogo de libros, stock transaccional con auditoría append-only, transacciones atómicas de venta bajo Unit of Work y control de acceso dinámico por roles (RBAC) con mitigación de ataques de seguridad.

---

## 📋 Credenciales Iniciales de Prueba (Seed)

El script `parcial/seed.py` inicializa la base de datos con los usuarios canónicos requeridos por la consigna, todos configurados con la contraseña estándar **`Password123!`**:

| Email | Rol | Debe Cambiar Password | Propósito / Rol en el Sistema |
|---|---|:---:|---|
| `admin@example.com` | `ADMIN` | No | Administrador principal con permisos globales de gestión |
| `admin2@example.com` | `ADMIN` | No | Administrador secundario para verificar autoprotección |
| `vendedor@example.com` | `VENDEDOR` | No | Personal de ventas (emisión de ventas y reposición) |
| `ana@example.com` | `CLIENTE` | No | Cliente con cuenta de usuario vinculada a su ficha de cliente |
| `nuevo@example.com` | `VENDEDOR` | **Sí** | Usuario nuevo bloqueado para grupos protegidos hasta cambiar clave |

---

## 🚀 Guía de Puesta en Marcha

### 1. Activar Entorno Virtual e Instalar Dependencias

```bash
# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Iniciar PostgreSQL

```bash
docker compose up -d
```

### 3. Aplicar Migraciones de Base de Datos

Aplica las migraciones de Alembic hasta el trigger append-only:

```bash
alembic upgrade head
```

### 4. Ejecutar la Siembra de Datos Iniciales (Seed)

Ejecuta el script idempotente que crea los usuarios, catálogo, clientes, Venta 1 y balance de stock:

```bash
python -m parcial.seed
```

Salida esperada:
```text
=====================================================================
INICIANDO CARGA DE DATOS INICIALES (SEED) - PARCIAL CAPÍTULOS 1 A 6
=====================================================================
[SEED] Creado usuario admin@example.com (ADMIN)
...
[SEED] Creado libro 'Rayuela' con stock inicial 10
...
[SEED] Registrada Venta 1 Total: $69000.00 para Lucía Fernández
[SEED] Evento de auditoría 'SISTEMA' registrado exitosamente.
[INVARIANTE OK] 'Rayuela': Stock=9 == SUM(Movimientos)=9
...
SEED COMPLETADO CON ÉXITO
```

### 5. Iniciar Servidor de Desarrollo

```bash
uvicorn parcial.app.main:app --reload --port 8000
```

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Ejecución de Pruebas

### 1. Suite Automatizada E2E de Casos C-01 a C-16 (Pytest)

Ejecuta programáticamente la suite completa que valida todos los requerimientos de la consigna:

```bash
pytest parcial/tests/integration/test_e2e_casos_c01_c16.py -v
```

Para correr todas las pruebas de integración del parcial:
```bash
pytest parcial/tests/integration/ -v
```

### 2. Archivos de Peticiones REST (.http)

En la carpeta `parcial/test/` se encuentran disponibles los archivos listos para ejecutar mediante la extensión **REST Client** de VS Code o el cliente HTTP de IntelliJ:

- `suite_completa_c01_a_c16.http`: Flujo integral secuencial de todos los casos.
- Archivos individuales por caso:
  - `c01_login_cookie.http`: Login exitoso con cookie HttpOnly y sin token en body.
  - `c02_rechazo_bearer.http`: Rechazo de `Authorization: Bearer` y peticiones sin cookie (401).
  - `c03_rate_limiting.http`: 5 intentos fallidos en 60s disparan HTTP 429 con `Retry-After: 60`.
  - `c04_timing_attacks.http`: Tiempos uniformes con hash ficticio ante usuarios inexistentes.
  - `c05_cambio_password.http`: Bloqueo 403 por `debe_cambiar_password` y desbloqueo tras cambio.
  - `c06_roles_dinamicos.http`: Consulta dinámica a BD y efecto inmediato de revocación.
  - `c07_autoproteccion_admin.http`: Rechazo 409 a la auto-revocación del último admin.
  - `c08_contratos_estrictos.http`: `extra="forbid"` rechaza campos no definidos (422).
  - `c09_paginacion_estandar.http`: Envoltorio `{items, total, page, size, pages}` y rechazo si `page > pages`.
  - `c10_catalogo_reposicion_stock.http`: Alta, reposición y bloqueo de edición de stock por PATCH.
  - `c11_soft_delete_libro.http`: Borrado lógico (204), exclusión del catálogo y reuso de ISBN.
  - `c12_ventas_atomicas.http`: Venta atómica en único UoW con deducción de stock.
  - `c13_rollback_stock_insuficiente.http`: Rollback transaccional íntegro ante falta de existencias (409).
  - `c14_trigger_append_only.http`: Referencia y guía del disparador de base de datos.
  - `c15_ventas_sin_nplusone.http`: Detalle de venta en cantidad fija de consultas.
  - `c16_permisos_detalle_venta.http`: Control de titularidad y rol en `GET /ventas/{id}`.

### 3. Verificación del Trigger Append-Only en PostgreSQL (Caso C-14)

Ejecutar directamente en el motor de base de datos mediante `psql`:

```bash
docker compose exec db psql -U postgres -d tp_cap1a4_db -f /parcial/test/solo_agregado.sql
# O desde la máquina host:
psql -U postgres -h localhost -p 5432 -d tp_cap1a4_db -f parcial/test/solo_agregado.sql
```

Salida esperada:
```text
NOTICE:  ÉXITO C-14 (UPDATE): El trigger rechazó la modificación correctamente: La tabla movimiento_stock es de sólo agregado...
NOTICE:  ÉXITO C-14 (DELETE): El trigger rechazó la eliminación correctamente: La tabla movimiento_stock es de sólo agregado...
```

---

## 📊 Evidencias Técnicas

- **Ausencia de Consultas N+1 (Caso C-15):** Documentación cuantitativa y análisis de plan de consultas en [parcial/evidencia/c15_nplusone_evidence.md](evidencia/c15_nplusone_evidence.md).
