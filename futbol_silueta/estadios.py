"""Estadios personalizados: césped, momento, gradas y diseño de cancha.

Reúne los datos del estadio (qué césped, de día o de noche, con o sin
aficionados y el diseño de corte del campo) y las funciones de dibujo
que comparten la vista del partido y la vista previa del menú: el mismo
``Estadio`` se pinta a pantalla completa o en una miniatura.
"""

from __future__ import annotations

import math
import random
from enum import StrEnum
from typing import NamedTuple, TypeVar

import pygame

from .configuracion import Color

T = TypeVar("T")

# ============================================================
# Opciones del estadio
# ============================================================


class Cesped(StrEnum):
    """Tipos de césped de la cancha."""

    CLARO = "claro"
    OSCURO = "oscuro"
    ARTIFICIAL = "artificial"


class Momento(StrEnum):
    """Iluminación del estadio."""

    DIA = "dia"
    NOCHE = "noche"


class Diseno(StrEnum):
    """Diseños de corte del césped."""

    CLASICO = "clasico"
    RAYAS = "rayas"
    AJEDREZ = "ajedrez"
    CIRCULOS = "circulos"


class Estadio(NamedTuple):
    """Configuración completa de un estadio."""

    cesped: Cesped
    momento: Momento
    diseno: Diseno
    gradas: bool


ESTADIO_POR_DEFECTO = Estadio(
    Cesped.CLARO,
    Momento.DIA,
    Diseno.CLASICO,
    True,
)

# Orden en el que cicla cada opción con ENTER (y ←/→ en los menús).
CESPEDES: tuple[Cesped, ...] = (
    Cesped.CLARO,
    Cesped.OSCURO,
    Cesped.ARTIFICIAL,
)
MOMENTOS: tuple[Momento, ...] = (Momento.DIA, Momento.NOCHE)
DISENOS: tuple[Diseno, ...] = (
    Diseno.CLASICO,
    Diseno.RAYAS,
    Diseno.AJEDREZ,
    Diseno.CIRCULOS,
)

# Nombres con acentos para las etiquetas de los menús; el césped usa
# ``value.upper()`` porque no lleva ninguno.
NOMBRES_MOMENTO: dict[Momento, str] = {
    Momento.DIA: "DÍA",
    Momento.NOCHE: "NOCHE",
}
NOMBRES_DISENO: dict[Diseno, str] = {
    Diseno.CLASICO: "CLÁSICO",
    Diseno.RAYAS: "RAYAS",
    Diseno.AJEDREZ: "AJEDREZ",
    Diseno.CIRCULOS: "CÍRCULOS",
}


def siguiente_opcion(opciones: tuple[T, ...], actual: T) -> T:
    """La opción siguiente a ``actual``, dando la vuelta a la lista."""
    return opciones[(opciones.index(actual) + 1) % len(opciones)]


# ============================================================
# Colores
# ============================================================

# (base, alterno) de cada césped a plena luz del día; de noche ambos
# se atenúan. El artificial, más uniforme y teñido de azul.
CESPEDES_COLORES: dict[Cesped, tuple[Color, Color]] = {
    Cesped.CLARO: ((92, 164, 92), (82, 154, 82)),
    Cesped.OSCURO: ((36, 108, 44), (31, 98, 39)),
    Cesped.ARTIFICIAL: ((60, 156, 128), (55, 148, 121)),
}

FACTOR_NOCHE = 0.55
# La tribuna y el cordón exterior cuando no hay gradas.
COLOR_TRIBUNA: dict[Momento, Color] = {
    Momento.DIA: (44, 50, 60),
    Momento.NOCHE: (16, 18, 26),
}

COLORES_AFICIONADOS: tuple[Color, ...] = (
    (225, 225, 225),
    (60, 60, 65),
    (196, 60, 60),
    (60, 110, 196),
    (230, 200, 60),
    (90, 160, 90),
    (150, 90, 170),
    (230, 140, 50),
)


def atenuar(color: Color, factor: float) -> Color:
    """Oscurece un color multiplicando sus canales."""
    return tuple(int(valor * factor) for valor in color)


def colores_cesped(cesped: Cesped, momento: Momento) -> tuple[Color, Color]:
    """Par (base, alterno) del césped, con la luz del momento."""
    base, alterno = CESPEDES_COLORES[cesped]

    if momento is Momento.NOCHE:
        return atenuar(base, FACTOR_NOCHE), atenuar(alterno, FACTOR_NOCHE)

    return base, alterno


def color_tribuna(momento: Momento) -> Color:
    """Color del graderío donde se sienta el público."""
    return COLOR_TRIBUNA[momento]


def color_entorno(estadio: Estadio) -> Color:
    """Cordón exterior de césped cuando el estadio va sin gradas."""
    base, _alterno = colores_cesped(estadio.cesped, estadio.momento)
    factor = 0.75 if estadio.momento is Momento.DIA else 0.40
    return atenuar(base, factor)


# Semilla fija: el público se ve igual en cada redibujado del estadio.
SEMILLA_AFICIONADOS = 9


def dibujar_cesped(superficie: pygame.Surface, estadio: Estadio) -> None:
    """Pinta el césped con el diseño elegido en toda la superficie."""
    base, alterno = colores_cesped(estadio.cesped, estadio.momento)
    ancho, alto = superficie.get_size()
    superficie.fill(base)

    if estadio.diseno is Diseno.RAYAS:
        banda = max(20, ancho // 10)
        for x in range(0, ancho, banda * 2):
            pygame.draw.rect(superficie, alterno, (x, 0, banda, alto))
    elif estadio.diseno is Diseno.AJEDREZ:
        lado = max(20, alto // 8)
        for fila, y in enumerate(range(0, alto, lado)):
            for columna, x in enumerate(range(0, ancho, lado)):
                if (fila + columna) % 2:
                    pygame.draw.rect(
                        superficie,
                        alterno,
                        (x, y, lado, lado),
                    )
    elif estadio.diseno is Diseno.CIRCULOS:
        centro = (ancho // 2, alto // 2)
        grosor = max(18, min(ancho, alto) // 12)
        anillos = math.hypot(ancho, alto) // (2 * grosor) + 2

        for indice in range(1, int(anillos) + 1, 2):
            pygame.draw.circle(
                superficie,
                alterno,
                centro,
                indice * grosor,
                grosor,
            )


def dibujar_aficionados(
    superficie: pygame.Surface,
    momento: Momento,
) -> None:
    """Pinta el público sobre todo el entorno de la superficie.

    Se estampa antes de la cancha: los puntos que caen dentro quedan
    tapados. La semilla fija hace que la multitud sea siempre la misma.
    """
    aleatorio = random.Random(SEMILLA_AFICIONADOS)
    ancho, alto = superficie.get_size()
    paso = 11 if ancho > 600 else 9
    radio = 3 if ancho > 600 else 2
    factor = 1.0 if momento is Momento.DIA else FACTOR_NOCHE

    for y in range(radio + 2, alto - radio, paso):
        for x in range(radio + 2, ancho - radio, paso):
            if aleatorio.random() < 0.18:
                continue  # Huecos: el público no forma una retícula.

            color = COLORES_AFICIONADOS[
                aleatorio.randrange(len(COLORES_AFICIONADOS))
            ]
            pygame.draw.circle(
                superficie,
                atenuar(color, factor),
                (
                    x + aleatorio.randint(-2, 2),
                    y + aleatorio.randint(-2, 2),
                ),
                radio,
            )
