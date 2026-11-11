# Librería Web — Base de Conocimiento (Knowledge Base)

Base de conocimiento canónica generada para el Trabajo Práctico Integrador (TPI) de Programación III: *Integración de Librería Web y Despliegue en Easypanel*.

---

## Índice de Archivos Canónicos

| # | Archivo | Contenido Temático |
|---|---|---|
| 01 | [01_vision_y_objetivos.md](01_vision_y_objetivos.md) | Propósito del sistema, objetivos por actor, alcance v1.0 y métricas de éxito. |
| 02 | [02_descripcion_general.md](02_descripcion_general.md) | Stack tecnológico, arquitectura general desacoplada, proxy Nginx y resumen de endpoints REST. |
| 03 | [03_actores_y_roles.md](03_actores_y_roles.md) | Actores del sistema, roles de autoría válidos y matriz de operaciones. |
| 04 | [04_modelo_de_datos.md](04_modelo_de_datos.md) | Diagrama entidad-relación (ERD), entidades, restricciones y seed data requerido. |
| 05 | [05_reglas_de_negocio.md](05_reglas_de_negocio.md) | Reglas codificadas por dominio (`RN-LIB-XX`, `RN-CLI-XX`, `RN-VEN-XX`) e invariante de precios. |
| 06 | [06_funcionalidades.md](06_funcionalidades.md) | Historias de usuario (`US-001` a `US-008`) organizadas por épica con criterios de aceptación. |
| 07 | [07_flujos_principales.md](07_flujos_principales.md) | Flujos extremo a extremo, diagramas de secuencia del registro de venta y caso G-05. |
| 08 | [08_arquitectura_propuesta.md](08_arquitectura_propuesta.md) | Patrones de diseño, estructura de directorios, proxy Nginx y variables de entorno. |
| 09 | [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md) | Registro de decisiones arquitectónicas (`DD-01` a `DD-03`) y supuestos (`SU-01`, `SU-02`). |
| 10 | [10_preguntas_abiertas.md](10_preguntas_abiertas.md) | Inconsistencias detectadas (`IN-01`, `IN-02`) y preguntas abiertas priorizadas. |
| 11 | [11_despliegue_y_casos_de_prueba.md](11_despliegue_y_casos_de_prueba.md) | Matriz completa de validación de los casos de prueba `G-01` a `G-07` en la URL pública. |

---

## Quick Start para Desarrolladores

1. **Entender el dominio y requerimientos:** Leer [01_vision_y_objetivos.md](01_vision_y_objetivos.md) y [03_actores_y_roles.md](03_actores_y_roles.md).
2. **Entender el modelo y las tablas:** Consultar [04_modelo_de_datos.md](04_modelo_de_datos.md).
3. **Reglas duras de validación:** Revisar [05_reglas_de_negocio.md](05_reglas_de_negocio.md) antes de escribir lógica de negocio.
4. **Arquitectura y Docker:** Seguir [02_descripcion_general.md](02_descripcion_general.md) y [08_arquitectura_propuesta.md](08_arquitectura_propuesta.md).
5. **Implementación de tareas:** Guiarse por los criterios de aceptación en [06_funcionalidades.md](06_funcionalidades.md).
6. **Validación previa a la entrega:** Correr los casos de prueba en [11_despliegue_y_casos_de_prueba.md](11_despliegue_y_casos_de_prueba.md).

---

## Resumen Ejecutivo
El proyecto integra el frontend en JavaScript nativo del Parcial 1 con la API en FastAPI y PostgreSQL del Parcial 2. Nginx actúa como reverse proxy sirviendo la interfaz y canalizando las llamadas a `/api/` hacia el backend. Se garantiza la inmutabilidad de precios históricos en las ventas, la resiliencia ante errores de negocio (409 y 422) y el despliegue contenerizado en Easypanel cumpliendo los casos de prueba G-01 a G-07.
