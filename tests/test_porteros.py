"""Pruebas headless de los porteros inteligentes."""

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
    CAMPO_RECT,
    PORTERIA_CENTRO,
    PORTERIA_SUPERIOR,
    Equipo,
)
from futbol_silueta.juego import Juego
from futbol_silueta.niveles import NIVEL_MAXIMO
from futbol_silueta.porteros import (
    PORTERO_LOCAL,
    PorteroCalidad,
    PorteroInteligente,
    calidad_rival,
)


def _portero_de(juego: Juego, equipo: Equipo):
    """El portero IA de un equipo del partido de prueba."""
    for portero in juego.porteros:
        if portero.equipo is equipo:
            return portero

    raise AssertionError("falta el portero del equipo")


class PorterosTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        pygame.display.set_mode((ANCHO, 650))

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def setUp(self) -> None:
        self.juego = Juego(None)
        self.juego.portador = None

    def test_la_calidad_del_rival_mejora_con_el_nivel(self) -> None:
        bajo = calidad_rival(1)
        alto = calidad_rival(NIVEL_MAXIMO)

        self.assertGreater(bajo.error, alto.error)
        self.assertGreater(bajo.reaccion_ms, alto.reaccion_ms)
        self.assertLess(bajo.factor_lance, alto.factor_lance)
        self.assertLess(bajo.anticipacion, alto.anticipacion)

    def test_el_portero_local_tiene_calidad_fija(self) -> None:
        for nivel in (1, NIVEL_MAXIMO):
            juego = Juego(None)
            juego.nivel = nivel
            juego.reiniciar_jugada(con_silbato=False)

            self.assertIs(
                juego.porteros_ia[_portero_de(juego, Equipo.LOCAL)].calidad,
                PORTERO_LOCAL,
            )

    def test_anticipa_la_trayectoria_del_disparo(self) -> None:
        juego = self.juego
        portero = _portero_de(juego, Equipo.LOCAL)
        portero_ia = juego.porteros_ia[portero]
        portero_ia.calidad = PorteroCalidad(
            error=0.0,
            reaccion_ms=0.0,
            factor_lance=2.0,
            anticipacion=1.0,
        )

        # Disparo lejano: tarda más de TIEMPO_LLEGADA_LANCE, así que el
        # portero cubre el ángulo sin lanzarse.
        juego.balon.pos.update(700.0, PORTERIA_CENTRO)
        juego.balon.vel.update(-600.0, -300.0)

        for _ in range(20):
            portero_ia.actualizar(juego, 1 / 60)

        self.assertEqual(portero_ia._lance_restante, 0.0)
        # La predicción cruza por la esquina alta (y ≈ 261): se despega
        # del centro en lugar de seguir el balón a ciegas.
        self.assertLess(portero.pos.y, PORTERIA_CENTRO - 20.0)

    def test_se_lanza_con_un_tiro_a_la_esquina(self) -> None:
        juego = self.juego
        portero = _portero_de(juego, Equipo.LOCAL)
        portero_ia = juego.porteros_ia[portero]
        portero_ia.calidad = PorteroCalidad(
            error=0.0,
            reaccion_ms=0.0,
            factor_lance=2.0,
            anticipacion=1.0,
        )

        # Disparo raso y cerca a la esquina superior: hay que volar.
        juego.balon.pos.update(400.0, PORTERIA_SUPERIOR + 6.0)
        juego.balon.vel.update(-800.0, 0.0)
        portero.pos.y = PORTERIA_CENTRO
        portero_ia.actualizar(juego, 1 / 60)

        self.assertGreater(portero_ia._lance_restante, 0.0)
        self.assertGreater(portero.lance_restante, 0.0)

    def test_el_error_decide_si_atrapa_el_lance(self) -> None:
        juego = self.juego
        portero = _portero_de(juego, Equipo.LOCAL)
        portero_ia = juego.porteros_ia[portero]

        portero_ia._lance_restante = 0.0
        self.assertTrue(portero_ia.puede_atrapar())

        portero_ia._lance_restante = 100.0
        portero_ia.falla_tiro = False
        self.assertTrue(portero_ia.puede_atrapar())

        portero_ia.falla_tiro = True
        self.assertFalse(portero_ia.puede_atrapar())

    def test_el_lance_amplia_el_alcance(self) -> None:
        portero_ia = PorteroInteligente(
            _portero_de(self.juego, Equipo.LOCAL),
            PORTERO_LOCAL,
        )

        self.assertEqual(portero_ia.radio_atajada(34.0), 34.0)

        portero_ia._lance_restante = 100.0
        self.assertGreater(portero_ia.radio_atajada(34.0), 34.0)

    def test_la_atajada_respeta_el_error_del_portero(self) -> None:
        juego = self.juego
        portero = _portero_de(juego, Equipo.VISITANTE)
        portero_ia = juego.porteros_ia[portero]

        # Balón justo sobre el portero visitante y disparo a su arco.
        juego.balon.pos.update(portero.pos.x, portero.pos.y)
        juego.balon.vel.update(720.0, 0.0)

        portero_ia._lance_restante = 100.0
        portero_ia.falla_tiro = True
        self.assertFalse(juego._intentar_atajada())

        portero_ia.falla_tiro = False
        self.assertTrue(juego._intentar_atajada())
        self.assertIs(juego.portador, portero)

    def test_el_portero_no_se_lanza_si_el_tiro_va_fuera(self) -> None:
        juego = self.juego
        portero = _portero_de(juego, Equipo.LOCAL)
        portero_ia = juego.porteros_ia[portero]
        portero_ia.calidad = PorteroCalidad(
            error=0.0,
            reaccion_ms=0.0,
            factor_lance=2.0,
            anticipacion=1.0,
        )

        # Disparo cerca y fuera de la portería: la predicción se recorta
        # al arco, pero un tiro ya cruzado no debe lanzarlo.
        juego.balon.pos.update(CAMPO_RECT.left - 30.0, PORTERIA_CENTRO)
        juego.balon.vel.update(-800.0, 0.0)
        portero_ia.actualizar(juego, 1 / 60)

        self.assertEqual(portero_ia._lance_restante, 0.0)


if __name__ == "__main__":
    unittest.main()
