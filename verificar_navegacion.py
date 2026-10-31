"""Verificación de la navegación de menús y de los uniformes.

Ejecutar: ``python verificar_navegacion.py``
Usa controladores SDL ``dummy``: no abre ventana ni reproduce audio.
Sale con código 0 si todas las comprobaciones pasan, 1 si falla alguna.
"""

from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from futbol_silueta.configuracion import (
    ALTO,
    ANCHO,
    CAMPO_RECT,
    DURACION_GOL,
    PORTERIA_CENTRO,
    Equipo,
    Estado,
)
from futbol_silueta.juego import Juego
from futbol_silueta.menus import Accion, Boton, Menus, Pantalla
from futbol_silueta.uniformes import UNIFORMES_POR_DEFECTO
from futbol_silueta.vista import Vista

fallos: list[str] = []


def comprobar(nombre: str, obtenido: Pantalla, esperado: Pantalla) -> None:
    if obtenido is esperado:
        print(f"ok     {nombre}")
    else:
        print(
            f"FALLO  {nombre}: se esperaba {esperado.value},"
            f" hubo {obtenido.value}"
        )
        fallos.append(nombre)


def comprobar_valor(nombre: str, obtenido: object, esperado: object) -> None:
    if obtenido == esperado:
        print(f"ok     {nombre}")
    else:
        print(f"FALLO  {nombre}: se esperaba {esperado}, hubo {obtenido}")
        fallos.append(nombre)


def nueva() -> Menus:
    return Menus()


def flujo_bug_reportado() -> None:
    """Pausa -> Opciones -> Escudo -> Volver -> Volver debe llegar a Pausa."""
    menus = nueva()
    menus.reanudar()
    menus.abrir_pausa()
    menus._ejecutar(Accion.CONFIGURACION)
    comprobar(
        "pausa -> configuración abre opciones",
        menus.pantalla,
        Pantalla.OPCIONES,
    )
    menus._ejecutar(Accion.ESCUDO)
    comprobar(
        "opciones -> personalizar escudo",
        menus.pantalla,
        Pantalla.ESCUDO,
    )
    menus._ejecutar(Accion.VOLVER)
    comprobar(
        "escudo -> volver regresa a opciones",
        menus.pantalla,
        Pantalla.OPCIONES,
    )
    menus._ejecutar(Accion.VOLVER)
    comprobar(
        "opciones -> volver regresa a pausa (bug reportado)",
        menus.pantalla,
        Pantalla.PAUSA,
    )
    menus._ejecutar(Accion.CONTINUAR)
    comprobar(
        "pausa -> continuar vuelve al partido",
        menus.pantalla,
        Pantalla.PARTIDO,
    )


def flujo_esc() -> None:
    """ESC retrocede un nivel, igual que el botón Volver."""
    menus = nueva()
    menus.reanudar()
    menus.abrir_pausa()
    menus._ejecutar(Accion.CONFIGURACION)
    menus._ejecutar(Accion.ESCUDO)
    menus.procesar_tecla(pygame.K_ESCAPE)
    comprobar(
        "ESC en escudo regresa a opciones",
        menus.pantalla,
        Pantalla.OPCIONES,
    )
    menus.procesar_tecla(pygame.K_ESCAPE)
    comprobar(
        "ESC en opciones regresa a pausa",
        menus.pantalla,
        Pantalla.PAUSA,
    )
    menus.procesar_tecla(pygame.K_ESCAPE)
    comprobar(
        "ESC en pausa continúa el partido",
        menus.pantalla,
        Pantalla.PARTIDO,
    )


def flujo_desde_principal() -> None:
    """Volver y ESC desde las pantallas abiertas en el menú principal."""
    menus = nueva()
    menus._ejecutar(Accion.OPCIONES)
    menus._ejecutar(Accion.ESCUDO)
    menus._ejecutar(Accion.VOLVER)
    comprobar(
        "principal -> escudo -> volver regresa a opciones",
        menus.pantalla,
        Pantalla.OPCIONES,
    )
    menus._ejecutar(Accion.VOLVER)
    comprobar(
        "segundo volver regresa al principal",
        menus.pantalla,
        Pantalla.PRINCIPAL,
    )

    menus._ejecutar(Accion.AYUDA)
    menus._ejecutar(Accion.VOLVER)
    comprobar(
        "ayuda -> volver regresa al principal",
        menus.pantalla,
        Pantalla.PRINCIPAL,
    )

    menus._ejecutar(Accion.OPCIONES)
    menus.procesar_tecla(pygame.K_ESCAPE)
    comprobar(
        "ESC en opciones (desde principal) regresa al principal",
        menus.pantalla,
        Pantalla.PRINCIPAL,
    )


