"""Todo el dibujo de la partida."""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

import pygame

from .configuracion import (
    ALTO,
    AMARILLO,
    ANCHO,
    ANCHO_POSTE,
    AREA_PENALTI_ALTO,
    AREA_PENALTI_ANCHO,
    BLANCO,
    CAMPO_RECT,
    CIAN,
    ENERGIA_MAXIMA,
    ESTADOS_ESPERA,
    Estado,
    MENSAJE_ENTRETIEMPO,
    MENSAJE_FINAL,
    MENSAJE_CORNER,
    MENSAJE_GOL,
    MENSAJE_REPETICION,
    NEGRO,
    PORTERIA_ALTO,
    PORTERIA_SUPERIOR,
    RADIO_CIRCULO_CENTRAL,
    ROJO_ENERGIA,
    SUAVIZADO_CAMARA,
    SUAVIZADO_ZOOM,
    TEXTO_AYUDA,
    TEXTO_CONTINUAR,
    TEXTO_ENTRETIEMPO,
    TEXTO_FINAL,
    TEXTO_SALTAR_REPETICION,
    VERDE_ENERGIA,
    ZOOM_CAMARA,
    ZOOM_CAMARA_AREA,
    ZOOM_CAMARA_VELOCIDAD,
    Color,
    Equipo,
)

from .entidades import Jugador
from .escudos import (
    Escudo,
    cargar_escudo,
    limpiar_cache as limpiar_cache_escudos,
)
from .estadios import (
    ESTADIO_POR_DEFECTO,
    Clima,
    Estadio,
    color_entorno,
    color_tribuna,
    dibujar_aficionados,
    dibujar_cesped,
)
from .modos import ModoJuego
from .niveles import nivel_por_numero
from .utilidades import acotar

if TYPE_CHECKING:
    from .juego import Juego


