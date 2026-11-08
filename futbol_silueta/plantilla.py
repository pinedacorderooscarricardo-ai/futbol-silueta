"""Plantilla: nombre, dorsal, atributos y posición de cada jugador.

La plantilla editable guarda un ``JugadorPlantilla`` por cada uno de los
once huecos de cada equipo, en el mismo orden que ``FORMACION``: la
posición ``x`` se expresa desde el arco propio (0.0 = arco propio,
1.0 = arco rival) y el visitante se refleja al dibujar, igual que la
formación base.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import NamedTuple

from .configuracion import (
    FORMACION,
    NUMERO_SUPLENTES,
    TITULARES_POR_EQUIPO,
    Equipo,
    Rol,
    formacion_por_nombre,
)
from .utilidades import acotar

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
    # Los once primeros son los titulares; el resto, el banquillo.
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
        "Parodi",
        "Quintero",
        "Ríos",
        "Salas",
        "Torres",
        "Urbina",
        "Vidal",
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
        "Cáceres",
        "Espinoza",
        "Figueroa",
        "Gallardo",
        "Herrera",
        "Insaurralde",
        "Jara",
    ),
}


def plantilla_por_defecto(equipo: Equipo) -> tuple[JugadorPlantilla, ...]:
    """Once fichas iniciales de los titulares, siguiendo la formación."""
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


# Banquillo por defecto: un portero, dos defensas, dos medios y dos
# delanteros, con dorsales del 12 en adelante.
ROLES_SUPLENTES: tuple[Rol, ...] = (
    Rol.PORTERO,
    Rol.DEFENSA,
    Rol.DEFENSA,
    Rol.MEDIO,
    Rol.MEDIO,
    Rol.DELANTERO,
    Rol.DELANTERO,
)


def suplentes_por_defecto(
    equipo: Equipo,
) -> tuple[JugadorPlantilla, ...]:
    """Fichas del banquillo, listas para entrar por sustitución.

    Su posición es de referencia (no salen al campo hasta entrar) y al
    sustituir heredan el rol y el hueco del titular que sale, por lo que
    conservan nombre, dorsal y atributos propios.
    """
    nombres = NOMBRES_POR_DEFECTO[equipo]
    reparto = max(1, len(ROLES_SUPLENTES) - 1)

    return tuple(
        JugadorPlantilla(
            nombre=nombres[TITULARES_POR_EQUIPO + indice],
            dorsal=TITULARES_POR_EQUIPO + 1 + indice,
            rol=ROLES_SUPLENTES[indice % len(ROLES_SUPLENTES)],
            x=0.5,
            y=acotar(0.08 + indice * 0.12 / reparto * 0.5, 0.05, 0.95),
            factor_velocidad=1.0,
            factor_fuerza=1.0,
        )
        for indice in range(NUMERO_SUPLENTES)
    )


def suplentes_por_defecto_todos() -> dict[Equipo, tuple[JugadorPlantilla, ...]]:
    """Banquillos iniciales de los dos equipos."""
    return {equipo: suplentes_por_defecto(equipo) for equipo in Equipo}


def plantillas_por_defecto() -> dict[Equipo, tuple[JugadorPlantilla, ...]]:
    """Plantillas iniciales de los dos equipos."""
    return {equipo: plantilla_por_defecto(equipo) for equipo in Equipo}


def _numero_finito(valor: object, defecto: float) -> float:
    """Convierte ``valor`` a un float finito o devuelve ``defecto``."""
    try:
        numero = float(valor)  # type: ignore[arg-type]
    except (TypeError, ValueError, OverflowError):
        return defecto

    return numero if math.isfinite(numero) else defecto


def _dorsal_valido(valor: object, defecto: int) -> int:
    """Dorsal entero dentro del rango que admite el juego (1-99)."""
    try:
        numero = int(valor)  # type: ignore[arg-type]
    except (TypeError, ValueError, OverflowError):
        return defecto

    return int(acotar(numero, 1, 99))


def _rol_valido(rol: object, defecto: Rol) -> Rol:
    """Rol válido a partir de un ``Rol`` o de su texto guardado."""
    if isinstance(rol, Rol):
        return rol

    try:
        return Rol(str(rol))
    except (ValueError, TypeError):
        return defecto


def normalizar_ficha(
    ficha: JugadorPlantilla,
    base: JugadorPlantilla,
) -> JugadorPlantilla:
    """Devuelve una ficha con todos sus valores dentro de rangos seguros.

    Se usa al cargar datos guardados y al crear a los jugadores: una base
    corrupta o una plantilla incompleta nunca debe mover a un jugador
    fuera del campo, dejar el dorsal a cero ni provocar factores NaN.
    """
    nombre = ficha.nombre if isinstance(ficha.nombre, str) else base.nombre

    return JugadorPlantilla(
        nombre=nombre[:LARGO_NOMBRE],
        dorsal=_dorsal_valido(ficha.dorsal, base.dorsal),
        rol=_rol_valido(ficha.rol, base.rol),
        x=acotar(_numero_finito(ficha.x, base.x), 0.0, 1.0),
        y=acotar(_numero_finito(ficha.y, base.y), 0.0, 1.0),
        factor_velocidad=acotar(
            _numero_finito(ficha.factor_velocidad, base.factor_velocidad),
            PRESETS_VELOCIDAD[0][1],
            PRESETS_VELOCIDAD[-1][1],
        ),
        factor_fuerza=acotar(
            _numero_finito(ficha.factor_fuerza, base.factor_fuerza),
            PRESETS_FUERZA[0][1],
            PRESETS_FUERZA[-1][1],
        ),
    )


def normalizar_plantilla(
    fichas: Sequence[JugadorPlantilla] | None,
    equipo: Equipo,
    base: Sequence[JugadorPlantilla] | None = None,
) -> tuple[JugadorPlantilla, ...]:
    """Devuelve exactamente once fichas válidas para ``equipo``.

    Si faltan fichas se completan con ``base`` (por defecto, la
    plantilla inicial); si sobran se recortan; y cada ficha se sanea con
    :func:`normalizar_ficha`. Así el partido, el editor y el guardado
    trabajan siempre con 11 jugadores.
    """
    if (
        base is None
        or not isinstance(base, Sequence)
        or len(base) != len(FORMACION)
    ):
        base = plantilla_por_defecto(equipo)

    if not fichas:
        return tuple(base)

    try:
        lista = tuple(fichas)
    except TypeError:
        # Un valor inesperado (por ejemplo, None dentro del diccionario)
        # se trata como plantilla vacía y se completa con la base.
        return tuple(base)
    normalizadas: list[JugadorPlantilla] = []

    for indice, defecto in enumerate(base):
        ficha = lista[indice] if indice < len(lista) else None

        if not isinstance(ficha, JugadorPlantilla):
            normalizadas.append(defecto)
            continue

        normalizadas.append(normalizar_ficha(ficha, defecto))

    return tuple(normalizadas)


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
