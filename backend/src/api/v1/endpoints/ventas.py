from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models.cliente import Cliente
from src.db.models.libro import Libro
from src.db.models.venta import Venta
from src.db.models.venta_renglon import VentaRenglon
from src.db.session import get_db
from src.schemas.venta import (
    VentaCreate,
    VentaRenglonResponse,
    VentaResponse,
)

router = APIRouter(tags=["ventas"])


def _build_venta_response(venta: Venta) -> VentaResponse:
    """Construye el esquema de respuesta oficial de una venta con sus renglones congelados."""
    renglones_res = [
        VentaRenglonResponse(
            id=r.id or 0,
            libro_id=r.libro_id,
            titulo=r.libro.titulo if getattr(r, "libro", None) else None,
            cantidad=r.cantidad,
            precio_unitario=round(float(r.precio_unitario), 2),
            subtotal=round(float(r.subtotal), 2),
        )
        for r in getattr(venta, "renglones", [])
    ]

    fecha_venta = venta.fecha if getattr(venta, "fecha", None) else datetime.now(timezone.utc)
    cliente_obj = getattr(venta, "cliente", None)

    return VentaResponse(
        id=venta.id or 0,
        cliente_id=venta.cliente_id,
        cliente_nombre=cliente_obj.nombre if cliente_obj else None,
        fecha=fecha_venta,
        total=round(float(venta.total), 2),
        renglones=renglones_res,
    )


@router.post(
    "/",
    response_model=VentaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una nueva venta transaccional",
)
async def create_venta(
    venta_in: VentaCreate,
    db: AsyncSession = Depends(get_db),
) -> VentaResponse:
    """Registra y confirma una venta de forma atómica con congelamiento de precios de catálogo."""
    # 1. Verificar existencia del cliente (RN-VEN-01)
    stmt_cli = select(Cliente).where(Cliente.id == venta_in.cliente_id)
    cliente = (await db.execute(stmt_cli)).scalar_one_or_none()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El cliente con ID {venta_in.cliente_id} no existe",
        )

    # 2. Verificar existencia de cada libro y congelar precio unitario de catálogo (RN-VEN-01, RN-VEN-05)
    renglones_model: list[VentaRenglon] = []
    total_acumulado = 0.0

    for r_in in venta_in.renglones:
        stmt_lib = select(Libro).where(Libro.id == r_in.libro_id)
        libro = (await db.execute(stmt_lib)).scalar_one_or_none()
        if not libro:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El libro con ID {r_in.libro_id} no existe",
            )

        precio_unitario = float(libro.precio)
        subtotal = round(precio_unitario * r_in.cantidad, 2)
        total_acumulado = round(total_acumulado + subtotal, 2)

        renglon = VentaRenglon(
            libro_id=libro.id,
            cantidad=r_in.cantidad,
            precio_unitario=precio_unitario,
            subtotal=subtotal,
        )
        # Asignar referencia al libro para facilitar el mapeo de respuesta
        renglon.libro = libro
        renglones_model.append(renglon)

    # 3. Persistir atómicamente la venta y sus renglones
    venta = Venta(
        cliente_id=cliente.id,
        total=total_acumulado,
        renglones=renglones_model,
    )
    venta.cliente = cliente
    db.add(venta)

    try:
        await db.commit()
        await db.refresh(venta)
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar la transacción de venta: {exc}",
        )

    # 4. Construir respuesta oficial con importes congelados (RN-VEN-06)
    return _build_venta_response(venta)


@router.get(
    "/",
    response_model=list[VentaResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar historial de ventas confirmadas con paginación",
)
async def list_ventas(
    offset: int = Query(default=0, ge=0, description="Desplazamiento inicial"),
    limit: int = Query(default=20, ge=1, le=100, description="Cantidad máxima de ventas"),
    db: AsyncSession = Depends(get_db),
) -> list[VentaResponse]:
    """Retorna el historial paginado de ventas ordenadas de la más reciente a la más antigua."""
    stmt = (
        select(Venta)
        .options(
            selectinload(Venta.cliente),
            selectinload(Venta.renglones).selectinload(VentaRenglon.libro),
        )
        .order_by(Venta.id.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    ventas = result.scalars().all()
    return [_build_venta_response(v) for v in ventas]


@router.get(
    "/{venta_id}",
    response_model=VentaResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar el detalle completo e histórico de una venta por su ID",
)
async def get_venta_detail(
    venta_id: int,
    db: AsyncSession = Depends(get_db),
) -> VentaResponse:
    """Retorna una venta confirmada con cliente, fecha, renglones congelados y total oficial."""
    stmt = (
        select(Venta)
        .options(
            selectinload(Venta.cliente),
            selectinload(Venta.renglones).selectinload(VentaRenglon.libro),
        )
        .where(Venta.id == venta_id)
    )
    venta = (await db.execute(stmt)).scalar_one_or_none()
    if venta is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Venta con ID {venta_id} no encontrada",
        )
    return _build_venta_response(venta)
