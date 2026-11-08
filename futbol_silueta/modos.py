"""Modos de juego y torneos: liga, copa, campeones y supervivencia.

El modo :attr:`ModoJuego.CAMPANA` es el clásico de niveles; el resto
organiza varios partidos alrededor del mismo motor de partido. Los
torneos (y su progreso) se guardan en la base de datos entre sesiones:
al elegir un modo se reanuda el torneo que tenía guardado, si lo hay.

Los rivales se identifican por su número de nivel (1..11): cada equipo
rival es un club con su escudo y su dificultad, igual que en la
campaña. El equipo del jugador es el 0.
"""

from __future__ import annotations

import random
from enum import StrEnum

from .niveles import NIVEL_MAXIMO
from .utilidades import acotar

JUGADOR = 0
FUERZA_JUGADOR = 5.5  # Fuerza del equipo del jugador en los sorteos.
PARTIDOS_POR_GANADO = 3
PARTIDO_POR_EMPATE = 1


class ModoJuego(StrEnum):
    """Modos entre los que puede elegir el jugador."""

    CAMPANA = "campana"
    LIGA = "liga"
    COPA = "copa"
    CAMPEONES = "campeones"
    SUPERVIVENCIA = "supervivencia"
    ENTRENAMIENTO = "entrenamiento"
    DOS_JUGADORES = "dos_jugadores"


ETIQUETAS: dict[ModoJuego, str] = {
    ModoJuego.CAMPANA: "Campaña",
    ModoJuego.LIGA: "Liga",
    ModoJuego.COPA: "Copa",
    ModoJuego.CAMPEONES: "Copa de Campeones",
    ModoJuego.SUPERVIVENCIA: "Supervivencia",
    ModoJuego.ENTRENAMIENTO: "Entrenamiento",
    ModoJuego.DOS_JUGADORES: "Dos jugadores",
}

DESCRIPCIONES: dict[ModoJuego, str] = {
    ModoJuego.CAMPANA: "Los once niveles de la campaña, uno tras otro",
    ModoJuego.LIGA: "Todos contra todos: once jornadas por puntos",
    ModoJuego.COPA: "Torneo de eliminación directa: cuartos, semis y final",
    ModoJuego.CAMPEONES: "Dos grupos, semifinales y gran final",
    ModoJuego.SUPERVIVENCIA: "Gana y la dificultad sube; pierde y se acaba",
    ModoJuego.ENTRENAMIENTO: "Campo abierto para tiros, pases y regates",
    ModoJuego.DOS_JUGADORES: "Dos personas en el mismo teclado",
}


class Solicitud(StrEnum):
    """Petición del partido hacia la aplicación."""

    MENU_PRINCIPAL = "menu_principal"


class _Stats:
    """Acumulador de una fila de la clasificación."""

    __slots__ = ("pj", "pg", "pe", "pp", "gf", "gc", "puntos")

    def __init__(self) -> None:
        self.pj = 0
        self.pg = 0
        self.pe = 0
        self.pp = 0
        self.gf = 0
        self.gc = 0
        self.puntos = 0

    def registrar(self, gfavor: int, gcontra: int) -> None:
        self.pj += 1
        self.gf += gfavor
        self.gc += gcontra

        if gfavor > gcontra:
            self.pg += 1
            self.puntos += PARTIDOS_POR_GANADO
        elif gfavor == gcontra:
            self.pe += 1
            self.puntos += PARTIDO_POR_EMPATE
        else:
            self.pp += 1

    def serializar(self) -> dict[str, int]:
        """Fila lista para guardar en la base de datos."""
        return {campo: getattr(self, campo) for campo in self.__slots__}

    @classmethod
    def deserializar(cls, datos: dict[str, int]) -> "_Stats":
        """Reconstruye una fila desde su diccionario guardado."""
        stats = cls()

        for campo in cls.__slots__:
            setattr(stats, campo, int(datos[campo]))

        return stats


