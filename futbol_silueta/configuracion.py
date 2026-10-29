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
TITULO_VENTANA = "Fútbol Silueta - 22 jugadores"

Color = tuple[int, int, int]

# ============================================================
# 2. Colores
# ============================================================

VERDE: Color = (34, 139, 34)
BLANCO: Color = (255, 255, 255)
ROJO: Color = (200, 40, 40)
AZUL: Color = (40, 80, 200)
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

COLOR_EQUIPO: dict[Equipo, Color] = {
    Equipo.LOCAL: ROJO,
    Equipo.VISITANTE: AZUL,
}

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
DURACION_MITAD = 3 * 60 * 1000

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

# ============================================================
# 10. Disparo de la IA
# ============================================================

DISTANCIA_DISPARO_IA = 220.0
TIEMPO_MINIMO_POSESION_IA = 450
FACTOR_APUNTADO_DISPARO = 0.7

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

TEXTO_AYUDA = (
    "WASD/Flechas: mover | SHIFT: sprintar | "
    "ESPACIO: chutar | E: pasar | ESC: pausa"
)
TEXTO_CONTINUAR = "Pulsa ESPACIO para continuar"
TEXTO_ENTRETIEMPO = "Pulsa ESPACIO para el segundo tiempo"
TEXTO_FINAL = "Pulsa ESPACIO para la revancha"
MENSAJE_GOL: dict[Equipo, str] = {
    Equipo.LOCAL: "¡GOOOL DEL ROJO!",
    Equipo.VISITANTE: "GOL DEL AZUL...",
}
MENSAJE_ENTRETIEMPO = "ENTRETIEMPO"
MENSAJE_FINAL = "FINAL"

# ============================================================
# 13. Formación
# ============================================================


class PosicionFormacion(NamedTuple):
    """Rol y posición relativa (0-1) de un jugador en la formación."""

    rol: Rol
    x: float
    y: float


# El visitante usa esta misma formación reflejada en horizontal.
FORMACION: tuple[PosicionFormacion, ...] = (
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

# Punto hacia el que conduce el balón la IA visitante: un poco más allá
# de la línea de gol izquierda, a la altura del centro de la portería.
OBJETIVO_ATAQUE_IA = pygame.Vector2(
    CAMPO_RECT.left - 10,
    PORTERIA_CENTRO,
)
