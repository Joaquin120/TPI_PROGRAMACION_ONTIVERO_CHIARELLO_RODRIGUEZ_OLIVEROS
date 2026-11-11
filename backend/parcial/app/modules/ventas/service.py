"""Business service layer for sales transactions and atomic stock management."""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
import logging
from fastapi import HTTPException, status

from parcial.app.core.paginacion import (
    PaginatedResponse,
    PaginationParams,
    crear_respuesta_paginada,
)
from parcial.app.core.unit_of_work import UnitOfWork
from parcial.app.modules.clientes.models import Cliente
from parcial.app.modules.clientes.repository import ClienteRepository
from parcial.app.modules.libros.models import Libro, MovimientoStock
from parcial.app.modules.libros.repository import LibroRepository
from parcial.app.modules.usuarios.models import Usuario
from parcial.app.modules.ventas.models import DetalleVenta, Venta
from parcial.app.modules.ventas.repository import VentaRepository
from parcial.app.modules.ventas.schemas import (
    VentaCreateRequest,
    VentaDetailResponse,
    VentaResponse,
)

logger = logging.getLogger(__name__)


async def simular_notificacion_comprobante(
    venta_id: int,
    total: float,
    email_destinatario: str,
) -> None:
    """Simulates sending a receipt in the background after sale commit.

    Crucial Architectural Rule (CONSIGNA_PARCIAL §3.3):
    - Runs exclusively via BackgroundTasks after successful commit.
    - Simulates dispatch with non-blocking await asyncio.sleep(0.5).
    """
    await asyncio.sleep(0.5)
    logger.info(
        "Aviso de comprobante emitido: Venta #%d por $%.2f enviada a %s",
        venta_id,
        total,
        email_destinatario,
    )


