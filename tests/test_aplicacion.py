"""Pruebas de integración del bucle principal y las pantallas."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame

from futbol_silueta.aplicacion import Aplicacion
from futbol_silueta.configuracion import (
    ALTO,
    ANCHO,
    DURACION_MITAD,
    Equipo,
    Estado,
    Rol,
)
from futbol_silueta.guardado import Guardado
from futbol_silueta.menus import Accion, Pantalla


class AplicacionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        cls.pantalla = pygame.display.set_mode((ANCHO, ALTO))

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def setUp(self) -> None:
        pygame.event.clear()
        # Cada prueba usa su propia base de datos temporal.
        directorio = tempfile.TemporaryDirectory()
        self.addCleanup(directorio.cleanup)
        self.guardado = Guardado(
            Path(directorio.name) / "pruebas.sqlite"
        )
        self.addCleanup(self.guardado.cerrar)
        self.app = Aplicacion(self.pantalla, guardado=self.guardado)

    def _tecla(self, tecla: int) -> None:
        pygame.event.post(
            pygame.event.Event(
                pygame.KEYDOWN,
                {"key": tecla, "mod": 0, "unicode": "", "scancode": 0},
            )
        )

    def _click(self, rect: pygame.Rect) -> None:
        pygame.event.post(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {"pos": rect.center, "button": 1},
            )
        )

    def test_click_en_jugar_inicia_una_partida(self) -> None:
        self._click(self.app.menus.botones[Pantalla.PRINCIPAL][0].rect)
        self.app.procesar_eventos()

        self.assertIs(self.app.menus.pantalla, Pantalla.PARTIDO)
        self.assertIs(self.app.juego.estado, Estado.JUGANDO)
        self.assertEqual(
            self.app.juego.tiempo_restante,
            float(DURACION_MITAD),
        )

    def test_escape_abre_la_pausa_y_continuar_reanuda(self) -> None:
        self.app.menus.pantalla = Pantalla.PARTIDO

        self._tecla(pygame.K_ESCAPE)
        self.app.procesar_eventos()
        self.assertIs(self.app.menus.pantalla, Pantalla.PAUSA)

        self._tecla(pygame.K_RETURN)
        self.app.procesar_eventos()
        self.assertIs(self.app.menus.pantalla, Pantalla.PARTIDO)

    def test_reiniciar_desde_la_pausa(self) -> None:
        self.app.menus.pantalla = Pantalla.PARTIDO
        self.app.juego.goles_local = 3
        self.app.juego.tiempo_restante = 1000.0

        self._tecla(pygame.K_ESCAPE)
        self._tecla(pygame.K_DOWN)
        self._tecla(pygame.K_RETURN)
        self.app.procesar_eventos()

        self.assertIs(self.app.menus.pantalla, Pantalla.PARTIDO)
        self.assertEqual(self.app.juego.goles_local, 0)
        self.assertEqual(
            self.app.juego.tiempo_restante,
            float(DURACION_MITAD),
        )

    def test_el_sonido_desactivado_se_aplica_al_juego(self) -> None:
        self.app.menus.pantalla = Pantalla.OPCIONES
        self.app.menus.indice = 0
        self.app.menus.procesar_tecla(pygame.K_RETURN)

        self.assertFalse(self.app.menus.sonido_activado)

        self.app.actualizar(0.0)
        self.assertFalse(self.app.juego.sonidos.habilitado)

    def test_la_formacion_elegida_llega_al_partido(self) -> None:
        menus = self.app.menus
        menus.pantalla = Pantalla.OPCIONES
        menus.indice = 1  # Tácticas
        menus.procesar_tecla(pygame.K_RETURN)
        self.assertIs(menus.pantalla, Pantalla.TACTICA)

        menus.indice = 1  # 4-3-3
        menus.procesar_tecla(pygame.K_RETURN)
        self.assertEqual(menus.formacion_nombre, "4-3-3")

        self.app.procesar_eventos()  # consume la acción pendiente
        self.assertIsNone(menus.consumir_accion())

        self.assertEqual(self.app.juego.formacion_nombre, "4-3-3")
        roles = [
            jugador.rol
            for jugador in self.app.juego.jugadores
            if jugador.equipo is Equipo.LOCAL
        ]
        self.assertEqual(roles.count(Rol.DEFENSA), 4)
        self.assertEqual(roles.count(Rol.MEDIO), 3)
        self.assertEqual(roles.count(Rol.DELANTERO), 3)

    def test_escape_en_el_menu_principal_cierra(self) -> None:
        self._tecla(pygame.K_ESCAPE)
        self.app.procesar_eventos()

        self.assertFalse(self.app.ejecutando)

    def test_dibujar_el_partido_muestra_el_escudo_del_nivel(self) -> None:
        juego = self.app.juego
        juego.estado = Estado.JUGANDO
        juego.jugador_controlado = juego.jugadores[0]

        self.app.vista.dibujar(juego)

        # El marcador incorporó la imagen del escudo del nivel actual.
        self.assertIn(juego.nivel, self.app.vista._escudos_rivales)
        escudo_rival = self.app.vista._escudos_rivales[juego.nivel]
        self.assertEqual(escudo_rival.get_height(), 34)

        # Y el panel es más ancho que el texto del resultado a secas.
        marcador = self.app.vista._crear_superficie_marcador(juego)
        texto = self.app.vista.fuente_marcador.render(
            f"NIVEL {juego.nivel}   ROJO 0 - 0 AZUL",
            True,
            (255, 255, 255),
        )
        self.assertGreater(marcador.get_width(), texto.get_width())

    def test_cada_nivel_cambia_el_escudo_del_marcador(self) -> None:
        juego = self.app.juego
        juego.estado = Estado.JUGANDO
        juego.jugador_controlado = juego.jugadores[0]

        for nivel in range(1, 12):
            juego.nivel = nivel
            self.app.vista._dibujar_marcador(juego)
            self.assertIn(nivel, self.app.vista._escudos_rivales)

        self.assertEqual(len(self.app.vista._escudos_rivales), 11)


if __name__ == "__main__":
    unittest.main()
