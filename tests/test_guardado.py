"""Pruebas headless de la base de datos SQLite del juego."""

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

from futbol_silueta.configuracion import ALTO, ANCHO, Equipo
from futbol_silueta.escudos import ESCUDO_PRESETS, FORMAS_ESCUDO
from futbol_silueta.guardado import Guardado
from futbol_silueta.menus import Accion, Boton, Menus
from futbol_silueta.plantilla import PRESETS_VELOCIDAD
from futbol_silueta.uniformes import UNIFORME_PRESETS


class GuardadoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        pygame.display.set_mode((ANCHO, ALTO))

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def setUp(self) -> None:
        directorio = tempfile.TemporaryDirectory()
        self.addCleanup(directorio.cleanup)
        self.ruta = Path(directorio.name) / "prueba.sqlite"

    def abrir(self) -> Guardado:
        """Abre la base de la prueba y registra su cierre."""
        guardado = Guardado(self.ruta)
        self.addCleanup(guardado.cerrar)
        return guardado

    def test_guardar_y_cargar_la_personalizacion(self) -> None:
        menus = Menus()
        menus._ejecutar(Accion.SONIDO)
        menus._ejecutar(
            Accion.ESCUDO,
            Boton(pygame.Rect(0, 0, 1, 1), "", Accion.ESCUDO, valor=2),
        )
        menus._ejecutar(
            Accion.FORMA_ESCUDO,
            Boton(
                pygame.Rect(0, 0, 1, 1),
                "",
                Accion.FORMA_ESCUDO,
                valor=2,
            ),
        )
        menus._ejecutar(
            Accion.PRENDA,
            Boton(pygame.Rect(0, 0, 1, 1), "", Accion.PRENDA, valor="medias"),
        )
        menus._ejecutar(Accion.NUMEROS)
        menus._ejecutar(Accion.CICLAR_JUGADOR)
        menus._ejecutar(Accion.CICLAR_DORSAL)
        menus._ejecutar(Accion.CICLAR_VELOCIDAD)
        menus.formacion_nombre = "4-3-3"

        self.abrir().guardar_desde(menus)

        otros = Menus()
        self.abrir().cargar_en(otros)

        self.assertFalse(otros.sonido_activado)
        self.assertEqual(otros.escudo_color, ESCUDO_PRESETS[2][1])
        self.assertEqual(otros.escudo_forma, FORMAS_ESCUDO[2])
        self.assertEqual(
            otros.uniformes_seleccionados[Equipo.LOCAL].medias,
            UNIFORME_PRESETS[3][1],
        )
        self.assertFalse(otros.numeros_activados)
        self.assertEqual(otros.formacion_nombre, "4-3-3")
        ficha = otros.plantillas_seleccionadas[Equipo.LOCAL][1]
        self.assertEqual(ficha.dorsal, 3)
        self.assertEqual(ficha.factor_velocidad, PRESETS_VELOCIDAD[2][1])

    def test_ciclar_velocidad_guarda_el_factor_correcto(self) -> None:
        menus = Menus()
        menus._ejecutar(Accion.CICLAR_VELOCIDAD)

        self.abrir().guardar_desde(menus)

        otros = Menus()
        self.abrir().cargar_en(otros)
        self.assertEqual(
            otros.plantillas_seleccionadas[Equipo.LOCAL][0].factor_velocidad,
            PRESETS_VELOCIDAD[2][1],
        )

    def test_base_sin_datos_deja_los_valores_por_defecto(self) -> None:
        self.abrir().cerrar()

        menus = Menus()
        self.abrir().cargar_en(menus)

        self.assertTrue(menus.sonido_activado)
        self.assertEqual(
            menus.uniformes_seleccionados[Equipo.VISITANTE].camiseta,
            (40, 80, 200),
        )

    def test_base_indisponible_no_rompe_el_juego(self) -> None:
        guardado = Guardado(
            Path(self.ruta.parent) / "no_existe" / "base.sqlite"
        )
        self.addCleanup(guardado.cerrar)
        self.assertFalse(guardado.disponible)

        menus = Menus()
        menus._ejecutar(Accion.SONIDO)
        guardado.guardar_desde(menus)
        guardado.cargar_en(menus)

        self.assertFalse(guardado.disponible)
        self.assertFalse(menus.sonido_activado)

    def test_datos_corruptos_se_ignoran(self) -> None:
        guardado = self.abrir()
        guardado.guardar_desde(Menus())
        guardado.conexion.execute(
            "UPDATE ajustes SET escudo_forma = 'no-existe' WHERE id = 1"
        )

        menus = Menus()
        self.abrir().cargar_en(menus)

        self.assertEqual(menus.escudo_forma, FORMAS_ESCUDO[0])

    def test_los_veintidos_jugadores_quedan_guardados(self) -> None:
        guardado = self.abrir()
        guardado.guardar_desde(Menus())
        filas = guardado.conexion.execute(
            "SELECT COUNT(*) FROM jugadores"
        ).fetchone()[0]

        self.assertEqual(filas, 22)


if __name__ == "__main__":
    unittest.main()
