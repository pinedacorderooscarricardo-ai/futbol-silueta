"""Lógica y estados de la partida."""

from __future__ import annotations

import math
import random
from collections import deque
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

import pygame

from .audio import Sonidos
from .configuracion import (
    ALCANCE_POSESION2,
    CAMPO_RECT,
    CANSANCIO_PARA_ROTAR,
    COOLDOWN_LIBERACION,
    COOLDOWN_ROBO,
    DEFENSAS_MINIMAS_CONTRA,
    DESPLAZAMIENTO_MARCA,
    DISPAROS_PARA_PRESIONAR,
    DURACION_CONTRAATAQUE,
    DURACION_CORNER,
    DURACION_GOL,
    DURACION_MITAD,
    ENERGIA_MAXIMA,
    ENERGIA_MINIMA_SPRINT,
    EQUIPOS,
    ESTADOS_ESPERA,
    FACTOR_CANSANCIO,
    FACTOR_COLISION,
    FACTOR_CONTRAATAQUE,
    FACTOR_POSESION,
    FACTORES_ATAQUE,
    FORMACIONES,
    FORMACION_REMONTADA,
    Estado,
    FPS,
    FUERZA_DESPEJE_PORTERO,
    FUERZA_PATEO,
    GASTO_CANSANCIO,
    GASTO_SPRINT,
    INTERVALO_DECISION_IA,
    INTERVALO_VIENTO,
    ITERACIONES_COLISION,
    LATERAL_APOYO,
    OBJETIVO_ATAQUE_IA,
    PAUSA_CONTRAATAQUE,
    PAUSA_ROTACION,
    PASE_FUERZA_FACTOR,
    PASE_FUERZA_MAX,
    PASE_FUERZA_MIN,
    PORTERIA_CENTRO,
    PORTERIA_INFERIOR,
    PORTERIA_SUPERIOR,
    PORTERO_CENTRADO_TOLERANCIA,
    RADIO_ATAJADA,
    TITULARES_POR_EQUIPO,
    RADIO_BALON,
    RECARGA_ENERGIA,
    RECUPERO_CANSANCIO,
    REPETICION_SEGUNDOS,
    SEGUNDOS_MINIMOS_MUESTRA,
    SESGO_LATERAL_MAX,
    TEXTOS_NARRADOR,
    UMBRAL_ROTACION,
    VENTANA_ADAPTACION,
    VELOCIDAD_MINIMA_ATAJADA,
    VELOCIDAD_REPETICION,
    VELOCIDAD_SPRINT,
    AVANCE_APOYO,
    APOYOS_POR_EQUIPO,
    DISTANCIA_DISPARO_CONTRA,
    Color,
    Equipo,
    Rol,
    formacion_por_nombre,
)
from .modos import ModoJuego, Solicitud, TorneoBase, crear_torneo
from .entidades import (
    Balon,
    Jugador,
    crear_jugadores,
    crear_jugador_de_ficha,
    elegir_delantero_controlado,
)
from .escudos import FormaEscudo, Escudo
from .estadios import (
    ESTADIO_POR_DEFECTO,
    Estadio,
    FRICCION_CLIMA,
    VIENTO_POR_CLIMA,
)
from .estadisticas import EstadisticasPartido
from .niveles import NIVEL_MAXIMO, Nivel, nivel_por_numero
from .plantilla import (
    JugadorPlantilla,
    normalizar_plantilla,
    plantillas_por_defecto,
)
from .porteros import PORTERO_LOCAL, PorteroInteligente, calidad_rival
from .repeticion import Instante, aplicar_instante, capturar_instante
from .uniformes import UNIFORMES_POR_DEFECTO, Uniforme
from .utilidades import acotar, acotar_posicion, equipo_rival

if TYPE_CHECKING:
    from .vista import Vista


