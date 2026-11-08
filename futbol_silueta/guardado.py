"""Persistencia en SQLite de la configuración y la plantilla del juego.

Guarda todo lo que el jugador personaliza en los menús (sonido, escudo,
uniformes, formación, estadio y las fichas del editor de jugadores)
para que se conserven entre sesiones. Si la base de datos no existe se
crea al arrancar; si está corrupta o bloqueada, el juego sigue
funcionando con los valores por defecto y simplemente no guarda.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from typing import TYPE_CHECKING, TypeVar

from .configuracion import (
    FORMACION,
    NOMBRES_FORMACION,
    Color,
    Equipo,
)
from .modos import (
    ModoJuego,
    TorneoBase,
    deserializar_torneo,
    serializar_torneo,
)
from .escudos import ESCUDO_PRESETS, FORMAS_ESCUDO, FormaEscudo
from .estadios import (
    ESTADIO_POR_DEFECTO,
    Cesped,
    Clima,
    Diseno,
    Estadio,
    Momento,
)
from .estadisticas import (
    MAX_HISTORIAL,
    FilaPosiciones,
    Resultado,
    TablaPosiciones,
)
from .niveles import NIVEL_MAXIMO
from .plantilla import (
    JugadorPlantilla,
    aplicar_formacion,
    normalizar_plantilla,
    plantilla_por_defecto,
)
from .uniformes import UNIFORMES_POR_DEFECTO, Uniforme
from .utilidades import acotar

if TYPE_CHECKING:
    from .menus import Menus

EQUIPOS: tuple[str, ...] = (Equipo.LOCAL.value, Equipo.VISITANTE.value)

T = TypeVar("T")


def ruta_base_datos() -> Path:
    """Ubicación de la base: junto al ejecutable o al proyecto."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "futbol_silueta.sqlite"

    return Path(__file__).resolve().parent.parent / "futbol_silueta.sqlite"


def _color_a_texto(color: Color) -> str:
    """Serializa un color como ``"r,g,b"``, limitado al rango de 8 bits."""
    return ",".join(
        str(int(acotar(valor, 0, 255)))
        for valor in color
    )


def _texto_a_color(texto: str) -> Color:
    """Recupera un color guardado como ``"r,g,b"``.

    Los canales fuera de rango se recortan: una base manipulada a mano
    no debe provocar errores de dibujo al aplicar el color.
    """
    partes = texto.split(",")

    if len(partes) != 3:
        raise ValueError("color con formato inválido")

    rojo, verde, azul = (int(valor) for valor in partes)
    return (
        int(acotar(rojo, 0, 255)),
        int(acotar(verde, 0, 255)),
        int(acotar(azul, 0, 255)),
    )


def _formacion_valida(nombre: object) -> str:
    """Nombre de formación del catálogo; la 4-4-2 si no existe."""
    texto = str(nombre)

    return texto if texto in NOMBRES_FORMACION else NOMBRES_FORMACION[0]


def _opcion_valida(
    tipo: type[T],
    valor: object,
    defecto: T,
) -> T:
    """Convierte ``valor`` al enum ``tipo``; si no es válido, al defecto."""
    try:
        return tipo(valor)  # type: ignore[call-arg]
    except (TypeError, ValueError):
        return defecto


def _booleano_valido(valor: object, defecto: bool) -> bool:
    """Interpreta un 0/1 guardado; cualquier otro valor conserva el actual."""
    try:
        return bool(int(valor))  # type: ignore[arg-type]
    except (TypeError, ValueError, OverflowError):
        return defecto


def _color_valido(valor: object, defecto: Color) -> Color:
    """Color guardado y recortado a 8 bits; si falta, el de respaldo."""
    try:
        return _texto_a_color(str(valor))
    except (TypeError, ValueError, OverflowError):
        return defecto


def _color_seguro(valor: object, defecto: Color) -> Color:
    """Serie de tres canales válida para guardar; si no, el respaldo."""
    try:
        canales = tuple(valor)  # type: ignore[arg-type]
    except TypeError:
        return defecto

    if len(canales) != 3:
        return defecto

    try:
        return (
            int(acotar(int(canales[0]), 0, 255)),
            int(acotar(int(canales[1]), 0, 255)),
            int(acotar(int(canales[2]), 0, 255)),
        )
    except (TypeError, ValueError, OverflowError):
        return defecto


