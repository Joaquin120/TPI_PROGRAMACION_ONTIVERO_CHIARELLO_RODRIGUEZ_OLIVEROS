"""Business service layer for customer management."""

from collections.abc import Sequence
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from parcial.app.core.paginacion import (
    PaginatedResponse,
    PaginationParams,
    crear_respuesta_paginada,
)
from parcial.app.core.unit_of_work import UnitOfWork
from parcial.app.modules.clientes.models import Cliente
from parcial.app.modules.clientes.repository import ClienteRepository
from parcial.app.modules.clientes.schemas import (
    ClienteCreateRequest,
    ClienteResponse,
    ClienteUpdateRequest,
)
from parcial.app.modules.ventas.models import Venta
from parcial.app.modules.ventas.repository import VentaRepository
from parcial.app.modules.ventas.schemas import VentaResponse


class ClienteService:
    """Service encapsulating customer operations under Unit of Work."""

    async def crear_cliente(
        self,
        datos: ClienteCreateRequest,
        uow: UnitOfWork,
        repo: ClienteRepository | None = None,
    ) -> ClienteResponse:
        """Creates a new customer verifying email uniqueness."""
        cliente_repo = repo or ClienteRepository(uow.session)
        existente = await cliente_repo.obtener_por_email(datos.email)
        if existente is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un cliente registrado con el email '{datos.email}'",
            )

        cliente = Cliente(
            nombre=datos.nombre,
            email=datos.email,
            telefono=datos.telefono,
            direccion=datos.direccion,
        )
        await cliente_repo.add(cliente)
        return ClienteResponse.model_validate(cliente)

    async def obtener_cliente_por_id(
        self,
        cliente_id: int,
        uow: UnitOfWork,
        repo: ClienteRepository | None = None,
    ) -> ClienteResponse:
        """Fetches a customer by ID or raises 404."""
        cliente_repo = repo or ClienteRepository(uow.session)
        cliente = await cliente_repo.get_by_id(cliente_id)
        if cliente is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente #{cliente_id} no encontrado",
            )
        return ClienteResponse.model_validate(cliente)

    async def actualizar_cliente(
        self,
        cliente_id: int,
        datos: ClienteUpdateRequest,
        uow: UnitOfWork,
        repo: ClienteRepository | None = None,
    ) -> ClienteResponse:
        """Applies partial updates to a customer record."""
        cliente_repo = repo or ClienteRepository(uow.session)
        cliente = await cliente_repo.get_by_id(cliente_id)
        if cliente is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente #{cliente_id} no encontrado",
            )

        valores = datos.model_dump(exclude_unset=True)
        if "email" in valores and valores["email"] != cliente.email:
            existente = await cliente_repo.obtener_por_email(valores["email"])
            if existente is not None and existente.id != cliente_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ya existe otro cliente con el email '{valores['email']}'",
                )

        for campo, valor in valores.items():
            setattr(cliente, campo, valor)

        await cliente_repo.update(cliente)
        return ClienteResponse.model_validate(cliente)

    async def vincular_perfil(
        self,
        cliente_id: int,
        usuario_id: int,
        uow: UnitOfWork,
        repo: ClienteRepository | None = None,
    ) -> ClienteResponse:
        """Binds an authenticated user account to an existing customer record (1-to-1)."""
        cliente_repo = repo or ClienteRepository(uow.session)
        cliente = await cliente_repo.get_by_id(cliente_id)
        if cliente is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente #{cliente_id} no encontrado",
            )

        if cliente.usuario_id is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El cliente #{cliente_id} ya se encuentra vinculado a una cuenta de usuario",
            )

        cliente_previo = await cliente_repo.obtener_por_usuario_id(usuario_id)
        if cliente_previo is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El usuario ya posee una ficha de cliente asignada",
            )

        cliente.usuario_id = usuario_id
        await cliente_repo.update(cliente)
        return ClienteResponse.model_validate(cliente)

    async def listar_clientes_paginado(
        self,
        params: PaginationParams,
        uow: UnitOfWork,
        repo: ClienteRepository | None = None,
    ) -> PaginatedResponse[ClienteResponse]:
        """Returns paginated customer list."""
        cliente_repo = repo or ClienteRepository(uow.session)
        total = await cliente_repo.contar_total()
        skip = (params.page - 1) * params.size
        clientes = await cliente_repo.listar_paginado(skip=skip, limit=params.size)
        items = [ClienteResponse.model_validate(c) for c in clientes]
        return crear_respuesta_paginada(items=items, total=total, page=params.page, size=params.size)

    async def listar_ventas_cliente_paginado(
        self,
        cliente_id: int,
        params: PaginationParams,
        uow: UnitOfWork,
        cliente_repo: ClienteRepository | None = None,
        venta_repo: VentaRepository | None = None,
    ) -> PaginatedResponse[VentaResponse]:
        """Returns paginated sales history for a specific customer."""
        c_repo = cliente_repo or ClienteRepository(uow.session)
        cliente = await c_repo.get_by_id(cliente_id)
        if cliente is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente #{cliente_id} no encontrado",
            )

        v_repo = venta_repo or VentaRepository(uow.session)
        total = await v_repo.contar_por_cliente(cliente_id)
        skip = (params.page - 1) * params.size
        ventas = await v_repo.listar_por_cliente_paginado(cliente_id, skip=skip, limit=params.size)
        items = [VentaResponse.model_validate(v) for v in ventas]
        return crear_respuesta_paginada(items=items, total=total, page=params.page, size=params.size)
