"""Efectos de sonido sintetizados, sin assets externos."""

from __future__ import annotations

import math
from array import array
from collections.abc import Callable, Sequence

import pygame

from .configuracion import (
    FRECUENCIA_AUDIO,
    VOLUMEN_DISPARO,
    VOLUMEN_GOL,
    VOLUMEN_PASE,
    VOLUMEN_SILBATO,
)


def _onda_seno(angulo: float) -> float:
    return math.sin(angulo)


def _onda_cuadrada(angulo: float) -> float:
    return 1.0 if math.sin(angulo) >= 0.0 else -1.0


def _onda_triangulo(angulo: float) -> float:
    return (2.0 / math.pi) * math.asin(math.sin(angulo))


ONDAS: dict[str, Callable[[float], float]] = {
    "seno": _onda_seno,
    "cuadrada": _onda_cuadrada,
    "triangulo": _onda_triangulo,
}


class Sonidos:
    """Efectos de sonido sintetizados, sin assets externos.

    Si el mixer no está disponible o no usa muestras de 16 bits con
    signo, todos los métodos quedan como no-op.
    """

    def __init__(self) -> None:
        self.disponible = False
        self.habilitado = True
        self._efectos: dict[str, pygame.mixer.Sound] = {}
        self._frecuencia = FRECUENCIA_AUDIO
        self._canales = 1

        if not self._inicializar_mixer():
            return

        try:
            self._efectos = self._crear_efectos()
        except (pygame.error, ValueError, OverflowError):
            self._efectos.clear()
            return

        self.disponible = True

    def silbato(self) -> None:
        self._reproducir("silbato")

    def gol(self) -> None:
        self._reproducir("gol")

    def pase(self) -> None:
        self._reproducir("pase")

    def disparo(self) -> None:
        self._reproducir("disparo")

    def _inicializar_mixer(self) -> bool:
        """Comprueba que el mixer use el formato esperado."""
        try:
            inicializacion = pygame.mixer.get_init()
        except pygame.error:
            return False

        if inicializacion is None:
            return False

        frecuencia, tamano, canales = inicializacion

        if tamano != -16:
            return False

        self._frecuencia = frecuencia
        self._canales = max(1, canales)
        return True

    def _crear_efectos(self) -> dict[str, pygame.mixer.Sound]:
        """Genera todos los efectos una sola vez al arrancar."""
        return {
            "silbato": self._crear_sound(
                self._arpegio(
                    [1760.0, 2217.0, 1760.0, 2217.0],
                    0.055,
                    VOLUMEN_SILBATO,
                    "triangulo",
                )
            ),
            "gol": self._crear_sound(
                self._arpegio(
                    [523.25, 659.25, 783.99, 1046.50],
                    0.11,
                    VOLUMEN_GOL,
                    "triangulo",
                )
            ),
            "pase": self._crear_sound(
                self._tono(620.0, 0.055, VOLUMEN_PASE)
            ),
            "disparo": self._crear_sound(
                self._arpegio(
                    [220.0, 140.0],
                    0.045,
                    VOLUMEN_DISPARO,
                    "triangulo",
                )
            ),
        }

    def _reproducir(self, nombre: str) -> None:
        if not self.disponible or not self.habilitado:
            return

        sonido = self._efectos.get(nombre)

        if sonido is None:
            return

        try:
            sonido.play()
        except pygame.error:
            self.disponible = False

    def _tono(
        self,
        frecuencia: float,
        duracion: float,
        volumen: float,
        forma: str = "seno",
        ataque: float = 0.008,
        caida: float = 0.025,
    ) -> array:
        """Genera una nota mono de 16 bits con signo."""
        total = max(1, int(self._frecuencia * duracion))
        muestras_ataque = max(1, int(self._frecuencia * ataque))
        muestras_caida = max(1, int(self._frecuencia * caida))
        generar_onda = ONDAS.get(forma, _onda_seno)
        incremento = math.tau * frecuencia / self._frecuencia
        datos = array("h")
        angulo = 0.0

        for indice in range(total):
            valor = generar_onda(angulo)
            envolvente = 1.0

            if indice < muestras_ataque:
                envolvente = indice / muestras_ataque

            restantes = total - indice

            if restantes < muestras_caida:
                envolvente = min(envolvente, restantes / muestras_caida)

            datos.append(int(32767 * volumen * envolvente * valor))
            angulo = (angulo + incremento) % math.tau

        return datos

    def _arpegio(
        self,
        frecuencias: Sequence[float],
        duracion_nota: float,
        volumen: float,
        forma: str = "seno",
    ) -> array:
        """Encadena varias notas para formar un efecto."""
        datos = array("h")

        for frecuencia in frecuencias:
            datos.extend(
                self._tono(
                    frecuencia,
                    duracion_nota,
                    volumen,
                    forma,
                )
            )

        return datos

    def _crear_sound(self, muestras: array) -> pygame.mixer.Sound:
        """Convierte muestras mono al formato real del mixer."""
        if self._canales > 1:
            canales = array("h")

            for muestra in muestras:
                for _ in range(self._canales):
                    canales.append(muestra)

            muestras = canales

        return pygame.mixer.Sound(buffer=muestras.tobytes())
