"""Pruebas de utilidades: carga de imágenes y tolerancia a fallos."""

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

from futbol_silueta.configuracion import (
    FORMACIONES,
    NOMBRES_FORMACION,
    Equipo,
)
from futbol_silueta.entidades import crear_jugadores
from futbol_silueta.plantilla import (
    JugadorPlantilla,
    plantilla_por_defecto,
)
from futbol_silueta.utilidades import (
    DIRECTORIO_IMAGENES,
    RESERVA_TAMANO,
    cargar_imagen,
)


class CargarImagenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def test_carga_una_imagen_existente(self) -> None:
        ruta = DIRECTORIO_IMAGENES / "escudos" / "escudo_01.jpeg"
        superficie = cargar_imagen(ruta)

        self.assertIsInstance(superficie, pygame.Surface)
        self.assertGreater(superficie.get_width(), 0)

    def test_un_archivo_ausente_devuelve_una_reserva(self) -> None:
        ruta = DIRECTORIO_IMAGENES / "no_existe.jpeg"
        superficie = cargar_imagen(ruta)

        self.assertIsInstance(superficie, pygame.Surface)
        self.assertEqual(
            superficie.get_size(),
            (RESERVA_TAMANO, RESERVA_TAMANO),
        )


class PlantillasIncompletasTests(unittest.TestCase):
    """La plantilla guardada no debe poder dejar el campo a medias."""

    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def _plantilla_recortada(
        self,
        equipo: Equipo,
        tamano: int,
    ) -> tuple[JugadorPlantilla, ...]:
        return plantilla_por_defecto(equipo)[:tamano]

    def test_una_plantilla_corta_se_completa_a_once(self) -> None:
        jugadores = crear_jugadores(
            plantillas={
                equipo: self._plantilla_recortada(equipo, 5)
                for equipo in Equipo
            },
        )

        self.assertEqual(len(jugadores), 22)
        self.assertTrue(
            all(jugador.nombre for jugador in jugadores),
        )

    def test_una_plantilla_larga_se_recorta_a_once(self) -> None:
        defecto = plantilla_por_defecto(Equipo.LOCAL)
        sobrantes = plantilla_por_defecto(Equipo.VISITANTE)
        plantillas = {
            equipo: (*plantilla_por_defecto(equipo), *sobrantes)
            for equipo in Equipo
        }
        del defecto

        jugadores = crear_jugadores(plantillas=plantillas)

        self.assertEqual(len(jugadores), 22)

    def test_sin_plantilla_usa_la_por_defecto(self) -> None:
        self.assertEqual(len(crear_jugadores()), 22)


class FormacionesTests(unittest.TestCase):
    def test_los_nombres_se_derivanel_catalogo(self) -> None:
        self.assertEqual(NOMBRES_FORMACION, tuple(FORMACIONES))
        self.assertIn("4-4-2", FORMACIONES)


if __name__ == "__main__":
    unittest.main()