def flujo_pantallas_sin_navegar() -> None:
    """Sonido y selección de color/forma no cambian de pantalla."""
    menus = nueva()
    menus._ejecutar(Accion.OPCIONES)
    menus._ejecutar(Accion.SONIDO)
    comprobar(
        "alternar sonido no sale de opciones",
        menus.pantalla,
        Pantalla.OPCIONES,
    )

    menus._ejecutar(Accion.ESCUDO)
    menus._ejecutar(
        Accion.ESCUDO,
        Boton(pygame.Rect(0, 0, 1, 1), "", Accion.ESCUDO, valor=1),
    )
    comprobar(
        "elegir color no sale de escudo",
        menus.pantalla,
        Pantalla.ESCUDO,
    )
    menus._ejecutar(
        Accion.FORMA_ESCUDO,
        Boton(pygame.Rect(0, 0, 1, 1), "", Accion.FORMA_ESCUDO, valor=1),
    )
    comprobar(
        "elegir forma no sale de escudo",
        menus.pantalla,
        Pantalla.ESCUDO,
    )


def flujo_robustez() -> None:
    """Pila vacía y saltos largos no dejan estados rotos."""
    menus = nueva()
    menus.pantalla = Pantalla.OPCIONES  # estado forzado: pila vacía
    menus._ejecutar(Accion.VOLVER)
    comprobar(
        "volver sin historial cae en el principal",
        menus.pantalla,
        Pantalla.PRINCIPAL,
    )

    menus = nueva()
    menus.reanudar()
    menus.abrir_pausa()
    menus._ejecutar(Accion.CONFIGURACION)
    menus._ejecutar(Accion.ESCUDO)
    menus.abrir_pausa()  # salto: descarta el historial pendiente
    menus._ejecutar(Accion.CONFIGURACION)
    menus._ejecutar(Accion.VOLVER)
    comprobar(
        "tras reabrir pausa, volver regresa a pausa",
        menus.pantalla,
        Pantalla.PAUSA,
    )

    menus = nueva()
    menus.reanudar()
    menus.abrir_pausa()
    menus._ejecutar(Accion.MENU_PRINCIPAL)
    comprobar(
        "pausa -> menú principal",
        menus.pantalla,
        Pantalla.PRINCIPAL,
    )
    menus._ejecutar(Accion.JUGAR)
    comprobar(
        "principal -> jugar entra al partido",
        menus.pantalla,
        Pantalla.PARTIDO,
    )


