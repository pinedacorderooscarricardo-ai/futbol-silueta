"""Estadísticas del partido, tabla de posiciones, historial y trofeos.

Reúne lo que se mide de una campaña: las cifras del partido en curso
(posesión, disparos, pases y atajadas, que la vista muestra en el
descanso y el final), la tabla de puntos contra cada rival del
circuito, los resultados anteriores y los trofeos por logros.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .configuracion import Equipo
from .niveles import NIVEL_MAXIMO

if TYPE_CHECKING:
    from .juego import Juego
    from .menus import Menus

CLAVE_LOCAL = "local"
MAX_HISTORIAL = 20


# --------------------------------------------------
# Estadísticas del partido en curso
# --------------------------------------------------


class EstadisticasPartido:
    """Cifras del partido: posesión, disparos, pases y atajadas."""

    def __init__(self) -> None:
        self.reiniciar()

    def reiniciar(self) -> None:
        self.posesion: dict[Equipo, float] = {
            Equipo.LOCAL: 0.0,
            Equipo.VISITANTE: 0.0,
        }
        self.disparos: dict[Equipo, int] = {
            Equipo.LOCAL: 0,
            Equipo.VISITANTE: 0,
        }
        self.pases: dict[Equipo, int] = {
            Equipo.LOCAL: 0,
            Equipo.VISITANTE: 0,
        }
        self.atajadas: dict[Equipo, int] = {
            Equipo.LOCAL: 0,
            Equipo.VISITANTE: 0,
        }

    def acumular_posesion(self, portador: object, dt: float) -> None:
        """Suma el fotograma al equipo que conduce el balón."""
        equipo = getattr(portador, "equipo", None)

        if equipo is not None:
            self.posesion[equipo] += dt

    def contar_disparo(self, equipo: Equipo) -> None:
        self.disparos[equipo] += 1

    def contar_pase(self, equipo: Equipo) -> None:
        self.pases[equipo] += 1

    def contar_atajada(self, equipo: Equipo) -> None:
        self.atajadas[equipo] += 1

    def posesion_en_porcentaje(self) -> tuple[int, int]:
        """Reparto de la posesión redondeado (local, visitante)."""
        total = self.posesion[Equipo.LOCAL] + self.posesion[Equipo.VISITANTE]

        if total <= 0.0:
            return (50, 50)

        local = round(100 * self.posesion[Equipo.LOCAL] / total)
        return (local, 100 - local)

    def lineas(self) -> tuple[str, ...]:
        """Líneas del panel de descanso y final, LOCAL - VISITANTE."""
        posesion_local, posesion_visitante = self.posesion_en_porcentaje()
        return (
            f"Posesión {posesion_local}% - {posesion_visitante}%",
            f"Disparos {self.disparos[Equipo.LOCAL]} - "
            f"{self.disparos[Equipo.VISITANTE]}",
            f"Pases {self.pases[Equipo.LOCAL]} - "
            f"{self.pases[Equipo.VISITANTE]}",
            f"Atajadas {self.atajadas[Equipo.LOCAL]} - "
            f"{self.atajadas[Equipo.VISITANTE]}",
        )


# --------------------------------------------------
# Tabla de posiciones de la campaña
# --------------------------------------------------


@dataclass
class FilaPosiciones:
    """Acumulado de un equipo: jugados, resultados y puntos."""

    pj: int = 0
    g: int = 0
    e: int = 0
    p: int = 0
    gf: int = 0
    gc: int = 0
    puntos: int = 0


class TablaPosiciones:
    """Puntos de la campaña: el club local contra cada rival.

    Las filas se identifican con ``"local"`` y con el número del nivel
    rival (``"1"`` a ``"11"``), así se guardan y cargan de la base.
    """

    def __init__(self) -> None:
        self.filas: dict[str, FilaPosiciones] = {}

    def fila(self, clave: str) -> FilaPosiciones:
        """La fila del equipo, creándola a ceros si no existía."""
        fila = self.filas.get(clave)

        if fila is None:
            fila = FilaPosiciones()
            self.filas[clave] = fila

        return fila

    def registrar(
        self,
        nivel: int,
        goles_local: int,
        goles_visitante: int,
    ) -> None:
        """Anota el resultado del nivel en las dos filas."""
        local = self.fila(CLAVE_LOCAL)
        rival = self.fila(str(nivel))

        local.pj += 1
        rival.pj += 1
        local.gf += goles_local
        local.gc += goles_visitante
        rival.gf += goles_visitante
        rival.gc += goles_local

        if goles_local > goles_visitante:
            local.g += 1
            rival.p += 1
            local.puntos += 3
        elif goles_local < goles_visitante:
            rival.g += 1
            local.p += 1
            rival.puntos += 3
        else:
            local.e += 1
            rival.e += 1
            local.puntos += 1
            rival.puntos += 1

    def filas_de_campana(self) -> list[tuple[str, FilaPosiciones]]:
        """Las doce filas (local + rivales), por puntos y diferencia."""
        self.fila(CLAVE_LOCAL)

        for nivel in range(1, NIVEL_MAXIMO + 1):
            self.fila(str(nivel))

        return sorted(
            self.filas.items(),
            key=lambda par: (
                par[1].puntos,
                par[1].gf - par[1].gc,
                par[1].gf,
            ),
            reverse=True,
        )


# --------------------------------------------------
# Historial de resultados
# --------------------------------------------------


@dataclass
class Resultado:
    """El marcador final de un partido de la campaña."""

    nivel: int
    goles_local: int
    goles_visitante: int


def registrar_en_historial(
    historial: list[Resultado],
    resultado: Resultado,
) -> None:
    """Deja el resultado primero y conserva solo los últimos."""
    historial.insert(0, resultado)
    del historial[MAX_HISTORIAL:]


# --------------------------------------------------
# Trofeos por logros
# --------------------------------------------------


@dataclass(frozen=True)
class Trofeo:
    """Un premio desbloqueable de la campaña."""

    id: str
    nombre: str
    descripcion: str


TROFEOS: tuple[Trofeo, ...] = (
    Trofeo("primera_victoria", "PRIMERA VICTORIA", "Gana tu primer partido"),
    Trofeo("goleada", "GOLEADA", "Gana por 3 o más goles de diferencia"),
    Trofeo("valla_invicta", "VALLA INVICTA", "Gana sin recibir goles"),
    Trofeo("artillero", "ARTILLERO", "Marca 5 goles en un partido"),
    Trofeo("campeon", "CAMPEÓN", "Completa la campaña: gana el nivel 11"),
)


def evaluar_trofeos(
    goles_local: int,
    goles_visitante: int,
    nivel: int,
    desbloqueados: set[str],
) -> list[Trofeo]:
    """Los trofeos que gana el resultado, marcándolos como logrados."""
    gano = goles_local > goles_visitante
    condiciones = {
        "primera_victoria": gano,
        "goleada": goles_local - goles_visitante >= 3,
        "valla_invicta": gano and goles_visitante == 0,
        "artillero": goles_local >= 5,
        "campeon": gano and nivel >= NIVEL_MAXIMO,
    }
    nuevos = [
        trofeo
        for trofeo in TROFEOS
        if condiciones[trofeo.id] and trofeo.id not in desbloqueados
    ]
    desbloqueados.update(trofeo.id for trofeo in nuevos)
    return nuevos


# --------------------------------------------------
# Registro del resultado de un partido
# --------------------------------------------------


def registrar_resultado(menus: Menus, juego: Juego) -> list[Trofeo]:
    """Anota el partido finalizado en tabla, historial y trofeos.

    Devuelve los trofeos recién desbloqueados para anunciarlos en el
    panel del final del partido.
    """
    menus.tabla_posiciones.registrar(
        juego.nivel,
        juego.goles_local,
        juego.goles_visitante,
    )
    registrar_en_historial(
        menus.historial,
        Resultado(juego.nivel, juego.goles_local, juego.goles_visitante),
    )
    return evaluar_trofeos(
        juego.goles_local,
        juego.goles_visitante,
        juego.nivel,
        menus.trofeos,
    )
