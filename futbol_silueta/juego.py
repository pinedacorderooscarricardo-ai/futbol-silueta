"""Lógica y estados de la partida."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

import pygame

from .audio import Sonidos
from .configuracion import (
    ALCANCE_POSESION2,
    CAMPO_RECT,
    COOLDOWN_LIBERACION,
    COOLDOWN_ROBO,
    DESPLAZAMIENTO_MARCA,
    DISTANCIA_DISPARO_IA,
    DURACION_GOL,
    DURACION_MITAD,
    DURACION_POSESION_PORTERO,
    ENERGIA_MAXIMA,
    ENERGIA_MINIMA_SPRINT,
    EQUIPOS,
    ESTADOS_ESPERA,
    Estado,
    FACTOR_APUNTADO_DISPARO,
    FACTOR_COLISION,
    FACTOR_POSESION,
    FACTORES_ATAQUE,
    FUERZA_DESPEJE_PORTERO,
    FUERZA_PATEO,
    GASTO_SPRINT,
    ITERACIONES_COLISION,
    OBJETIVO_ATAQUE_IA,
    PASE_FUERZA_FACTOR,
    PASE_FUERZA_MAX,
    PASE_FUERZA_MIN,
    PORTERIA_CENTRO,
    PORTERIA_INFERIOR,
    PORTERIA_SUPERIOR,
    PRESORES_POR_EQUIPO,
    RADIO_ATAJADA,
    RADIO_BALON,
    RADIO_MARCAJE,
    RECARGA_ENERGIA,
    TIEMPO_MINIMO_POSESION_IA,
    VELOCIDAD_IA,
    VELOCIDAD_MINIMA_ATAJADA,
    VELOCIDAD_SPRINT,
    Equipo,
    Rol,
)
from .entidades import (
    Balon,
    Jugador,
    crear_jugadores,
    elegir_delantero_controlado,
)
from .utilidades import acotar, acotar_al_campo, equipo_rival

if TYPE_CHECKING:
    from .vista import Vista


class Juego:
    """Estado y lógica de una partida: posesión, IA, input y marcador."""

    def __init__(self, vista: Vista) -> None:
        self.vista = vista

        self.jugadores: list[Jugador] = []
        self.jugador_controlado: Jugador | None = None

        self.balon = Balon()
        self.portador: Jugador | None = None
        self.liberador: Jugador | None = None

        self.goles_local = 0
        self.goles_visitante = 0
        self.ultimo_gol: Equipo | None = None

        self.tiempo_posesion = 0
        self.tiempo_liberacion = -COOLDOWN_LIBERACION
        self.tiempo_gol = 0
        self.estado = Estado.JUGANDO

        self.mitad = 1
        self.tiempo_restante = float(DURACION_MITAD)
        self.energia_actual = float(ENERGIA_MAXIMA)
        self.sonidos = Sonidos()

        self.reiniciar_jugada(con_silbato=False)

    # --------------------------------------------------
    # Inicio, reinicio y posesión
    # --------------------------------------------------

    def reiniciar_jugada(self, con_silbato: bool = True) -> None:
        """Reinicia posiciones y balón sin tocar el marcador.

        La primera jugada del arranque no suena para no silbar mientras
        el jugador todavía está en el menú principal.
        """
        self.jugadores = crear_jugadores()
        self.jugador_controlado = elegir_delantero_controlado(self.jugadores)

        self.portador = None
        self.liberador = None
        self.tiempo_posesion = 0
        self.tiempo_liberacion = (
            pygame.time.get_ticks() - COOLDOWN_LIBERACION
        )

        self.balon.colocar_en_el_centro()
        self.estado = Estado.JUGANDO

        if con_silbato:
            self.sonidos.silbato()

    def dar_posesion(self, jugador: Jugador) -> None:
        """Da el balón a un jugador y se lo quita a su dueño anterior."""
        if self.portador is not None:
            self.portador.tiene_balon = False

        jugador.tiene_balon = True
        self.portador = jugador
        self.liberador = None
        self.tiempo_posesion = pygame.time.get_ticks()

        if jugador.equipo is Equipo.LOCAL:
            self.jugador_controlado = jugador

    def liberar_posesion(
        self,
        velocidad: pygame.Vector2 | None = None,
    ) -> None:
        """Suelta el balón, opcionalmente con una velocidad inicial."""
        self.liberador = self.portador

        if self.portador is not None:
            self.portador.tiene_balon = False

        self.portador = None
        self.tiempo_liberacion = pygame.time.get_ticks()

        if velocidad is not None:
            self.balon.vel.update(velocidad)

    def _jugador_mas_cercano(
        self,
        punto: pygame.Vector2,
        filtro: Callable[[Jugador], bool] | None = None,
        alcance2: float = ALCANCE_POSESION2,
    ) -> Jugador | None:
        """Jugador más cercano a un punto dentro del alcance indicado."""
        mejor: Jugador | None = None
        mejor_distancia = alcance2

        for jugador in self.jugadores:
            if filtro is not None and not filtro(jugador):
                continue

            distancia = jugador.pos.distance_squared_to(punto)

            if distancia <= mejor_distancia:
                mejor_distancia = distancia
                mejor = jugador

        return mejor

    def _recoger_balon_libre(self) -> bool:
        """Da posesión al jugador que alcance el balón libre, si hay uno.

        Durante el cooldown solo se impide que lo recoja quien lo soltó;
        así un pase corto sí puede llegar a su destinatario y un rival
        puede interceptar un tiro rápido.
        """
        ahora = pygame.time.get_ticks()
        liberador = self.liberador

        if (
            liberador is not None
            and ahora - self.tiempo_liberacion < COOLDOWN_LIBERACION
        ):
            cercano = self._jugador_mas_cercano(
                self.balon.pos,
                lambda jugador: jugador is not liberador,
            )
        else:
            cercano = self._jugador_mas_cercano(self.balon.pos)

        if cercano is None:
            return False

        self.dar_posesion(cercano)
        return True

    def actualizar_posesion(self) -> None:
        """Resuelve quién tiene el balón en este fotograma."""
        if self.portador is None:
            self._recoger_balon_libre()
            return

        if (
            pygame.time.get_ticks() - self.tiempo_posesion
            < COOLDOWN_ROBO
        ):
            return

        portador = self.portador
        rival = self._jugador_mas_cercano(
            self.balon.pos,
            lambda jugador: jugador.equipo is not portador.equipo,
        )

        if rival is not None:
            self.dar_posesion(rival)

    # --------------------------------------------------
    # Pases
    # --------------------------------------------------

    def obtener_receptor_mas_cercano(
        self,
        jugador: Jugador,
    ) -> Jugador | None:
        """Compañero de campo más cercano; el portero solo si no hay otro."""
        mejor: Jugador | None = None
        mejor_distancia = float("inf")

        portero: Jugador | None = None
        mejor_distancia_portero = float("inf")

        for companero in self.jugadores:
            if companero is jugador or companero.equipo is not jugador.equipo:
                continue

            distancia = companero.pos.distance_squared_to(jugador.pos)

            if companero.rol is Rol.PORTERO:
                if distancia < mejor_distancia_portero:
                    mejor_distancia_portero = distancia
                    portero = companero
            elif distancia < mejor_distancia:
                mejor_distancia = distancia
                mejor = companero

        return mejor if mejor is not None else portero

    def pasar_al_companero_mas_cercano(self) -> None:
        """Pasa el balón al compañero de campo más cercano."""
        jugador = self.jugador_controlado

        if jugador is None or not jugador.tiene_balon:
            return

        receptor = self.obtener_receptor_mas_cercano(jugador)

        if receptor is None:
            return

        direccion = receptor.pos - jugador.pos
        distancia = direccion.length()

        if distancia < 1e-6:
            return

        direccion /= distancia
        fuerza = min(
            max(PASE_FUERZA_MIN, distancia * PASE_FUERZA_FACTOR),
            PASE_FUERZA_MAX,
        )

        self.sonidos.pase()
        self.liberar_posesion(direccion * fuerza)

        if receptor.equipo is Equipo.LOCAL:
            self.jugador_controlado = receptor

    # --------------------------------------------------
    # Balón
    # --------------------------------------------------

    def _intentar_atajada(self) -> bool:
        """Atrapa un balón rápido que llega a la zona del portero."""
        if (
            self.balon.vel.length_squared()
            < VELOCIDAD_MINIMA_ATAJADA**2
        ):
            return False

        for jugador in self.jugadores:
            if jugador.rol is not Rol.PORTERO:
                continue

            if (
                jugador.pos.distance_squared_to(self.balon.pos)
                > RADIO_ATAJADA**2
            ):
                continue

            hacia_el_arco = -1.0 if jugador.equipo is Equipo.LOCAL else 1.0
            if self.balon.vel.x * hacia_el_arco <= 0.0:
                continue

            # Mira hacia el campo para que el balón quede delante suyo.
            jugador.direccion.update(hacia_el_arco * -1.0, 0.0)
            self.dar_posesion(jugador)
            return True

        return False

    def _intentar_recoger_o_atajar(self) -> bool:
        """Primero prueba la atajada; si no, la recogida normal."""
        return self._intentar_atajada() or self._recoger_balon_libre()

    def actualizar_balon(self, dt: float) -> None:
        """Actualiza el balón y registra el gol, si lo hay."""
        if self.portador is not None:
            gol = self.balon.actualizar_conducido(self.portador)
        else:
            gol = self.balon.actualizar_libre(
                dt,
                self._intentar_recoger_o_atajar,
            )

        if gol is not None:
            self.marcar_gol(gol)

    def _chutar(self, direccion: pygame.Vector2) -> None:
        """Suelta el balón con la fuerza de un disparo en ``direccion``."""
        if direccion.length_squared() < 1e-6:
            return

        direccion = direccion.normalize()
        self.sonidos.disparo()
        self.liberar_posesion(direccion * FUERZA_PATEO)

    # --------------------------------------------------
    # IA
    # --------------------------------------------------

    def actualizar_ia(self, dt: float) -> None:
        equipo_con_balon = (
            self.portador.equipo if self.portador is not None else None
        )

        perseguidores = self._elegir_perseguidores(equipo_con_balon)
        marcajes = self._asignar_marcajes(equipo_con_balon, perseguidores)

        # El portador visitante decide entre conducir y disparar.
        if (
            self.portador is not None
            and self.portador.equipo is Equipo.VISITANTE
        ):
            self._accion_portador_ia(self.portador, dt)

        # El resto de los 21 jugadores (menos el humano controlado).
        for jugador in self.jugadores:
            if jugador is self.portador:
                continue
            if jugador is self.jugador_controlado:
                continue

            objetivo = self._objetivo_ia(
                jugador,
                equipo_con_balon,
                jugador in perseguidores,
                marcajes.get(jugador),
            )
            jugador.mover_hacia(objetivo, VELOCIDAD_IA, dt)

    def _elegir_perseguidores(
        self,
        equipo_con_balon: Equipo | None,
    ) -> set[Jugador]:
        """Los N jugadores de campo más cercanos al balón de cada equipo.

        El jugador controlado por el humano no ocupa una plaza de presión:
        si está cerca, presiona él mismo y el equipo conserva sus N
        perseguidores de IA.
        """
        perseguidores: set[Jugador] = set()

        for equipo in EQUIPOS:
            if equipo is equipo_con_balon:
                continue

            candidatos = [
                jugador
                for jugador in self.jugadores
                if jugador.equipo is equipo
                and jugador.rol is not Rol.PORTERO
                and jugador is not self.jugador_controlado
            ]
            candidatos.sort(
                key=lambda jugador: jugador.pos.distance_squared_to(
                    self.balon.pos
                )
            )
            perseguidores.update(candidatos[:PRESORES_POR_EQUIPO])

        return perseguidores

    def _asignar_marcajes(
        self,
        equipo_con_balon: Equipo | None,
        perseguidores: set[Jugador],
    ) -> dict[Jugador, Jugador]:
        """Asigna a cada defensa un rival distinto de su zona."""
        if equipo_con_balon is None:
            return {}

        equipo_defensor = equipo_rival(equipo_con_balon)
        defensas = [
            jugador
            for jugador in self.jugadores
            if jugador.equipo is equipo_defensor
            and jugador.rol is Rol.DEFENSA
            and jugador is not self.jugador_controlado
            and jugador not in perseguidores
        ]
        atacantes = [
            jugador
            for jugador in self.jugadores
            if jugador.equipo is not equipo_defensor
            and jugador.rol is not Rol.PORTERO
            and jugador is not self.portador
        ]

        disponibles = set(atacantes)
        asignaciones: dict[Jugador, Jugador] = {}
        radio2 = RADIO_MARCAJE**2

        for defensor in sorted(
            defensas,
            key=lambda jugador: jugador.posicion_base.y,
        ):
            candidatos = [
                atacante
                for atacante in disponibles
                if atacante.pos.distance_squared_to(defensor.posicion_base)
                <= radio2
            ]

            if not candidatos:
                continue

            marcado = min(
                candidatos,
                key=lambda atacante: atacante.pos.distance_squared_to(
                    defensor.posicion_base
                ),
            )
            asignaciones[defensor] = marcado
            disponibles.remove(marcado)

        return asignaciones

    def _despejar_portero(self, portero: Jugador) -> None:
        """Pase largo del portero IA al compañero más cercano."""
        companeros = [
            jugador
            for jugador in self.jugadores
            if jugador.equipo is portero.equipo
            and jugador.rol is not Rol.PORTERO
        ]

        if companeros:
            receptor = min(
                companeros,
                key=lambda jugador: jugador.pos.distance_squared_to(
                    portero.pos
                ),
            )
            direccion = receptor.pos - portero.pos
        else:
            direccion = pygame.Vector2(
                CAMPO_RECT.centerx - portero.pos.x,
                PORTERIA_CENTRO - portero.pos.y,
            )

        if direccion.length_squared() < 1e-6:
            return

        direccion.normalize_ip()
        self.sonidos.pase()
        self.liberar_posesion(direccion * FUERZA_DESPEJE_PORTERO)

    def _accion_portador_ia(self, jugador: Jugador, dt: float) -> None:
        """Conduce hacia el arco o dispara si ya está en zona de tiro."""
        if jugador.rol is Rol.PORTERO:
            # El portero IA no se va de dribling: aguanta y despeja.
            jugador.mover_hacia(
                jugador.posicion_base,
                VELOCIDAD_IA,
                dt,
            )
            if (
                pygame.time.get_ticks() - self.tiempo_posesion
                >= DURACION_POSESION_PORTERO
            ):
                self._despejar_portero(jugador)
            return

        distancia = math.hypot(
            jugador.pos.x - CAMPO_RECT.left,
            jugador.pos.y - PORTERIA_CENTRO,
        )
        tiempo_con_balon = (
            pygame.time.get_ticks() - self.tiempo_posesion
        )

        if (
            distancia <= DISTANCIA_DISPARO_IA
            and tiempo_con_balon >= TIEMPO_MINIMO_POSESION_IA
        ):
            self._disparar_ia(jugador)
            return

        jugador.mover_hacia(
            OBJETIVO_ATAQUE_IA,
            VELOCIDAD_IA * FACTOR_POSESION,
            dt,
        )

    def _disparar_ia(self, jugador: Jugador) -> None:
        """Dispara la IA hacia el lado abierto del arco local."""
        objetivo = self._objetivo_para_disparo_ia(jugador)
        self._chutar(objetivo - jugador.pos)

    def _objetivo_para_disparo_ia(
        self,
        jugador: Jugador,
    ) -> pygame.Vector2:
        """Punto del arco visitante al lado opuesto al portero local."""
        portero = next(
            (
                otro
                for otro in self.jugadores
                if otro.equipo is Equipo.LOCAL
                and otro.rol is Rol.PORTERO
            ),
            None,
        )

        if (
            portero is None
            or abs(portero.pos.y - PORTERIA_CENTRO) < 12.0
        ):
            # Portero centrado: buscar el palo más lejano al tirador.
            lado = 1.0 if jugador.pos.y <= PORTERIA_CENTRO else -1.0
        else:
            lado = 1.0 if portero.pos.y < PORTERIA_CENTRO else -1.0

        margen = RADIO_BALON
        medio_arco = (
            PORTERIA_INFERIOR - PORTERIA_SUPERIOR
        ) / 2.0 - margen
        y = PORTERIA_CENTRO + lado * medio_arco * FACTOR_APUNTADO_DISPARO
        y = acotar(
            y,
            PORTERIA_SUPERIOR + margen,
            PORTERIA_INFERIOR - margen,
        )

        return pygame.Vector2(CAMPO_RECT.left, y)

    def _objetivo_ia(
        self,
        jugador: Jugador,
        equipo_con_balon: Equipo | None,
        persigue: bool,
        marcado: Jugador | None = None,
    ) -> pygame.Vector2:
        """Punto al que un jugador IA quiere moverse este frame."""
        if jugador.rol is Rol.PORTERO:
            return self._objetivo_portero(jugador)

        base = jugador.posicion_base
        ataca = equipo_con_balon is jugador.equipo

        if persigue:
            objetivo = self.balon.pos.copy()
        elif marcado is not None:
            # Colocarse entre el rival marcado y el arco propio.
            signo = -1.0 if jugador.equipo is Equipo.LOCAL else 1.0
            objetivo = pygame.Vector2(
                marcado.pos.x + signo * DESPLAZAMIENTO_MARCA,
                marcado.pos.y,
            )
        elif ataca:
            fx, fy = FACTORES_ATAQUE.get(jugador.rol, (0.1, 0.15))
            objetivo = pygame.Vector2(
                base.x + (self.balon.pos.x - base.x) * fx,
                base.y + (self.balon.pos.y - base.y) * fy,
            )
        else:
            objetivo = base.copy()

        return acotar_al_campo(objetivo, jugador.RADIO)

    def _objetivo_portero(self, jugador: Jugador) -> pygame.Vector2:
        """El portero se desplaza lateralmente siguiendo la Y del balón."""
        signo = 1 if jugador.equipo is Equipo.LOCAL else -1
        x = jugador.posicion_base.x + signo * 5
        y = acotar(
            self.balon.pos.y,
            PORTERIA_SUPERIOR - 20,
            PORTERIA_INFERIOR + 20,
        )
        return pygame.Vector2(x, y)

    # --------------------------------------------------
    # Colisiones
    # --------------------------------------------------

    def _resolver_colisiones(self) -> None:
        """Separa suavemente a los jugadores que se superponen."""
        for _ in range(ITERACIONES_COLISION):
            for indice, jugador_a in enumerate(self.jugadores):
                for jugador_b in self.jugadores[indice + 1:]:
                    delta = jugador_b.pos - jugador_a.pos
                    distancia2 = delta.length_squared()
                    minima = jugador_a.RADIO + jugador_b.RADIO

                    if distancia2 >= minima * minima:
                        continue

                    if distancia2 < 1e-12:
                        normal = pygame.Vector2(1.0, 0.0)
                        distancia = 0.0
                    else:
                        distancia = math.sqrt(distancia2)
                        normal = delta / distancia

                    empuje = (
                        (minima - distancia) * FACTOR_COLISION * 0.5
                    )
                    jugador_a.empujar(
                        -normal.x * empuje,
                        -normal.y * empuje,
                    )
                    jugador_b.empujar(
                        normal.x * empuje,
                        normal.y * empuje,
                    )

    # --------------------------------------------------
    # Jugador humano
    # --------------------------------------------------

    def actualizar_jugador(
        self,
        dt: float,
        teclas: Sequence[bool],
    ) -> None:
        """Mueve al jugador controlado y gestiona su energía."""
        control = self.jugador_controlado

        if control is None:
            return

        dx = 0
        dy = 0

        if teclas[pygame.K_w] or teclas[pygame.K_UP]:
            dy -= 1
        if teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
            dy += 1
        if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
            dx -= 1
        if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
            dx += 1

        movimiento = pygame.Vector2(dx, dy)

        if movimiento.length_squared() == 0.0:
            self._recargar_energia(dt)
            return

        movimiento.normalize_ip()

        if self._quiere_sprintar(teclas):
            self.energia_actual = max(
                0.0,
                self.energia_actual - GASTO_SPRINT * dt,
            )
            velocidad = control.velocidad_efectiva() * VELOCIDAD_SPRINT
        else:
            self._recargar_energia(dt)
            velocidad = control.velocidad_efectiva()

        control.mover(
            movimiento.x * velocidad * dt,
            movimiento.y * velocidad * dt,
        )

    def _quiere_sprintar(self, teclas: Sequence[bool]) -> bool:
        """True si se pide sprint y queda energía suficiente."""
        if self.energia_actual < ENERGIA_MINIMA_SPRINT:
            return False

        return bool(teclas[pygame.K_LSHIFT] or teclas[pygame.K_RSHIFT])

    def _recargar_energia(self, dt: float) -> None:
        """Recupera energía mientras no se está sprintando."""
        self.energia_actual = min(
            float(ENERGIA_MAXIMA),
            self.energia_actual + RECARGA_ENERGIA * dt,
        )

    def _disparar_humano(self) -> None:
        """Chuta el balón en la dirección de mirada del jugador."""
        control = self.jugador_controlado

        if control is None or self.portador is not control:
            return

        self._chutar(control.direccion)

    # --------------------------------------------------
    # Goles, eventos y bucle principal
    # --------------------------------------------------

    def marcar_gol(self, equipo: Equipo) -> None:
        """Registra un gol y pasa al estado de celebración."""
        if self.portador is not None:
            self.portador.tiene_balon = False

        self.portador = None
        self.liberador = None
        self.ultimo_gol = equipo

        if equipo is Equipo.LOCAL:
            self.goles_local += 1
        else:
            self.goles_visitante += 1

        self.estado = Estado.GOL
        self.tiempo_gol = pygame.time.get_ticks()
        self.sonidos.gol()

    def actualizar(self, dt: float) -> None:
        """Avanza la simulación un fotograma."""
        if self.estado in ESTADOS_ESPERA:
            return

        if self.estado is Estado.GOL:
            if pygame.time.get_ticks() - self.tiempo_gol >= DURACION_GOL:
                self.reiniciar_jugada()
            return

        self.tiempo_restante -= dt * 1000.0

        if self.tiempo_restante <= 0.0:
            self.tiempo_restante = 0.0
            self._terminar_mitad()
            return

        self.actualizar_jugador(dt, pygame.key.get_pressed())
        self.actualizar_ia(dt)
        self._resolver_colisiones()
        self.actualizar_balon(dt)

        # Si se marcó gol, actualizar_balon ya cambió el estado.
        if self.estado is Estado.JUGANDO:
            self.actualizar_posesion()

    def _terminar_mitad(self) -> None:
        """Detiene el juego al final del primer o segundo tiempo."""
        self.estado = (
            Estado.ENTRETIEMPO if self.mitad == 1 else Estado.FINAL
        )

    def _empezar_segunda_mitad(self) -> None:
        """Prepara el segundo tiempo tras el descanso."""
        self.mitad = 2
        self.tiempo_restante = float(DURACION_MITAD)
        self.energia_actual = float(ENERGIA_MAXIMA)
        self.reiniciar_jugada()

    def nueva_partida(self, con_silbato: bool = True) -> None:
        """Empieza una partida desde cero, conservando la misma ventana."""
        self._reiniciar_partido(con_silbato=con_silbato)

    def _reiniciar_partido(self, con_silbato: bool = True) -> None:
        """Reinicia el marcador y el reloj para una revancha."""
        self.goles_local = 0
        self.goles_visitante = 0
        self.ultimo_gol = None
        self.mitad = 1
        self.tiempo_restante = float(DURACION_MITAD)
        self.energia_actual = float(ENERGIA_MAXIMA)
        self.reiniciar_jugada(con_silbato=con_silbato)

    def procesar_tecla(self, tecla: int) -> None:
        """Reacciona a una tecla pulsada durante el partido."""
        if tecla == pygame.K_SPACE:
            self._al_pulsar_espacio()
        elif tecla == pygame.K_e and self.estado is Estado.JUGANDO:
            self.pasar_al_companero_mas_cercano()

    def _al_pulsar_espacio(self) -> None:
        """ESPACIO: chutar, continuar tras un gol o pasar de tiempo."""
        if self.estado is Estado.GOL:
            self.reiniciar_jugada()
        elif self.estado is Estado.ENTRETIEMPO:
            self._empezar_segunda_mitad()
        elif self.estado is Estado.FINAL:
            self._reiniciar_partido()
        elif self.estado is Estado.JUGANDO:
            self._disparar_humano()
