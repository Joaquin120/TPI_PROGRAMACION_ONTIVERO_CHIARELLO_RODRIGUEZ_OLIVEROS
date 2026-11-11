"""Script canónico de carga de datos iniciales (Seed) para el Parcial.

Consigna Parcial §4.1:
- Usuarios:
  * admin@example.com (ADMIN)
  * admin2@example.com (ADMIN)
  * vendedor@example.com (VENDEDOR)
  * ana@example.com (CLIENTE)
  * nuevo@example.com (VENDEDOR, debe_cambiar_password = True)
- 5 libros del TP con stock inicial balanceado (libro.stock == SUM(movimientos)):
  * Rayuela (10)
  * Antología poética (5)
  * Ficciones (8)
  * Respiración artificial (3)
  * Bestiario (1)
- Clientes:
  * Lucía Fernández (sin usuario)
  * Tomás Ríos (sin usuario)
  * Ana Paz (con usuario ana@example.com)
- Venta inicial 1:
  * Lucía compra 1 Rayuela ($25.000) y 2 Ficciones ($22.000 cada uno) -> Total $69.000,00
  * Stock deducido y movimientos negativos registrados (libro.stock == SUM(movimientos))
- Auditoría:
  * Registro inicial en evento_seguridad con actor 'SISTEMA'

Ejecución:
    python -m parcial.seed
    o
    python parcial/seed.py
"""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
import sys

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from parcial.app.core.database import async_session_factory
from parcial.app.core.security import hash_password
from parcial.app.modules.clientes.models import Cliente
from parcial.app.modules.libros.models import Autor, Editorial, Genero, Libro, MovimientoStock
from parcial.app.modules.usuarios.models import AsignacionRol, EventoSeguridad, Usuario
from parcial.app.modules.ventas.models import DetalleVenta, Venta

DEFAULT_PASSWORD = "Password123!"


async def seed_usuarios(session: AsyncSession) -> dict[str, Usuario]:
    """Crea o recupera los usuarios canónicos requeridos por la consigna."""
    usuarios_data = [
        {"email": "admin@example.com", "nombre": "Admin Principal", "rol": "ADMIN", "debe_cambiar": False},
        {"email": "admin2@example.com", "nombre": "Admin Secundario", "rol": "ADMIN", "debe_cambiar": False},
        {"email": "vendedor@example.com", "nombre": "Carlos Vendedor", "rol": "VENDEDOR", "debe_cambiar": False},
        {"email": "ana@example.com", "nombre": "Ana Paz", "rol": "CLIENTE", "debe_cambiar": False},
        {"email": "nuevo@example.com", "nombre": "Nuevo Empleado", "rol": "VENDEDOR", "debe_cambiar": True},
    ]

    usuarios_map: dict[str, Usuario] = {}

    for u_info in usuarios_data:
        stmt = select(Usuario).where(Usuario.email == u_info["email"])
        res = await session.execute(stmt)
        usuario = res.scalar_one_or_none()

        if usuario is None:
            pwd_hash = await hash_password(DEFAULT_PASSWORD)
            usuario = Usuario(
                email=u_info["email"],
                nombre=u_info["nombre"],
                password_hash=pwd_hash,
                activo=True,
                debe_cambiar_password=u_info["debe_cambiar"],
            )
            session.add(usuario)
            await session.flush()

            # Asignación de rol activo sin vencimiento
            asignacion = AsignacionRol(
                usuario_id=usuario.id,
                rol=u_info["rol"],
                desde=datetime.now(timezone.utc),
                vence_en=None,
                revocada_en=None,
                otorgada_por=None,
            )
            session.add(asignacion)
            await session.flush()
            print(f"[SEED] Creado usuario {usuario.email} ({u_info['rol']}) - debe_cambiar: {usuario.debe_cambiar_password}")
        else:
            print(f"[SEED] Usuario existente: {usuario.email}")

        usuarios_map[usuario.email] = usuario

    return usuarios_map


