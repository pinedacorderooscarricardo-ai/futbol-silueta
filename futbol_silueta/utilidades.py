"""Funciones auxiliares compartidas por el resto del juego."""

from __future__ import annotations

import sys
from pathlib import Path

import pygame

from .configuracion import (
    CAMPO_RECT,
    PORTERIA_INFERIOR,
    PORTERIA_SUPERIOR,
    RADIO_BALON,
    Equipo,
)


def _directorio_imagenes() -> Path:
    """Ubica las imágenes en el código fuente y dentro del ejecutable."""
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", None)

        if base is None:
            base = Path(sys.executable).resolve().parent

        return Path(base) / "imagenes"

    return Path(__file__).resolve().parent.parent / "imagenes"


DIRECTORIO_IMAGENES = _directorio_imagenes()


def acotar(valor: float, minimo: float, maximo: float) -> float:
    """Limita ``valor`` al rango ``[minimo, maximo]``."""
    return min(max(valor, minimo), maximo)


def acotar_posicion(posicion: pygame.Vector2, margen: float) -> None:
    """Limita ``posicion`` al interior del campo, dejando ``margen``."""
    posicion.x = acotar(
        posicion.x,
        CAMPO_RECT.left + margen,
        CAMPO_RECT.right - margen,
    )
    posicion.y = acotar(
        posicion.y,
        CAMPO_RECT.top + margen,
        CAMPO_RECT.bottom - margen,
    )


def acotar_al_campo(
    posicion: pygame.Vector2,
    margen: float,
) -> pygame.Vector2:
    """Devuelve una copia de ``posicion`` limitada al campo."""
    copia = posicion.copy()
    acotar_posicion(copia, margen)
    return copia


def dentro_de_porteria(y: float) -> bool:
    """Indica si la coordenada ``y`` está dentro de la portería."""
    return (
        PORTERIA_SUPERIOR + RADIO_BALON
        < y
        < PORTERIA_INFERIOR - RADIO_BALON
    )


def equipo_que_anota(x: float, y: float) -> Equipo | None:
    """Equipo que anota si el balón (en x, y) toca una línea de gol."""
    if x + RADIO_BALON >= CAMPO_RECT.right and dentro_de_porteria(y):
        return Equipo.LOCAL

    if x - RADIO_BALON <= CAMPO_RECT.left and dentro_de_porteria(y):
        return Equipo.VISITANTE

    return None


def equipo_rival(equipo: Equipo) -> Equipo:
    """Devuelve el equipo contrario."""
    return Equipo.VISITANTE if equipo is Equipo.LOCAL else Equipo.LOCAL
