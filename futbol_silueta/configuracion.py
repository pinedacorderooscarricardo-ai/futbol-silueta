"""Constantes y configuración global de Fútbol Silueta.

Aquí viven todos los valores ajustables del juego: tamaño de la ventana,
colores, física, tiempos, formación de los equipos y textos de la interfaz.
"""

from __future__ import annotations

from enum import StrEnum
from typing import NamedTuple

import pygame

# ============================================================
# 1. Ventana
# ============================================================

ANCHO, ALTO = 1000, 650
FPS = 60
DT_MAXIMO = 0.05
# Paso de simulación fijo: la física avanza siempre en incrementos
# iguales, acumulando el tiempo real sobrante, de modo que el partido
# se comporta igual en computadoras rápidas y lentas.
DT_FIJO = 1.0 / FPS
# Máximo de pasos de simulación por fotograma para ponerse al día. Si
# aun así sobra tiempo atrasado, se descarta en vez de acumular retraso
# (y que la simulación entre en espiral).
MAX_PASOS_FISICA = 3
TITULO_VENTANA = "Fútbol Silueta - 22 jugadores"

Color = tuple[int, int, int]

# ============================================================
# 2. Colores
# ============================================================

VERDE: Color = (34, 139, 34)
BLANCO: Color = (255, 255, 255)
AMARILLO: Color = (255, 215, 0)
NEGRO: Color = (20, 20, 20)
CIAN: Color = (0, 255, 255)
VERDE_ENERGIA: Color = (70, 200, 90)
ROJO_ENERGIA: Color = (220, 60, 60)

# ============================================================
# 3. Equipos, estados y roles
# ============================================================


class Equipo(StrEnum):
    """Equipos que participan en el partido."""

    LOCAL = "local"
    VISITANTE = "visitante"


class Estado(StrEnum):
    """Estados posibles de la partida."""

    JUGANDO = "jugando"
    GOL = "gol"
    REPETICION = "repeticion"
    CORNER = "corner"
    ENTRETIEMPO = "entretiempo"
    FINAL = "final"


class Rol(StrEnum):
    """Roles de los jugadores dentro de la formación."""

    PORTERO = "portero"
    DEFENSA = "defensa"
    MEDIO = "medio"
    DELANTERO = "delantero"


EQUIPOS: tuple[Equipo, ...] = (Equipo.LOCAL, Equipo.VISITANTE)
ESTADOS_ESPERA: tuple[Estado, ...] = (Estado.ENTRETIEMPO, Estado.FINAL)

# ============================================================
# 4. Campo y porterías
# ============================================================

MARGEN_X = 50
MARGEN_Y = 60
CAMPO_RECT = pygame.Rect(
    MARGEN_X,
    MARGEN_Y,
    ANCHO - 2 * MARGEN_X,
    ALTO - 2 * MARGEN_Y,
)

RADIO_BALON = 10
RADIO_JUGADOR = 12
ALCANCE_POSESION = RADIO_JUGADOR + RADIO_BALON
ALCANCE_POSESION2 = ALCANCE_POSESION * ALCANCE_POSESION

PORTERIA_ALTO = 100
PORTERIA_CENTRO = CAMPO_RECT.centery
PORTERIA_SUPERIOR = PORTERIA_CENTRO - PORTERIA_ALTO // 2
PORTERIA_INFERIOR = PORTERIA_CENTRO + PORTERIA_ALTO // 2

AREA_PENALTI_ANCHO = 100
AREA_PENALTI_ALTO = 240
RADIO_CIRCULO_CENTRAL = 60
ANCHO_POSTE = 12

# ============================================================
# 5. Física (píxeles por segundo)
# ============================================================

VELOCIDAD_JUGADOR = 180.0
VELOCIDAD_IA = 144.0
FUERZA_PATEO = 720.0
PASE_FUERZA_MIN = 360.0
PASE_FUERZA_MAX = 960.0
PASE_FUERZA_FACTOR = 3.0
FRICCION = 0.985  # Por cada paso de 1/60 s.
FACTOR_POSESION = 0.7  # Velocidad relativa al conducir el balón.
VELOCIDAD_MINIMA_BALON = 4.8
PASO_MAXIMO_BALON = 8.0  # px por subpaso, para no atravesar jugadores.
# Distancia a la que rueda el balón delante del jugador que lo conduce.
DISTANCIA_CONDUCCION = RADIO_JUGADOR + RADIO_BALON - 4

# ============================================================
# 6. Sprint y energía
# ============================================================

VELOCIDAD_SPRINT = 1.5
ENERGIA_MAXIMA = 100.0
GASTO_SPRINT = 25.0  # Energía por segundo.
RECARGA_ENERGIA = 20.0  # Energía por segundo.
ENERGIA_MINIMA_SPRINT = 5.0

