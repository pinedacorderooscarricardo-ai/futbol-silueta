"""Punto de entrada de Fútbol Silueta.

Ejecuta este archivo desde la carpeta del proyecto:

    python main.py

Controles durante el partido:
    WASD / flechas : mover al jugador controlado.
    SHIFT          : sprintar mientras quede energía.
    ESPACIO        : chutar o continuar tras un gol, descanso o final.
    E              : pasar al compañero más cercano.
    ESC            : abrir el menú de pausa.

En los menús se puede usar el ratón o las flechas y ENTER.
"""

from __future__ import annotations

import sys

import pygame

from futbol_silueta.aplicacion import Aplicacion
from futbol_silueta.configuracion import (
    ALTO,
    ANCHO,
    FRECUENCIA_AUDIO,
)


def main() -> int:
    """Inicializa pygame, crea la ventana y arranca la aplicación."""
    try:
        pygame.mixer.pre_init(FRECUENCIA_AUDIO, -16, 1, 512)
    except pygame.error:
        pass

    pygame.init()

    try:
        pantalla = pygame.display.set_mode((ANCHO, ALTO))
        Aplicacion(pantalla).ejecutar()
    finally:
        pygame.quit()

    return 0


if __name__ == "__main__":
    sys.exit(main())