def _uniforme_seguro(valor: object, defecto: Uniforme) -> Uniforme:
    """Uniforme con sus tres colores saneados; si no, el de respaldo."""
    if not isinstance(valor, Uniforme):
        return defecto

    return Uniforme(
        _color_seguro(valor.camiseta, defecto.camiseta),
        _color_seguro(valor.pantalon, defecto.pantalon),
        _color_seguro(valor.medias, defecto.medias),
    )


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
            self._migrar()
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
                    visitante_medias TEXT NOT NULL,
                    estadio_cesped TEXT NOT NULL DEFAULT 'claro',
                    estadio_momento TEXT NOT NULL DEFAULT 'dia',
                    estadio_diseno TEXT NOT NULL DEFAULT 'clasico',
                    estadio_gradas INTEGER NOT NULL DEFAULT 1,
                    estadio_clima TEXT NOT NULL DEFAULT 'despejado',
                    nivel_campana INTEGER NOT NULL DEFAULT 1
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
            self.conexion.execute(
                """
                CREATE TABLE IF NOT EXISTS resultados (
                    nivel INTEGER NOT NULL,
                    goles_local INTEGER NOT NULL,
                    goles_visitante INTEGER NOT NULL
                )
                """
            )
            self.conexion.execute(
                """
                CREATE TABLE IF NOT EXISTS posiciones (
                    equipo TEXT PRIMARY KEY,
                    pj INTEGER NOT NULL,
                    g INTEGER NOT NULL,
                    e INTEGER NOT NULL,
                    p INTEGER NOT NULL,
                    gf INTEGER NOT NULL,
                    gc INTEGER NOT NULL,
                    puntos INTEGER NOT NULL
                )
                """
            )
            self.conexion.execute(
                """
                CREATE TABLE IF NOT EXISTS trofeos (
                    id TEXT PRIMARY KEY
                )
                """
            )
            self.conexion.execute(
                """
                CREATE TABLE IF NOT EXISTS torneos (
                    modo TEXT PRIMARY KEY,
                    datos TEXT NOT NULL
                )
                """
            )

    def _migrar(self) -> None:
        """Añade las columnas nuevas a bases de versiones anteriores.

        ``CREATE TABLE IF NOT EXISTS`` no toca las bases ya creadas:
        aquí se completan con las columnas que falten, con valores por
        defecto, para que el guardado siga funcionando con bases viejas.
        """
        assert self.conexion is not None
        columnas = {
            fila[1]
            for fila in self.conexion.execute("PRAGMA table_info(ajustes)")
        }

        with self.conexion:
            for nombre, tipo in (
                ("estadio_cesped", "TEXT NOT NULL DEFAULT 'claro'"),
                ("estadio_momento", "TEXT NOT NULL DEFAULT 'dia'"),
                ("estadio_diseno", "TEXT NOT NULL DEFAULT 'clasico'"),
                ("estadio_gradas", "INTEGER NOT NULL DEFAULT 1"),
                ("estadio_clima", "TEXT NOT NULL DEFAULT 'despejado'"),
                ("nivel_campana", "INTEGER NOT NULL DEFAULT 1"),
            ):
                if nombre not in columnas:
                    self.conexion.execute(
                        f"ALTER TABLE ajustes ADD COLUMN {nombre} {tipo}"
                    )

    # --------------------------------------------------
    # Guardar y cargar
    # --------------------------------------------------

    def guardar_desde(self, menus: Menus, nivel: int | None = None) -> None:
        """Guarda el estado actual de los menús en la base.

        ``nivel`` es el nivel de campaña en curso (guardado automático
        al terminar o cerrar un partido); sin dato, se conserva el que
        ya estuviera guardado. Los datos se sanean antes de escribirlos
        (22 fichas exactas, colores de 8 bits y formación válida): así
        una edición externa o un menú en un estado raro no rompe la base
        ni el cierre del juego.
        """
        if not self.disponible or self.conexion is None:
            return

        try:
            uniformes = menus.uniformes_seleccionados
            local = _uniforme_seguro(
                uniformes.get(Equipo.LOCAL),
                UNIFORMES_POR_DEFECTO[Equipo.LOCAL],
            )
            visitante = _uniforme_seguro(
                uniformes.get(Equipo.VISITANTE),
                UNIFORMES_POR_DEFECTO[Equipo.VISITANTE],
            )
            estadio = menus.estadio_seleccionado

            if not isinstance(estadio, Estadio):
                estadio = ESTADIO_POR_DEFECTO

            if nivel is None:
                nivel = self.nivel_guardado()

            forma = _opcion_valida(
                FormaEscudo,
                menus.escudo_forma,
                FORMAS_ESCUDO[0],
            )
            color = _color_seguro(
                menus.escudo_color,
                ESCUDO_PRESETS[0][1],
            )
            color_borde = _color_seguro(
                menus.escudo_color_borde,
                ESCUDO_PRESETS[0][2],
            )
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
            posiciones = [
                (
                    clave,
                    fila.pj,
                    fila.g,
                    fila.e,
                    fila.p,
                    fila.gf,
                    fila.gc,
                    fila.puntos,
                )
                for clave, fila in menus.tabla_posiciones.filas.items()
            ]
            trofeos = [
                (trofeo,) for trofeo in sorted(menus.trofeos)
            ]
            resultados = [
                (r.nivel, r.goles_local, r.goles_visitante)
                for r in menus.historial[:MAX_HISTORIAL]
            ]
            parametros = (
                int(bool(menus.sonido_activado)),
                _color_a_texto(color),
                _color_a_texto(color_borde),
                forma.value,
                int(bool(menus.numeros_activados)),
                _formacion_valida(menus.formacion_nombre),
                _color_a_texto(local.camiseta),
                _color_a_texto(local.pantalon),
                _color_a_texto(local.medias),
                _color_a_texto(visitante.camiseta),
                _color_a_texto(visitante.pantalon),
                _color_a_texto(visitante.medias),
                _opcion_valida(
                    Cesped,
                    estadio.cesped,
                    ESTADIO_POR_DEFECTO.cesped,
                ).value,
                _opcion_valida(
                    Momento,
                    estadio.momento,
                    ESTADIO_POR_DEFECTO.momento,
                ).value,
                _opcion_valida(
                    Diseno,
                    estadio.diseno,
                    ESTADIO_POR_DEFECTO.diseno,
                ).value,
                int(bool(estadio.gradas)),
                _opcion_valida(
                    Clima,
                    estadio.clima,
                    ESTADIO_POR_DEFECTO.clima,
                ).value,
                acotar(int(nivel), 1, NIVEL_MAXIMO),
            )
        except (AttributeError, KeyError, TypeError, ValueError):
            # Menús en un estado inesperado: se conserva lo ya guardado.
            return

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
                        visitante_medias, estadio_cesped,
                        estadio_momento, estadio_diseno, estadio_gradas,
                        estadio_clima, nivel_campana
                    ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    parametros,
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
                self.conexion.execute("DELETE FROM posiciones")
                self.conexion.executemany(
                    """
                    INSERT INTO posiciones (
                        equipo, pj, g, e, p, gf, gc, puntos
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    posiciones,
                )
                self.conexion.execute("DELETE FROM trofeos")
                self.conexion.executemany(
                    "INSERT INTO trofeos (id) VALUES (?)",
                    trofeos,
                )
                self.conexion.execute("DELETE FROM resultados")
                self.conexion.executemany(
                    """
                    INSERT INTO resultados (
                        nivel, goles_local, goles_visitante
                    ) VALUES (?, ?, ?)
                    """,
                    resultados,
                )
        except sqlite3.Error:
            self._desactivar()

    def nivel_guardado(self) -> int:
        """El nivel de campaña guardado; 1 sin base o sin datos."""
        if not self.disponible or self.conexion is None:
            return 1

        try:
            fila = self.conexion.execute(
                "SELECT nivel_campana FROM ajustes WHERE id = 1"
            ).fetchone()

            if fila is None:
                return 1

            return acotar(int(fila["nivel_campana"]), 1, NIVEL_MAXIMO)
        except (sqlite3.Error, TypeError, ValueError):
            return 1

    def cargar_en(self, menus: Menus) -> None:
        """Aplica a los menús lo guardado; sin datos, deja los valores.

        La carga es atómica ante errores de la base, pero cada campo se
        valida por separado: un color o una opción corrupta conserva el
        valor que ya tenía el menú en lugar de descartar todo el guardado.
        """
        if not self.disponible or self.conexion is None:
            return

        try:
            fila = self.conexion.execute(
                "SELECT * FROM ajustes WHERE id = 1"
            ).fetchone()

            if fila is None:
                return

            uniformes_actuales = menus.uniformes_seleccionados
            local_actual = uniformes_actuales.get(
                Equipo.LOCAL,
                UNIFORMES_POR_DEFECTO[Equipo.LOCAL],
            )
            visitante_actual = uniformes_actuales.get(
                Equipo.VISITANTE,
                UNIFORMES_POR_DEFECTO[Equipo.VISITANTE],
            )
            estadio_actual = menus.estadio_seleccionado
            sonido = _booleano_valido(
                fila["sonido_activado"],
                menus.sonido_activado,
            )
            numeros = _booleano_valido(
                fila["mostrar_numeros"],
                menus.numeros_activados,
            )
            color = _color_valido(fila["escudo_color"], menus.escudo_color)
            color_borde = _color_valido(
                fila["escudo_color_borde"],
                menus.escudo_color_borde,
            )
            forma = _opcion_valida(
                FormaEscudo,
                fila["escudo_forma"],
                FORMAS_ESCUDO[0],
            )
            formacion = _formacion_valida(fila["formacion"])
            uniformes = {
                Equipo.LOCAL: Uniforme(
                    _color_valido(
                        fila["local_camiseta"],
                        local_actual.camiseta,
                    ),
                    _color_valido(
                        fila["local_pantalon"],
                        local_actual.pantalon,
                    ),
                    _color_valido(
                        fila["local_medias"],
                        local_actual.medias,
                    ),
                ),
                Equipo.VISITANTE: Uniforme(
                    _color_valido(
                        fila["visitante_camiseta"],
                        visitante_actual.camiseta,
                    ),
                    _color_valido(
                        fila["visitante_pantalon"],
                        visitante_actual.pantalon,
                    ),
                    _color_valido(
                        fila["visitante_medias"],
                        visitante_actual.medias,
                    ),
                ),
            }
            plantillas = self._cargar_plantilla(formacion)
            estadio = Estadio(
                _opcion_valida(
                    Cesped,
                    fila["estadio_cesped"],
                    estadio_actual.cesped,
                ),
                _opcion_valida(
                    Momento,
                    fila["estadio_momento"],
                    estadio_actual.momento,
                ),
                _opcion_valida(
                    Diseno,
                    fila["estadio_diseno"],
                    estadio_actual.diseno,
                ),
                _booleano_valido(
                    fila["estadio_gradas"],
                    estadio_actual.gradas,
                ),
                _opcion_valida(
                    Clima,
                    fila["estadio_clima"],
                    estadio_actual.clima,
                ),
            )
            tabla = self._cargar_tabla()
            historial = self._cargar_historial()
            trofeos = {
                str(fila_t["id"])
                for fila_t in self.conexion.execute(
                    "SELECT id FROM trofeos"
                )
            }
        except (
            sqlite3.Error,
            AttributeError,
            IndexError,
            KeyError,
            TypeError,
        ):
            # Base incompleta o menús en un estado inesperado: no se
            # aplica nada a medias.
            return

        menus.sonido_activado = sonido
        menus.escudo_color = color
        menus.escudo_color_borde = color_borde
        menus.escudo_forma = forma
        menus.numeros_activados = numeros
        menus.formacion_nombre = formacion
        menus.uniformes_seleccionados = uniformes
        menus.plantillas_editables = {
            equipo: list(plantillas[equipo]) for equipo in Equipo
        }

        menus.adoptar_estadio(estadio)
        menus.tabla_posiciones = tabla
        menus.historial = historial
        menus.trofeos = trofeos
        menus._actualizar_etiqueta_sonido()
        menus._actualizar_etiquetas_uniforme()
        menus._actualizar_etiquetas_editor()

    def _cargar_tabla(self) -> TablaPosiciones:
        """La tabla de posiciones guardada; filas sanas, ceros por defecto."""
        assert self.conexion is not None
        tabla = TablaPosiciones()
        filas = self.conexion.execute(
            """
            SELECT equipo, pj, g, e, p, gf, gc, puntos FROM posiciones
            """
        ).fetchall()

        for fila in filas:
            clave = str(fila["equipo"])

            # Solo se admiten las claves que el juego entiende: "local"
            # y un número de nivel; cualquier otra fila se descarta.
            if clave != "local" and (
                not clave.isdigit() or not 1 <= int(clave) <= NIVEL_MAXIMO
            ):
                continue

            try:
                tabla.filas[clave] = FilaPosiciones(
                    pj=int(fila["pj"]),
                    g=int(fila["g"]),
                    e=int(fila["e"]),
                    p=int(fila["p"]),
                    gf=int(fila["gf"]),
                    gc=int(fila["gc"]),
                    puntos=int(fila["puntos"]),
                )
            except (TypeError, ValueError):
                continue  # Fila dañada: el equipo queda a cero.

        return tabla

    def _cargar_historial(self) -> list[Resultado]:
        """Los resultados guardados, del más reciente al más viejo."""
        assert self.conexion is not None
        filas = self.conexion.execute(
            """
            SELECT nivel, goles_local, goles_visitante FROM resultados
            ORDER BY rowid DESC LIMIT ?
            """,
            (MAX_HISTORIAL,),
        ).fetchall()
        historial: list[Resultado] = []

        for fila in filas:
            try:
                historial.append(
                    Resultado(
                        nivel=acotar(int(fila["nivel"]), 1, NIVEL_MAXIMO),
                        goles_local=int(fila["goles_local"]),
                        goles_visitante=int(fila["goles_visitante"]),
                    )
                )
            except (TypeError, ValueError):
                continue

        return historial

    def _cargar_plantilla(
        self,
        formacion: str,
    ) -> dict[Equipo, tuple[JugadorPlantilla, ...]]:
        """Fichas guardadas, completadas y saneadas para cada equipo.

        Una base con menos de once jugadores se completa con la
        formación elegida y un jugador con datos raros se corrige; nunca
        se descarta la plantilla entera por una sola fila dañada.
        """
        assert self.conexion is not None
        filas = self.conexion.execute(
            """
            SELECT equipo, indice, nombre, dorsal, rol,
                   x, y, factor_velocidad, factor_fuerza
            FROM jugadores
            ORDER BY equipo, indice
            """
        ).fetchall()
        por_equipo: dict[Equipo, dict[int, JugadorPlantilla]] = {
            equipo: {} for equipo in Equipo
        }

        for fila in filas:
            try:
                equipo = Equipo(fila["equipo"])
                indice = int(fila["indice"])
            except (TypeError, ValueError):
                continue

            if not 0 <= indice < len(FORMACION):
                continue

            por_equipo[equipo].setdefault(
                indice,
                JugadorPlantilla(
                    nombre=fila["nombre"],
                    dorsal=fila["dorsal"],
                    rol=fila["rol"],
                    x=fila["x"],
                    y=fila["y"],
                    factor_velocidad=fila["factor_velocidad"],
                    factor_fuerza=fila["factor_fuerza"],
                ),
            )

        plantillas: dict[Equipo, tuple[JugadorPlantilla, ...]] = {}

        for equipo in Equipo:
            base = aplicar_formacion(
                plantilla_por_defecto(equipo),
                formacion,
            )
            fichas = list(base)

            for indice, ficha in por_equipo[equipo].items():
                fichas[indice] = ficha

            plantillas[equipo] = normalizar_plantilla(
                fichas,
                equipo,
                base=base,
            )

        return plantillas

    # --------------------------------------------------
    # Torneos (modos de juego)
    # --------------------------------------------------

    def guardar_torneo(
        self,
        modo: ModoJuego,
        torneo: TorneoBase | None,
    ) -> None:
        """Guarda el torneo de un modo; los terminados se borran.

        Así, la próxima vez que se elija ese modo, empieza uno nuevo
        desde cero en lugar de reanudar uno ya decidido.
        """
        if not self.disponible or self.conexion is None:
            return

        try:
            with self.conexion:
                if torneo is None or torneo.terminado:
                    self.conexion.execute(
                        "DELETE FROM torneos WHERE modo = ?",
                        (modo.value,),
                    )
                    return

                self.conexion.execute(
                    """
                    INSERT OR REPLACE INTO torneos (modo, datos)
                    VALUES (?, ?)
                    """,
                    (modo.value, json.dumps(serializar_torneo(torneo))),
                )
        except (sqlite3.Error, TypeError, ValueError):
            self._desactivar()

    def cargar_torneo(self, modo: ModoJuego) -> TorneoBase | None:
        """Torneo guardado de un modo; None si no hay o está corrupto."""
        if not self.disponible or self.conexion is None:
            return None

        try:
            fila = self.conexion.execute(
                "SELECT datos FROM torneos WHERE modo = ?",
                (modo.value,),
            ).fetchone()
        except sqlite3.Error:
            return None

        if fila is None:
            return None

        try:
            return deserializar_torneo(modo, json.loads(fila["datos"]))
        except (ValueError, KeyError, TypeError):
            return None