# ============================================================
# 7. Temporizadores (milisegundos)
# ============================================================

COOLDOWN_ROBO = 400
COOLDOWN_LIBERACION = 200
DURACION_GOL = 1500
# Pausa del saque de esquina antes de colocarlo en el vértice.
DURACION_CORNER = 1200
DURACION_MITAD = 3 * 60 * 1000

# Repetición de goles: segundos de partido que conserva el buffer
# circular y velocidad de reproducción (<1.0 = cámara lenta; 0.4
# reproduce 4 s grabados en 10 s reales).
REPETICION_SEGUNDOS = 4.0
VELOCIDAD_REPETICION = 0.4

# ============================================================
# 8. IA de formación
# ============================================================

# Cuánto se acerca cada rol al balón cuando su equipo ataca.
# (factor_x, factor_y): 0.0 = quedarse en la base, 1.0 = ir al balón.
FACTORES_ATAQUE: dict[Rol, tuple[float, float]] = {
    Rol.DEFENSA: (0.08, 0.15),
    Rol.MEDIO: (0.20, 0.30),
    Rol.DELANTERO: (0.35, 0.45),
}

# Jugadores que presionan el balón por equipo cuando NO lo tienen.
PRESORES_POR_EQUIPO = 2

# Cada cuántos milisegundos la IA recalcula sus decisiones tácticas
# (persecutores y marcajes). El movimiento de cada jugador sigue
# actualizándose en todos los fotogramas.
INTERVALO_DECISION_IA = 100

# ============================================================
# 8b. IA adaptativa y juego colectivo
# ============================================================

# La rival muestrea el estilo del jugador en ventanas de este tamaño
# y ajusta su bloque: dónde atacas (sesgo lateral) y cuánto disparas
# (un perseguidor extra).
VENTANA_ADAPTACION = 5000
SEGUNDOS_MINIMOS_MUESTRA = 2.0
SESGO_LATERAL_MAX = 70.0
DISPAROS_PARA_PRESIONAR = 2

# Juego colectivo: los compañeros del portador buscan espacios para
# recibir, adelantados y abiertos por bandas.
APOYOS_POR_EQUIPO = 2
AVANCE_APOYO = 110.0
LATERAL_APOYO = 90.0

# ============================================================
# 8c. Contraataques, táctica rival y sustituciones
# ============================================================

# Al robar en campo contrario y con pocos defensores por detrás, el
# rival sale a la carrera: conduce más rápido y dispara desde más lejos.
DURACION_CONTRAATAQUE = 3000
PAUSA_CONTRAATAQUE = 6000
FACTOR_CONTRAATAQUE = 1.25
DISTANCIA_DISPARO_CONTRA = 1.4
DEFENSAS_MINIMAS_CONTRA = 3

# Perdiendo en el segundo tiempo, la rival pasa a la formación remontada.
FORMACION_REMONTADA = "4-3-3"

# Cansancio de los rivales (0-1): corren más lento a medida que se
# agotan y la IA rota al más fresco de la misma posición.
GASTO_CANSANCIO = 0.045
RECUPERO_CANSANCIO = 0.02
FACTOR_CANSANCIO = 0.3
UMBRAL_ROTACION = 0.88
CANSANCIO_PARA_ROTAR = 0.5
PAUSA_ROTACION = 10000

# ============================================================
# 8d. Presentación: viento, cámara y animaciones
# ============================================================

# El viento cambia de dirección y fuerza cada tanto y empuja al balón
# libre; su fuerza máxima depende del clima (más tormenta, más viento).
INTERVALO_VIENTO = 8000

# Cámara dinámica: zoom hacia el balón cuando corre o ronda las áreas.
ZOOM_CAMARA = 0.9
ZOOM_CAMARA_VELOCIDAD = 260.0
ZOOM_CAMARA_AREA = 220.0
SUAVIZADO_ZOOM = 0.05
SUAVIZADO_CAMARA = 0.08

# ============================================================
# 9. Marcaje, colisiones y atajadas
# ============================================================

# Radio alrededor de la base de un defensa para asignarle un rival.
RADIO_MARCAJE = 220.0
# Distancia a la que el defensa se coloca del lado de su propio arco.
DESPLAZAMIENTO_MARCA = 2 * RADIO_JUGADOR + 4
# Separación suave entre jugadores que se superponen.
FACTOR_COLISION = 0.85
ITERACIONES_COLISION = 3
# Un portero atrapa un balón rápido que le llega dentro de este radio.
RADIO_ATAJADA = 34.0
VELOCIDAD_MINIMA_ATAJADA = 320.0
# Tiempo que el portero IA conserva el balón antes de despejar.
DURACION_POSESION_PORTERO = 900
FUERZA_DESPEJE_PORTERO = 620.0

