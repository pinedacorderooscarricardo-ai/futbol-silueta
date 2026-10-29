"""Niveles del juego: cada escudo rival es un nivel de dificultad.

La función :func:`construir_niveles` divide el partido en
``NIVEL_MAXIMO`` niveles: cada uno tiene su escudo, su rival y unos
parámetros de dificultad que aumentan de forma progresiva.
"""

from __future__ import annotations

from typing import NamedTuple

from .configuracion import (
    DISTANCIA_DISPARO_IA,
    DURACION_POSESION_PORTERO,
    FACTOR_APUNTADO_DISPARO,
    PRESORES_POR_EQUIPO,
    RADIO_ATAJADA,
    RADIO_MARCAJE,
    TIEMPO_MINIMO_POSESION_IA,
    VELOCIDAD_IA,
)
from .escudos import nombre_archivo_escudo
from .utilidades import acotar


class ParametrosNivel(NamedTuple):
    """Ajustes de dificultad de un nivel.

    El nivel 1 replica exactamente los valores por defecto del juego;
    a partir de ahí la IA corre más, presiona con más jugadores,
    dispara antes y con mejor puntería, y su portero despeja más rápido.
    """

    velocidad_ia: float
    presores: int
    distancia_disparo: float
    tiempo_minimo_posesion: int
    factor_apuntado: float
    radio_atajada_rival: float
    duracion_posesion_portero: int
    radio_marcaje: float


class Nivel(NamedTuple):
    """Un nivel del juego: número, rival, escudo y dificultad."""

    numero: int
    rival: str
    escudo: str
    parametros: ParametrosNivel


# Rival de cada nivel, en el orden de los escudos escudo_01..escudo_11.
RIVALES: tuple[str, ...] = (
    "Club Aurora",
    "Pasión Fútbol",
    "U. D. Prisma",
    "Atlético Corona",
    "Real Laurel",
    "Deportivo Trueno",
    "Club Titán",
    "Imperial Oro",
    "Furia FC",
    "Real Leyenda",
    "Campeón Eterno",
)

NIVEL_MAXIMO = len(RIVALES)

# Fracción de dificultad extra repartida linealmente entre el nivel 1
# y el último nivel.
_FACTOR_VELOCIDAD = 0.30
_PASO_PRESORES = 5  # Nivel a partir del cual presionan 3 jugadores.
_REDUCCION_DISPARO = 0.23
_REDUCCION_POSESION_IA = 0.55
_AMPLIACION_APUNTADO = 0.18
_AMPLIACION_ATAJADA = 12.0
_REDUCCION_POSESION_PORTERO = 0.44
_AMPLIACION_MARCAJE = 40.0


def parametros_de_nivel(nivel: int) -> ParametrosNivel:
    """Calcula los parámetros de dificultad de un nivel.

    El nivel 1 usa los valores por defecto de :mod:`configuracion` y
    cada nivel siguiente los endurece de forma lineal.
    """
    numero = round(acotar(nivel, 1, NIVEL_MAXIMO))
    progreso = (numero - 1) / (NIVEL_MAXIMO - 1)

    return ParametrosNivel(
        velocidad_ia=VELOCIDAD_IA * (1.0 + _FACTOR_VELOCIDAD * progreso),
        presores=3 if numero >= _PASO_PRESORES else PRESORES_POR_EQUIPO,
        distancia_disparo=(
            DISTANCIA_DISPARO_IA * (1.0 - _REDUCCION_DISPARO * progreso)
        ),
        tiempo_minimo_posesion=round(
            TIEMPO_MINIMO_POSESION_IA
            * (1.0 - _REDUCCION_POSESION_IA * progreso)
        ),
        factor_apuntado=(
            FACTOR_APUNTADO_DISPARO + _AMPLIACION_APUNTADO * progreso
        ),
        radio_atajada_rival=RADIO_ATAJADA + _AMPLIACION_ATAJADA * progreso,
        duracion_posesion_portero=round(
            DURACION_POSESION_PORTERO
            * (1.0 - _REDUCCION_POSESION_PORTERO * progreso)
        ),
        radio_marcaje=RADIO_MARCAJE + _AMPLIACION_MARCAJE * progreso,
    )


def construir_niveles() -> list[Nivel]:
    """Divide el juego en niveles: un escudo rival por nivel.

    Cada nivel es más difícil que el anterior y usa el escudo cuya
    imagen vive en ``imagenes/escudos/escudo_NN.jpeg``.
    """
    return [
        Nivel(
            numero=numero,
            rival=RIVALES[indice],
            escudo=nombre_archivo_escudo(numero),
            parametros=parametros_de_nivel(numero),
        )
        for indice, numero in enumerate(range(1, NIVEL_MAXIMO + 1))
    ]


NIVELES: tuple[Nivel, ...] = tuple(construir_niveles())


def nivel_por_numero(numero: int) -> Nivel:
    """Devuelve el nivel pedido, limitando al rango válido."""
    numero = round(acotar(numero, 1, NIVEL_MAXIMO))
    return NIVELES[numero - 1]
