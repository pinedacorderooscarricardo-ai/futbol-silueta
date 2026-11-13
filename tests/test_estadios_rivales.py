"""Pruebas de los estadios rivales, sus fotos y su escalado."""

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

from futbol_silueta.estadios_rivales import (
    ESTADIOS_RIVALES,
    cargar_vista,
    cubrir,
    estadio_rival,
    limpiar_cache,
    ruta_vista,
)
from futbol_silueta.niveles import NIVEL_MAXIMO, nivel_por_numero


class EstadiosRivalesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        cls.pantalla = pygame.display.set_mode((100, 100))

    @classmethod
    def tearDownClass(cls) -> None:
        limpiar_cache()
        pygame.quit()

    def setUp(self) -> None:
        limpiar_cache()

    def test_hay_un_estadio_por_nivel(self) -> None:
        self.assertEqual(len(ESTADIOS_RIVALES), NIVEL_MAXIMO)
        self.assertEqual(
            [estadio.nivel for estadio in ESTADIOS_RIVALES],
            list(range(1, NIVEL_MAXIMO + 1)),
        )

    def test_cada_estadio_tiene_club_y_vistas(self) -> None:
        for estadio in ESTADIOS_RIVALES:
            self.assertTrue(estadio.nombre)
            self.assertTrue(estadio.vistas)
            self.assertEqual(
                estadio.club,
                nivel_por_numero(estadio.nivel).rival,
            )

    def test_las_fotos_existen_y_no_se_repiten(self) -> None:
        archivos = [
            vista.archivo
            for estadio in ESTADIOS_RIVALES
            for vista in estadio.vistas
        ]

        self.assertEqual(len(archivos), len(set(archivos)))

        for estadio in ESTADIOS_RIVALES:
            for vista in estadio.vistas:
                self.assertTrue(
                    ruta_vista(vista).is_file(),
                    f"falta {vista.archivo}",
                )

    def test_estadio_rival_limita_el_rango(self) -> None:
        self.assertEqual(estadio_rival(0).nivel, 1)
        self.assertEqual(estadio_rival(NIVEL_MAXIMO + 5).nivel, NIVEL_MAXIMO)
        self.assertEqual(estadio_rival(7).nombre, "Old Trafford")

    def test_cubrir_llena_el_tamano_sin_barras(self) -> None:
        imagen = pygame.Surface((200, 100))
        imagen.fill((30, 90, 150))

        cubierta = cubrir(imagen, (80, 80))

        self.assertEqual(cubierta.get_size(), (80, 80))
        for esquina in (
            (0, 0),
            (79, 0),
            (0, 79),
            (79, 79),
        ):
            color = cubierta.get_at(esquina)[:3]
            for canal, esperado in zip(color, (30, 90, 150), strict=True):
                self.assertLessEqual(abs(canal - esperado), 2)

    def test_cargar_vista_reutiliza_la_cache(self) -> None:
        vista = ESTADIOS_RIVALES[0].vistas[0]

        primera = cargar_vista(vista)
        segunda = cargar_vista(vista)

        self.assertIs(primera, segunda)
        self.assertGreater(primera.get_width(), 0)

        limpiar_cache()
        recargada = cargar_vista(vista)

        self.assertIsNot(recargada, primera)
        self.assertGreater(recargada.get_width(), 0)


if __name__ == "__main__":
    unittest.main()