def flujo_uniformes() -> None:
    """Pantalla de uniformes: ciclar colores, equipo y dorsales."""
    menus = nueva()
    menus._ejecutar(Accion.OPCIONES)
    menus._ejecutar(Accion.UNIFORME)
    comprobar("opciones -> uniformes", menus.pantalla, Pantalla.UNIFORME)

    menus._ejecutar(
        Accion.PRENDA,
        Boton(pygame.Rect(0, 0, 1, 1), "", Accion.PRENDA, valor="camiseta"),
    )
    comprobar(
        "elegir color de camiseta no sale de uniformes",
        menus.pantalla,
        Pantalla.UNIFORME,
    )
    comprobar_valor(
        "camiseta local pasa de rojo a azul",
        menus.uniformes_seleccionados[Equipo.LOCAL].camiseta,
        (40, 80, 200),
    )

    menus._ejecutar(Accion.EQUIPO_UNIFORME)
    menus._ejecutar(
        Accion.PRENDA,
        Boton(pygame.Rect(0, 0, 1, 1), "", Accion.PRENDA, valor="medias"),
    )
    comprobar_valor(
        "medias visitante pasa de azul a verde",
        menus.uniformes_seleccionados[Equipo.VISITANTE].medias,
        (34, 139, 34),
    )
    comprobar_valor(
        "las medias locales no cambian",
        menus.uniformes_seleccionados[Equipo.LOCAL].medias,
        (200, 40, 40),
    )

    menus._ejecutar(Accion.NUMEROS)
    comprobar_valor(
        "dorsales se desactivan",
        menus.numeros_activados,
        False,
    )

    etiquetas = {
        boton.accion: boton.etiqueta
        for boton in menus.botones[Pantalla.UNIFORME]
    }
    comprobar_valor(
        "etiqueta del equipo muestra VISITANTE",
        etiquetas[Accion.EQUIPO_UNIFORME],
        "Equipo: VISITANTE",
    )
    comprobar_valor(
        "etiqueta de medias muestra el color nuevo",
        etiquetas[Accion.PRENDA],
        "Medias: Verde",
    )
    comprobar_valor(
        "etiqueta de dorsales muestra DESACTIVADOS",
        etiquetas[Accion.NUMEROS],
        "Dorsales: DESACTIVADOS",
    )

    menus.procesar_tecla(pygame.K_ESCAPE)
    comprobar("ESC en uniformes regresa a opciones", menus.pantalla, Pantalla.OPCIONES)
    menus._ejecutar(Accion.VOLVER)
    comprobar("volver desde opciones regresa al principal", menus.pantalla, Pantalla.PRINCIPAL)


def flujo_uniformes_en_partido() -> None:
    """Los uniformes elegidos llegan a los jugadores y a sus sprites."""
    menus = nueva()
    menus._ejecutar(
        Accion.PRENDA,
        Boton(pygame.Rect(0, 0, 1, 1), "", Accion.PRENDA, valor="camiseta"),
    )
    menus._ejecutar(Accion.NUMEROS)

    juego = Juego(None)
    juego.personalizar_uniformes(
        menus.uniformes_seleccionados,
        menus.numeros_activados,
    )
    juego.nueva_partida()

    locales = [j for j in juego.jugadores if j.equipo is Equipo.LOCAL]
    visitantes = [j for j in juego.jugadores if j.equipo is Equipo.VISITANTE]
    comprobar_valor(
        "los locales visten la camiseta elegida",
        {j.uniforme.camiseta for j in locales},
        {(40, 80, 200)},
    )
    comprobar_valor(
        "los visitantes conservan su uniforme",
        {j.uniforme for j in visitantes},
        {UNIFORMES_POR_DEFECTO[Equipo.VISITANTE]},
    )
    comprobar_valor(
        "dorsales del 1 al 11 por equipo",
        (
            sorted(j.numero for j in locales),
            sorted(j.numero for j in visitantes),
        ),
        (list(range(1, 12)), list(range(1, 12))),
    )
    comprobar_valor(
        "dorsales ocultos al desactivarlos",
        {j.mostrar_numero for j in juego.jugadores},
        {False},
    )

    superficie = pygame.Surface((60, 60), pygame.SRCALPHA)
    try:
        for jugador in juego.jugadores:
            jugador.dibujar(superficie)
        print("ok     sprites con uniforme se dibujan sin errores")
    except Exception as error:  # noqa: BLE001
        print(f"FALLO  sprites con uniforme: {error}")
        fallos.append("sprites con uniforme")


