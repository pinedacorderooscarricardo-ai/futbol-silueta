"""Persistencia en SQLite de la configuración y la plantilla del juego.

Guarda todo lo que el jugador personaliza en los menús (sonido, escudo,
uniformes, formación y las fichas del editor de jugadores) para que se
conserven entre sesiones. Si la base de datos no existe se crea al
arrancar; si está corrupta o bloqueada, el juego sigue funcionando con
los valores por defecto y simplemente no guarda.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from .configuracion import Color, Equipo, Rol
from .escudos import FormaEscudo
from .plantilla import JugadorPlantilla
from .uniformes import Uniforme
from .utilidades import acotar

if TYPE_CHECKING:
    from .menus import Menus

EQUIPOS: tuple[str, ...] = (Equipo.LOCAL.value, Equipo.VISITANTE.value)


def ruta_base_datos() -> Path:
    """Ubicación de la base: junto al ejecutable o al proyecto."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "futbol_silueta.sqlite"

    return Path(__file__).resolve().parent.parent / "futbol_silueta.sqlite"


def _color_a_texto(color: Color) -> str:
    """Serializa un color como ``"r,g,b"``."""
    return ",".join(str(valor) for valor in color)


def _texto_a_color(texto: str) -> Color:
    """Recupera un color guardado como ``"r,g,b"``."""
    rojo, verde, azul = (int(valor) for valor in texto.split(","))
    return (rojo, verde, azul)


