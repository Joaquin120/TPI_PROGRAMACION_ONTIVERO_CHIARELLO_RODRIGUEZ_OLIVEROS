"""Central models registry for the Parcial application."""

from parcial.app.core.base import Base
from parcial.app.modules.clientes.models import Cliente
from parcial.app.modules.libros.models import (
    Autor,
    Editorial,
    Genero,
    Libro,
    MovimientoStock,
)
from parcial.app.modules.usuarios.models import (
    AsignacionRol,
    EventoSeguridad,
    IntentoAcceso,
    Usuario,
)
from parcial.app.modules.ventas.models import DetalleVenta, Venta

__all__ = [
    "Base",
    "Usuario",
    "AsignacionRol",
    "IntentoAcceso",
    "EventoSeguridad",
    "Autor",
    "Editorial",
    "Genero",
    "Libro",
    "MovimientoStock",
    "Cliente",
    "Venta",
    "DetalleVenta",
]
