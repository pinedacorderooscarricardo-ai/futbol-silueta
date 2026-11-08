"""Jugadores y balón: estado, movimiento y sprites."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from typing import NamedTuple

import pygame

from .configuracion import (
    AMARILLO,
    BLANCO,
    CAMPO_RECT,
    DISTANCIA_CONDUCCION,
    FACTOR_POSESION,
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
from .uniformes import (
    UNIFORMES_POR_DEFECTO,
    Uniforme,
    dibujar_jugador_uniforme,
)
from .plantilla import (
    JugadorPlantilla,
    normalizar_plantilla,
)
from .utilidades import acotar_posicion, equipo_que_anota

# Cuánto se eleva un jugador al saltar, en píxeles.
ALTURA_SALTO = 16.0


class Jugador:
    """Jugador de cualquiera de los dos equipos.

    Los sprites no cambian durante la partida: se generan una sola vez
    y quedan guardados en caché por la clave (equipo, tiene_balon,
    dorsal, uniforme, mostrar_numero).
    """

    RADIO = RADIO_JUGADOR
    MARGEN_SPRITE = 8  # Borde extra del sprite, para el aro de posesión.

    _sprites: dict[
        tuple[Equipo, bool, int, Uniforme, bool],
        pygame.Surface,
    ] = {}

    def __init__(
        self,
        equipo: Equipo,
        rol: Rol,
        x: float,
        y: float,
        numero: int = 0,
        uniforme: Uniforme | None = None,
        mostrar_numero: bool = True,
        nombre: str = "",
        factor_velocidad: float = 1.0,
        factor_fuerza: float = 1.0,
    ) -> None:
        self.equipo = equipo
        self.rol = rol
        self.pos = pygame.Vector2(x, y)
        self.posicion_base = pygame.Vector2(x, y)
        self.velocidad = VELOCIDAD_JUGADOR * factor_velocidad
        self.factor_velocidad = factor_velocidad
        self.factor_fuerza = factor_fuerza
        self.tiene_balon = False
        # Dirección de mirada: cada equipo arranca mirando al arco rival.
        self.direccion = pygame.Vector2(
            1.0 if equipo is Equipo.LOCAL else -1.0,
            0.0,
        )
        self.numero = numero
        self.nombre = nombre
        # Milisegundos que faltan para terminar un lance (solo porteros).
        self.lance_restante = 0.0
        # Cansancio de la IA (0-1): sube persiguiendo o conduciendo y
        # reduce la velocidad; la rival rota a sus agotados.
        self.cansancio = 0.0
        # Animación procedural: zancada al correr, salto y caída.
        self.fase = 0.0
        self._impulso = 0.0
        self.salto_restante = 0.0
        self.salto_total = 1.0
        self.caida_restante = 0.0
        self.caida_total = 1.0
        self.uniforme = (
            uniforme
            if uniforme is not None
            else UNIFORMES_POR_DEFECTO[equipo]
        )
        self.mostrar_numero = mostrar_numero
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
        # Zancada: la fase de carrera avanza con los pasos dados.
        self.fase += math.hypot(dx, dy) * 0.11
        self._impulso = 1.0
        acotar_posicion(self.pos, self.RADIO)
        self.actualizar_rect()

    # --------------------------------------------------
    # Animaciones
    # --------------------------------------------------

    def saltar(self, duracion: float = 0.8) -> None:
        """Salta durante ``duracion`` segundos (celebraciones y remates)."""
        self.salto_total = duracion
        self.salto_restante = duracion

    def caer(self, duracion: float = 0.7) -> None:
        """Cae al suelo durante ``duracion`` segundos y se levanta."""
        self.caida_total = duracion
        self.caida_restante = duracion

    def avanzar_animacion(self, dt: float) -> None:
        """Hace correr los temporizadores de salto, caída e impulso."""
        self._impulso = max(0.0, self._impulso - 3.0 * dt)

        if self.salto_restante > 0.0:
            self.salto_restante = max(0.0, self.salto_restante - dt)

        if self.caida_restante > 0.0:
            self.caida_restante = max(0.0, self.caida_restante - dt)

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
        dy = 0.0
        angulo = 0.0

        if self.caida_restante > 0.0:
            # La caída: tumbado un instante y de pie de nuevo.
            progreso = 1.0 - self.caida_restante / self.caida_total
            angulo = 72.0 * math.sin(math.pi * progreso)
        else:
            if self.salto_restante > 0.0:
                progreso = 1.0 - self.salto_restante / self.salto_total
                dy -= ALTURA_SALTO * math.sin(math.pi * progreso)

            # Zancada: rebote al correr, apagándose al detenerse.
            dy -= abs(math.sin(self.fase)) * 3.0 * self._impulso

        if angulo:
            sprite = pygame.transform.rotate(sprite, angulo)

        superficie.blit(sprite, self.rect_sprite.move(0, round(dy)))

    def _obtener_sprite(self) -> pygame.Surface:
        clave = (
            self.equipo,
            self.tiene_balon,
            self.numero,
            self.uniforme,
            self.mostrar_numero,
        )
        sprite = self._sprites.get(clave)

        if sprite is None:
            sprite = self._crear_sprite()
            self._sprites[clave] = sprite

        return sprite

    @classmethod
    def limpiar_cache(cls) -> None:
        """Descarta los sprites guardados.

        Los sprites se convierten al formato de la pantalla; si pygame se
        reinicia (por ejemplo entre pruebas) las superficies antiguas
        dejan de ser válidas. La vista llama a este método al arrancar
        para reconstruirlos con el nuevo contexto gráfico.
        """
        cls._sprites.clear()

    def _crear_sprite(self) -> pygame.Surface:
        lado = (self.RADIO + self.MARGEN_SPRITE) * 2
        sprite = pygame.Surface((lado, lado), pygame.SRCALPHA)
        centro = (lado // 2, lado // 2)

        dibujar_jugador_uniforme(
            sprite,
            centro,
            self.uniforme,
            numero=self.numero if self.mostrar_numero else None,
        )

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


def _fichas_normalizadas(
    equipo: Equipo,
    fichas: tuple[JugadorPlantilla, ...] | None,
) -> tuple[JugadorPlantilla, ...]:
    """Devuelve once fichas válidas para ``equipo``.

    La normalización (completar, recortar y sanear atributos) vive en
    :func:`plantilla.normalizar_plantilla`, compartida con el guardado y
    el editor: así una plantilla corta o dañada nunca deja el campo a
    medias ni con valores imposibles.
    """
    return normalizar_plantilla(fichas, equipo)


def crear_jugador_de_ficha(
    equipo: Equipo,
    ficha: JugadorPlantilla,
    uniforme: Uniforme | None = None,
    mostrar_numero: bool = True,
) -> Jugador:
    """Crea el ``Jugador`` en campo que corresponde a una ficha.

    La posición ``x`` de la ficha mira desde el arco propio: el
    visitante se refleja, igual que al crear la plantilla entera. Se
    usa tanto al armar los equipos como al meter a un suplente.
    """
    uniforme_efectivo = (
        uniforme
        if uniforme is not None
        else UNIFORMES_POR_DEFECTO[equipo]
    )
    fraccion_x = ficha.x if equipo is Equipo.LOCAL else 1.0 - ficha.x
    x = CAMPO_RECT.left + fraccion_x * CAMPO_RECT.width
    y = CAMPO_RECT.top + ficha.y * CAMPO_RECT.height

    return Jugador(
        equipo,
        ficha.rol,
        x,
        y,
        numero=ficha.dorsal,
        uniforme=uniforme_efectivo,
        mostrar_numero=mostrar_numero,
        nombre=ficha.nombre,
        factor_velocidad=ficha.factor_velocidad,
        factor_fuerza=ficha.factor_fuerza,
    )


def crear_jugadores(
    uniformes: dict[Equipo, Uniforme] | None = None,
    mostrar_numeros: bool = True,
    plantillas: dict[Equipo, tuple[JugadorPlantilla, ...]] | None = None,
) -> list[Jugador]:
    """Crea los 22 jugadores (11 por equipo) a partir de la plantilla.

    Cada equipo recibe su uniforme y las fichas de su plantilla (nombre,
    dorsal, rol, posición y atributos). Sin plantilla se usa la formación
    base con dorsales del 1 al 11; una plantilla incompleta se completa
    con fichas por defecto en vez de dejar huecos en el campo.
    """
    jugadores: list[Jugador] = []

    for equipo in (Equipo.LOCAL, Equipo.VISITANTE):
        uniforme = (uniformes or UNIFORMES_POR_DEFECTO).get(
            equipo,
            UNIFORMES_POR_DEFECTO[equipo],
        )
        for ficha in _fichas_normalizadas(
            equipo,
            (plantillas or {}).get(equipo),
        ):
            jugadores.append(
                crear_jugador_de_ficha(
                    equipo,
                    ficha,
                    uniforme,
                    mostrar_numeros,
                )
            )

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


class SalidaBalon(NamedTuple):
    """Lo que ocurre cuando el balón alcanza un borde del campo.

    ``gol`` es el equipo que anota si el balón entró en una portería y
    ``esquina`` el que cobra el saque de esquina si salió por la línea
    de fondo tras tocar al equipo defensor.
    """

    gol: Equipo | None = None
    esquina: Equipo | None = None


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

    def actualizar_conducido(self, portador: Jugador) -> SalidaBalon:
        """Pega el balón delante del jugador que lo conduce.

        Devuelve la salida del balón: conduce también puede acabar en
        gol (o autogol); sin gol, lo mantiene dentro del campo.
        """
        self.pos.update(
            portador.pos.x + portador.direccion.x * DISTANCIA_CONDUCCION,
            portador.pos.y + portador.direccion.y * DISTANCIA_CONDUCCION,
        )
        self.vel.update(0.0, 0.0)

        gol = equipo_que_anota(self.pos.x, self.pos.y)

        if gol is None:
            acotar_posicion(self.pos, self.RADIO)

        return SalidaBalon(gol=gol)

    def actualizar_libre(
        self,
        dt: float,
        intentar_recoger: Callable[[], bool],
        friccion: float = FRICCION,
        tocado_por: Equipo | None = None,
        viento: pygame.Vector2 | None = None,
    ) -> SalidaBalon:
        """Física del balón libre, avanzando en subpasos.

        Los subpasos evitan que un balón rápido atraviese a un jugador
        entre dos fotogramas. En cada subpaso: se mueve, roza con el
        césped, rebota en los bordes y puede ser recogido por alguien.
        La fricción la aporta el clima del estadio y el viento empuja
        al balón mientras vuela.

        Devuelve la salida del balón: gol o córner, si los hubo.
        """
        velocidad = self.vel.length()
        pasos = max(
            1,
            math.ceil(velocidad * dt / PASO_MAXIMO_BALON),
        )
        dt_paso = dt / pasos
        # La fricción es la misma en todos los subpasos: se calcula
        # una sola vez en lugar de una potencia por subpaso.
        factor_friccion = friccion ** (dt_paso * FPS)
        empuje_viento = (
            viento * dt_paso if viento is not None else pygame.Vector2()
        )

        for _ in range(pasos):
            self.vel += empuje_viento
            self.pos.x += self.vel.x * dt_paso
            self.pos.y += self.vel.y * dt_paso
            self.vel *= factor_friccion
            self._detener_si_va_lento()

            salida = self._rebotar(tocado_por)
            if salida.gol is not None or salida.esquina is not None:
                return salida

            if intentar_recoger():
                return SalidaBalon()

            if self.vel.length_squared() == 0.0:
                break

        return SalidaBalon()

    def _detener_si_va_lento(self) -> None:
        if self.vel.length_squared() < VELOCIDAD_MINIMA_BALON**2:
            self.vel.update(0.0, 0.0)

    def _rebotar(self, tocado_por: Equipo | None) -> SalidaBalon:
        """Rebota en los bordes; en las líneas de fondo puede haber gol
        o, si el último toque fue del equipo defensor, córner."""
        # Bordes superior e inferior.
        if self.pos.y - self.RADIO < CAMPO_RECT.top:
            self.pos.y = CAMPO_RECT.top + self.RADIO
            self.vel.y = abs(self.vel.y)
        elif self.pos.y + self.RADIO > CAMPO_RECT.bottom:
            self.pos.y = CAMPO_RECT.bottom - self.RADIO
            self.vel.y = -abs(self.vel.y)

        # Líneas de gol: gol si entra por la portería; córner si sale
        # tras tocar al defensor; si no, rebote.
        gol = equipo_que_anota(self.pos.x, self.pos.y)
        if gol is not None:
            return SalidaBalon(gol=gol)

        if self.pos.x + self.RADIO >= CAMPO_RECT.right:
            if tocado_por is Equipo.VISITANTE:
                # El visitante defiende su línea: córner para el local.
                return SalidaBalon(esquina=Equipo.LOCAL)

            self.pos.x = CAMPO_RECT.right - self.RADIO
            self.vel.x = -abs(self.vel.x)
        elif self.pos.x - self.RADIO <= CAMPO_RECT.left:
            if tocado_por is Equipo.LOCAL:
                # El local defiende su línea: córner para el visitante.
                return SalidaBalon(esquina=Equipo.VISITANTE)

            self.pos.x = CAMPO_RECT.left + self.RADIO
            self.vel.x = abs(self.vel.x)

        return SalidaBalon()

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
