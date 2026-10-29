"""Pantallas de menú, fondos ilustrados y botones clicables."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from enum import StrEnum
from pathlib import Path

import pygame

from .configuracion import ALTO, ANCHO, BLANCO, NEGRO, Color
from .escudos import ESCUDO_PRESETS, FORMAS_ESCUDO, Escudo, FormaEscudo


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
                    pygame.Rect(260, 366, 480, 58),
                    "Sonido: ACTIVADO",
                    Accion.SONIDO,
                ),
                Boton(
                    pygame.Rect(260, 448, 480, 58),
                    "Volver",
                    Accion.VOLVER,
                ),
                Boton(
                    pygame.Rect(260, 530, 480, 58),
                    "Personalizar escudo",
                    Accion.ESCUDO,
                ),
            ],
            Pantalla.ESCUDO: self._botones_de_escudo(),
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
        self._volver_a = Pantalla.PRINCIPAL
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

    def _cambiar_pantalla(self, pantalla: Pantalla) -> None:
        self.pantalla = pantalla
        self.indice = 0
        self._cursor_normal()

    def procesar_evento(self, evento: pygame.event.Event) -> None:
        """Procesa ratón y teclado cuando no se está jugando."""
        if self.pantalla is Pantalla.PARTIDO:
            return

        if evento.type == pygame.MOUSEMOTION:
            sobre_boton = self._seguir_raton(evento.pos)
            self._cursor_mano(sobre_boton)
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            sobre_boton = self._seguir_raton(evento.pos)

            if sobre_boton:
                self._activar()
        elif evento.type == pygame.KEYDOWN:
            self.procesar_tecla(evento.key)

    def procesar_tecla(self, tecla: int) -> None:
        """Navega por el menú con el teclado."""
        if self.pantalla is Pantalla.PARTIDO:
            return

        if tecla == pygame.K_ESCAPE:
            self._atras()
            return

        botones = self.botones_actuales

        if not botones:
            return

        if tecla in (pygame.K_UP, pygame.K_w):
            self.indice = (self.indice - 1) % len(botones)
        elif tecla in (pygame.K_DOWN, pygame.K_s):
            self.indice = (self.indice + 1) % len(botones)
        elif tecla in (
            pygame.K_RETURN,
            pygame.K_KP_ENTER,
            pygame.K_SPACE,
        ):
            self._activar()

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
        ):
            self._cambiar_pantalla(self._volver_a)

    def _ejecutar(self, accion: Accion, boton: Boton | None = None) -> None:
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

        if accion is Accion.JUGAR:
            self._cambiar_pantalla(Pantalla.PARTIDO)
            self._accion_pendiente = Accion.JUGAR
        elif accion is Accion.CONTINUAR:
            self._cambiar_pantalla(Pantalla.PARTIDO)
        elif accion is Accion.REINICIAR:
            self._cambiar_pantalla(Pantalla.PARTIDO)
            self._accion_pendiente = Accion.REINICIAR
        elif accion is Accion.CONFIGURACION:
            self._volver_a = Pantalla.PAUSA
            self._cambiar_pantalla(Pantalla.OPCIONES)
        elif accion is Accion.OPCIONES:
            self._volver_a = Pantalla.PRINCIPAL
            self._cambiar_pantalla(Pantalla.OPCIONES)
        elif accion is Accion.AYUDA:
            self._volver_a = Pantalla.PRINCIPAL
            self._cambiar_pantalla(Pantalla.AYUDA)
        elif accion is Accion.MENU_PRINCIPAL:
            self._cambiar_pantalla(Pantalla.PRINCIPAL)
            self._accion_pendiente = Accion.MENU_PRINCIPAL
        elif accion is Accion.SONIDO:
            self.sonido_activado = not self.sonido_activado
            self._actualizar_etiqueta_sonido()
        elif accion is Accion.VOLVER:
            self._cambiar_pantalla(self._volver_a)
        elif accion is Accion.SALIR:
            self._accion_pendiente = Accion.SALIR
        elif accion is Accion.ESCUDO:
            self._volver_a = Pantalla.OPCIONES
            self._cambiar_pantalla(Pantalla.ESCUDO)

    def _actualizar_etiqueta_sonido(self) -> None:
        estado = "ACTIVADO" if self.sonido_activado else "DESACTIVADO"

        for boton in self.botones[Pantalla.OPCIONES]:
            if boton.accion is Accion.SONIDO:
                boton.etiqueta = f"Sonido: {estado}"

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
            284,
            self.fuente_titulo,
            BLANCO,
        )
        self._centrar(
            pantalla,
            "Sonido y preferencias",
            324,
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
            538,
            self.fuente_pequena,
            self.TEXTO_SUAVE,
        )
        self._centrar(
            pantalla,
            "Flechas: elegir | ENTER: aceptar | ESC: volver",
            584,
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
