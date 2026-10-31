"""Pantallas de menú, fondos ilustrados y botones clicables."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from enum import StrEnum
from pathlib import Path

import pygame

from .configuracion import (
    ALTO,
    ANCHO,
    BLANCO,
    NEGRO,
    NOMBRES_FORMACION,
    Color,
    Equipo,
    Rol,
)
from .escudos import ESCUDO_PRESETS, FORMAS_ESCUDO, Escudo, FormaEscudo
from .plantilla import (
    LARGO_NOMBRE,
    PRESETS_FUERZA,
    PRESETS_VELOCIDAD,
    ROLES,
    JugadorPlantilla,
    aplicar_formacion,
    nombre_fuerza,
    nombre_velocidad,
    plantillas_por_defecto,
)
from .uniformes import (
    UNIFORMES_POR_DEFECTO,
    UNIFORME_PRESETS,
    Uniforme,
    dibujar_jugador_uniforme,
)
from .utilidades import acotar, equipo_rival


def _directorio_imagenes() -> Path:
    """Ubica las imágenes en el código fuente y dentro del ejecutable."""
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", None)

        if base is None:
            base = Path(sys.executable).resolve().parent

        return Path(base) / "imagenes"

    return Path(__file__).resolve().parent.parent / "imagenes"


DIRECTORIO_IMAGENES = _directorio_imagenes()


class Pantalla(StrEnum):
    """Pantallas que puede mostrar la aplicación."""

    PRINCIPAL = "principal"
    OPCIONES = "opciones"
    AYUDA = "ayuda"
    PARTIDO = "partido"
    PAUSA = "pausa"
    ESCUDO = "escudo"
    UNIFORME = "uniforme"
    EDITOR = "editor"
    TACTICA = "tactica"


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
        original = pygame.image.load(ruta).convert()
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
                ),
            ),
            Pantalla.OPCIONES: [
                Boton(
                    pygame.Rect(260, 334, 480, 42),
                    "Sonido: ACTIVADO",
                    Accion.SONIDO,
                ),
                Boton(
                    pygame.Rect(260, 378, 480, 42),
                    "Tácticas",
                    Accion.TACTICA,
                ),
                Boton(
                    pygame.Rect(260, 422, 480, 42),
                    "Uniformes",
                    Accion.UNIFORME,
                ),
                Boton(
                    pygame.Rect(260, 466, 480, 42),
                    "Personalizar escudo",
                    Accion.ESCUDO,
                ),
                Boton(
                    pygame.Rect(260, 510, 480, 42),
                    "Editor de jugadores",
                    Accion.EDITOR,
                ),
                Boton(
                    pygame.Rect(260, 554, 480, 42),
                    "Volver",
                    Accion.VOLVER,
                ),
            ],
            Pantalla.ESCUDO: self._botones_de_escudo(),
            Pantalla.UNIFORME: self._botones_de_uniforme(),
            Pantalla.EDITOR: self._botones_de_editor(),
            Pantalla.TACTICA: self._botones_de_tactica(),
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
        """Fichas editadas, listas para aplicarse al partido."""
        return {
            equipo: tuple(fichas)
            for equipo, fichas in self.plantillas_editables.items()
        }

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
            Accion.CICLAR_DORSAL,
            Accion.CICLAR_FUERZA,
            Accion.CICLAR_JUGADOR,
            Accion.CICLAR_ROL,
            Accion.CICLAR_VELOCIDAD,
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
            and boton.valor is not None
        ):
            indice = int(boton.valor)
            _etiqueta, color, color_borde = ESCUDO_PRESETS[indice]
            self.escudo_color = color
            self.escudo_color_borde = color_borde
            return

        if (
            accion is Accion.FORMA_ESCUDO
            and boton is not None
            and boton.valor is not None
        ):
            self.escudo_forma = FORMAS_ESCUDO[int(boton.valor)]
            return

        if (
            accion is Accion.FORMACION
            and boton is not None
            and boton.valor is not None
        ):
            self._elegir_formacion(NOMBRES_FORMACION[int(boton.valor)])
            return

        if (
            accion is Accion.PRENDA
            and boton is not None
            and isinstance(boton.valor, str)
        ):
            self._ciclar_color_prenda(boton.valor)
            return

        if accion is Accion.JUGAR:
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
        elif accion is Accion.EQUIPO_EDITOR:
            self._equipo_editor = equipo_rival(self._equipo_editor)
            self._jugador_editor %= len(
                self.plantillas_editables[self._equipo_editor]
            )
        elif accion is Accion.CICLAR_JUGADOR:
            self._jugador_editor = (
                self._jugador_editor + paso
            ) % len(self.plantillas_editables[self._equipo_editor])
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

        elif accion is Accion.VOLVER:
            self._retroceder()
        elif accion is Accion.SALIR:
            self._accion_pendiente = Accion.SALIR
        elif accion is Accion.ESCUDO:
            self._navegar(Pantalla.ESCUDO)

        self._actualizar_etiquetas_editor()

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

    def _ciclar_color_prenda(self, prenda: str) -> None:
        """Avanza al color siguiente de una prenda del equipo en pantalla."""
        uniforme = self.uniformes_seleccionados[self._equipo_uniforme]
        posicion = next(
            (
                indice
                for indice, (_nombre, color) in enumerate(UNIFORME_PRESETS)
                if color == getattr(uniforme, prenda)
            ),
            -1,
        )
        _nombre, color = UNIFORME_PRESETS[
            (posicion + 1) % len(UNIFORME_PRESETS)
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
        self.formacion_nombre = nombre

        for equipo in Equipo:
            self.plantillas_editables[equipo] = list(
                aplicar_formacion(
                    tuple(self.plantillas_editables[equipo]),
                    nombre,
                )
            )

        self._accion_pendiente = Accion.FORMACION

    # --------------------------------------------------
    # Editor de jugadores
    # --------------------------------------------------

    def _ficha_editor(self) -> JugadorPlantilla:
        """Ficha del jugador que se está editando."""
        return self.plantillas_editables[self._equipo_editor][
            self._jugador_editor
        ]

    def _guardar_ficha(self, ficha: JugadorPlantilla) -> None:
        """Reemplaza la ficha editada del jugador en pantalla."""
        plantilla = self.plantillas_editables[self._equipo_editor]
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
            self._guardar_ficha(
                ficha._replace(nombre=nombre.strip().capitalize())
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
        """Letra o dígito que representa una tecla, si aplica."""
        if pygame.K_a <= tecla <= pygame.K_z:
            return chr(ord("a") + tecla - pygame.K_a)

        if pygame.K_0 <= tecla <= pygame.K_9:
            return chr(ord("0") + tecla - pygame.K_0)

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
        plantilla = self.plantillas_editables[equipo]
        ficha = plantilla[self._jugador_editor % len(plantilla)]

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

    def _cursor_mano(self, activo: bool) -> None:
        try:
            pygame.mouse.set_cursor(
                pygame.SYSTEM_CURSOR_HAND
                if activo
                else pygame.SYSTEM_CURSOR_ARROW
            )
        except pygame.error:
            pass

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
            "El cambio de sonido se aplica al instante.",
            610,
            self.fuente_pequena,
            self.TEXTO_SUAVE,
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
                self.plantillas_editables[equipo]
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

        for ficha in self.plantillas_editables[Equipo.LOCAL]:
            x, y = self._punto_en_campo(Equipo.LOCAL, ficha, campo)
            color = (230, 230, 230) if ficha.rol is Rol.PORTERO else camiseta
            pygame.draw.circle(pantalla, color, (x, y), 7)
            pygame.draw.circle(pantalla, BLANCO, (x, y), 7, 1)

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

        if NOMBRES_FORMACION[boton.valor] == self.formacion_nombre:
            pygame.draw.rect(
                pantalla,
                BLANCO,
                boton.rect.inflate(8, 8),
                1,
                border_radius=12,
            )

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

            if boton.accion is Accion.SONIDO:
                self._dibujar_interruptor(pantalla, boton.rect)

    def _marcar_seleccion_escudo(
        self,
        pantalla: pygame.Surface,
        boton: Boton,
    ) -> None:
        """Muestra la muestra de color y señala la opción elegida."""
        if boton.accion is Accion.ESCUDO and isinstance(boton.valor, int):
            _etiqueta, color, borde = ESCUDO_PRESETS[boton.valor]
            centro = (boton.rect.left + 24, boton.rect.centery)
            pygame.draw.circle(pantalla, color, centro, 9)
            pygame.draw.circle(pantalla, borde, centro, 9, 2)

            if color == self.escudo_color:
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
            and FORMAS_ESCUDO[boton.valor] is self.escudo_forma
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