class VentaService:
    """Service encapsulating atomic sales transactions under Unit of Work."""

    async def crear_venta(
        self,
        datos: VentaCreateRequest,
        usuario_id: int,
        uow: UnitOfWork,
        venta_repo: VentaRepository | None = None,
        cliente_repo: ClienteRepository | None = None,
        libro_repo: LibroRepository | None = None,
    ) -> VentaDetailResponse:
        """Records an atomic sale transaction, deducting stock and registering audit movements.

        Crucial Architectural Rules (CONSIGNA_PARCIAL §1.1, §3.3):
        - Runs within a single Unit of Work boundary.
        - Checks sufficient stock and active status (borrado_en IS NULL) on each book.
        - Any failure or deficit rolls back the entire transaction and answers HTTP 409 Conflict.
        - Unit prices are copied directly from the catalog database record and total is computed server-side.
        - Creates negative MovimientoStock with motivo='Venta'.
        """
        v_repo = venta_repo or VentaRepository(uow.session)
        c_repo = cliente_repo or ClienteRepository(uow.session)
        l_repo = libro_repo or LibroRepository(uow.session)

        # 1. Verify customer exists
        cliente = await c_repo.get_by_id(datos.cliente_id)
        if cliente is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente #{datos.cliente_id} no encontrado",
            )

        # 2. Consolidate requested quantities per book ID
        cantidades_solicitadas: dict[int, int] = {}
        for item in datos.items:
            cantidades_solicitadas[item.libro_id] = (
                cantidades_solicitadas.get(item.libro_id, 0) + item.cantidad
            )

        # 3. Validate each book and check available inventory
        libros_map: dict[int, Libro] = {}
        for libro_id, cant_total in cantidades_solicitadas.items():
            libro = await l_repo.get_by_id(libro_id)
            if libro is None or libro.borrado_en is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"El libro #{libro_id} se encuentra dado de baja o no existe en el catálogo",
                )
            if libro.stock < cant_total:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Stock insuficiente para el libro '{libro.titulo}'. "
                        f"Stock disponible: {libro.stock}, cantidad solicitada: {cant_total}"
                    ),
                )
            libros_map[libro_id] = libro

        # 4. Calculate total with server-side catalog prices and deduct stock
        total = Decimal("0.00")
        lineas: list[tuple[Libro, int, Decimal]] = []
        for item in datos.items:
            libro = libros_map[item.libro_id]
            precio_unitario = libro.precio
            subtotal = precio_unitario * Decimal(item.cantidad)
            total += subtotal
            lineas.append((libro, item.cantidad, precio_unitario))
            libro.stock -= item.cantidad
            await l_repo.update(libro)

        # 5. Persist Sale Header
        venta = Venta(
            cliente_id=datos.cliente_id,
            usuario_id=usuario_id,
            total=total,
            fecha=datetime.now(timezone.utc),
        )
        await v_repo.add(venta)

        # 6. Persist DetalleVenta and negative append-only MovimientoStock
        for libro, cantidad, precio_unitario in lineas:
            detalle = DetalleVenta(
                venta_id=venta.id,
                libro_id=libro.id,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
            )
            uow.session.add(detalle)

            movimiento = MovimientoStock(
                libro_id=libro.id,
                venta_id=venta.id,
                usuario_id=usuario_id,
                cantidad=-cantidad,
                motivo="Venta",
            )
            uow.session.add(movimiento)

        await uow.session.flush()

        # 7. Reload with eager loading to resolve response without N+1 queries
        venta_cargada = await v_repo.obtener_por_id_con_detalles(venta.id)
        if venta_cargada is None:
            venta_cargada = venta
        return VentaDetailResponse.model_validate(venta_cargada)

    async def obtener_venta_por_id(
        self,
        venta_id: int,
        usuario_actual: Usuario,
        uow: UnitOfWork,
        venta_repo: VentaRepository | None = None,
    ) -> VentaDetailResponse:
        """Fetches sale details with dynamic ownership/role authorization.

        Crucial Architectural Rules (CONSIGNA_PARCIAL §2.6, §3.5):
        - No static role dependency on the router.
        - Staff (ADMIN/VENDEDOR) or the owning customer can access (HTTP 200).
        - Any foreign customer is denied with HTTP 403 Forbidden.
        - Relations loaded with joinedload/selectinload avoiding N+1 queries.
        - Avoids MissingGreenlet by reading in-memory roles dict or querying UsuarioRepository.
        """
        v_repo = venta_repo or VentaRepository(uow.session)
        venta = await v_repo.obtener_por_id_con_detalles(venta_id)
        if venta is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Venta #{venta_id} no encontrada",
            )

        # Resolve live roles: check in-memory dictionary first (unit tests/preloaded), else query repository
        roles_vigentes: set[str] = set()
        ahora = datetime.now(timezone.utc)
        if "roles" in usuario_actual.__dict__:
            for r in getattr(usuario_actual, "roles", []):
                revocada_en = getattr(r, "revocada_en", None)
                vence_en = getattr(r, "vence_en", None)
                es_valido = (revocada_en is None) and (vence_en is None or vence_en > ahora)
                if es_valido:
                    roles_vigentes.add(getattr(r, "rol", ""))
        else:
            from parcial.app.modules.usuarios.repository import UsuarioRepository
            roles_repo = UsuarioRepository(uow.session)
            roles_vigentes = set(await roles_repo.get_roles_vigentes(usuario_actual.id))

        es_personal = bool(roles_vigentes & {"ADMIN", "VENDEDOR"})
        es_titular = bool(venta.cliente and venta.cliente.usuario_id == usuario_actual.id)

        if not (es_personal or es_titular):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado a la venta solicitada",
            )

        return VentaDetailResponse.model_validate(venta)

    async def listar_ventas_paginado(
        self,
        params: PaginationParams,
        uow: UnitOfWork,
        venta_repo: VentaRepository | None = None,
    ) -> PaginatedResponse[VentaResponse]:
        """Returns paginated sales list for store staff."""
        v_repo = venta_repo or VentaRepository(uow.session)
        total = await v_repo.contar_total()
        skip = (params.page - 1) * params.size
        ventas = await v_repo.listar_paginado(skip=skip, limit=params.size)
        items = [VentaResponse.model_validate(v) for v in ventas]
        return crear_respuesta_paginada(items=items, total=total, page=params.page, size=params.size)

    async def listar_mis_ventas(
        self,
        usuario_actual: Usuario,
        params: PaginationParams,
        uow: UnitOfWork,
        cliente_repo: ClienteRepository | None = None,
        venta_repo: VentaRepository | None = None,
    ) -> PaginatedResponse[VentaResponse]:
        """Returns paginated purchases made by the authenticated customer."""
        c_repo = cliente_repo or ClienteRepository(uow.session)
        cliente = await c_repo.obtener_por_usuario_id(usuario_actual.id)
        if cliente is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El usuario autenticado no tiene una ficha de cliente asociada",
            )

        v_repo = venta_repo or VentaRepository(uow.session)
        total = await v_repo.contar_por_cliente(cliente.id)
        skip = (params.page - 1) * params.size
        ventas = await v_repo.listar_por_cliente_paginado(cliente.id, skip=skip, limit=params.size)
        items = [VentaResponse.model_validate(v) for v in ventas]
        return crear_respuesta_paginada(items=items, total=total, page=params.page, size=params.size)
