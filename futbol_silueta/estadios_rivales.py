"""Estadios rivales: los recintos de la campaña y su galería de fotos.

Cada nivel de la campaña tiene un estadio con nombre propio y una o
varias vistas fotográficas en ``imagenes/estadios``. El módulo reúne los
datos y las funciones de carga y escalado que comparten la presentación
previa al partido y la galería de **Opciones → Estadio**.
"""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import NamedTuple

import pygame

from .niveles import NIVEL_MAXIMO, nivel_por_numero
from .utilidades import DIRECTORIO_IMAGENES, acotar, cargar_imagen


class Vista(NamedTuple):
    """Una foto del estadio y su etiqueta para la galería."""

    archivo: str
    etiqueta: str


class EstadioRival(NamedTuple):
    """Estadio que recibe al jugador en un nivel de la campaña."""

    nivel: int
    nombre: str
    vistas: tuple[Vista, ...]

    @property
    def club(self) -> str:
        """Nombre del club rival que juega en este estadio."""
        return nivel_por_numero(self.nivel).rival


# Un estadio por nivel, en el mismo orden que los escudos rivales. Las
# fotos viven en ``imagenes/estadios/nivel_NN_*.jpeg``.
ESTADIOS_RIVALES: tuple[EstadioRival, ...] = (
    EstadioRival(
        1,
        "Royal Star Arena",
        (
            Vista("nivel_01_exterior.jpeg", "Exterior"),
            Vista("nivel_01_interior.jpeg", "Interior"),
            Vista("nivel_01_acceso.jpeg", "Acceso"),
        ),
    ),
    EstadioRival(
        2,
        "El Coliseo de la Pasión Latina",
        (
            Vista("nivel_02_exterior.jpeg", "Exterior"),
            Vista("nivel_02_acceso.jpeg", "Acceso"),
        ),
    ),
    EstadioRival(
        3,
        "Estadio Prismático",
        (
            Vista("nivel_03_exterior.jpeg", "Exterior"),
            Vista("nivel_03_interior.jpeg", "Interior"),
            Vista("nivel_03_acceso.jpeg", "Acceso"),
        ),
    ),
    EstadioRival(
        4,
        "Stadion Adler",
        (
            Vista("nivel_04_exterior.jpeg", "Exterior"),
            Vista("nivel_04_interior.jpeg", "Interior"),
        ),
    ),
    EstadioRival(
        5,
        "Estadio Corona de Oro",
        (Vista("nivel_05_exterior.jpeg", "Exterior"),),
    ),
    EstadioRival(
        6,
        "Stadio Forza 10 Italia",
        (Vista("nivel_06_exterior.jpeg", "Exterior"),),
    ),
    EstadioRival(
        7,
        "Old Trafford",
        (Vista("nivel_07_exterior.jpeg", "Exterior"),),
    ),
    EstadioRival(
        8,
        "Puerta del León",
        (
            Vista("nivel_08_exterior.jpeg", "Exterior"),
            Vista("nivel_08_interior.jpeg", "Interior"),
        ),
    ),
    EstadioRival(
        9,
        "Crest Arena",
        (
            Vista("nivel_09_exterior.jpeg", "Exterior"),
            Vista("nivel_09_exterior_2.jpeg", "Exterior (2)"),
            Vista("nivel_09_exterior_3.jpeg", "Exterior (3)"),
            Vista("nivel_09_aereo.jpeg", "Vista aérea"),
            Vista("nivel_09_acceso.jpeg", "Acceso"),
            Vista("nivel_09_pabellon.jpeg", "Pabellón"),
        ),
    ),
    EstadioRival(
        10,
        "Estadio Imperial Alemán",
        (
            Vista("nivel_10_exterior.jpeg", "Exterior"),
            Vista("nivel_10_interior.jpeg", "Interior"),
        ),
    ),
    EstadioRival(
        11,
        "Einheit Arena",
        (
            Vista("nivel_11_exterior.jpeg", "Exterior"),
            Vista("nivel_11_exterior_2.jpeg", "Exterior (2)"),
            Vista("nivel_11_acceso.jpeg", "Acceso"),
            Vista("nivel_11_interior.jpeg", "Interior"),
        ),
    ),
)


def estadio_rival(nivel: int) -> EstadioRival:
    """Devuelve el estadio del nivel pedido, limitando al rango válido."""
    numero = round(acotar(nivel, 1, NIVEL_MAXIMO))
    return ESTADIOS_RIVALES[numero - 1]


def ruta_vista(vista: Vista) -> Path:
    """Ruta del archivo de una vista dentro de ``imagenes/estadios``."""
    return DIRECTORIO_IMAGENES / "estadios" / vista.archivo


# Las fotos originales ocupan varios megabytes en memoria. Se conservan
# solo las últimas cargadas: la galería puede recorrerlas todas y las
# que salen de la caché se vuelven a leer del disco si hacen falta.
_MAXIMO_CACHE = 8


class _CacheVistas:
    """Caché FIFO de imágenes de estadios ya cargadas."""

    def __init__(self, maximo: int) -> None:
        self.maximo = maximo
        self._imagenes: OrderedDict[str, pygame.Surface] = OrderedDict()

    def obtener(self, vista: Vista) -> pygame.Surface:
        superficie = self._imagenes.get(vista.archivo)

        if superficie is not None:
            self._imagenes.move_to_end(vista.archivo)
            return superficie

        superficie = cargar_imagen(ruta_vista(vista))
        self._imagenes[vista.archivo] = superficie

        while len(self._imagenes) > self.maximo:
            self._imagenes.popitem(last=False)

        return superficie

    def limpiar(self) -> None:
        self._imagenes.clear()

    def __len__(self) -> int:
        return len(self._imagenes)


_cache = _CacheVistas(_MAXIMO_CACHE)


def cargar_vista(vista: Vista) -> pygame.Surface:
    """Carga la foto de una vista, reutilizando la caché acotada."""
    return _cache.obtener(vista)


def limpiar_cache() -> None:
    """Vacía las fotos guardadas (por ejemplo, tras reiniciar pygame)."""
    _cache.limpiar()


def cubrir(
    imagen: pygame.Surface,
    tamano: tuple[int, int],
) -> pygame.Surface:
    """Escala ``imagen`` para llenar ``tamano`` recortando el sobrante.

    Mantiene la proporción original: la foto cubre todo el rectángulo
    destino y los bordes que no encajan se recortan, como el fondo de un
    menú. Se usa para la presentación y para la galería, que tienen
    proporciones distintas a las de las fotos.
    """
    ancho, alto = imagen.get_size()
    destino_ancho, destino_alto = tamano

    if ancho <= 0 or alto <= 0 or destino_ancho <= 0 or destino_alto <= 0:
        return pygame.Surface(tamano)

    escala = max(destino_ancho / ancho, destino_alto / alto)
    escalada = pygame.transform.smoothscale(
        imagen,
        (round(ancho * escala), round(alto * escala)),
    )
    recorte = pygame.Rect(0, 0, destino_ancho, destino_alto)
    recorte.center = escalada.get_rect().center

    cubierta = pygame.Surface(tamano)
    cubierta.blit(escalada, (0, 0), recorte)
    return cubierta
