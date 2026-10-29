"""Bucle principal de Fútbol Silueta y transiciones entre pantallas."""

from __future__ import annotations

import pygame

from .configuracion import ALTO, ANCHO, DT_MAXIMO, FPS, TITULO_VENTANA
from .juego import Juego
from .menus import Accion, Menus, Pantalla
from .vista import Vista


class Aplicacion:
    """Coordina el partido, los menús y el bucle de fotogramas."""

    def __init__(self, pantalla: pygame.Surface | None = None) -> None:
        if pantalla is None:
            pantalla = pygame.display.get_surface()

        if pantalla is None:
            pantalla = pygame.display.set_mode((ANCHO, ALTO))

        self.pantalla = pantalla
        pygame.display.set_caption(TITULO_VENTANA)

        self.reloj = pygame.time.Clock()
        self.vista = Vista(pantalla)
        self.juego = Juego(self.vista)
        self.menus = Menus()
        self.ejecutando = True

    def ejecutar(self) -> None:
        """Bucle principal: eventos, simulación, dibujo y presentación."""
        while self.ejecutando:
            dt = min(self.reloj.tick(FPS) / 1000.0, DT_MAXIMO)

            self.procesar_eventos()

            if not self.ejecutando:
                break

            self.actualizar(dt)
            self.dibujar()
            pygame.display.flip()

    def procesar_eventos(self) -> None:
        """Reparte los eventos entre el partido y los menús."""
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.ejecutando = False
                return

            if self.menus.pantalla is Pantalla.PARTIDO:
                if evento.type != pygame.KEYDOWN:
                    continue

                if evento.key == pygame.K_ESCAPE:
                    self.menus.abrir_pausa()
                else:
                    self.juego.procesar_tecla(evento.key)
            else:
                self.menus.procesar_evento(evento)

        self._ejecutar_accion_pendiente()

    def actualizar(self, dt: float) -> None:
        """Avanza el partido solo cuando la pantalla de juego está activa."""
        self.juego.sonidos.habilitado = self.menus.sonido_activado

        if self.menus.pantalla is Pantalla.PARTIDO:
            self.juego.actualizar(dt)

    def dibujar(self) -> None:
        """Dibuja el partido o la pantalla de menú actual."""
        if self.menus.pantalla is Pantalla.PARTIDO:
            self.vista.dibujar(self.juego)
        else:
            self.menus.dibujar(self.pantalla)

    def _ejecutar_accion_pendiente(self) -> None:
        self.juego.sonidos.habilitado = self.menus.sonido_activado
        accion = self.menus.consumir_accion()

        if accion in (Accion.JUGAR, Accion.REINICIAR):
            color, color_borde, forma = self.menus.escudo_seleccionado
            self.juego.personalizar_escudo(color, color_borde, forma)
            self.juego.nueva_partida()
        elif accion is Accion.SALIR:
            self.ejecutando = False
