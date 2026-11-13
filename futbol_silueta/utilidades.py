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
    Color,
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

# Tamaño del cuadro de reserva cuando falta un archivo gráfico.
RESERVA_TAMANO = 256


def cargar_imagen(ruta: Path) -> pygame.Surface:
    """Carga una imagen; si falta o está dañada, devuelve una reserva.

    La reserva (un cuadro oscuro con borde rojo) mantiene el juego
    funcionando y la suite en pie aunque falte algún asset, en lugar de
    abortar con una excepción al arrancar. La conversión al formato de
    pantalla es opcional: sin un modo de vídeo activo se devuelve la
    imagen tal cual, para que herramientas y pruebas puedan cargarla.
    """
    try:
        imagen = pygame.image.load(ruta)
    except (pygame.error, OSError, TypeError):
        print(f"Aviso: no se pudo cargar {ruta}; se usa una reserva.",
              file=sys.stderr)
        reserva = pygame.Surface((RESERVA_TAMANO, RESERVA_TAMANO))
        reserva.fill((30, 32, 40))
        pygame.draw.rect(reserva, (200, 60, 60), reserva.get_rect(), 6)
        return reserva

    if pygame.display.get_surface() is not None:
        try:
            return imagen.convert()
        except pygame.error:
            # Sin formato de pantalla disponible se conserva la original.
            pass

    return imagen


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


class CacheTextos:
    """Caché de textos renderizados compartida por las pantallas.

    La clave incluye ``id(fuente)`` porque la identidad de la fuente basta
    para distinguir tamaños y estilos durante una misma sesión de pygame.
    """

    def __init__(self) -> None:
        self._superficies: dict[
            tuple[str, int, Color],
            pygame.Surface,
        ] = {}

    def __call__(
        self,
        texto: str,
        fuente: pygame.font.Font,
        color: Color,
    ) -> pygame.Surface:
        clave = (texto, id(fuente), color)
        superficie = self._superficies.get(clave)

        if superficie is None:
            superficie = fuente.render(texto, True, color)
            self._superficies[clave] = superficie

        return superficie
