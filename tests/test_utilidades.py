"""Pruebas de utilidades: carga de imágenes y tolerancia a fallos."""

from __future__ import annotations

import io
import os
import sys
import unittest
from contextlib import redirect_stderr
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
    NUMERO_SUPLENTES,
    TITULARES_POR_EQUIPO,
    Equipo,
    Rol,
)
from futbol_silueta.entidades import crear_jugadores
from futbol_silueta.plantilla import (
    PRESETS_FUERZA,
    PRESETS_VELOCIDAD,
    JugadorPlantilla,
    normalizar_plantilla,
    plantilla_por_defecto,
    suplentes_por_defecto,
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

        with redirect_stderr(io.StringIO()) as errores:
            superficie = cargar_imagen(ruta)

        self.assertIsInstance(superficie, pygame.Surface)
        self.assertEqual(
            superficie.get_size(),
            (RESERVA_TAMANO, RESERVA_TAMANO),
        )
        self.assertIn("no se pudo cargar", errores.getvalue())


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

    def test_los_datos_raros_se_corrigen(self) -> None:
        fichas = list(plantilla_por_defecto(Equipo.LOCAL))
        fichas[0] = fichas[0]._replace(
            nombre=None,
            dorsal=0,
            rol="no-existe",
            x=5.0,
            y=-2.0,
            factor_velocidad=float("nan"),
            factor_fuerza=999.0,
        )

        normalizadas = normalizar_plantilla(fichas, Equipo.LOCAL)
        defecto = plantilla_por_defecto(Equipo.LOCAL)[0]
        ficha = normalizadas[0]

        self.assertEqual(len(normalizadas), 11)
        self.assertEqual(ficha.nombre, defecto.nombre)
        self.assertEqual(ficha.dorsal, 1)
        self.assertIs(ficha.rol, Rol.PORTERO)
        self.assertEqual((ficha.x, ficha.y), (1.0, 0.0))
        self.assertEqual(ficha.factor_velocidad, PRESETS_VELOCIDAD[1][1])
        self.assertEqual(ficha.factor_fuerza, PRESETS_FUERZA[-1][1])


class FormacionesTests(unittest.TestCase):
    def test_los_nombres_se_derivanel_catalogo(self) -> None:
        self.assertEqual(NOMBRES_FORMACION, tuple(FORMACIONES))
        self.assertIn("4-4-2", FORMACIONES)


class SuplentesTests(unittest.TestCase):
    """El banquillo: la plantilla completa queda en 18 jugadores."""

    def test_el_banquillo_por_defecto_tiene_siete_fichas(self) -> None:
        for equipo in Equipo:
            suplentes = suplentes_por_defecto(equipo)
            dorsales = [ficha.dorsal for ficha in suplentes]

            self.assertEqual(len(suplentes), NUMERO_SUPLENTES)
            self.assertEqual(
                dorsales,
                list(range(TITULARES_POR_EQUIPO + 1, 18 + 1)),
            )

    def test_el_banquillo_cubre_todos_los_roles(self) -> None:
        roles = [ficha.rol for ficha in suplentes_por_defecto(Equipo.LOCAL)]

        self.assertEqual(roles.count(Rol.PORTERO), 1)
        self.assertEqual(roles.count(Rol.DEFENSA), 2)
        self.assertEqual(roles.count(Rol.MEDIO), 2)
        self.assertEqual(roles.count(Rol.DELANTERO), 2)

    def test_los_suplentes_no_repiten_nombres_ni_dorsales(self) -> None:
        for equipo in Equipo:
            fichas = (*plantilla_por_defecto(equipo), *suplentes_por_defecto(equipo))
            nombres = [ficha.nombre for ficha in fichas]
            dorsales = [ficha.dorsal for ficha in fichas]

            self.assertEqual(len(set(nombres)), 18)
            self.assertEqual(len(set(dorsales)), 18)


if __name__ == "__main__":
    unittest.main()
