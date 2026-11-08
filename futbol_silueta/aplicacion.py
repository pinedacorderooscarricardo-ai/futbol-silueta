"""Bucle principal de Fútbol Silueta y transiciones entre pantallas."""

from __future__ import annotations

import time

import pygame

from .configuracion import (
    ALTO,
    ANCHO,
    CIAN,
    DT_FIJO,
    DT_MAXIMO,
    FPS,
    MAX_PASOS_FISICA,
    NEGRO,
    TITULO_VENTANA,
    Estado,
)
from .juego import Juego
from .estadisticas import registrar_resultado
from .guardado import Guardado
from .menus import Accion, Menus, Pantalla
from .modos import ModoJuego, Solicitud
from .vista import Vista


class Aplicacion:
    """Coordina el partido, los menús y el bucle de fotogramas."""

    def __init__(
        self,
        pantalla: pygame.Surface | None = None,
        guardado: Guardado | None = None,
    ) -> None:
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

        # Base de datos con la configuración y la plantilla guardadas.
        self.guardado = guardado if guardado is not None else Guardado()
        self.guardado.cargar_en(self.menus)
        # La campaña continúa donde quedó la sesión anterior.
        self.juego.adoptar_nivel(self.guardado.nivel_guardado())

        # Medidor de rendimiento (se activa con F3; no cuesta nada apagado).
        self.mostrar_rendimiento = False
        self.fuente_rendimiento = pygame.font.SysFont("Arial", 14)
        self._ms_simulacion = 0.0
        self._ms_dibujo = 0.0
        self._pasos_simulacion = 0

    def ejecutar(self) -> None:
        """Bucle principal: eventos, simulación a paso fijo y dibujo.

        El tiempo real se acumula y la simulación avanza en pasos de
        ``DT_FIJO`` (hasta ``MAX_PASOS_FISICA`` por fotograma), de modo
        que la física no depende de la velocidad de cada computadora.
        """
        acumulado = 0.0

        try:
            while self.ejecutando:
                acumulado += min(self.reloj.tick(FPS) / 1000.0, DT_MAXIMO)

                self.procesar_eventos()

                if not self.ejecutando:
                    break

                inicio = time.perf_counter()
                pasos = 0

                while acumulado >= DT_FIJO and pasos < MAX_PASOS_FISICA:
                    self.actualizar(DT_FIJO)
                    acumulado -= DT_FIJO
                    pasos += 1

                if pasos == MAX_PASOS_FISICA and acumulado > 0.0:
                    # El equipo no da abasto: se descarta el atraso
                    # pendiente en vez de seguir acumulándolo (espiral de
                    # la muerte).
                    acumulado = 0.0

                self._medir_simulacion(inicio, pasos)

                inicio = time.perf_counter()
                self.dibujar()
                pygame.display.flip()
                self._medir_dibujo(inicio)
        finally:
            # Al cerrar, por cualquier vía, quedan guardados los ajustes,
            # la plantilla, la campaña, el palmarés y el torneo en curso.
            self.guardado.guardar_desde(self.menus, self.juego.nivel)
            self.guardado.guardar_torneo(self.juego.modo, self.juego.torneo)
            self.guardado.cerrar()

    def _medir_simulacion(self, inicio: float, pasos: int) -> None:
        """Promedia cuánto tardó la simulación de este fotograma."""
        muestra = (time.perf_counter() - inicio) * 1000.0
        self._ms_simulacion += (muestra - self._ms_simulacion) * 0.1
        self._pasos_simulacion = pasos

    def _medir_dibujo(self, inicio: float) -> None:
        """Promedia cuánto tardaron el dibujo y la presentación."""
        muestra = (time.perf_counter() - inicio) * 1000.0
        self._ms_dibujo += (muestra - self._ms_dibujo) * 0.1

    def procesar_eventos(self) -> None:
        """Reparte los eventos entre el partido y los menús."""
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.ejecutando = False
                return

            if (
                evento.type == pygame.KEYDOWN
                and evento.key == pygame.K_F3
            ):
                self.mostrar_rendimiento = not self.mostrar_rendimiento
                continue

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

        # El partido puede pedir volver al menú (fin de torneo, racha).
        if self.juego.solicitud is Solicitud.MENU_PRINCIPAL:
            self.juego.solicitud = None
            self.menus.abrir_menu_principal()

    def actualizar(self, dt: float) -> None:
        """Avanza el partido solo cuando la pantalla de juego está activa."""
        self.juego.sonidos.habilitado = self.menus.sonido_activado

        # Las animaciones (saltos, caídas, celebraciones) corren en
        # cualquier estado para que el gol se siga celebrando.
        self.juego.avanzar_animaciones(dt)

        if self.menus.pantalla is Pantalla.PARTIDO:
            self.juego.actualizar(dt)

            # Guardado automático del resultado: el final del partido se
            # registra una sola vez (tabla, historial y trofeos).
            if (
                self.juego.estado is Estado.FINAL
                and not self.juego.resultado_registrado
            ):
                self._registrar_resultado()

    def _registrar_resultado(self) -> None:
        """Anota el partido terminado y anuncia sus trofeos nuevos.

        Solo la campaña alimenta la tabla de la campaña, el historial
        y los trofeos: en los torneos los rivales son los del circuito,
        pero sus partidos no cuentan como campaña.
        """
        juego = self.juego
        juego.resultado_registrado = True
        if juego.modo is ModoJuego.CAMPANA:
            nuevos = registrar_resultado(self.menus, juego)
        else:
            nuevos = []
        juego.trofeos_nuevos = [trofeo.nombre for trofeo in nuevos]
        self.guardado.guardar_desde(self.menus, juego.nivel)
        self.guardado.guardar_torneo(self.juego.modo, self.juego.torneo)

    def dibujar(self) -> None:
        """Dibuja el partido o la pantalla de menú actual."""
        if self.menus.pantalla is Pantalla.PARTIDO:
            self.vista.dibujar(self.juego)
        else:
            self.menus.dibujar(self.pantalla)

        if self.mostrar_rendimiento:
            self._dibujar_rendimiento()

    def _dibujar_rendimiento(self) -> None:
        """Superpone FPS y tiempos de simulación y dibujo (tecla F3)."""
        texto = (
            f"FPS {self.reloj.get_fps():.0f}"
            f" | sim {self._ms_simulacion:.2f} ms"
            f" | dibujo {self._ms_dibujo:.2f} ms"
            f" | pasos {self._pasos_simulacion}"
        )
        superficie = self.fuente_rendimiento.render(
            texto,
            True,
            CIAN,
            NEGRO,
        )
        self.pantalla.blit(
            superficie,
            superficie.get_rect(topright=(ANCHO - 10, 10)),
        )

    def _aplicar_preferencias(self) -> None:
        """Lleva al juego la personalización elegida en los menús.

        Se usa al empezar o reiniciar una partida: escudo, uniformes,
        estadio, plantillas del editor y la táctica elegida (sin
        recolocar, porque el partido se reinicia de todos modos).
        """
        color, color_borde, forma = self.menus.escudo_seleccionado
        self.juego.personalizar_escudo(color, color_borde, forma)
        self.juego.personalizar_uniformes(
            self.menus.uniformes_seleccionados,
            self.menus.numeros_activados,
        )
        self.juego.personalizar_estadio(self.menus.estadio_seleccionado)
        self.juego.personalizar_plantillas(
            self.menus.plantillas_seleccionadas
        )
        self.juego.cambiar_formacion(
            self.menus.formacion_nombre,
            recolocar=False,
        )

    def _ejecutar_accion_pendiente(self) -> None:
        self.juego.sonidos.habilitado = self.menus.sonido_activado
        accion = self.menus.consumir_accion()

        if accion is Accion.JUGAR:
            self.menus.reiniciar_sustituciones()
            self._aplicar_preferencias()
            modo = self.menus.modo_seleccionado
            # Reanuda el torneo guardado de ese modo, si lo hay.
            self.juego.iniciar_modo(modo, self.guardado.cargar_torneo(modo))
            self.guardado.guardar_torneo(modo, self.juego.torneo)
            self.guardado.guardar_desde(self.menus, self.juego.nivel)
        elif accion is Accion.REINICIAR:
            self.menus.reiniciar_sustituciones()
            self._aplicar_preferencias()
            self.juego.nueva_partida()
            self.guardado.guardar_desde(self.menus, self.juego.nivel)
        elif accion is Accion.FORMACION:
            # Las fichas ya llegan recolocadas desde el menú de
            # tácticas: solo falta recrear a los jugadores en el campo.
            self.juego.personalizar_plantillas(
                self.menus.plantillas_seleccionadas
            )
            self.juego.cambiar_formacion(self.menus.formacion_nombre)
        elif accion is Accion.SALIR:
            self.ejecutando = False

        self._aplicar_sustitucion_pendiente()

    def _aplicar_sustitucion_pendiente(self) -> None:
        """Reemplaza en el campo al jugador de un cambio confirmado.

        Se llama en cada fotograma de eventos: el menú deja la pareja
        lista y aquí se recrea al jugador sin cortar la jugada.
        """
        sustitucion = self.menus.consumir_sustitucion()

        if sustitucion is None:
            return

        equipo, hueco, _dorsal_saliente, ficha_entrante = sustitucion
        self.juego.sustituir(
            equipo,
            hueco,
            ficha_entrante,
        )
        self.juego.personalizar_plantillas(
            self.menus.plantillas_seleccionadas
        )
