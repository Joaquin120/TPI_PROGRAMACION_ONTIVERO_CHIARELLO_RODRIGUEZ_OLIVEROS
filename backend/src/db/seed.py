"""Script idempotente de carga de datos iniciales para Librería Web.

Garantiza editoriales, géneros, autores, libros iniciales con stock suficiente
y un cliente de muestra sin duplicar registros ni sobrescribir precios o stocks
modificados posteriormente (invariante G-05 / G-07).

Ejecución CLI:
    python -m src.db.seed
"""

import asyncio
from decimal import Decimal
import logging
from typing import Any, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.autor import Autor
from src.db.models.cliente import Cliente
from src.db.models.editorial import Editorial
from src.db.models.genero import Genero
from src.db.models.libro import Libro
from src.db.models.libro_autor import LibroAutor

logger = logging.getLogger(__name__)

T = TypeVar("T")

EDITORIALES_INICIALES: tuple[str, ...] = (
    "Sudamericana",
    "Planeta",
    "Alianza",
)

GENEROS_INICIALES: tuple[str, ...] = (
    "Ficción",
    "Ciencia Ficción",
    "Ensayo",
)

AUTORES_INICIALES: tuple[dict[str, str], ...] = (
    {
        "nombre": "Gabriel García Márquez",
        "biografia": "Escritor colombiano, figura central del realismo mágico.",
    },
    {
        "nombre": "Jorge Luis Borges",
        "biografia": "Escritor argentino referente del cuento filosófico y el ensayo.",
    },
    {
        "nombre": "Julio Cortázar",
        "biografia": "Escritor argentino maestro de la narrativa breve y moderna.",
    },
)

LIBROS_INICIALES: tuple[dict[str, Any], ...] = (
    {
        "titulo": "Cien años de soledad",
        "isbn": "9788439733072",
        "precio": Decimal("25000.00"),
        "stock": 15,
        "editorial": "Sudamericana",
        "genero": "Ficción",
        "autor": "Gabriel García Márquez",
    },
    {
        "titulo": "Ficciones",
        "isbn": "9788499089508",
        "precio": Decimal("18500.00"),
        "stock": 20,
        "editorial": "Alianza",
        "genero": "Ficción",
        "autor": "Jorge Luis Borges",
    },
    {
        "titulo": "Rayuela",
        "isbn": "9788420471891",
        "precio": Decimal("22000.00"),
        "stock": 12,
        "editorial": "Planeta",
        "genero": "Ficción",
        "autor": "Julio Cortázar",
    },
)

CLIENTES_INICIALES: tuple[dict[str, str], ...] = (
    {
        "nombre": "Lucía Fernández",
        "email": "lucia.fernandez@ejemplo.com",
    },
)


async def _obtener_o_crear(
    session: AsyncSession,
    model: type[T],
    lookup_column: Any,
    lookup_value: Any,
    create_kwargs: dict[str, Any],
) -> tuple[T, bool]:
    """Busca un registro por clave natural y lo crea únicamente si no existe."""
    stmt = select(model).where(lookup_column == lookup_value)
    existente = (await session.execute(stmt)).scalar_one_or_none()
    if existente is not None:
        return existente, False

    instancia = model(**create_kwargs)
    session.add(instancia)
    await session.flush()
    return instancia, True


async def seed_database(session: AsyncSession) -> dict[str, int]:
    """Inserta datos mínimos iniciales de forma idempotente sin alterar existentes."""
    resumen = {
        "editoriales_creadas": 0,
        "generos_creados": 0,
        "autores_creados": 0,
        "libros_creados": 0,
        "clientes_creados": 0,
    }

    editoriales_map: dict[str, Editorial] = {}
    for nombre in EDITORIALES_INICIALES:
        editorial, creada = await _obtener_o_crear(
            session, Editorial, Editorial.nombre, nombre, {"nombre": nombre}
        )
        editoriales_map[nombre] = editorial
        if creada:
            resumen["editoriales_creadas"] += 1

    generos_map: dict[str, Genero] = {}
    for nombre in GENEROS_INICIALES:
        genero, creado = await _obtener_o_crear(
            session, Genero, Genero.nombre, nombre, {"nombre": nombre}
        )
        generos_map[nombre] = genero
        if creado:
            resumen["generos_creados"] += 1

    autores_map: dict[str, Autor] = {}
    for datos_autor in AUTORES_INICIALES:
        autor, creado = await _obtener_o_crear(
            session, Autor, Autor.nombre, datos_autor["nombre"], dict(datos_autor)
        )
        autores_map[datos_autor["nombre"]] = autor
        if creado:
            resumen["autores_creados"] += 1

    for datos_libro in LIBROS_INICIALES:
        editorial = editoriales_map[datos_libro["editorial"]]
        genero = generos_map[datos_libro["genero"]]
        autor = autores_map[datos_libro["autor"]]

        # No sobrescribir libros existentes para preservar cambios de precio/stock (G-05 / G-07).
        libro, creado = await _obtener_o_crear(
            session,
            Libro,
            Libro.isbn,
            datos_libro["isbn"],
            {
                "titulo": datos_libro["titulo"],
                "isbn": datos_libro["isbn"],
                "precio": datos_libro["precio"],
                "stock": datos_libro["stock"],
                "editorial_id": editorial.id,
                "genero_id": genero.id,
            },
        )
        if creado:
            resumen["libros_creados"] += 1
            session.add(
                LibroAutor(
                    libro_id=libro.id,
                    autor_id=autor.id,
                    rol="autor",
                    orden=1,
                )
            )
            await session.flush()

    for datos_cliente in CLIENTES_INICIALES:
        _, creado = await _obtener_o_crear(
            session, Cliente, Cliente.email, datos_cliente["email"], dict(datos_cliente)
        )
        if creado:
            resumen["clientes_creados"] += 1

    await session.commit()
    return resumen


async def run_seed() -> dict[str, int]:
    """Abre una sesión asíncrona contra DATABASE_URL, ejecuta el seed y libera el pool."""
    from src.db.session import async_session_factory, engine

    try:
        async with async_session_factory() as session:
            return await seed_database(session)
    finally:
        await engine.dispose()


def main() -> None:
    """Punto de entrada CLI para ejecutar `python -m src.db.seed`."""
    resumen = asyncio.run(run_seed())
    print(f"[seed] Datos iniciales procesados: {resumen}")


if __name__ == "__main__":
    main()