async def seed_catalogo(session: AsyncSession, admin_user: Usuario) -> dict[str, Libro]:
    """Crea entidades maestras y los 5 libros canónicos con sus movimientos de stock iniciales."""
    # Autores
    autores_nombres = ["Julio Cortázar", "Jorge Luis Borges", "Ricardo Piglia"]
    autores_map: dict[str, Autor] = {}
    for nombre in autores_nombres:
        stmt = select(Autor).where(Autor.nombre == nombre)
        res = await session.execute(stmt)
        autor = res.scalar_one_or_none()
        if autor is None:
            autor = Autor(nombre=nombre, biografia=f"Autor célebre: {nombre}")
            session.add(autor)
            await session.flush()
        autores_map[nombre] = autor

    # Editoriales
    editoriales_nombres = ["Sudamericana", "Emecé", "Anagrama"]
    editoriales_map: dict[str, Editorial] = {}
    for nombre in editoriales_nombres:
        stmt = select(Editorial).where(Editorial.nombre == nombre)
        res = await session.execute(stmt)
        ed = res.scalar_one_or_none()
        if ed is None:
            ed = Editorial(nombre=nombre)
            session.add(ed)
            await session.flush()
        editoriales_map[nombre] = ed

    # Géneros
    generos_nombres = ["Novela", "Cuento", "Poesía"]
    generos_map: dict[str, Genero] = {}
    for nombre in generos_nombres:
        stmt = select(Genero).where(Genero.nombre == nombre)
        res = await session.execute(stmt)
        gen = res.scalar_one_or_none()
        if gen is None:
            gen = Genero(nombre=nombre)
            session.add(gen)
            await session.flush()
        generos_map[nombre] = gen

    # 5 Libros del TP con stock inicial de la consigna:
    # Rayuela (10), Antología poética (5), Ficciones (8), Respiración artificial (3), Bestiario (1)
    # Precios unitarios elegidos de modo que Rayuela (25000) + 2*Ficciones (22000) = 69000.00
    libros_data = [
        {
            "isbn": "978-950-07-0001-1",
            "titulo": "Rayuela",
            "precio": Decimal("25000.00"),
            "stock_inicial": 10,
            "autor": "Julio Cortázar",
            "editorial": "Sudamericana",
            "genero": "Novela",
        },
        {
            "isbn": "978-950-07-0002-2",
            "titulo": "Antología poética",
            "precio": Decimal("18000.00"),
            "stock_inicial": 5,
            "autor": "Jorge Luis Borges",
            "editorial": "Emecé",
            "genero": "Poesía",
        },
        {
            "isbn": "978-950-07-0003-3",
            "titulo": "Ficciones",
            "precio": Decimal("22000.00"),
            "stock_inicial": 8,
            "autor": "Jorge Luis Borges",
            "editorial": "Emecé",
            "genero": "Cuento",
        },
        {
            "isbn": "978-950-07-0004-4",
            "titulo": "Respiración artificial",
            "precio": Decimal("21000.00"),
            "stock_inicial": 3,
            "autor": "Ricardo Piglia",
            "editorial": "Anagrama",
            "genero": "Novela",
        },
        {
            "isbn": "978-950-07-0005-5",
            "titulo": "Bestiario",
            "precio": Decimal("19000.00"),
            "stock_inicial": 1,
            "autor": "Julio Cortázar",
            "editorial": "Sudamericana",
            "genero": "Cuento",
        },
    ]

    libros_map: dict[str, Libro] = {}

    for l_info in libros_data:
        stmt = select(Libro).where(Libro.isbn == l_info["isbn"])
        res = await session.execute(stmt)
        libro = res.scalar_one_or_none()

        if libro is None:
            libro = Libro(
                isbn=l_info["isbn"],
                titulo=l_info["titulo"],
                precio=l_info["precio"],
                stock=l_info["stock_inicial"],
                autor_id=autores_map[l_info["autor"]].id,
                editorial_id=editoriales_map[l_info["editorial"]].id,
                genero_id=generos_map[l_info["genero"]].id,
                borrado_en=None,
            )
            session.add(libro)
            await session.flush()

            # Movimiento de stock inicial balanceado
            mov = MovimientoStock(
                libro_id=libro.id,
                venta_id=None,
                usuario_id=admin_user.id,
                cantidad=l_info["stock_inicial"],
                motivo="Stock inicial",
                cuando=datetime.now(timezone.utc),
            )
            session.add(mov)
            await session.flush()
            print(f"[SEED] Creado libro '{libro.titulo}' con stock inicial {libro.stock}")
        else:
            print(f"[SEED] Libro existente: '{libro.titulo}' (Stock: {libro.stock})")

        libros_map[libro.titulo] = libro

    return libros_map


