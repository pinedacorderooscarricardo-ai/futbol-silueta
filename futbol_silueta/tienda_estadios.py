"""Catálogo de estadios que se compran con las monedas del entrenamiento.

Cada artículo guarda un identificador estable (el que se escribe en la
base de datos), su precio y la configuración visual que se aplica al
equiparlo. El estadio municipal es gratuito y siempre está disponible;
el resto se desbloquea en la tienda.
"""

from __future__ import annotations

from typing import NamedTuple

from .estadios import (
    ESTADIO_POR_DEFECTO,
    Cesped,
    Clima,
    Diseno,
    Estadio,
    Momento,
)

ESTADIO_GRATIS = "municipal"


class ArticuloEstadio(NamedTuple):
    """Un estadio a la venta en la tienda."""

    id: str
    nombre: str
    descripcion: str
    precio: int
    estadio: Estadio


CATALOGO_ESTADIOS: tuple[ArticuloEstadio, ...] = (
    ArticuloEstadio(
        ESTADIO_GRATIS,
        "Estadio Municipal",
        "El recinto de siempre: césped claro, de día y con público.",
        0,
        ESTADIO_POR_DEFECTO,
    ),
    ArticuloEstadio(
        "amanecer",
        "Amanecer Dorado",
        "Césped a rayas y una grada que despierta con el sol.",
        250,
        Estadio(Cesped.CLARO, Momento.DIA, Diseno.RAYAS, True),
    ),
    ArticuloEstadio(
        "nocturno",
        "Coliseo Nocturno",
        "Noche cerrada, césped oscuro y un tablero de ajedrez.",
        600,
        Estadio(Cesped.OSCURO, Momento.NOCHE, Diseno.AJEDREZ, True),
    ),
    ArticuloEstadio(
        "cristal",
        "Arena de Cristal",
        "Césped artificial y círculos concéntricos de gala.",
        900,
        Estadio(Cesped.ARTIFICIAL, Momento.DIA, Diseno.CIRCULOS, True),
    ),
    ArticuloEstadio(
        "invierno",
        "Fortaleza Invernal",
        "Un estadio de noche con nieve y líneas bien marcadas.",
        1200,
        Estadio(
            Cesped.OSCURO,
            Momento.NOCHE,
            Diseno.RAYAS,
            True,
            Clima.NIEVE,
        ),
    ),
    ArticuloEstadio(
        "tormenta",
        "Estadio Tormenta",
        "Lluvia, viento y un césped artificial que brilla bajo los focos.",
        1600,
        Estadio(
            Cesped.ARTIFICIAL,
            Momento.NOCHE,
            Diseno.CIRCULOS,
            True,
            Clima.LLUVIA,
        ),
    ),
)


def articulo_por_id(identificador: str) -> ArticuloEstadio | None:
    """El artículo del catálogo con ese id, o None si no existe."""
    for articulo in CATALOGO_ESTADIOS:
        if articulo.id == identificador:
            return articulo

    return None


def ids_validos() -> frozenset[str]:
    """Identificadores que la tienda reconoce."""
    return frozenset(articulo.id for articulo in CATALOGO_ESTADIOS)
