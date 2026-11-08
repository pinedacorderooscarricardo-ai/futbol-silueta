"""Pantallas de menú, fondos ilustrados y botones clicables."""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum
from pathlib import Path

import pygame

from .configuracion import (
    ALTO,
    AMARILLO,
    ANCHO,
    BLANCO,
    NOMBRES_FORMACION,
    SUSTITUCIONES_MAXIMAS,
    TITULARES_POR_EQUIPO,
    Color,
    Equipo,
    Rol,
)
from .escudos import ESCUDO_PRESETS, FORMAS_ESCUDO, Escudo, FormaEscudo
from .modos import DESCRIPCIONES, ETIQUETAS, ModoJuego
from .estadios import (
    CESPEDES,
    CLIMAS,
    DISENOS,
    ESTADIO_POR_DEFECTO,
    MOMENTOS,
    NOMBRES_DISENO,
    NOMBRES_MOMENTO,
    Estadio,
    color_entorno,
    color_tribuna,
    dibujar_aficionados,
    dibujar_cesped,
    siguiente_opcion,
)
from .estadisticas import (
    CLAVE_LOCAL,
    TROFEOS,
    Resultado,
    TablaPosiciones,
)
from .niveles import nivel_por_numero
from .plantilla import (
    LARGO_NOMBRE,
    PRESETS_FUERZA,
    PRESETS_VELOCIDAD,
    ROLES,
    JugadorPlantilla,
    aplicar_formacion,
    nombre_fuerza,
    nombre_velocidad,
    normalizar_plantilla,
    plantilla_por_defecto,
    plantillas_por_defecto,
    suplentes_por_defecto_todos,
)
from .uniformes import (
    UNIFORMES_POR_DEFECTO,
    UNIFORME_PRESETS,
    Uniforme,
    dibujar_jugador_uniforme,
)
from .utilidades import (
    DIRECTORIO_IMAGENES,
    acotar,
    cargar_imagen,
    equipo_rival,
)


class Pantalla(StrEnum):
    """Pantallas que puede mostrar la aplicación."""

    PRINCIPAL = "principal"
    MODOS = "modos"
    OPCIONES = "opciones"
    AYUDA = "ayuda"
    PARTIDO = "partido"
    PAUSA = "pausa"
    ESCUDO = "escudo"
    UNIFORME = "uniforme"
    EDITOR = "editor"
    TACTICA = "tactica"
    ESTADIO = "estadio"
    PALMARES = "palmares"
    SUSTITUCIONES = "sustituciones"


class Accion(StrEnum):
    """Acciones que puede pedir un botón del menú."""

    JUGAR = "jugar"
    CONTINUAR = "continuar"
    REINICIAR = "reiniciar"
    CONFIGURACION = "configuracion"
    OPCIONES = "opciones"
    AYUDA = "ayuda"
    MENU_PRINCIPAL = "menu_principal"
    SONIDO = "sonido"
    VOLVER = "volver"
    SALIR = "salir"
    ESCUDO = "escudo"
    FORMA_ESCUDO = "forma_escudo"
    UNIFORME = "uniforme"
    PRENDA = "prenda"
    EQUIPO_UNIFORME = "equipo_uniforme"
    NUMEROS = "numeros"
    EDITOR = "editor"
    TACTICA = "tactica"
    FORMACION = "formacion"
    EQUIPO_EDITOR = "equipo_editor"
    CICLAR_JUGADOR = "ciclar_jugador"
    EDITOR_NOMBRE = "editor_nombre"
    CICLAR_DORSAL = "ciclar_dorsal"
    CICLAR_VELOCIDAD = "ciclar_velocidad"
    CICLAR_FUERZA = "ciclar_fuerza"
    CICLAR_ROL = "ciclar_rol"
    MOVER_POSICION = "mover_posicion"
    SUSTITUCIONES = "sustituciones"
    ELEGIR_SALE = "elegir_sale"
    ELEGIR_ENTRA = "elegir_entra"
    HACER_CAMBIO = "hacer_cambio"
    ESTADIO = "estadio"
    PALMARES = "palmares"
    CESPED = "cesped"
    MOMENTO = "momento"
    CLIMA = "clima"
    DISENO = "diseno"
    GRADAS = "gradas"
    CAMPANA = "campana"
    LIGA = "liga"
    COPA = "copa"
    CAMPEONES = "campeones"
    SUPERVIVENCIA = "supervivencia"
    ENTRENAMIENTO = "entrenamiento"
    DOS_JUGADORES = "dos_jugadores"



_ETIQUETAS_MODO: dict[ModoJuego, str] = ETIQUETAS
_ACCION_DE_MODO: dict[ModoJuego, Accion] = {
    modo: Accion(modo.value) for modo in ModoJuego
}


