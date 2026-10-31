"""Porteros inteligentes: anticipan disparos, se lanzan y fallan.

Cada portero IA se apoya en un :class:`PorteroInteligente`, que decide
dónde colocarse, cuándo lanzarse y con cuánto error. La calidad del
portero rival escala con el nivel de la campaña; la del local es fija.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, NamedTuple

import pygame

from .configuracion import (
    DESVIO_ERROR_PORTERO,
    DURACION_LANCE_PORTERO,
    ENFRIAMIENTO_LANCE,
    MARGEN_LANCE_X,
    PORTERIA_INFERIOR,
    PORTERIA_SUPERIOR,
    TIEMPO_LLEGADA_LANCE,
    UMBRAL_LANCE_Y,
    VELOCIDAD_MINIMA_ATAJADA,
    Equipo,
)
from .niveles import NIVEL_MAXIMO
from .utilidades import acotar

if TYPE_CHECKING:
    from .entidades import Jugador
    from .juego import Juego


class PorteroCalidad(NamedTuple):
    """Habilidad de un portero, de torpe (valores bajos) a sobresaliente.

    ``error`` es la probabilidad de encarar mal un disparo (y de fallar
    el lance); ``reaccion_ms`` cuánto tarda en responder; ``factor_lance``
    multiplica su velocidad durante el lance; ``anticipacion`` mide cuánto
    predice la trayectoria del balón frente a seguirlo a ciegas.
    """

    error: float
    reaccion_ms: float
    factor_lance: float
    anticipacion: float


# El portero local defiende la portería del jugador: seguro pero no
# perfecto, con la misma calidad en todos los niveles.
PORTERO_LOCAL = PorteroCalidad(
    error=0.16,
    reaccion_ms=260.0,
    factor_lance=1.9,
    anticipacion=0.65,
)


def calidad_rival(nivel: int) -> PorteroCalidad:
    """Calidad del portero rival: mejora nivel a nivel de la campaña.

    En el nivel 1 es torpe (se equivoca a menudo, tarda en reaccionar) y
    en el último casi no falla, responde rápido y casi siempre adivina
    la trayectoria del disparo.
    """
    numero = round(acotar(nivel, 1, NIVEL_MAXIMO))
    progreso = (numero - 1) / (NIVEL_MAXIMO - 1)

    return PorteroCalidad(
        error=0.42 - 0.34 * progreso,
        reaccion_ms=430.0 - 290.0 * progreso,
        factor_lance=1.6 + 0.5 * progreso,
        anticipacion=0.30 + 0.62 * progreso,
    )


class PorteroInteligente:
    """Cerebro de un portero durante una jugada.

    Sin peligro cubre el ángulo sobre su línea, siguiendo la altura del
    balón. Cuando detecta un disparo hacia su arco espera su tiempo de
    reacción, predice dónde cruzará el balón —con un desvío que crece
    con su error— y se lanza si el punto de intercepción queda fuera de
    su alcance caminando. Un portero que falló el tiro se lanza igual,
    pero al sitio equivocado y con las manos blandas: el balón se le
    escapa.
    """

    def __init__(self, jugador: Jugador, calidad: PorteroCalidad) -> None:
        self.jugador = jugador
        self.calidad = calidad
        self.falla_tiro = False
        self._desvio = 0.0
        self._reaccion_restante = 0.0
        self._lance_restante = 0.0
        self._enfriamiento = 0.0
        self._tiro_activo = False
        self._objetivo_lance = pygame.Vector2()

    # --------------------------------------------------
    # Detección del disparo
    # --------------------------------------------------

    def _es_tiro_peligroso(self, juego: Juego) -> bool:
        """True si el balón libre y rápido apunta a la portería propia."""
        balon = juego.balon

        if juego.portador is not None:
            return False

        if balon.vel.length_squared() < VELOCIDAD_MINIMA_ATAJADA**2:
            return False

        return self._intercepcion(juego) is not None

    def _intercepcion(self, juego: Juego) -> tuple[float, float] | None:
        """(y, segundos) donde el balón cruzará la línea del portero.

        Devuelve None si el balón no llegará a esa línea (se aleja, va
        demasiado lento o tardaría demasiado).
        """
        balon = juego.balon

        if abs(balon.vel.x) < 1e-6:
            return None

        linea = self.jugador.posicion_base.x
        t = (linea - balon.pos.x) / balon.vel.x

        if t < 0.0 or t > 2.5:
            return None

        y = balon.pos.y + balon.vel.y * t

        return (
            acotar(y, PORTERIA_SUPERIOR - 14.0, PORTERIA_INFERIOR + 14.0),
            t,
        )

    def _actualizar_tiro(self, juego: Juego) -> None:
        """Detecta el inicio y fin de cada disparo y tira los dados.

        El error se decide una vez por disparo, no por fotograma: si el
        portero ``falla`` este tiro, se equivocará de sitio y no lo
        atrapará durante el lance.
        """
        tiro = self._es_tiro_peligroso(juego)

        if tiro and not self._tiro_activo:
            self.falla_tiro = random.random() < self.calidad.error
            self._desvio = random.uniform(-1.0, 1.0) * (
                DESVIO_ERROR_PORTERO * self.calidad.error
            )
            self._reaccion_restante = self.calidad.reaccion_ms * (
                1.6 if self.falla_tiro else 1.0
            )
        elif not tiro:
            self.falla_tiro = False
            self._desvio = 0.0

        self._tiro_activo = tiro

    # --------------------------------------------------
    # Movimiento
    # --------------------------------------------------

    def actualizar(self, juego: Juego, dt: float) -> None:
        """Mueve al portero un fotograma según la situación del balón."""
        jugador = self.jugador
        dt_ms = dt * 1000.0
        self._reaccion_restante = max(0.0, self._reaccion_restante - dt_ms)
        self._enfriamiento = max(0.0, self._enfriamiento - dt_ms)
        self._actualizar_tiro(juego)

        if self._lance_restante > 0.0:
            self._lance_restante -= dt_ms
            jugador.lance_restante = self._lance_restante
            jugador.mover_hacia(
                self._objetivo_lance,
                self._velocidad_base(juego) * self.calidad.factor_lance,
                dt,
            )
            return

        jugador.lance_restante = 0.0
        predicho = self._intercepcion(juego)
        atento = (
            self._tiro_activo
            and self._reaccion_restante <= 0.0
            and predicho is not None
        )

        if atento:
            y_predicho, t_llegada = predicho
            y_objetivo = (
                juego.balon.pos.y * (1.0 - self.calidad.anticipacion)
                + (y_predicho + self._desvio) * self.calidad.anticipacion
            )

            if (
                self._enfriamiento <= 0.0
                and t_llegada <= TIEMPO_LLEGADA_LANCE
                and abs(y_objetivo - jugador.pos.y) > UMBRAL_LANCE_Y
            ):
                self._iniciar_lance(juego, y_objetivo)
                return

            objetivo = pygame.Vector2(
                self.jugador.posicion_base.x
                + (1.0 if self.jugador.equipo is Equipo.LOCAL else -1.0)
                * 5.0,
                acotar(
                    y_objetivo,
                    PORTERIA_SUPERIOR - 20.0,
                    PORTERIA_INFERIOR + 20.0,
                ),
            )
        else:
            objetivo = self._posicion_de_angulo(juego)

        jugador.mover_hacia(objetivo, self._velocidad_base(juego), dt)

    def _iniciar_lance(self, juego: Juego, y_objetivo: float) -> None:
        """Arranca el lance hacia el punto de intercepción estimado."""
        jugador = self.jugador
        linea = jugador.posicion_base.x
        self._objetivo_lance.update(
            linea
            + acotar(
                juego.balon.pos.x - linea,
                -MARGEN_LANCE_X,
                MARGEN_LANCE_X,
            ),
            y_objetivo,
        )
        self._lance_restante = float(DURACION_LANCE_PORTERO)
        self._enfriamiento = DURACION_LANCE_PORTERO + ENFRIAMIENTO_LANCE
        jugador.lance_restante = self._lance_restante

    def _posicion_de_angulo(self, juego: Juego) -> pygame.Vector2:
        """Cobertura clásica: sobre su línea, siguiendo la Y del balón."""
        jugador = self.jugador
        signo = 1.0 if jugador.equipo is Equipo.LOCAL else -1.0

        return pygame.Vector2(
            jugador.posicion_base.x + signo * 5.0,
            acotar(
                juego.balon.pos.y,
                PORTERIA_SUPERIOR - 20.0,
                PORTERIA_INFERIOR + 20.0,
            ),
        )

    def _velocidad_base(self, juego: Juego) -> float:
        """Velocidad de desplazamiento del portero en este nivel."""
        return juego.nivel_actual.parametros.velocidad_ia * (
            self.jugador.factor_velocidad
        )

    # --------------------------------------------------
    # Atajada
    # --------------------------------------------------

    def radio_atajada(self, base: float) -> float:
        """Alcance de las manos: mayor mientras dura un lance."""
        if self._lance_restante > 0.0:
            return base * 1.35

        return base

    def puede_atrapar(self) -> bool:
        """False si este lance va a fallar por un error del portero."""
        return not (self._lance_restante > 0.0 and self.falla_tiro)