async def seed_clientes(session: AsyncSession, ana_usuario: Usuario) -> dict[str, Cliente]:
    """Crea los clientes requeridos: Lucía Fernández, Tomás Ríos y Ana Paz."""
    clientes_data = [
        {"nombre": "Lucía Fernández", "email": "lucia.fernandez@example.com", "usuario_id": None},
        {"nombre": "Tomás Ríos", "email": "tomas.rios@example.com", "usuario_id": None},
        {"nombre": "Ana Paz", "email": "ana@example.com", "usuario_id": ana_usuario.id},
    ]

    clientes_map: dict[str, Cliente] = {}

    for c_info in clientes_data:
        stmt = select(Cliente).where(Cliente.email == c_info["email"])
        res = await session.execute(stmt)
        cliente = res.scalar_one_or_none()

        if cliente is None:
            cliente = Cliente(
                nombre=c_info["nombre"],
                email=c_info["email"],
                telefono="1144556677",
                direccion="Av. Siempre Viva 742",
                usuario_id=c_info["usuario_id"],
            )
            session.add(cliente)
            await session.flush()
            print(f"[SEED] Creado cliente '{cliente.nombre}' (usuario_id: {cliente.usuario_id})")
        else:
            print(f"[SEED] Cliente existente: '{cliente.nombre}'")

        clientes_map[cliente.nombre] = cliente

    return clientes_map


async def seed_venta_inicial(
    session: AsyncSession,
    cliente_lucia: Cliente,
    vendedor_user: Usuario,
    libros_map: dict[str, Libro],
) -> Venta | None:
    """Registra la Venta inicial 1: Lucía compra 1 Rayuela y 2 Ficciones ($69.000,00).

    Descuenta stock y genera MovimientoStock negativos para preservar el invariante:
    libro.stock == SUM(movimientos).
    """
    # Verificar si ya existe alguna venta previa para Lucía Fernández
    stmt = select(Venta).where(Venta.cliente_id == cliente_lucia.id)
    res = await session.execute(stmt)
    venta_existente = res.scalar_one_or_none()

    if venta_existente is not None:
        print(f"[SEED] Venta inicial ya existente (ID: {venta_existente.id}, Total: {venta_existente.total})")
        return venta_existente

    libro_rayuela = libros_map["Rayuela"]
    libro_ficciones = libros_map["Ficciones"]

    # 1 Rayuela ($25.000) + 2 Ficciones ($22.000 cada uno = $44.000) = $69.000,00
    total_venta = Decimal("25000.00") + (Decimal("22000.00") * 2)

    venta = Venta(
        cliente_id=cliente_lucia.id,
        usuario_id=vendedor_user.id,
        fecha=datetime.now(timezone.utc),
        total=total_venta,
    )
    session.add(venta)
    await session.flush()

    # Renglón 1: 1 Rayuela
    d1 = DetalleVenta(
        venta_id=venta.id,
        libro_id=libro_rayuela.id,
        cantidad=1,
        precio_unitario=libro_rayuela.precio,
    )
    session.add(d1)

    # Descuento de stock y movimiento de Rayuela (-1)
    libro_rayuela.stock -= 1
    session.add(libro_rayuela)

    mov1 = MovimientoStock(
        libro_id=libro_rayuela.id,
        venta_id=venta.id,
        usuario_id=vendedor_user.id,
        cantidad=-1,
        motivo="Venta",
        cuando=datetime.now(timezone.utc),
    )
    session.add(mov1)

    # Renglón 2: 2 Ficciones
    d2 = DetalleVenta(
        venta_id=venta.id,
        libro_id=libro_ficciones.id,
        cantidad=2,
        precio_unitario=libro_ficciones.precio,
    )
    session.add(d2)

    # Descuento de stock y movimiento de Ficciones (-2)
    libro_ficciones.stock -= 2
    session.add(libro_ficciones)

    mov2 = MovimientoStock(
        libro_id=libro_ficciones.id,
        venta_id=venta.id,
        usuario_id=vendedor_user.id,
        cantidad=-2,
        motivo="Venta",
        cuando=datetime.now(timezone.utc),
    )
    session.add(mov2)

    await session.flush()
    print(f"[SEED] Registrada Venta 1 (ID: {venta.id}) Total: ${venta.total} para Lucía Fernández")
    print(f"[SEED] Stock actualizado: Rayuela={libro_rayuela.stock}, Ficciones={libro_ficciones.stock}")
    return venta


