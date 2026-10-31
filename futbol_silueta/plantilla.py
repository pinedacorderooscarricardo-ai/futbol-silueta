"""Plantilla: nombre, dorsal, atributos y posición de cada jugador.

La plantilla editable guarda un ``JugadorPlantilla`` por cada uno de los
once huecos de cada equipo, en el mismo orden que ``FORMACION``: la
posición ``x`` se expresa desde el arco propio (0.0 = arco propio,
1.0 = arco rival) y el visitante se refleja al dibujar, igual que la
formación base.
"""

from __future__ import annotations

from typing import NamedTuple

from .configuracion import FORMACION, Equipo, Rol, formacion_por_nombre

# Orden fijo para ciclar el rol en el editor.
ROLES: tuple[Rol, ...] = (
    Rol.PORTERO,
    Rol.DEFENSA,
    Rol.MEDIO,
    Rol.DELANTERO,
)

# Ajustes de atributos: multiplicadores sobre la velocidad y la fuerza
# base del juego.
PRESETS_VELOCIDAD: tuple[tuple[str, float], ...] = (
    ("Lenta", 0.85),
    ("Normal", 1.0),
    ("Rápida", 1.15),
    ("Veloz", 1.3),
)
PRESETS_FUERZA: tuple[tuple[str, float], ...] = (
    ("Débil", 0.8),
    ("Normal", 1.0),
    ("Fuerte", 1.2),
    ("Potente", 1.4),
)

LARGO_NOMBRE = 14


class JugadorPlantilla(NamedTuple):
    """Ficha editable de un jugador de la plantilla."""

    nombre: str
    dorsal: int
    rol: Rol
    x: float
    y: float
    factor_velocidad: float
    factor_fuerza: float


NOMBRES_POR_DEFECTO: dict[Equipo, tuple[str, ...]] = {
    Equipo.LOCAL: (
        "Cabrera",
        "Duarte",
        "Ferrer",
        "Guzmán",
        "Ibarra",
        "Juárez",
        "Luna",
        "Molina",
        "Nieto",
        "Ocampo",
        "Peralta",
    ),
    Equipo.VISITANTE: (
        "Quiroga",
        "Ramírez",
        "Sosa",
        "Tejeda",
        "Ulloa",
        "Vargas",
        "Yáñez",
        "Zárate",
        "Álvarez",
        "Bravo",
        "Castro",
    ),
}


def plantilla_por_defecto(equipo: Equipo) -> tuple[JugadorPlantilla, ...]:
    """Once fichas iniciales para un equipo, siguiendo la formación base."""
    nombres = NOMBRES_POR_DEFECTO[equipo]

    return tuple(
        JugadorPlantilla(
            nombre=nombres[indice],
            dorsal=indice + 1,
            rol=posicion.rol,
            x=posicion.x,
            y=posicion.y,
            factor_velocidad=1.0,
            factor_fuerza=1.0,
        )
        for indice, posicion in enumerate(FORMACION)
    )


def plantillas_por_defecto() -> dict[Equipo, tuple[JugadorPlantilla, ...]]:
    """Plantillas iniciales de los dos equipos."""
    return {equipo: plantilla_por_defecto(equipo) for equipo in Equipo}


def nombre_velocidad(factor: float) -> str:
    """Nombre del preset de velocidad más cercano a ``factor``."""
    return min(
        PRESETS_VELOCIDAD,
        key=lambda preset: abs(preset[1] - factor),
    )[0]


def nombre_fuerza(factor: float) -> str:
    """Nombre del preset de fuerza más cercano a ``factor``."""
    return min(
        PRESETS_FUERZA,
        key=lambda preset: abs(preset[1] - factor),
    )[0]


def aplicar_formacion(
    fichas: tuple[JugadorPlantilla, ...],
    nombre: str,
) -> tuple[JugadorPlantilla, ...]:
    """Recoloca las fichas de un equipo según una formación de tácticas.

    Asigna a cada ficha el rol y la posición que la formación pide en
    su hueco (portero primero, luego defensas, medios y delanteros),
    conservando el nombre, el dorsal y los atributos de cada jugador.
    """
    posiciones = formacion_por_nombre(nombre)

    return tuple(
        ficha._replace(rol=posicion.rol, x=posicion.x, y=posicion.y)
        for ficha, posicion in zip(fichas, posiciones, strict=False)
    )
