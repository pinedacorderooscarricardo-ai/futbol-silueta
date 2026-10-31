"""Pruebas headless de los menús y sus botones."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

# La suite debe funcionar sin ventana ni dispositivo de audio reales.
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame

from futbol_silueta.configuracion import ALTO, ANCHO, Equipo, Rol
from futbol_silueta.escudos import ESCUDO_PRESETS, FORMAS_ESCUDO
from futbol_silueta.menus import Accion, Menus, Pantalla


class MenusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        cls.pantalla = pygame.display.set_mode((ANCHO, ALTO))

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def setUp(self) -> None:
        self.menus = Menus()

    def _evento_raton(
        self,
        tipo: int,
        posicion: tuple[int, int],
        boton: int = 1,
    ) -> pygame.event.Event:
        return pygame.event.Event(
            tipo,
            {"pos": posicion, "button": boton},
        )

    def test_inicia_en_el_menu_principal(self) -> None:
        self.assertIs(self.menus.pantalla, Pantalla.PRINCIPAL)
        boton = self.menus.boton_actual

        self.assertIsNotNone(boton)
        assert boton is not None
        self.assertIs(boton.accion, Accion.JUGAR)
        self.assertAlmostEqual(boton.rect.centerx, ANCHO // 2, delta=3)

    def test_los_hotspots_caben_en_la_pantalla(self) -> None:
        for pantalla in (Pantalla.PRINCIPAL, Pantalla.PAUSA):
            for boton in self.menus.botones[pantalla]:
                self.assertGreaterEqual(boton.rect.left, 0)
                self.assertGreaterEqual(boton.rect.top, 0)
                self.assertLessEqual(boton.rect.right, ANCHO)
                self.assertLessEqual(boton.rect.bottom, ALTO)

    def test_click_en_jugar_abre_el_partido(self) -> None:
        rect = self.menus.botones[Pantalla.PRINCIPAL][0].rect
        evento = self._evento_raton(
            pygame.MOUSEBUTTONDOWN,
            rect.center,
        )

        self.menus.procesar_evento(evento)

        self.assertIs(self.menus.pantalla, Pantalla.PARTIDO)
        self.assertIs(self.menus.consumir_accion(), Accion.JUGAR)
        self.assertIsNone(self.menus.consumir_accion())

    def test_click_en_todos_los_botones_principales(self) -> None:
        casos = (
            (0, Pantalla.PARTIDO, Accion.JUGAR),
            (1, Pantalla.OPCIONES, None),
            (2, Pantalla.AYUDA, None),
            (3, Pantalla.PRINCIPAL, Accion.SALIR),
        )

        for indice, pantalla, accion in casos:
            menus = Menus()
            rect = menus.botones[Pantalla.PRINCIPAL][indice].rect
            menus.procesar_evento(
                self._evento_raton(
                    pygame.MOUSEBUTTONDOWN,
                    rect.center,
                )
            )

            self.assertIs(menus.pantalla, pantalla, f"botón {indice}")
            self.assertIs(
                menus.consumir_accion(),
                accion,
                f"botón {indice}",
            )

    def test_click_en_todos_los_botones_de_pausa(self) -> None:
        casos = (
            (0, Pantalla.PARTIDO, None),
            (1, Pantalla.PARTIDO, Accion.REINICIAR),
            (2, Pantalla.OPCIONES, None),
            (3, Pantalla.PRINCIPAL, Accion.MENU_PRINCIPAL),
        )

        for indice, pantalla, accion in casos:
            menus = Menus()
            menus.abrir_pausa()
            rect = menus.botones[Pantalla.PAUSA][indice].rect
            menus.procesar_evento(
                self._evento_raton(
                    pygame.MOUSEBUTTONDOWN,
                    rect.center,
                )
            )

            self.assertIs(menus.pantalla, pantalla, f"botón {indice}")
            self.assertIs(
                menus.consumir_accion(),
                accion,
                f"botón {indice}",
            )

            if indice == 2:
                menus.procesar_tecla(pygame.K_ESCAPE)
                self.assertIs(menus.pantalla, Pantalla.PAUSA)

    def test_hover_actualiza_la_seleccion(self) -> None:
        rect = self.menus.botones[Pantalla.PRINCIPAL][1].rect
        evento = self._evento_raton(pygame.MOUSEMOTION, rect.center)

        self.menus.procesar_evento(evento)

        boton = self.menus.boton_actual
        self.assertIsNotNone(boton)
        assert boton is not None
        self.assertIs(boton.accion, Accion.OPCIONES)

    def test_teclado_navega_y_abre_opciones(self) -> None:
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)

        self.assertIs(self.menus.pantalla, Pantalla.OPCIONES)
        self.menus.procesar_tecla(pygame.K_ESCAPE)
        self.assertIs(self.menus.pantalla, Pantalla.PRINCIPAL)

    def test_opciones_cambia_el_sonido_y_vuelve(self) -> None:
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)
        self.assertTrue(self.menus.sonido_activado)

        self.menus.procesar_tecla(pygame.K_RETURN)
        self.assertFalse(self.menus.sonido_activado)
        self.assertEqual(
            self.menus.boton_actual.etiqueta,
            "Sonido: DESACTIVADO",
        )

        # "Volver" es el sexto botón de Opciones, tras Tácticas,
        # Uniformes, escudo y el editor de jugadores.
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)
        self.assertIs(self.menus.pantalla, Pantalla.PRINCIPAL)

        # El ajuste se conserva al volver a entrar.
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)
        self.assertFalse(self.menus.sonido_activado)

    def test_opciones_abren_el_escudo_y_aplican_un_preset(self) -> None:
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)
        self.assertIs(self.menus.pantalla, Pantalla.OPCIONES)

        # El escudo es el cuarto botón de Opciones, tras Tácticas y
        # Uniformes.
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)
        self.assertIs(self.menus.pantalla, Pantalla.ESCUDO)

        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)

        color, color_borde, forma = self.menus.escudo_seleccionado
        self.assertEqual(color, ESCUDO_PRESETS[1][1])
        self.assertEqual(color_borde, ESCUDO_PRESETS[1][2])
        self.assertEqual(forma, FORMAS_ESCUDO[0])

        # La primera forma queda aplicada: 6 colores y 3 formas antes de
        # Volver, así que hay que bajar cinco veces desde el segundo color.
        for _ in range(5):
            self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)

        _color, _borde, forma = self.menus.escudo_seleccionado
        self.assertEqual(forma, FORMAS_ESCUDO[0])

        self.menus.procesar_tecla(pygame.K_ESCAPE)
        self.assertIs(self.menus.pantalla, Pantalla.OPCIONES)

    def test_tacticas_aplica_una_formacion_a_las_fichas(self) -> None:
        self.menus.procesar_tecla(pygame.K_DOWN)  # Opciones
        self.menus.procesar_tecla(pygame.K_RETURN)
        self.menus.procesar_tecla(pygame.K_DOWN)  # Tácticas
        self.menus.procesar_tecla(pygame.K_RETURN)
        self.assertIs(self.menus.pantalla, Pantalla.TACTICA)

        # Segunda formación de la lista: 4-3-3.
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)

        self.assertEqual(self.menus.formacion_nombre, "4-3-3")
        self.assertIs(self.menus.consumir_accion(), Accion.FORMACION)

        for equipo in (Equipo.LOCAL, Equipo.VISITANTE):
            fichas = self.menus.plantillas_editables[equipo]
            roles = [ficha.rol for ficha in fichas]

            self.assertEqual(len(fichas), 11)
            self.assertEqual(roles.count(Rol.PORTERO), 1)
            self.assertEqual(roles.count(Rol.DEFENSA), 4)
            self.assertEqual(roles.count(Rol.MEDIO), 3)
            self.assertEqual(roles.count(Rol.DELANTERO), 3)

        # La identidad de cada jugador se conserva al recolocar.
        local = self.menus.plantillas_editables[Equipo.LOCAL]
        self.assertEqual(local[0].nombre, "Cabrera")
        self.assertEqual(local[0].dorsal, 1)
        self.assertIs(local[0].rol, Rol.PORTERO)

    def test_volver_encadena_pantallas_sin_atascarse(self) -> None:
        # Opciones -> Escudo -> ESC -> ESC: de regreso al principal.
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_DOWN)  # Personalizar escudo
        self.menus.procesar_tecla(pygame.K_RETURN)
        self.assertIs(self.menus.pantalla, Pantalla.ESCUDO)

        self.menus.procesar_tecla(pygame.K_ESCAPE)
        self.assertIs(self.menus.pantalla, Pantalla.OPCIONES)
        self.menus.procesar_tecla(pygame.K_ESCAPE)
        self.assertIs(self.menus.pantalla, Pantalla.PRINCIPAL)

        # Y desde la pausa, Configuración vuelve a la pausa.
        self.menus.abrir_pausa()
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_DOWN)  # Configuración
        self.menus.procesar_tecla(pygame.K_RETURN)
        self.assertIs(self.menus.pantalla, Pantalla.OPCIONES)
        self.menus.procesar_tecla(pygame.K_ESCAPE)
        self.assertIs(self.menus.pantalla, Pantalla.PAUSA)

    def test_ayuda_muestra_los_controles_y_vuelve(self) -> None:
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)

        self.assertIs(self.menus.pantalla, Pantalla.AYUDA)
        self.assertEqual(len(self.menus.botones_actuales), 1)

        self.menus.procesar_tecla(pygame.K_RETURN)
        self.assertIs(self.menus.pantalla, Pantalla.PRINCIPAL)

    def test_pausa_continuar_reiniciar_y_menu(self) -> None:
        self.menus.abrir_pausa()
        self.assertIs(self.menus.pantalla, Pantalla.PAUSA)

        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)

        self.assertIs(self.menus.pantalla, Pantalla.PARTIDO)
        self.assertIs(self.menus.consumir_accion(), Accion.REINICIAR)

        self.menus.abrir_pausa()
        for _ in range(3):
            self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)

        self.assertIs(self.menus.pantalla, Pantalla.PRINCIPAL)
        self.assertIs(
            self.menus.consumir_accion(),
            Accion.MENU_PRINCIPAL,
        )

        self.menus.abrir_pausa()
        self.menus.procesar_tecla(pygame.K_ESCAPE)
        self.assertIs(self.menus.pantalla, Pantalla.PARTIDO)

    def test_escape_en_el_menu_principal_pide_salir(self) -> None:
        self.menus.procesar_tecla(pygame.K_ESCAPE)

        self.assertIs(self.menus.pantalla, Pantalla.PRINCIPAL)
        self.assertIs(self.menus.consumir_accion(), Accion.SALIR)
        self.assertIsNone(self.menus.consumir_accion())

    def test_dibuja_todas_las_pantallas(self) -> None:
        for pantalla in (
            Pantalla.PRINCIPAL,
            Pantalla.OPCIONES,
            Pantalla.ESCUDO,
            Pantalla.UNIFORME,
            Pantalla.EDITOR,
            Pantalla.TACTICA,
            Pantalla.AYUDA,
            Pantalla.PAUSA,
        ):
            self.menus.pantalla = pantalla
            self.menus.indice = 0
            self.menus.dibujar(self.pantalla)

        self.assertIsNotNone(pygame.display.get_surface())


if __name__ == "__main__":
    unittest.main()
