"""Pruebas headless de los menús y sus botones."""

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
    ALTO,
    ANCHO,
    SUSTITUCIONES_MAXIMAS,
    TITULARES_POR_EQUIPO,
    Equipo,
    Rol,
)
from futbol_silueta.escudos import ESCUDO_PRESETS, FORMAS_ESCUDO
from futbol_silueta.estadios import Cesped, Clima, Diseno, Momento
from futbol_silueta.menus import Accion, Menus, Pantalla
from futbol_silueta.plantilla import suplentes_por_defecto
from futbol_silueta.tienda_estadios import (
    ESTADIO_GRATIS,
    articulo_por_id,
)
from futbol_silueta.uniformes import UNIFORME_PRESETS


class MenusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        cls.pantalla = pygame.display.set_mode((ANCHO, ALTO))

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def setUp(self) -> None:
        self.menus = Menus()

    def _evento_raton(
        self,
        tipo: int,
        posicion: tuple[int, int],
        boton: int = 1,
    ) -> pygame.event.Event:
        return pygame.event.Event(
            tipo,
            {"pos": posicion, "button": boton},
        )

    def test_inicia_en_el_menu_principal(self) -> None:
        self.assertIs(self.menus.pantalla, Pantalla.PRINCIPAL)
        boton = self.menus.boton_actual

        self.assertIsNotNone(boton)
        assert boton is not None
        self.assertIs(boton.accion, Accion.JUGAR)
        self.assertAlmostEqual(boton.rect.centerx, ANCHO // 2, delta=3)

    def test_los_hotspots_caben_en_la_pantalla(self) -> None:
        for pantalla in (Pantalla.PRINCIPAL, Pantalla.PAUSA):
            for boton in self.menus.botones[pantalla]:
                self.assertGreaterEqual(boton.rect.left, 0)
                self.assertGreaterEqual(boton.rect.top, 0)
                self.assertLessEqual(boton.rect.right, ANCHO)
                self.assertLessEqual(boton.rect.bottom, ALTO)

    def test_click_en_jugar_presenta_el_estadio_y_abre_el_partido(self) -> None:
        rect = self.menus.botones[Pantalla.PRINCIPAL][0].rect
        evento = self._evento_raton(
            pygame.MOUSEBUTTONDOWN,
            rect.center,
        )

        self.menus.procesar_evento(evento)

        # JUGAR abre el selector de modos; desde él, "Campaña" presenta
        # el estadio rival y espera a que el jugador pulse "Comenzar".
        self.assertIs(self.menus.pantalla, Pantalla.MODOS)
        self.assertIsNone(self.menus.consumir_accion())

        rect_modos = self.menus.botones[Pantalla.MODOS][0].rect
        self.menus.procesar_evento(
            self._evento_raton(
                pygame.MOUSEBUTTONDOWN,
                rect_modos.center,
            )
        )

        self.assertIs(self.menus.pantalla, Pantalla.PRESENTACION)
        self.assertIs(self.menus.consumir_accion(), Accion.PRESENTAR)

        rect_presentacion = self.menus.botones[Pantalla.PRESENTACION][0].rect
        self.menus.procesar_evento(
            self._evento_raton(
                pygame.MOUSEBUTTONDOWN,
                rect_presentacion.center,
            )
        )

        self.assertIs(self.menus.pantalla, Pantalla.PARTIDO)
        self.assertIsNone(self.menus.consumir_accion())

    def test_click_en_todos_los_botones_principales(self) -> None:
        casos = (
            (0, Pantalla.MODOS, None),
            (1, Pantalla.OPCIONES, None),
            (2, Pantalla.AYUDA, None),
            (3, Pantalla.PRINCIPAL, Accion.SALIR),
        )

        for indice, pantalla, accion in casos:
            menus = Menus()
            rect = menus.botones[Pantalla.PRINCIPAL][indice].rect
            menus.procesar_evento(
                self._evento_raton(
                    pygame.MOUSEBUTTONDOWN,
                    rect.center,
                )
            )

            self.assertIs(menus.pantalla, pantalla, f"botón {indice}")
            self.assertIs(
                menus.consumir_accion(),
                accion,
                f"botón {indice}",
            )

    def test_click_en_todos_los_botones_de_pausa(self) -> None:
        casos = (
            (0, Pantalla.PARTIDO, None),
            (1, Pantalla.PARTIDO, Accion.REINICIAR),
            (2, Pantalla.OPCIONES, None),
            (3, Pantalla.PRINCIPAL, Accion.MENU_PRINCIPAL),
        )

        for indice, pantalla, accion in casos:
            menus = Menus()
            menus.abrir_pausa()
            rect = menus.botones[Pantalla.PAUSA][indice].rect
            menus.procesar_evento(
                self._evento_raton(
                    pygame.MOUSEBUTTONDOWN,
                    rect.center,
                )
            )

            self.assertIs(menus.pantalla, pantalla, f"botón {indice}")
            self.assertIs(
                menus.consumir_accion(),
                accion,
                f"botón {indice}",
            )

            if indice == 2:
                menus.procesar_tecla(pygame.K_ESCAPE)
                self.assertIs(menus.pantalla, Pantalla.PAUSA)

    def test_hover_actualiza_la_seleccion(self) -> None:
        rect = self.menus.botones[Pantalla.PRINCIPAL][1].rect
        evento = self._evento_raton(pygame.MOUSEMOTION, rect.center)

        self.menus.procesar_evento(evento)

        boton = self.menus.boton_actual
        self.assertIsNotNone(boton)
        assert boton is not None
        self.assertIs(boton.accion, Accion.OPCIONES)

    def test_teclado_navega_y_abre_opciones(self) -> None:
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)

        self.assertIs(self.menus.pantalla, Pantalla.OPCIONES)
        self.menus.procesar_tecla(pygame.K_ESCAPE)
        self.assertIs(self.menus.pantalla, Pantalla.PRINCIPAL)

    def test_opciones_cambia_el_sonido_y_vuelve(self) -> None:
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)
        self.assertTrue(self.menus.sonido_activado)

        self.menus.procesar_tecla(pygame.K_RETURN)
        self.assertFalse(self.menus.sonido_activado)
        self.assertEqual(
            self.menus.boton_actual.etiqueta,
            "Sonido: DESACTIVADO",
        )

        # "Volver" es el octavo botón de Opciones, tras Tácticas,
        # Uniformes, escudo, el editor, Estadio y Palmarés.
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)
        self.assertIs(self.menus.pantalla, Pantalla.PRINCIPAL)

        # El ajuste se conserva al volver a entrar.
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)
        self.assertFalse(self.menus.sonido_activado)

    def test_opciones_abren_el_escudo_y_aplican_un_preset(self) -> None:
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)
        self.assertIs(self.menus.pantalla, Pantalla.OPCIONES)

        # El escudo es el cuarto botón de Opciones, tras Tácticas y
        # Uniformes.
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)
        self.assertIs(self.menus.pantalla, Pantalla.ESCUDO)

        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)

        color, color_borde, forma = self.menus.escudo_seleccionado
        self.assertEqual(color, ESCUDO_PRESETS[1][1])
        self.assertEqual(color_borde, ESCUDO_PRESETS[1][2])
        self.assertEqual(forma, FORMAS_ESCUDO[0])

        # La primera forma queda aplicada: 6 colores y 3 formas antes de
        # Volver, así que hay que bajar cinco veces desde el segundo color.
        for _ in range(5):
            self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)

        _color, _borde, forma = self.menus.escudo_seleccionado
        self.assertEqual(forma, FORMAS_ESCUDO[0])

        self.menus.procesar_tecla(pygame.K_ESCAPE)
        self.assertIs(self.menus.pantalla, Pantalla.OPCIONES)

    def test_tacticas_aplica_una_formacion_a_las_fichas(self) -> None:
        self.menus.procesar_tecla(pygame.K_DOWN)  # Opciones
        self.menus.procesar_tecla(pygame.K_RETURN)
        self.menus.procesar_tecla(pygame.K_DOWN)  # Tácticas
        self.menus.procesar_tecla(pygame.K_RETURN)
        self.assertIs(self.menus.pantalla, Pantalla.TACTICA)

        # Segunda formación de la lista: 4-3-3.
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)

        self.assertEqual(self.menus.formacion_nombre, "4-3-3")
        self.assertIs(self.menus.consumir_accion(), Accion.FORMACION)

        for equipo in (Equipo.LOCAL, Equipo.VISITANTE):
            fichas = self.menus.plantillas_editables[equipo]
            roles = [ficha.rol for ficha in fichas]

            self.assertEqual(len(fichas), 11)
            self.assertEqual(roles.count(Rol.PORTERO), 1)
            self.assertEqual(roles.count(Rol.DEFENSA), 4)
            self.assertEqual(roles.count(Rol.MEDIO), 3)
            self.assertEqual(roles.count(Rol.DELANTERO), 3)

        # La identidad de cada jugador se conserva al recolocar.
        local = self.menus.plantillas_editables[Equipo.LOCAL]
        self.assertEqual(local[0].nombre, "Cabrera")
        self.assertEqual(local[0].dorsal, 1)
        self.assertIs(local[0].rol, Rol.PORTERO)

    def test_volver_encadena_pantallas_sin_atascarse(self) -> None:
        # Opciones -> Escudo -> ESC -> ESC: de regreso al principal.
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_DOWN)  # Personalizar escudo
        self.menus.procesar_tecla(pygame.K_RETURN)
        self.assertIs(self.menus.pantalla, Pantalla.ESCUDO)

        self.menus.procesar_tecla(pygame.K_ESCAPE)
        self.assertIs(self.menus.pantalla, Pantalla.OPCIONES)
        self.menus.procesar_tecla(pygame.K_ESCAPE)
        self.assertIs(self.menus.pantalla, Pantalla.PRINCIPAL)

        # Y desde la pausa, Configuración vuelve a la pausa.
        self.menus.abrir_pausa()
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_DOWN)  # Configuración
        self.menus.procesar_tecla(pygame.K_RETURN)
        self.assertIs(self.menus.pantalla, Pantalla.OPCIONES)
        self.menus.procesar_tecla(pygame.K_ESCAPE)
        self.assertIs(self.menus.pantalla, Pantalla.PAUSA)

    def test_estadio_cicla_cesped_momento_diseno_y_gradas(self) -> None:
        self.menus.procesar_tecla(pygame.K_DOWN)  # Opciones
        self.menus.procesar_tecla(pygame.K_RETURN)
        for _ in range(5):
            self.menus.procesar_tecla(pygame.K_DOWN)  # Estadio
        self.menus.procesar_tecla(pygame.K_RETURN)
        self.assertIs(self.menus.pantalla, Pantalla.ESTADIO)

        self.menus.procesar_tecla(pygame.K_RETURN)  # Césped
        self.assertIs(self.menus.estadio_seleccionado.cesped, Cesped.OSCURO)

        self.menus.procesar_tecla(pygame.K_DOWN)  # Momento
        self.menus.procesar_tecla(pygame.K_RETURN)
        self.assertIs(self.menus.estadio_seleccionado.momento, Momento.NOCHE)

        self.menus.procesar_tecla(pygame.K_DOWN)  # Clima
        self.menus.procesar_tecla(pygame.K_RIGHT)
        self.assertIs(self.menus.estadio_seleccionado.clima, Clima.LLUVIA)

        self.menus.procesar_tecla(pygame.K_DOWN)  # Diseño
        self.menus.procesar_tecla(pygame.K_RIGHT)
        self.assertIs(self.menus.estadio_seleccionado.diseno, Diseno.RAYAS)

        self.menus.procesar_tecla(pygame.K_DOWN)  # Gradas
        self.menus.procesar_tecla(pygame.K_RETURN)
        self.assertFalse(self.menus.estadio_seleccionado.gradas)

        etiquetas = {
            boton.accion: boton.etiqueta
            for boton in self.menus.botones[Pantalla.ESTADIO]
        }
        self.assertEqual(etiquetas[Accion.CESPED], "Césped: OSCURO")
        self.assertEqual(etiquetas[Accion.MOMENTO], "Momento: NOCHE")
        self.assertEqual(etiquetas[Accion.CLIMA], "Clima: LLUVIA")
        self.assertEqual(etiquetas[Accion.DISENO], "Diseño: RAYAS")
        self.assertEqual(etiquetas[Accion.GRADAS], "Gradas: SIN AFICIONADOS")

        self.menus.procesar_tecla(pygame.K_ESCAPE)
        self.assertIs(self.menus.pantalla, Pantalla.OPCIONES)

    def test_la_galeria_recorre_estadios_y_vistas(self) -> None:
        self.menus._ejecutar(Accion.ESTADIO)
        self.menus._ejecutar(Accion.GALERIA_ESTADIOS)

        self.assertIs(self.menus.pantalla, Pantalla.GALERIA)
        self.assertEqual(self.menus.estadio_galeria.nivel, 1)
        self.assertEqual(self.menus.vista_galeria.etiqueta, "Exterior")

        self.menus._ejecutar(Accion.SIGUIENTE_ESTADIO)
        self.assertEqual(self.menus.estadio_galeria.nivel, 2)
        self.assertEqual(self.menus.indice_vista_galeria, 0)

        # "Vista >" es el cuarto botón de la galería.
        self.menus._ejecutar(
            Accion.VISTA_ESTADIO,
            self.menus.botones[Pantalla.GALERIA][3],
        )
        self.assertEqual(self.menus.vista_galeria.etiqueta, "Acceso")

        # El dibujo carga la foto y la deja en la caché acotada.
        self.menus.dibujar(self.pantalla)
        self.assertTrue(self.menus._cache_estadios)
        self.assertLessEqual(
            len(self.menus._cache_estadios),
            self.menus._MAXIMO_CACHE_ESTADIOS,
        )

        self.menus.procesar_tecla(pygame.K_ESCAPE)
        self.assertIs(self.menus.pantalla, Pantalla.ESTADIO)

    def test_el_palmares_se_abre_y_vuelve(self) -> None:
        self.menus.procesar_tecla(pygame.K_DOWN)  # Opciones
        self.menus.procesar_tecla(pygame.K_RETURN)
        for _ in range(6):
            self.menus.procesar_tecla(pygame.K_DOWN)  # Palmarés
        self.menus.procesar_tecla(pygame.K_RETURN)
        self.assertIs(self.menus.pantalla, Pantalla.PALMARES)

        # Se dibuja con la tabla, el historial y los trofeos vacíos.
        self.menus.dibujar(self.pantalla)

        self.menus.procesar_tecla(pygame.K_ESCAPE)
        self.assertIs(self.menus.pantalla, Pantalla.OPCIONES)

    def test_flecha_izquierda_cicla_hacia_atras(self) -> None:
        self.menus.procesar_tecla(pygame.K_DOWN)  # Opciones
        self.menus.procesar_tecla(pygame.K_RETURN)
        for _ in range(5):
            self.menus.procesar_tecla(pygame.K_DOWN)  # Estadio
        self.menus.procesar_tecla(pygame.K_RETURN)

        self.menus.procesar_tecla(pygame.K_LEFT)  # Césped
        self.assertIs(
            self.menus.estadio_seleccionado.cesped,
            Cesped.ARTIFICIAL,
        )

        self.menus.procesar_tecla(pygame.K_DOWN)  # Momento
        self.menus.procesar_tecla(pygame.K_LEFT)
        self.assertIs(self.menus.estadio_seleccionado.momento, Momento.NOCHE)

        self.menus.procesar_tecla(pygame.K_DOWN)  # Clima
        self.menus.procesar_tecla(pygame.K_LEFT)

        self.menus.procesar_tecla(pygame.K_DOWN)  # Diseño
        self.menus.procesar_tecla(pygame.K_LEFT)
        self.assertIs(self.menus.estadio_seleccionado.diseno, Diseno.CIRCULOS)

        # El local viste de rojo (tercer preset); ← pasa al anterior.
        self.menus._ejecutar(Accion.OPCIONES)
        self.menus._ejecutar(Accion.UNIFORME)
        self.menus.procesar_tecla(pygame.K_DOWN)  # Camiseta
        self.menus.procesar_tecla(pygame.K_LEFT)
        self.assertEqual(
            self.menus.uniformes_seleccionados[Equipo.LOCAL].camiseta,
            UNIFORME_PRESETS[1][1],
        )

    def test_el_editor_acepta_espacios_en_el_nombre(self) -> None:
        self.menus._ejecutar(Accion.EDITOR)
        self.menus._ejecutar(Accion.EDITOR_NOMBRE)

        for _ in range(12):
            self.menus.procesar_tecla(pygame.K_BACKSPACE)
        for tecla in (
            pygame.K_a,
            pygame.K_n,
            pygame.K_a,
            pygame.K_SPACE,
            pygame.K_m,
            pygame.K_a,
            pygame.K_r,
            pygame.K_i,
            pygame.K_a,
        ):
            self.menus.procesar_tecla(tecla)
        self.menus.procesar_tecla(pygame.K_RETURN)

        self.assertEqual(
            self.menus.plantillas_seleccionadas[Equipo.LOCAL][0].nombre,
            "Ana maria",
        )

    def test_el_editor_reconstruye_una_plantilla_vacia(self) -> None:
        self.menus.plantillas_editables[Equipo.LOCAL] = []
        self.menus._ejecutar(Accion.EDITOR)
        self.menus._ejecutar(Accion.CICLAR_DORSAL)

        local = self.menus.plantillas_seleccionadas[Equipo.LOCAL]
        self.assertEqual(len(local), 11)
        self.assertEqual(local[0].dorsal, 2)

    def test_ayuda_muestra_los_controles_y_vuelve(self) -> None:
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)

        self.assertIs(self.menus.pantalla, Pantalla.AYUDA)
        self.assertEqual(len(self.menus.botones_actuales), 1)

        self.menus.procesar_tecla(pygame.K_RETURN)
        self.assertIs(self.menus.pantalla, Pantalla.PRINCIPAL)

    def test_pausa_continuar_reiniciar_y_menu(self) -> None:
        self.menus.abrir_pausa()
        self.assertIs(self.menus.pantalla, Pantalla.PAUSA)

        self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)

        self.assertIs(self.menus.pantalla, Pantalla.PARTIDO)
        self.assertIs(self.menus.consumir_accion(), Accion.REINICIAR)

        self.menus.abrir_pausa()
        for _ in range(3):
            self.menus.procesar_tecla(pygame.K_DOWN)
        self.menus.procesar_tecla(pygame.K_RETURN)

        self.assertIs(self.menus.pantalla, Pantalla.PRINCIPAL)
        self.assertIs(
            self.menus.consumir_accion(),
            Accion.MENU_PRINCIPAL,
        )

        self.menus.abrir_pausa()
        self.menus.procesar_tecla(pygame.K_ESCAPE)
        self.assertIs(self.menus.pantalla, Pantalla.PARTIDO)

    def test_escape_en_el_menu_principal_pide_salir(self) -> None:
        self.menus.procesar_tecla(pygame.K_ESCAPE)

        self.assertIs(self.menus.pantalla, Pantalla.PRINCIPAL)
        self.assertIs(self.menus.consumir_accion(), Accion.SALIR)
        self.assertIsNone(self.menus.consumir_accion())

    def test_dibuja_todas_las_pantallas(self) -> None:
        for pantalla in (
            Pantalla.PRINCIPAL,
            Pantalla.OPCIONES,
            Pantalla.ESCUDO,
            Pantalla.UNIFORME,
            Pantalla.EDITOR,
            Pantalla.TACTICA,
            Pantalla.ESTADIO,
            Pantalla.GALERIA,
            Pantalla.PRESENTACION,
            Pantalla.PALMARES,
            Pantalla.SUSTITUCIONES,
            Pantalla.AYUDA,
            Pantalla.PAUSA,
            Pantalla.ENTRENAMIENTOS,
            Pantalla.TIENDA_ESTADIOS,
        ):
            self.menus.pantalla = pantalla
            self.menus.indice = 0
            self.menus.dibujar(self.pantalla)

        self.assertIsNotNone(pygame.display.get_surface())

    def test_sustituciones_elegir_y_confirmar(self) -> None:
        menus = self.menus
        menus.abrir_sustituciones()

        self.assertIs(menus.pantalla, Pantalla.SUSTITUCIONES)
        suplentes = suplentes_por_defecto(Equipo.LOCAL)
        self.assertEqual(
            len(menus.botones_actuales),
            TITULARES_POR_EQUIPO + len(suplentes) + 2,
        )

        # Sale el delantero del hueco 9 (dorsal 10); entra el primer
        # suplente (dorsal 12), marcando ambos y confirmando.
        menus._ejecutar(Accion.ELEGIR_SALE, menus.botones_actuales[9])
        menus._ejecutar(
            Accion.ELEGIR_ENTRA,
            menus.botones_actuales[TITULARES_POR_EQUIPO],
        )
        menus._ejecutar(Accion.HACER_CAMBIO)

        self.assertEqual(menus.cambios_usados[Equipo.LOCAL], 1)
        entrante = menus.plantillas_editables[Equipo.LOCAL][9]

        self.assertEqual(entrante.dorsal, suplentes[0].dorsal)
        self.assertEqual(entrante.nombre, suplentes[0].nombre)
        self.assertIs(entrante.rol, Rol.DELANTERO)
        saliente = menus.suplentes_editables[Equipo.LOCAL][0]
        self.assertEqual(saliente.dorsal, 10)

        sustitucion = menus.consumir_sustitucion()
        self.assertIsNotNone(sustitucion)
        assert sustitucion is not None
        equipo, hueco, dorsal_saliente, ficha = sustitucion

        self.assertIs(equipo, Equipo.LOCAL)
        self.assertEqual(hueco, 9)
        self.assertEqual(dorsal_saliente, 10)
        self.assertEqual(ficha.dorsal, suplentes[0].dorsal)
        self.assertIsNone(menus.consumir_sustitucion())

    def test_el_modo_entrenamiento_abre_su_submenu(self) -> None:
        self.menus._ejecutar(Accion.ENTRENAMIENTO)

        self.assertIs(self.menus.pantalla, Pantalla.ENTRENAMIENTOS)
        self.assertIsNone(self.menus.consumir_accion())

    def test_los_ejercicios_abren_la_sesion_activa(self) -> None:
        for accion in (
            Accion.TIROS,
            Accion.PENALES,
            Accion.DOS_CONTRA_UNO,
        ):
            menus = Menus()
            menus._ejecutar(Accion.ENTRENAMIENTO)
            menus._ejecutar(accion)

            self.assertIs(
                menus.pantalla,
                Pantalla.ENTRENAMIENTO_ACTIVO,
                accion,
            )
            self.assertIs(menus.consumir_accion(), accion)

    def test_campo_libre_pide_el_modo_de_siempre(self) -> None:
        self.menus._ejecutar(Accion.CAMPO_LIBRE)

        self.assertIs(self.menus.pantalla, Pantalla.PARTIDO)
        self.assertIs(self.menus.consumir_accion(), Accion.JUGAR)
        self.assertEqual(self.menus.modo_seleccionado.value, "entrenamiento")

    def test_la_tienda_compra_y_equipa_un_estadio(self) -> None:
        menus = self.menus
        menus.monedas = 300
        menus.abrir_tienda_estadios()
        self.assertIs(menus.pantalla, Pantalla.TIENDA_ESTADIOS)
        self.assertIn(ESTADIO_GRATIS, menus.estadios_comprados)

        boton = next(
            boton
            for boton in menus.botones_actuales
            if boton.valor == "amanecer"
        )
        menus._ejecutar(boton.accion, boton)

        articulo = articulo_por_id("amanecer")
        self.assertIsNotNone(articulo)
        assert articulo is not None
        self.assertEqual(menus.monedas, 300 - articulo.precio)
        self.assertIn("amanecer", menus.estadios_comprados)
        self.assertEqual(menus.estadio_seleccionado, articulo.estadio)
        self.assertIs(menus.consumir_accion(), Accion.COMPRAR_ESTADIO)
        self.assertIn("Compraste", menus.mensaje_tienda)

        # El estadio comprado se puede volver a equipar.
        boton = next(
            boton
            for boton in menus.botones_actuales
            if boton.valor == "amanecer"
        )
        self.assertIs(boton.accion, Accion.EQUIPAR_ESTADIO)
        menus._ejecutar(boton.accion, boton)
        self.assertIs(menus.consumir_accion(), Accion.EQUIPAR_ESTADIO)

    def test_la_tienda_no_vende_sin_monedas(self) -> None:
        menus = self.menus
        menus.monedas = 10
        menus.abrir_tienda_estadios()

        boton = next(
            boton
            for boton in menus.botones_actuales
            if boton.valor == "nocturno"
        )
        menus._ejecutar(boton.accion, boton)

        self.assertEqual(menus.monedas, 10)
        self.assertNotIn("nocturno", menus.estadios_comprados)
        self.assertTrue(menus.mensaje_tienda_error)
        self.assertIn("faltan", menus.mensaje_tienda)

    def test_sustituciones_respetan_el_limite(self) -> None:
        menus = self.menus

        for _ in range(SUSTITUCIONES_MAXIMAS + 1):
            menus.abrir_sustituciones()
            menus._ejecutar(Accion.ELEGIR_SALE, menus.botones_actuales[10])
            menus._ejecutar(
                Accion.ELEGIR_ENTRA,
                menus.botones_actuales[TITULARES_POR_EQUIPO],
            )
            menus._ejecutar(Accion.HACER_CAMBIO)

        self.assertEqual(
            menus.cambios_usados[Equipo.LOCAL],
            SUSTITUCIONES_MAXIMAS,
        )

    def test_reiniciar_sustituciones_vuelve_al_banquillo_original(self) -> None:
        menus = self.menus
        menus.abrir_sustituciones()
        menus._ejecutar(Accion.ELEGIR_SALE, menus.botones_actuales[0])
        menus._ejecutar(
            Accion.ELEGIR_ENTRA,
            menus.botones_actuales[TITULARES_POR_EQUIPO],
        )
        menus._ejecutar(Accion.HACER_CAMBIO)

        self.assertEqual(menus.cambios_usados[Equipo.LOCAL], 1)

        menus.reiniciar_sustituciones()

        self.assertEqual(menus.cambios_usados[Equipo.LOCAL], 0)
        self.assertEqual(
            menus.suplentes_editables[Equipo.LOCAL],
            suplentes_por_defecto(Equipo.LOCAL),
        )
        self.assertIsNone(menus.consumir_sustitucion())


if __name__ == "__main__":
    unittest.main()
