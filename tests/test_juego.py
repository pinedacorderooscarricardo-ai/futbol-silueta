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
    DURACION_GOL,
    PORTERIA_CENTRO,
    PRESORES_POR_EQUIPO,
    RADIO_BALON,
    VELOCIDAD_IA,
    Equipo,
    Estado,
    Rol,
)
from futbol_silueta.juego import Juego
from futbol_silueta.estadios import Cesped, Diseno, Estadio, Momento
from futbol_silueta.niveles import parametros_de_nivel
from futbol_silueta.plantilla import aplicar_formacion
from futbol_silueta.repeticion import aplicar_instante, capturar_instante
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

    def _gol_con_jugada_previa(self) -> None:
        """Da posesión, graba unos fotogramas y marca un gol.

        Deja el partido en ``Estado.GOL`` con una repetición congelada.
        """
        juego = self.juego
        control = juego.jugador_controlado
        assert control is not None

        juego.dar_posesion(control)

        for _ in range(30):
            juego.actualizar(1.0 / 60.0)

        control.pos.update(CAMPO_RECT.right - 20, PORTERIA_CENTRO)
        control.actualizar_rect()
        control.direccion.update(1, 0)
        juego.actualizar_balon(1.0 / 60.0)

    def test_el_gol_deja_una_repeticion_grabada(self) -> None:
        self._gol_con_jugada_previa()

        juego = self.juego
        self.assertIs(juego.estado, Estado.GOL)
        self.assertTrue(juego.repeticion)

        # El último fotograma muestra el balón llegando a la red: el
        # gol se detecta con el balón a menos de su radio de la línea.
        repeticion = juego.repeticion
        assert repeticion is not None
        ultimo = repeticion[-1]
        self.assertGreater(ultimo.balon_x, repeticion[0].balon_x)
        self.assertGreaterEqual(
            ultimo.balon_x,
            CAMPO_RECT.right - RADIO_BALON,
        )

    def test_capturar_y_aplicar_un_instante(self) -> None:
        juego = self.juego
        instante = capturar_instante(juego)

        jugador = juego.jugadores[0]
        jugador.pos.update(123.0, 45.0)
        jugador.tiene_balon = True
        jugador.actualizar_rect()
        juego.balon.pos.update(500.0, 300.0)

        aplicar_instante(juego, instante)

        x, y, tiene_balon = instante.jugadores[0]
        self.assertEqual((jugador.pos.x, jugador.pos.y), (x, y))
        self.assertEqual(jugador.rect.center, (round(x), round(y)))
        self.assertFalse(jugador.tiene_balon)
        self.assertEqual(
            (juego.balon.pos.x, juego.balon.pos.y),
            (instante.balon_x, instante.balon_y),
        )

    def test_la_repeticion_arranca_tras_la_celebracion(self) -> None:
        self._gol_con_jugada_previa()

        juego = self.juego
        juego.tiempo_gol -= DURACION_GOL
        juego.actualizar(1.0 / 60.0)

        self.assertIs(juego.estado, Estado.REPETICION)

        juego.actualizar(1.0 / 60.0)
        self.assertGreater(juego._indice_repeticion, 0.0)

    def test_espacio_salta_la_repeticion(self) -> None:
        self._gol_con_jugada_previa()
        juego = self.juego
        juego.tiempo_gol -= DURACION_GOL
        juego.actualizar(1.0 / 60.0)
        self.assertIs(juego.estado, Estado.REPETICION)

        juego.procesar_tecla(pygame.K_SPACE)

        self.assertIs(juego.estado, Estado.JUGANDO)

    def test_la_repeticion_termina_en_el_saque(self) -> None:
        self._gol_con_jugada_previa()
        juego = self.juego
        juego.tiempo_gol -= DURACION_GOL
        juego.actualizar(1.0 / 60.0)
        self.assertIs(juego.estado, Estado.REPETICION)

        for _ in range(1000):
            juego.actualizar(1.0 / 60.0)

            if juego.estado is Estado.JUGANDO:
                break

        self.assertIs(juego.estado, Estado.JUGANDO)
        self.assertIsNone(juego.repeticion)

    def test_gol_sin_grabacion_reinicia_sin_repeticion(self) -> None:
        juego = self.juego
        juego.estado = Estado.GOL
        juego.repeticion = None
        juego.tiempo_gol = pygame.time.get_ticks() - DURACION_GOL

        juego.actualizar(1.0 / 60.0)

        self.assertIs(juego.estado, Estado.JUGANDO)

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

    def test_decisiones_ia_se_renuevan_tras_reiniciar(self) -> None:
        juego = self.juego
        juego.actualizar_ia(1.0 / 60.0)

        juego.reiniciar_jugada(con_silbato=False)

        # La caché no debe conservar jugadores de la jugada anterior.
        self.assertEqual(juego._perseguidores, set())
        self.assertEqual(juego._marcajes, {})
        self.assertEqual(len(juego.porteros), 2)

        # Y en el siguiente frame la IA vuelve a decidir quién presiona.
        visitante = next(
            jugador
            for jugador in juego.jugadores
            if jugador.equipo is Equipo.VISITANTE
            and jugador.rol is not Rol.PORTERO
        )
        juego.dar_posesion(visitante)
        juego.actualizar_ia(1.0 / 60.0)

        self.assertTrue(juego._perseguidores)

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

    def test_personalizar_el_estadio_cambia_la_seleccion(self) -> None:
        estadio = Estadio(
            Cesped.ARTIFICIAL,
            Momento.NOCHE,
            Diseno.RAYAS,
            False,
        )
        self.juego.personalizar_estadio(estadio)

        self.assertEqual(self.juego.estadio, estadio)

    def test_el_fondo_refleja_el_estadio_elegido(self) -> None:
        juego = self.juego
        vista = self.vista

        # Día claro por defecto, con gradas y público alrededor.
        vista.dibujar(juego)
        punto_cesped = (CAMPO_RECT.centerx - 200, CAMPO_RECT.centery + 150)
        dia = vista.pantalla.get_at(punto_cesped)

        juego.personalizar_estadio(
            Estadio(Cesped.CLARO, Momento.NOCHE, Diseno.CLASICO, True)
        )
        vista.dibujar(juego)
        noche = vista.pantalla.get_at(punto_cesped)
        self.assertLess(noche.r, dia.r)

        # Sin gradas, el entorno pasa a ser un cordón de césped.
        juego.personalizar_estadio(
            Estadio(Cesped.CLARO, Momento.DIA, Diseno.CLASICO, False)
        )
        vista.dibujar(juego)
        esquina = vista.pantalla.get_at((8, 8))
        self.assertGreater(esquina.g, 60)

        # Y las rayas del diseño alternan dos tonos de césped.
        juego.personalizar_estadio(
            Estadio(Cesped.CLARO, Momento.DIA, Diseno.RAYAS, False)
        )
        vista.dibujar(juego)
        banda_a = vista.pantalla.get_at((CAMPO_RECT.left + 20, punto_cesped[1]))
        banda_b = vista.pantalla.get_at((CAMPO_RECT.left + 110, punto_cesped[1]))
        self.assertNotEqual(banda_a.r, banda_b.r)

    def test_cambiar_jugador_pasa_al_local_mas_cercano_al_balon(self) -> None:
        juego = self.juego
        control = juego.jugador_controlado
        assert control is not None

        # El control empieza lejos del balón (que queda en el centro).
        control.pos.update(CAMPO_RECT.left + 50, CAMPO_RECT.centery)
        control.actualizar_rect()

        esperado = min(
            (
                jugador
                for jugador in juego.jugadores
                if jugador.equipo is Equipo.LOCAL
                and jugador.rol is not Rol.PORTERO
                and jugador is not control
            ),
            key=lambda jugador: jugador.pos.distance_squared_to(
                juego.balon.pos
            ),
        )

        juego.procesar_tecla(pygame.K_q)

        self.assertIs(juego.jugador_controlado, esperado)

    def test_cambiar_jugador_cicla_entre_los_locales(self) -> None:
        juego = self.juego

        for _ in range(3):
            anterior = juego.jugador_controlado
            juego.procesar_tecla(pygame.K_q)
            actual = juego.jugador_controlado

            self.assertIsNot(actual, anterior)
            self.assertIs(actual.equipo, Equipo.LOCAL)
            self.assertIsNot(actual.rol, Rol.PORTERO)

    def test_cambiar_jugador_no_se_aplica_con_posesion_local(self) -> None:
        juego = self.juego
        control = juego.jugador_controlado
        juego.dar_posesion(control)

        juego.procesar_tecla(pygame.K_q)

        self.assertIs(juego.jugador_controlado, control)

    def test_cambiar_jugador_saca_el_control_del_portero(self) -> None:
        juego = self.juego
        portero = next(
            jugador
            for jugador in juego.jugadores
            if jugador.equipo is Equipo.LOCAL
            and jugador.rol is Rol.PORTERO
        )
        juego.jugador_controlado = portero

        juego.procesar_tecla(pygame.K_q)

        self.assertIsNot(juego.jugador_controlado, portero)
        self.assertIsNot(juego.jugador_controlado.rol, Rol.PORTERO)

    def test_avanza_al_siguiente_nivel_tras_el_final(self) -> None:
        self.juego.estado = Estado.FINAL
        self.juego._al_pulsar_espacio()

        self.assertEqual(self.juego.nivel, 2)
        self.assertIs(self.juego.estado, Estado.JUGANDO)
        self.assertEqual(
            (self.juego.goles_local, self.juego.goles_visitante),
            (0, 0),
        )

    def test_nueva_partida_reinicia_el_nivel(self) -> None:
        self.juego.nivel = 3
        self.juego.nueva_partida()

        self.assertEqual(self.juego.nivel, 1)
        self.assertEqual(self.juego.escudo.nivel, 1)

    def test_el_nivel_siguiente_sustituye_el_escudo_y_los_ajustes(
        self,
    ) -> None:
        self.juego.nivel = 2
        self.juego._reiniciar_nivel(2)

        self.assertEqual(self.juego.nivel, 2)
        self.assertEqual(self.juego.escudo.nivel, 2)
        self.assertEqual(
            self.juego.nivel_actual.parametros,
            parametros_de_nivel(2),
        )

    def test_personalizar_el_escudo_cambia_colores(self) -> None:
        self.juego.personalizar_escudo((10, 20, 30), (40, 50, 60))

        self.assertEqual(self.juego.escudo.color, (10, 20, 30))
        self.assertEqual(self.juego.escudo.color_borde, (40, 50, 60))

    def test_cambiar_formacion_recoloca_a_los_jugadores(self) -> None:
        # Como hace el menú de tácticas: primero recoloca las fichas.
        plantillas = {
            equipo: aplicar_formacion(self.juego.plantillas[equipo], "3-5-2")
            for equipo in Equipo
        }
        self.juego.personalizar_plantillas(plantillas)
        self.juego.cambiar_formacion("3-5-2")

        self.assertEqual(self.juego.formacion_nombre, "3-5-2")
        self.assertEqual(len(self.juego.porteros), 2)

        for equipo in (Equipo.LOCAL, Equipo.VISITANTE):
            roles = [
                jugador.rol
                for jugador in self.juego.jugadores
                if jugador.equipo is equipo
            ]

            self.assertEqual(len(roles), 11)
            self.assertEqual(roles.count(Rol.PORTERO), 1)
            self.assertEqual(roles.count(Rol.DEFENSA), 3)
            self.assertEqual(roles.count(Rol.MEDIO), 5)
            self.assertEqual(roles.count(Rol.DELANTERO), 2)

    def test_la_formacion_desconocida_vuelve_a_la_442(self) -> None:
        self.juego.cambiar_formacion("1-9-1", recolocar=False)

        self.assertEqual(self.juego.formacion_nombre, "4-4-2")


if __name__ == "__main__":
    unittest.main()
