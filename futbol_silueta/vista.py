"""Todo el dibujo de la partida."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

from .configuracion import (
    ALTO,
    AMARILLO,
    ANCHO,
    ANCHO_POSTE,
    AREA_PENALTI_ALTO,
    AREA_PENALTI_ANCHO,
    BLANCO,
    CAMPO_RECT,
    CIAN,
    ENERGIA_MAXIMA,
    ESTADOS_ESPERA,
    Estado,
    MENSAJE_ENTRETIEMPO,
    MENSAJE_FINAL,
    MENSAJE_GOL,
    MENSAJE_REPETICION,
    NEGRO,
    PORTERIA_ALTO,
    PORTERIA_SUPERIOR,
    RADIO_CIRCULO_CENTRAL,
    ROJO_ENERGIA,
    TEXTO_AYUDA,
    TEXTO_CONTINUAR,
    TEXTO_ENTRETIEMPO,
    TEXTO_FINAL,
    TEXTO_SALTAR_REPETICION,
    VERDE,
    VERDE_ENERGIA,
    Color,
)

from .escudos import Escudo, cargar_escudo
from .niveles import nivel_por_numero

if TYPE_CHECKING:
    from .juego import Juego


class Vista:
    """Todo el dibujo de la partida.

    Pre-renderiza en el arranque lo que nunca cambia (campo, HUD,
    mensajes de gol) y guarda en caché lo que cambia poco (marcador).
    """

    POSICION_MARCADOR = (ANCHO // 2, 46)
    POSICION_TIEMPO = (20, 18)
    POSICION_ENERGIA = (20, 56)
    ANCHO_ENERGIA = 170
    ALTO_ENERGIA = 12
    ALTO_ESCUDO_MARCADOR = 34
    POSICION_MENSAJE_GOL = (ANCHO // 2, ALTO // 2)
    POSICION_CONTINUAR = (ANCHO // 2, ALTO // 2 + 50)
    POSICION_REPETICION = (ANCHO // 2, 108)

    def __init__(self, pantalla: pygame.Surface) -> None:
        self.pantalla = pantalla

        self.fuente_marcador = pygame.font.SysFont("Arial", 30, bold=True)
        self.fuente_mensaje = pygame.font.SysFont("Arial", 48, bold=True)
        self.fuente_instrucciones = pygame.font.SysFont("Arial", 20)
        self.fuente_hud = pygame.font.SysFont("Arial", 16)
        self.fuente_tiempo = pygame.font.SysFont("Arial", 20, bold=True)

        # Elementos estáticos: se crean una vez y solo se copian.
        self.fondo = self._crear_fondo()
        self.hud = self.fuente_hud.render(TEXTO_AYUDA, True, BLANCO)
        self.mensajes_gol = {
            equipo: self.fuente_mensaje.render(texto, True, AMARILLO)
            for equipo, texto in MENSAJE_GOL.items()
        }
        self.mensajes_estado = {
            Estado.ENTRETIEMPO: self.fuente_mensaje.render(
                MENSAJE_ENTRETIEMPO,
                True,
                AMARILLO,
            ),
            Estado.FINAL: self.fuente_mensaje.render(
                MENSAJE_FINAL,
                True,
                AMARILLO,
            ),
        }
        self.textos_estado = {
            Estado.ENTRETIEMPO: self.fuente_instrucciones.render(
                TEXTO_ENTRETIEMPO,
                True,
                BLANCO,
            ),
            Estado.FINAL: self.fuente_instrucciones.render(
                TEXTO_FINAL,
                True,
                BLANCO,
            ),
        }
        self.paneles_estado = {
            estado: self._crear_panel(
                self.mensajes_estado[estado],
                self.textos_estado[estado],
            )
            for estado in ESTADOS_ESPERA
        }
        self.superficie_continuar = self.fuente_instrucciones.render(
            TEXTO_CONTINUAR,
            True,
            BLANCO,
        )
        # Cartela y aviso de la repetición de gol.
        self.superficie_repeticion = self._crear_superficie_con_fondo(
            MENSAJE_REPETICION,
            self.fuente_tiempo,
            CIAN,
            padding_x=16,
            padding_y=8,
            radio=8,
        )
        self.superficie_salto_repeticion = self.fuente_instrucciones.render(
            TEXTO_SALTAR_REPETICION,
            True,
            BLANCO,
        )

        # Caché del marcador: (goles dibujados, superficie).
        self._marcador_cache: tuple[
            tuple[int, int], pygame.Surface
        ] | None = None
        # Caché del reloj: ((mitad, segundos), superficie).
        self._tiempo_cache: tuple[
            tuple[int, int], pygame.Surface
        ] | None = None
        # Caché de escudos rivales escalados, uno por nivel.
        self._escudos_rivales: dict[int, pygame.Surface] = {}

    # --------------------------------------------------
    # Dibujo general
    # --------------------------------------------------

    def dibujar(self, juego: Juego) -> None:
        self.pantalla.blit(self.fondo, (0, 0))
        self._dibujar_objetivo_pase(juego)

        for jugador in juego.jugadores:
            jugador.dibujar(self.pantalla)

        juego.balon.dibujar(self.pantalla)
        self._dibujar_jugador_controlado(juego)
        self._dibujar_escudo(juego)

        self._dibujar_marcador(juego)
        self._dibujar_tiempo(juego)
        self._dibujar_energia(juego)
        self._dibujar_hud()

        if juego.estado is Estado.GOL:
            self._dibujar_mensaje_gol(juego)
        elif juego.estado is Estado.REPETICION:
            self._dibujar_mensaje_repeticion()
        elif juego.estado in ESTADOS_ESPERA:
            self._dibujar_mensaje_estado(juego.estado)

    def _dibujar_hud(self) -> None:
        self.pantalla.blit(
            self.hud,
            (12, ALTO - self.hud.get_height() - 6),
        )

    def _dibujar_mensaje_gol(self, juego: Juego) -> None:
        if juego.ultimo_gol is None:
            return

        mensaje = self.mensajes_gol[juego.ultimo_gol]
        self.pantalla.blit(
            mensaje,
            mensaje.get_rect(center=self.POSICION_MENSAJE_GOL),
        )
        self.pantalla.blit(
            self.superficie_continuar,
            self.superficie_continuar.get_rect(center=self.POSICION_CONTINUAR),
        )

    def _dibujar_mensaje_repeticion(self) -> None:
        """Cartela de repetición en curso y cómo saltarla."""
        self.pantalla.blit(
            self.superficie_repeticion,
            self.superficie_repeticion.get_rect(
                center=self.POSICION_REPETICION
            ),
        )
        self.pantalla.blit(
            self.superficie_salto_repeticion,
            self.superficie_salto_repeticion.get_rect(
                center=self.POSICION_CONTINUAR
            ),
        )

    def _dibujar_mensaje_estado(self, estado: Estado) -> None:
        """Mensaje de descanso o final del partido."""
        panel = self.paneles_estado[estado]
        self.pantalla.blit(
            panel,
            panel.get_rect(center=(ANCHO // 2, ALTO // 2 + 20)),
        )
        self.pantalla.blit(
            self.mensajes_estado[estado],
            self.mensajes_estado[estado].get_rect(
                center=self.POSICION_MENSAJE_GOL
            ),
        )
        self.pantalla.blit(
            self.textos_estado[estado],
            self.textos_estado[estado].get_rect(
                center=self.POSICION_CONTINUAR
            ),
        )

    # --------------------------------------------------
    # Piezas pre-renderizadas y cachés
    # --------------------------------------------------

    def _crear_fondo(self) -> pygame.Surface:
        """Pre-renderiza el campo, que no cambia entre fotogramas."""
        fondo = pygame.Surface((ANCHO, ALTO)).convert()
        fondo.fill(VERDE)

        pygame.draw.rect(fondo, BLANCO, CAMPO_RECT, 3)

        pygame.draw.line(
            fondo,
            BLANCO,
            (CAMPO_RECT.centerx, CAMPO_RECT.top),
            (CAMPO_RECT.centerx, CAMPO_RECT.bottom),
            2,
        )

        pygame.draw.circle(
            fondo,
            BLANCO,
            (CAMPO_RECT.centerx, CAMPO_RECT.centery),
            RADIO_CIRCULO_CENTRAL,
            2,
        )

        # Áreas de penalti, en las dos bandas.
        for x in (
            CAMPO_RECT.left,
            CAMPO_RECT.right - AREA_PENALTI_ANCHO,
        ):
            pygame.draw.rect(
                fondo,
                BLANCO,
                (
                    x,
                    CAMPO_RECT.centery - AREA_PENALTI_ALTO // 2,
                    AREA_PENALTI_ANCHO,
                    AREA_PENALTI_ALTO,
                ),
                2,
            )

        # Porterías, a cada lado del campo.
        for x in (
            CAMPO_RECT.left - ANCHO_POSTE,
            CAMPO_RECT.right,
        ):
            pygame.draw.rect(
                fondo,
                BLANCO,
                (x, PORTERIA_SUPERIOR, ANCHO_POSTE, PORTERIA_ALTO),
                3,
            )

        return fondo

    def _crear_panel(
        self,
        mensaje: pygame.Surface,
        texto: pygame.Surface,
    ) -> pygame.Surface:
        """Crea el panel oscuro que acompaña a un mensaje de estado."""
        ancho = max(mensaje.get_width(), texto.get_width()) + 48
        alto = mensaje.get_height() + texto.get_height() + 36
        panel = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        pygame.draw.rect(
            panel,
            (0, 0, 0, 170),
            panel.get_rect(),
            border_radius=16,
        )
        return panel

    def _dibujar_marcador(self, juego: Juego) -> None:
        clave = (
            juego.nivel,
            juego.goles_local,
            juego.goles_visitante,
            juego.escudo.color,
            juego.escudo.color_borde,
            juego.escudo.forma,
        )

        if self._marcador_cache is None or self._marcador_cache[0] != clave:
            self._marcador_cache = (
                clave,
                self._crear_superficie_marcador(juego),
            )

        superficie = self._marcador_cache[1]
        self.pantalla.blit(
            superficie,
            superficie.get_rect(center=self.POSICION_MARCADOR),
        )

    def _crear_superficie_marcador(self, juego: Juego) -> pygame.Surface:
        """Panel del marcador con el escudo del jugador y el del rival.

        Cada nivel es un escudo rival distinto: la imagen del escudo del
        nivel aparece a la derecha y el escudo personalizado del jugador
        a la izquierda, junto al resultado y al nombre del club.
        """
        nivel = nivel_por_numero(juego.nivel)
        texto = (
            f"NIVEL {juego.nivel}   LOCAL {juego.goles_local} - "
            f"{juego.goles_visitante} VISITANTE"
        )
        texto_render = self.fuente_marcador.render(texto, True, BLANCO)
        subtitulo = self.fuente_hud.render(nivel.rival, True, BLANCO)

        escudo_rival = self._escudo_rival_escalado(juego.nivel)
        ancho_escudo_jugador = round(Escudo.TAMANO * 2 * 1.05)

        separacion = 14
        padding_x = 22
        ancho = (
            padding_x
            + ancho_escudo_jugador
            + separacion
            + max(texto_render.get_width(), subtitulo.get_width())
            + separacion
            + escudo_rival.get_width()
            + padding_x
        )
        alto = self.ALTO_ESCUDO_MARCADOR + subtitulo.get_height() + 18

        panel = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        pygame.draw.rect(panel, NEGRO, panel.get_rect(), border_radius=8)

        centro_y = panel.get_rect().centery
        x_escudo_jugador = padding_x + ancho_escudo_jugador // 2
        juego.escudo.dibujar(panel, (x_escudo_jugador, centro_y), 1.05)
        panel.blit(
            escudo_rival,
            escudo_rival.get_rect(
                midright=(ancho - padding_x, centro_y),
            ),
        )

        centro_texto = padding_x + ancho_escudo_jugador + separacion
        ancho_texto = ancho - 2 * (
            padding_x + ancho_escudo_jugador + separacion
        )
        panel.blit(
            texto_render,
            texto_render.get_rect(
                midtop=(centro_texto + ancho_texto // 2, 9),
            ),
        )
        panel.blit(
            subtitulo,
            subtitulo.get_rect(
                midtop=(centro_texto + ancho_texto // 2, 9 + texto_render.get_height() + 2),
            ),
        )

        return panel.convert_alpha()

    def _escudo_rival_escalado(self, nivel: int) -> pygame.Surface:
        """Imagen del escudo del nivel, escalada para el marcador."""
        escalado = self._escudos_rivales.get(nivel)

        if escalado is None:
            original = cargar_escudo(nivel)
            alto = self.ALTO_ESCUDO_MARCADOR
            ancho = round(original.get_width() * alto / original.get_height())
            escalado = pygame.transform.smoothscale(
                original,
                (ancho, alto),
            ).convert_alpha()
            self._escudos_rivales[nivel] = escalado

        return escalado

    def _dibujar_tiempo(self, juego: Juego) -> None:
        segundos = math.ceil(max(0.0, juego.tiempo_restante) / 1000.0)
        clave = (juego.mitad, segundos)

        if self._tiempo_cache is None or self._tiempo_cache[0] != clave:
            texto = f"{juego.mitad}T  {segundos // 60:02d}:{segundos % 60:02d}"
            self._tiempo_cache = (
                clave,
                self._crear_superficie_tiempo(texto),
            )

        superficie = self._tiempo_cache[1]
        self.pantalla.blit(superficie, self.POSICION_TIEMPO)

    def _dibujar_energia(self, juego: Juego) -> None:
        """Barra de energía del jugador, justo debajo del reloj."""
        x, y = self.POSICION_ENERGIA
        ancho = self.ANCHO_ENERGIA
        alto = self.ALTO_ENERGIA

        pygame.draw.rect(
            self.pantalla,
            NEGRO,
            (x, y, ancho, alto),
            border_radius=4,
        )

        proporcion = max(
            0.0,
            min(1.0, juego.energia_actual / ENERGIA_MAXIMA),
        )
        relleno = round((ancho - 4) * proporcion)

        if relleno > 0:
            color = (
                ROJO_ENERGIA
                if proporcion < 0.30
                else VERDE_ENERGIA
            )
            pygame.draw.rect(
                self.pantalla,
                color,
                (x + 2, y + 2, relleno, alto - 4),
                border_radius=3,
            )

        pygame.draw.rect(
            self.pantalla,
            BLANCO,
            (x, y, ancho, alto),
            1,
            border_radius=4,
        )

    def _crear_superficie_tiempo(self, texto: str) -> pygame.Surface:
        return self._crear_superficie_con_fondo(
            texto,
            self.fuente_tiempo,
            BLANCO,
            padding_x=16,
            padding_y=8,
            radio=8,
        )

    def _crear_superficie_con_fondo(
        self,
        texto: str,
        fuente: pygame.font.Font,
        color: Color,
        *,
        padding_x: int,
        padding_y: int,
        radio: int,
    ) -> pygame.Surface:
        """Renderiza un texto sobre un fondo oscuro redondeado."""
        texto_render = fuente.render(texto, True, color)
        fondo = pygame.Surface(
            (
                texto_render.get_width() + padding_x,
                texto_render.get_height() + padding_y,
            ),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            fondo,
            NEGRO,
            fondo.get_rect(),
            border_radius=radio,
        )
        fondo.blit(
            texto_render,
            texto_render.get_rect(center=fondo.get_rect().center),
        )
        return fondo.convert_alpha()

    def _dibujar_jugador_controlado(self, juego: Juego) -> None:
        """Triángulo cian sobre el jugador que controla el humano."""
        control = juego.jugador_controlado

        if control is None or juego.estado is not Estado.JUGANDO:
            return

        x, y = control.rect.center
        base_y = y - control.RADIO - 6
        puntos = (
            (x, base_y),
            (x - 7, base_y - 9),
            (x + 7, base_y - 9),
        )

        pygame.draw.polygon(self.pantalla, CIAN, puntos)
        pygame.draw.polygon(self.pantalla, BLANCO, puntos, 1)

    def _dibujar_escudo(self, juego: Juego) -> None:
        """Escudo personalizado del jugador controlado."""
        control = juego.jugador_controlado

        if control is None or juego.estado is not Estado.JUGANDO:
            return

        juego.escudo.dibujar(self.pantalla, control.rect.center)

    def _dibujar_objetivo_pase(self, juego: Juego) -> None:
        """Aro cian sobre el compañero al que iría el próximo pase."""
        control = juego.jugador_controlado

        if (
            control is None
            or juego.estado is not Estado.JUGANDO
            or juego.portador is not control
        ):
            return

        receptor = juego.obtener_receptor_mas_cercano(control)

        if receptor is None:
            return

        pygame.draw.circle(
            self.pantalla,
            CIAN,
            receptor.rect.center,
            receptor.RADIO + 6,
            2,
        )