class Vista:
    """Todo el dibujo de la partida.

    Pre-renderiza en el arranque lo que nunca cambia (campo, HUD,
    mensajes de gol) y guarda en caché lo que cambia poco (marcador).
    """

    POSICION_MARCADOR = (ANCHO // 2, 46)
    POSICION_TIEMPO = (20, 18)
    POSICION_ENERGIA = (20, 56)
    ANCHO_ENERGIA = 170
    ALTO_ENERGIA = 12
    ALTO_ESCUDO_MARCADOR = 34
    POSICION_MENSAJE_GOL = (ANCHO // 2, ALTO // 2)
    POSICION_CONTINUAR = (ANCHO // 2, ALTO // 2 + 50)
    POSICION_REPETICION = (ANCHO // 2, 108)

    def __init__(self, pantalla: pygame.Surface) -> None:
        self.pantalla = pantalla

        # Las cachés de sprites e imágenes se convierten al formato de la
        # pantalla; al crear una vista nueva (por ejemplo tras reiniciar
        # pygame) hay que regenerarlas con el contexto actual.
        Jugador.limpiar_cache()
        limpiar_cache_escudos()

        self.fuente_marcador = pygame.font.SysFont("Arial", 30, bold=True)
        self.fuente_mensaje = pygame.font.SysFont("Arial", 48, bold=True)
        self.fuente_instrucciones = pygame.font.SysFont("Arial", 20)
        self.fuente_hud = pygame.font.SysFont("Arial", 16)
        self.fuente_tiempo = pygame.font.SysFont("Arial", 20, bold=True)

        # Elementos estáticos: se crean una vez y solo se copian.
        self._estadio_fondo: Estadio = ESTADIO_POR_DEFECTO
        self.fondo = self._crear_fondo(self._estadio_fondo)
        self.hud = [
            self.fuente_hud.render(linea, True, BLANCO)
            for linea in TEXTO_AYUDA
        ]
        self.mensajes_gol = {
            equipo: self.fuente_mensaje.render(texto, True, AMARILLO)
            for equipo, texto in MENSAJE_GOL.items()
        }
        self.mensajes_estado = {
            Estado.ENTRETIEMPO: self.fuente_mensaje.render(
                MENSAJE_ENTRETIEMPO,
                True,
                AMARILLO,
            ),
            Estado.FINAL: self.fuente_mensaje.render(
                MENSAJE_FINAL,
                True,
                AMARILLO,
            ),
        }
        self.textos_estado = {
            Estado.ENTRETIEMPO: self.fuente_instrucciones.render(
                TEXTO_ENTRETIEMPO,
                True,
                BLANCO,
            ),
            Estado.FINAL: self.fuente_instrucciones.render(
                TEXTO_FINAL,
                True,
                BLANCO,
            ),
        }
        self.paneles_estado = {
            estado: self._crear_panel(
                self.mensajes_estado[estado],
                self.textos_estado[estado],
            )
            for estado in ESTADOS_ESPERA
        }
        self.superficie_continuar = self.fuente_instrucciones.render(
            TEXTO_CONTINUAR,
            True,
            BLANCO,
        )
        # Cartela y aviso de la repetición de gol.
        self.superficie_repeticion = self._crear_superficie_con_fondo(
            MENSAJE_REPETICION,
            self.fuente_tiempo,
            CIAN,
            padding_x=16,
            padding_y=8,
            radio=8,
        )
        self.superficie_salto_repeticion = self.fuente_instrucciones.render(
            TEXTO_SALTAR_REPETICION,
            True,
            BLANCO,
        )
        # Cartela del saque de esquina.
        self.superficie_corner = self._crear_superficie_con_fondo(
            MENSAJE_CORNER,
            self.fuente_tiempo,
            AMARILLO,
            padding_x=16,
            padding_y=8,
            radio=8,
        )
        # Comentarios del narrador, cacheados por texto.
        self._comentarios_cache: dict[str, pygame.Surface] = {}

        # Cámara dinámica: el mundo se pinta en un lienzo propio para
        # poder acercarlo y seguir al balón antes de presentarlo.
        self._lienzo = pygame.Surface((ANCHO, ALTO)).convert()
        self._zoom = 1.0
        self._centro_camara = pygame.Vector2(ANCHO / 2, ALTO / 2)
        # Confeti de la grada: puntos fijos fuera de la cancha.
        self._confeti = self._crear_confeti()

        # Caché del marcador: (goles dibujados, superficie).
        self._marcador_cache: tuple[
            tuple[int, int], pygame.Surface
        ] | None = None
        # Caché del reloj: ((mitad, segundos), superficie).
        self._tiempo_cache: tuple[
            tuple[int, int], pygame.Surface
        ] | None = None
        # Caché de escudos rivales escalados, uno por nivel.
        self._escudos_rivales: dict[int, pygame.Surface] = {}

    # --------------------------------------------------
    # Dibujo general
    # --------------------------------------------------

    def dibujar(self, juego: Juego) -> None:
        if juego.estadio != self._estadio_fondo:
            # Estadio distinto: se pre-renderiza una vez y se conserva.
            self._estadio_fondo = juego.estadio
            self.fondo = self._crear_fondo(juego.estadio)

        # El mundo (campo, jugadores, balón, clima y grada) se pinta en
        # un lienzo propio para que la cámara pueda acercarlo; los
        # overlays televisivos van directos sobre la pantalla. Los
        # métodos de dibujo escriben en self.pantalla: se redirige al
        # lienzo durante el pase de mundo y se restituye después.
        mundo = self._lienzo
        pantalla_real = self.pantalla
        self.pantalla = mundo

        mundo.blit(self.fondo, (0, 0))
        self._dibujar_aficionados_reaccion(juego)
        self._dibujar_objetivo_pase(juego)

        for jugador in juego.jugadores:
            jugador.dibujar(mundo)

        self._dibujar_lances(juego)
        juego.balon.dibujar(mundo)
        self._dibujar_jugador_controlado(juego)
        self._dibujar_escudo(juego)
        self._dibujar_clima(juego)

        self.pantalla = pantalla_real
        self._dibujar_con_camara(mundo, juego)

        self._dibujar_marcador(juego)
        self._dibujar_tiempo(juego)
        self._dibujar_viento(juego)
        self._dibujar_energia(juego)
        self._dibujar_hud()

        if juego.estado is Estado.GOL:
            self._dibujar_mensaje_gol(juego)
        elif juego.estado is Estado.REPETICION:
            self._dibujar_mensaje_repeticion()
        elif juego.estado is Estado.CORNER:
            self._dibujar_mensaje_corner()
        elif juego.estado in ESTADOS_ESPERA:
            self._dibujar_mensaje_estado(juego)

    def _dibujar_con_camara(self, mundo: pygame.Surface, juego: Juego) -> None:
        """Cámara dinámica: acerca y sigue al balón.

        El zoom entra cuando el balón corre o ronda las áreas y el
        encuadre lo persigue con suavizado; en reposo vuelve al plano
        completo, donde no hace falta reescalar nada.
        """
        velocidad = juego.balon.vel.length()
        cerca_del_arco = min(
            abs(juego.balon.pos.x - CAMPO_RECT.left),
            abs(juego.balon.pos.x - CAMPO_RECT.right),
        ) < ZOOM_CAMARA_AREA
        objetivo = ZOOM_CAMARA if (velocidad > ZOOM_CAMARA_VELOCIDAD or cerca_del_arco) else 1.0
        self._zoom += (objetivo - self._zoom) * SUAVIZADO_ZOOM
        self._centro_camara += (juego.balon.pos - self._centro_camara) * SUAVIZADO_CAMARA

        ancho = ANCHO * self._zoom
        alto = ALTO * self._zoom
        self._centro_camara.x = acotar(
            self._centro_camara.x, ancho / 2, ANCHO - ancho / 2
        )
        self._centro_camara.y = acotar(
            self._centro_camara.y, alto / 2, ALTO - alto / 2
        )

        if self._zoom >= 0.999:
            self.pantalla.blit(mundo, (0, 0))
            return

        camara = pygame.Rect(0, 0, round(ancho), round(alto))
        camara.center = (
            round(self._centro_camara.x),
            round(self._centro_camara.y),
        )
        pygame.transform.scale(
            mundo.subsurface(camara),
            (ANCHO, ALTO),
            self.pantalla,
        )

    def _camara_rect(self) -> pygame.Rect:
        """El encuadre actual de la cámara, para pruebas y ajustes."""
        camara = pygame.Rect(
            0,
            0,
            round(ANCHO * self._zoom),
            round(ALTO * self._zoom),
        )
        camara.center = (
            round(self._centro_camara.x),
            round(self._centro_camara.y),
        )
        return camara

    def _crear_confeti(self) -> list[tuple[int, int, float, Color]]:
        """Puntos de confeti fijos en la grada, fuera de la cancha."""
        aleatorio = random.Random(3)
        puntos: list[tuple[int, int, float, Color]] = []
        colores = (BLANCO, AMARILLO, CIAN, VERDE_ENERGIA)

        while len(puntos) < 150:
            x = aleatorio.randrange(ANCHO)
            y = aleatorio.randrange(ALTO)

            if CAMPO_RECT.inflate(14, 14).collidepoint(x, y):
                continue

            puntos.append(
                (
                    x,
                    y,
                    aleatorio.uniform(0.0, math.tau),
                    colores[aleatorio.randrange(len(colores))],
                )
            )

        return puntos

    def _dibujar_aficionados_reaccion(self, juego: Juego) -> None:
        """La grada celebra goles y vitorea ocasiones con confeti."""
        emocion = juego.emocion_grada

        if emocion <= 0.02:
            return

        t = pygame.time.get_ticks() * 0.006
        visibles = int(len(self._confeti) * min(1.0, emocion))

        for indice, (x, y, fase, color) in enumerate(self._confeti):
            if indice >= visibles:
                break

            rebote = -abs(math.sin(t + fase)) * 6.0
            self.pantalla.fill(
                color,
                (x, round(y + rebote), 3, 3),
            )

    def _dibujar_viento(self, juego: Juego) -> None:
        """Chip del viento: flecha con su dirección y fuerza actual."""
        viento = juego.viento
        fuerza = viento.length()

        if fuerza < 4.0:
            return

        chip = self._crear_superficie_con_fondo(
            f"VIENTO {fuerza:.0f}",
            self.fuente_hud,
            BLANCO,
            padding_x=14,
            padding_y=6,
            radio=8,
        )
        rect = chip.get_rect(topright=(ANCHO - 14, 12))
        self.pantalla.blit(chip, rect)

        # Flecha en la dirección del viento, junto al chip.
        direccion = viento.normalize()
        origen = pygame.Vector2(rect.left - 22, rect.centery)
        punta = origen + direccion * 13.0
        pygame.draw.line(
            self.pantalla,
            BLANCO,
            origen,
            punta,
            2,
        )
        perpendicular = pygame.Vector2(-direccion.y, direccion.x) * 4.0
        pygame.draw.polygon(
            self.pantalla,
            BLANCO,
            (
                punta + direccion * 5.0,
                punta + perpendicular,
                punta - perpendicular,
            ),
        )

    def _dibujar_hud(self) -> None:
        y = ALTO - len(self.hud) * (self.hud[0].get_height() + 2) - 6

        for linea in self.hud:
            self.pantalla.blit(linea, (12, y))
            y += linea.get_height() + 2

    def _dibujar_clima(self, juego: Juego) -> None:
        """Partículas de lluvia o nieve según el clima del estadio."""
        clima = juego.estadio.clima

        if clima is Clima.DESPEJADO:
            return

        if not hasattr(self, "_particulas_clima") or self._particulas_clima[0] is not clima:
            # Partículas fijas por clima: se crean una vez y caen
            # siempre; el sorteo usa semilla determinista.
            aleatorio = random.Random(11)
            self._particulas_clima = (
                clima,
                [
                    (
                        aleatorio.randrange(ANCHO),
                        aleatorio.randrange(ALTO),
                        aleatorio.uniform(0.6, 1.0),
                    )
                    for _ in range(90)
                ],
            )

        _clima, particulas = self._particulas_clima

        if clima is Clima.LLUVIA:
            for indice, (x, y, velocidad) in enumerate(particulas):
                y += 17.0 * velocidad
                x -= 2.0

                if y > ALTO:
                    y -= ALTO + 20
                    x += 60

                particulas[indice] = (x % ANCHO, y, velocidad)
                pygame.draw.line(
                    self.pantalla,
                    (175, 205, 235),
                    (x, y),
                    (x + 2, y - 12),
                    2,
                )
        else:
            for indice, (x, y, velocidad) in enumerate(particulas):
                y += 2.2 * velocidad
                x += math.sin((y + indice * 13) * 0.05) * 0.6

                if y > ALTO:
                    y -= ALTO + 10

                particulas[indice] = (x % ANCHO, y, velocidad)
                pygame.draw.circle(
                    self.pantalla,
                    BLANCO,
                    (round(x), round(y)),
                    2,
                )

    def _dibujar_mensaje_gol(self, juego: Juego) -> None:
        if juego.ultimo_gol is None:
            return

        mensaje = self.mensajes_gol[juego.ultimo_gol]
        self.pantalla.blit(
            mensaje,
            mensaje.get_rect(center=self.POSICION_MENSAJE_GOL),
        )
        # Narración del gol, debajo del aviso de continuar.
        comentario = juego.comentario_gol

        if comentario:
            superficie = self._comentario_gol(comentario)
            self.pantalla.blit(
                superficie,
                superficie.get_rect(
                    center=(ANCHO // 2, self.POSICION_CONTINUAR[1] + 34)
                ),
            )

        self.pantalla.blit(
            self.superficie_continuar,
            self.superficie_continuar.get_rect(center=self.POSICION_CONTINUAR),
        )

    def _comentario_gol(self, texto: str) -> pygame.Surface:
        """El comentario del narrador, con fondo oscuro y en caché."""
        if texto not in self._comentarios_cache:
            self._comentarios_cache[texto] = self._crear_superficie_con_fondo(
                texto,
                self.fuente_instrucciones,
                CIAN,
                padding_x=14,
                padding_y=6,
                radio=8,
            )

        return self._comentarios_cache[texto]

    def _dibujar_mensaje_repeticion(self) -> None:
        """Cartela de repetición en curso y cómo saltarla."""
        self.pantalla.blit(
            self.superficie_repeticion,
            self.superficie_repeticion.get_rect(
                center=self.POSICION_REPETICION
            ),
        )
        self.pantalla.blit(
            self.superficie_salto_repeticion,
            self.superficie_salto_repeticion.get_rect(
                center=self.POSICION_CONTINUAR
            ),
        )

    def _dibujar_mensaje_corner(self) -> None:
        """Cartela del saque de esquina mientras se coloca el balón."""
        self.pantalla.blit(
            self.superficie_corner,
            self.superficie_corner.get_rect(
                center=self.POSICION_REPETICION
            ),
        )
        self.pantalla.blit(
            self.superficie_continuar,
            self.superficie_continuar.get_rect(
                center=self.POSICION_CONTINUAR
            ),
        )

    def _dibujar_mensaje_estado(self, juego: Juego) -> None:
        """Mensaje de descanso o final, con las cifras del partido."""
        estado = juego.estado
        panel = self.paneles_estado[estado]
        self.pantalla.blit(
            panel,
            panel.get_rect(center=(ANCHO // 2, ALTO // 2 + 20)),
        )
        self.pantalla.blit(
            self.mensajes_estado[estado],
            self.mensajes_estado[estado].get_rect(
                center=self.POSICION_MENSAJE_GOL
            ),
        )
        texto_continuar = self.textos_estado[estado]

        if estado is Estado.FINAL and juego.texto_final:
            # Los modos sustituyen el aviso fijo por su propio desenlace.
            texto_continuar = self.fuente_instrucciones.render(
                juego.texto_final,
                True,
                BLANCO,
            )

        self.pantalla.blit(
            texto_continuar,
            texto_continuar.get_rect(center=self.POSICION_CONTINUAR),
        )

        # Estadísticas del partido, bajo el panel del mensaje.
        y = ALTO // 2 + 110

        for linea in juego.estadisticas.lineas():
            texto = self.fuente_hud.render(linea, True, BLANCO)
            self.pantalla.blit(
                texto,
                texto.get_rect(center=(ANCHO // 2, y)),
            )
            y += texto.get_height() + 4

        # Los trofeos recién ganados se anuncian en el final.
        for nombre in juego.trofeos_nuevos:
            texto = self.fuente_instrucciones.render(
                f"¡TROFEO DESBLOQUEADO: {nombre}!",
                True,
                AMARILLO,
            )
            self.pantalla.blit(
                texto,
                texto.get_rect(center=(ANCHO // 2, y + 10)),
            )
            y += texto.get_height() + 8

    # --------------------------------------------------
    # Piezas pre-renderizadas y cachés
    # --------------------------------------------------

    def _crear_fondo(self, estadio: Estadio) -> pygame.Surface:
        """Pre-renderiza el estadio: entorno, cancha y líneas."""
        fondo = pygame.Surface((ANCHO, ALTO)).convert()

        if estadio.gradas:
            # Graderío con público; la cancha se estampa encima.
            fondo.fill(color_tribuna(estadio.momento))
            dibujar_aficionados(fondo, estadio.momento)
        else:
            fondo.fill(color_entorno(estadio))

        cancha = pygame.Surface(CAMPO_RECT.size)
        dibujar_cesped(cancha, estadio)
        fondo.blit(cancha, CAMPO_RECT.topleft)

        pygame.draw.rect(fondo, BLANCO, CAMPO_RECT, 3)

        pygame.draw.line(
            fondo,
            BLANCO,
            (CAMPO_RECT.centerx, CAMPO_RECT.top),
            (CAMPO_RECT.centerx, CAMPO_RECT.bottom),
            2,
        )

        pygame.draw.circle(
            fondo,
            BLANCO,
            (CAMPO_RECT.centerx, CAMPO_RECT.centery),
            RADIO_CIRCULO_CENTRAL,
            2,
        )

        # Áreas de penalti, en las dos bandas.
        for x in (
            CAMPO_RECT.left,
            CAMPO_RECT.right - AREA_PENALTI_ANCHO,
        ):
            pygame.draw.rect(
                fondo,
                BLANCO,
                (
                    x,
                    CAMPO_RECT.centery - AREA_PENALTI_ALTO // 2,
                    AREA_PENALTI_ANCHO,
                    AREA_PENALTI_ALTO,
                ),
                2,
            )

        # Porterías, a cada lado del campo.
        for x in (
            CAMPO_RECT.left - ANCHO_POSTE,
            CAMPO_RECT.right,
        ):
            pygame.draw.rect(
                fondo,
                BLANCO,
                (x, PORTERIA_SUPERIOR, ANCHO_POSTE, PORTERIA_ALTO),
                3,
            )

        return fondo

    def _crear_panel(
        self,
        mensaje: pygame.Surface,
        texto: pygame.Surface,
    ) -> pygame.Surface:
        """Crea el panel oscuro que acompaña a un mensaje de estado."""
        ancho = max(mensaje.get_width(), texto.get_width()) + 48
        alto = mensaje.get_height() + texto.get_height() + 36
        panel = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        pygame.draw.rect(
            panel,
            (0, 0, 0, 170),
            panel.get_rect(),
            border_radius=16,
        )
        return panel

    def _dibujar_marcador(self, juego: Juego) -> None:
        clave = (
            juego.nivel,
            juego.goles_local,
            juego.goles_visitante,
            juego.escudo.color,
            juego.escudo.color_borde,
            juego.escudo.forma,
            juego.uniformes[Equipo.LOCAL].camiseta,
            juego.uniformes[Equipo.VISITANTE].camiseta,
        )

        if self._marcador_cache is None or self._marcador_cache[0] != clave:
            self._marcador_cache = (
                clave,
                self._crear_superficie_marcador(juego),
            )

        superficie = self._marcador_cache[1]
        self.pantalla.blit(
            superficie,
            superficie.get_rect(center=self.POSICION_MARCADOR),
        )

    def _crear_superficie_marcador(self, juego: Juego) -> pygame.Surface:
        """Bug televisivo: escudos, resultado, colores y aviso en vivo.

        Inspirado en las transmisiones deportivas: franja con el color
        de la camiseta de cada equipo en su borde, escudos a los lados
        del resultado y un punto rojo de emisión en directo.
        """
        nivel = nivel_por_numero(juego.nivel)
        texto = (
            f"LOCAL {juego.goles_local} - "
            f"{juego.goles_visitante} VISITANTE"
        )
        texto_render = self.fuente_marcador.render(texto, True, BLANCO)
        ronda = (
            juego.torneo.etiqueta()
            if juego.torneo is not None
            else f"NIVEL {juego.nivel}"
        )
        subtitulo = self.fuente_hud.render(
            f"{ronda} · {nivel.rival}",
            True,
            BLANCO,
        )

        escudo_rival = self._escudo_rival_escalado(juego.nivel)
        ancho_escudo_jugador = round(Escudo.TAMANO * 2 * 1.05)
        ancho_en_vivo = 84
        ancho_franja = 6

        separacion = 14
        padding_x = 22
        ancho = (
            padding_x
            + ancho_escudo_jugador
            + separacion
            + max(texto_render.get_width(), subtitulo.get_width())
            + separacion
            + escudo_rival.get_width()
            + separacion
            + ancho_en_vivo
            + padding_x
        )
        alto = self.ALTO_ESCUDO_MARCADOR + subtitulo.get_height() + 18

        panel = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        pygame.draw.rect(panel, NEGRO, panel.get_rect(), border_radius=8)

        centro_y = panel.get_rect().centery
        x_escudo_jugador = padding_x + ancho_escudo_jugador // 2
        juego.escudo.dibujar(panel, (x_escudo_jugador, centro_y), 1.05)
        panel.blit(
            escudo_rival,
            escudo_rival.get_rect(
                midright=(
                    ancho - padding_x - ancho_en_vivo,
                    centro_y,
                ),
            ),
        )

        centro_texto = padding_x + ancho_escudo_jugador + separacion
        ancho_texto = ancho - 2 * (
            padding_x + ancho_escudo_jugador + separacion
        ) - ancho_en_vivo
        panel.blit(
            texto_render,
            texto_render.get_rect(
                midtop=(centro_texto + ancho_texto // 2, 9),
            ),
        )
        panel.blit(
            subtitulo,
            subtitulo.get_rect(
                midtop=(centro_texto + ancho_texto // 2, 9 + texto_render.get_height() + 2),
            ),
        )

        # Aviso de emisión en directo, con su punto rojo.
        punto_x = ancho - padding_x - ancho_en_vivo + separacion
        pygame.draw.circle(panel, ROJO_ENERGIA, (punto_x, centro_y), 5)
        en_vivo = self.fuente_hud.render("EN VIVO", True, BLANCO)
        panel.blit(
            en_vivo,
            en_vivo.get_rect(midleft=(punto_x + 12, centro_y)),
        )

        # Franjas del borde con el color de la camiseta de cada equipo.
        pygame.draw.rect(
            panel,
            juego.uniformes[Equipo.LOCAL].camiseta,
            (0, 0, ancho_franja, alto),
        )
        pygame.draw.rect(
            panel,
            juego.uniformes[Equipo.VISITANTE].camiseta,
            (ancho - ancho_franja, 0, ancho_franja, alto),
        )

        return panel.convert_alpha()

    def _escudo_rival_escalado(self, nivel: int) -> pygame.Surface:
        """Imagen del escudo del nivel, escalada para el marcador."""
        escalado = self._escudos_rivales.get(nivel)

        if escalado is None:
            original = cargar_escudo(nivel)
            alto = self.ALTO_ESCUDO_MARCADOR
            ancho = round(original.get_width() * alto / original.get_height())
            escalado = pygame.transform.smoothscale(
                original,
                (ancho, alto),
            ).convert_alpha()
            self._escudos_rivales[nivel] = escalado

        return escalado

    def _dibujar_tiempo(self, juego: Juego) -> None:
        segundos = math.ceil(max(0.0, juego.tiempo_restante) / 1000.0)
        clave = (juego.mitad, segundos)

        if self._tiempo_cache is None or self._tiempo_cache[0] != clave:
            texto = f"{juego.mitad}T  {segundos // 60:02d}:{segundos % 60:02d}"
            self._tiempo_cache = (
                clave,
                self._crear_superficie_tiempo(texto),
            )

        superficie = self._tiempo_cache[1]
        self.pantalla.blit(superficie, self.POSICION_TIEMPO)

    def _dibujar_energia(self, juego: Juego) -> None:
        """Barras de energía: una por jugador controlado en el modo."""
        x, y = self.POSICION_ENERGIA
        self._barra_energia(x, y, juego.energia_actual)

        if juego.modo is ModoJuego.DOS_JUGADORES:
            self._barra_energia(
                x,
                y + self.ALTO_ENERGIA + 8,
                juego.energia_2,
            )

    def _barra_energia(self, x: float, y: float, energia: float) -> None:
        """Dibuja una barra de energía con su marco."""
        ancho = self.ANCHO_ENERGIA
        alto = self.ALTO_ENERGIA

        pygame.draw.rect(
            self.pantalla,
            NEGRO,
            (x, y, ancho, alto),
            border_radius=4,
        )

        proporcion = max(
            0.0,
            min(1.0, energia / ENERGIA_MAXIMA),
        )
        relleno = round((ancho - 4) * proporcion)

        if relleno > 0:
            color = (
                ROJO_ENERGIA
                if proporcion < 0.30
                else VERDE_ENERGIA
            )
            pygame.draw.rect(
                self.pantalla,
                color,
                (x + 2, y + 2, relleno, alto - 4),
                border_radius=3,
            )

        pygame.draw.rect(
            self.pantalla,
            BLANCO,
            (x, y, ancho, alto),
            1,
            border_radius=4,
        )

    def _crear_superficie_tiempo(self, texto: str) -> pygame.Surface:
        return self._crear_superficie_con_fondo(
            texto,
            self.fuente_tiempo,
            BLANCO,
            padding_x=16,
            padding_y=8,
            radio=8,
        )

    def _crear_superficie_con_fondo(
        self,
        texto: str,
        fuente: pygame.font.Font,
        color: Color,
        *,
        padding_x: int,
        padding_y: int,
        radio: int,
    ) -> pygame.Surface:
        """Renderiza un texto sobre un fondo oscuro redondeado."""
        texto_render = fuente.render(texto, True, color)
        fondo = pygame.Surface(
            (
                texto_render.get_width() + padding_x,
                texto_render.get_height() + padding_y,
            ),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            fondo,
            NEGRO,
            fondo.get_rect(),
            border_radius=radio,
        )
        fondo.blit(
            texto_render,
            texto_render.get_rect(center=fondo.get_rect().center),
        )
        return fondo.convert_alpha()

    def _dibujar_jugador_controlado(self, juego: Juego) -> None:
        """Triángulo cian sobre el jugador que controla el humano."""
        control = juego.jugador_controlado

        if control is None or juego.estado is not Estado.JUGANDO:
            return

        x, y = control.rect.center
        base_y = y - control.RADIO - 6
        puntos = (
            (x, base_y),
            (x - 7, base_y - 9),
            (x + 7, base_y - 9),
        )

        pygame.draw.polygon(self.pantalla, CIAN, puntos)
        pygame.draw.polygon(self.pantalla, BLANCO, puntos, 1)

    def _dibujar_escudo(self, juego: Juego) -> None:
        """Escudo personalizado del jugador controlado."""
        control = juego.jugador_controlado

        if control is None or juego.estado is not Estado.JUGANDO:
            return

        juego.escudo.dibujar(self.pantalla, control.rect.center)

    def _dibujar_lances(self, juego: Juego) -> None:
        """Aro blanco alrededor del portero mientras dura su lance."""
        for portero in juego.porteros:
            if portero.lance_restante <= 0.0:
                continue

            pygame.draw.circle(
                self.pantalla,
                BLANCO,
                portero.rect.center,
                portero.RADIO + 7,
                2,
            )

    def _dibujar_objetivo_pase(self, juego: Juego) -> None:
        """Aro cian sobre el compañero al que iría el próximo pase."""
        control = juego.jugador_controlado

        if (
            control is None
            or juego.estado is not Estado.JUGANDO
            or juego.portador is not control
        ):
            return

        receptor = juego.obtener_receptor_mas_cercano(control)

        if receptor is None:
            return

        pygame.draw.circle(
            self.pantalla,
            CIAN,
            receptor.rect.center,
            receptor.RADIO + 6,
            2,
        )