class Juego:
    """Estado y lógica de una partida: posesión, IA, input y marcador."""

    def __init__(self, vista: Vista) -> None:
        self.vista = vista

        self.jugadores: list[Jugador] = []
        self.jugador_controlado: Jugador | None = None

        self.balon = Balon()
        self.portador: Jugador | None = None
        self.liberador: Jugador | None = None

        self.goles_local = 0
        self.goles_visitante = 0
        self.ultimo_gol: Equipo | None = None

        # Reloj de simulación (ms): avanza solo cuando la partida avanza
        # (actualizar), así que las pausas y los menús no vencen los
        # cooldowns ni acortan las celebraciones del partido.
        self._reloj = 0.0
        self.tiempo_posesion = 0
        self.tiempo_liberacion = -COOLDOWN_LIBERACION
        self.tiempo_gol = 0
        self.estado = Estado.JUGANDO

        # Nivel de la campaña y escudo del jugador para ese nivel.
        self.nivel = 1
        self.escudo = Escudo.crear_para_nivel(self.nivel)

        # Uniformes de ambos equipos y si se muestran los dorsales.
        self.uniformes: dict[Equipo, Uniforme] = dict(
            UNIFORMES_POR_DEFECTO
        )
        self.mostrar_numeros = True

        # Estadio elegido: césped, momento, gradas y diseño de cancha.
        self.estadio = ESTADIO_POR_DEFECTO

        # Fichas editables de los 22 jugadores (nombres, dorsales,
        # atributos y posiciones).
        self.plantillas = plantillas_por_defecto()

        # Táctica en uso: nombre de la formación elegida en el menú.
        self.formacion_nombre = "4-4-2"

        # Modo de juego y torneo en curso (liga, copa, campeones o
        # supervivencia); texto de la pantalla final y petición hacia
        # la aplicación (por ejemplo, volver al menú principal).
        self.modo = ModoJuego.CAMPANA
        self.torneo = crear_torneo(self.modo)
        self.texto_final = ""
        self.solicitud: Solicitud | None = None
        self._fin_del_torneo_mostrado = False

        # Segundo jugador (modo dos jugadores) y su energía propia.
        self.jugador_controlado_2: Jugador | None = None
        self.energia_2 = float(ENERGIA_MAXIMA)

        self.mitad = 1
        self.tiempo_restante = float(DURACION_MITAD)
        self.energia_actual = float(ENERGIA_MAXIMA)
        self.sonidos = Sonidos()

        # Decisiones tácticas de la IA, recalculadas cada intervalo y al
        # cambiar la posesión; el movimiento usa la última decisión.
        self._tiempo_decision = 0
        self._equipo_con_balon: Equipo | None = None
        self._perseguidores: set[Jugador] = set()
        self._marcajes: dict[Jugador, Jugador] = {}

        # Repeticiones de gol: buffer circular con los últimos segundos
        # de juego y, al marcar, la jugada congelada que se reproduce
        # en cámara lenta tras la celebración. Las tres últimas quedan
        # guardadas para volver a verlas con R.
        self._instantes: deque[Instante] = deque(
            maxlen=round(REPETICION_SEGUNDOS * FPS)
        )
        self.repeticion: list[Instante] | None = None
        self._indice_repeticion = 0.0
        self.repeticiones_guardadas: deque[list[Instante]] = deque(maxlen=3)
        self._instante_reanudar: Instante | None = None

        # Estadísticas del partido y narración de los goles.
        self.estadisticas = EstadisticasPartido()
        self.ultimo_tocador: Jugador | None = None
        self.comentario_gol = ""

        # El resultado se registra una sola vez, al terminar el partido.
        self.resultado_registrado = False
        self.trofeos_nuevos: list[str] = []

        # Saque de esquina: equipo que cobra y vértice de la cancha.
        self.esquina: Equipo | None = None
        self.tiempo_corner = 0
        self._punto_esquina = pygame.Vector2(CAMPO_RECT.center)

        # Clima avanzado: viento dinámico que empuja al balón libre.
        self.viento = pygame.Vector2()
        self._tiempo_viento = 0

        # Emoción de la grada (0-1): sube con goles y ocasiones.
        self.emocion_grada = 0.0

        # IA adaptativa: muestrea el estilo del jugador por ventanas.
        self._ventana_estilo = float(VENTANA_ADAPTACION)
        self._t_arriba = 0.0
        self._t_abajo = 0.0
        self._disparos_ventana = 0
        self._sesgo_lateral = 0.0
        self._presores_extra = 0

        # Contraataques y táctica rival.
        self._en_contraataque = False
        self._fin_contraataque = 0
        self._ultimo_fin_contraataque = -PAUSA_CONTRAATAQUE
        self._formacion_visitante = self.formacion_nombre
        self._ultima_rotacion = -PAUSA_ROTACION
        self._apoyos: set[Jugador] = set()
        self._marcajes_fijos: dict[Jugador, Jugador] = {}

        self.reiniciar_jugada(con_silbato=False)

    # --------------------------------------------------
    # Niveles
    # --------------------------------------------------

    @property
    def nivel_actual(self) -> Nivel:
        """Nivel con el que se está jugando ahora."""
        return nivel_por_numero(self.nivel)

    def _actualizar_escudo(self) -> None:
        """Recrea el escudo del nivel conservando la personalización."""
        self.escudo = Escudo.crear_para_nivel(
            self.nivel,
            color=self.escudo.color,
            color_borde=self.escudo.color_borde,
            forma=self.escudo.forma,
        )

    def _reiniciar_nivel(self, nivel: int, con_silbato: bool = True) -> None:
        """Reinicia el partido para un nivel de la campaña."""
        self.nivel = nivel
        self._actualizar_escudo()

        self.goles_local = 0
        self.goles_visitante = 0
        self.ultimo_gol = None
        self.comentario_gol = ""
        self.mitad = 1
        self.tiempo_restante = float(DURACION_MITAD)
        self.energia_actual = float(ENERGIA_MAXIMA)
        self.energia_2 = float(ENERGIA_MAXIMA)
        # La IA adaptativa arranca sin datos previos del partido anterior.
        self._disparos_ventana = 0
        self._presores_extra = 0
        self._sesgo_lateral = 0.0

        # El nuevo partido arranca con sus estadísticas a cero y sin
        # resultado registrado; las repeticiones guardadas se renuevan.
        self.estadisticas.reiniciar()
        self.repeticiones_guardadas.clear()
        self.resultado_registrado = False
        self.trofeos_nuevos = []
        self.reiniciar_jugada(con_silbato=con_silbato)

    def adoptar_nivel(self, nivel: int) -> None:
        """Adopta el nivel guardado de la campaña (al arrancar).

        Solo fija el nivel y su escudo rival: la partida arranca después
        con JUGAR, que ya se ocupa de recrear a los jugadores.
        """
        self.nivel = acotar(int(nivel), 1, NIVEL_MAXIMO)
        self._actualizar_escudo()

    def _reiniciar_partido(
        self,
        nivel: int = 1,
        con_silbato: bool = True,
    ) -> None:
        """Reinicia el marcador y el reloj para una revancha."""
        self._reiniciar_nivel(nivel, con_silbato=con_silbato)

    def _siguiente_nivel(self) -> None:
        """Pasa al nivel siguiente de la campaña."""
        siguiente = self.nivel + 1 if self.nivel < NIVEL_MAXIMO else 1
        self._reiniciar_nivel(siguiente, con_silbato=True)

    def personalizar_escudo(
        self,
        color: Color,
        color_borde: Color,
        forma: FormaEscudo | None = None,
    ) -> None:
        """Aplica la personalización elegida por el jugador."""
        self.escudo.cambiar_colores(color, color_borde)

        if forma is not None:
            self.escudo.cambiar_forma(forma)

    def personalizar_uniformes(
        self,
        uniformes: dict[Equipo, Uniforme],
        mostrar_numeros: bool,
    ) -> None:
        """Aplica las equipaciones y los dorsales elegidos por el jugador."""
        self.uniformes = dict(uniformes)
        self.mostrar_numeros = mostrar_numeros

    def personalizar_estadio(self, estadio: Estadio) -> None:
        """Aplica el estadio elegido; la vista redibuja el fondo al pintar."""
        self.estadio = estadio

    def personalizar_plantillas(
        self,
        plantillas: dict[Equipo, tuple[JugadorPlantilla, ...]],
    ) -> None:
        """Aplica las fichas editadas por el jugador en el editor."""
        self.plantillas = {
            equipo: normalizar_plantilla(plantillas.get(equipo), equipo)
            for equipo in Equipo
        }

    def cambiar_formacion(
        self,
        nombre: str,
        recolocar: bool = True,
    ) -> None:
        """Adopta una formación de tácticas como la disposición en uso.

        ``recolocar`` recrea a los jugadores en sus nuevas posiciones
        con saque al centro; se evita cuando la partida se reinicia de
        todos modos (por ejemplo al pulsar JUGAR). Las fichas ya deben
        llegar recolocadas: el menú de tácticas las reajusta.
        """
        self.formacion_nombre = (
            nombre if nombre in FORMACIONES else "4-4-2"
        )

        if recolocar:
            self.reiniciar_jugada()

    def sustituir(
        self,
        equipo: Equipo,
        hueco: int,
        ficha_entrante: JugadorPlantilla,
    ) -> bool:
        """Mete a un suplente en el hueco de un titular, sin parar la jugada.

        ``ficha_entrante`` ya lleva el rol y la posición del hueco (el
        menú de sustituciones la reemplaza al confirmar). El titular que
        deja el campo se identifica por ``hueco`` (su índice en la
        plantilla), no por el dorsal, que es editable y puede repetirse.
        Devuelve True si el cambio se aplicó.
        """
        if not 0 <= hueco < TITULARES_POR_EQUIPO:
            return False

        equipo_jugadores = [
            jugador
            for jugador in self.jugadores
            if jugador.equipo is equipo
        ]

        if hueco >= len(equipo_jugadores):
            return False

        saliente = equipo_jugadores[hueco]
        indice = self.jugadores.index(saliente)

        entrante = crear_jugador_de_ficha(
            equipo,
            ficha_entrante,
            saliente.uniforme,
            saliente.mostrar_numero,
        )

        self.jugadores[indice] = entrante
        # Reconstruye los porteros IA por si cambió el portero.
        self._recrear_porteros_ia()

        # Si el cambio toca al jugador controlado o al portador, el
        # control y el balón pasan al que entra.
        if self.jugador_controlado is saliente:
            self.jugador_controlado = entrante

        if self.portador is saliente:
            saliente.tiene_balon = False
            entrante.tiene_balon = True
            self.portador = entrante

        self._invalidar_decisiones()
        return True

    def _recrear_porteros_ia(self) -> None:
        """Reconstruye la lista de porteros y sus cerebros IA.

        Se llama cada vez que cambian los porteros (jugada nueva,
        sustitución o cambio de táctica rival): ``porteros_ia`` siempre
        apunta a los objetos vivos, sin referencias a jugadores que ya
        dejaron el campo.
        """
        # Los porteros se usan en cada subpaso del balón: se guardan una
        # sola vez por jugada en vez de filtrar entre los 22 cada vez.
        self.porteros = tuple(
            jugador
            for jugador in self.jugadores
            if jugador.rol is Rol.PORTERO
        )
        # Porteros inteligentes: uno por portero, con la calidad del
        # nivel para el rival y la fija para el local.
        self.porteros_ia: dict[Jugador, PorteroInteligente] = {
            portero: PorteroInteligente(
                portero,
                (
                    PORTERO_LOCAL
                    if portero.equipo is Equipo.LOCAL
                    else calidad_rival(self.nivel)
                ),
            )
            for portero in self.porteros
        }

    # --------------------------------------------------
    # Inicio, reinicio y posesión
    # --------------------------------------------------

    def reiniciar_jugada(self, con_silbato: bool = True) -> None:
        """Reinicia posiciones y balón sin tocar el marcador.

        La primera jugada del arranque no suena para no silbar mientras
        el jugador todavía está en el menú principal.
        """
        self.jugadores = crear_jugadores(
            self.uniformes,
            self.mostrar_numeros,
            self.plantillas,
        )
        self.jugador_controlado = elegir_delantero_controlado(self.jugadores)

        # Segundo jugador del modo dos jugadores: delantero visitante.
        self.jugador_controlado_2 = (
            self._delantero_de(Equipo.VISITANTE)
            if self.modo is ModoJuego.DOS_JUGADORES
            else None
        )

        self._recrear_porteros_ia()

        self.portador = None
        self.liberador = None
        self.tiempo_posesion = 0
        self.tiempo_liberacion = (
            self._reloj - COOLDOWN_LIBERACION
        )
        self._invalidar_decisiones()

        # Los instantes referencian posiciones por índice: al recrearse
        # los jugadores, la grabación anterior ya no corresponde.
        self._instantes.clear()
        self.repeticion = None
        self._instante_reanudar = None

        # La IA recupera su táctica y sus marcajes con jugadores nuevos.
        self._formacion_visitante = self.formacion_nombre
        self._marcajes_fijos = {}
        self._apoyos = set()
        # Un contraataque no sobrevive al saque de centro ni a un gol.
        self._en_contraataque = False
        self._fin_contraataque = 0

        self.balon.colocar_en_el_centro()
        self.estado = Estado.JUGANDO

        if con_silbato:
            self.sonidos.silbato()

    def _delantero_de(self, equipo: Equipo) -> Jugador | None:
        """Delantero de un equipo más cercano al centro del campo."""
        delanteros = [
            jugador
            for jugador in self.jugadores
            if jugador.equipo is equipo and jugador.rol is Rol.DELANTERO
        ]

        if not delanteros:
            delanteros = [
                jugador
                for jugador in self.jugadores
                if jugador.equipo is equipo
            ]

        if not delanteros:
            return None

        centro = pygame.Vector2(CAMPO_RECT.center)

        return min(
            delanteros,
            key=lambda jugador: jugador.pos.distance_squared_to(centro),
        )

    def _invalidar_decisiones(self) -> None:
        """Fuerza a la IA a recalcular sus decisiones en el próximo frame.

        También vacía la caché: así nunca quedan referencias a jugadores
        de una jugada anterior (al reiniciar se crean otros nuevos).
        """
        self._tiempo_decision = (
            self._reloj - INTERVALO_DECISION_IA
        )
        self._perseguidores = set()
        self._marcajes = {}

    def _actualizar_decisiones(self) -> None:
        """Recalcula quién presiona, a quién marca y dónde se apoya.

        Aprovecha la revisión para la táctica rival (formación al ir
        perdiendo) y las rotaciones de los rivales cansados.
        """
        self._equipo_con_balon = (
            self.portador.equipo if self.portador is not None else None
        )
        self._perseguidores = self._elegir_perseguidores(
            self._equipo_con_balon
        )
        self._marcajes = self._asignar_marcajes(
            self._equipo_con_balon,
            self._perseguidores,
        )
        self._elegir_apoyos()
        self._revisar_tactica_visitante()
        self._revisar_rotaciones()

    def _elegir_apoyos(self) -> None:
        """Los dos compañeros más cercanos al portador buscan espacios."""
        self._apoyos = set()

        if self.portador is None:
            return

        companeros = [
            jugador
            for jugador in self.jugadores
            if jugador.equipo is self.portador.equipo
            and jugador is not self.portador
            and jugador.rol is not Rol.PORTERO
            and jugador is not self.jugador_controlado
            and jugador is not self.jugador_controlado_2
        ]
        companeros.sort(
            key=lambda jugador: jugador.pos.distance_squared_to(
                self.portador.pos
            )
        )
        self._apoyos = set(companeros[:APOYOS_POR_EQUIPO])

    def dar_posesion(self, jugador: Jugador) -> None:
        """Da el balón a un jugador y se lo quita a su dueño anterior."""
        previo = self.portador
        previo_equipo = previo.equipo if previo is not None else None

        if previo is not None:
            previo.tiene_balon = False

        jugador.tiene_balon = True
        self.portador = jugador
        self.liberador = None
        self.ultimo_tocador = jugador
        self.tiempo_posesion = self._reloj
        self._invalidar_decisiones()

        if jugador.equipo is Equipo.LOCAL:
            self.jugador_controlado = jugador
        elif self.modo is ModoJuego.DOS_JUGADORES:
            self.jugador_controlado_2 = jugador

        # El jugador al que le roban el balón cae al suelo un instante.
        if previo is not None and previo_equipo is not jugador.equipo:
            previo.caer(0.6)

        # Contraataque: el rival roba en campo local con pocos defensores
        # detrás y sale a la carrera aprovechando los espacios.
        if (
            jugador.equipo is Equipo.VISITANTE
            and previo_equipo is Equipo.LOCAL
            and self.estado is Estado.JUGANDO
        ):
            self._iniciar_contraataque()

    def liberar_posesion(
        self,
        velocidad: pygame.Vector2 | None = None,
    ) -> None:
        """Suelta el balón, opcionalmente con una velocidad inicial."""
        self.liberador = self.portador
        self.ultimo_tocador = self.liberador

        if self.portador is not None:
            self.portador.tiene_balon = False

        self.portador = None
        self.tiempo_liberacion = self._reloj
        self._invalidar_decisiones()

        if velocidad is not None:
            self.balon.vel.update(velocidad)

    def _jugador_mas_cercano(
        self,
        punto: pygame.Vector2,
        filtro: Callable[[Jugador], bool] | None = None,
        alcance2: float = ALCANCE_POSESION2,
    ) -> Jugador | None:
        """Jugador más cercano a un punto dentro del alcance indicado."""
        mejor: Jugador | None = None
        mejor_distancia = alcance2

        for jugador in self.jugadores:
            if filtro is not None and not filtro(jugador):
                continue

            distancia = jugador.pos.distance_squared_to(punto)

            if distancia <= mejor_distancia:
                mejor_distancia = distancia
                mejor = jugador

        return mejor

    def _recoger_balon_libre(self) -> bool:
        """Da posesión al jugador que alcance el balón libre, si hay uno.

        Durante el cooldown solo se impide que lo recoja quien lo soltó;
        así un pase corto sí puede llegar a su destinatario y un rival
        puede interceptar un tiro rápido.
        """
        ahora = self._reloj
        liberador = self.liberador

        if (
            liberador is not None
            and ahora - self.tiempo_liberacion < COOLDOWN_LIBERACION
        ):
            cercano = self._jugador_mas_cercano(
                self.balon.pos,
                lambda jugador: jugador is not liberador,
            )
        else:
            cercano = self._jugador_mas_cercano(self.balon.pos)

        if cercano is None:
            return False

        self.dar_posesion(cercano)
        return True

    def actualizar_posesion(self) -> None:
        """Resuelve quién tiene el balón en este fotograma."""
        if self.portador is None:
            self._recoger_balon_libre()
            return

        if (
            self._reloj - self.tiempo_posesion
            < COOLDOWN_ROBO
        ):
            return

        if (
            self.modo is ModoJuego.ENTRENAMIENTO
            and self.portador.equipo is Equipo.LOCAL
        ):
            # Rivales congelados: en el entrenamiento no roban el balón.
            return

        portador = self.portador
        rival = self._jugador_mas_cercano(
            self.balon.pos,
            lambda jugador: jugador.equipo is not portador.equipo,
        )

        if rival is not None:
            self.dar_posesion(rival)

    # --------------------------------------------------
    # Pases
    # --------------------------------------------------

    def obtener_receptor_mas_cercano(
        self,
        jugador: Jugador,
    ) -> Jugador | None:
        """Compañero de campo más cercano; el portero solo si no hay otro."""
        mejor: Jugador | None = None
        mejor_distancia = float("inf")

        portero: Jugador | None = None
        mejor_distancia_portero = float("inf")

        for companero in self.jugadores:
            if companero is jugador or companero.equipo is not jugador.equipo:
                continue

            distancia = companero.pos.distance_squared_to(jugador.pos)

            if companero.rol is Rol.PORTERO:
                if distancia < mejor_distancia_portero:
                    mejor_distancia_portero = distancia
                    portero = companero
            elif distancia < mejor_distancia:
                mejor_distancia = distancia
                mejor = companero

        return mejor if mejor is not None else portero

    def pasar_al_companero_mas_cercano(self) -> None:
        """Pasa el balón al compañero de campo más cercano."""
        self._pasar_de(self.jugador_controlado)

    def _pasar_de(self, jugador: Jugador | None) -> None:
        """Pase del jugador indicado a su compañero más cercano."""

        if jugador is None or not jugador.tiene_balon:
            return

        receptor = self.obtener_receptor_mas_cercano(jugador)

        if receptor is None:
            return

        direccion = receptor.pos - jugador.pos
        distancia = direccion.length()

        if distancia < 1e-6:
            return

        direccion /= distancia
        fuerza = min(
            max(PASE_FUERZA_MIN, distancia * PASE_FUERZA_FACTOR),
            PASE_FUERZA_MAX,
        ) * jugador.factor_fuerza

        self.sonidos.pase()
        self.estadisticas.contar_pase(jugador.equipo)
        self.liberar_posesion(direccion * fuerza)

        if receptor.equipo is Equipo.LOCAL:
            self.jugador_controlado = receptor
        elif (
            self.modo is ModoJuego.DOS_JUGADORES
            and receptor.equipo is Equipo.VISITANTE
        ):
            self.jugador_controlado_2 = receptor

    # --------------------------------------------------
    # Balón
    # --------------------------------------------------

    def _intentar_atajada(self) -> bool:
        """Atrapa un balón rápido que llega a la zona del portero.

        Cada portero usa su propio alcance: el rival, el del nivel, y el
        local, el base. Durante un lance las manos llegan más lejos,
        pero si el portero falló el disparo (lo decide su calidad) el
        balón se le escapa entre las manos.
        """
        if (
            self.balon.vel.length_squared()
            < VELOCIDAD_MINIMA_ATAJADA**2
        ):
            return False

        radio_rival = (
            self.nivel_actual.parametros.radio_atajada_rival
        )

        # Solo los dos porteros, ya filtrados: se consulta en cada
        # subpaso del balón, no hace falta recorrer a los 22 jugadores.
        for portero in self.porteros:
            portero_ia = self.porteros_ia[portero]
            base = radio_rival if portero.equipo is Equipo.VISITANTE else RADIO_ATAJADA

            if portero.pos.distance_squared_to(
                self.balon.pos
            ) > portero_ia.radio_atajada(base) ** 2:
                continue

            hacia_el_arco = -1.0 if portero.equipo is Equipo.LOCAL else 1.0
            if self.balon.vel.x * hacia_el_arco <= 0.0:
                continue

            if not portero_ia.puede_atrapar():
                continue

            # Mira hacia el campo para que el balón quede delante suyo.
            portero.direccion.update(hacia_el_arco * -1.0, 0.0)
            self.dar_posesion(portero)
            self.estadisticas.contar_atajada(portero.equipo)

            # Reacción del portero: si atrapó en pleno lance cae al
            # suelo; de pie, celebra el gesto con un salto.
            if portero.lance_restante > 0.0:
                portero.caer(0.9)
            else:
                portero.saltar(0.9)

            # La grada vitorea la ocasión.
            self.emocion_grada = max(self.emocion_grada, 0.45)
            return True

        return False

    def _intentar_recoger_o_atajar(self) -> bool:
        """Primero prueba la atajada; si no, la recogida normal."""
        return self._intentar_atajada() or self._recoger_balon_libre()

    def actualizar_balon(self, dt: float) -> None:
        """Actualiza el balón y registra gol o córner, si los hay."""
        if self.portador is not None:
            salida = self.balon.actualizar_conducido(self.portador)
        else:
            tocado_por = (
                self.ultimo_tocador.equipo
                if self.ultimo_tocador is not None
                else None
            )
            salida = self.balon.actualizar_libre(
                dt,
                self._intentar_recoger_o_atajar,
                FRICCION_CLIMA[self.estadio.clima],
                tocado_por,
                self.viento,
            )

        if salida.gol is not None:
            self.marcar_gol(salida.gol)
        elif salida.esquina is not None:
            self.generar_corner(salida.esquina)

    def _actualizar_viento(self) -> None:
        """Cambia la dirección y fuerza del viento de vez en cuando."""
        ahora = self._reloj

        if ahora - self._tiempo_viento < INTERVALO_VIENTO:
            return

        self._tiempo_viento = ahora
        maximo = VIENTO_POR_CLIMA[self.estadio.clima]
        angulo = random.uniform(0.0, math.tau)
        fuerza = random.uniform(0.3, 1.0) * maximo
        self.viento.update(
            math.cos(angulo) * fuerza,
            math.sin(angulo) * fuerza,
        )

    def avanzar_animaciones(self, dt: float) -> None:
        """Hace vivas las animaciones en cualquier estado del partido.

        Los saltos, caídas y zancadas corren también durante el gol y
        la repetición; en celebración, los goleadores no paran de saltar.
        """
        self.emocion_grada = max(0.0, self.emocion_grada - 0.22 * dt)

        for jugador in self.jugadores:
            jugador.avanzar_animacion(dt)

            if (
                self.estado in (Estado.GOL, Estado.REPETICION)
                and self.ultimo_gol is jugador.equipo
                and jugador.salto_restante <= 0.0
            ):
                jugador.saltar(0.8)

    def _chutar(self, direccion: pygame.Vector2, chutador: Jugador) -> None:
        """Suelta el balón con la fuerza de un disparo en ``direccion``.

        La fuerza base se escala con el atributo de fuerza del chutador.
        """
        if direccion.length_squared() < 1e-6:
            return

        direccion = direccion.normalize()
        self.sonidos.disparo()
        self.estadisticas.contar_disparo(chutador.equipo)
        self.liberar_posesion(
            direccion * FUERZA_PATEO * chutador.factor_fuerza
        )

    # --------------------------------------------------
    # IA
    # --------------------------------------------------

    def actualizar_ia(self, dt: float) -> None:
        """Mueve a los jugadores IA según su última decisión táctica.

        Las decisiones (persecutores, marcajes, apoyos) se recalculan
        cada ``INTERVALO_DECISION_IA`` milisegundos y al cambiar la
        posesión; el movimiento de cada jugador se aplica en todos los
        fotogramas. El contraataque termina al expirar o perder el balón
        y los rivales se cansan con el esfuerzo.
        """
        ahora = self._reloj

        if self._en_contraataque and (
            ahora >= self._fin_contraataque
            or self.portador is None
            or self.portador.equipo is not Equipo.VISITANTE
        ):
            self._en_contraataque = False
            self._ultimo_fin_contraataque = ahora

        if ahora - self._tiempo_decision >= INTERVALO_DECISION_IA:
            self._tiempo_decision = ahora
            self._actualizar_decisiones()

        parametros = self.nivel_actual.parametros

        # El portador visitante decide entre conducir y disparar. En
        # Dos Jugadores, si el portador es el segundo humano, no decide la IA.
        if (
            self.portador is not None
            and self.portador.equipo is Equipo.VISITANTE
            and self.portador is not self.jugador_controlado_2
        ):
            self._accion_portador_ia(self.portador, dt)

        # Porteros inteligentes: anticipan, cubren el ángulo y se
        # lanzan. El portador y el portero controlado por el humano no
        # los mueve la IA.
        for portero in self.porteros:
            if portero is self.portador:
                continue
            if portero is self.jugador_controlado:
                continue
            if portero is self.jugador_controlado_2:
                continue

            self.porteros_ia[portero].actualizar(self, dt)

        # El resto de los jugadores de campo (menos el humano controlado).
        velocidad_ia = parametros.velocidad_ia
        equipo_con_balon = self._equipo_con_balon
        perseguidores = self._perseguidores
        marcajes = self._marcajes

        # Cansancio rival: sube con el esfuerzo y frena al agotado.
        for jugador in self.jugadores:
            if (
                jugador.equipo is not Equipo.VISITANTE
                or jugador.rol is Rol.PORTERO
            ):
                continue

            if jugador is self.portador or jugador in perseguidores:
                jugador.cansancio = min(
                    1.0,
                    jugador.cansancio + GASTO_CANSANCIO * dt,
                )
            else:
                jugador.cansancio = max(
                    0.0,
                    jugador.cansancio - RECUPERO_CANSANCIO * dt,
                )

        for jugador in self.jugadores:
            if jugador.rol is Rol.PORTERO:
                continue
            if jugador is self.portador:
                continue
            if jugador is self.jugador_controlado:
                continue
            if jugador is self.jugador_controlado_2:
                continue
            if (
                self.modo is ModoJuego.ENTRENAMIENTO
                and jugador.equipo is Equipo.VISITANTE
            ):
                # Rivales congelados: entrenamiento sin oposición.
                continue

            objetivo = self._objetivo_ia(
                jugador,
                equipo_con_balon,
                jugador in perseguidores,
                marcajes.get(jugador),
            )
            velocidad = velocidad_ia * jugador.factor_velocidad

            if jugador.equipo is Equipo.VISITANTE:
                velocidad *= 1.0 - FACTOR_CANSANCIO * jugador.cansancio

            jugador.mover_hacia(objetivo, velocidad, dt)

    def _elegir_perseguidores(
        self,
        equipo_con_balon: Equipo | None,
    ) -> set[Jugador]:
        """Los N jugadores de campo más cercanos al balón de cada equipo.

        El jugador controlado por el humano no ocupa una plaza de presión:
        si está cerca, presiona él mismo y el equipo conserva sus N
        perseguidores de IA.
        """
        perseguidores: set[Jugador] = set()

        for equipo in EQUIPOS:
            if equipo is equipo_con_balon:
                continue

            candidatos = [
                jugador
                for jugador in self.jugadores
                if jugador.equipo is equipo
                and jugador.rol is not Rol.PORTERO
                and jugador is not self.jugador_controlado
                and jugador is not self.jugador_controlado_2
            ]
            candidatos.sort(
                key=lambda jugador: jugador.pos.distance_squared_to(
                    self.balon.pos
                )
            )
            # IA adaptativa: si el humano dispara mucho, la rival presiona
            # con un jugador más de lo habitual.
            extra = (
                self._presores_extra if equipo is Equipo.VISITANTE else 0
            )
            perseguidores.update(
                candidatos[
                    : self.nivel_actual.parametros.presores + extra
                ]
            )

        return perseguidores

    def _asignar_marcajes(
        self,
        equipo_con_balon: Equipo | None,
        perseguidores: set[Jugador],
    ) -> dict[Jugador, Jugador]:
        """Marcaje individual: cada defensa sigue a un atacante fijo.

        Las parejas se heredan entre decisiones (y entre cambios de
        posesión) para que cada defensa persiga siempre al mismo
        rival; solo se reasignan los huecos nuevos, tomados por
        cercanía del rival libre a la zona del defensa.
        """
        equipo_defensor = (
            equipo_rival(equipo_con_balon)
            if equipo_con_balon is not None
            else None
        )

        # Sin posesión clara, cada defensa conserva a su hombre.
        if equipo_defensor is None:
            return dict(self._marcajes_fijos)

        defensas = [
            jugador
            for jugador in self.jugadores
            if jugador.equipo is equipo_defensor
            and jugador.rol is Rol.DEFENSA
            and jugador is not self.jugador_controlado
            and jugador is not self.jugador_controlado_2
            and jugador not in perseguidores
        ]
        atacantes = [
            jugador
            for jugador in self.jugadores
            if jugador.equipo is not equipo_defensor
            and jugador.rol is not Rol.PORTERO
            and jugador is not self.portador
            and jugador is not self.jugador_controlado_2
        ]

        disponibles = set(atacantes)
        asignaciones: dict[Jugador, Jugador] = {}

        # Hereda las parejas que siguen siendo válidas.
        for defensor in defensas:
            marcado = self._marcajes_fijos.get(defensor)

            if marcado in disponibles:
                asignaciones[defensor] = marcado
                disponibles.remove(marcado)

        # Los defensas nuevos toman el rival libre más cercano a su zona.
        radio2 = self.nivel_actual.parametros.radio_marcaje**2

        for defensor in sorted(
            (d for d in defensas if d not in asignaciones),
            key=lambda jugador: jugador.posicion_base.y,
        ):
            candidatos = [
                atacante
                for atacante in disponibles
                if atacante.pos.distance_squared_to(defensor.posicion_base)
                <= radio2
            ]

            if not candidatos:
                continue

            marcado = min(
                candidatos,
                key=lambda atacante: atacante.pos.distance_squared_to(
                    defensor.posicion_base
                ),
            )
            asignaciones[defensor] = marcado
            disponibles.remove(marcado)

        self._marcajes_fijos = dict(asignaciones)
        return asignaciones

    # --------------------------------------------------
    # IA adaptativa, contraataques y táctica rival
    # --------------------------------------------------

    def _observar_estilo(self, dt: float) -> None:
        """IA adaptativa: aprende dónde atacas y cuánto disparas.

        Al cerrar cada ventana corre su bloque defensivo hacia el lado
        de ataque más usado y añade un perseguidor si el jugador dispara
        con frecuencia; con poca muestra, conserva lo aprendido.
        """
        self._ventana_estilo -= dt * 1000.0

        if self.portador is not None and self.portador.equipo is Equipo.LOCAL:
            if self.balon.pos.y < CAMPO_RECT.centery:
                self._t_arriba += dt
            else:
                self._t_abajo += dt

        if self._ventana_estilo > 0.0:
            return

        self._ventana_estilo = float(VENTANA_ADAPTACION)
        total = self._t_arriba + self._t_abajo

        if total >= SEGUNDOS_MINIMOS_MUESTRA:
            sesgo = (self._t_abajo - self._t_arriba) / total
            self._sesgo_lateral = (
                max(-1.0, min(1.0, sesgo)) * SESGO_LATERAL_MAX
            )

        self._t_arriba = 0.0
        self._t_abajo = 0.0

        disparos = (
            self.estadisticas.disparos[Equipo.LOCAL] - self._disparos_ventana
        )
        self._disparos_ventana = self.estadisticas.disparos[Equipo.LOCAL]
        self._presores_extra = (
            1 if disparos >= DISPAROS_PARA_PRESIONAR else 0
        )

    def _iniciar_contraataque(self) -> None:
        """Activa el contraataque si el robo deja espacios detrás."""
        ahora = self._reloj

        if ahora - self._ultimo_fin_contraataque < PAUSA_CONTRAATAQUE:
            return

        defensores_detras = sum(
            1
            for jugador in self.jugadores
            if jugador.equipo is Equipo.LOCAL
            and jugador.rol is not Rol.PORTERO
            and jugador.pos.x < self.balon.pos.x
        )

        if defensores_detras >= DEFENSAS_MINIMAS_CONTRA:
            return

        self._en_contraataque = True
        self._fin_contraataque = ahora + DURACION_CONTRAATAQUE

    def _revisar_tactica_visitante(self) -> None:
        """Perdiendo en el segundo tiempo, la rival pasa a la remontada."""
        if self.mitad != 2:
            return

        if self.goles_visitante >= self.goles_local:
            return

        if self._formacion_visitante == FORMACION_REMONTADA:
            return

        self._formacion_visitante = FORMACION_REMONTADA
        self._recolocar_visitante(FORMACION_REMONTADA)

    def _recolocar_visitante(self, nombre: str) -> None:
        """Adapta a los rivales a una formación: rol y base de cada uno.

        Solo cambian el rol táctico y la zona de referencia del equipo
        rival; sus fichas del editor (nombres, atributos) no se tocan.
        """
        rivales = [
            jugador
            for jugador in self.jugadores
            if jugador.equipo is Equipo.VISITANTE
        ]

        for jugador, slot in zip(
            rivales,
            formacion_por_nombre(nombre),
            strict=False,
        ):
            jugador.rol = slot.rol
            # El visitante defiende el arco derecho: base reflejada.
            jugador.posicion_base.update(
                CAMPO_RECT.left + (1.0 - slot.x) * CAMPO_RECT.width,
                CAMPO_RECT.top + slot.y * CAMPO_RECT.height,
            )

        # Los roles cambian por slot; los porteros se rehacen para que
        # porteros y porteros_ia sigan a los jugadores vivos.
        self._recrear_porteros_ia()

    def _revisar_rotaciones(self) -> None:
        """Sustituciones tácticas: el más fresco cubre la zona agotada.

        Un rival muy cansado intercambia su zona de referencia con la
        del compañero más descansado de su misma posición, con una
        pausa entre rotaciones para no marear al bloque.
        """
        ahora = self._reloj

        if ahora - self._ultima_rotacion < PAUSA_ROTACION:
            return

        rivales = [
            jugador
            for jugador in self.jugadores
            if jugador.equipo is Equipo.VISITANTE
            and jugador.rol is not Rol.PORTERO
        ]

        for agotado in rivales:
            if agotado.cansancio < UMBRAL_ROTACION:
                continue

            if agotado is self.portador:
                continue

            frescos = [
                jugador
                for jugador in rivales
                if jugador is not agotado
                and jugador.rol is agotado.rol
                and jugador.cansancio < CANSANCIO_PARA_ROTAR
            ]

            if not frescos:
                continue

            fresco = min(frescos, key=lambda jugador: jugador.cansancio)
            fresco.posicion_base, agotado.posicion_base = (
                agotado.posicion_base,
                fresco.posicion_base,
            )
            self._ultima_rotacion = ahora
            return

    def _despejar_portero(self, portero: Jugador) -> None:
        """Pase largo del portero IA al compañero más cercano."""
        companeros = [
            jugador
            for jugador in self.jugadores
            if jugador.equipo is portero.equipo
            and jugador.rol is not Rol.PORTERO
        ]

        if companeros:
            receptor = min(
                companeros,
                key=lambda jugador: jugador.pos.distance_squared_to(
                    portero.pos
                ),
            )
            direccion = receptor.pos - portero.pos
        else:
            direccion = pygame.Vector2(
                CAMPO_RECT.centerx - portero.pos.x,
                PORTERIA_CENTRO - portero.pos.y,
            )

        if direccion.length_squared() < 1e-6:
            return

        direccion.normalize_ip()
        self.sonidos.pase()
        self.estadisticas.contar_pase(portero.equipo)
        self.liberar_posesion(
            direccion * FUERZA_DESPEJE_PORTERO * portero.factor_fuerza
        )

    def _accion_portador_ia(self, jugador: Jugador, dt: float) -> None:
        """Conduce hacia el arco o dispara si ya está en zona de tiro.

        En contraataque conduce más rápido y dispara desde más lejos,
        aprovechando los espacios que deja la defensa.
        """
        parametros = self.nivel_actual.parametros
        factor_contra = (
            FACTOR_CONTRAATAQUE if self._en_contraataque else 1.0
        )
        distancia_disparo = parametros.distancia_disparo

        if self._en_contraataque:
            distancia_disparo *= DISTANCIA_DISPARO_CONTRA

        if jugador.rol is Rol.PORTERO:
            # El portero IA no se va de dribling: aguanta y despeja.
            jugador.mover_hacia(
                jugador.posicion_base,
                parametros.velocidad_ia * jugador.factor_velocidad,
                dt,
            )
            if (
                self._reloj - self.tiempo_posesion
                >= parametros.duracion_posesion_portero
            ):
                self._despejar_portero(jugador)
            return

        distancia = math.hypot(
            jugador.pos.x - CAMPO_RECT.left,
            jugador.pos.y - PORTERIA_CENTRO,
        )
        tiempo_con_balon = (
            self._reloj - self.tiempo_posesion
        )

        if (
            distancia <= distancia_disparo
            and tiempo_con_balon >= parametros.tiempo_minimo_posesion
        ):
            self._disparar_ia(jugador)
            return

        jugador.mover_hacia(
            OBJETIVO_ATAQUE_IA,
            parametros.velocidad_ia
            * FACTOR_POSESION
            * factor_contra
            * jugador.factor_velocidad
            * (1.0 - FACTOR_CANSANCIO * jugador.cansancio),
            dt,
        )

    def _disparar_ia(self, jugador: Jugador) -> None:
        """Dispara la IA hacia el lado abierto del arco local."""
        objetivo = self._objetivo_para_disparo_ia(jugador)
        self._chutar(objetivo - jugador.pos, jugador)

    def _objetivo_para_disparo_ia(
        self,
        jugador: Jugador,
    ) -> pygame.Vector2:
        """Punto del arco local al lado opuesto al portero local."""
        portero = next(
            (
                otro
                for otro in self.jugadores
                if otro.equipo is Equipo.LOCAL
                and otro.rol is Rol.PORTERO
            ),
            None,
        )

        if (
            portero is None
            or abs(portero.pos.y - PORTERIA_CENTRO)
            < PORTERO_CENTRADO_TOLERANCIA
        ):
            # Portero centrado: buscar el palo más lejano al tirador.
            lado = 1.0 if jugador.pos.y <= PORTERIA_CENTRO else -1.0
        else:
            lado = 1.0 if portero.pos.y < PORTERIA_CENTRO else -1.0

        margen = RADIO_BALON
        medio_arco = (
            PORTERIA_INFERIOR - PORTERIA_SUPERIOR
        ) / 2.0 - margen
        factor = self.nivel_actual.parametros.factor_apuntado
        y = PORTERIA_CENTRO + lado * medio_arco * factor
        y = acotar(
            y,
            PORTERIA_SUPERIOR + margen,
            PORTERIA_INFERIOR - margen,
        )

        return pygame.Vector2(CAMPO_RECT.left, y)

    def _objetivo_ia(
        self,
        jugador: Jugador,
        equipo_con_balon: Equipo | None,
        persigue: bool,
        marcado: Jugador | None = None,
    ) -> pygame.Vector2:
        """Punto al que un jugador de campo IA quiere moverse este frame."""
        base = jugador.posicion_base
        ataca = equipo_con_balon is jugador.equipo

        if persigue:
            objetivo = self.balon.pos.copy()
        elif (
            ataca
            and self.portador is not None
            and jugador in self._apoyos
        ):
            # Juego colectivo: desmarque adelantado y abierto a banda
            # para recibir un pase del portador.
            avance = 1.0 if jugador.equipo is Equipo.LOCAL else -1.0
            lado = 1.0 if jugador.pos.y >= self.portador.pos.y else -1.0
            objetivo = self.portador.pos + pygame.Vector2(
                avance * AVANCE_APOYO,
                lado * LATERAL_APOYO,
            )
        elif marcado is not None:
            # Colocarse entre el rival marcado y el arco propio.
            signo = -1.0 if jugador.equipo is Equipo.LOCAL else 1.0
            objetivo = pygame.Vector2(
                marcado.pos.x + signo * DESPLAZAMIENTO_MARCA,
                marcado.pos.y,
            )
            # IA adaptativa: el bloque rival se corre hacia el lado por
            # el que el jugador ataca más.
            if jugador.equipo is Equipo.VISITANTE:
                objetivo.y += self._sesgo_lateral
        elif ataca:
            fx, fy = FACTORES_ATAQUE.get(jugador.rol, (0.1, 0.15))
            objetivo = pygame.Vector2(
                base.x + (self.balon.pos.x - base.x) * fx,
                base.y + (self.balon.pos.y - base.y) * fy,
            )
        else:
            objetivo = base.copy()

        acotar_posicion(objetivo, jugador.RADIO)
        return objetivo

    # --------------------------------------------------
    # Colisiones
    # --------------------------------------------------

    def _resolver_colisiones(self) -> None:
        """Separa suavemente a los jugadores que se superponen.

        Trabaja con coordenadas sueltas en vez de crear un vector por
        pareja: con 231 parejas y varias iteraciones por fotograma,
        son cientos de objetos temporales que no hacen falta.
        """
        # Todos los jugadores comparten el mismo radio.
        minima = Jugador.RADIO * 2
        minima2 = minima * minima
        factor = FACTOR_COLISION * 0.5

        jugadores = self.jugadores
        total = len(jugadores)

        for _ in range(ITERACIONES_COLISION):
            for indice in range(total - 1):
                jugador_a = jugadores[indice]

                for otro_indice in range(indice + 1, total):
                    jugador_b = jugadores[otro_indice]
                    dx = jugador_b.pos.x - jugador_a.pos.x
                    dy = jugador_b.pos.y - jugador_a.pos.y
                    distancia2 = dx * dx + dy * dy

                    if distancia2 >= minima2:
                        continue

                    if distancia2 < 1e-12:
                        # Totalmente superpuestos: empuje hacia la derecha.
                        distancia = 0.0
                        normal_x, normal_y = 1.0, 0.0
                    else:
                        distancia = math.sqrt(distancia2)
                        normal_x = dx / distancia
                        normal_y = dy / distancia

                    empuje = (minima - distancia) * factor
                    jugador_a.empujar(
                        -normal_x * empuje,
                        -normal_y * empuje,
                    )
                    jugador_b.empujar(
                        normal_x * empuje,
                        normal_y * empuje,
                    )

    # --------------------------------------------------
    # Jugador humano
    # --------------------------------------------------

    def actualizar_jugador(
        self,
        dt: float,
        teclas: Sequence[bool],
    ) -> None:
        """Mueve a los jugadores controlados y gestiona su energía.

        Con dos jugadores en el teclado, el primero juega con WASD y el
        segundo con las flechas; cada uno tiene su propia energía.
        """
        control = self.jugador_controlado

        if control is None:
            return

        dos = self.modo is ModoJuego.DOS_JUGADORES
        self.energia_actual = self._mover_controlado(
            control,
            self._entrada_p1(teclas, dos),
            dt,
            self._sprint_p1(teclas, dos),
            self.energia_actual,
        )

        if dos and self.jugador_controlado_2 is not None:
            self.energia_2 = self._mover_controlado(
                self.jugador_controlado_2,
                self._entrada_p2(teclas),
                dt,
                self._sprint_p2(teclas),
                self.energia_2,
            )

    @staticmethod
    def _entrada_p1(teclas: Sequence[bool], dos: bool) -> tuple[int, int]:
        """WASD siempre; las flechas solo si no juega el segundo."""
        dx = 0
        dy = 0

        if teclas[pygame.K_w] or (not dos and teclas[pygame.K_UP]):
            dy -= 1
        if teclas[pygame.K_s] or (not dos and teclas[pygame.K_DOWN]):
            dy += 1
        if teclas[pygame.K_a] or (not dos and teclas[pygame.K_LEFT]):
            dx -= 1
        if teclas[pygame.K_d] or (not dos and teclas[pygame.K_RIGHT]):
            dx += 1

        return dx, dy

    @staticmethod
    def _entrada_p2(teclas: Sequence[bool]) -> tuple[int, int]:
        """El segundo jugador se mueve con las flechas."""
        dx = 0
        dy = 0

        if teclas[pygame.K_UP]:
            dy -= 1
        if teclas[pygame.K_DOWN]:
            dy += 1
        if teclas[pygame.K_LEFT]:
            dx -= 1
        if teclas[pygame.K_RIGHT]:
            dx += 1

        return dx, dy

    def _sprint_p1(self, teclas: Sequence[bool], dos: bool) -> bool:
        """Sprint del primer jugador: SHIFT izquierdo (o ambos a uno)."""
        if self.energia_actual < ENERGIA_MINIMA_SPRINT:
            return False

        return bool(
            teclas[pygame.K_LSHIFT] or (not dos and teclas[pygame.K_RSHIFT])
        )

    def _sprint_p2(self, teclas: Sequence[bool]) -> bool:
        """Sprint del segundo jugador: SHIFT derecho."""
        if self.energia_2 < ENERGIA_MINIMA_SPRINT:
            return False

        return bool(teclas[pygame.K_RSHIFT])

    def _mover_controlado(
        self,
        control: Jugador,
        entrada: tuple[int, int],
        dt: float,
        sprint: bool,
        energia: float,
    ) -> float:
        """Aplica el movimiento de un controlado y devuelve su energía."""
        dx, dy = entrada

        if dx == 0 and dy == 0:
            return self._recargar_energia(energia, dt)

        movimiento = pygame.Vector2(dx, dy)
        movimiento.normalize_ip()

        if sprint:
            energia = max(0.0, energia - GASTO_SPRINT * dt)
            velocidad = control.velocidad_efectiva() * VELOCIDAD_SPRINT
        else:
            energia = self._recargar_energia(energia, dt)
            velocidad = control.velocidad_efectiva()

        control.mover(
            movimiento.x * velocidad * dt,
            movimiento.y * velocidad * dt,
        )
        return energia

    def _recargar_energia(self, energia: float, dt: float) -> float:
        """Recupera energía mientras no se está sprintando."""
        return min(float(ENERGIA_MAXIMA), energia + RECARGA_ENERGIA * dt)

    def _disparar_humano(self) -> None:
        """Chuta el balón en la dirección de mirada del jugador."""
        self._chutar_de(self.jugador_controlado)

    def _chutar_de(self, jugador: Jugador | None) -> None:
        """Disparo del jugador indicado, si tiene el balón."""
        if jugador is None or self.portador is not jugador:
            return

        self._chutar(jugador.direccion, jugador)

    def _cambiar_jugador(self) -> None:
        """Cambia el control al siguiente local por cercanía al balón.

        Cada pulsación entrega el mando al siguiente jugador de campo
        local más cercano al balón: la primera ya controla al más
        conveniente y las siguientes recorren al resto. Con posesión
        local el control acompaña a quien lleva el balón y no cambia.
        """
        if self.portador is not None and self.portador.equipo is Equipo.LOCAL:
            return

        ordenados = sorted(
            (
                jugador
                for jugador in self.jugadores
                if jugador.equipo is Equipo.LOCAL
                and jugador.rol is not Rol.PORTERO
            ),
            key=lambda jugador: jugador.pos.distance_squared_to(
                self.balon.pos
            ),
        )

        if not ordenados:
            return

        if self.jugador_controlado in ordenados:
            indice = ordenados.index(self.jugador_controlado)
            self.jugador_controlado = ordenados[
                (indice + 1) % len(ordenados)
            ]
        else:
            # El control estaba en el portero: pasa al más cercano.
            self.jugador_controlado = ordenados[0]

    # --------------------------------------------------
    # Goles, eventos y bucle principal
    # --------------------------------------------------

    def marcar_gol(self, equipo: Equipo) -> None:
        """Registra un gol y pasa al estado de celebración."""
        if self.portador is not None:
            self.portador.tiene_balon = False

        self.portador = None
        self.liberador = None
        self.ultimo_gol = equipo

        if equipo is Equipo.LOCAL:
            self.goles_local += 1
        else:
            self.goles_visitante += 1

        self.estado = Estado.GOL
        self.tiempo_gol = self._reloj
        self.sonidos.gol()

        # Celebración: los del equipo que marca saltan y el portero
        # batido cae al suelo; la grada estalla.
        for jugador in self.jugadores:
            if jugador.equipo is equipo:
                jugador.saltar(1.0)

        for portero in self.porteros:
            if portero.equipo is not equipo:
                portero.caer(1.2)

        self.emocion_grada = 1.0

        # Narración: el comentario lleva el nombre de quien tocó el
        # balón por última vez antes de cruzar la línea.
        autor = self.ultimo_tocador
        nombre = (
            autor.nombre
            if autor is not None and autor.nombre
            else ("el local" if equipo is Equipo.LOCAL else "el visitante")
        )
        self.comentario_gol = random.choice(TEXTOS_NARRADOR).format(
            jugador=nombre
        )

        # Congela la jugada completa, hasta el balón dentro de la red,
        # para reproducirla en cámara lenta tras la celebración. Queda
        # entre las mejores jugadas para volver a verla con R.
        self._instantes.append(capturar_instante(self))
        self.repeticion = list(self._instantes)
        self.repeticiones_guardadas.append(self.repeticion)
        self._indice_repeticion = 0.0

    def generar_corner(self, equipo: Equipo) -> None:
        """Pita un saque de esquina para ``equipo`` y congela la jugada.

        El vértice se elige por dónde salió el balón: línea izquierda o
        derecha y mitad superior o inferior de la cancha.
        """
        if self.portador is not None:
            self.portador.tiene_balon = False

        self.portador = None
        self.liberador = None
        self.esquina = equipo
        self.estado = Estado.CORNER
        self.tiempo_corner = self._reloj
        self.sonidos.silbato()

        a_la_izquierda = self.balon.pos.x < CAMPO_RECT.centerx
        abajo = self.balon.pos.y > CAMPO_RECT.centery
        self._punto_esquina = pygame.Vector2(
            CAMPO_RECT.left + RADIO_BALON if a_la_izquierda
            else CAMPO_RECT.right - RADIO_BALON,
            CAMPO_RECT.bottom - RADIO_BALON if abajo
            else CAMPO_RECT.top + RADIO_BALON,
        )

    def _cobrar_corner(self) -> None:
        """Coloca el córner: el balón al vértice y el cobrador a su lado.

        El jugador de campo del equipo que cobra más cercano al vértice
        se sitúa junto a él, mirando al centro, y saca conduciendo.
        """
        punto = self._punto_esquina
        equipo = self.esquina
        assert equipo is not None
        cobrador = min(
            (
                jugador
                for jugador in self.jugadores
                if jugador.equipo is equipo
                and jugador.rol is not Rol.PORTERO
            ),
            key=lambda jugador: jugador.pos.distance_squared_to(punto),
        )

        hacia_dentro = 1.0 if punto.x < CAMPO_RECT.centerx else -1.0
        cobrador.pos.update(punto.x + hacia_dentro * 24.0, punto.y)
        cobrador.direccion.update(hacia_dentro, 0.0)
        cobrador.actualizar_rect()

        self.balon.pos.update(punto)
        self.balon.vel.update(0.0, 0.0)
        self.dar_posesion(cobrador)
        self.estado = Estado.JUGANDO

    def actualizar(self, dt: float) -> None:
        """Avanza la simulación un fotograma."""
        # El reloj del partido solo corre cuando el partido corre: una
        # pausa abierta con ESC congela también los cooldowns, las
        # celebraciones y los córners pendientes.
        self._reloj += dt * 1000.0

        if self.estado in ESTADOS_ESPERA:
            return

        if self.estado is Estado.REPETICION:
            self._avanzar_repeticion()
            return

        if self.estado is Estado.CORNER:
            if self._reloj - self.tiempo_corner >= DURACION_CORNER:
                self._cobrar_corner()
            return

        if self.estado is Estado.GOL:
            if self._reloj - self.tiempo_gol >= DURACION_GOL:
                self._iniciar_repeticion()
            return

        if self.modo is not ModoJuego.ENTRENAMIENTO:
            self.tiempo_restante -= dt * 1000.0

            if self.tiempo_restante <= 0.0:
                self.tiempo_restante = 0.0
                self._terminar_mitad()
                return

        self.actualizar_jugador(dt, pygame.key.get_pressed())
        self.actualizar_ia(dt)
        self._resolver_colisiones()
        self.actualizar_balon(dt)

        # Si se marcó gol, actualizar_balon ya cambió el estado y
        # congeló la repetición: solo se graba en juego corriente.
        if self.estado is Estado.JUGANDO:
            self._instantes.append(capturar_instante(self))
            self.estadisticas.acumular_posesion(self.portador, dt)
            self._observar_estilo(dt)
            self._actualizar_viento()
            self.actualizar_posesion()

    def _iniciar_repeticion(self) -> None:
        """Reproduce el gol recién marcado en cámara lenta."""
        if not self.repeticion:
            self.reiniciar_jugada()
            return

        self.estado = Estado.REPETICION
        self._indice_repeticion = 0.0
        aplicar_instante(self, self.repeticion[0])

    def _avanzar_repeticion(self) -> None:
        """Muestra el siguiente fotograma grabado; al acabar, saca."""
        repeticion = self.repeticion

        if not repeticion:
            self.reiniciar_jugada()
            return

        self._indice_repeticion += VELOCIDAD_REPETICION

        if self._indice_repeticion >= len(repeticion):
            self._terminar_repeticion()
            return

        aplicar_instante(self, repeticion[int(self._indice_repeticion)])

    def _terminar_repeticion(self) -> None:
        """Cierra la repetición: saque de centro o reanudar la jugada.

        Cuando la repetición se pidió con R, el estado del partido se
        congeló al empezar: se restaura tal cual y se sigue jugando.
        """
        instante = self._instante_reanudar
        self._instante_reanudar = None
        self.repeticion = None

        if instante is not None:
            aplicar_instante(self, instante)
            self.estado = Estado.JUGANDO
        else:
            self.reiniciar_jugada()

    def _repetir_mejor_jugada(self) -> None:
        """Vuelve a mostrar en cámara lenta la última mejor jugada.

        Congela el estado actual del partido (posiciones y balón) para
        restaurarlo cuando la repetición termine o se salte.
        """
        if not self.repeticiones_guardadas:
            return

        self._instante_reanudar = capturar_instante(self)
        self.repeticion = self.repeticiones_guardadas[-1]
        self._indice_repeticion = 0.0
        self.estado = Estado.REPETICION
        aplicar_instante(self, self.repeticion[0])

    def _terminar_mitad(self) -> None:
        """Detiene el juego al final del primer o segundo tiempo."""
        if self.mitad == 1:
            self.estado = Estado.ENTRETIEMPO
            return

        self.estado = Estado.FINAL
        self._cerrar_partido()

    def _cerrar_partido(self) -> None:
        """Registra el resultado y prepara el texto final según el modo."""
        self._fin_del_torneo_mostrado = False

        if self.modo is ModoJuego.CAMPANA:
            self.texto_final = ""
            return

        if self.modo is ModoJuego.DOS_JUGADORES:
            if self.goles_local == self.goles_visitante:
                self.texto_final = "Empate. ESPACIO: otro partido"
            else:
                ganador = (
                    "LOCAL"
                    if self.goles_local > self.goles_visitante
                    else "VISITANTE"
                )
                self.texto_final = f"¡GANA {ganador}! ESPACIO: otro partido"
            return

        if self.torneo is not None:
            self.torneo.registrar(self.goles_local, self.goles_visitante)
            self.texto_final = self.torneo.texto_tras_partido()

    def _empezar_segunda_mitad(self) -> None:
        """Prepara el segundo tiempo tras el descanso."""
        self.mitad = 2
        self.tiempo_restante = float(DURACION_MITAD)
        self.energia_actual = float(ENERGIA_MAXIMA)
        self.energia_2 = float(ENERGIA_MAXIMA)
        self.reiniciar_jugada()

    def nueva_partida(self, con_silbato: bool = True) -> None:
        """Empieza una partida desde cero, conservando la misma ventana.

        En la campaña se retoma el nivel que estaba en curso (el guardado
        o el alcanzado); en los torneos, el rival de la próxima ronda.
        Si el torneo ya está decidido, reiniciar empieza uno nuevo: no
        queda ninguna ronda de la que sacar rival.
        """
        if self.torneo is not None and self.torneo.terminado:
            self.torneo = crear_torneo(self.modo)

        nivel = (
            self.torneo.rival_del_partido() if self.torneo is not None else self.nivel
        )
        self._reiniciar_partido(nivel, con_silbato=con_silbato)

    def iniciar_modo(
        self,
        modo: ModoJuego,
        torneo: TorneoBase | None = None,
    ) -> None:
        """Arranca un modo; ``torneo`` reanuda uno guardado si hay.

        Sin torneo indicado, el modo empieza de cero con el suyo nuevo.
        """
        self.modo = modo
        self.torneo = torneo if torneo is not None else crear_torneo(modo)
        self.texto_final = ""
        self.solicitud = None
        self._fin_del_torneo_mostrado = False
        self.nueva_partida()

    def procesar_tecla(self, tecla: int) -> None:
        """Reacciona a una tecla pulsada durante el partido."""
        if tecla == pygame.K_SPACE:
            self._al_pulsar_espacio()
        elif tecla == pygame.K_e and self.estado is Estado.JUGANDO:
            self.pasar_al_companero_mas_cercano()
        elif tecla == pygame.K_q and self.estado is Estado.JUGANDO:
            self._cambiar_jugador()
        elif tecla == pygame.K_r and self.estado is Estado.JUGANDO:
            self._repetir_mejor_jugada()
        elif (
            self.modo is ModoJuego.DOS_JUGADORES
            and tecla in (pygame.K_RETURN, pygame.K_KP_ENTER)
        ):
            # Segundo jugador: ENTER chuta o avanza los estados.
            if self.estado is Estado.JUGANDO:
                self._chutar_de(self.jugador_controlado_2)
            else:
                self._al_pulsar_espacio()
        elif (
            self.modo is ModoJuego.DOS_JUGADORES
            and tecla == pygame.K_RCTRL
            and self.estado is Estado.JUGANDO
        ):
            self._pasar_de(self.jugador_controlado_2)

    def _continuar_tras_final(self) -> None:
        """ESPACIO en la pantalla final, según el modo de juego.

        Los torneos terminados muestran primero su desenlace y solo en
        el siguiente ESPACIO piden volver al menú principal.
        """
        if self.modo is ModoJuego.CAMPANA:
            self._siguiente_nivel()
            return

        if self.modo is ModoJuego.ENTRENAMIENTO:
            return

        torneo = self.torneo

        if torneo is not None and torneo.terminado:
            if not self._fin_del_torneo_mostrado:
                self.texto_final = torneo.texto_final_torneo()
                self._fin_del_torneo_mostrado = True
                return

            self.solicitud = Solicitud.MENU_PRINCIPAL
            return

        self.nueva_partida()

    def _al_pulsar_espacio(self) -> None:
        """ESPACIO: chutar, pasar de la celebración a la repetición,
        saltarla, adelantar el córner o pasar de tiempo."""
        if self.estado is Estado.GOL:
            self._iniciar_repeticion()
        elif self.estado is Estado.REPETICION:
            self._terminar_repeticion()
        elif self.estado is Estado.CORNER:
            self._cobrar_corner()
        elif self.estado is Estado.ENTRETIEMPO:
            self._empezar_segunda_mitad()
        elif self.estado is Estado.FINAL:
            self._continuar_tras_final()
        elif self.estado is Estado.JUGANDO:
            self._disparar_humano()
