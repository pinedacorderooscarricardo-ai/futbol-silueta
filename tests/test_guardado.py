"""Pruebas headless de la base de datos SQLite del juego."""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame

from futbol_silueta.configuracion import ALTO, ANCHO, Equipo, Rol
from futbol_silueta.escudos import ESCUDO_PRESETS, FORMAS_ESCUDO
from futbol_silueta.estadios import Cesped, Clima, Momento
from futbol_silueta.estadisticas import registrar_resultado
from futbol_silueta.guardado import Guardado
from futbol_silueta.juego import Juego
from futbol_silueta.menus import Accion, Boton, Menus, Pantalla
from futbol_silueta.modos import ModoJuego, Copa, Campeones, Liga, Supervivencia
from futbol_silueta.plantilla import PRESETS_VELOCIDAD
from futbol_silueta.uniformes import UNIFORME_PRESETS, Uniforme


class GuardadoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        pygame.display.set_mode((ANCHO, ALTO))

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def setUp(self) -> None:
        directorio = tempfile.TemporaryDirectory()
        self.addCleanup(directorio.cleanup)
        self.ruta = Path(directorio.name) / "prueba.sqlite"

    def abrir(self) -> Guardado:
        """Abre la base de la prueba y registra su cierre."""
        guardado = Guardado(self.ruta)
        self.addCleanup(guardado.cerrar)
        return guardado

    def test_guardar_y_cargar_la_personalizacion(self) -> None:
        menus = Menus()
        menus._ejecutar(Accion.SONIDO)
        menus._ejecutar(
            Accion.ESCUDO,
            Boton(pygame.Rect(0, 0, 1, 1), "", Accion.ESCUDO, valor=2),
        )
        menus._ejecutar(
            Accion.FORMA_ESCUDO,
            Boton(
                pygame.Rect(0, 0, 1, 1),
                "",
                Accion.FORMA_ESCUDO,
                valor=2,
            ),
        )
        menus._ejecutar(
            Accion.PRENDA,
            Boton(pygame.Rect(0, 0, 1, 1), "", Accion.PRENDA, valor="medias"),
        )
        menus._ejecutar(Accion.NUMEROS)
        menus._ejecutar(Accion.CICLAR_JUGADOR)
        menus._ejecutar(Accion.CICLAR_DORSAL)
        menus._ejecutar(Accion.CICLAR_VELOCIDAD)
        menus.formacion_nombre = "4-3-3"

        self.abrir().guardar_desde(menus)

        otros = Menus()
        self.abrir().cargar_en(otros)

        self.assertFalse(otros.sonido_activado)
        self.assertEqual(otros.escudo_color, ESCUDO_PRESETS[2][1])
        self.assertEqual(otros.escudo_forma, FORMAS_ESCUDO[2])
        self.assertEqual(
            otros.uniformes_seleccionados[Equipo.LOCAL].medias,
            UNIFORME_PRESETS[3][1],
        )
        self.assertFalse(otros.numeros_activados)
        self.assertEqual(otros.formacion_nombre, "4-3-3")
        ficha = otros.plantillas_seleccionadas[Equipo.LOCAL][1]
        self.assertEqual(ficha.dorsal, 3)
        self.assertEqual(ficha.factor_velocidad, PRESETS_VELOCIDAD[2][1])

    def test_ciclar_velocidad_guarda_el_factor_correcto(self) -> None:
        menus = Menus()
        menus._ejecutar(Accion.CICLAR_VELOCIDAD)

        self.abrir().guardar_desde(menus)

        otros = Menus()
        self.abrir().cargar_en(otros)
        self.assertEqual(
            otros.plantillas_seleccionadas[Equipo.LOCAL][0].factor_velocidad,
            PRESETS_VELOCIDAD[2][1],
        )

    def test_el_estadio_queda_guardado_y_cargado(self) -> None:
        menus = Menus()
        menus._ejecutar(Accion.CESPED)  # Claro -> oscuro
        menus._ejecutar(Accion.MOMENTO)  # Día -> noche
        menus._ejecutar(Accion.GRADAS)  # Con -> sin aficionados
        self.abrir().guardar_desde(menus)

        otros = Menus()
        self.abrir().cargar_en(otros)

        estadio = otros.estadio_seleccionado
        self.assertIs(estadio.cesped, Cesped.OSCURO)
        self.assertIs(estadio.momento, Momento.NOCHE)
        self.assertFalse(estadio.gradas)
        self.assertEqual(
            otros.botones[Pantalla.ESTADIO][0].etiqueta,
            "Césped: OSCURO",
        )

    def test_la_campana_y_el_palmares_quedan_guardados(self) -> None:
        menus = Menus()
        menus._ejecutar(Accion.CLIMA)  # Despejado -> lluvia

        juego = Juego(None)
        juego.nivel = 4
        juego.goles_local = 2
        juego.goles_visitante = 1
        registrar_resultado(menus, juego)

        self.abrir().guardar_desde(menus, juego.nivel)

        otros = Menus()
        self.abrir().cargar_en(otros)
        self.assertIs(otros.estadio_seleccionado.clima, Clima.LLUVIA)
        self.assertEqual(otros.tabla_posiciones.fila("local").puntos, 3)
        self.assertEqual(otros.tabla_posiciones.fila("4").p, 1)
        self.assertEqual(otros.historial[0].nivel, 4)
        self.assertIn("primera_victoria", otros.trofeos)

        # Y el nivel de campaña se recupera aparte para el juego.
        self.assertEqual(self.abrir().nivel_guardado(), 4)

    def test_base_de_version_anterior_se_migra(self) -> None:
        # Base creada antes de los estadios: sin sus columnas.
        conexion = sqlite3.connect(self.ruta)
        conexion.execute(
            """
            CREATE TABLE ajustes (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                sonido_activado INTEGER NOT NULL DEFAULT 1,
                escudo_color TEXT NOT NULL,
                escudo_color_borde TEXT NOT NULL,
                escudo_forma TEXT NOT NULL,
                mostrar_numeros INTEGER NOT NULL DEFAULT 1,
                formacion TEXT NOT NULL,
                local_camiseta TEXT NOT NULL,
                local_pantalon TEXT NOT NULL,
                local_medias TEXT NOT NULL,
                visitante_camiseta TEXT NOT NULL,
                visitante_pantalon TEXT NOT NULL,
                visitante_medias TEXT NOT NULL
            )
            """
        )
        conexion.execute(
            """
            INSERT INTO ajustes (
                id, escudo_color, escudo_color_borde, escudo_forma,
                formacion, local_camiseta, local_pantalon, local_medias,
                visitante_camiseta, visitante_pantalon, visitante_medias
            ) VALUES (1, '10,20,30', '40,50,60', ?, '4-4-2',
                      '200,40,40', '200,40,40', '200,40,40',
                      '40,80,200', '40,80,200', '40,80,200')
            """,
            (FORMAS_ESCUDO[0].value,),
        )
        conexion.commit()
        conexion.close()

        guardado = self.abrir()
        menus = Menus()
        guardado.cargar_en(menus)

        # Los ajustes viejos se cargan y el estadio toma el defecto.
        self.assertEqual(menus.escudo_color, (10, 20, 30))
        self.assertIs(menus.estadio_seleccionado.cesped, Cesped.CLARO)

        # Y el guardado sigue funcionando con la base migrada.
        menus._ejecutar(Accion.CESPED)
        guardado.guardar_desde(menus)
        otros = Menus()
        self.abrir().cargar_en(otros)
        self.assertIs(otros.estadio_seleccionado.cesped, Cesped.OSCURO)

    def test_base_sin_datos_deja_los_valores_por_defecto(self) -> None:
        self.abrir().cerrar()

        menus = Menus()
        self.abrir().cargar_en(menus)

        self.assertTrue(menus.sonido_activado)
        self.assertEqual(
            menus.uniformes_seleccionados[Equipo.VISITANTE].camiseta,
            (40, 80, 200),
        )

    def test_base_indisponible_no_rompe_el_juego(self) -> None:
        guardado = Guardado(
            Path(self.ruta.parent) / "no_existe" / "base.sqlite"
        )
        self.addCleanup(guardado.cerrar)
        self.assertFalse(guardado.disponible)

        menus = Menus()
        menus._ejecutar(Accion.SONIDO)
        guardado.guardar_desde(menus)
        guardado.cargar_en(menus)

        self.assertFalse(guardado.disponible)
        self.assertFalse(menus.sonido_activado)

    def test_datos_corruptos_se_ignoran(self) -> None:
        guardado = self.abrir()
        guardado.guardar_desde(Menus())
        guardado.conexion.execute(
            "UPDATE ajustes SET escudo_forma = 'no-existe' WHERE id = 1"
        )

        menus = Menus()
        self.abrir().cargar_en(menus)

        self.assertEqual(menus.escudo_forma, FORMAS_ESCUDO[0])

    def test_los_veintidos_jugadores_quedan_guardados(self) -> None:
        guardado = self.abrir()
        guardado.guardar_desde(Menus())
        filas = guardado.conexion.execute(
            "SELECT COUNT(*) FROM jugadores"
        ).fetchone()[0]

        self.assertEqual(filas, 22)

    def test_un_campo_corrupto_no_descarta_el_resto_del_guardado(self) -> None:
        menus = Menus()
        menus._ejecutar(Accion.SONIDO)
        menus.formacion_nombre = "3-5-2"
        guardado = self.abrir()
        guardado.guardar_desde(menus)
        guardado.conexion.execute(
            """
            UPDATE ajustes
            SET escudo_forma = 'no-existe', escudo_color = 'rojo'
            WHERE id = 1
            """
        )
        guardado.conexion.commit()

        otros = Menus()
        self.abrir().cargar_en(otros)

        # Los campos válidos se aplican y los corruptos conservan el
        # valor que ya tenía el menú, sin descartar toda la carga.
        self.assertFalse(otros.sonido_activado)
        self.assertEqual(otros.formacion_nombre, "3-5-2")
        self.assertEqual(otros.escudo_forma, FORMAS_ESCUDO[0])
        self.assertEqual(otros.escudo_color, ESCUDO_PRESETS[0][1])
        self.assertEqual(len(otros.plantillas_seleccionadas[Equipo.LOCAL]), 11)

    def test_los_colores_fuera_de_rango_se_recortan(self) -> None:
        guardado = self.abrir()
        guardado.guardar_desde(Menus())
        guardado.conexion.execute(
            """
            UPDATE ajustes
            SET escudo_color = '300,-20,128',
                local_camiseta = '999,0,0'
            WHERE id = 1
            """
        )
        guardado.conexion.commit()

        otros = Menus()
        self.abrir().cargar_en(otros)

        self.assertEqual(otros.escudo_color, (255, 0, 128))
        self.assertEqual(
            otros.uniformes_seleccionados[Equipo.LOCAL].camiseta,
            (255, 0, 0),
        )

    def test_un_menu_con_datos_raros_se_sanea_al_guardar(self) -> None:
        menus = Menus()
        menus.escudo_color = (300, -4, 50)
        menus.escudo_forma = "no-existe"  # type: ignore[assignment]
        menus.uniformes_seleccionados[Equipo.LOCAL] = Uniforme(
            (999, 0, 0),
            (0, 300, 0),
            (-1, 0, 255),
        )
        guardado = self.abrir()
        guardado.guardar_desde(menus)

        otros = Menus()
        self.abrir().cargar_en(otros)

        self.assertEqual(otros.escudo_color, (255, 0, 50))
        self.assertEqual(otros.escudo_forma, FORMAS_ESCUDO[0])
        uniforme = otros.uniformes_seleccionados[Equipo.LOCAL]
        self.assertEqual(uniforme.camiseta, (255, 0, 0))
        self.assertEqual(uniforme.pantalon, (0, 255, 0))
        self.assertEqual(uniforme.medias, (0, 0, 255))

    def test_una_plantilla_incompleta_se_completa_al_cargar(self) -> None:
        menus = Menus()
        menus.formacion_nombre = "4-3-3"
        guardado = self.abrir()
        guardado.guardar_desde(menus)
        guardado.conexion.execute(
            """
            DELETE FROM jugadores
            WHERE equipo = 'local' AND indice IN (2, 7)
            """
        )
        guardado.conexion.execute(
            """
            UPDATE jugadores
            SET dorsal = 500, rol = 'no-existe', x = 5,
                y = -3, factor_velocidad = 999, factor_fuerza = -1
            WHERE equipo = 'local' AND indice = 0
            """
        )
        guardado.conexion.commit()

        otros = Menus()
        self.abrir().cargar_en(otros)

        local = otros.plantillas_seleccionadas[Equipo.LOCAL]
        visitante = otros.plantillas_seleccionadas[Equipo.VISITANTE]
        self.assertEqual(len(local), 11)
        self.assertEqual(len(visitante), 11)
        self.assertTrue(all(ficha.nombre for ficha in local))
        self.assertEqual(local[2].nombre, "Ferrer")
        self.assertEqual(local[7].nombre, "Molina")
        self.assertEqual(local[0].dorsal, 99)
        self.assertIs(local[0].rol, Rol.PORTERO)
        self.assertEqual((local[0].x, local[0].y), (1.0, 0.0))
        self.assertEqual(local[0].factor_velocidad, PRESETS_VELOCIDAD[-1][1])
        self.assertEqual(local[0].factor_fuerza, 0.8)

    def test_sin_jugadores_se_aplica_la_formacion_guardada(self) -> None:
        menus = Menus()
        menus.formacion_nombre = "4-3-3"
        guardado = self.abrir()
        guardado.guardar_desde(menus)
        guardado.conexion.execute("DELETE FROM jugadores")
        guardado.conexion.commit()

        otros = Menus()
        self.abrir().cargar_en(otros)

        roles = [
            ficha.rol
            for ficha in otros.plantillas_seleccionadas[Equipo.LOCAL]
        ]
        self.assertEqual(roles.count(Rol.PORTERO), 1)
        self.assertEqual(roles.count(Rol.DEFENSA), 4)
        self.assertEqual(roles.count(Rol.MEDIO), 3)
        self.assertEqual(roles.count(Rol.DELANTERO), 3)