def _calendario_round_robin(equipos: list[int]) -> list[list[tuple[int, int]]]:
    """Calendario todos contra todos por el método del círculo.

    Con un número par de equipos genera ``n - 1`` jornadas con ``n / 2``
    partidos cada una, y todos se enfrentan una vez.
    """
    lista = list(equipos)
    fijo = lista[0]
    rotantes = lista[1:]
    jornadas: list[list[tuple[int, int]]] = []

    for _ in range(len(equipos) - 1):
        bloque = [fijo] + rotantes
        partidos = [
            (bloque[indice], bloque[-1 - indice])
            for indice in range(len(equipos) // 2)
        ]
        jornadas.append(partidos)
        rotantes = [rotantes[-1]] + rotantes[:-1]

    return jornadas


def _simular(local: int, visitante: int) -> tuple[int, int]:
    """Resultado simulado de un partido entre dos equipos por fuerza.

    La fuerza de cada equipo es su nivel (el jugador usa una fuerza
    media). Devuelve los goles de local y visitante.
    """
    def goles(favorable: float, desfavorable: float) -> int:
        esperados = max(0.3, 0.9 + 0.3 * (favorable - desfavorable))
        return max(0, round(random.gauss(esperados, 0.9)))

    fuerza = {JUGADOR: FUERZA_JUGADOR}

    def nivel_de(equipo: int) -> float:
        return fuerza.get(equipo, float(equipo))

    return goles(nivel_de(local), nivel_de(visitante)), goles(
        nivel_de(visitante),
        nivel_de(local),
    )


def _ordenar_tabla(tabla: dict[int, _Stats]) -> list[tuple[int, _Stats]]:
    """Clasificación ordenada por puntos, diferencia de goles y goles."""
    return sorted(
        tabla.items(),
        key=lambda par: (
            -par[1].puntos,
            -(par[1].gf - par[1].gc),
            -par[1].gf,
        ),
    )


class TorneoBase:
    """Protocolo común de los torneos que gestiona el partido."""

    def rival_del_partido(self) -> int:
        """Nivel del rival del partido que se va a jugar ahora."""
        raise NotImplementedError

    def etiqueta(self) -> str:
        """Texto corto para el marcador: competición y ronda."""
        raise NotImplementedError

    def registrar(self, goles_local: int, goles_visitante: int) -> None:
        """Registra el resultado del partido que acaba de terminar."""
        raise NotImplementedError

    @property
    def terminado(self) -> bool:
        raise NotImplementedError

    def texto_tras_partido(self) -> str:
        """Texto para la pantalla final de un partido intermedio."""
        raise NotImplementedError

    def texto_final_torneo(self) -> str:
        """Texto para la pantalla final del torneo completo."""
        raise NotImplementedError

    def serializar(self) -> dict[str, object]:
        """Estado del torneo listo para la base de datos."""
        raise NotImplementedError

    def restaurar(self, datos: dict[str, object]) -> None:
        """Recupera el estado guardado; los calendarios se recalculan."""
        raise NotImplementedError


class Liga(TorneoBase):
    """Liga a una vuelta contra los once rivales, por puntos.

    Además del partido del jugador se simulan los demás enfrentamientos
    de cada jornada, así que la clasificación es una tabla real.
    """

    def __init__(self) -> None:
        # Rivales invertidos: el calendario arranca contra el más flojo
        # y la dificultad crece jornada a jornada.
        equipos = [JUGADOR] + list(range(NIVEL_MAXIMO, 0, -1))
        self.calendario = _calendario_round_robin(equipos)
        self.jornada = 0
        self.tabla: dict[int, _Stats] = {
            equipo: _Stats() for equipo in equipos
        }

    def rival_del_partido(self) -> int:
        for local, visitante in self.calendario[self.jornada]:
            if local is JUGADOR:
                return visitante
            if visitante is JUGADOR:
                return local

        raise AssertionError("jornada sin partido del jugador")

    def etiqueta(self) -> str:
        return f"LIGA · J{self.jornada + 1}/{len(self.calendario)}"

    def registrar(self, goles_local: int, goles_visitante: int) -> None:
        if self.terminado:
            return

        for local, visitante in self.calendario[self.jornada]:
            if local is JUGADOR or visitante is JUGADOR:
                gl, gv = goles_local, goles_visitante
            else:
                gl, gv = _simular(local, visitante)

            self.tabla[local].registrar(gl, gv)
            self.tabla[visitante].registrar(gv, gl)

        self.jornada += 1

    @property
    def terminado(self) -> bool:
        return self.jornada >= len(self.calendario)

    def _posicion(self) -> tuple[int, _Stats]:
        clasificacion = _ordenar_tabla(self.tabla)

        for posicion, (equipo, stats) in enumerate(clasificacion, start=1):
            if equipo is JUGADOR:
                return posicion, stats

        raise AssertionError("el jugador no está en la tabla")

    def texto_tras_partido(self) -> str:
        posicion, stats = self._posicion()
        return (
            f"Jornada {self.jornada}/{len(self.calendario)}: "
            f"{posicion}º con {stats.puntos} pts"
        )

    def texto_final_torneo(self) -> str:
        posicion, stats = self._posicion()

        if posicion == 1:
            return f"¡CAMPEÓN DE LIGA con {stats.puntos} puntos!"

        return f"LIGA TERMINADA: {posicion}º con {stats.puntos} puntos"

    def clasificacion_texto(self, filas: int = 4) -> list[str]:
        """Primeras filas de la tabla, para mostrar en pantalla."""
        texto: list[str] = []

        for posicion, (_equipo, stats) in enumerate(
            _ordenar_tabla(self.tabla)[:filas],
            start=1,
        ):
            texto.append(
                f"{posicion}. {stats.puntos} pts  "
                f"({stats.pg}-{stats.pe}-{stats.pp})"
            )

        return texto

    def serializar(self) -> dict[str, object]:
        return {
            "jornada": self.jornada,
            "tabla": {
                str(equipo): stats.serializar()
                for equipo, stats in self.tabla.items()
            },
        }

    def restaurar(self, datos: dict[str, object]) -> None:
        self.jornada = int(
            acotar(int(datos["jornada"]), 0, len(self.calendario))
        )
        self.tabla = {
            int(equipo): _Stats.deserializar(fila)
            for equipo, fila in datos["tabla"].items()
        }


class Copa(TorneoBase):
    """Torneo de eliminación directa de ocho equipos.

    El jugador entra en cuartos contra el rival más flojo; los otros
    cruces se simulan. Un empate se decide por penaltis (sorteo).
    """

    RONDAS = ("Cuartos de final", "Semifinal", "Final")

    def __init__(self, rivales: tuple[int, ...] | None = None) -> None:
        if rivales is None:
            rivales = tuple(range(1, 8))

        assert len(rivales) == 7
        self._ronda = 0
        self._emparejamientos: list[tuple[int, int]] = [
            (JUGADOR, rivales[0]),
            (rivales[1], rivales[2]),
            (rivales[3], rivales[4]),
            (rivales[5], rivales[6]),
        ]
        self.eliminado = False

    def rival_del_partido(self) -> int:
        for local, visitante in self._emparejamientos:
            if local is JUGADOR:
                return visitante
            if visitante is JUGADOR:
                return local

        raise AssertionError("sin partido del jugador en esta ronda")

    def etiqueta(self) -> str:
        return f"COPA · {self.RONDAS[self._ronda]}"

    def registrar(self, goles_local: int, goles_visitante: int) -> None:
        if self.terminado:
            return

        ganadores: list[int] = []

        for local, visitante in self._emparejamientos:
            if local is JUGADOR or visitante is JUGADOR:
                gl, gv = goles_local, goles_visitante
            else:
                gl, gv = _simular(local, visitante)

            if gl > gv:
                ganador = local
            elif gv > gl:
                ganador = visitante
            else:
                # Penaltis: el rival más fuerte tiene ventaja.
                favorito = max(local, visitante)
                ganador = favorito if random.random() < 0.65 else min(
                    local,
                    visitante,
                )

            if JUGADOR in (local, visitante) and ganador is not JUGADOR:
                self.eliminado = True

            ganadores.append(ganador)

        self._ronda += 1

        if len(ganadores) > 1:
            self._emparejamientos = [
                (ganadores[indice], ganadores[indice + 1])
                for indice in range(0, len(ganadores), 2)
            ]
        else:
            # Torneo terminado: no quedan cruces por jugar.
            self._emparejamientos = []

    @property
    def terminado(self) -> bool:
        return self.eliminado or self._ronda >= len(self.RONDAS)

    def texto_tras_partido(self) -> str:
        if self.terminado:
            return self.texto_final_torneo()

        return f"Superaste los {self.RONDAS[self._ronda - 1].lower()}"

    def texto_final_torneo(self) -> str:
        if self.eliminado:
            return f"ELIMINADO en {self.RONDAS[self._ronda - 1].lower()}"

        return "¡CAMPEÓN DE LA COPA!"

    def serializar(self) -> dict[str, object]:
        return {
            "ronda": self._ronda,
            "emparejamientos": [
                list(cruce) for cruce in self._emparejamientos
            ],
            "eliminado": self.eliminado,
        }

    def restaurar(self, datos: dict[str, object]) -> None:
        self._ronda = int(
            acotar(int(datos["ronda"]), 0, len(self.RONDAS) - 1)
        )
        self._emparejamientos = [
            (int(local), int(visitante))
            for local, visitante in datos["emparejamientos"]
        ]
        self.eliminado = bool(datos["eliminado"])


class Campeones(TorneoBase):
    """Copa de Campeones: dos grupos de cuatro, semis y final.

    El jugador cae en el grupo A. Los partidos de los demás se simulan;
    los dos primeros de cada grupo pasan a las semifinales cruzadas
    (A1-B2 y B1-A2) y los ganadores juegan la final.
    """

    FASE_GRUPOS = 0
    FASE_SEMIS = 1
    FASE_FINAL = 2

    def __init__(self, rivales: tuple[int, ...] | None = None) -> None:
        if rivales is None:
            rivales = tuple(range(1, 8))

        assert len(rivales) == 7
        self.grupo_a = (JUGADOR, rivales[0], rivales[1], rivales[2])
        self.grupo_b = (rivales[3], rivales[4], rivales[5], rivales[6])
        self._fase = self.FASE_GRUPOS
        self._jornada = 0
        self.tabla_a: dict[int, _Stats] = {
            equipo: _Stats() for equipo in self.grupo_a
        }
        self.tabla_b: dict[int, _Stats] = {
            equipo: _Stats() for equipo in self.grupo_b
        }
        self._semifinales: tuple[tuple[int, int], tuple[int, int]] | None = None
        self._final: tuple[int, int] | None = None
        self._final_registrada = False
        self.campeon = False
        self.eliminado = False

    def _calendarios(self) -> tuple[list, list]:
        return (
            _calendario_round_robin(list(self.grupo_a)),
            _calendario_round_robin(list(self.grupo_b)),
        )

    def rival_del_partido(self) -> int:
        if self._fase is self.FASE_GRUPOS:
            calendario_a, _ = self._calendarios()

            for local, visitante in calendario_a[self._jornada]:
                if local is JUGADOR:
                    return visitante
                if visitante is JUGADOR:
                    return local

            raise AssertionError("jornada de grupo sin partido del jugador")

        if self._fase is self.FASE_SEMIS:
            assert self._semifinales is not None
            for local, visitante in self._semifinales:
                if local is JUGADOR:
                    return visitante
                if visitante is JUGADOR:
                    return local

            raise AssertionError("semifinal sin partido del jugador")

        assert self._final is not None
        return self._final[0] if JUGADOR is self._final[0] else self._final[1]

    def etiqueta(self) -> str:
        if self._fase is self.FASE_GRUPOS:
            return f"CAMPEONES · GRUPO A · J{self._jornada + 1}/3"

        if self._fase is self.FASE_SEMIS:
            return "CAMPEONES · SEMIFINAL"

        return "CAMPEONES · FINAL"

    def registrar(self, goles_local: int, goles_visitante: int) -> None:
        if self.terminado:
            return

        if self._fase is self.FASE_GRUPOS:
            calendario_a, calendario_b = self._calendarios()

            for grupo, calendario, tabla in (
                (self.grupo_a, calendario_a, self.tabla_a),
                (self.grupo_b, calendario_b, self.tabla_b),
            ):
                del grupo

                for local, visitante in calendario[self._jornada]:
                    if local is JUGADOR or visitante is JUGADOR:
                        gl, gv = goles_local, goles_visitante
                    else:
                        gl, gv = _simular(local, visitante)

                    tabla[local].registrar(gl, gv)
                    tabla[visitante].registrar(gv, gl)

            self._jornada += 1

            if self._jornada >= 3:
                self._clasificar_grupos()

            return

        if self._fase is self.FASE_SEMIS:
            assert self._semifinales is not None
            ganadores: list[int] = []

            for local, visitante in self._semifinales:
                if local is JUGADOR or visitante is JUGADOR:
                    gl, gv = goles_local, goles_visitante
                else:
                    gl, gv = _simular(local, visitante)

                if gl > gv:
                    ganador = local
                elif gv > gl:
                    ganador = visitante
                else:
                    # Sin empates en una semifinal: penaltis, con el
                    # rival más fuerte con ventaja.
                    favorito = max(local, visitante)
                    ganador = favorito if random.random() < 0.65 else min(
                        local,
                        visitante,
                    )

                if JUGADOR in (local, visitante) and ganador is not JUGADOR:
                    self.eliminado = True

                ganadores.append(ganador)

            self._final = (ganadores[0], ganadores[1])
            self._fase = self.FASE_FINAL
            return

        # Registro de la gran final.
        assert self._final is not None
        gl, gv = goles_local, goles_visitante

        if gl == gv:
            # Sin empates en una final: penaltis.
            favorito = max(self._final)
            ganador = favorito if random.random() < 0.65 else min(self._final)
        else:
            ganador = self._final[0] if gl > gv else self._final[1]

        self.campeon = ganador is JUGADOR
        self.eliminado = not self.campeon
        self._final_registrada = True

    def _clasificar_grupos(self) -> None:
        primeros = [e for e, _s in _ordenar_tabla(self.tabla_a)[:2]]
        segundos = [e for e, _s in _ordenar_tabla(self.tabla_b)[:2]]

        self._semifinales = (
            (primeros[0], segundos[1]),
            (segundos[0], primeros[1]),
        )
        self._fase = self.FASE_SEMIS

        if not any(JUGADOR in cruce for cruce in self._semifinales):
            self.eliminado = True

    @property
    def terminado(self) -> bool:
        if self.eliminado:
            return True

        return self._fase is self.FASE_FINAL and self._final_registrada

    def texto_tras_partido(self) -> str:
        if self._fase is self.FASE_GRUPOS:
            posicion = next(
                (
                    posicion
                    for posicion, (equipo, _stats) in enumerate(
                        _ordenar_tabla(self.tabla_a),
                        start=1,
                    )
                    if equipo is JUGADOR
                ),
                4,
            )
            return f"Grupo A: {posicion}º tras la jornada {self._jornada}/3"

        if self._fase is self.FASE_SEMIS and not self.eliminado:
            return "Semifinal superada: ¡a la final!"

        return self.texto_final_torneo()

    def texto_final_torneo(self) -> str:
        if self.campeon:
            return "¡CAMPEÓN DE LA COPA DE CAMPEONES!"

        if self._final_registrada:
            return "SUBCAMPEÓN: la final se te resistió"

        return "ELIMINADO: no pasaste de la fase de grupos"

    def serializar(self) -> dict[str, object]:
        return {
            "fase": self._fase,
            "jornada": self._jornada,
            "tabla_a": {
                str(equipo): stats.serializar()
                for equipo, stats in self.tabla_a.items()
            },
            "tabla_b": {
                str(equipo): stats.serializar()
                for equipo, stats in self.tabla_b.items()
            },
            "semifinales": (
                None
                if self._semifinales is None
                else [list(cruce) for cruce in self._semifinales]
            ),
            "final": None if self._final is None else list(self._final),
            "final_registrada": self._final_registrada,
            "campeon": self.campeon,
            "eliminado": self.eliminado,
        }

    def restaurar(self, datos: dict[str, object]) -> None:
        self._fase = int(
            acotar(int(datos["fase"]), self.FASE_GRUPOS, self.FASE_FINAL)
        )
        self._jornada = int(acotar(int(datos["jornada"]), 0, 3))
        self.tabla_a = {
            int(equipo): _Stats.deserializar(fila)
            for equipo, fila in datos["tabla_a"].items()
        }
        self.tabla_b = {
            int(equipo): _Stats.deserializar(fila)
            for equipo, fila in datos["tabla_b"].items()
        }
        semifinales = datos["semifinales"]
        self._semifinales = (
            None
            if semifinales is None
            else tuple(
                (int(local), int(visitante))
                for local, visitante in semifinales
            )
        )
        final = datos["final"]
        self._final = (
            None if final is None else (int(final[0]), int(final[1]))
        )
        self._final_registrada = bool(datos["final_registrada"])
        self.campeon = bool(datos["campeon"])
        self.eliminado = bool(datos["eliminado"])


class Supervivencia(TorneoBase):
    """Partidos consecutivos con dificultad creciente.

    Cada victoria suma una racha y sube el nivel del rival; una derrota
    (o un empate) termina el intento.
    """

    def __init__(self) -> None:
        self.racha = 0
        self.acabado = False

    def rival_del_partido(self) -> int:
        return min(NIVEL_MAXIMO, 1 + self.racha)

    def etiqueta(self) -> str:
        return f"SUPERVIVENCIA · Racha {self.racha}"

    def registrar(self, goles_local: int, goles_visitante: int) -> None:
        if self.terminado:
            return

        if goles_local > goles_visitante:
            self.racha += 1
        else:
            self.acabado = True

    @property
    def terminado(self) -> bool:
        return self.acabado

    def texto_tras_partido(self) -> str:
        if self.terminado:
            return self.texto_final_torneo()

        return f"Racha de {self.racha}: el rival sube al nivel {self.rival_del_partido()}"

    def texto_final_torneo(self) -> str:
        return f"SUPERVIVENCIA TERMINADA: racha de {self.racha}"

    def serializar(self) -> dict[str, object]:
        return {"racha": self.racha, "acabado": self.acabado}

    def restaurar(self, datos: dict[str, object]) -> None:
        self.racha = int(datos["racha"])
        self.acabado = bool(datos["acabado"])


def serializar_torneo(torneo: TorneoBase | None) -> dict[str, object] | None:
    """Estado del torneo para la base; None si no hay torneo."""
    return None if torneo is None else torneo.serializar()


def deserializar_torneo(
    modo: ModoJuego,
    datos: dict[str, object],
) -> TorneoBase | None:
    """Reconstruye el torneo de un modo desde su estado guardado."""
    torneo = crear_torneo(modo)

    if torneo is None:
        return None

    torneo.restaurar(datos)
    return torneo


def crear_torneo(modo: ModoJuego) -> TorneoBase | None:
    """Torneo que corresponde a un modo; None si no tiene."""
    if modo is ModoJuego.LIGA:
        return Liga()

    if modo is ModoJuego.COPA:
        return Copa()

    if modo is ModoJuego.CAMPEONES:
        return Campeones()

    if modo is ModoJuego.SUPERVIVENCIA:
        return Supervivencia()

    return None
