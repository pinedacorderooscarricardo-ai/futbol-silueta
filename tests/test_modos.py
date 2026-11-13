"""Pruebas headless de los modos de juego y sus torneos."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame

from futbol_silueta.configuracion import (
    ANCHO,
    ENERGIA_MAXIMA,
    Equipo,
)
from futbol_silueta.juego import Juego
from futbol_silueta.modos import (
    Copa,
    Campeones,
    Liga,
    ModoJuego,
    Solicitud,
    Supervivencia,
)


class LigaTests(unittest.TestCase):
    def test_juega_contra_todos_los_rivales(self) -> None:
        liga = Liga()
        rivales = []

        for _ in range(11):
            rivales.append(liga.rival_del_partido())
            liga.registrar(1, 0)

        self.assertEqual(sorted(rivales), list(range(1, 12)))
        self.assertTrue(liga.terminado)

    def test_la_tabla_suma_puntos_y_se_ordena(self) -> None:
        liga = Liga()
        liga.registrar(3, 0)  # jornada 1: goleada
        liga.registrar(0, 0)  # jornada 2: empate

        self.assertEqual(liga.tabla[0].puntos, 4)
        self.assertEqual(liga.tabla[0].pg, 1)
        self.assertEqual(liga.tabla[0].pe, 1)

        texto = liga.texto_tras_partido()
        self.assertIn("Jornada 2/11", texto)

    def test_campeon_tras_todas_las_jornadas(self) -> None:
        liga = Liga()

        for _ in range(11):
            liga.registrar(2, 0)

        self.assertTrue(liga.terminado)
        self.assertIn("CAMPEÓN DE LIGA", liga.texto_final_torneo())

    def test_la_etiqueta_no_supera_las_jornadas(self) -> None:
        liga = Liga()

        for _ in range(11):
            liga.registrar(1, 0)

        self.assertIn("J11/11", liga.etiqueta())


class CopaTests(unittest.TestCase):
    def test_ganar_tres_rondas_da_el_titulo(self) -> None:
        copa = Copa()
        rondas = []

        while not copa.terminado:
            rondas.append(copa.etiqueta())
            copa.registrar(1, 0)

        self.assertEqual(len(rondas), 3)
        self.assertIn("Cuartos de final", rondas[0])
        self.assertIn("Final", rondas[2])
        self.assertIn("¡CAMPEÓN DE LA COPA!", copa.texto_final_torneo())

    def test_perder_elimina(self) -> None:
        copa = Copa()
        copa.registrar(0, 2)

        self.assertTrue(copa.terminado)
        self.assertIn("ELIMINADO", copa.texto_final_torneo())

    def test_la_etiqueta_sigue_valida_tras_ganar_la_final(self) -> None:
        copa = Copa()

        while not copa.terminado:
            copa.registrar(1, 0)

        # La ronda quedó tras la última: el marcador puede seguir
        # pidiendo la etiqueta en la pantalla final sin romperse.
        self.assertIn("Final", copa.etiqueta())

    def test_ganar_un_cruce_como_visitante_avanza(self) -> None:
        # Un torneo restaurado puede traer al jugador como visitante del
        # cruce: los goles del juego (siempre su perspectiva) deben
        # traducirse al cruce antes de decidir el ganador.
        copa = Copa()
        copa._emparejamientos = [(5, 0), (2, 3), (4, 6), (7, 1)]

        copa.registrar(3, 0)

        self.assertFalse(copa.eliminado)
        self.assertIn(0, copa._emparejamientos[0])


class CampeonesTests(unittest.TestCase):
    def test_ganar_todo_da_el_titulo(self) -> None:
        torneo = Campeones()

        for _ in range(3):
            torneo.registrar(2, 0)

        self.assertFalse(torneo.terminado)
        self.assertEqual(torneo._fase, Campeones.FASE_SEMIS)

        torneo.registrar(1, 0)
        self.assertEqual(torneo._fase, Campeones.FASE_FINAL)
        self.assertFalse(torneo.terminado)

        torneo.registrar(2, 1)
        self.assertTrue(torneo.terminado)
        self.assertIn("¡CAMPEÓN", torneo.texto_final_torneo())

    def test_quedar_fuera_de_grupos_elimina(self) -> None:
        torneo = Campeones()

        for _ in range(3):
            torneo.registrar(0, 5)

        self.assertTrue(torneo.terminado)
        self.assertIn("ELIMINADO", torneo.texto_final_torneo())

    def test_ganar_la_semifinal_como_visitante_del_cruce(self) -> None:
        # Segundo del grupo: en el cruce le toca ser visitante. Ganar
        # 3-0 tiene que llevarlo a la final, no eliminarlo: los goles
        # del juego son siempre del punto de vista del jugador.
        torneo = Campeones()
        torneo._fase = Campeones.FASE_SEMIS
        torneo._semifinales = ((11, 3), (9, 0))

        torneo.registrar(3, 0)

        self.assertFalse(torneo.eliminado)
        self.assertIn(0, torneo._final)
        self.assertIn("Semifinal superada", torneo.texto_tras_partido())

    def test_perder_la_semifinal_como_visitante_elimina(self) -> None:
        torneo = Campeones()
        torneo._fase = Campeones.FASE_SEMIS
        torneo._semifinales = ((11, 3), (9, 0))

        torneo.registrar(0, 2)

        self.assertTrue(torneo.eliminado)
        self.assertTrue(torneo.terminado)
        self.assertIn("SEMIFINAL", torneo.texto_final_torneo())
        self.assertNotIn("fase de grupos", torneo.texto_final_torneo())

    def test_ganar_la_final_como_visitante_da_el_titulo(self) -> None:
        torneo = Campeones()
        torneo._fase = Campeones.FASE_FINAL
        torneo._final = (9, 0)

        torneo.registrar(2, 1)

        self.assertTrue(torneo.campeon)
        self.assertTrue(torneo.terminado)
        self.assertIn("¡CAMPEÓN", torneo.texto_final_torneo())

    def test_rival_de_la_final_es_el_otro_finalista(self) -> None:
        torneo = Campeones()
        torneo._fase = Campeones.FASE_FINAL

        torneo._final = (9, 0)
        self.assertEqual(torneo.rival_del_partido(), 9)

        torneo._final = (0, 9)
        self.assertEqual(torneo.rival_del_partido(), 9)

    def test_clasificado_anuncia_la_semifinal(self) -> None:
        torneo = Campeones()
        torneo._fase = Campeones.FASE_SEMIS
        torneo._semifinales = ((0, 3), (9, 11))
        torneo._final = None

        self.assertIn("semifinal", torneo.texto_tras_partido().lower())


class SupervivenciaTests(unittest.TestCase):
    def test_ganar_subel_nivel_y_perder_termina(self) -> None:
        racha = Supervivencia()
        self.assertEqual(racha.rival_del_partido(), 1)

        racha.registrar(2, 1)
        self.assertEqual(racha.racha, 1)
        self.assertEqual(racha.rival_del_partido(), 2)
        self.assertFalse(racha.terminado)

        racha.registrar(0, 1)
        self.assertTrue(racha.terminado)
        self.assertIn("racha de 1", racha.texto_final_torneo())


class JuegoModoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        pygame.display.set_mode((ANCHO, 650))

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def setUp(self) -> None:
        self.juego = Juego(None)

    def _cerrar_partido(self, gl: int, gv: int) -> None:
        self.juego.goles_local = gl
        self.juego.goles_visitante = gv
        self.juego.mitad = 2
        self.juego._terminar_mitad()

    def test_reiniciar_un_torneo_terminado_empieza_otro(self) -> None:
        self.juego.iniciar_modo(ModoJuego.LIGA)

        for _ in range(11):
            self.juego.torneo.registrar(1, 0)

        self.assertTrue(self.juego.torneo.terminado)

        # ESC -> "Reiniciar partido" en la pantalla final no debe pedir
        # el rival de una jornada que ya no existe.
        self.juego.nueva_partida()

        self.assertFalse(self.juego.torneo.terminado)
        self.assertEqual(
            self.juego.nivel,
            self.juego.torneo.rival_del_partido(),
        )

    def test_la_campana_sigue_igual(self) -> None:
        self.juego.iniciar_modo(ModoJuego.CAMPANA)

        self.assertIsNone(self.juego.torneo)
        self._cerrar_partido(1, 0)
        self.juego._continuar_tras_final()

        self.assertEqual(self.juego.nivel, 2)
        self.assertIsNone(self.juego.solicitud)

    def test_la_liga_avanza_jornada_a_jornada(self) -> None:
        self.juego.iniciar_modo(ModoJuego.LIGA)
        self.assertEqual(self.juego.nivel, 1)

        self._cerrar_partido(2, 0)
        self.assertEqual(self.juego.torneo.jornada, 1)
        self.assertIn("Jornada 1/11", self.juego.texto_final)

        self.juego._continuar_tras_final()
        self.assertEqual(self.juego.nivel, self.juego.torneo.rival_del_partido())

    def test_liga_terminada_pide_volver_al_menu(self) -> None:
        self.juego.iniciar_modo(ModoJuego.LIGA)

        for _ in range(11):
            self._cerrar_partido(2, 0)
            self.juego._continuar_tras_final()

        # El primer ESPACIO muestra el desenlace; el segundo vuelve.
        self.assertIn("CAMPEÓN", self.juego.texto_final)
        self.assertIsNone(self.juego.solicitud)

        self.juego._continuar_tras_final()
        self.assertIs(self.juego.solicitud, Solicitud.MENU_PRINCIPAL)

    def test_supervivencia_termina_al_perder(self) -> None:
        self.juego.iniciar_modo(ModoJuego.SUPERVIVENCIA)

        self._cerrar_partido(3, 1)
        self.juego._continuar_tras_final()
        self.assertEqual(self.juego.nivel, 2)

        self._cerrar_partido(0, 2)
        self.juego._continuar_tras_final()
        self.assertIn("racha de 1", self.juego.texto_final)
        self.assertIsNone(self.juego.solicitud)

        self.juego._continuar_tras_final()
        self.assertIs(self.juego.solicitud, Solicitud.MENU_PRINCIPAL)

    def test_el_entrenamiento_no_consume_el_reloj(self) -> None:
        self.juego.iniciar_modo(ModoJuego.ENTRENAMIENTO)
        restante = self.juego.tiempo_restante

        for _ in range(30):
            self.juego.actualizar(1 / 60)

        self.assertEqual(self.juego.tiempo_restante, restante)
        self.assertEqual(self.juego.mitad, 1)

    def test_dos_jugadores_tiene_control_y_energia_propios(self) -> None:
        self.juego.iniciar_modo(ModoJuego.DOS_JUGADORES)

        self.assertIsNotNone(self.juego.jugador_controlado)
        self.assertIsNotNone(self.juego.jugador_controlado_2)
        self.assertIs(self.juego.jugador_controlado_2.equipo, Equipo.VISITANTE)
        self.assertIs(self.juego.jugador_controlado.equipo, Equipo.LOCAL)
        self.assertEqual(self.juego.energia_2, ENERGIA_MAXIMA)

    def test_enter_del_segundo_jugador_chuta(self) -> None:
        self.juego.iniciar_modo(ModoJuego.DOS_JUGADORES)
        p2 = self.juego.jugador_controlado_2

        # Balón a los pies del segundo jugador y mira hacia el campo.
        self.juego.dar_posesion(p2)
        self.assertIs(self.juego.portador, p2)

        self.juego.procesar_tecla(pygame.K_RETURN)

        self.assertIsNone(self.juego.portador)


if __name__ == "__main__":
    unittest.main()
