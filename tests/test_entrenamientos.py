"""Pruebas headless de los ejercicios con premio y su integración."""

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
from futbol_silueta.configuracion import ALTO, ANCHO, CAMPO_RECT
from futbol_silueta.entrenamientos import (
    ENTRENAMIENTOS,
    FaseEntrenamiento,
    SesionEntrenamiento,
    TipoEntrenamiento,
    definicion_entrenamiento,
)
from futbol_silueta.guardado import Guardado
from futbol_silueta.menus import Accion, Pantalla
from futbol_silueta.modos import ModoJuego


class EntrenamientoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        cls.pantalla = pygame.display.set_mode((ANCHO, ALTO))

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def setUp(self) -> None:
        pygame.event.clear()
        directorio = tempfile.TemporaryDirectory()
        self.addCleanup(directorio.cleanup)
        self.guardado = Guardado(Path(directorio.name) / "entrenamientos.sqlite")
        self.addCleanup(self.guardado.cerrar)
        self.app = Aplicacion(self.pantalla, guardado=self.guardado)

    def _abrir_ejercicio(self, accion: Accion) -> SesionEntrenamiento:
        self.app.menus._ejecutar(accion)
        self.app._ejecutar_accion_pendiente()
        sesion = self.app.entrenamiento
        self.assertIsNotNone(sesion)
        assert sesion is not None
        self.assertIs(self.app.menus.pantalla, Pantalla.ENTRENAMIENTO_ACTIVO)
        return sesion

    def test_las_tres_definiciones_tienen_meta_y_premio(self) -> None:
        self.assertEqual(len(ENTRENAMIENTOS), 3)

        for definicion in ENTRENAMIENTOS:
            self.assertGreater(definicion.intentos, 0)
            self.assertGreater(definicion.objetivo, 0)
            self.assertLessEqual(definicion.objetivo, definicion.intentos)
            self.assertGreater(definicion.recompensa, 0)
            self.assertGreater(definicion.monedas_por_gol, 0)

    def test_las_monedas_solo_se_ganan_al_cumplir_la_meta(self) -> None:
        sesion = SesionEntrenamiento(TipoEntrenamiento.TIROS)

        sesion.goles = definicion_entrenamiento(
            TipoEntrenamiento.TIROS
        ).objetivo - 1
        self.assertEqual(sesion.monedas_ganadas, 0)

        sesion.goles += 1
        definicion = definicion_entrenamiento(TipoEntrenamiento.TIROS)
        self.assertEqual(
            sesion.monedas_ganadas,
            definicion.recompensa
            + definicion.monedas_por_gol * sesion.goles,
        )

    def test_completar_el_ejercicio_paga_una_sola_vez(self) -> None:
        sesion = self._abrir_ejercicio(Accion.TIROS)
        sesion.goles = 4
        sesion._finalizar()

        self.assertIs(sesion.fase, FaseEntrenamiento.FINAL)
        self.assertTrue(sesion.exito)

        self.app.actualizar(0.0)
        premio = 40 + 8 * 4
        self.assertEqual(self.app.menus.monedas, premio)
        self.assertEqual(sesion.monedas, premio)

        # Otro fotograma con la sesión terminada no vuelve a pagar.
        self.app.actualizar(0.0)
        self.assertEqual(self.app.menus.monedas, premio)

    def test_repetir_la_sesion_permite_volver_a_ganar(self) -> None:
        sesion = self._abrir_ejercicio(Accion.PENALES)
        sesion.goles = 3
        sesion._finalizar()
        self.app.actualizar(0.0)
        primer_pago = self.app.menus.monedas

        self.app._procesar_tecla_entrenamiento(pygame.K_SPACE)

        self.assertFalse(sesion.terminado)
        self.assertEqual(sesion.goles, 0)
        self.assertFalse(self.app._entrenamiento_pagado)

        sesion.goles = 3
        sesion._finalizar()
        self.app.actualizar(0.0)
        self.assertGreater(self.app.menus.monedas, primer_pago)

    def test_el_premio_queda_guardado_en_la_base(self) -> None:
        sesion = self._abrir_ejercicio(Accion.DOS_CONTRA_UNO)
        sesion.goles = 3
        sesion._finalizar()
        self.app.actualizar(0.0)

        otros = self.app.menus.__class__()
        self.guardado.cargar_en(otros)
        self.assertEqual(otros.monedas, self.app.menus.monedas)

    def test_escape_vuelve_al_submenu_de_entrenamientos(self) -> None:
        self._abrir_ejercicio(Accion.PENALES)

        self.app._procesar_tecla_entrenamiento(pygame.K_ESCAPE)

        self.assertIsNone(self.app.entrenamiento)
        self.assertIs(self.app.menus.pantalla, Pantalla.ENTRENAMIENTOS)

    def test_el_campo_libre_sigue_siendo_el_modo_de_siempre(self) -> None:
        self.app.menus._ejecutar(Accion.CAMPO_LIBRE)
        self.app._ejecutar_accion_pendiente()

        self.assertIs(self.app.menus.pantalla, Pantalla.PARTIDO)
        self.assertIsNone(self.app.entrenamiento)
        self.assertIs(self.app.juego.modo, ModoJuego.ENTRENAMIENTO)

    def test_la_sesion_se_dibuja_sin_errores(self) -> None:
        sesion = self._abrir_ejercicio(Accion.TIROS)
        sesion.dibujar(self.pantalla)
        self.app.dibujar()

    def test_el_balon_detenido_se_mide_en_segundos_reales(self) -> None:
        sesion = SesionEntrenamiento(TipoEntrenamiento.TIROS)
        sesion._soltar_balon()
        sesion.balon.pos.update(CAMPO_RECT.center)
        sesion.balon.vel.update(0.0, 0.0)

        sesion._comprobar_balon(0.3)
        sesion._comprobar_balon(0.3)
        self.assertAlmostEqual(sesion._tiempo_libre, 0.6)
        self.assertIs(sesion.fase, FaseEntrenamiento.JUGANDO)

        sesion._comprobar_balon(0.3)
        self.assertIs(sesion.fase, FaseEntrenamiento.RESULTADO)
        self.assertEqual(sesion.texto_resultado, "BALÓN PERDIDO")


if __name__ == "__main__":
    unittest.main()