# Porteros inteligentes: anticipación, lances y errores.
# Milisegundos que dura un lance y de enfriamiento antes del siguiente.
DURACION_LANCE_PORTERO = 450
ENFRIAMIENTO_LANCE = 650
# Desvío vertical (px) a partir del cual el portero se lanza.
UMBRAL_LANCE_Y = 16.0
# Solo se lanza si el disparo llegará a su línea antes de este tiempo (s).
TIEMPO_LLEGADA_LANCE = 0.9
# Píxeles que puede adelantarse o retrasarse de su línea en el lance.
MARGEN_LANCE_X = 36.0
# Error máximo de predicción (px) de un portero con la peor calidad.
DESVIO_ERROR_PORTERO = 120.0

# ============================================================
# 10. Disparo de la IA
# ============================================================

DISTANCIA_DISPARO_IA = 220.0
TIEMPO_MINIMO_POSESION_IA = 450
FACTOR_APUNTADO_DISPARO = 0.7
# El portero se considera centrado (y la IA tira al palo más lejano al
# propio tirador) si está a menos de esta distancia del centro del arco.
PORTERO_CENTRADO_TOLERANCIA = 12.0

# ============================================================
# 11. Audio
# ============================================================

FRECUENCIA_AUDIO = 22050
VOLUMEN_SILBATO = 0.35
VOLUMEN_GOL = 0.50
VOLUMEN_PASE = 0.25
VOLUMEN_DISPARO = 0.40

# ============================================================
# 12. Textos
# ============================================================

# La ayuda se dibuja en dos líneas para que quepa en la ventana.
TEXTO_AYUDA = (
    "WASD/Flechas: mover | SHIFT: sprintar | ESPACIO: chutar",
    "E: pasar | Q: cambiar jugador | R: repetir gol | ESC: pausa | F3: rendimiento",
)
TEXTO_CONTINUAR = "Pulsa ESPACIO para continuar"
TEXTO_ENTRETIEMPO = "Pulsa ESPACIO para el segundo tiempo"
TEXTO_FINAL = "Pulsa ESPACIO para el siguiente nivel"

# Comentarios del narrador al marcar gol; ``{jugador}`` se sustituye
# por el nombre de quien tocó el balón por última vez.
TEXTOS_NARRADOR: tuple[str, ...] = (
    "¡GOOOL DE {jugador}!",
    "¡{jugador} no perdona!",
    "¡Qué definición la de {jugador}!",
    "¡{jugador} hace estremecer el estadio!",
    "¡GOLAZO! {jugador} lo manda a guardar",
    "¡{jugador} rompe la red!",
)
MENSAJE_GOL: dict[Equipo, str] = {
    Equipo.LOCAL: "¡GOOOL DEL LOCAL!",
    Equipo.VISITANTE: "GOL DEL VISITANTE...",
}
MENSAJE_ENTRETIEMPO = "ENTRETIEMPO"
MENSAJE_FINAL = "FINAL"
MENSAJE_REPETICION = "REPETICIÓN"
MENSAJE_CORNER = "CÓRNER"
TEXTO_SALTAR_REPETICION = "Pulsa ESPACIO para saltar la repetición"

# ============================================================
# 13. Formación
# ============================================================


class PosicionFormacion(NamedTuple):
    """Rol y posición relativa (0-1) de un jugador en la formación."""

    rol: Rol
    x: float
    y: float


# ============================================================
# Tácticas y formaciones
# ============================================================

# El visitante usa la formación elegida reflejada en horizontal.
FORMACION_442: tuple[PosicionFormacion, ...] = (
    PosicionFormacion(Rol.PORTERO, 0.05, 0.50),
    PosicionFormacion(Rol.DEFENSA, 0.22, 0.20),
    PosicionFormacion(Rol.DEFENSA, 0.22, 0.40),
    PosicionFormacion(Rol.DEFENSA, 0.22, 0.60),
    PosicionFormacion(Rol.DEFENSA, 0.22, 0.80),
    PosicionFormacion(Rol.MEDIO, 0.45, 0.20),
    PosicionFormacion(Rol.MEDIO, 0.45, 0.40),
    PosicionFormacion(Rol.MEDIO, 0.45, 0.60),
    PosicionFormacion(Rol.MEDIO, 0.45, 0.80),
    PosicionFormacion(Rol.DELANTERO, 0.65, 0.40),
    PosicionFormacion(Rol.DELANTERO, 0.65, 0.60),
)

