"""Escudos: imágenes por nivel y personalización de colores y formas."""

from __future__ import annotations

from enum import StrEnum

import pygame

from .configuracion import Color
from .utilidades import DIRECTORIO_IMAGENES


def nombre_archivo_escudo(nivel: int) -> str:
    """Devuelve el archivo de escudo de un nivel: ``escudo_01.jpeg``..."""
    return f"escudo_{nivel:02d}.jpeg"


_IMAGENES: dict[int, pygame.Surface] = {}


def cargar_escudo(nivel: int) -> pygame.Surface:
    """Carga la imagen del escudo de un nivel y la cachea por nivel."""
    superficie = _IMAGENES.get(nivel)

    if superficie is None:
        ruta = DIRECTORIO_IMAGENES / "escudos" / nombre_archivo_escudo(nivel)
        superficie = pygame.image.load(ruta).convert()
        _IMAGENES[nivel] = superficie

    return superficie


class FormaEscudo(StrEnum):
    """Formas entre las que puede elegir el escudo del jugador."""

    CLASICA = "Clásica"
    REDONDA = "Redonda"
    ROMBO = "Rombo"


FORMAS_ESCUDO: tuple[FormaEscudo, ...] = (
    FormaEscudo.CLASICA,
    FormaEscudo.REDONDA,
    FormaEscudo.ROMBO,
)


class Escudo:
    """Escudo del jugador durante un nivel de la campaña.

    Cada nivel tiene su propio diseño (color y grosor de borde); el
    jugador puede personalizar el color, el borde y la forma desde el
    menú antes de jugar.
    """

    TAMANO = 16  # Radio vertical del escudo, en píxeles.

    _PUNTOS: tuple[tuple[float, float], ...] = (
        (0.0, -16.0),
        (7.0, -6.0),
        (16.0, 0.0),
        (7.0, 6.0),
        (0.0, 16.0),
        (-7.0, 6.0),
        (-16.0, 0.0),
        (-7.0, -6.0),
    )

    _PUNTOS_ROMBO: tuple[tuple[float, float], ...] = (
        (0.0, -16.0),
        (16.0, 0.0),
        (0.0, 16.0),
        (-16.0, 0.0),
    )

    def __init__(
        self,
        nivel: int,
        color: Color,
        color_borde: Color,
        forma: FormaEscudo = FormaEscudo.CLASICA,
    ) -> None:
        self.nivel = nivel
        self.color = color
        self.color_borde = color_borde
        self.forma = forma

    @classmethod
    def crear_para_nivel(
        cls,
        nivel: int,
        color: Color | None = None,
        color_borde: Color | None = None,
        forma: FormaEscudo | None = None,
    ) -> Escudo:
        """Crea el escudo de un nivel, con su color y borde base."""
        diseno = COLORES_ESCUDO_POR_NIVEL.get(
            nivel,
            COLORES_ESCUDO_POR_NIVEL[1],
        )

        return cls(
            nivel=nivel,
            color=color if color is not None else diseno[0],
            color_borde=color_borde if color_borde is not None else diseno[1],
            forma=forma if forma is not None else FormaEscudo.CLASICA,
        )

    def cambiar_colores(self, color: Color, color_borde: Color) -> None:
        """Personaliza los colores del escudo del jugador."""
        self.color = color
        self.color_borde = color_borde

    def cambiar_forma(self, forma: FormaEscudo) -> None:
        """Personaliza la forma del escudo del jugador."""
        self.forma = forma

    def dibujar(
        self,
        superficie: pygame.Surface,
        centro: tuple[float, float],
        escala: float = 1.0,
    ) -> None:
        """Dibuja el escudo en ``centro``, con su grosor según el nivel."""
        grosor = min(1 + self.nivel, 5)

        if self.forma is FormaEscudo.REDONDA:
            radio = round(self.TAMANO * escala)
            pygame.draw.circle(superficie, self.color, centro, radio)
            pygame.draw.circle(
                superficie,
                self.color_borde,
                centro,
                radio,
                grosor,
            )
            return

        plantilla = (
            self._PUNTOS_ROMBO
            if self.forma is FormaEscudo.ROMBO
            else self._PUNTOS
        )
        puntos = [
            (centro[0] + x * escala, centro[1] + y * escala)
            for x, y in plantilla
        ]

        pygame.draw.polygon(superficie, self.color, puntos)
        pygame.draw.polygon(superficie, self.color_borde, puntos, grosor)


# Colores y detalles del escudo de cada nivel de la campaña.
COLORES_ESCUDO_POR_NIVEL: dict[int, tuple[Color, Color]] = {
    1: ((34, 139, 34), (255, 255, 255)),     # Club Aurora
    2: ((40, 80, 200), (255, 255, 255)),     # Pasión Fútbol
    3: ((255, 205, 50), (20, 20, 20)),       # U. D. Prisma
    4: ((150, 60, 200), (255, 255, 255)),    # Atlético Corona
    5: ((215, 65, 45), (255, 255, 255)),     # Real Laurel
    6: ((255, 125, 30), (20, 20, 20)),       # Deportivo Trueno
    7: ((20, 105, 105), (255, 255, 255)),    # Club Titán
    8: ((212, 175, 55), (20, 20, 20)),       # Imperial Oro
    9: ((120, 30, 60), (255, 255, 255)),     # Furia FC
    10: ((30, 30, 30), (255, 215, 0)),       # Real Leyenda
    11: ((70, 70, 85), (255, 255, 255)),     # Campeón Eterno
}

# Personalizaciones de escudo que el jugador puede elegir en el menú.
ESCUDO_PRESETS: tuple[tuple[str, Color, Color], ...] = (
    ("Verde", (34, 139, 34), (255, 255, 255)),
    ("Azul", (40, 80, 200), (255, 255, 255)),
    ("Rojo", (200, 40, 40), (255, 255, 255)),
    ("Amarillo", (255, 205, 50), (20, 20, 20)),
    ("Naranja", (255, 125, 30), (255, 255, 255)),
    ("Rosa", (230, 60, 150), (255, 255, 255)),
)
