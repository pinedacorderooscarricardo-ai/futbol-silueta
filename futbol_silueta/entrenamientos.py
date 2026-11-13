"""Entrenamientos con recompensa: tiros, penales y dos contra uno.

Los tres ejercicios comparten una cancha reducida y un portero rival.
Cada sesión termina con una meta de goles: al cumplirla se entregan
monedas para la tienda de estadios. El módulo es independiente del motor
de partido para que las reglas del entrenamiento puedan ser distintas
(sin reloj de 90 minutos, sin faltas y con reinicios rápidos).
"""

from __future__ import annotations

import random
from enum import StrEnum
from typing import NamedTuple

import pygame

from .configuracion import (
    ALTO,
    AMARILLO,
    ANCHO,
    BLANCO,
    CAMPO_RECT,
    DISTANCIA_CONDUCCION,
    FRICCION,
    NEGRO,
    PORTERIA_CENTRO,
    PORTERIA_INFERIOR,
    PORTERIA_SUPERIOR,
    RADIO_BALON,
    RADIO_JUGADOR,
    ROJO_ENERGIA,
    VERDE_ENERGIA,
    Color,
    Equipo,
    Rol,
)
from .entidades import Balon, Jugador
from .estadios import ESTADIO_POR_DEFECTO, Estadio, crear_fondo_estadio
from .uniformes import UNIFORMES_POR_DEFECTO, Uniforme
from .utilidades import CacheTextos, acotar, acotar_posicion


class TipoEntrenamiento(StrEnum):
    """Ejercicios disponibles en el centro de entrenamiento."""

    TIROS = "tiros"
    PENALES = "penales"
    DOS_CONTRA_UNO = "dos_contra_uno"


class FaseEntrenamiento(StrEnum):
    """Estados internos de una sesión."""

    JUGANDO = "jugando"
    RESULTADO = "resultado"
    FINAL = "final"


class DefinicionEntrenamiento(NamedTuple):
    """Reglas y recompensa de un ejercicio."""

    tipo: TipoEntrenamiento
    nombre: str
    descripcion: str
    intentos: int
    objetivo: int
    recompensa: int
    monedas_por_gol: int


ENTRENAMIENTOS: tuple[DefinicionEntrenamiento, ...] = (
    DefinicionEntrenamiento(
        TipoEntrenamiento.TIROS,
        "Tiros a puerta",
        "8 disparos desde media distancia: marca al menos 4 goles.",
        8,
        4,
        40,
        8,
    ),
    DefinicionEntrenamiento(
        TipoEntrenamiento.PENALES,
        "Penales",
        "5 penales con portero: acierta 3 o más para llevarte el premio.",
        5,
        3,
        60,
        12,
    ),
    DefinicionEntrenamiento(
        TipoEntrenamiento.DOS_CONTRA_UNO,
        "Dos contra uno",
        "5 ataques con un compañero: supera al defensor y marca 3 goles.",
        5,
        3,
        80,
        15,
    ),
)


def definicion_entrenamiento(
    tipo: TipoEntrenamiento,
) -> DefinicionEntrenamiento:
    """Definición del ejercicio pedido."""
    for definicion in ENTRENAMIENTOS:
        if definicion.tipo is tipo:
            return definicion

    return ENTRENAMIENTOS[0]


# Movimiento del jugador y del balón durante el entrenamiento.
VELOCIDAD_CONTROL = 225.0
VELOCIDAD_SPRINT = 315.0
VELOCIDAD_DISPARO = 760.0
VELOCIDAD_PENAL = 840.0
VELOCIDAD_PASE = 540.0
VELOCIDAD_PORTERO = 205.0
VELOCIDAD_DEFENSOR = 165.0
TIEMPO_RESULTADO = 1.15
LIMITE_TIROS = 12.0
LIMITE_PENALES = 15.0
LIMITE_DOS_CONTRA_UNO = 15.0
MARGEN_PALO = 14.0


