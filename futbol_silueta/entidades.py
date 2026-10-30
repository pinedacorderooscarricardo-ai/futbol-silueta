"""Jugadores y balón: estado, movimiento y sprites."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

import pygame

from .configuracion import (
    AMARILLO,
    BLANCO,
    CAMPO_RECT,
    COLOR_EQUIPO,
    DISTANCIA_CONDUCCION,
    FACTOR_POSESION,
    FORMACION,
    FPS,
    FRICCION,
    NEGRO,
    PASO_MAXIMO_BALON,
    RADIO_BALON,
    RADIO_JUGADOR,
    VELOCIDAD_JUGADOR,
    VELOCIDAD_MINIMA_BALON,
    Equipo,
    Rol,
)
from .utilidades import acotar_posicion, equipo_que_anota


class Jugador:
    """Jugador de cualquiera de los dos equipos.

    Los sprites no cambian durante la partida: se generan una sola vez
    y quedan guardados en caché por la clave (equipo, tiene_balon).
    """

    RADIO = RADIO_JUGADOR
    MARGEN_SPRITE = 8  # Borde extra del sprite, para el aro de posesión.

    _sprites: dict[tuple[Equipo, bool], pygame.Surface] = {}

    def __init__(
        self,
        equipo: Equipo,
        rol: Rol,
        x: float,
        y: float,
    ) -> None:
        self.equipo = equipo
        self.rol = rol
        self.pos = pygame.Vector2(x, y)
        self.posicion_base = pygame.Vector2(x, y)
        self.velocidad = VELOCIDAD_JUGADOR
        self.tiene_balon = False
        # Dirección de mirada: cada equipo arranca mirando al arco rival.
        self.direccion = pygame.Vector2(
            1.0 if equipo is Equipo.LOCAL else -1.0,
            0.0,
        )
        self.color = COLOR_EQUIPO[equipo]
        self.rect = pygame.Rect(0, 0, self.RADIO * 2, self.RADIO * 2)
        # Rect del sprite completo (con margen), para blitear sin crear
        # un rect nuevo en cada fotograma.
        lado_sprite = (self.RADIO + self.MARGEN_SPRITE) * 2
        self.rect_sprite = pygame.Rect(0, 0, lado_sprite, lado_sprite)
        self.actualizar_rect()

    def actualizar_rect(self) -> None:
        centro = (round(self.pos.x), round(self.pos.y))
        self.rect.center = centro
        self.rect_sprite.center = centro

    def mover(self, dx: float, dy: float) -> None:
        """Desplaza al jugador y lo mantiene dentro del campo."""
        if dx == 0.0 and dy == 0.0:
            return

        self.direccion.update(dx, dy)
        self.direccion.normalize_ip()
        self._desplazar(dx, dy)

    def empujar(self, dx: float, dy: float) -> None:
        """Desplaza por una colisión sin cambiar la dirección de mirada."""
        self._desplazar(dx, dy)

    def _desplazar(self, dx: float, dy: float) -> None:
        if dx == 0.0 and dy == 0.0:
            return

        self.pos.x += dx
        self.pos.y += dy
        acotar_posicion(self.pos, self.RADIO)
        self.actualizar_rect()

    def mover_hacia(
        self,
        objetivo: pygame.Vector2,
        velocidad: float,
        dt: float,
    ) -> None:
        """Se mueve hacia un objetivo sin sobrepasarlo."""
        dx = objetivo.x - self.pos.x
        dy = objetivo.y - self.pos.y
        distancia2 = dx * dx + dy * dy

        if distancia2 <= 1.0:
            return

        distancia = math.sqrt(distancia2)
        factor = min(velocidad * dt, distancia) / distancia
        self.mover(dx * factor, dy * factor)

    def velocidad_efectiva(self) -> float:
        """Velocidad real: se reduce mientras conduce el balón."""
        return self.velocidad * (
            FACTOR_POSESION if self.tiene_balon else 1.0
        )

    def dibujar(self, superficie: pygame.Surface) -> None:
        sprite = self._obtener_sprite()
        superficie.blit(sprite, self.rect_sprite)

    def _obtener_sprite(self) -> pygame.Surface:
        clave = (self.equipo, self.tiene_balon)
        sprite = self._sprites.get(clave)

        if sprite is None:
            sprite = self._crear_sprite()
            self._sprites[clave] = sprite

        return sprite

    def _crear_sprite(self) -> pygame.Surface:
        lado = (self.RADIO + self.MARGEN_SPRITE) * 2
        sprite = pygame.Surface((lado, lado), pygame.SRCALPHA)
        centro = (lado // 2, lado // 2)

        pygame.draw.circle(sprite, self.color, centro, self.RADIO)
        pygame.draw.circle(sprite, BLANCO, centro, self.RADIO, 2)

        if self.tiene_balon:
            # Aro amarillo alrededor del jugador con el balón.
            pygame.draw.circle(
                sprite,
                AMARILLO,
                centro,
                self.RADIO + 5,
                2,
            )

        return sprite.convert_alpha()


def crear_jugadores() -> list[Jugador]:
    """Crea los 22 jugadores (11 por equipo) a partir de la formación."""
    jugadores: list[Jugador] = []

    for equipo in (Equipo.LOCAL, Equipo.VISITANTE):
        for posicion in FORMACION:
            fraccion_x = posicion.x

            if equipo is Equipo.VISITANTE:
                fraccion_x = 1.0 - fraccion_x

            x = CAMPO_RECT.left + fraccion_x * CAMPO_RECT.width
            y = CAMPO_RECT.top + posicion.y * CAMPO_RECT.height
            jugadores.append(Jugador(equipo, posicion.rol, x, y))

    return jugadores


def elegir_delantero_controlado(jugadores: Sequence[Jugador]) -> Jugador:
    """Devuelve el delantero local más cercano al centro del campo."""
    delanteros = [
        jugador
        for jugador in jugadores
        if jugador.equipo is Equipo.LOCAL
        and jugador.rol is Rol.DELANTERO
    ]

    if not delanteros:
        delanteros = [
            jugador
            for jugador in jugadores
            if jugador.equipo is Equipo.LOCAL
        ]

    centro = pygame.Vector2(CAMPO_RECT.center)

    return min(
        delanteros,
        key=lambda jugador: jugador.pos.distance_squared_to(centro),
    )


class Balon:
    """Balón: posición, física libre y sprite.

    La posesión la gestiona ``Juego``; esta clase solo se ocupa de dónde
    está el balón y de cómo se mueve.
    """

    RADIO = RADIO_BALON
    MARGEN_SPRITE = 2  # Borde extra del sprite, para el contorno.

    def __init__(self) -> None:
        self.pos = pygame.Vector2()
        self.vel = pygame.Vector2()
        self._sprite: pygame.Surface | None = None

    def colocar_en_el_centro(self) -> None:
        """Deja el balón parado en el punto del saque."""
        self.pos.update(CAMPO_RECT.center)
        self.vel.update(0.0, 0.0)

    def actualizar_conducido(self, portador: Jugador) -> Equipo | None:
        """Pega el balón delante del jugador que lo conduce.

        Devuelve el equipo que anota si el balón cruza una línea de gol
        (conducirlo también puede acabar en autogol). Si no hay gol, lo
        mantiene dentro del campo.
        """
        self.pos.update(
            portador.pos.x + portador.direccion.x * DISTANCIA_CONDUCCION,
            portador.pos.y + portador.direccion.y * DISTANCIA_CONDUCCION,
        )
        self.vel.update(0.0, 0.0)

        gol = equipo_que_anota(self.pos.x, self.pos.y)

        if gol is None:
            acotar_posicion(self.pos, self.RADIO)

        return gol

    def actualizar_libre(
        self,
        dt: float,
        intentar_recoger: Callable[[], bool],
    ) -> Equipo | None:
        """Física del balón libre, avanzando en subpasos.

        Los subpasos evitan que un balón rápido atraviese a un jugador
        entre dos fotogramas. En cada subpaso: se mueve, roza con el
        césped, rebota en los bordes y puede ser recogido por alguien.

        Devuelve el equipo que anota si entra en una portería, o None.
        """
        velocidad = self.vel.length()
        pasos = max(
            1,
            math.ceil(velocidad * dt / PASO_MAXIMO_BALON),
        )
        dt_paso = dt / pasos
        # La fricción es la misma en todos los subpasos: se calcula
        # una sola vez en lugar de una potencia por subpaso.
        factor_friccion = FRICCION ** (dt_paso * FPS)

        for _ in range(pasos):
            self.pos.x += self.vel.x * dt_paso
            self.pos.y += self.vel.y * dt_paso
            self.vel *= factor_friccion
            self._detener_si_va_lento()

            gol = self._rebotar()
            if gol is not None:
                return gol

            if intentar_recoger():
                return None

            if self.vel.length_squared() == 0.0:
                break

        return None

    def _detener_si_va_lento(self) -> None:
        if self.vel.length_squared() < VELOCIDAD_MINIMA_BALON**2:
            self.vel.update(0.0, 0.0)

    def _rebotar(self) -> Equipo | None:
        """Rebota en los bordes. Devuelve el equipo que anota, si hay gol."""
        # Bordes superior e inferior.
        if self.pos.y - self.RADIO < CAMPO_RECT.top:
            self.pos.y = CAMPO_RECT.top + self.RADIO
            self.vel.y = abs(self.vel.y)
        elif self.pos.y + self.RADIO > CAMPO_RECT.bottom:
            self.pos.y = CAMPO_RECT.bottom - self.RADIO
            self.vel.y = -abs(self.vel.y)

        # Líneas de gol: gol si entra por la portería; si no, rebote.
        gol = equipo_que_anota(self.pos.x, self.pos.y)
        if gol is not None:
            return gol

        if self.pos.x + self.RADIO >= CAMPO_RECT.right:
            self.pos.x = CAMPO_RECT.right - self.RADIO
            self.vel.x = -abs(self.vel.x)
        elif self.pos.x - self.RADIO <= CAMPO_RECT.left:
            self.pos.x = CAMPO_RECT.left + self.RADIO
            self.vel.x = abs(self.vel.x)

        return None

    def dibujar(self, superficie: pygame.Surface) -> None:
        if self._sprite is None:
            self._sprite = self._crear_sprite()

        superficie.blit(
            self._sprite,
            self._sprite.get_rect(
                center=(round(self.pos.x), round(self.pos.y))
            ),
        )

    def _crear_sprite(self) -> pygame.Surface:
        lado = (self.RADIO + self.MARGEN_SPRITE) * 2
        sprite = pygame.Surface((lado, lado), pygame.SRCALPHA)
        centro = (lado // 2, lado // 2)

        pygame.draw.circle(sprite, BLANCO, centro, self.RADIO)
        pygame.draw.circle(sprite, NEGRO, centro, self.RADIO, 1)

        return sprite.convert_alpha()
