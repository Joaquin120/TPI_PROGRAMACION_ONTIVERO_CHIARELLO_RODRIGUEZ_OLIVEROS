# Actores y Roles

## Actores del sistema
| Actor | Descripción | Interacción con la Interfaz |
|---|---|---|
| **Operador de Librería (General)** | Usuario administrativo o cajero que gestiona el inventario de libros y ejecuta transacciones de venta. | - Navega y busca en el catálogo.<br>- Da de alta libros completando datos y seleccionando autores.<br>- Da de alta nuevos clientes.<br>- Arma ventas, selecciona cliente y libros, y confirma.<br>- Consulta el historial y los detalles de ventas pasadas. |
| **Evaluador Académico** | Docente que audita los contratos HTTP, la resiliencia ante errores de negocio, el invariante de precios y la infraestructura desplegada. | - Ejecuta la suite de casos G-01 a G-07.<br>- Comprueba la respuesta de salud en `/api/health/ready`.<br>- Valida que no haya secretos expuestos ni `.env` quemados. |

## Roles de Autoría (Dominio Libros)
En la asignación de autores a libros (`POST /libros/`), el sistema distingue roles de participación formal:
| Rol de Autoría | Descripción | Valor esperado en API |
|---|---|---|
| **Autor Principal** | Creador principal de la obra literaria o técnica. | `"autor"` |
| **Coautor** | Participante en la autoría conjunta. | `"coautor"` |
| **Traductor** | Responsable de la traducción al idioma de la edición. | `"traductor"` |
| **Ilustrador** | Artista gráfico a cargo de ilustraciones o portada. | `"ilustrador"` |

*Nota:* Cada autoría requiere adicionalmente un entero `orden` (1, 2, ...) para determinar la precedencia de visualización.

## Matriz de Operaciones y Recursos
El sistema opera en modo quiosco/operativo abierto según la especificación del Global (sin módulo de autenticación con contraseñas):

| Recurso | Lectura (GET) | Creación (POST) | Modificación (PATCH) | Eliminación (DELETE) |
|---|---|---|---|---|
| `/libros/` | Abierto a todos | Operador | Operador (precios) | No permitido |
| `/editoriales/` | Abierto a todos | Seed inicial | No permitido | No permitido |
| `/generos/` | Abierto a todos | Seed inicial | No permitido | No permitido |
| `/autores/` | Abierto a todos | Seed inicial | No permitido | No permitido |
| `/clientes/` | Abierto a todos | Operador | No permitido | No permitido |
| `/ventas/` | Abierto a todos | Operador | Inmutable | No permitido |

## Rutas públicas
- `/` e `index.html`: Acceso general a la Single-Page / Multi-Section Application del frontend.
- `/api/health/ready`: Endpoint de health check para Easypanel y balanceadores.