async def seed_auditoria_sistema(session: AsyncSession) -> None:
    """Inserta evento de seguridad inicial con actor 'SISTEMA'."""
    stmt = select(EventoSeguridad).where(EventoSeguridad.actor == "SISTEMA")
    res = await session.execute(stmt)
    evento_existente = res.first()

    if evento_existente is None:
        evento = EventoSeguridad(
            cuando=datetime.now(timezone.utc),
            actor="SISTEMA",
            accion="Inicialización de datos de semilla (seed inicial)",
        )
        session.add(evento)
        await session.flush()
        print("[SEED] Evento de auditoría 'SISTEMA' registrado exitosamente.")
    else:
        print("[SEED] Evento de auditoría 'SISTEMA' ya presente.")


async def verificar_invariantes(session: AsyncSession) -> None:
    """Valida que para cada libro se cumpla estrictamente libro.stock == SUM(movimiento_stock.cantidad)."""
    stmt = select(Libro)
    res = await session.execute(stmt)
    libros = res.scalars().all()

    for libro in libros:
        sum_stmt = select(func.coalesce(func.sum(MovimientoStock.cantidad), 0)).where(
            MovimientoStock.libro_id == libro.id
        )
        sum_res = await session.execute(sum_stmt)
        total_movimientos = sum_res.scalar_one()

        assert libro.stock == total_movimientos, (
            f"INVARIANTE ROTO en '{libro.titulo}': stock={libro.stock} != sum_movimientos={total_movimientos}"
        )
        print(f"[INVARIANTE OK] '{libro.titulo}': Stock={libro.stock} == SUM(Movimientos)={total_movimientos}")


async def run_seed() -> None:
    """Función principal de orquestación del seed asíncrono e idempotente."""
    print("=====================================================================")
    print("INICIANDO CARGA DE DATOS INICIALES (SEED) - PARCIAL CAPÍTULOS 1 A 6")
    print("=====================================================================")

    async with async_session_factory() as session:
        async with session.begin():
            # 1. Usuarios y roles
            usuarios_map = await seed_usuarios(session)

            # 2. Catálogo y stock
            admin_user = usuarios_map["admin@example.com"]
            vendedor_user = usuarios_map["vendedor@example.com"]
            libros_map = await seed_catalogo(session, admin_user)

            # 3. Clientes
            ana_user = usuarios_map["ana@example.com"]
            clientes_map = await seed_clientes(session, ana_user)

            # 4. Venta inicial 1
            lucia_cliente = clientes_map["Lucía Fernández"]
            await seed_venta_inicial(session, lucia_cliente, vendedor_user, libros_map)

            # 5. Auditoría
            await seed_auditoria_sistema(session)

            # 6. Verificación de invariantes de stock
            await verificar_invariantes(session)

    print("=====================================================================")
    print("SEED COMPLETADO CON ÉXITO")
    print("Credenciales de prueba generadas con contraseña por defecto:")
    print(f"Password común: '{DEFAULT_PASSWORD}'")
    print("- admin@example.com    (ADMIN)")
    print("- admin2@example.com   (ADMIN)")
    print("- vendedor@example.com (VENDEDOR)")
    print("- ana@example.com      (CLIENTE)")
    print("- nuevo@example.com    (VENDEDOR - debe_cambiar_password = True)")
    print("=====================================================================")


if __name__ == "__main__":
    try:
        asyncio.run(run_seed())
    except Exception as exc:
        print(f"[ERROR SEED] Error durante la ejecución del seed: {exc}", file=sys.stderr)
        raise exc