class SesionEntrenamiento:
    """Una sesión jugable de tiros, penales o dos contra uno."""

    def __init__(
        self,
        tipo: TipoEntrenamiento,
        estadio: Estadio = ESTADIO_POR_DEFECTO,
        uniformes: dict[Equipo, Uniforme] | None = None,
        mostrar_numeros: bool = True,
        monedas: int = 0,
    ) -> None:
        self.tipo = tipo
        self.definicion = definicion_entrenamiento(tipo)
        self.estadio = estadio
        self.uniformes = dict(uniformes or UNIFORMES_POR_DEFECTO)
        self.mostrar_numeros = mostrar_numeros
        self.monedas = max(0, int(monedas))

        self.fase = FaseEntrenamiento.JUGANDO
        self.intento = 1
        self.goles = 0
        self.tiros = 0
        self.exito = False
        self.recompensa = 0
        self.texto_resultado = ""

        self._tiempo_intento = 0.0
        self._tiempo_resultado = 0.0
        self._tiempo_libre = 0.0
        self._ultimo_intento = False
        self._objetivo_y = float(PORTERIA_CENTRO)
        self._pase_en_curso = False
        self._receptor: Jugador | None = None

        self.balon = Balon()
        self._portero = Jugador(
            Equipo.VISITANTE,
            Rol.PORTERO,
            CAMPO_RECT.right - 18,
            PORTERIA_CENTRO,
            numero=1,
            uniforme=self.uniformes[Equipo.VISITANTE],
            mostrar_numero=mostrar_numeros,
        )
        self._jugador = Jugador(
            Equipo.LOCAL,
            Rol.DELANTERO,
            CAMPO_RECT.centerx,
            CAMPO_RECT.centery,
            numero=9,
            uniforme=self.uniformes[Equipo.LOCAL],
            mostrar_numero=mostrar_numeros,
        )
        self._companero = Jugador(
            Equipo.LOCAL,
            Rol.DELANTERO,
            CAMPO_RECT.centerx,
            CAMPO_RECT.centery,
            numero=10,
            uniforme=self.uniformes[Equipo.LOCAL],
            mostrar_numero=mostrar_numeros,
        )
        self._defensor = Jugador(
            Equipo.VISITANTE,
            Rol.DEFENSA,
            CAMPO_RECT.centerx,
            CAMPO_RECT.centery,
            numero=4,
            uniforme=self.uniformes[Equipo.VISITANTE],
            mostrar_numero=mostrar_numeros,
        )
        self._portador: Jugador | None = None
        self.controlado = self._jugador

        self.fuente_titulo = pygame.font.SysFont("Arial", 30, bold=True)
        self.fuente_hud = pygame.font.SysFont("Arial", 19, bold=True)
        self.fuente_pequena = pygame.font.SysFont("Arial", 16)
        self.fuente_resultado = pygame.font.SysFont("Arial", 54, bold=True)
        self.fuente_final = pygame.font.SysFont("Arial", 30, bold=True)
        self._texto = CacheTextos()
        self._fondo = self._crear_fondo(estadio)

        self.reiniciar()

    # --------------------------------------------------
    # Estado de la sesión
    # --------------------------------------------------

    @property
    def terminado(self) -> bool:
        """True cuando ya se jugaron todos los intentos."""
        return self.fase is FaseEntrenamiento.FINAL

    @property
    def monedas_ganadas(self) -> int:
        """Monedas que entrega la sesión; solo paga si se cumple la meta."""
        if self.goles < self.definicion.objetivo:
            return 0

        return (
            self.definicion.recompensa
            + self.definicion.monedas_por_gol * self.goles
        )

    def reiniciar(self) -> None:
        """Vuelve a empezar la sesión desde el primer intento."""
        self.fase = FaseEntrenamiento.JUGANDO
        self.intento = 1
        self.goles = 0
        self.tiros = 0
        self.exito = False
        self.recompensa = 0
        self.texto_resultado = ""
        self._preparar_intento()

    def _preparar_intento(self) -> None:
        """Coloca a los protagonistas según el ejercicio elegido."""
        self.fase = FaseEntrenamiento.JUGANDO
        self._tiempo_intento = 0.0
        self._tiempo_resultado = 0.0
        self._tiempo_libre = 0.0
        self.texto_resultado = ""
        self._pase_en_curso = False
        self._receptor = None
        self._ultimo_intento = self.intento >= self.definicion.intentos
        self._soltar_balon()

        for jugador in (self._jugador, self._companero, self._defensor):
            jugador.tiene_balon = False
            jugador.caida_restante = 0.0
            jugador.salto_restante = 0.0

        centro_porteria = float(PORTERIA_CENTRO)
        self._colocar(self._portero, CAMPO_RECT.right - 18, centro_porteria)
        self._portero.direccion.update(-1.0, 0.0)
        self.balon.vel.update(0.0, 0.0)

        if self.tipo is TipoEntrenamiento.TIROS:
            x = random.uniform(
                CAMPO_RECT.left + CAMPO_RECT.width * 0.42,
                CAMPO_RECT.right - 250,
            )
            y = random.uniform(centro_porteria - 150, centro_porteria + 150)
            self._colocar(self._jugador, x, y)
            self._dar_balon(self._jugador)
        elif self.tipo is TipoEntrenamiento.PENALES:
            punto = CAMPO_RECT.right - 150
            self._colocar(self._jugador, punto - 34, centro_porteria)
            self._objetivo_y = centro_porteria
            self.balon.pos.update(punto, centro_porteria)
            self.balon.vel.update(0.0, 0.0)
        else:
            y = random.uniform(centro_porteria - 70, centro_porteria + 70)
            self._colocar(self._jugador, CAMPO_RECT.right - 320, y)
            lado = random.choice((-1.0, 1.0))
            self._colocar(
                self._companero,
                CAMPO_RECT.right - 405,
                acotar(
                    centro_porteria + lado * random.uniform(80, 135),
                    CAMPO_RECT.top + 40,
                    CAMPO_RECT.bottom - 40,
                ),
            )
            self._colocar(
                self._defensor,
                CAMPO_RECT.right - 215,
                centro_porteria + random.uniform(-55, 55),
            )
            self._defensor.direccion.update(-1.0, 0.0)
            self._dar_balon(self._jugador)

    # --------------------------------------------------
    # Entrada
    # --------------------------------------------------

    def procesar_tecla(self, tecla: int) -> None:
        """Atiende una tecla pulsada durante la sesión."""
        if self.fase is FaseEntrenamiento.RESULTADO:
            self._tiempo_resultado = 0.0
            return

        if self.fase is not FaseEntrenamiento.JUGANDO:
            return

        if tecla == pygame.K_SPACE:
            self._chutar()
        elif (
            tecla in (pygame.K_e, pygame.K_RETURN, pygame.K_KP_ENTER)
            and self.tipo is TipoEntrenamiento.DOS_CONTRA_UNO
        ):
            self._pasar()

    # --------------------------------------------------
    # Simulación
    # --------------------------------------------------

    def actualizar(self, dt: float) -> None:
        """Avanza la sesión un fotograma."""
        self._avanzar_animaciones(dt)

        if self.fase is FaseEntrenamiento.FINAL:
            return

        if self.fase is FaseEntrenamiento.RESULTADO:
            self._tiempo_resultado -= dt

            if self._tiempo_resultado <= 0.0:
                if self._ultimo_intento:
                    self._finalizar()
                else:
                    self.intento += 1
                    self._preparar_intento()

            return

        self._tiempo_intento += dt

        if self._tiempo_intento > self._limite_tiempo():
            self._terminar_intento("SE ACABÓ EL TIEMPO", False)
            return

        if self.tipo is TipoEntrenamiento.PENALES:
            self._actualizar_penal(dt)
        else:
            self._actualizar_juego_libre(dt)

    def _limite_tiempo(self) -> float:
        if self.tipo is TipoEntrenamiento.TIROS:
            return LIMITE_TIROS

        if self.tipo is TipoEntrenamiento.PENALES:
            return LIMITE_PENALES

        return LIMITE_DOS_CONTRA_UNO

    def _actualizar_penal(self, dt: float) -> None:
        """Apunta con las flechas y deja el disparo para ESPACIO."""
        teclas = pygame.key.get_pressed()
        paso = 0.0

        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            paso -= 150.0 * dt
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            paso += 150.0 * dt
        if teclas[pygame.K_UP] or teclas[pygame.K_w]:
            paso -= 110.0 * dt
        if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            paso += 110.0 * dt

        self._objetivo_y = acotar(
            self._objetivo_y + paso,
            PORTERIA_SUPERIOR + MARGEN_PALO,
            PORTERIA_INFERIOR - MARGEN_PALO,
        )
        self._jugador.direccion.update(
            (CAMPO_RECT.right - self.balon.pos.x),
            (self._objetivo_y - self.balon.pos.y),
        )
        if self._jugador.direccion.length_squared() > 0.0:
            self._jugador.direccion.normalize_ip()

        self._mover_portero(dt)

        if self.balon.vel.length_squared() > 0.0:
            self._avanzar_balon(dt)

        self._comprobar_balon(dt)

    def _actualizar_juego_libre(self, dt: float) -> None:
        """Movimiento, compañero, defensor y física del balón."""
        self._mover_controlado(dt)

        for apoyo in (self._jugador, self._companero):
            if (
                apoyo is not self.controlado
                and self.tipo is TipoEntrenamiento.DOS_CONTRA_UNO
            ):
                self._mover_apoyo(apoyo, dt)

        if self.tipo is TipoEntrenamiento.DOS_CONTRA_UNO:
            self._mover_defensor(dt)

        self._mover_portero(dt)

        if self._portador is not None and self._portador.tiene_balon:
            portador = self._portador
            self.balon.pos.update(
                portador.pos.x + portador.direccion.x * DISTANCIA_CONDUCCION,
                portador.pos.y + portador.direccion.y * DISTANCIA_CONDUCCION,
            )
            self._tiempo_libre = 0.0
        else:
            self._avanzar_balon(dt)

            if self._pase_en_curso and self._receptor is not None:
                distancia = self.balon.pos.distance_to(self._receptor.pos)

                if distancia <= RADIO_JUGADOR + RADIO_BALON + 5:
                    self._dar_balon(self._receptor)
                    self._pase_en_curso = False
                    self._receptor = None

        self._comprobar_robo()
        self._comprobar_balon(dt)

    def _mover_controlado(self, dt: float) -> None:
        """WASD o flechas: movimiento con sprint opcional."""
        teclas = pygame.key.get_pressed()
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

        if dx == 0 and dy == 0:
            return

        direccion = pygame.Vector2(dx, dy)
        direccion.normalize_ip()
        velocidad = (
            VELOCIDAD_SPRINT
            if teclas[pygame.K_LSHIFT] or teclas[pygame.K_RSHIFT]
            else VELOCIDAD_CONTROL
        )
        self.controlado.mover(
            direccion.x * velocidad * dt,
            direccion.y * velocidad * dt,
        )

    def _mover_apoyo(self, jugador: Jugador, dt: float) -> None:
        """El compañero (o el atacante libre) se abre para recibir."""
        objetivo_y = acotar(
            self.balon.pos.y
            + (85.0 if jugador.pos.y < self.balon.pos.y else -85.0),
            CAMPO_RECT.top + 50,
            CAMPO_RECT.bottom - 50,
        )
        objetivo = pygame.Vector2(
            min(CAMPO_RECT.right - 150, self.balon.pos.x + 95.0),
            objetivo_y,
        )
        jugador.mover_hacia(objetivo, 175.0, dt)

    def _mover_defensor(self, dt: float) -> None:
        """El defensor persigue el balón y roba si llega a tiempo."""
        self._defensor.mover_hacia(self.balon.pos, VELOCIDAD_DEFENSOR, dt)

    def _mover_portero(self, dt: float) -> None:
        """El portero cubre el centro y se lanza hacia donde va el balón."""
        objetivo_y = float(PORTERIA_CENTRO)

        if self.balon.pos.x > CAMPO_RECT.centerx:
            if self.balon.vel.x > 80.0:
                distancia = max(1.0, CAMPO_RECT.right - self.balon.pos.x)
                tiempo = distancia / self.balon.vel.x
                prediccion = self.balon.pos.y + self.balon.vel.y * tiempo
                objetivo_y = acotar(
                    prediccion,
                    PORTERIA_SUPERIOR + MARGEN_PALO,
                    PORTERIA_INFERIOR - MARGEN_PALO,
                )
            else:
                objetivo_y = acotar(
                    self.balon.pos.y,
                    PORTERIA_SUPERIOR + MARGEN_PALO,
                    PORTERIA_INFERIOR - MARGEN_PALO,
                )

        self._portero.mover_hacia(
            pygame.Vector2(self._portero.pos.x, objetivo_y),
            VELOCIDAD_PORTERO,
            dt,
        )

    def _avanzar_balon(self, dt: float) -> None:
        """Física libre del balón: inercia y rozamiento del césped."""
        self.balon.pos += self.balon.vel * dt
        self.balon.vel *= FRICCION ** (dt * 60.0)

        if self.balon.vel.length_squared() < 25.0:
            self.balon.vel.update(0.0, 0.0)

    # --------------------------------------------------
    # Disparos y pases
    # --------------------------------------------------

    def _chutar(self) -> None:
        if self.tipo is TipoEntrenamiento.PENALES:
            self._chutar_penal()
            return

        portador = self._portador

        if portador is None or portador is not self.controlado:
            return

        direccion = pygame.Vector2(portador.direccion)

        if direccion.length_squared() < 0.01:
            direccion.update(1.0, 0.0)

        direccion.normalize_ip()
        # Asistencia suave: si se mira cerca del arco, el disparo se
        # corrige hacia la portería sin quitarle el control del ángulo.
        hacia_arco = pygame.Vector2(
            CAMPO_RECT.right - 20,
            PORTERIA_CENTRO,
        ) - self.balon.pos

        if hacia_arco.length_squared() > 0.01:
            hacia_arco.normalize_ip()

            if abs(direccion.angle_to(hacia_arco)) < 55.0:
                direccion = direccion.lerp(hacia_arco, 0.35)
                direccion.normalize_ip()

        self._soltar_balon()
        self.balon.vel.update(direccion * VELOCIDAD_DISPARO)
        self._tiempo_libre = 0.0

    def _chutar_penal(self) -> None:
        if self.balon.vel.length_squared() > 0.0:
            return

        objetivo = pygame.Vector2(
            CAMPO_RECT.right - 2,
            self._objetivo_y + random.uniform(-7.0, 7.0),
        )
        direccion = objetivo - self.balon.pos

        if direccion.length_squared() < 0.01:
            return

        direccion.normalize_ip()
        self._soltar_balon()
        self.balon.vel.update(direccion * VELOCIDAD_PENAL)
        self._tiempo_libre = 0.0

    def _pasar(self) -> None:
        portador = self._portador

        if portador is None or portador is not self.controlado:
            return

        receptor = (
            self._companero if portador is self._jugador else self._jugador
        )
        direccion = receptor.pos - self.balon.pos

        if direccion.length_squared() < 0.01:
            return

        direccion.normalize_ip()
        self._soltar_balon()
        self.balon.vel.update(direccion * VELOCIDAD_PASE)
        self._pase_en_curso = True
        self._receptor = receptor
        self._tiempo_libre = 0.0

    # --------------------------------------------------
    # Final de cada intento
    # --------------------------------------------------

    def _comprobar_robo(self) -> None:
        """El defensor corta la jugada si alcanza el balón."""
        if self.tipo is not TipoEntrenamiento.DOS_CONTRA_UNO:
            return

        distancia = self.balon.pos.distance_to(self._defensor.pos)

        if distancia > RADIO_JUGADOR + RADIO_BALON + 5:
            return

        if self.balon.vel.length() > 430.0:
            return

        self._terminar_intento("ROBO DEL DEFENSOR", False)

    def _comprobar_balon(self, dt: float) -> None:
        """Detecta gol, atajada, fuera de banda o balón detenido."""
        if self.fase is not FaseEntrenamiento.JUGANDO:
            return

        if (
            self._portador is None
            and self.balon.vel.length() > 140.0
            and self.balon.pos.x < CAMPO_RECT.right - 8
            and self.balon.pos.distance_to(self._portero.pos)
            <= RADIO_JUGADOR + RADIO_BALON + 8
        ):
            self._terminar_intento("¡ATAJADA DEL PORTERO!", False)
            return

        radio = RADIO_BALON

        if self.balon.pos.x + radio >= CAMPO_RECT.right:
            if (
                PORTERIA_SUPERIOR + radio
                <= self.balon.pos.y
                <= PORTERIA_INFERIOR - radio
            ):
                self._terminar_intento("¡GOL!", True)
            else:
                self._terminar_intento("FUERA", False)

            return

        if self.balon.pos.x - radio <= CAMPO_RECT.left:
            self._terminar_intento("FUERA", False)
            return

        if (
            self.balon.pos.y - radio <= CAMPO_RECT.top
            or self.balon.pos.y + radio >= CAMPO_RECT.bottom
        ):
            self._terminar_intento("FUERA", False)
            return

        if self._portador is None and self.balon.vel.length_squared() < 25.0:
            self._tiempo_libre += dt

            if self._tiempo_libre >= 0.65:
                self._terminar_intento("BALÓN PERDIDO", False)
        else:
            self._tiempo_libre = 0.0

    def _terminar_intento(self, texto: str, gol: bool) -> None:
        """Congela el intento y programa el siguiente o el final."""
        if self.fase is not FaseEntrenamiento.JUGANDO:
            return

        self._soltar_balon()
        self.balon.vel.update(0.0, 0.0)
        self.fase = FaseEntrenamiento.RESULTADO
        self.texto_resultado = texto
        self._tiempo_resultado = TIEMPO_RESULTADO
        self.tiros += 1

        if gol:
            self.goles += 1

        self._ultimo_intento = self.intento >= self.definicion.intentos

    def _finalizar(self) -> None:
        """Cierra la sesión y calcula la recompensa."""
        self.fase = FaseEntrenamiento.FINAL
        self.controlado.tiene_balon = False
        self._portador = None
        self.exito = self.goles >= self.definicion.objetivo
        self.recompensa = self.monedas_ganadas

    # --------------------------------------------------
    # Utilidades internas
    # --------------------------------------------------

    def _dar_balon(self, jugador: Jugador) -> None:
        for otro in (self._jugador, self._companero, self._defensor):
            otro.tiene_balon = False

        jugador.tiene_balon = True
        self._portador = jugador
        self.controlado = jugador
        self.balon.pos.update(
            jugador.pos.x + jugador.direccion.x * DISTANCIA_CONDUCCION,
            jugador.pos.y + jugador.direccion.y * DISTANCIA_CONDUCCION,
        )
        self.balon.vel.update(0.0, 0.0)

    def _soltar_balon(self) -> None:
        if self._portador is not None:
            self._portador.tiene_balon = False

        self._portador = None

    @staticmethod
    def _colocar(jugador: Jugador, x: float, y: float) -> None:
        jugador.pos.update(x, y)
        acotar_posicion(jugador.pos, RADIO_JUGADOR)
        jugador.direccion.update(1.0, 0.0)
        jugador.tiene_balon = False
        jugador.actualizar_rect()

    def _avanzar_animaciones(self, dt: float) -> None:
        for jugador in (
            self._jugador,
            self._companero,
            self._defensor,
            self._portero,
        ):
            jugador.avanzar_animacion(dt)

    # --------------------------------------------------
    # Dibujo
    # --------------------------------------------------

    def _crear_fondo(self, estadio: Estadio) -> pygame.Surface:
        """Pre-renderiza el recinto y las líneas del campo."""
        return crear_fondo_estadio(estadio, red=True)

    def _chip(
        self,
        texto: str,
        fuente: pygame.font.Font,
        color: Color,
    ) -> pygame.Surface:
        letras = self._texto(texto, fuente, color)
        fondo = pygame.Surface(
            (letras.get_width() + 26, letras.get_height() + 12),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            fondo,
            (4, 12, 22, 200),
            fondo.get_rect(),
            border_radius=9,
        )
        pygame.draw.rect(
            fondo,
            (*color, 90),
            fondo.get_rect(),
            1,
            border_radius=9,
        )
        fondo.blit(letras, letras.get_rect(center=fondo.get_rect().center))
        return fondo

    def dibujar(self, pantalla: pygame.Surface) -> None:
        """Dibuja la cancha, los jugadores y el marcador del ejercicio."""
        pantalla.blit(self._fondo, (0, 0))

        if self.tipo is TipoEntrenamiento.DOS_CONTRA_UNO:
            self._companero.dibujar(pantalla)
            self._defensor.dibujar(pantalla)

        self._jugador.dibujar(pantalla)
        self._portero.dibujar(pantalla)

        if self.tipo is TipoEntrenamiento.PENALES:
            self._dibujar_objetivo(pantalla)

        self.balon.dibujar(pantalla)
        self._dibujar_controlado(pantalla)
        self._dibujar_hud(pantalla)

        if self.fase is FaseEntrenamiento.RESULTADO:
            color = AMARILLO if self.goles and self.texto_resultado.startswith("¡GOL") else BLANCO
            letras = self._texto(
                self.texto_resultado,
                self.fuente_resultado,
                color,
            )
            sombra = self._texto(
                self.texto_resultado,
                self.fuente_resultado,
                NEGRO,
            )
            rect = letras.get_rect(center=(ANCHO // 2, ALTO // 2 - 20))
            pantalla.blit(sombra, rect.move(3, 3))
            pantalla.blit(letras, rect)
        elif self.fase is FaseEntrenamiento.FINAL:
            self._dibujar_final(pantalla)

    def _dibujar_controlado(self, pantalla: pygame.Surface) -> None:
        if self.fase is FaseEntrenamiento.FINAL:
            return

        pygame.draw.circle(
            pantalla,
            AMARILLO,
            (round(self.controlado.pos.x), round(self.controlado.pos.y)),
            RADIO_JUGADOR + 6,
            2,
        )

    def _dibujar_objetivo(self, pantalla: pygame.Surface) -> None:
        """Mira de tiro del penal: línea y punto de mira."""
        destino = (CAMPO_RECT.right, round(self._objetivo_y))
        pygame.draw.line(
            pantalla,
            (255, 255, 255),
            (round(self.balon.pos.x), round(self.balon.pos.y)),
            destino,
            1,
        )
        pygame.draw.circle(pantalla, AMARILLO, destino, 7, 2)
        pygame.draw.line(
            pantalla,
            AMARILLO,
            (destino[0] - 11, destino[1]),
            (destino[0] + 11, destino[1]),
            2,
        )
        pygame.draw.line(
            pantalla,
            AMARILLO,
            (destino[0], destino[1] - 11),
            (destino[0], destino[1] + 11),
            2,
        )

    def _dibujar_hud(self, pantalla: pygame.Surface) -> None:
        etiqueta = self._etiqueta_intento()
        izquierda = self._chip(etiqueta, self.fuente_hud, BLANCO)
        pantalla.blit(izquierda, (18, 16))

        marcador = self._chip(
            f"GOLES {self.goles}  ·  META {self.definicion.objetivo}",
            self.fuente_hud,
            AMARILLO,
        )
        pantalla.blit(
            marcador,
            marcador.get_rect(midtop=(ANCHO // 2, 16)),
        )

        monedas = self._chip(
            f"MONEDAS {self.monedas}",
            self.fuente_hud,
            AMARILLO,
        )
        pantalla.blit(
            monedas,
            monedas.get_rect(topright=(ANCHO - 18, 16)),
        )

        ayuda = self._ayuda()
        letras = self._texto(ayuda, self.fuente_pequena, BLANCO)
        fondo = pygame.Surface(
            (letras.get_width() + 24, letras.get_height() + 10),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            fondo,
            (0, 0, 0, 150),
            fondo.get_rect(),
            border_radius=9,
        )
        fondo.blit(letras, letras.get_rect(center=fondo.get_rect().center))
        pantalla.blit(
            fondo,
            fondo.get_rect(midbottom=(ANCHO // 2, ALTO - 10)),
        )

    def _etiqueta_intento(self) -> str:
        if self.tipo is TipoEntrenamiento.TIROS:
            nombre = "TIRO"
        elif self.tipo is TipoEntrenamiento.PENALES:
            nombre = "PENAL"
        else:
            nombre = "ATAQUE"

        return (
            f"{self.definicion.nombre.upper()} · "
            f"{nombre} {self.intento}/{self.definicion.intentos}"
        )

    def _ayuda(self) -> str:
        if self.tipo is TipoEntrenamiento.PENALES:
            return "←/→ o ↑/↓: apuntar · ESPACIO: chutar · ESC: salir"

        if self.tipo is TipoEntrenamiento.DOS_CONTRA_UNO:
            return (
                "WASD/Flechas: mover · ESPACIO: chutar · "
                "E: pasar · ESC: salir"
            )

        return "WASD/Flechas: mover · ESPACIO: chutar · ESC: salir"

    def _dibujar_final(self, pantalla: pygame.Surface) -> None:
        panel = pygame.Surface((600, 280), pygame.SRCALPHA)
        pygame.draw.rect(
            panel,
            (4, 12, 24, 238),
            panel.get_rect(),
            border_radius=20,
        )
        pygame.draw.rect(
            panel,
            (VERDE_ENERGIA if self.exito else ROJO_ENERGIA),
            panel.get_rect(),
            2,
            border_radius=20,
        )

        titulo = (
            "¡ENTRENAMIENTO COMPLETADO!"
            if self.exito
            else "ENTRENAMIENTO NO SUPERADO"
        )
        color = VERDE_ENERGIA if self.exito else ROJO_ENERGIA
        letras = self._texto(titulo, self.fuente_final, color)
        panel.blit(letras, letras.get_rect(midtop=(300, 28)))

        resumen = (
            f"Goles: {self.goles}  ·  Meta: {self.definicion.objetivo}"
        )
        linea = self._texto(resumen, self.fuente_hud, BLANCO)
        panel.blit(linea, linea.get_rect(midtop=(300, 86)))

        if self.exito:
            premio = (
                f"+{self.recompensa} monedas "
                f"({self.definicion.recompensa} base"
                f" + {self.definicion.monedas_por_gol}/gol)"
            )
            color_premio = AMARILLO
        else:
            premio = "Cumple la meta para ganar monedas"
            color_premio = (190, 200, 210)

        letras_premio = self._texto(premio, self.fuente_hud, color_premio)
        panel.blit(letras_premio, letras_premio.get_rect(midtop=(300, 130)))

        pie = self._texto(
            "ESPACIO: repetir  ·  ESC: volver",
            self.fuente_pequena,
            BLANCO,
        )
        panel.blit(pie, pie.get_rect(midbottom=(300, 250)))

        pantalla.blit(panel, panel.get_rect(center=(ANCHO // 2, ALTO // 2)))
