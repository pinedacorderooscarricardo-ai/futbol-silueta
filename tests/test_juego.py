"""Pruebas automáticas de Fútbol Silueta."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

# La suite debe funcionar sin ventana ni dispositivo de audio reales.
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

# Permite ejecutar el archivo directamente además de con unittest.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame

from futbol_silueta.configuracion import (
    ALTO,
    ANCHO,
    CAMPO_RECT,
    PORTERIA_CENTRO,
    PRESORES_POR_EQUIPO,
    Equipo,
    Estado,
    Rol,
)
from futbol_silueta.juego import Juego
from futbol_silueta.vista import Vista


class Teclas:
    """Sustituto mínimo de ``pygame.key.get_pressed()`` para las pruebas."""

    def __init__(self, activas: set[int]) -> None:
        self.activas = activas

    def __getitem__(self, tecla: int) -> bool:
        return tecla in self.activas


class JuegoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        cls.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        cls.vista = Vista(cls.pantalla)

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def setUp(self) -> None:
        self.juego = Juego(self.vista)

    def test_jugador_inicial_es_delantero_local(self) -> None:
        control = self.juego.jugador_controlado

        self.assertIsNotNone(control)
        assert control is not None
        self.assertIs(control.equipo, Equipo.LOCAL)
        self.assertIs(control.rol, Rol.DELANTERO)

    def test_gol_conduciendo_el_balon(self) -> None:
        jugador = self.juego.jugador_controlado
        self.assertIsNotNone(jugador)
        assert jugador is not None

        jugador.pos.update(CAMPO_RECT.right - 20, PORTERIA_CENTRO)
        jugador.actualizar_rect()
        jugador.direccion.update(1, 0)
        self.juego.dar_posesion(jugador)

        self.juego.actualizar_balon(1.0 / 60.0)

        self.assertIs(self.juego.estado, Estado.GOL)
        self.assertEqual(self.juego.goles_local, 1)
        self.assertIs(self.juego.ultimo_gol, Equipo.LOCAL)

    def test_transiciones_entretiempo_final_y_revancha(self) -> None:
        juego = self.juego

        juego.tiempo_restante = 0.001
        juego.actualizar(1.0 / 60.0)
        self.assertIs(juego.estado, Estado.ENTRETIEMPO)

        juego._al_pulsar_espacio()
        self.assertIs(juego.estado, Estado.JUGANDO)
        self.assertEqual(juego.mitad, 2)

        juego.tiempo_restante = 0.001
        juego.actualizar(1.0 / 60.0)
        self.assertIs(juego.estado, Estado.FINAL)

        juego._al_pulsar_espacio()
        self.assertIs(juego.estado, Estado.JUGANDO)
        self.assertEqual(juego.mitad, 1)
        self.assertEqual(
            (juego.goles_local, juego.goles_visitante),
            (0, 0),
        )

    def test_pase_cambia_el_control(self) -> None:
        control = self.juego.jugador_controlado
        self.assertIsNotNone(control)
        assert control is not None

        self.juego.dar_posesion(control)
        receptor = self.juego.obtener_receptor_mas_cercano(control)
        self.assertIsNotNone(receptor)
        assert receptor is not None

        self.juego.pasar_al_companero_mas_cercano()

        self.assertIsNone(self.juego.portador)
        self.assertIs(self.juego.jugador_controlado, receptor)
        self.assertGreater(self.juego.balon.vel.length_squared(), 0.0)

    def test_sprint_gasta_y_recarga_energia(self) -> None:
        energia_inicial = self.juego.energia_actual

        self.juego.actualizar_jugador(
            1.0 / 60.0,
            Teclas({pygame.K_d, pygame.K_LSHIFT}),
        )
        energia_tras_sprint = self.juego.energia_actual
        self.assertLess(energia_tras_sprint, energia_inicial)

        self.juego.actualizar_jugador(
            1.0 / 60.0,
            Teclas(set()),
        )
        self.assertGreater(self.juego.energia_actual, energia_tras_sprint)

    def test_perseguidores_excluyen_al_jugador_controlado(self) -> None:
        control = self.juego.jugador_controlado
        self.assertIsNotNone(control)
        assert control is not None

        # Colocar al humano como el local más cercano al balón.
        control.pos.update(CAMPO_RECT.center)
        control.actualizar_rect()

        visitante = next(
            jugador
            for jugador in self.juego.jugadores
            if jugador.equipo is Equipo.VISITANTE
            and jugador.rol is not Rol.PORTERO
        )
        self.juego.dar_posesion(visitante)

        perseguidores = self.juego._elegir_perseguidores(Equipo.VISITANTE)

        self.assertEqual(len(perseguidores), PRESORES_POR_EQUIPO)
        self.assertNotIn(control, perseguidores)
        self.assertTrue(
            all(jugador.equipo is Equipo.LOCAL for jugador in perseguidores)
        )

    def test_las_colisiones_separan_a_los_jugadores(self) -> None:
        jugador_a, jugador_b = self.juego.jugadores[0:2]
        jugador_b.pos.update(jugador_a.pos)
        jugador_a.actualizar_rect()
        jugador_b.actualizar_rect()

        self.juego._resolver_colisiones()

        distancia = jugador_a.pos.distance_to(jugador_b.pos)
        self.assertGreater(distancia, 0.0)
        self.assertLessEqual(distancia, jugador_a.RADIO * 2)

    def test_dibujo_y_simulacion_sin_errores(self) -> None:
        for _ in range(180):
            self.juego.actualizar(1.0 / 60.0)
            self.vista.dibujar(self.juego)

        self.assertIsInstance(self.juego.estado, Estado)


if __name__ == "__main__":
    unittest.main()
