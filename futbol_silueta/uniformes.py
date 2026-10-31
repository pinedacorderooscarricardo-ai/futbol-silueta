"""Uniformes: colores de camiseta, pantalón y medias, y dorsales."""

from __future__ import annotations

from typing import NamedTuple

import pygame

from .configuracion import BLANCO, NEGRO, RADIO_JUGADOR, Color, Equipo


class Uniforme(NamedTuple):
    """Equipación de un equipo: camiseta, pantalón y medias."""

    camiseta: Color
    pantalon: Color
    medias: Color


# Equipaciones iniciales: el local viste de rojo y el visitante de azul.
UNIFORMES_POR_DEFECTO: dict[Equipo, Uniforme] = {
    Equipo.LOCAL: Uniforme((200, 40, 40), (245, 245, 245), (200, 40, 40)),
    Equipo.VISITANTE: Uniforme((40, 80, 200), (245, 245, 245), (40, 80, 200)),
}

# Colores que el jugador puede asignar a cada prenda en el menú.
UNIFORME_PRESETS: tuple[tuple[str, Color], ...] = (
    ("Blanco", (245, 245, 245)),
    ("Negro", (30, 30, 35)),
    ("Rojo", (200, 40, 40)),
    ("Azul", (40, 80, 200)),
    ("Verde", (34, 139, 34)),
    ("Amarillo", (255, 205, 50)),
    ("Naranja", (255, 125, 30)),
    ("Rosa", (230, 60, 150)),
    ("Celeste", (120, 190, 240)),
    ("Granate", (120, 30, 60)),
)

_FUENTES_DORSAL: dict[int, pygame.font.Font] = {}


def _fuente_dorsal(tamano: int) -> pygame.font.Font:
    """Fuente para dorsales, creada una vez por tamaño."""
    fuente = _FUENTES_DORSAL.get(tamano)

    if fuente is None:
        fuente = pygame.font.SysFont("Arial", tamano, bold=True)
        _FUENTES_DORSAL[tamano] = fuente

    return fuente


def _superficie_dorsal(
    texto: str,
    tamano: int,
    color: Color,
) -> pygame.Surface:
    """Renderiza el dorsal; si pygame.font se reinició, recrea la fuente.

    La caché vive a nivel de módulo: si ``pygame.quit`` y una nueva
    inicialización ocurren en la misma sesión (por ejemplo entre pruebas),
    las fuentes guardadas quedan inválidas y hay que regenerarlas.
    """
    try:
        return _fuente_dorsal(tamano).render(texto, True, color)
    except pygame.error:
        _FUENTES_DORSAL.clear()
        return _fuente_dorsal(tamano).render(texto, True, color)


def _color_dorsal(camiseta: Color) -> Color:
    """Blanco o negro: el que más contraste con la camiseta."""
    brillo = (
        0.299 * camiseta[0]
        + 0.587 * camiseta[1]
        + 0.114 * camiseta[2]
    )
    return NEGRO if brillo > 140.0 else BLANCO


def dibujar_jugador_uniforme(
    superficie: pygame.Surface,
    centro: tuple[float, float],
    uniforme: Uniforme,
    escala: float = 1.0,
    numero: int | None = None,
) -> None:
    """Dibuja la figura de un jugador con su equipación.

    La camiseta es el cuerpo circular (el radio de juego), el pantalón
    una franja en su parte baja y las medias dos pies asomando debajo;
    el dorsal, si se pide, va centrado en la camiseta. La usan el sprite
    del partido y la vista previa del menú.
    """
    cx, cy = centro
    radio = RADIO_JUGADOR * escala

    # Medias: un pie a cada lado, asomando bajo la camiseta.
    radio_pie = radio * 0.30
    for lado in (-1.0, 1.0):
        pygame.draw.circle(
            superficie,
            uniforme.medias,
            (cx + lado * radio * 0.45, cy + radio * 1.18),
            radio_pie,
        )

    # Camiseta con su contorno, como el clásico círculo del partido.
    pygame.draw.circle(superficie, uniforme.camiseta, (cx, cy), radio)

    # Pantalón: franja inferior que queda dentro de la camiseta.
    pygame.draw.rect(
        superficie,
        uniforme.pantalon,
        (
            cx - radio * 0.66,
            cy + radio * 0.18,
            radio * 1.32,
            radio * 0.52,
        ),
    )
    pygame.draw.circle(superficie, BLANCO, (cx, cy), radio, 2)

    if numero is not None:
        dorsal = _superficie_dorsal(
            str(numero),
            round(radio * 0.8),
            _color_dorsal(uniforme.camiseta),
        )
        superficie.blit(
            dorsal,
            dorsal.get_rect(center=(cx, cy - radio * 0.3)),
        )
