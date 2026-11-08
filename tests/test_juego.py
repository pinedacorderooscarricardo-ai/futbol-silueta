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
    DURACION_CORNER,
    DURACION_GOL,
    FORMACION_REMONTADA,
    INTERVALO_VIENTO,
    LATERAL_APOYO,
    PORTERIA_CENTRO,
    PRESORES_POR_EQUIPO,
    RADIO_BALON,
    VELOCIDAD_IA,
    Equipo,
    Estado,
    Rol,
)
from futbol_silueta.juego import Juego
from futbol_silueta.entidades import Balon
from futbol_silueta.estadios import (
    FRICCION_CLIMA,
    Cesped,
    Clima,
    Diseno,
    Estadio,
    Momento,
)
from futbol_silueta.estadisticas import registrar_resultado
from futbol_silueta.menus import Menus
from futbol_silueta.niveles import parametros_de_nivel
from futbol_silueta.plantilla import (
    aplicar_formacion,
    suplentes_por_defecto,
)
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
            Clima.LLUVIA,
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

    def test_las_estadisticas_cuentan_el_partido(self) -> None:
        juego = self.juego
        control = juego.jugador_controlado
        assert control is not None

        juego.dar_posesion(control)
        juego.actualizar(1.0 / 60.0)  # acumula posesión local
        juego._chutar(pygame.Vector2(1, 0), control)
        juego.dar_posesion(control)
        juego.pasar_al_companero_mas_cercano()
        juego.estadisticas.contar_atajada(Equipo.VISITANTE)

        estadisticas = juego.estadisticas
        self.assertGreater(estadisticas.posesion[Equipo.LOCAL], 0.0)
        self.assertEqual(estadisticas.disparos[Equipo.LOCAL], 1)
        self.assertEqual(estadisticas.pases[Equipo.LOCAL], 1)
        self.assertEqual(estadisticas.atajadas[Equipo.VISITANTE], 1)
        self.assertEqual(estadisticas.lineas()[1], "Disparos 1 - 0")

    def test_el_narrador_comenta_el_gol(self) -> None:
        self._gol_con_jugada_previa()

        comentario = self.juego.comentario_gol
        self.assertTrue(comentario)
        self.assertIn(self.juego.jugador_controlado.nombre, comentario)

    def test_r_repite_la_ultima_jugada_y_reanuda(self) -> None:
        juego = self.juego

        # Un gol deja su jugada entre las mejores guardadas.
        self._gol_con_jugada_previa()
        juego.tiempo_gol -= DURACION_GOL
        juego.actualizar(1.0 / 60.0)
        juego.procesar_tecla(pygame.K_SPACE)
        self.assertIs(juego.estado, Estado.JUGANDO)

        # R congela el estado actual, repite y lo restaura al acabar.
        juego.balon.pos.update(CAMPO_RECT.centerx + 80, CAMPO_RECT.centery)
        antes = capturar_instante(juego)

        juego.procesar_tecla(pygame.K_r)
        self.assertIs(juego.estado, Estado.REPETICION)

        for _ in range(400):
            juego.actualizar(1.0 / 60.0)

            if juego.estado is Estado.JUGANDO:
                break

        self.assertIs(juego.estado, Estado.JUGANDO)
        self.assertEqual(antes, capturar_instante(juego))

    def test_registrar_resultado_actualiza_tabla_y_trofeos(self) -> None:
        juego = self.juego
        juego.nivel = 3
        juego.goles_local = 3
        juego.goles_visitante = 0

        menus = Menus()
        nuevos = registrar_resultado(menus, juego)

        fila = menus.tabla_posiciones.fila("local")
        self.assertEqual(fila.puntos, 3)
        self.assertEqual(fila.g, 1)
        self.assertEqual(menus.tabla_posiciones.fila("3").p, 1)
        self.assertEqual(menus.historial[0].nivel, 3)

        ids = {trofeo.id for trofeo in nuevos}
        self.assertIn("primera_victoria", ids)
        self.assertIn("goleada", ids)
        self.assertIn("valla_invicta", ids)
        self.assertEqual(menus.trofeos, ids)

    def test_el_clima_cambia_la_friccion_del_balon(self) -> None:
        distancia: dict[Clima, float] = {}

        for clima in (Clima.LLUVIA, Clima.DESPEJADO, Clima.NIEVE):
            balon = Balon()
            balon.pos.update(CAMPO_RECT.center)
            balon.vel.update(400.0, 0.0)

            for _ in range(30):
                salida = balon.actualizar_libre(
                    1.0 / 60.0,
                    lambda: False,
                    FRICCION_CLIMA[clima],
                )
                self.assertIsNone(salida.gol)
                self.assertIsNone(salida.esquina)

            distancia[clima] = balon.pos.x - CAMPO_RECT.centerx

        self.assertGreater(
            distancia[Clima.LLUVIA],
            distancia[Clima.DESPEJADO],
        )
        self.assertGreater(
            distancia[Clima.DESPEJADO],
            distancia[Clima.NIEVE],
        )

    def test_el_corner_se_genera_tras_tocar_el_defensor(self) -> None:
        juego = self.juego
        defensor = next(
            jugador
            for jugador in juego.jugadores
            if jugador.equipo is Equipo.VISITANTE
            and jugador.rol is Rol.DEFENSA
        )
        juego.ultimo_tocador = defensor
        juego.balon.pos.update(CAMPO_RECT.right - 5, CAMPO_RECT.top + 40)
        juego.balon.vel.update(500.0, 0.0)

        juego.actualizar_balon(1.0 / 60.0)

        self.assertIs(juego.estado, Estado.CORNER)
        self.assertIs(juego.esquina, Equipo.LOCAL)

        juego.tiempo_corner -= DURACION_CORNER
        juego.actualizar(1.0 / 60.0)
        self.assertIs(juego.estado, Estado.JUGANDO)
        self.assertIsNotNone(juego.portador)
        assert juego.portador is not None
        self.assertIs(juego.portador.equipo, Equipo.LOCAL)
        self.assertIs(juego.jugador_controlado, juego.portador)
        self.assertEqual(
            (round(juego.balon.pos.x), round(juego.balon.pos.y)),
            (
                CAMPO_RECT.right - RADIO_BALON,
                CAMPO_RECT.top + RADIO_BALON,
            ),
        )

    def test_sin_corner_si_el_ultimo_toque_fue_del_atacante(self) -> None:
        juego = self.juego
        atacante = next(
            jugador
            for jugador in juego.jugadores
            if jugador.equipo is Equipo.LOCAL
            and jugador.rol is Rol.DELANTERO
        )
        juego.ultimo_tocador = atacante
        juego.balon.pos.update(CAMPO_RECT.right - 5, CAMPO_RECT.top + 40)
        juego.balon.vel.update(500.0, 0.0)

        juego.actualizar_balon(1.0 / 60.0)

        self.assertIs(juego.estado, Estado.JUGANDO)
        self.assertIsNone(juego.esquina)
        self.assertLess(juego.balon.pos.x, CAMPO_RECT.right)

    def test_espacio_cobra_el_corner_al_instante(self) -> None:
        juego = self.juego
        defensor = next(
            jugador
            for jugador in juego.jugadores
            if jugador.equipo is Equipo.LOCAL
            and jugador.rol is Rol.DEFENSA
        )
        juego.ultimo_tocador = defensor
        juego.balon.pos.update(CAMPO_RECT.left + 5, CAMPO_RECT.bottom - 40)
        juego.balon.vel.update(-500.0, 0.0)

        juego.actualizar_balon(1.0 / 60.0)
        self.assertIs(juego.estado, Estado.CORNER)
        self.assertIs(juego.esquina, Equipo.VISITANTE)

        juego.procesar_tecla(pygame.K_SPACE)
        self.assertIs(juego.estado, Estado.JUGANDO)
        self.assertIsNotNone(juego.portador)
        assert juego.portador is not None
        self.assertIs(juego.portador.equipo, Equipo.VISITANTE)
        self.assertEqual(
            (round(juego.balon.pos.x), round(juego.balon.pos.y)),
            (
                CAMPO_RECT.left + RADIO_BALON,
                CAMPO_RECT.bottom - RADIO_BALON,
            ),
        )

    def test_la_ia_aprende_el_lado_de_ataque(self) -> None:
        juego = self.juego
        control = juego.jugador_controlado
        assert control is not None
        juego.dar_posesion(control)

        # El jugador ataca casi siempre por la mitad de abajo.
        juego.balon.pos.update(CAMPO_RECT.centerx, CAMPO_RECT.bottom - 60)
        # Una ventana completa de observación (5 s) más margen.
        for _ in range(320):
            juego._observar_estilo(1.0 / 60.0)

        self.assertGreater(juego._sesgo_lateral, 0.0)

        # El defensa visitante marca desplazado hacia ese lado.
        defensa = next(
            jugador
            for jugador in juego.jugadores
            if jugador.equipo is Equipo.VISITANTE
            and jugador.rol is Rol.DEFENSA
        )
        objetivo = juego._objetivo_ia(
            defensa,
            Equipo.LOCAL,
            False,
            control,
        )
        self.assertAlmostEqual(
            objetivo.y,
            control.pos.y + juego._sesgo_lateral,
            delta=1.0,
        )

    def test_la_ia_presiona_mas_si_disparas_seguido(self) -> None:
        juego = self.juego
        control = juego.jugador_controlado
        assert control is not None
        juego.dar_posesion(control)

        # Dos disparos del jugador dentro de la misma ventana.
        juego.estadisticas.contar_disparo(Equipo.LOCAL)
        juego.estadisticas.contar_disparo(Equipo.LOCAL)
        juego._ventana_estilo = 0.001
        juego._observar_estilo(1.0 / 60.0)

        self.assertEqual(juego._presores_extra, 1)

        perseguidores = juego._elegir_perseguidores(Equipo.LOCAL)
        self.assertEqual(len(perseguidores), PRESORES_POR_EQUIPO + 1)

    def test_el_contraataque_sale_al_robar_con_espacios(self) -> None:
        juego = self.juego
        ladron = next(
            jugador
            for jugador in juego.jugadores
            if jugador.equipo is Equipo.VISITANTE
            and jugador.rol is Rol.MEDIO
        )
        control = juego.jugador_controlado
        assert control is not None

        # El robo cerca del arco local con toda la defensa lanzada.
        juego.balon.pos.update(CAMPO_RECT.left + 60, CAMPO_RECT.centery)
        ladron.pos.update(CAMPO_RECT.left + 90, CAMPO_RECT.centery)
        ladron.actualizar_rect()

        for jugador in juego.jugadores:
            if (
                jugador.equipo is Equipo.LOCAL
                and jugador.rol is not Rol.PORTERO
                and jugador is not control
            ):
                jugador.pos.update(CAMPO_RECT.right - 80, CAMPO_RECT.centery)
                jugador.actualizar_rect()

        juego.dar_posesion(control)
        juego.dar_posesion(ladron)

        self.assertTrue(juego._en_contraataque)

        # Expira el tiempo (o pierde el balón) y se apaga.
        juego._fin_contraataque = pygame.time.get_ticks() - 1
        juego.actualizar_ia(1.0 / 60.0)
        self.assertFalse(juego._en_contraataque)

    def test_sin_contraataque_si_la_defensa_esta_detras(self) -> None:
        juego = self.juego
        ladron = next(
            jugador
            for jugador in juego.jugadores
            if jugador.equipo is Equipo.VISITANTE
            and jugador.rol is Rol.MEDIO
        )
        control = juego.jugador_controlado
        assert control is not None

        # Robo en el centro: los defensores locales siguen detrás.
        juego.dar_posesion(control)
        juego.dar_posesion(ladron)

        self.assertFalse(juego._en_contraataque)

    def test_la_ia_cambia_de_formacion_al_perder(self) -> None:
        juego = self.juego
        juego.mitad = 2
        juego.goles_local = 1
        juego.goles_visitante = 0

        juego._revisar_tactica_visitante()

        self.assertEqual(juego._formacion_visitante, FORMACION_REMONTADA)
        roles = [
            jugador.rol
            for jugador in juego.jugadores
            if jugador.equipo is Equipo.VISITANTE
        ]
        self.assertEqual(roles.count(Rol.PORTERO), 1)
        self.assertEqual(roles.count(Rol.DEFENSA), 4)
        self.assertEqual(roles.count(Rol.MEDIO), 3)
        self.assertEqual(roles.count(Rol.DELANTERO), 3)

        # Al reiniciar la jugada, la rival vuelve a su formación base.
        juego.reiniciar_jugada(con_silbato=False)
        self.assertEqual(juego._formacion_visitante, juego.formacion_nombre)

    def test_el_cansancio_frena_y_rota_al_agotado(self) -> None:
        juego = self.juego
        agotado = next(
            jugador
            for jugador in juego.jugadores
            if jugador.equipo is Equipo.VISITANTE
            and jugador.rol is Rol.DELANTERO
        )
        fresco = next(
            jugador
            for jugador in juego.jugadores
            if jugador.equipo is Equipo.VISITANTE
            and jugador.rol is agotado.rol
            and jugador is not agotado
        )
        agotado.cansancio = 0.95
        base_agotado = pygame.Vector2(agotado.posicion_base)
        base_fresco = pygame.Vector2(fresco.posicion_base)

        juego._revisar_rotaciones()

        # La rotación intercambia las zonas del agotado y del fresco.
        self.assertEqual(agotado.posicion_base, base_fresco)
        self.assertEqual(fresco.posicion_base, base_agotado)

        # Y el cansancio frena: el portador agotado avanza menos.
        def avance_con(cansancio: float) -> float:
            juego.dar_posesion(agotado)
            agotado.pos.update(CAMPO_RECT.centerx, CAMPO_RECT.centery)
            agotado.cansancio = cansancio
            x_inicial = agotado.pos.x

            for _ in range(10):
                juego.actualizar_ia(1.0 / 60.0)

            return agotado.pos.x - x_inicial

        # El portador avanza hacia la izquierda (avance negativo).
        self.assertLess(abs(avance_con(0.95)), abs(avance_con(0.0)))

    def test_el_marcaje_individual_es_persistente(self) -> None:
        juego = self.juego
        control = juego.jugador_controlado
        assert control is not None

        # El balón lejos de los defensas rivales: ninguno persigue.
        control.pos.update(CAMPO_RECT.left + 100, CAMPO_RECT.centery)
        control.actualizar_rect()
        juego.dar_posesion(control)
        juego._actualizar_decisiones()

        parejas = {
            defensa: marcado
            for defensa, marcado in juego._marcajes_fijos.items()
            if defensa.equipo is Equipo.VISITANTE
        }
        self.assertTrue(parejas)

        # Mover al marcado no rompe la pareja asignada.
        marcado = next(iter(parejas.values()))
        marcado.pos.update(CAMPO_RECT.centerx, CAMPO_RECT.centery)
        marcado.actualizar_rect()
        juego._actualizar_decisiones()

        self.assertEqual(juego._marcajes_fijos, parejas)

    def test_los_companeros_buscan_espacios_para_recibir(self) -> None:
        juego = self.juego
        control = juego.jugador_controlado
        assert control is not None
        juego.dar_posesion(control)
        juego.balon.pos.update(CAMPO_RECT.centerx, CAMPO_RECT.centery)
        control.pos.update(CAMPO_RECT.centerx, CAMPO_RECT.centery)

        juego._actualizar_decisiones()

        self.assertEqual(len(juego._apoyos), 2)
        self.assertNotIn(control, juego._apoyos)

        apoyo = next(iter(juego._apoyos))
        objetivo = juego._objetivo_ia(apoyo, Equipo.LOCAL, False, None)

        # Desmarque adelantado hacia el arco rival y abierto a banda.
        self.assertGreater(objetivo.x, control.pos.x)
        self.assertAlmostEqual(
            abs(objetivo.y - control.pos.y),
            LATERAL_APOYO,
            delta=1.0,
        )

    def test_el_viento_empuja_el_balon(self) -> None:
        def avance_con(viento: pygame.Vector2) -> float:
            balon = Balon()
            balon.pos.update(CAMPO_RECT.center)
            balon.vel.update(200.0, 0.0)

            for _ in range(40):
                salida = balon.actualizar_libre(
                    1.0 / 60.0,
                    lambda: False,
                    viento=viento,
                )
                self.assertIsNone(salida.gol)
                self.assertIsNone(salida.esquina)

            return balon.pos.x - CAMPO_RECT.centerx

        # Con viento a favor el balón llega más lejos.
        self.assertGreater(
            avance_con(pygame.Vector2(35.0, 0.0)),
            avance_con(pygame.Vector2(0.0, 0.0)),
        )

    def test_el_viento_cambia_con_el_clima(self) -> None:
        juego = self.juego
        juego.estadio = Estadio(
            Cesped.CLARO,
            Momento.DIA,
            Diseno.CLASICO,
            True,
            Clima.LLUVIA,
        )
        # El viento se renueva cada INTERVALO_VIENTO: se fuerza la
        # ventana vencida para comprobar el cambio al instante.
        juego._tiempo_viento = pygame.time.get_ticks() - INTERVALO_VIENTO

        juego._actualizar_viento()

        fuerza = juego.viento.length()
        self.assertGreater(fuerza, 8.0)
        self.assertLessEqual(fuerza, 34.0)

    def test_la_camara_sigue_al_balon(self) -> None:
        juego = self.juego
        vista = self.vista

        # Estado de cámara limpio: la vista se comparte entre pruebas.
        vista._zoom = 1.0
        vista._centro_camara.update(ANCHO / 2, ALTO / 2)

        # Balón quieto en el centro: plano completo, sin zoom.
        vista.dibujar(juego)
        self.assertEqual(vista._camara_rect().width, ANCHO)

        # Balón rápido junto al arco: zoom y seguimiento.
        juego.balon.pos.update(CAMPO_RECT.right - 30, CAMPO_RECT.centery)
        juego.balon.vel.update(600.0, 0.0)
        vista.dibujar(juego)
        vista.dibujar(juego)
        camara = vista._camara_rect()

        self.assertLess(camara.width, ANCHO)
        self.assertGreater(camara.centerx, ANCHO // 2)

    def test_las_animaciones_del_jugador(self) -> None:
        juego = self.juego
        jugador = juego.jugadores[0]
        ladron = next(
            j for j in juego.jugadores if j.equipo is Equipo.VISITANTE
        )

        # Correr avanza la zancada.
        fase_inicial = jugador.fase
        jugador.mover(10.0, 0.0)
        self.assertGreater(jugador.fase, fase_inicial)

        # El salto se agota con el tiempo.
        jugador.saltar(0.8)
        jugador.avanzar_animacion(0.3)
        self.assertLess(jugador.salto_restante, 0.8)
        self.assertGreater(jugador.salto_restante, 0.0)

        # Un robo tumba al que perdía el balón.
        juego.dar_posesion(jugador)
        juego.dar_posesion(ladron)
        self.assertGreater(jugador.caida_restante, 0.0)

    def test_los_goles_se_celebran_y_el_portero_cae(self) -> None:
        juego = self.juego
        self._gol_con_jugada_previa()

        self.assertEqual(juego.emocion_grada, 1.0)

        goleador = juego.jugador_controlado
        portero = next(
            j
            for j in juego.jugadores
            if j.equipo is Equipo.VISITANTE and j.rol is Rol.PORTERO
        )
        self.assertGreater(goleador.salto_restante, 0.0)
        self.assertGreater(portero.caida_restante, 0.0)

        # La emoción de la grada se apaga poco a poco.
        juego.avanzar_animaciones(1.0)
        self.assertLess(juego.emocion_grada, 1.0)

    def test_el_marcador_lleva_los_colores_de_los_equipos(self) -> None:
        juego = self.juego
        superficie = self.vista._crear_superficie_marcador(juego)

        color_local = juego.uniformes[Equipo.LOCAL].camiseta
        color_visitante = juego.uniformes[Equipo.VISITANTE].camiseta
        self.assertEqual(
            superficie.get_at((2, superficie.get_height() // 2))[:3],
            color_local,
        )
        self.assertEqual(
            superficie.get_at(
                (superficie.get_width() - 3, superficie.get_height() // 2)
            )[:3],
            color_visitante,
        )

    def test_avanza_al_siguiente_nivel_tras_el_final(self) -> None:
        self.juego.estado = Estado.FINAL
        self.juego._al_pulsar_espacio()

        self.assertEqual(self.juego.nivel, 2)
        self.assertIs(self.juego.estado, Estado.JUGANDO)
        self.assertEqual(
            (self.juego.goles_local, self.juego.goles_visitante),
            (0, 0),
        )

    def test_nueva_partida_conserva_el_nivel_de_la_campana(self) -> None:
        self.juego.nivel = 3
        self.juego.nueva_partida()

        self.assertEqual(self.juego.nivel, 3)
        self.assertEqual(self.juego.escudo.nivel, 3)

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

    def test_sustituir_reemplaza_al_jugador_en_campo(self) -> None:
        juego = self.juego
        control = juego.jugador_controlado
        self.assertIsNotNone(control)
        assert control is not None

        # El controlado conduce el balón: el cambio debe transferir
        # tanto el control como el balón al que entra.
        juego.dar_posesion(control)

        hueco = 9  # Delantero local (dorsal 10) en la formación 4-4-2.
        saliente = juego.plantillas[Equipo.LOCAL][hueco]
        suplente = suplentes_por_defecto(Equipo.LOCAL)[0]
        ficha_entrante = suplente._replace(
            rol=saliente.rol,
            x=saliente.x,
            y=saliente.y,
        )

        aplicado = juego.sustituir(
            Equipo.LOCAL,
            hueco,
            ficha_entrante,
        )

        self.assertTrue(aplicado)
        self.assertEqual(len(juego.jugadores), 22)

        entrante = next(
            jugador
            for jugador in juego.jugadores
            if jugador.equipo is Equipo.LOCAL
            and jugador.numero == suplente.dorsal
        )
        salidos = [
            jugador
            for jugador in juego.jugadores
            if jugador.equipo is Equipo.LOCAL
            and jugador.numero == saliente.dorsal
        ]

        self.assertEqual(entrante.nombre, suplente.nombre)
        self.assertFalse(salidos)
        self.assertIs(juego.jugador_controlado, entrante)
        self.assertIs(juego.portador, entrante)
        self.assertTrue(entrante.tiene_balon)
        self.assertFalse(control.tiene_balon)

        # El que entra ocupa el hueco del que sale (posición base).
        campo_x = CAMPO_RECT.left + saliente.x * CAMPO_RECT.width
        self.assertAlmostEqual(entrante.pos.x, campo_x, delta=1.0)

    def test_sustituir_con_datos_invalidos_no_hace_nada(self) -> None:
        suplente = suplentes_por_defecto(Equipo.LOCAL)[0]

        self.assertFalse(
            self.juego.sustituir(Equipo.LOCAL, 99, suplente),
        )
        self.assertFalse(
            self.juego.sustituir(Equipo.LOCAL, -1, suplente),
        )


if __name__ == "__main__":
    unittest.main()
