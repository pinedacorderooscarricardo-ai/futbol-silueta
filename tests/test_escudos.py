"""Pruebas automáticas de los escudos y la personalización."""

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

from futbol_silueta.escudos import (
    COLORES_ESCUDO_POR_NIVEL,
    ESCUDO_PRESETS,
    FORMAS_ESCUDO,
    Escudo,
    FormaEscudo,
    cargar_escudo,
    nombre_archivo_escudo,
)
from futbol_silueta.niveles import NIVEL_MAXIMO, NIVELES
from futbol_silueta.utilidades import DIRECTORIO_IMAGENES


class EscudoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        cls.pantalla = pygame.display.set_mode((1000, 650))

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def test_nombre_del_escudo_por_nivel(self) -> None:
        self.assertEqual(nombre_archivo_escudo(1), "escudo_01.jpeg")
        self.assertEqual(nombre_archivo_escudo(11), "escudo_11.jpeg")
        self.assertEqual(nombre_archivo_escudo(3), "escudo_03.jpeg")

    def test_carga_del_escudo_de_un_nivel(self) -> None:
        superficie = cargar_escudo(1)

        self.assertIsInstance(superficie, pygame.Surface)
        self.assertEqual(superficie.get_size(), (1600, 1460))

    def test_escudo_de_nivel_sigue_su_color_base(self) -> None:
        escudo = Escudo.crear_para_nivel(2)

        self.assertEqual(escudo.nivel, 2)
        self.assertEqual(escudo.color, COLORES_ESCUDO_POR_NIVEL[2][0])
        self.assertEqual(escudo.color_borde, COLORES_ESCUDO_POR_NIVEL[2][1])

    def test_escudo_personalizable(self) -> None:
        escudo = Escudo.crear_para_nivel(1)

        escudo.cambiar_colores((10, 20, 30), (40, 50, 60))
        self.assertEqual(escudo.color, (10, 20, 30))
        self.assertEqual(escudo.color_borde, (40, 50, 60))

    def test_el_grosor_del_borde_crece_con_el_nivel(self) -> None:
        escudo = Escudo.crear_para_nivel(1)
        grosor_1 = 1 + escudo.nivel
        escudo.nivel = 4
        grosor_4 = 1 + escudo.nivel

        self.assertEqual(grosor_1, 2)
        self.assertEqual(grosor_4, 5)

    def test_dibujar_el_escudo_en_la_pantalla(self) -> None:
        escudo = Escudo.crear_para_nivel(1)
        centro = (500, 300)
        escudo.dibujar(self.pantalla, centro, escala=8.0)

        self.assertIsInstance(self.pantalla, pygame.Surface)

    def test_cada_nivel_tiene_su_color_de_escudo(self) -> None:
        for nivel in range(1, NIVEL_MAXIMO + 1):
            self.assertIn(nivel, COLORES_ESCUDO_POR_NIVEL)
            self.assertEqual(
                Escudo.crear_para_nivel(nivel).color,
                COLORES_ESCUDO_POR_NIVEL[nivel][0],
            )

    def test_cada_nivel_apunta_a_una_imagen_existente(self) -> None:
        for nivel in NIVELES:
            ruta = DIRECTORIO_IMAGENES / "escudos" / nivel.escudo
            self.assertTrue(ruta.is_file(), ruta)

    def test_el_escudo_tiene_una_forma_personalizable(self) -> None:
        escudo = Escudo.crear_para_nivel(1)

        self.assertIs(escudo.forma, FormaEscudo.CLASICA)

        for forma in FORMAS_ESCUDO:
            escudo.cambiar_forma(forma)
            self.assertIs(escudo.forma, forma)
            escudo.dibujar(self.pantalla, (500, 300), escala=4.0)

    def test_crear_para_nivel_acepta_la_forma(self) -> None:
        escudo = Escudo.crear_para_nivel(3, forma=FormaEscudo.REDONDA)

        self.assertIs(escudo.forma, FormaEscudo.REDONDA)
        self.assertEqual(escudo.color, COLORES_ESCUDO_POR_NIVEL[3][0])

    def test_los_once_escudos_cargan(self) -> None:
        for nivel in range(1, NIVEL_MAXIMO + 1):
            superficie = cargar_escudo(nivel)

            self.assertIsInstance(superficie, pygame.Surface)


if __name__ == "__main__":
    unittest.main()