def flujo_editor() -> None:
    """Editor de jugadores: nombre, dorsal, atributos, rol y posición."""
    menus = nueva()
    menus._ejecutar(Accion.OPCIONES)
    menus._ejecutar(Accion.EDITOR)
    comprobar("opciones -> editor de jugadores", menus.pantalla, Pantalla.EDITOR)

    menus._ejecutar(Accion.CICLAR_JUGADOR)
    etiqueta = menus.botones[Pantalla.EDITOR][1].etiqueta
    comprobar_valor(
        "ciclar jugador pasa al segundo",
        etiqueta,
        "Jugador 2/11: Duarte",
    )

    menus._ejecutar(Accion.EDITOR_NOMBRE)
    for _ in range(12):
        menus.procesar_tecla(pygame.K_BACKSPACE)
    for letra in "oca":
        menus.procesar_tecla(getattr(pygame, f"K_{letra}"))
    menus.procesar_tecla(pygame.K_RETURN)
    comprobar_valor(
        "borrar y escribir cambia el nombre",
        menus.plantillas_seleccionadas[Equipo.LOCAL][1].nombre,
        "Oca",
    )

    menus._ejecutar(Accion.CICLAR_DORSAL)
    comprobar_valor(
        "dorsal cicla hacia adelante",
        menus.plantillas_seleccionadas[Equipo.LOCAL][1].dorsal,
        3,
    )
    menus._ejecutar(Accion.CICLAR_DORSAL, None, -1)
    comprobar_valor(
        "ajuste hacia atrás devuelve el dorsal",
        menus.plantillas_seleccionadas[Equipo.LOCAL][1].dorsal,
        2,
    )

    menus._ejecutar(Accion.CICLAR_VELOCIDAD)
    comprobar_valor(
        "velocidad pasa de Normal a Rápida",
        menus.plantillas_seleccionadas[Equipo.LOCAL][1].factor_velocidad,
        1.15,
    )
    menus._ejecutar(Accion.CICLAR_FUERZA, None, -1)
    comprobar_valor(
        "ajuste hacia atrás deja la fuerza Débil",
        menus.plantillas_seleccionadas[Equipo.LOCAL][1].factor_fuerza,
        0.8,
    )

    menus._ejecutar(Accion.CICLAR_ROL)
    comprobar_valor(
        "rol de defensa pasa a medio",
        menus.plantillas_seleccionadas[Equipo.LOCAL][1].rol.value,
        "medio",
    )

    menus._ejecutar(Accion.MOVER_POSICION)
    menus.procesar_tecla(pygame.K_RIGHT)
    menus.procesar_tecla(pygame.K_UP)
    ficha = menus.plantillas_seleccionadas[Equipo.LOCAL][1]
    comprobar_valor(
        "las flechas mueven la posición",
        (round(ficha.x, 3), round(ficha.y, 3)),
        (0.24, 0.18),
    )
    menus._colocar_en_campo(menus.rect_campo_editor.center)
    comprobar_valor(
        "un clic en el campo coloca al jugador en el centro",
        menus.plantillas_seleccionadas[Equipo.LOCAL][1].y,
        0.5,
    )
    menus.procesar_tecla(pygame.K_RETURN)
    comprobar_valor(
        "ENTER confirma el movimiento",
        menus._moviendo_posicion,
        False,
    )

    menus._ejecutar(Accion.EQUIPO_EDITOR)
    comprobar_valor(
        "el equipo alterna a VISITANTE",
        menus.botones[Pantalla.EDITOR][0].etiqueta,
        "Equipo: VISITANTE",
    )
    comprobar_valor(
        "la ficha editada del local no cambió",
        menus.plantillas_seleccionadas[Equipo.LOCAL][1].nombre,
        "Oca",
    )

    menus._ejecutar(Accion.VOLVER)
    comprobar("volver regresa a opciones", menus.pantalla, Pantalla.OPCIONES)
    menus._ejecutar(Accion.VOLVER)
    comprobar("segundo volver regresa al principal", menus.pantalla, Pantalla.PRINCIPAL)


def flujo_editor_con_pausa() -> None:
    """La pila también funciona con el editor abierto desde la pausa."""
    menus = nueva()
    menus.reanudar()
    menus.abrir_pausa()
    menus._ejecutar(Accion.CONFIGURACION)
    menus._ejecutar(Accion.EDITOR)
    menus._ejecutar(Accion.VOLVER)
    comprobar(
        "editor -> volver regresa a opciones",
        menus.pantalla,
        Pantalla.OPCIONES,
    )
    menus._ejecutar(Accion.VOLVER)
    comprobar(
        "opciones -> volver regresa a pausa",
        menus.pantalla,
        Pantalla.PAUSA,
    )
    menus._ejecutar(Accion.CONTINUAR)
    comprobar(
        "pausa -> continuar vuelve al partido",
        menus.pantalla,
        Pantalla.PARTIDO,
    )