class Boton:
    """Zona clicable de una pantalla de menú."""

    def __init__(
        self,
        rect: pygame.Rect,
        etiqueta: str,
        accion: Accion,
        valor: object = None,
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.etiqueta = etiqueta
        self.accion = accion
        self.valor = valor


class FondoImagen:
    """Imagen de fondo escalada para cubrir toda la ventana.

    Guarda la escala y el desplazamiento usados para poder convertir
    las coordenadas de los botones dibujados en la imagen original a
    coordenadas de pantalla.
    """

    def __init__(self, ruta: Path) -> None:
        original = cargar_imagen(ruta)
        ancho, alto = original.get_size()

        self.escala = max(ANCHO / ancho, ALTO / alto)
        ancho_escalado = round(ancho * self.escala)
        alto_escalado = round(alto * self.escala)

        self.desplazamiento = (
            (ANCHO - ancho_escalado) // 2,
            (ALTO - alto_escalado) // 2,
        )
        self.superficie = pygame.transform.smoothscale(
            original,
            (ancho_escalado, alto_escalado),
        )

    def dibujar(self, pantalla: pygame.Surface) -> None:
        """Dibuja la imagen cubriendo la ventana."""
        pantalla.blit(self.superficie, self.desplazamiento)

    def rect(
        self,
        original: tuple[int, int, int, int],
    ) -> pygame.Rect:
        """Convierte un rectángulo de la imagen original a la pantalla."""
        x, y, ancho, alto = original
        desplazamiento_x, desplazamiento_y = self.desplazamiento

        return pygame.Rect(
            desplazamiento_x + round(x * self.escala),
            desplazamiento_y + round(y * self.escala),
            round(ancho * self.escala),
            round(alto * self.escala),
        )


class Menus:
    """Máquina de estados de los menús y su dibujo."""

    ACENTO_PRINCIPAL: Color = (255, 196, 70)
    ACENTO_PAUSA: Color = (120, 255, 170)
    ACENTO_PANEL: Color = (90, 210, 255)
    TEXTO_SUAVE: Color = (185, 200, 215)

    def __init__(self) -> None:
        self.fuente_titulo = pygame.font.SysFont("Arial", 42, bold=True)
        self.fuente_boton = pygame.font.SysFont("Arial", 24, bold=True)
        self.fuente_texto = pygame.font.SysFont("Arial", 20)
        self.fuente_pequena = pygame.font.SysFont("Arial", 16)
        self._cache_textos: dict[
            tuple[str, int, Color],
            pygame.Surface,
        ] = {}

        self.fondo_principal = FondoImagen(
            DIRECTORIO_IMAGENES / "menu_principal.jpeg"
        )
        self.fondo_opciones = FondoImagen(
            DIRECTORIO_IMAGENES / "menu_opciones.jpeg"
        )
        self.fondo_pausa = FondoImagen(
            DIRECTORIO_IMAGENES / "menu_pausa.jpeg"
        )
        self.fondo_ayuda = FondoImagen(
            DIRECTORIO_IMAGENES / "ayuda_controles.jpeg"
        )

        self.botones: dict[Pantalla, list[Boton]] = {
            Pantalla.PRINCIPAL: self._botones_de_imagen(
                self.fondo_principal,
                (
                    ((518, 370, 372, 72), "Jugar", Accion.JUGAR),
                    ((518, 453, 372, 69), "Opciones", Accion.OPCIONES),
                    ((518, 535, 372, 68), "Cómo jugar", Accion.AYUDA),
                    ((518, 617, 372, 68), "Salir", Accion.SALIR),
                ),
            ),
            Pantalla.PAUSA: self._botones_de_imagen(
                self.fondo_pausa,
                (
                    (
                        (428, 253, 552, 64),
                        "Continuar partido",
                        Accion.CONTINUAR,
                    ),
                    (
                        (428, 323, 552, 64),
                        "Reiniciar partido",
                        Accion.REINICIAR,
                    ),
                    (
                        (428, 393, 552, 64),
                        "Configuración",
                        Accion.CONFIGURACION,
                    ),
                    (
                        (428, 463, 552, 64),
                        "Volver al menú principal",
                        Accion.MENU_PRINCIPAL,
                    ),
                    (
                        (428, 545, 552, 56),
                        "Cambios de jugadores",
                        Accion.SUSTITUCIONES,
                    ),
                ),
            ),
            Pantalla.OPCIONES: [
                Boton(
                    pygame.Rect(260, 334, 480, 34),
                    "Sonido: ACTIVADO",
                    Accion.SONIDO,
                ),
                Boton(
                    pygame.Rect(260, 371, 480, 34),
                    "Tácticas",
                    Accion.TACTICA,
                ),
                Boton(
                    pygame.Rect(260, 408, 480, 34),
                    "Uniformes",
                    Accion.UNIFORME,
                ),
                Boton(
                    pygame.Rect(260, 445, 480, 34),
                    "Personalizar escudo",
                    Accion.ESCUDO,
                ),
                Boton(
                    pygame.Rect(260, 482, 480, 34),
                    "Editor de jugadores",
                    Accion.EDITOR,
                ),
                Boton(
                    pygame.Rect(260, 519, 480, 34),
                    "Estadio",
                    Accion.ESTADIO,
                ),
                Boton(
                    pygame.Rect(260, 556, 480, 34),
                    "Palmarés",
                    Accion.PALMARES,
                ),
                Boton(
                    pygame.Rect(260, 593, 480, 34),
                    "Volver",
                    Accion.VOLVER,
                ),
            ],
            Pantalla.ESCUDO: self._botones_de_escudo(),
            Pantalla.MODOS: self._botones_de_modos(),
            Pantalla.UNIFORME: self._botones_de_uniforme(),
            Pantalla.EDITOR: self._botones_de_editor(),
            Pantalla.TACTICA: self._botones_de_tactica(),
            Pantalla.ESTADIO: self._botones_de_estadio(),
            # Se regenera al abrir la pantalla y tras cada cambio.
            Pantalla.SUSTITUCIONES: [],
            Pantalla.PALMARES: [
                Boton(
                    pygame.Rect(380, 545, 240, 52),
                    "Volver",
                    Accion.VOLVER,
                ),
            ],
            Pantalla.AYUDA: [
                Boton(
                    pygame.Rect(380, 468, 240, 52),
                    "Volver",
                    Accion.VOLVER,
                ),
            ],
        }

        self.pantalla = Pantalla.PRINCIPAL
        self.indice = 0
        self.sonido_activado = True
        # Pantallas desde las que se llegó a la actual: al volver se
        # retoma la última, sin importar cuántos niveles se bajaron.
        self._historial: list[Pantalla] = []
        self._accion_pendiente: Accion | None = None

        self.rect_panel_opciones = pygame.Rect(190, 242, 620, 404)
        self.rect_panel_ayuda = pygame.Rect(140, 60, 720, 530)
        self._panel_opciones = self._crear_panel(
            self.rect_panel_opciones,
            self.ACENTO_PANEL,
        )
        self._panel_ayuda = self._crear_panel(
            self.rect_panel_ayuda,
            self.ACENTO_PRINCIPAL,
        )
        self._velo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        self._velo.fill((2, 8, 18, 165))
        self._velo_suave = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        self._velo_suave.fill((2, 8, 18, 38))
        self._pies: dict[str, pygame.Surface] = {}
        # Último cursor aplicado: evita llamar a SDL en cada movimiento.
        self._cursor_activo: bool | None = None
        # Miniatura del estadio, cacheada por configuración.
        self._mini_estadio_cache: tuple[Estadio, pygame.Surface] | None = None

        # Personalización del escudo del jugador.
        self.escudo_color: Color = ESCUDO_PRESETS[0][1]
        self.escudo_color_borde: Color = ESCUDO_PRESETS[0][2]
        self.escudo_forma: FormaEscudo = FORMAS_ESCUDO[0]

        self.rect_panel_escudo = pygame.Rect(150, 90, 700, 520)
        self._panel_escudo = self._crear_panel(
            self.rect_panel_escudo,
            self.ACENTO_PANEL,
        )

        # Personalización de los uniformes de cada equipo.
        self.uniformes_seleccionados: dict[Equipo, Uniforme] = dict(
            UNIFORMES_POR_DEFECTO
        )
        self.numeros_activados = True
        self._equipo_uniforme = Equipo.LOCAL

        self.rect_panel_uniforme = pygame.Rect(150, 90, 700, 520)
        self._panel_uniforme = self._crear_panel(
            self.rect_panel_uniforme,
            self.ACENTO_PANEL,
        )
        self._actualizar_etiquetas_uniforme()

        # Editor de jugadores: fichas editables y estado de la pantalla.
        self.plantillas_editables: dict[Equipo, list[JugadorPlantilla]] = {
            equipo: list(fichas)
            for equipo, fichas in plantillas_por_defecto().items()
        }
        self._equipo_editor = Equipo.LOCAL
        self._jugador_editor = 0
        self._editando_nombre = False
        self._moviendo_posicion = False

        self.rect_panel_editor = pygame.Rect(150, 90, 700, 520)
        self._panel_editor = self._crear_panel(
            self.rect_panel_editor,
            self.ACENTO_PANEL,
        )
        self.rect_campo_editor = pygame.Rect(600, 220, 230, 330)
        self._actualizar_etiquetas_editor()

        # Tácticas: formación elegida y panel con su vista previa.
        self.formacion_nombre: str = NOMBRES_FORMACION[0]
        self.rect_panel_tactica = pygame.Rect(150, 90, 700, 520)
        self._panel_tactica = self._crear_panel(
            self.rect_panel_tactica,
            self.ACENTO_PANEL,
        )
        self.rect_campo_tactica = pygame.Rect(600, 220, 230, 330)

        # Estadio: césped, momento, gradas y diseño de la cancha.
        self._estadio = ESTADIO_POR_DEFECTO
        # Modo de juego elegido en la pantalla de modos.
        self.modo_seleccionado = ModoJuego.CAMPANA

        self.rect_panel_modos = pygame.Rect(150, 90, 700, 520)
        self._panel_modos = self._crear_panel(
            self.rect_panel_modos,
            self.ACENTO_PANEL,
        )

        self.rect_panel_estadio = pygame.Rect(150, 90, 700, 520)
        self._panel_estadio = self._crear_panel(
            self.rect_panel_estadio,
            self.ACENTO_PANEL,
        )

        # Palmarés de la campaña: tabla de posiciones, historial de
        # resultados y trofeos desbloqueados (los llena el guardado).
        self.tabla_posiciones = TablaPosiciones()
        self.historial: list[Resultado] = []
        self.trofeos: set[str] = set()
        self.rect_panel_palmares = pygame.Rect(110, 90, 780, 520)
        self._panel_palmares = self._crear_panel(
            self.rect_panel_palmares,
            self.ACENTO_PANEL,
        )

        # Sustituciones: banquillo del equipo humano, pareja elegida
        # (hueco que sale, índice de banquillo que entra) y cambios ya
        # usados por equipo, con tope por partido.
        self.suplentes_editables = suplentes_por_defecto_todos()
        self.cambios_usados: dict[Equipo, int] = dict.fromkeys(
            Equipo,
            0,
        )
        self._cambio_sale: int | None = None
        self._cambio_entra: int | None = None
        self._sustitucion_pendiente: (
            tuple[Equipo, int, int, JugadorPlantilla] | None
        ) = None
        # Cambios confirmados en este partido (equipo, hueco y ficha que
        # salió): se deshacen al empezar el siguiente para que el partido
        # arranque siempre con los once titulares del editor.
        self._sustituciones_partido: list[tuple[Equipo, int, JugadorPlantilla]] = []
        self.rect_panel_sustituciones = pygame.Rect(150, 70, 700, 540)
        self._panel_sustituciones = self._crear_panel(
            self.rect_panel_sustituciones,
            self.ACENTO_PANEL,
        )
        self._regenerar_sustituciones()

    # --------------------------------------------------
    # Construcción
    # --------------------------------------------------

    @staticmethod
    def _botones_de_imagen(
        fondo: FondoImagen,
        definiciones: Sequence[
            tuple[tuple[int, int, int, int], str, Accion]
        ],
    ) -> list[Boton]:
        return [
            Boton(fondo.rect(rect), etiqueta, accion)
            for rect, etiqueta, accion in definiciones
        ]

    @staticmethod
    def _botones_de_escudo() -> list[Boton]:
        """Botones de personalización: colores, formas y volver."""
        colores = [
            Boton(
                pygame.Rect(200, 245 + indice * 50, 300, 38),
                f"Escudo {etiqueta}",
                Accion.ESCUDO,
                valor=indice,
            )
            for indice, (etiqueta, _color, _borde) in enumerate(
                ESCUDO_PRESETS
            )
        ]
        formas = [
            Boton(
                pygame.Rect(550, 245 + indice * 50, 300, 38),
                f"Forma {forma}",
                Accion.FORMA_ESCUDO,
                valor=indice,
            )
            for indice, forma in enumerate(FORMAS_ESCUDO)
        ]

        return colores + formas + [
            Boton(pygame.Rect(260, 535, 480, 44), "Volver", Accion.VOLVER),
        ]

    @staticmethod
    def _botones_de_uniforme() -> list[Boton]:
        """Botones de uniformes: equipo, prendas, dorsales y volver."""
        prendas = (
            ("Camiseta", "camiseta"),
            ("Pantalón", "pantalon"),
            ("Medias", "medias"),
        )
        botones = [
            Boton(
                pygame.Rect(190, 220, 370, 44),
                "Equipo: LOCAL",
                Accion.EQUIPO_UNIFORME,
            )
        ]
        botones.extend(
            Boton(
                pygame.Rect(190, 272 + indice * 52, 370, 44),
                f"{titulo}: …",
                Accion.PRENDA,
                valor=prenda,
            )
            for indice, (titulo, prenda) in enumerate(prendas)
        )
        botones.extend(
            (
                Boton(
                    pygame.Rect(190, 428, 370, 44),
                    "Dorsales: ACTIVADOS",
                    Accion.NUMEROS,
                ),
                Boton(
                    pygame.Rect(190, 535, 370, 44),
                    "Volver",
                    Accion.VOLVER,
                ),
            )
        )

        return botones

    @staticmethod
    def _botones_de_editor() -> list[Boton]:
        """Botones del editor: equipo, jugador y ficha del seleccionado."""
        filas = (
            (218, Accion.EQUIPO_EDITOR),
            (258, Accion.CICLAR_JUGADOR),
            (298, Accion.EDITOR_NOMBRE),
            (338, Accion.CICLAR_DORSAL),
            (378, Accion.CICLAR_VELOCIDAD),
            (418, Accion.CICLAR_FUERZA),
            (458, Accion.CICLAR_ROL),
            (498, Accion.MOVER_POSICION),
        )
        botones = [
            Boton(pygame.Rect(190, y, 370, 36), "…", accion)
            for y, accion in filas
        ]
        botones.append(
            Boton(pygame.Rect(190, 535, 370, 44), "Volver", Accion.VOLVER)
        )

        return botones

    @staticmethod
    def _botones_de_tactica() -> list[Boton]:
        """Botones de tácticas: una formación por botón y volver."""
        formaciones = [
            Boton(
                pygame.Rect(190, 245 + indice * 64, 370, 48),
                nombre,
                Accion.FORMACION,
                valor=indice,
            )
            for indice, nombre in enumerate(NOMBRES_FORMACION)
        ]

        return formaciones + [
            Boton(pygame.Rect(190, 535, 370, 44), "Volver", Accion.VOLVER)
        ]

    @staticmethod
    def _botones_de_modos() -> list[Boton]:
        """Botones del selector de modos: uno por modo y volver."""
        modos = (
            ModoJuego.CAMPANA,
            ModoJuego.LIGA,
            ModoJuego.COPA,
            ModoJuego.CAMPEONES,
            ModoJuego.SUPERVIVENCIA,
            ModoJuego.ENTRENAMIENTO,
            ModoJuego.DOS_JUGADORES,
        )
        botones = [
            Boton(
                pygame.Rect(260, 218 + indice * 46, 480, 40),
                _ETIQUETAS_MODO[modo],
                _ACCION_DE_MODO[modo],
            )
            for indice, modo in enumerate(modos)
        ]
        botones.append(
            Boton(
                pygame.Rect(260, 554, 480, 42),
                "Volver",
                Accion.VOLVER,
            )
        )

        return botones

    @staticmethod
    def _botones_de_estadio() -> list[Boton]:
        """Botones del estadio: césped, momento, clima, diseño, gradas."""
        return [
            Boton(
                pygame.Rect(190, 220, 370, 44),
                "Césped: CLARO",
                Accion.CESPED,
            ),
            Boton(
                pygame.Rect(190, 272, 370, 44),
                "Momento: DÍA",
                Accion.MOMENTO,
            ),
            Boton(
                pygame.Rect(190, 324, 370, 44),
                "Clima: DESPEJADO",
                Accion.CLIMA,
            ),
            Boton(
                pygame.Rect(190, 376, 370, 44),
                "Diseño: CLÁSICO",
                Accion.DISENO,
            ),
            Boton(
                pygame.Rect(190, 428, 370, 44),
                "Gradas: CON AFICIONADOS",
                Accion.GRADAS,
            ),
            Boton(
                pygame.Rect(190, 535, 370, 44),
                "Volver",
                Accion.VOLVER,
            ),
        ]

    @staticmethod
    def _crear_panel(
        rect: pygame.Rect,
        borde: Color,
    ) -> pygame.Surface:
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            panel,
            (8, 15, 26, 250),
            panel.get_rect(),
            border_radius=18,
        )
        pygame.draw.rect(
            panel,
            (*borde, 150),
            panel.get_rect(),
            2,
            border_radius=18,
        )
        pygame.draw.rect(
            panel,
            (255, 255, 255, 26),
            panel.get_rect().inflate(-10, -10),
            1,
            border_radius=14,
        )
        return panel

    # --------------------------------------------------
    # Estado y navegación
    # --------------------------------------------------

    @property
    def botones_actuales(self) -> list[Boton]:
        """Botones de la pantalla visible."""
        return self.botones.get(self.pantalla, [])

    @property
    def boton_actual(self) -> Boton | None:
        """Botón seleccionado en la pantalla visible."""
        botones = self.botones_actuales

        if not botones:
            return None

        self.indice %= len(botones)
        return botones[self.indice]

    @property
    def escudo_seleccionado(self) -> tuple[Color, Color, FormaEscudo]:
        """Personalización actual del escudo del jugador."""
        return (self.escudo_color, self.escudo_color_borde, self.escudo_forma)

    @property
    def plantillas_seleccionadas(
        self,
    ) -> dict[Equipo, tuple[JugadorPlantilla, ...]]:
        """Fichas editadas, saneadas y listas para el partido."""
        return {
            equipo: normalizar_plantilla(
                self.plantillas_editables.get(equipo),
                equipo,
            )
            for equipo in Equipo
        }

    @property
    def estadio_seleccionado(self) -> Estadio:
        """Estadio elegido: césped, momento, gradas y diseño."""
        return self._estadio

    def adoptar_estadio(self, estadio: Estadio) -> None:
        """Reemplaza el estadio en uso y refresca sus etiquetas."""
        self._estadio = estadio
        self._actualizar_etiquetas_estadio()

    def consumir_accion(self) -> Accion | None:
        """Devuelve y borra la acción que debe ejecutar la aplicación."""
        accion = self._accion_pendiente
        self._accion_pendiente = None
        return accion

    def abrir_pausa(self) -> None:
        """Muestra el menú de pausa."""
        self._cambiar_pantalla(Pantalla.PAUSA)

    def abrir_menu_principal(self) -> None:
        """Vuelve al menú principal."""
        self._cambiar_pantalla(Pantalla.PRINCIPAL)

    def reanudar(self) -> None:
        """Cierra el menú y vuelve al partido."""
        self._cambiar_pantalla(Pantalla.PARTIDO)

    def _mostrar(self, pantalla: Pantalla) -> None:
        self.pantalla = pantalla
        self.indice = 0
        self._cursor_normal()
        self._salir_de_modos_editor()

    def _cambiar_pantalla(self, pantalla: Pantalla) -> None:
        """Salta a una pantalla descartando el historial de vuelta."""
        self._historial.clear()
        self._mostrar(pantalla)

    def _navegar(self, pantalla: Pantalla) -> None:
        """Entra a una pantalla apilando la actual para poder volver."""
        self._historial.append(self.pantalla)
        self._mostrar(pantalla)

    def _retroceder(self) -> None:
        """Vuelve a la pantalla anterior; sin historial, al principal."""
        anterior = (
            self._historial.pop() if self._historial else Pantalla.PRINCIPAL
        )
        self._mostrar(anterior)

    def procesar_evento(self, evento: pygame.event.Event) -> None:
        """Procesa ratón y teclado cuando no se está jugando."""
        if self.pantalla is Pantalla.PARTIDO:
            return

        if evento.type == pygame.MOUSEMOTION:
            sobre_boton = self._seguir_raton(evento.pos)
            self._cursor_mano(sobre_boton)
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if (
                self.pantalla is Pantalla.EDITOR
                and self._moviendo_posicion
                and self.rect_campo_editor.collidepoint(evento.pos)
            ):
                self._colocar_en_campo(evento.pos)
                return

            sobre_boton = self._seguir_raton(evento.pos)

            if sobre_boton:
                self._activar()
        elif evento.type == pygame.KEYDOWN:
            self.procesar_tecla(evento.key)

    def procesar_tecla(self, tecla: int) -> None:
        """Navega por el menú con el teclado."""
        if self.pantalla is Pantalla.PARTIDO:
            return

        if self._editando_nombre:
            self._teclear_nombre(tecla)
            return

        if self._moviendo_posicion:
            self._teclear_posicion(tecla)
            return

        if tecla == pygame.K_ESCAPE:
            self._atras()
            return

        botones = self.botones_actuales

        if not botones:
            return

        if tecla in (pygame.K_LEFT, pygame.K_a):
            self._ciclar_seleccion(-1)
        elif tecla in (pygame.K_RIGHT, pygame.K_d):
            self._ciclar_seleccion(1)
        elif tecla in (pygame.K_UP, pygame.K_w):
            self.indice = (self.indice - 1) % len(botones)
        elif tecla in (pygame.K_DOWN, pygame.K_s):
            self.indice = (self.indice + 1) % len(botones)
        elif tecla in (
            pygame.K_RETURN,
            pygame.K_KP_ENTER,
            pygame.K_SPACE,
        ):
            self._activar()

    # Acciones que aceptan ←/→ para ajustar su valor hacia atrás o
    # adelante; el resto de botones ignora las flechas laterales.
    _AJUSTABLES: frozenset[Accion] = frozenset(
        (
            Accion.CESPED,
            Accion.CICLAR_DORSAL,
            Accion.CICLAR_FUERZA,
            Accion.CICLAR_JUGADOR,
            Accion.CICLAR_ROL,
            Accion.CICLAR_VELOCIDAD,
            Accion.CLIMA,
            Accion.DISENO,
            Accion.MOMENTO,
            Accion.PRENDA,
        )
    )

    def _ciclar_seleccion(self, direccion: int) -> None:
        """Ajusta el botón elegido en la dirección indicada."""
        boton = self.boton_actual

        if boton is None or boton.accion not in self._AJUSTABLES:
            return

        self._ejecutar(boton.accion, boton, direccion)

    def _seguir_raton(self, posicion: tuple[int, int]) -> bool:
        """Selecciona el botón bajo el ratón y dice si hay alguno."""
        for indice, boton in enumerate(self.botones_actuales):
            if boton.rect.collidepoint(posicion):
                self.indice = indice
                return True

        return False

    def _activar(self) -> None:
        boton = self.boton_actual

        if boton is not None:
            self._ejecutar(boton.accion, boton)

    def _atras(self) -> None:
        """Acción de ESC según la pantalla actual."""
        if self.pantalla is Pantalla.PRINCIPAL:
            self._accion_pendiente = Accion.SALIR
        elif self.pantalla is Pantalla.PAUSA:
            self._cambiar_pantalla(Pantalla.PARTIDO)
        elif self.pantalla in (
            Pantalla.OPCIONES,
            Pantalla.AYUDA,
            Pantalla.ESCUDO,
            Pantalla.UNIFORME,
            Pantalla.EDITOR,
            Pantalla.TACTICA,
            Pantalla.MODOS,
            Pantalla.ESTADIO,
            Pantalla.PALMARES,
            Pantalla.SUSTITUCIONES,
        ):
            self._retroceder()

    def _ejecutar(
        self,
        accion: Accion,
        boton: Boton | None = None,
        direccion: int = 0,
    ) -> None:
        paso = 1 if direccion >= 0 else -1

        if (
            accion is Accion.ESCUDO
            and boton is not None
            and isinstance(boton.valor, int)
        ):
            indice = boton.valor % len(ESCUDO_PRESETS)
            _etiqueta, color, color_borde = ESCUDO_PRESETS[indice]
            self.escudo_color = color
            self.escudo_color_borde = color_borde
            return

        if (
            accion is Accion.FORMA_ESCUDO
            and boton is not None
            and isinstance(boton.valor, int)
        ):
            self.escudo_forma = FORMAS_ESCUDO[
                boton.valor % len(FORMAS_ESCUDO)
            ]
            return

        if (
            accion is Accion.FORMACION
            and boton is not None
            and isinstance(boton.valor, int)
        ):
            self._elegir_formacion(
                NOMBRES_FORMACION[boton.valor % len(NOMBRES_FORMACION)]
            )
            return

        if (
            accion is Accion.ELEGIR_SALE
            and boton is not None
            and isinstance(boton.valor, int)
        ):
            # Segundo toque sobre el mismo jugador: se desmarca.
            self._cambio_sale = (
                None if self._cambio_sale == boton.valor else boton.valor
            )
            return

        if (
            accion is Accion.ELEGIR_ENTRA
            and boton is not None
            and isinstance(boton.valor, int)
        ):
            self._cambio_entra = (
                None if self._cambio_entra == boton.valor else boton.valor
            )
            return

        if accion is Accion.HACER_CAMBIO:
            self._confirmar_sustitucion()
            return

        if (
            accion is Accion.PRENDA
            and boton is not None
            and isinstance(boton.valor, str)
        ):
            self._ciclar_color_prenda(boton.valor, paso)
            return

        if accion is Accion.JUGAR:
            self._navegar(Pantalla.MODOS)
        elif accion in _ACCION_DE_MODO.values():
            self.modo_seleccionado = ModoJuego(accion.value)
            self._cambiar_pantalla(Pantalla.PARTIDO)
            self._accion_pendiente = Accion.JUGAR
        elif accion is Accion.CONTINUAR:
            self._cambiar_pantalla(Pantalla.PARTIDO)
        elif accion is Accion.REINICIAR:
            self._cambiar_pantalla(Pantalla.PARTIDO)
            self._accion_pendiente = Accion.REINICIAR
        elif accion is Accion.CONFIGURACION:
            self._navegar(Pantalla.OPCIONES)
        elif accion is Accion.OPCIONES:
            self._navegar(Pantalla.OPCIONES)
        elif accion is Accion.AYUDA:
            self._navegar(Pantalla.AYUDA)
        elif accion is Accion.MENU_PRINCIPAL:
            # La pantalla ya cambió; la acción queda pendiente por si
            # quien consuma las acciones quiere reaccionar (p. ej. tests).
            self._cambiar_pantalla(Pantalla.PRINCIPAL)
            self._accion_pendiente = Accion.MENU_PRINCIPAL
        elif accion is Accion.SONIDO:
            self.sonido_activado = not self.sonido_activado
            self._actualizar_etiqueta_sonido()
        elif accion is Accion.UNIFORME:
            self._navegar(Pantalla.UNIFORME)
        elif accion is Accion.EQUIPO_UNIFORME:
            self._equipo_uniforme = equipo_rival(self._equipo_uniforme)
            self._actualizar_etiquetas_uniforme()
        elif accion is Accion.NUMEROS:
            self.numeros_activados = not self.numeros_activados
            self._actualizar_etiquetas_uniforme()
        elif accion is Accion.EDITOR:
            self._navegar(Pantalla.EDITOR)
        elif accion is Accion.TACTICA:
            self._navegar(Pantalla.TACTICA)
        elif accion is Accion.SUSTITUCIONES:
            self.abrir_sustituciones()
        elif accion is Accion.ESTADIO:
            self._navegar(Pantalla.ESTADIO)
        elif accion is Accion.PALMARES:
            self._navegar(Pantalla.PALMARES)
        elif accion is Accion.EQUIPO_EDITOR:
            self._equipo_editor = equipo_rival(self._equipo_editor)
            self._jugador_editor %= len(self._plantilla_editor())
        elif accion is Accion.CICLAR_JUGADOR:
            self._jugador_editor = (
                self._jugador_editor + paso
            ) % len(self._plantilla_editor())
        elif accion is Accion.EDITOR_NOMBRE:
            self._editando_nombre = not self._editando_nombre

            if self._editando_nombre:
                self._moviendo_posicion = False
        elif accion is Accion.CICLAR_DORSAL:
            ficha = self._ficha_editor()
            dorsal = (ficha.dorsal - 1 + paso) % 99 + 1
            self._guardar_ficha(ficha._replace(dorsal=dorsal))
        elif accion is Accion.CICLAR_VELOCIDAD:
            ficha = self._ficha_editor()
            indice = self._indice_de_preset(
                PRESETS_VELOCIDAD,
                ficha.factor_velocidad,
            )
            _nombre, factor = PRESETS_VELOCIDAD[
                (indice + paso) % len(PRESETS_VELOCIDAD)
            ]
            self._guardar_ficha(ficha._replace(factor_velocidad=factor))
        elif accion is Accion.CICLAR_FUERZA:
            ficha = self._ficha_editor()
            indice = self._indice_de_preset(
                PRESETS_FUERZA,
                ficha.factor_fuerza,
            )
            _nombre, factor = PRESETS_FUERZA[
                (indice + paso) % len(PRESETS_FUERZA)
            ]
            self._guardar_ficha(ficha._replace(factor_fuerza=factor))
        elif accion is Accion.CICLAR_ROL:
            ficha = self._ficha_editor()
            indice = ROLES.index(ficha.rol)
            self._guardar_ficha(
                ficha._replace(rol=ROLES[(indice + paso) % len(ROLES)])
            )
        elif accion is Accion.MOVER_POSICION:
            self._moviendo_posicion = not self._moviendo_posicion

            if self._moviendo_posicion:
                self._editando_nombre = False

        elif accion is Accion.CESPED:
            self._estadio = self._estadio._replace(
                cesped=siguiente_opcion(
                    CESPEDES,
                    self._estadio.cesped,
                    paso,
                )
            )
        elif accion is Accion.MOMENTO:
            self._estadio = self._estadio._replace(
                momento=siguiente_opcion(
                    MOMENTOS,
                    self._estadio.momento,
                    paso,
                )
            )
        elif accion is Accion.CLIMA:
            self._estadio = self._estadio._replace(
                clima=siguiente_opcion(
                    CLIMAS,
                    self._estadio.clima,
                    paso,
                )
            )
        elif accion is Accion.DISENO:
            self._estadio = self._estadio._replace(
                diseno=siguiente_opcion(
                    DISENOS,
                    self._estadio.diseno,
                    paso,
                )
            )
        elif accion is Accion.GRADAS:
            self._estadio = self._estadio._replace(
                gradas=not self._estadio.gradas
            )
        elif accion is Accion.VOLVER:
            self._retroceder()
        elif accion is Accion.SALIR:
            self._accion_pendiente = Accion.SALIR
        elif accion is Accion.ESCUDO:
            self._navegar(Pantalla.ESCUDO)

        self._actualizar_etiquetas_editor()
        self._actualizar_etiquetas_estadio()

    def _actualizar_etiqueta_sonido(self) -> None:
        estado = "ACTIVADO" if self.sonido_activado else "DESACTIVADO"

        for boton in self.botones[Pantalla.OPCIONES]:
            if boton.accion is Accion.SONIDO:
                boton.etiqueta = f"Sonido: {estado}"

    _TITULOS_PRENDA: dict[str, str] = {
        "camiseta": "Camiseta",
        "pantalon": "Pantalón",
        "medias": "Medias",
    }

    @staticmethod
    def _nombre_color_uniforme(color: Color) -> str:
        """Nombre del preset de uniforme que coincide con ``color``."""
        for nombre, preset in UNIFORME_PRESETS:
            if preset == color:
                return nombre

        return "Personalizado"

    def _ciclar_color_prenda(self, prenda: str, paso: int = 1) -> None:
        """Avanza al color siguiente de una prenda del equipo en pantalla.

        ``paso`` permite recorrer la lista hacia atrás con la flecha
        izquierda; un clic o ENTER equivalen a ``paso=1``.
        """
        uniforme = self.uniformes_seleccionados[self._equipo_uniforme]

        if not hasattr(uniforme, prenda):
            return

        posicion = next(
            (
                indice
                for indice, (_nombre, color) in enumerate(UNIFORME_PRESETS)
                if color == getattr(uniforme, prenda)
            ),
            -1,
        )

        if posicion < 0:
            # Color personalizado: se entra por el extremo adecuado.
            posicion = -1 if paso > 0 else 0

        _nombre, color = UNIFORME_PRESETS[
            (posicion + paso) % len(UNIFORME_PRESETS)
        ]
        self.uniformes_seleccionados[self._equipo_uniforme] = (
            uniforme._replace(**{prenda: color})
        )
        self._actualizar_etiquetas_uniforme()

    def _actualizar_etiquetas_uniforme(self) -> None:
        """Refresca las etiquetas de la pantalla de uniformes."""
        equipo = self._equipo_uniforme
        uniforme = self.uniformes_seleccionados[equipo]

        for boton in self.botones[Pantalla.UNIFORME]:
            if boton.accion is Accion.EQUIPO_UNIFORME:
                boton.etiqueta = f"Equipo: {equipo.value.upper()}"
            elif boton.accion is Accion.PRENDA:
                prenda = str(boton.valor)
                color = getattr(uniforme, prenda)
                titulo = self._TITULOS_PRENDA[prenda]
                boton.etiqueta = (
                    f"{titulo}: {self._nombre_color_uniforme(color)}"
                )
            elif boton.accion is Accion.NUMEROS:
                estado = (
                    "ACTIVADOS"
                    if self.numeros_activados
                    else "DESACTIVADOS"
                )
                boton.etiqueta = f"Dorsales: {estado}"

    # --------------------------------------------------
    # Tácticas
    # --------------------------------------------------

    def _elegir_formacion(self, nombre: str) -> None:
        """Aplica la formación elegida a las fichas de los dos equipos.

        Recoloca a los 22 jugadores (rol y posición) sin tocar nombres,
        dorsales ni atributos, y deja pendiente la acción para que la
        aplicación recree a los jugadores con la nueva disposición.
        """
        if nombre not in NOMBRES_FORMACION:
            nombre = NOMBRES_FORMACION[0]

        self.formacion_nombre = nombre

        for equipo in Equipo:
            plantilla = normalizar_plantilla(
                self.plantillas_editables.get(equipo),
                equipo,
            )
            self.plantillas_editables[equipo] = list(
                aplicar_formacion(plantilla, nombre)
            )

        self._accion_pendiente = Accion.FORMACION

    # --------------------------------------------------
    # Sustituciones
    # --------------------------------------------------

    def abrir_sustituciones(self) -> None:
        """Abre la pantalla de cambios, con las listas al día."""
        self._regenerar_sustituciones()
        self._navegar(Pantalla.SUSTITUCIONES)

    def reiniciar_sustituciones(self) -> None:
        """Devuelve el banquillo y el contador a su estado inicial.

        Se llama al empezar o reiniciar una partida: cada partido parte
        con los once titulares del editor y su cupo de cambios intacto.
        También deshace los cambios confirmados en el partido anterior
        (devolviendo a los titulares que salieron) y descarta cualquier
        sustitución pendiente sin aplicar.
        """
        for equipo, hueco, saliente in reversed(self._sustituciones_partido):
            plantilla = list(self._plantilla_visible(equipo))

            if 0 <= hueco < len(plantilla):
                plantilla[hueco] = saliente
                self.plantillas_editables[equipo] = plantilla

        self._sustituciones_partido.clear()
        self.suplentes_editables = suplentes_por_defecto_todos()
        self.cambios_usados = dict.fromkeys(Equipo, 0)
        self._cambio_sale = None
        self._cambio_entra = None
        self._sustitucion_pendiente = None
        self._regenerar_sustituciones()

    def consumir_sustitucion(self) -> tuple[Equipo, int, int, JugadorPlantilla] | None:
        """Devuelve y borra el cambio confirmado, listo para aplicarse."""
        sustitucion = self._sustitucion_pendiente
        self._sustitucion_pendiente = None
        return sustitucion

    def _cambios_restantes(self, equipo: Equipo) -> int:
        """Cambios que le quedan a un equipo en este partido."""
        return max(0, SUSTITUCIONES_MAXIMAS - self.cambios_usados[equipo])

    def _regenerar_sustituciones(self) -> None:
        """Reconstruye los botones de la pantalla con las fichas vivas.

        Los titulares en campo y el banquillo se leen de los datos: los
        jugadores que ya entraron desaparecen del banquillo solos.
        """
        equipo = Equipo.LOCAL
        en_campo = self._plantilla_visible(equipo)[:TITULARES_POR_EQUIPO]
        banquillo = self.suplentes_editables.get(equipo, ())
        restantes = self._cambios_restantes(equipo)

        filas_campo = [
            Boton(
                pygame.Rect(185, 200 + fila * 32, 300, 28),
                f"{ficha.dorsal:>2} · {ficha.nombre}",
                Accion.ELEGIR_SALE,
                valor=fila,
            )
            for fila, ficha in enumerate(en_campo)
        ]
        filas_banquillo = [
            Boton(
                pygame.Rect(520, 200 + fila * 32, 300, 28),
                f"{ficha.dorsal:>2} · {ficha.nombre}",
                Accion.ELEGIR_ENTRA,
                valor=fila,
            )
            for fila, ficha in enumerate(banquillo)
        ]

        self.botones[Pantalla.SUSTITUCIONES] = (
            filas_campo
            + filas_banquillo
            + [
                Boton(
                    pygame.Rect(185, 566, 300, 36),
                    f"Confirmar ({restantes} restantes)"
                    if restantes
                    else "Sin cambios restantes",
                    Accion.HACER_CAMBIO,
                ),
                Boton(
                    pygame.Rect(520, 566, 300, 36),
                    "Volver",
                    Accion.VOLVER,
                ),
            ]
        )
        # La lista se reconstruye: el índice activo se deja dentro
        # del rango aunque el banquillo encoja.
        botones = self.botones[Pantalla.SUSTITUCIONES]
        self.indice = min(max(self.indice, 0), max(0, len(botones) - 1))

    def _confirmar_sustitucion(self) -> None:
        """Intercambia al titular elegido con el suplente elegido.

        El que entra hereda el hueco táctico del que sale (rol y
        posición) conservando nombre, dorsal y atributos; el que sale
        pasa al banquillo. Deja la sustitución pendiente para que la
        aplicación recree al jugador en el campo.
        """
        equipo = Equipo.LOCAL

        if (
            self._cambio_sale is None
            or self._cambio_entra is None
            or self._cambios_restantes(equipo) == 0
        ):
            return

        hueco = self._cambio_sale
        indice_banquillo = self._cambio_entra
        plantilla = list(self._plantilla_visible(equipo))
        banquillo = list(self.suplentes_editables.get(equipo, ()))

        if hueco >= len(plantilla) or indice_banquillo >= len(banquillo):
            return

        saliente = plantilla[hueco]
        entrante = banquillo[indice_banquillo]._replace(
            rol=saliente.rol,
            x=saliente.x,
            y=saliente.y,
        )
        banquillo[indice_banquillo] = saliente
        plantilla[hueco] = entrante

        self.suplentes_editables[equipo] = tuple(banquillo)
        self.plantillas_editables[equipo] = plantilla
        self.cambios_usados[equipo] += 1
        self._sustituciones_partido.append((equipo, hueco, saliente))
        self._cambio_sale = None
        self._cambio_entra = None
        self._sustitucion_pendiente = (
            equipo,
            hueco,
            saliente.dorsal,
            entrante,
        )
        self._regenerar_sustituciones()

    # --------------------------------------------------
    # Editor de jugadores
    # --------------------------------------------------

    def _plantilla_visible(
        self,
        equipo: Equipo,
    ) -> Sequence[JugadorPlantilla]:
        """Fichas dibujables de un equipo, con la base si faltan."""
        plantilla = self.plantillas_editables.get(equipo)

        if not isinstance(plantilla, (list, tuple)) or not plantilla:
            return plantilla_por_defecto(equipo)

        return plantilla

    def _plantilla_editor(self) -> list[JugadorPlantilla]:
        """Plantilla editable del equipo en pantalla, siempre con 11 fichas."""
        plantilla = self.plantillas_editables.get(self._equipo_editor)
        total = len(plantilla_por_defecto(self._equipo_editor))

        if not isinstance(plantilla, list) or len(plantilla) != total:
            plantilla = list(
                normalizar_plantilla(plantilla, self._equipo_editor)
            )
            self.plantillas_editables[self._equipo_editor] = plantilla

        return plantilla

    def _ficha_editor(self) -> JugadorPlantilla:
        """Ficha del jugador que se está editando."""
        plantilla = self._plantilla_editor()
        self._jugador_editor %= len(plantilla)
        return plantilla[self._jugador_editor]

    def _guardar_ficha(self, ficha: JugadorPlantilla) -> None:
        """Reemplaza la ficha editada del jugador en pantalla."""
        plantilla = self._plantilla_editor()
        self._jugador_editor %= len(plantilla)
        plantilla[self._jugador_editor] = ficha

    def _salir_de_modos_editor(self) -> None:
        """Apaga los modos de texto y movimiento al cambiar de pantalla."""
        self._editando_nombre = False
        self._moviendo_posicion = False

    @staticmethod
    def _indice_de_preset(
        presets: tuple[tuple[str, float], ...],
        factor: float,
    ) -> int:
        """Índice del preset cuyo factor coincide con el de la ficha."""
        return next(
            (
                indice
                for indice, (_nombre, valor) in enumerate(presets)
                if valor == factor
            ),
            1,
        )

    def _teclear_nombre(self, tecla: int) -> None:
        """Modo texto: letras y números escriben, retroceso borra."""
        ficha = self._ficha_editor()
        nombre = ficha.nombre

        if tecla in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._editando_nombre = False
            limpio = nombre.strip()
            # Un nombre vacío conserva el actual en vez de vaciar la ficha.
            self._guardar_ficha(
                ficha._replace(nombre=limpio.capitalize() if limpio else ficha.nombre)
            )
        elif tecla == pygame.K_ESCAPE:
            # Cancela la edición sin tocar el nombre.
            self._editando_nombre = False
        elif tecla == pygame.K_BACKSPACE:
            if nombre:
                self._guardar_ficha(ficha._replace(nombre=nombre[:-1]))
        else:
            letra = self._caracter_de_tecla(tecla)

            if letra and len(nombre) < LARGO_NOMBRE:
                self._guardar_ficha(ficha._replace(nombre=nombre + letra))

        self._actualizar_etiquetas_editor()

    @staticmethod
    def _caracter_de_tecla(tecla: int) -> str:
        """Letra, dígito o espacio que representa una tecla, si aplica."""
        if pygame.K_a <= tecla <= pygame.K_z:
            return chr(ord("a") + tecla - pygame.K_a)

        if pygame.K_0 <= tecla <= pygame.K_9:
            return chr(ord("0") + tecla - pygame.K_0)

        if tecla == pygame.K_SPACE:
            return " "

        return ""

    def _teclear_posicion(self, tecla: int) -> None:
        """En modo movimiento: flechas/WASD mueven, ENTER o ESC confirman."""
        dx = dy = 0

        if tecla in (pygame.K_LEFT, pygame.K_a):
            dx = -1
        elif tecla in (pygame.K_RIGHT, pygame.K_d):
            dx = 1
        elif tecla in (pygame.K_UP, pygame.K_w):
            dy = -1
        elif tecla in (pygame.K_DOWN, pygame.K_s):
            dy = 1
        elif tecla in (
            pygame.K_RETURN,
            pygame.K_KP_ENTER,
            pygame.K_SPACE,
            pygame.K_ESCAPE,
        ):
            self._moviendo_posicion = False
        else:
            return

        if dx or dy:
            ficha = self._ficha_editor()
            # La x de la plantilla mira desde el arco propio: el visitante
            # se refleja, así que pantalla y plantilla van en sentidos
            # opuestos.
            signo = 1.0 if self._equipo_editor is Equipo.LOCAL else -1.0
            x = acotar(ficha.x + signo * dx * 0.02, 0.02, 0.95)
            y = acotar(ficha.y + dy * 0.02, 0.05, 0.95)
            self._guardar_ficha(ficha._replace(x=x, y=y))

        self._actualizar_etiquetas_editor()

    def _colocar_en_campo(self, posicion: tuple[int, int]) -> None:
        """Coloca al jugador en el punto clicado del mini campo."""
        campo = self.rect_campo_editor
        fx = acotar(
            (posicion[0] - campo.left) / campo.width,
            0.02,
            0.95,
        )
        fy = acotar(
            (posicion[1] - campo.top) / campo.height,
            0.05,
            0.95,
        )
        ficha = self._ficha_editor()

        if self._equipo_editor is Equipo.VISITANTE:
            fx = 1.0 - fx

        self._guardar_ficha(ficha._replace(x=fx, y=fy))
        self._actualizar_etiquetas_editor()

    def _actualizar_etiquetas_editor(self) -> None:
        """Refresca las etiquetas de la pantalla del editor."""
        equipo = self._equipo_editor
        ficha = self._ficha_editor()

        for boton in self.botones[Pantalla.EDITOR]:
            if boton.accion is Accion.EQUIPO_EDITOR:
                boton.etiqueta = f"Equipo: {equipo.value.upper()}"
            elif boton.accion is Accion.CICLAR_JUGADOR:
                boton.etiqueta = (
                    f"Jugador {self._jugador_editor + 1}/11: {ficha.nombre}"
                )
            elif boton.accion is Accion.EDITOR_NOMBRE:
                cursor = "|" if self._editando_nombre else ""
                boton.etiqueta = f"Nombre: {ficha.nombre}{cursor}"
            elif boton.accion is Accion.CICLAR_DORSAL:
                boton.etiqueta = f"Dorsal: {ficha.dorsal}"
            elif boton.accion is Accion.CICLAR_VELOCIDAD:
                boton.etiqueta = (
                    f"Velocidad: {nombre_velocidad(ficha.factor_velocidad)}"
                )
            elif boton.accion is Accion.CICLAR_FUERZA:
                boton.etiqueta = (
                    f"Fuerza: {nombre_fuerza(ficha.factor_fuerza)}"
                )
            elif boton.accion is Accion.CICLAR_ROL:
                boton.etiqueta = f"Rol: {ficha.rol.value.capitalize()}"
            elif boton.accion is Accion.MOVER_POSICION:
                boton.etiqueta = (
                    "Posición: ENTER para listo"
                    if self._moviendo_posicion
                    else "Posición: ajustar"
                )

    def _actualizar_etiquetas_estadio(self) -> None:
        """Refresca las etiquetas de la pantalla del estadio."""
        estadio = self._estadio

        for boton in self.botones[Pantalla.ESTADIO]:
            if boton.accion is Accion.CESPED:
                boton.etiqueta = f"Césped: {estadio.cesped.value.upper()}"
            elif boton.accion is Accion.MOMENTO:
                boton.etiqueta = f"Momento: {NOMBRES_MOMENTO[estadio.momento]}"
            elif boton.accion is Accion.CLIMA:
                boton.etiqueta = f"Clima: {estadio.clima.value.upper()}"
            elif boton.accion is Accion.DISENO:
                boton.etiqueta = f"Diseño: {NOMBRES_DISENO[estadio.diseno]}"
            elif boton.accion is Accion.GRADAS:
                estado = (
                    "CON AFICIONADOS"
                    if estadio.gradas
                    else "SIN AFICIONADOS"
                )
                boton.etiqueta = f"Gradas: {estado}"

    def _cursor_mano(self, activo: bool) -> None:
        """Cambia el cursor solo cuando su estado realmente cambia."""
        if activo == self._cursor_activo:
            return

        try:
            pygame.mouse.set_cursor(
                pygame.SYSTEM_CURSOR_HAND
                if activo
                else pygame.SYSTEM_CURSOR_ARROW
            )
            self._cursor_activo = activo
        except pygame.error:
            # Sin sistema de ventanas (SDL dummy) no hay cursores; se
            # recuerda el estado para no reintentar en cada movimiento.
            self._cursor_activo = activo

    def _cursor_normal(self) -> None:
        self._cursor_mano(False)

    # --------------------------------------------------
    # Dibujo
    # --------------------------------------------------

    def dibujar(self, pantalla: pygame.Surface) -> None:
        """Dibuja la pantalla de menú actual."""
        if self.pantalla is Pantalla.PRINCIPAL:
            self.fondo_principal.dibujar(pantalla)
            pantalla.blit(self._velo_suave, (0, 0))
            self._dibujar_botones_imagen(
                pantalla,
                Pantalla.PRINCIPAL,
                self.ACENTO_PRINCIPAL,
            )
            self._dibujar_pie(
                pantalla,
                "Flechas o W/S: elegir | ENTER: aceptar | ESC: salir",
            )
        elif self.pantalla is Pantalla.PAUSA:
            self.fondo_pausa.dibujar(pantalla)
            pantalla.blit(self._velo_suave, (0, 0))
            self._dibujar_botones_imagen(
                pantalla,
                Pantalla.PAUSA,
                self.ACENTO_PAUSA,
            )
            self._dibujar_pie(
                pantalla,
                "Flechas o W/S: elegir | ENTER: aceptar | "
                "ESC: continuar",
            )
        elif self.pantalla is Pantalla.OPCIONES:
            self.fondo_opciones.dibujar(pantalla)
            pantalla.blit(self._velo, (0, 0))
            pantalla.blit(
                self._panel_opciones,
                self.rect_panel_opciones.topleft,
            )
            self._dibujar_opciones(pantalla)
        elif self.pantalla is Pantalla.AYUDA:
            self.fondo_ayuda.dibujar(pantalla)
            pantalla.blit(self._velo, (0, 0))
            pantalla.blit(
                self._panel_ayuda,
                self.rect_panel_ayuda.topleft,
            )
            self._dibujar_ayuda(pantalla)
        elif self.pantalla is Pantalla.ESCUDO:
            self.fondo_opciones.dibujar(pantalla)
            pantalla.blit(self._velo, (0, 0))
            pantalla.blit(
                self._panel_escudo,
                self.rect_panel_escudo.topleft,
            )
            self._dibujar_escudo(pantalla)
        elif self.pantalla is Pantalla.MODOS:
            self.fondo_principal.dibujar(pantalla)
            pantalla.blit(self._velo, (0, 0))
            pantalla.blit(
                self._panel_modos,
                self.rect_panel_modos.topleft,
            )
            self._dibujar_modos(pantalla)
        elif self.pantalla is Pantalla.UNIFORME:
            self.fondo_opciones.dibujar(pantalla)
            pantalla.blit(self._velo, (0, 0))
            pantalla.blit(
                self._panel_uniforme,
                self.rect_panel_uniforme.topleft,
            )
            self._dibujar_uniformes(pantalla)
        elif self.pantalla is Pantalla.EDITOR:
            self.fondo_opciones.dibujar(pantalla)
            pantalla.blit(self._velo, (0, 0))
            pantalla.blit(
                self._panel_editor,
                self.rect_panel_editor.topleft,
            )
            self._dibujar_editor(pantalla)
        elif self.pantalla is Pantalla.TACTICA:
            self.fondo_opciones.dibujar(pantalla)
            pantalla.blit(self._velo, (0, 0))
            pantalla.blit(
                self._panel_tactica,
                self.rect_panel_tactica.topleft,
            )
            self._dibujar_tactica(pantalla)
        elif self.pantalla is Pantalla.ESTADIO:
            self.fondo_opciones.dibujar(pantalla)
            pantalla.blit(self._velo, (0, 0))
            pantalla.blit(
                self._panel_estadio,
                self.rect_panel_estadio.topleft,
            )
            self._dibujar_estadio(pantalla)
        elif self.pantalla is Pantalla.PALMARES:
            self.fondo_opciones.dibujar(pantalla)
            pantalla.blit(self._velo, (0, 0))
            pantalla.blit(
                self._panel_palmares,
                self.rect_panel_palmares.topleft,
            )
            self._dibujar_palmares(pantalla)
        elif self.pantalla is Pantalla.SUSTITUCIONES:
            self.fondo_opciones.dibujar(pantalla)
            pantalla.blit(self._velo, (0, 0))
            pantalla.blit(
                self._panel_sustituciones,
                self.rect_panel_sustituciones.topleft,
            )
            self._dibujar_sustituciones(pantalla)

    def _dibujar_botones_imagen(
        self,
        pantalla: pygame.Surface,
        pantalla_menu: Pantalla,
        acento: Color,
    ) -> None:
        """Resalta el botón seleccionado sobre la imagen de fondo."""
        for indice, boton in enumerate(self.botones[pantalla_menu]):
            if indice != self.indice:
                continue

            rect = boton.rect
            pygame.draw.rect(
                pantalla,
                acento,
                rect.inflate(10, 10),
                2,
                border_radius=22,
            )
            pygame.draw.rect(
                pantalla,
                BLANCO,
                rect.inflate(4, 4),
                1,
                border_radius=18,
            )
            self._dibujar_flechas(pantalla, rect, acento)

    @staticmethod
    def _dibujar_flechas(
        pantalla: pygame.Surface,
        rect: pygame.Rect,
        acento: Color,
    ) -> None:
        y = rect.centery
        pygame.draw.polygon(
            pantalla,
            acento,
            (
                (rect.left - 18, y),
                (rect.left - 6, y - 9),
                (rect.left - 6, y + 9),
            ),
        )
        pygame.draw.polygon(
            pantalla,
            acento,
            (
                (rect.right + 18, y),
                (rect.right + 6, y - 9),
                (rect.right + 6, y + 9),
            ),
        )

    def _dibujar_pie(self, pantalla: pygame.Surface, texto: str) -> None:
        pie = self._pie(texto)
        rect = pie.get_rect(midbottom=(ANCHO // 2, ALTO - 10))
        pantalla.blit(pie, rect.topleft)

    def _pie(self, texto: str) -> pygame.Surface:
        if texto not in self._pies:
            letras = self._texto(texto, self.fuente_pequena, BLANCO)
            fondo = pygame.Surface(
                (letras.get_width() + 28, letras.get_height() + 14),
                pygame.SRCALPHA,
            )
            pygame.draw.rect(
                fondo,
                (0, 0, 0, 150),
                fondo.get_rect(),
                border_radius=10,
            )
            fondo.blit(letras, letras.get_rect(center=fondo.get_rect().center))
            self._pies[texto] = fondo

        return self._pies[texto]

    def _dibujar_opciones(self, pantalla: pygame.Surface) -> None:
        self._centrar(
            pantalla,
            "OPCIONES",
            280,
            self.fuente_titulo,
            BLANCO,
        )
        self._centrar(
            pantalla,
            "Sonido, tácticas y apariencia",
            316,
            self.fuente_texto,
            self.TEXTO_SUAVE,
        )
        self._dibujar_botones_panel(
            pantalla,
            Pantalla.OPCIONES,
            self.ACENTO_PANEL,
        )
        self._centrar(
            pantalla,
            "Flechas: elegir | ENTER: aceptar | ESC: volver",
            630,
            self.fuente_pequena,
            (150, 170, 190),
        )

    def _dibujar_escudo(self, pantalla: pygame.Surface) -> None:
        """Dibuja el panel de personalización del escudo."""
        self._centrar(
            pantalla,
            "PERSONALIZAR ESCUDO",
            150,
            self.fuente_titulo,
            BLANCO,
        )
        self._centrar(
            pantalla,
            "Elige el color y la forma de tu escudo",
            192,
            self.fuente_texto,
            self.TEXTO_SUAVE,
        )
        self._centrar_en(
            pantalla,
            "Color",
            350,
            222,
            self.fuente_boton,
            self.ACENTO_PANEL,
        )
        self._centrar_en(
            pantalla,
            "Forma",
            700,
            222,
            self.fuente_boton,
            self.ACENTO_PANEL,
        )
        self._dibujar_botones_panel(
            pantalla,
            Pantalla.ESCUDO,
            self.ACENTO_PANEL,
        )
        self._dibujar_vista_previa(pantalla)
        self._centrar(
            pantalla,
            "Flechas o W/S: elegir | ENTER: aceptar | ESC: volver",
            598,
            self.fuente_pequena,
            (150, 170, 190),
        )

    def _dibujar_vista_previa(self, pantalla: pygame.Surface) -> None:
        """Muestra el escudo con la personalización elegida."""
        escudo = Escudo.crear_para_nivel(
            1,
            color=self.escudo_color,
            color_borde=self.escudo_color_borde,
            forma=self.escudo_forma,
        )
        escudo.dibujar(pantalla, (700, 455), escala=4.2)
        vista = self._texto(
            "Así se ve tu escudo",
            self.fuente_pequena,
            self.TEXTO_SUAVE,
        )
        pantalla.blit(
            vista,
            vista.get_rect(center=(700, 528)),
        )

    def _dibujar_modos(self, pantalla: pygame.Surface) -> None:
        """Dibuja el selector de modos de juego."""
        self._centrar(
            pantalla,
            "MODOS DE JUEGO",
            150,
            self.fuente_titulo,
            BLANCO,
        )
        self._centrar(
            pantalla,
            "Elige cómo quieres jugar",
            192,
            self.fuente_texto,
            self.TEXTO_SUAVE,
        )
        self._dibujar_botones_panel(
            pantalla,
            Pantalla.MODOS,
            self.ACENTO_PANEL,
        )
        boton = self.boton_actual
        descripcion = "Flechas: elegir | ENTER: aceptar | ESC: volver"

        if boton is not None and boton.accion in _ACCION_DE_MODO.values():
            descripcion = DESCRIPCIONES[ModoJuego(boton.accion.value)]

        self._centrar(
            pantalla,
            descripcion,
            606,
            self.fuente_pequena,
            (150, 170, 190),
        )

    def _dibujar_uniformes(self, pantalla: pygame.Surface) -> None:
        """Dibuja el panel de personalización de uniformes."""
        self._centrar(
            pantalla,
            "UNIFORMES",
            150,
            self.fuente_titulo,
            BLANCO,
        )
        self._centrar(
            pantalla,
            "Diseña la equipación de cada equipo",
            192,
            self.fuente_texto,
            self.TEXTO_SUAVE,
        )
        self._dibujar_botones_panel(
            pantalla,
            Pantalla.UNIFORME,
            self.ACENTO_PANEL,
        )
        self._dibujar_vista_previa_uniformes(pantalla)
        self._centrar(
            pantalla,
            "Flechas o W/S: elegir | ENTER: aceptar | ESC: volver",
            598,
            self.fuente_pequena,
            (150, 170, 190),
        )

    def _dibujar_vista_previa_uniformes(
        self,
        pantalla: pygame.Surface,
    ) -> None:
        """Muestra cómo viste cada equipo; agranda el que se edita."""
        numero = 9 if self.numeros_activados else None

        for equipo, centro in (
            (Equipo.LOCAL, (680, 330)),
            (Equipo.VISITANTE, (680, 480)),
        ):
            activo = equipo is self._equipo_uniforme
            color = self.ACENTO_PANEL if activo else self.TEXTO_SUAVE
            self._centrar_en(
                pantalla,
                equipo.value.upper(),
                centro[0],
                centro[1] - 62,
                self.fuente_pequena,
                color,
            )
            dibujar_jugador_uniforme(
                pantalla,
                centro,
                self.uniformes_seleccionados[equipo],
                escala=3.0,
                numero=numero,
            )

    def _dibujar_editor(self, pantalla: pygame.Surface) -> None:
        """Dibuja el panel del editor de jugadores."""
        self._centrar(
            pantalla,
            "EDITOR DE JUGADORES",
            150,
            self.fuente_titulo,
            BLANCO,
        )
        self._centrar(
            pantalla,
            "Nombres, dorsales, atributos y posiciones",
            192,
            self.fuente_texto,
            self.TEXTO_SUAVE,
        )
        self._dibujar_botones_panel(
            pantalla,
            Pantalla.EDITOR,
            self.ACENTO_PANEL,
        )
        self._dibujar_campo_editor(pantalla)
        self._centrar(
            pantalla,
            "←/→ ajusta la opción | ENTER: aceptar | ESC: volver",
            598,
            self.fuente_pequena,
            (150, 170, 190),
        )

    def _dibujar_campo_editor(self, pantalla: pygame.Surface) -> None:
        """Mini campo con la ubicación de los 22 jugadores.

        El equipo que se edita se dibuja con los colores de su camiseta
        y el jugador seleccionado lleva un aro y su dorsal; el rival se
        muestra atenuado como referencia.
        """
        campo = self.rect_campo_editor
        pygame.draw.rect(pantalla, (16, 44, 26), campo, border_radius=8)
        pygame.draw.rect(pantalla, (120, 140, 160), campo, 1, border_radius=8)
        pygame.draw.line(
            pantalla,
            (120, 140, 160),
            campo.midleft,
            campo.midright,
            1,
        )
        pygame.draw.circle(pantalla, (120, 140, 160), campo.center, 26, 1)

        for equipo in (Equipo.LOCAL, Equipo.VISITANTE):
            activo = equipo is self._equipo_editor
            color = (
                self.uniformes_seleccionados[equipo].camiseta
                if activo
                else (95, 105, 118)
            )

            for indice, ficha in enumerate(
                self._plantilla_visible(equipo)
            ):
                x, y = self._punto_en_campo(equipo, ficha, campo)
                radio = 7 if activo else 4
                pygame.draw.circle(pantalla, color, (x, y), radio)

                if activo and indice == self._jugador_editor:
                    pygame.draw.circle(
                        pantalla,
                        BLANCO,
                        (x, y),
                        radio + 3,
                        2,
                    )
                    dorsal = self._texto(
                        str(ficha.dorsal),
                        self.fuente_pequena,
                        BLANCO,
                    )
                    pantalla.blit(
                        dorsal,
                        dorsal.get_rect(midbottom=(x, y - radio - 4)),
                    )

    def _punto_en_campo(
        self,
        equipo: Equipo,
        ficha: JugadorPlantilla,
        campo: pygame.Rect,
    ) -> tuple[int, int]:
        """Coordenada en un mini campo de una ficha, ya reflejada."""
        fx = ficha.x if equipo is Equipo.LOCAL else 1.0 - ficha.x

        return (
            campo.left + round(fx * campo.width),
            campo.top + round(ficha.y * campo.height),
        )

    def _dibujar_tactica(self, pantalla: pygame.Surface) -> None:
        """Dibuja el panel de tácticas con la vista previa del campo."""
        self._centrar(
            pantalla,
            "TÁCTICAS",
            150,
            self.fuente_titulo,
            BLANCO,
        )
        self._centrar(
            pantalla,
            "Elige la formación de tu equipo",
            192,
            self.fuente_texto,
            self.TEXTO_SUAVE,
        )
        self._centrar_en(
            pantalla,
            "Formación",
            375,
            222,
            self.fuente_boton,
            self.ACENTO_PANEL,
        )
        self._centrar_en(
            pantalla,
            "Tu equipo",
            715,
            200,
            self.fuente_boton,
            self.ACENTO_PANEL,
        )
        self._dibujar_botones_panel(
            pantalla,
            Pantalla.TACTICA,
            self.ACENTO_PANEL,
        )
        self._dibujar_campo_tactica(pantalla)
        self._centrar(
            pantalla,
            "ENTER: elegir | ESC: volver",
            598,
            self.fuente_pequena,
            (150, 170, 190),
        )

    def _dibujar_campo_tactica(self, pantalla: pygame.Surface) -> None:
        """Mini campo con los 11 locales en la formación elegida."""
        campo = self.rect_campo_tactica
        pygame.draw.rect(pantalla, (16, 44, 26), campo, border_radius=8)
        pygame.draw.rect(pantalla, (120, 140, 160), campo, 1, border_radius=8)
        pygame.draw.line(
            pantalla,
            (120, 140, 160),
            campo.midleft,
            campo.midright,
            1,
        )
        pygame.draw.circle(pantalla, (120, 140, 160), campo.center, 26, 1)

        camiseta = self.uniformes_seleccionados[Equipo.LOCAL].camiseta

        for ficha in self._plantilla_visible(Equipo.LOCAL):
            x, y = self._punto_en_campo(Equipo.LOCAL, ficha, campo)
            color = (230, 230, 230) if ficha.rol is Rol.PORTERO else camiseta
            pygame.draw.circle(pantalla, color, (x, y), 7)
            pygame.draw.circle(pantalla, BLANCO, (x, y), 7, 1)

    def _dibujar_sustituciones(self, pantalla: pygame.Surface) -> None:
        """Panel de cambios: en campo a la izquierda, banquillo a la derecha."""
        self._centrar(
            pantalla,
            "CAMBIOS",
            110,
            self.fuente_titulo,
            BLANCO,
        )
        restantes = self._cambios_restantes(Equipo.LOCAL)
        subtitulo = (
            f"Elige al que sale y al que entra · {restantes} cambio(s) restante(s)"
            if restantes
            else "No quedan cambios disponibles en este partido"
        )
        self._centrar(
            pantalla,
            subtitulo,
            148,
            self.fuente_texto,
            self.TEXTO_SUAVE,
        )
        self._centrar_en(
            pantalla,
            "En campo",
            335,
            180,
            self.fuente_boton,
            self.ACENTO_PANEL,
        )
        self._centrar_en(
            pantalla,
            "Banquillo",
            670,
            180,
            self.fuente_boton,
            self.ACENTO_PANEL,
        )
        self._dibujar_botones_panel(
            pantalla,
            Pantalla.SUSTITUCIONES,
            self.ACENTO_PANEL,
        )

    def _marcar_seleccion_tactica(
        self,
        pantalla: pygame.Surface,
        boton: Boton,
    ) -> None:
        """Resalta la formación que está en uso."""
        if not (
            boton.accion is Accion.FORMACION and isinstance(boton.valor, int)
        ):
            return

        if NOMBRES_FORMACION[
            boton.valor % len(NOMBRES_FORMACION)
        ] == self.formacion_nombre:
            pygame.draw.rect(
                pantalla,
                BLANCO,
                boton.rect.inflate(8, 8),
                1,
                border_radius=12,
            )

    def _dibujar_estadio(self, pantalla: pygame.Surface) -> None:
        """Dibuja el panel de personalización del estadio."""
        self._centrar(
            pantalla,
            "ESTADIO",
            150,
            self.fuente_titulo,
            BLANCO,
        )
        self._centrar(
            pantalla,
            "Césped, momento, gradas y diseño de la cancha",
            192,
            self.fuente_texto,
            self.TEXTO_SUAVE,
        )
        self._dibujar_botones_panel(
            pantalla,
            Pantalla.ESTADIO,
            self.ACENTO_PANEL,
        )
        self._dibujar_vista_previa_estadio(pantalla)
        self._centrar(
            pantalla,
            "←/→ ajusta la opción | ENTER: aceptar | ESC: volver",
            598,
            self.fuente_pequena,
            (150, 170, 190),
        )

    def _dibujar_vista_previa_estadio(
        self,
        pantalla: pygame.Surface,
    ) -> None:
        """Miniatura del estadio con la personalización en vivo."""
        mini = self._mini_estadio()
        pantalla.blit(mini, mini.get_rect(center=(700, 330)))
        self._centrar_en(
            pantalla,
            "Así se ve tu cancha",
            700,
            448,
            self.fuente_pequena,
            self.TEXTO_SUAVE,
        )

    def _mini_estadio(self) -> pygame.Surface:
        """Miniatura cacheada: solo se repinta al cambiar el estadio."""
        if (
            self._mini_estadio_cache is not None
            and self._mini_estadio_cache[0] == self._estadio
        ):
            return self._mini_estadio_cache[1]

        mini = pygame.Surface((280, 200))
        self._dibujar_estadio_mini(mini)
        self._mini_estadio_cache = (self._estadio, mini)
        return mini

    def _dibujar_estadio_mini(self, mini: pygame.Surface) -> None:
        """Estadio en miniatura: entorno, aficionados y cancha."""
        estadio = self._estadio

        if estadio.gradas:
            mini.fill(color_tribuna(estadio.momento))
            dibujar_aficionados(mini, estadio.momento)
        else:
            mini.fill(color_entorno(estadio))

        campo = pygame.Rect(
            (0, 0),
            (mini.get_width() - 40, mini.get_height() - 40),
        )
        campo.center = mini.get_rect().center
        cancha = pygame.Surface(campo.size)
        dibujar_cesped(cancha, estadio)
        mini.blit(cancha, campo.topleft)
        pygame.draw.rect(mini, BLANCO, campo, 1)
        pygame.draw.line(mini, BLANCO, campo.midleft, campo.midright, 1)
        pygame.draw.circle(mini, BLANCO, campo.center, 22, 1)

    def _dibujar_palmares(self, pantalla: pygame.Surface) -> None:
        """Panel de la campaña: posiciones, resultados y trofeos."""
        self._centrar(
            pantalla,
            "PALMARÉS",
            150,
            self.fuente_titulo,
            BLANCO,
        )
        self._centrar(
            pantalla,
            "La campaña del club: puntos, resultados y trofeos",
            192,
            self.fuente_texto,
            self.TEXTO_SUAVE,
        )
        self._dibujar_botones_panel(
            pantalla,
            Pantalla.PALMARES,
            self.ACENTO_PANEL,
        )
        self._centrar_en(
            pantalla, "POSICIONES", 300, 228, self.fuente_texto, self.TEXTO_SUAVE
        )
        self._centrar_en(
            pantalla, "RESULTADOS", 575, 228, self.fuente_texto, self.TEXTO_SUAVE
        )
        self._centrar_en(
            pantalla, "TROFEOS", 790, 228, self.fuente_texto, self.TEXTO_SUAVE
        )
        self._dibujar_tabla_posiciones(pantalla)
        self._dibujar_historial(pantalla)
        self._dibujar_trofeos(pantalla)

    def _dibujar_tabla_posiciones(self, pantalla: pygame.Surface) -> None:
        """La tabla de la campaña: TU CLUB contra los 11 rivales."""
        y = 260

        for posicion, (clave, fila) in enumerate(
            self.tabla_posiciones.filas_de_campana(),
            start=1,
        ):
            if clave == CLAVE_LOCAL:
                nombre = "TU CLUB"
                color = BLANCO
            else:
                nombre = nivel_por_numero(int(clave)).rival
                color = self.TEXTO_SUAVE

            etiqueta = self._texto(
                f"{posicion}. {nombre}",
                self.fuente_pequena,
                color,
            )
            pantalla.blit(etiqueta, (140, y))
            cifras = self._texto(
                f"{fila.puntos} pts  {fila.g}-{fila.e}-{fila.p}"
                f"  {fila.gf}:{fila.gc}",
                self.fuente_pequena,
                color,
            )
            pantalla.blit(cifras, cifras.get_rect(midright=(465, y + 9)))
            y += 19

    def _dibujar_historial(self, pantalla: pygame.Surface) -> None:
        """Los últimos resultados de la campaña."""
        if not self.historial:
            vacio = self._texto(
                "Aún no hay partidos",
                self.fuente_pequena,
                self.TEXTO_SUAVE,
            )
            pantalla.blit(vacio, vacio.get_rect(center=(575, 262)))
            return

        y = 260

        for resultado in self.historial[:8]:
            linea = self._texto(
                f"N{resultado.nivel}  {resultado.goles_local}"
                f" - {resultado.goles_visitante}",
                self.fuente_pequena,
                self.TEXTO_SUAVE,
            )
            pantalla.blit(linea, linea.get_rect(center=(575, y + 9)))
            y += 22

    def _dibujar_trofeos(self, pantalla: pygame.Surface) -> None:
        """Los trofeos de la campaña: ganados en oro, el resto apagado."""
        y = 260

        for trofeo in TROFEOS:
            logrado = trofeo.id in self.trofeos
            nombre = self._texto(
                ("★ " if logrado else "☆ ") + trofeo.nombre,
                self.fuente_pequena,
                AMARILLO if logrado else (95, 105, 120),
            )
            pantalla.blit(nombre, nombre.get_rect(midleft=(715, y + 9)))
            y += 24

    def _dibujar_ayuda(self, pantalla: pygame.Surface) -> None:
        self._centrar(
            pantalla,
            "CÓMO JUGAR",
            105,
            self.fuente_titulo,
            BLANCO,
        )
        self._izquierda(
            pantalla,
            "CONTROLES",
            180,
            150,
            self.fuente_boton,
            self.ACENTO_PRINCIPAL,
        )
        controles = (
            "WASD / flechas: mover",
            "SHIFT: sprintar",
            "ESPACIO: chutar",
            "E: pasar",
            "ESC: pausa",
        )

        for fila, texto in enumerate(controles):
            self._izquierda(
                pantalla,
                texto,
                180,
                190 + fila * 33,
                self.fuente_texto,
                BLANCO,
            )

        self._izquierda(
            pantalla,
            "INDICADORES",
            520,
            150,
            self.fuente_boton,
            self.ACENTO_PRINCIPAL,
        )
        indicadores = (
            "Aro amarillo: balón",
            "Triángulo cian: tu jugador",
            "Aro cian: próximo pase",
            "Barra verde: energía",
            "Portero: atrapa y controla",
        )

        for fila, texto in enumerate(indicadores):
            self._izquierda(
                pantalla,
                texto,
                520,
                190 + fila * 33,
                self.fuente_texto,
                BLANCO,
            )

        pygame.draw.line(
            pantalla,
            (90, 110, 130),
            (180, 360),
            (820, 360),
            1,
        )
        self._centrar(
            pantalla,
            "Partido de 2 tiempos de 3 minutos.",
            386,
            self.fuente_texto,
            self.TEXTO_SUAVE,
        )
        self._centrar(
            pantalla,
            "Gana el equipo que marque más goles.",
            414,
            self.fuente_texto,
            self.TEXTO_SUAVE,
        )
        self._dibujar_botones_panel(
            pantalla,
            Pantalla.AYUDA,
            self.ACENTO_PRINCIPAL,
        )
        self._centrar(
            pantalla,
            "ENTER o ESC: volver",
            558,
            self.fuente_pequena,
            (150, 170, 190),
        )

    def _dibujar_botones_panel(
        self,
        pantalla: pygame.Surface,
        pantalla_menu: Pantalla,
        acento: Color,
    ) -> None:
        for indice, boton in enumerate(self.botones[pantalla_menu]):
            seleccionado = indice == self.indice
            fondo = (28, 45, 68) if seleccionado else (16, 26, 40)
            borde = acento if seleccionado else (70, 90, 115)
            color_texto = BLANCO if seleccionado else (205, 215, 225)

            pygame.draw.rect(
                pantalla,
                fondo,
                boton.rect,
                border_radius=12,
            )
            pygame.draw.rect(
                pantalla,
                borde,
                boton.rect,
                2,
                border_radius=12,
            )
            texto = self._texto(
                boton.etiqueta,
                self.fuente_boton,
                color_texto,
            )
            pantalla.blit(
                texto,
                texto.get_rect(center=boton.rect.center),
            )

            if pantalla_menu is Pantalla.ESCUDO:
                self._marcar_seleccion_escudo(pantalla, boton)

            if pantalla_menu is Pantalla.TACTICA:
                self._marcar_seleccion_tactica(pantalla, boton)

            if pantalla_menu is Pantalla.SUSTITUCIONES:
                self._marcar_seleccion_sustitucion(pantalla, boton)

            if boton.accion is Accion.SONIDO:
                self._dibujar_interruptor(pantalla, boton.rect)

    def _marcar_seleccion_sustitucion(
        self,
        pantalla: pygame.Surface,
        boton: Boton,
    ) -> None:
        """Resalta el que sale, el que entra y el botón listo para confirmar."""
        pareja_completa = (
            self._cambio_sale is not None and self._cambio_entra is not None
        )
        puede_confirmar = (
            pareja_completa and self._cambios_restantes(Equipo.LOCAL) > 0
        )
        marcado = (
            (boton.accion is Accion.ELEGIR_SALE and boton.valor == self._cambio_sale)
            or (
                boton.accion is Accion.ELEGIR_ENTRA
                and boton.valor == self._cambio_entra
            )
            or (boton.accion is Accion.HACER_CAMBIO and puede_confirmar)
        )

        if marcado:
            pygame.draw.rect(
                pantalla,
                BLANCO,
                boton.rect.inflate(8, 8),
                1,
                border_radius=12,
            )

    def _marcar_seleccion_escudo(
        self,
        pantalla: pygame.Surface,
        boton: Boton,
    ) -> None:
        """Muestra la muestra de color y señala la opción elegida."""
        if boton.accion is Accion.ESCUDO and isinstance(boton.valor, int):
            indice = boton.valor % len(ESCUDO_PRESETS)
            _etiqueta, color, borde = ESCUDO_PRESETS[indice]
            centro = (boton.rect.left + 24, boton.rect.centery)
            pygame.draw.circle(pantalla, color, centro, 9)
            pygame.draw.circle(pantalla, borde, centro, 9, 2)
            elegido = next(
                (
                    posicion
                    for posicion, (_n, c, b) in enumerate(ESCUDO_PRESETS)
                    if c == self.escudo_color and b == self.escudo_color_borde
                ),
                None,
            )

            if indice == elegido:
                pygame.draw.rect(
                    pantalla,
                    BLANCO,
                    boton.rect.inflate(8, 8),
                    1,
                    border_radius=12,
                )
        elif (
            boton.accion is Accion.FORMA_ESCUDO
            and isinstance(boton.valor, int)
            and FORMAS_ESCUDO[boton.valor % len(FORMAS_ESCUDO)]
            is self.escudo_forma
        ):
            pygame.draw.rect(
                pantalla,
                BLANCO,
                boton.rect.inflate(8, 8),
                1,
                border_radius=12,
            )

    def _dibujar_interruptor(
        self,
        pantalla: pygame.Surface,
        rect: pygame.Rect,
    ) -> None:
        pil = pygame.Rect(0, 0, 46, 22)
        pil.midright = (rect.right - 16, rect.centery)
        color = (60, 200, 110) if self.sonido_activado else (95, 100, 110)
        pygame.draw.rect(pantalla, color, pil, border_radius=11)

        if self.sonido_activado:
            centro = (pil.right - 11, pil.centery)
        else:
            centro = (pil.left + 11, pil.centery)

        pygame.draw.circle(pantalla, BLANCO, centro, 8)

    def _centrar(
        self,
        pantalla: pygame.Surface,
        texto: str,
        y: int,
        fuente: pygame.font.Font,
        color: Color,
    ) -> None:
        superficie = self._texto(texto, fuente, color)
        pantalla.blit(
            superficie,
            superficie.get_rect(center=(ANCHO // 2, y)),
        )

    def _centrar_en(
        self,
        pantalla: pygame.Surface,
        texto: str,
        x: int,
        y: int,
        fuente: pygame.font.Font,
        color: Color,
    ) -> None:
        superficie = self._texto(texto, fuente, color)
        pantalla.blit(superficie, superficie.get_rect(center=(x, y)))

    def _izquierda(
        self,
        pantalla: pygame.Surface,
        texto: str,
        x: int,
        y: int,
        fuente: pygame.font.Font,
        color: Color,
    ) -> None:
        pantalla.blit(self._texto(texto, fuente, color), (x, y))

    def _texto(
        self,
        texto: str,
        fuente: pygame.font.Font,
        color: Color,
    ) -> pygame.Surface:
        clave = (texto, id(fuente), color)
        superficie = self._cache_textos.get(clave)

        if superficie is None:
            superficie = fuente.render(texto, True, color)
            self._cache_textos[clave] = superficie

        return superficie