class TorneoGuardadoTests(unittest.TestCase):
    """Guardar y reanudar torneos de los modos en la base de datos."""

    def setUp(self) -> None:
        pygame.init()
        pygame.display.set_mode((ANCHO, 650))
        self.addCleanup(pygame.quit)

        directorio = tempfile.TemporaryDirectory()
        self.addCleanup(directorio.cleanup)
        self.guardado = Guardado(Path(directorio.name) / "torneos.sqlite")
        self.addCleanup(self.guardado.cerrar)

    def test_la_liga_se_reanuda_en_su_jornada(self) -> None:
        liga = Liga()

        for _ in range(3):
            liga.registrar(2, 1)

        self.guardado.guardar_torneo(ModoJuego.LIGA, liga)

        reanudada = self.guardado.cargar_torneo(ModoJuego.LIGA)
        self.assertIsInstance(reanudada, Liga)
        self.assertEqual(reanudada.jornada, 3)
        self.assertEqual(
            reanudada.tabla[0].puntos,
            liga.tabla[0].puntos,
        )
        self.assertFalse(reanudada.terminado)
        self.assertEqual(reanudada.rival_del_partido(), liga.rival_del_partido())

    def test_la_copa_se_reanuda_en_su_ronda(self) -> None:
        copa = Copa()
        copa.registrar(1, 0)
        self.guardado.guardar_torneo(ModoJuego.COPA, copa)

        reanudada = self.guardado.cargar_torneo(ModoJuego.COPA)

        self.assertEqual(reanudada._ronda, 1)
        self.assertFalse(reanudada.terminado)
        self.assertIn("Semifinal", reanudada.etiqueta())

    def test_los_campeones_se_reanudan_en_grupos(self) -> None:
        torneo = Campeones()
        torneo.registrar(3, 1)
        self.guardado.guardar_torneo(ModoJuego.CAMPEONES, torneo)

        reanudada = self.guardado.cargar_torneo(ModoJuego.CAMPEONES)

        self.assertEqual(reanudada._fase, Campeones.FASE_GRUPOS)
        self.assertEqual(reanudada._jornada, 1)
        self.assertEqual(reanudada.tabla_a[0].gf, 3)

    def test_la_supervivencia_recupera_su_racha(self) -> None:
        racha = Supervivencia()
        racha.registrar(2, 0)
        racha.registrar(1, 0)
        self.guardado.guardar_torneo(ModoJuego.SUPERVIVENCIA, racha)

        reanudada = self.guardado.cargar_torneo(ModoJuego.SUPERVIVENCIA)

        self.assertEqual(reanudada.racha, 2)
        self.assertEqual(reanudada.rival_del_partido(), 3)

    def test_el_torneo_terminado_no_se_guarda(self) -> None:
        liga = Liga()

        for _ in range(11):
            liga.registrar(2, 0)

        self.guardado.guardar_torneo(ModoJuego.LIGA, liga)

        self.assertIsNone(self.guardado.cargar_torneo(ModoJuego.LIGA))
        filas = self.guardado.conexion.execute(
            "SELECT COUNT(*) FROM torneos"
        ).fetchone()[0]
        self.assertEqual(filas, 0)

    def test_guardar_none_borra_la_fila(self) -> None:
        self.guardado.guardar_torneo(ModoJuego.COPA, Copa())
        self.guardado.guardar_torneo(ModoJuego.COPA, None)

        self.assertIsNone(self.guardado.cargar_torneo(ModoJuego.COPA))

    def test_datos_corruptos_se_ignoran(self) -> None:
        self.guardado.conexion.execute(
            "INSERT INTO torneos (modo, datos) VALUES ('liga', '{no-json')")
        self.guardado.conexion.commit()

        self.assertIsNone(self.guardado.cargar_torneo(ModoJuego.LIGA))

    def test_indices_fuera_de_rango_se_acotan(self) -> None:
        # Una fila editada a mano con una jornada imposible no debe
        # poder crashear el juego al reanudar: se acota al calendario.
        self.guardado.conexion.execute(
            'INSERT INTO torneos (modo, datos) VALUES '
            "( 'liga', '{\"jornada\": 999, \"tabla\": {}}' )"
        )
        self.guardado.conexion.commit()

        reanudada = self.guardado.cargar_torneo(ModoJuego.LIGA)
        self.assertEqual(reanudada.jornada, 11)

        copa = Copa()
        copa.restaurar(
            {"ronda": 7, "emparejamientos": [], "eliminado": False}
        )
        self.assertEqual(copa._ronda, 2)

    def test_jugar_reanuda_el_torneo_guardado(self) -> None:
        from futbol_silueta.aplicacion import Aplicacion

        directorio = tempfile.TemporaryDirectory()
        self.addCleanup(directorio.cleanup)
        guardado = Guardado(Path(directorio.name) / "app.sqlite")
        self.addCleanup(guardado.cerrar)

        app = Aplicacion(pygame.display.get_surface(), guardado=guardado)
        self.addCleanup(guardado.cerrar)

        app.menus.modo_seleccionado = ModoJuego.LIGA
        app.menus._accion_pendiente = Accion.JUGAR
        app._ejecutar_accion_pendiente()

        liga = app.juego.torneo
        self.assertIsInstance(liga, Liga)
        liga.registrar(1, 0)
        app.guardado.guardar_torneo(ModoJuego.LIGA, liga)

        otra = Aplicacion(pygame.display.get_surface(), guardado=guardado)
        self.addCleanup(otra.guardado.cerrar)

        otra.menus.modo_seleccionado = ModoJuego.LIGA
        otra.menus._accion_pendiente = Accion.JUGAR
        otra._ejecutar_accion_pendiente()
        self.assertEqual(otra.juego.torneo.jornada, 1)


if __name__ == "__main__":
    unittest.main()