FORMACION_433: tuple[PosicionFormacion, ...] = (
    PosicionFormacion(Rol.PORTERO, 0.05, 0.50),
    PosicionFormacion(Rol.DEFENSA, 0.22, 0.15),
    PosicionFormacion(Rol.DEFENSA, 0.22, 0.38),
    PosicionFormacion(Rol.DEFENSA, 0.22, 0.62),
    PosicionFormacion(Rol.DEFENSA, 0.22, 0.85),
    PosicionFormacion(Rol.MEDIO, 0.42, 0.50),
    PosicionFormacion(Rol.MEDIO, 0.52, 0.28),
    PosicionFormacion(Rol.MEDIO, 0.52, 0.72),
    PosicionFormacion(Rol.DELANTERO, 0.68, 0.20),
    PosicionFormacion(Rol.DELANTERO, 0.72, 0.50),
    PosicionFormacion(Rol.DELANTERO, 0.68, 0.80),
)

FORMACION_352: tuple[PosicionFormacion, ...] = (
    PosicionFormacion(Rol.PORTERO, 0.05, 0.50),
    PosicionFormacion(Rol.DEFENSA, 0.22, 0.25),
    PosicionFormacion(Rol.DEFENSA, 0.20, 0.50),
    PosicionFormacion(Rol.DEFENSA, 0.22, 0.75),
    PosicionFormacion(Rol.MEDIO, 0.40, 0.12),
    PosicionFormacion(Rol.MEDIO, 0.45, 0.32),
    PosicionFormacion(Rol.MEDIO, 0.38, 0.50),
    PosicionFormacion(Rol.MEDIO, 0.45, 0.68),
    PosicionFormacion(Rol.MEDIO, 0.40, 0.88),
    PosicionFormacion(Rol.DELANTERO, 0.68, 0.40),
    PosicionFormacion(Rol.DELANTERO, 0.68, 0.60),
)

FORMACION_532: tuple[PosicionFormacion, ...] = (
    PosicionFormacion(Rol.PORTERO, 0.05, 0.50),
    PosicionFormacion(Rol.DEFENSA, 0.24, 0.10),
    PosicionFormacion(Rol.DEFENSA, 0.22, 0.30),
    PosicionFormacion(Rol.DEFENSA, 0.20, 0.50),
    PosicionFormacion(Rol.DEFENSA, 0.22, 0.70),
    PosicionFormacion(Rol.DEFENSA, 0.24, 0.90),
    PosicionFormacion(Rol.MEDIO, 0.45, 0.30),
    PosicionFormacion(Rol.MEDIO, 0.42, 0.50),
    PosicionFormacion(Rol.MEDIO, 0.45, 0.70),
    PosicionFormacion(Rol.DELANTERO, 0.68, 0.40),
    PosicionFormacion(Rol.DELANTERO, 0.68, 0.60),
)

# Catálogo de tácticas: añadir aquí una formación nueva basta para que
# aparezca en el menú de tácticas y sea valida en el resto del juego.
FORMACIONES: dict[str, tuple[PosicionFormacion, ...]] = {
    "4-4-2": FORMACION_442,
    "4-3-3": FORMACION_433,
    "3-5-2": FORMACION_352,
    "5-3-2": FORMACION_532,
}

# Nombres derivados del catálogo, en su orden de inserción.
NOMBRES_FORMACION: tuple[str, ...] = tuple(FORMACIONES)

# Formación por defecto, para el código que no indica una táctica.
FORMACION: tuple[PosicionFormacion, ...] = FORMACION_442


def formacion_por_nombre(
    nombre: str,
) -> tuple[PosicionFormacion, ...]:
    """Devuelve la formación pedida, con la 4-4-2 como alternativa."""
    return FORMACIONES.get(nombre, FORMACION)


# ============================================================
# 14. Suplentes y sustituciones
# ============================================================

# Los once primeros huecos de la plantilla son titulares (la formación).
TITULARES_POR_EQUIPO = len(FORMACION)

# Tamaño del banquillo: la plantilla completa queda en 18 futbolistas
# (11 titulares + 7 suplentes), dentro del formato 18-23 del fútbol.
NUMERO_SUPLENTES = 7

# Máximo del formato del acta: 11 titulares + 12 suplentes. El sistema
# admite banquillos hasta este tamaño aunque el juego arranque con 7.
PLANTILLA_MAXIMA = TITULARES_POR_EQUIPO + 12

# Cambios que puede hacer cada equipo por partido.
SUSTITUCIONES_MAXIMAS = 5

# Punto hacia el que conduce el balón la IA visitante: un poco más allá
# de la línea de gol izquierda, a la altura del centro de la portería.
OBJETIVO_ATAQUE_IA = pygame.Vector2(
    CAMPO_RECT.left - 10,
    PORTERIA_CENTRO,
)