class Guardado:
    """Base de datos SQLite con los datos persistentes del juego.

    Todos los métodos son seguros: si la base no está disponible (archivo
    bloqueado o dañado) se desactivan y el juego funciona con sus valores
    en memoria, igual que hace ``Sonidos`` sin mixer.
    """

    def __init__(self, ruta: Path | None = None) -> None:
        self.ruta = ruta if ruta is not None else ruta_base_datos()
        self.disponible = False
        self.conexion: sqlite3.Connection | None = None

        try:
            self.conexion = sqlite3.connect(self.ruta)
            self.conexion.row_factory = sqlite3.Row
            self._crear_tablas()
        except sqlite3.Error:
            self._desactivar()
            return

        self.disponible = True

    def cerrar(self) -> None:
        """Cierra la conexión, si hay una abierta."""
        if self.conexion is not None:
            self.conexion.close()
            self.conexion = None

        self.disponible = False

    def _desactivar(self) -> None:
        self.cerrar()
        self.disponible = False

    def _crear_tablas(self) -> None:
        assert self.conexion is not None
        with self.conexion:
            self.conexion.execute(
                """
                CREATE TABLE IF NOT EXISTS ajustes (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    sonido_activado INTEGER NOT NULL DEFAULT 1,
                    escudo_color TEXT NOT NULL,
                    escudo_color_borde TEXT NOT NULL,
                    escudo_forma TEXT NOT NULL,
                    mostrar_numeros INTEGER NOT NULL DEFAULT 1,
                    formacion TEXT NOT NULL,
                    local_camiseta TEXT NOT NULL,
                    local_pantalon TEXT NOT NULL,
                    local_medias TEXT NOT NULL,
                    visitante_camiseta TEXT NOT NULL,
                    visitante_pantalon TEXT NOT NULL,
                    visitante_medias TEXT NOT NULL
                )
                """
            )
            self.conexion.execute(
                """
                CREATE TABLE IF NOT EXISTS jugadores (
                    equipo TEXT NOT NULL CHECK (equipo IN ('local', 'visitante')),
                    indice INTEGER NOT NULL CHECK (indice BETWEEN 0 AND 10),
                    nombre TEXT NOT NULL,
                    dorsal INTEGER NOT NULL,
                    rol TEXT NOT NULL,
                    x REAL NOT NULL,
                    y REAL NOT NULL,
                    factor_velocidad REAL NOT NULL,
                    factor_fuerza REAL NOT NULL,
                    PRIMARY KEY (equipo, indice)
                )
                """
            )

    # --------------------------------------------------
    # Guardar y cargar
    # --------------------------------------------------

    def guardar_desde(self, menus: Menus) -> None:
        """Guarda el estado actual de los menús en la base."""
        if not self.disponible or self.conexion is None:
            return

        uniformes = menus.uniformes_seleccionados
        local = uniformes[Equipo.LOCAL]
        visitante = uniformes[Equipo.VISITANTE]
        fichas = menus.plantillas_seleccionadas
        filas = [
            (
                equipo.value,
                indice,
                ficha.nombre,
                ficha.dorsal,
                ficha.rol.value,
                ficha.x,
                ficha.y,
                ficha.factor_velocidad,
                ficha.factor_fuerza,
            )
            for equipo in Equipo
            for indice, ficha in enumerate(fichas[equipo])
        ]

        try:
            with self.conexion:
                self.conexion.execute(
                    """
                    INSERT OR REPLACE INTO ajustes (
                        id, sonido_activado, escudo_color,
                        escudo_color_borde, escudo_forma,
                        mostrar_numeros, formacion,
                        local_camiseta, local_pantalon, local_medias,
                        visitante_camiseta, visitante_pantalon,
                        visitante_medias
                    ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        int(menus.sonido_activado),
                        _color_a_texto(menus.escudo_color),
                        _color_a_texto(menus.escudo_color_borde),
                        menus.escudo_forma.value,
                        int(menus.numeros_activados),
                        menus.formacion_nombre,
                        _color_a_texto(local.camiseta),
                        _color_a_texto(local.pantalon),
                        _color_a_texto(local.medias),
                        _color_a_texto(visitante.camiseta),
                        _color_a_texto(visitante.pantalon),
                        _color_a_texto(visitante.medias),
                    ),
                )
                self.conexion.execute("DELETE FROM jugadores")
                self.conexion.executemany(
                    """
                    INSERT INTO jugadores (
                        equipo, indice, nombre, dorsal, rol,
                        x, y, factor_velocidad, factor_fuerza
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    filas,
                )
        except sqlite3.Error:
            self._desactivar()

    def cargar_en(self, menus: Menus) -> None:
        """Aplica a los menús lo guardado; sin datos, deja los valores.

        La carga es atómica: primero se leen y validan todos los datos y
        solo si todo es correcto se aplican, para que una base corrupta
        no deje los menús a medias.
        """
        if not self.disponible or self.conexion is None:
            return

        try:
            fila = self.conexion.execute(
                "SELECT * FROM ajustes WHERE id = 1"
            ).fetchone()

            if fila is None:
                return

            sonido = bool(fila["sonido_activado"])
            color = _texto_a_color(fila["escudo_color"])
            color_borde = _texto_a_color(fila["escudo_color_borde"])
            forma = FormaEscudo(fila["escudo_forma"])
            numeros = bool(fila["mostrar_numeros"])
            formacion = str(fila["formacion"])
            uniformes = {
                Equipo.LOCAL: Uniforme(
                    _texto_a_color(fila["local_camiseta"]),
                    _texto_a_color(fila["local_pantalon"]),
                    _texto_a_color(fila["local_medias"]),
                ),
                Equipo.VISITANTE: Uniforme(
                    _texto_a_color(fila["visitante_camiseta"]),
                    _texto_a_color(fila["visitante_pantalon"]),
                    _texto_a_color(fila["visitante_medias"]),
                ),
            }
            plantillas = self._cargar_plantilla()
        except (sqlite3.Error, ValueError, TypeError, IndexError):
            # Datos corruptos o incompletos: se conservan los de memoria.
            return

        menus.sonido_activado = sonido
        menus.escudo_color = color
        menus.escudo_color_borde = color_borde
        menus.escudo_forma = forma
        menus.numeros_activados = numeros
        menus.formacion_nombre = formacion
        menus.uniformes_seleccionados = uniformes

        if plantillas is not None:
            menus.plantillas_editables = plantillas

        menus._actualizar_etiqueta_sonido()
        menus._actualizar_etiquetas_uniforme()
        menus._actualizar_etiquetas_editor()

    def _cargar_plantilla(
        self,
    ) -> dict[Equipo, tuple[JugadorPlantilla, ...]] | None:
        """Fichas guardadas por equipo; None si faltan jugadores."""
        assert self.conexion is not None
        filas = self.conexion.execute(
            """
            SELECT equipo, indice, nombre, dorsal, rol,
                   x, y, factor_velocidad, factor_fuerza
            FROM jugadores
            ORDER BY equipo, indice
            """
        ).fetchall()
        por_equipo: dict[Equipo, list[JugadorPlantilla]] = {
            equipo: [] for equipo in Equipo
        }

        for fila in filas:
            equipo = Equipo(fila["equipo"])
            por_equipo[equipo].append(
                JugadorPlantilla(
                    nombre=str(fila["nombre"])[:14],
                    dorsal=acotar(int(fila["dorsal"]), 1, 99),
                    rol=self._rol_valido(fila["rol"]),
                    x=acotar(float(fila["x"]), 0.0, 1.0),
                    y=acotar(float(fila["y"]), 0.0, 1.0),
                    factor_velocidad=float(fila["factor_velocidad"]),
                    factor_fuerza=float(fila["factor_fuerza"]),
                )
            )

        if any(
            len(por_equipo[equipo]) != 11
            for equipo in (Equipo.LOCAL, Equipo.VISITANTE)
        ):
            return None

        return {
            equipo: tuple(por_equipo[equipo])
            for equipo in (Equipo.LOCAL, Equipo.VISITANTE)
        }

    @staticmethod
    def _rol_valido(rol: str) -> Rol:
        """Rol guardado si es válido; defensa como valor de respaldo."""
        try:
            return Rol(rol)
        except ValueError:
            return Rol.DEFENSA