def flujo_editor_en_partido() -> None:
    """Las fichas editadas llegan a los jugadores del partido."""
    menus = nueva()
    menus._ejecutar(Accion.CICLAR_JUGADOR)
    menus._ejecutar(Accion.EDITOR_NOMBRE)
    for _ in range(12):
        menus.procesar_tecla(pygame.K_BACKSPACE)
    menus.procesar_tecla(pygame.K_o)
    menus.procesar_tecla(pygame.K_c)
    menus.procesar_tecla(pygame.K_a)
    menus.procesar_tecla(pygame.K_RETURN)
    menus._ejecutar(Accion.CICLAR_DORSAL)
    menus._ejecutar(Accion.CICLAR_VELOCIDAD)
    menus._ejecutar(Accion.CICLAR_FUERZA, None, -1)
    menus._ejecutar(Accion.CICLAR_ROL)

    juego = Juego(None)
    juego.personalizar_plantillas(menus.plantillas_seleccionadas)
    juego.nueva_partida()

    locales = [j for j in juego.jugadores if j.equipo is Equipo.LOCAL]
    visitantes = [j for j in juego.jugadores if j.equipo is Equipo.VISITANTE]
    editado = locales[1]
    comprobar_valor("nombre llega al partido", editado.nombre, "Oca")
    comprobar_valor("dorsal llega al partido", editado.numero, 3)
    comprobar_valor("rol llega al partido", editado.rol.value, "medio")
    comprobar_valor(
        "velocidad escalada por el factor",
        round(editado.velocidad, 2),
        round(180.0 * 1.15, 2),
    )
    comprobar_valor(
        "factor de fuerza llega al partido",
        editado.factor_fuerza,
        0.8,
    )
    comprobar_valor(
        "los visitantes conservan sus nombres",
        visitantes[0].nombre,
        "Quiroga",
    )

    superficie = pygame.Surface((ANCHO, ALTO))
    try:
        for _ in range(30):
            juego.actualizar(1 / 60)
        menus.pantalla = Pantalla.EDITOR
        menus.dibujar(superficie)
        print("ok     partido y editor se simulan/dibujan sin errores")
    except Exception as error:  # noqa: BLE001
        print(f"FALLO  simulación o editor: {error}")
        fallos.append("simulación o editor")


def flujo_repeticion() -> None:
    """Repeticiones de gol: celebración, cámara lenta y salto."""
    vista = Vista(pygame.display.get_surface())
    juego = Juego(vista)
    juego.nueva_partida(con_silbato=False)

    control = juego.jugador_controlado
    juego.dar_posesion(control)
    for _ in range(30):
        juego.actualizar(1 / 60)

    control.pos.update(CAMPO_RECT.right - 20, PORTERIA_CENTRO)
    control.actualizar_rect()
    control.direccion.update(1, 0)
    juego.actualizar_balon(1 / 60)
    comprobar_valor("el gol queda en celebración", juego.estado, Estado.GOL)
    comprobar_valor(
        "la jugada queda congelada para la repetición",
        bool(juego.repeticion),
        True,
    )

    juego.tiempo_gol -= DURACION_GOL
    juego.actualizar(1 / 60)
    comprobar_valor(
        "tras la celebración arranca la repetición",
        juego.estado,
        Estado.REPETICION,
    )

    superficie = pygame.Surface((ANCHO, ALTO))
    try:
        for _ in range(5):
            juego.actualizar(1 / 60)
            vista.dibujar(juego)
        print("ok     la repetición se simula y dibuja sin errores")
    except Exception as error:  # noqa: BLE001
        print(f"FALLO  repetición en pantalla: {error}")
        fallos.append("repetición en pantalla")

    juego.procesar_tecla(pygame.K_SPACE)
    comprobar_valor(
        "ESPACIO salta la repetición y saca de centro",
        juego.estado,
        Estado.JUGANDO,
    )


def main() -> None:
    pygame.init()
    pygame.display.set_mode((ANCHO, ALTO))

    flujo_bug_reportado()
    flujo_esc()
    flujo_desde_principal()
    flujo_pantallas_sin_navegar()
    flujo_robustez()
    flujo_uniformes()
    flujo_uniformes_en_partido()
    flujo_editor()
    flujo_editor_con_pausa()
    flujo_editor_en_partido()
    flujo_repeticion()

    pygame.quit()

    if fallos:
        print(f"\n{len(fallos)} comprobación(es) fallaron")
        raise SystemExit(1)

    print("\nTodas las comprobaciones pasaron")


if __name__ == "__main__":
    main()
