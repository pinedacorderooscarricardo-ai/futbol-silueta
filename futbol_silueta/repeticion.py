"""Repeticiones de gol: fotogramas congelados de la partida.

Cada instante guarda lo justo para volver a dibujar la jugada: la
posición del balón y la de los 22 jugadores con su aro de posesión.
Los sprites se cachean por (equipo, tiene_balon, dorsal, uniforme),
así que con restaurar posiciones y banderas basta para reconstruir
la imagen de cualquier momento pasado.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from .juego import Juego


class Instante(NamedTuple):
    """Un fotograma de la partida congelado para la repetición."""

    balon_x: float
    balon_y: float
    # (x, y, tiene_balon) de cada jugador, en el orden de juego.jugadores.
    jugadores: tuple[tuple[float, float, bool], ...]


def capturar_instante(juego: Juego) -> Instante:
    """Congela el estado dibujable de la partida en un instante."""
    return Instante(
        juego.balon.pos.x,
        juego.balon.pos.y,
        tuple(
            (jugador.pos.x, jugador.pos.y, jugador.tiene_balon)
            for jugador in juego.jugadores
        ),
    )


def aplicar_instante(juego: Juego, instante: Instante) -> None:
    """Restaura en las entidades el estado de un instante grabado."""
    juego.balon.pos.update(instante.balon_x, instante.balon_y)

    for jugador, (x, y, tiene_balon) in zip(
        juego.jugadores,
        instante.jugadores,
        strict=False,
    ):
        jugador.pos.update(x, y)
        jugador.tiene_balon = tiene_balon
        jugador.actualizar_rect()
