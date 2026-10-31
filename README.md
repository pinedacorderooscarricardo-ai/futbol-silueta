# Fútbol Silueta

Juego 2D de fútbol para dos equipos de 11 jugadores, hecho con **pygame**.
Incluye IA para el equipo visitante, conducción de balón, pases, robos,
sprint con energía, atajadas, marcaje, un partido de dos tiempos de
3 minutos, menús ilustrados con botones clicables, una campaña de
niveles, la personalización del escudo del jugador, uniformes
personalizados, un editor de jugadores con nombres, dorsales,
atributos y posiciones, y tácticas con cuatro formaciones seleccionables
(4-4-2, 4-3-3, 3-5-2 y 5-3-2).

## Campaña de niveles

El juego se divide en niveles: cada nivel es un escudo rival distinto y
cada uno aumenta la dificultad de la IA de forma progresiva (velocidad,
presión, tiros y puntería). Al terminar el último nivel la campaña vuelve
al nivel 1.

| Nivel | Rival | Escudo |
| --- | --- | --- |
| 1 | Club Aurora | `imagenes/escudos/escudo_01.jpeg` |
| 2 | Pasión Fútbol | `imagenes/escudos/escudo_02.jpeg` |
| ... | ... | ... |
| 11 | Campeón Eterno | `imagenes/escudos/escudo_11.jpeg` |

## Escudo y personalización

Cada escudo es un nivel diferente: el marcador del partido muestra a la
izquierda el escudo del jugador, el resultado y el nombre del club rival,
y a la derecha la imagen del escudo de ese nivel. El escudo del jugador
crece de grosor según el nivel.

Desde el menú de opciones se puede personalizar el escudo del jugador:
se elige el color (verde, azul, rojo, amarillo, naranja o rosa), la forma
(clásica, redonda o rombo) y una vista previa muestra en vivo el diseño
elegido antes de volver al partido.

## Uniformes personalizados

En **Opciones → Uniformes** se diseña la equipación de cada equipo por
separado: el botón `Equipo` alterna entre LOCAL y VISITANTE, y para cada
uno se elige el color de la camiseta, del pantalón y de las medias entre
diez colores (blanco, negro, rojo, azul, verde, amarillo, naranja, rosa,
celeste y granate). El botón `Dorsales` activa o desactiva los números
1 al 11 en las camisetas (portero 1, defensas 2-5, medios 6-9,
delanteros 10-11).

La vista previa muestra cómo viste cada equipo y agranda el que se está
editando; el color del dorsal se elige solo (blanco o negro) para que
contraste con la camiseta. Los uniformes se aplican al empezar o
reiniciar un partido y el marcador ya no llama a los equipos "ROJO" y
"AZUL": ahora juegan LOCAL contra VISITANTE.

## Editor de jugadores

En **Opciones → Editor de jugadores** se edita la plantilla de cada
equipo (once jugadores por equipo). El botón `Equipo` alterna entre
LOCAL y VISITANTE y `Jugador` recorre los once huecos; para el jugador
seleccionado se puede cambiar:

- **Nombre:** ENTER empieza a escribir (letras, números y espacio,
  retroceso borra, hasta 14 caracteres) y ENTER confirma; ESC cancela.
- **Dorsal:** del 1 al 99, con ENTER o clic avanza y con ←/→ retrocede.
- **Velocidad:** Lenta, Normal, Rápida o Veloz (multiplica la velocidad
  con la que ese jugador se mueve, tanto controlado por el humano como
  por la IA).
- **Fuerza:** Débil, Normal, Fuerte o Potente (multiplica la fuerza de
  sus disparos, pases y despejes).
- **Rol:** Portero, Defensa, Medio o Delantero; define su comportamiento
  táctico dentro de la IA.
- **Posición:** `Posición: ajustar` entra en modo movimiento; las
  flechas o `WASD` desplazan al jugador sobre el mini campo (o se hace
  clic directamente en el punto deseado) y ENTER confirma.

El mini campo muestra a los 22 jugadores con los colores de su camiseta:
el equipo que se edita resaltado y el rival atenuado, con el jugador
seleccionado marcado por un aro y su dorsal. Los cambios se aplican al
empezar o reiniciar el partido.

## Tácticas y formaciones

En **Opciones → Tácticas** se elige la formación del equipo entre cuatro
presets: **4-4-2**, **4-3-3**, **3-5-2** y **5-3-2**. La lista muestra
cada formación con su nombre y el mini campo de la derecha presenta en
vivo la disposición de los once jugadores locales, con el portero
marcado en gris claro y el resto con el color de su camiseta.

Elegir una formación recoloca a los 22 jugadores (rol y posición) sin
tocar nombres, dorsales ni atributos: cada jugador conserva su identidad
del editor y solo cambia de hueco táctico. El visitante usa la misma
formación reflejada en horizontal, como siempre. La formación en uso se
resalta con un borde blanco y los cambios se aplican al instante: si se
elige durante la pausa, el equipo recibe el nuevo dibujo táctico con un
saque al centro; también queda fijada para las partidas que se inicien
después. Tras elegir una formación se puede seguir ajustando el detalle
de cada jugador en el editor de posiciones.

## Repeticiones de gol

Cada gol se revive en cámara lenta: durante el partido se graba de forma
continua un buffer circular con los últimos **4 segundos** de juego y,
cuando el balón entra en la portería, la jugada completa (hasta el balón
dentro de la red) queda congelada. Tras la celebración del gol arranca
la **REPETICIÓN** a **0,4×** de velocidad, con una cartela cian sobre el
campo que indica que se está reviviendo la jugada y el aviso para
saltarla.

- ESPACIO durante la celebración pasa directamente a la repetición.
- ESPACIO durante la repetición la salta y saca de centro.
- Al terminar sola, la repetición desemboca en el saque del centro.

La grabación solo guarda posiciones (balón y 22 jugadores con su aro de
posesión), así que no afecta al rendimiento del partido. La velocidad y
la duración del buffer se ajustan en `configuracion.py`
(`REPETICION_SEGUNDOS` y `VELOCIDAD_REPETICION`).

## Guardado en SQLite

Todo lo que se personaliza en los menús queda guardado en una base de
datos SQLite (`futbol_silueta.sqlite`, junto al proyecto o al
ejecutable) y se recupera al arrancar:

| Tabla | Contenido |
| --- | --- |
| `ajustes` | Sonido, escudo (color, borde y forma), dorsales visibles, formación táctica y los uniformes de los dos equipos |
| `jugadores` | Las 22 fichas de la plantilla: nombre, dorsal, rol, posición y factores de velocidad y fuerza |

Los datos se guardan al empezar o reiniciar un partido y al cerrar el
juego (por cualquier vía, incluso cerrando la ventana). Si la base no
existe se crea con los valores por defecto; si está dañada o bloqueada,
el juego sigue funcionando con los valores en memoria y no guarda, sin
avisos ni fallos. La carga es atómica: una base con datos a medias no
deja los menús en un estado mezclado.

## Requisitos

- Python **3.11 o superior** (se usa `StrEnum`).
- `pygame` o `pygame-ce`.

Instalación recomendada:

```bash
pip install -r requirements.txt
```

## Cómo ejecutar

Si aún no tienes el proyecto:

```bash
git clone https://github.com/pinedacorderooscarricardo-ai/futbol-silueta.git
cd futbol-silueta
```

Desde la carpeta del proyecto:

```bash
python main.py
```

## Crear un ejecutable

El proyecto incluye `build_exe.ps1`, que usa **PyInstaller** para generar
un único `dist/FutbolSilueta.exe` con las imágenes incluidas:

```powershell
pip install pyinstaller
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

No hace falta copiar la carpeta `imagenes/` junto al ejecutable: los
fondos se empaquetan dentro. La primera apertura puede tardar unos
segundos porque el formato de un solo archivo se descomprime en una
carpeta temporal. El ejecutable no se incluye en el repositorio: se
genera localmente en `dist/` con el script anterior.

## Controles

| Tecla | Acción |
| --- | --- |
| `WASD` o flechas | Mover al jugador controlado |
| `SHIFT` | Sprintar mientras quede energía |
| `ESPACIO` | Chutar / avanzar tras un gol (celebración → repetición → saque), descanso o final |
| `E` | Pasar al compañero más cercano |
| `ESC` | En partido abre la pausa; en menús vuelve o sale |
| Ratón | Elegir y pulsar los botones de los menús |
| Flechas o `W/S` | Elegir una opción en los menús |
| `ENTER` o `ESPACIO` | Confirmar la opción seleccionada en los menús |

Al arrancar se muestra el menú principal. Desde él se puede empezar una
partida, abrir las opciones, ver la ayuda o salir del juego. El partido
no avanza mientras hay un menú abierto.

Al inicio de cada jugada se controla al delantero local más cercano al
centro del campo. El control cambia automáticamente al compañero local
que recibe el balón; si el portero local atrapa un disparo, también pasa
a ser controlado.

### Indicadores en pantalla

| Indicador | Significado |
| --- | --- |
| Dorsal en la camiseta | Número de cada jugador (1-11, se puede ocultar) |
| Aro amarillo | Jugador que lleva el balón |
| Triángulo cian | Jugador controlado por el humano |
| Aro cian | Compañero al que iría el próximo pase (con balón) |
| Cartela "REPETICIÓN" | El gol recién marcado se revive en cámara lenta |
| Barra verde/roja | Energía disponible para sprintar |

## Reglas

- El balón rebota en las bandas y en los fondos; no hay saques de banda
  ni de esquina.
- Un gol se cuenta cuando el balón toca la línea de gol dentro de la
  portería.
- No hay fuera de juego, faltas ni tarjetas.

## Menús y pantallas

El juego usa cuatro ilustraciones propias como fondos de pantalla:

| Imagen | Pantalla |
| --- | --- |
| `imagenes/menu_principal.jpeg` | Menú principal |
| `imagenes/menu_opciones.jpeg` | Configuración |
| `imagenes/menu_pausa.jpeg` | Menú de pausa |
| `imagenes/ayuda_controles.jpeg` | Cómo jugar |

Los botones dibujados en las ilustraciones tienen zonas clicables
alineadas con la imagen, incluso cuando la ventana recorta el fondo para
cubrirla por completo. En el menú principal y en la pausa, la opción
seleccionada se marca con un borde y dos flechas. En configuración y
ayuda, el botón activo se resalta y se puede activar con el ratón o con
el teclado.

- **Menú principal:** JUGAR inicia una partida nueva; OPCIONES abre la
  configuración; CÓMO JUGAR muestra los controles y los indicadores;
  SALIR cierra el juego.
- **Pausa:** se abre con `ESC` durante el partido. Permite continuar,
  reiniciar el partido, abrir la configuración o volver al menú
  principal.
- **Opciones:** activa o desactiva los efectos de sonido (se aplica al
  instante y se conserva mientras el juego esté abierto), abre la
  elección de tácticas, la de uniformes, la del escudo y el editor de
  jugadores, o vuelve atrás.
- **Tácticas:** elige la formación del equipo (4-4-2, 4-3-3, 3-5-2 o
  5-3-2) con vista previa del campo; la formación en uso queda marcada.
- **Cómo jugar:** resume los controles, los indicadores en pantalla y
  las reglas del partido.

`ESC` también funciona como botón "volver" en las pantallas de
configuración, ayuda, escudo, uniformes, editor y tácticas. La navegación usa una
pila: cada pantalla guarda de dónde se llegó, así que `Volver` o `ESC`
regresan siempre a la pantalla anterior aunque se hayan encadenado
varias (por ejemplo Pausa → Opciones → Editor); volver deshace la ruta
paso a paso en lugar de saltar siempre al mismo sitio. En los menús,
las flechas ←/→ ajustan el valor de la opción elegida (colores,
dorsales y otros ajustes que avanzan en ciclo).

## Estructura del proyecto

```text
futbol-silueta/
├── main.py                     # Punto de entrada
├── build_exe.ps1               # Empaquetado con PyInstaller
├── FutbolSilueta.spec          # Configuración generada por PyInstaller
├── requirements.txt
├── README.md
├── verificar_navegacion.py     # Regresión de menús y uniformes (headless)
├── imagenes/
│   ├── menu_principal.jpeg
│   ├── menu_opciones.jpeg
│   ├── menu_pausa.jpeg
│   ├── ayuda_controles.jpeg
│   └── escudos/
│       ├── escudo_01.jpeg
│       ├── escudo_02.jpeg
│       └── ...
├── tests/
│   ├── __init__.py
│   ├── test_juego.py           # Pruebas de la simulación
│   ├── test_menus.py           # Pruebas de menús y botones
│   ├── test_aplicacion.py      # Pruebas del bucle y las pantallas
│   ├── test_escudos.py         # Pruebas de escudos y personalización
│   └── test_guardado.py        # Pruebas de la base de datos SQLite
└── futbol_silueta/
    ├── __init__.py
    ├── configuracion.py        # Constantes, colores, formación y textos
    ├── utilidades.py           # Funciones de ayuda (límites, goles, etc.)
    ├── audio.py                # Efectos de sonido sintetizados
    ├── guardado.py             # Persistencia en SQLite de los ajustes
    ├── entidades.py            # Jugador, Balón y creación de equipos
    ├── escudos.py              # Escudos por nivel y personalización
    ├── uniformes.py            # Equipaciones, dorsales y figura del jugador
    ├── plantilla.py            # Fichas de jugadores: nombres, dorsal y atributos
    ├── repeticion.py           # Instantes congelados para repetir goles
    ├── niveles.py              # Niveles de la campaña y dificultad
    ├── vista.py                # Todo el dibujo de la partida
    ├── menus.py                # Fondos, botones y pantallas de menú
    ├── aplicacion.py           # Bucle principal y cambios de pantalla
    └── juego.py                # Lógica, IA, posesión y estados
```

## Pruebas

La suite usa SDL en modo headless, así que no abre ventana ni necesita
audio real. Incluye 61 pruebas de simulación, repeticiones de gol, menús,
botones, tácticas, guardado, bucle principal, escudos y dibujo:

```bash
python -m unittest discover -s tests -t . -v
```

También se pueden ejecutar los archivos de pruebas directamente:

```bash
python tests/test_juego.py
python tests/test_menus.py
python tests/test_aplicacion.py
```

Además, `verificar_navegacion.py` recorre a mano los flujos de menús,
uniformes y editor (la pila de vuelta, ESC en cada pantalla, el ciclado
de colores por prenda, la edición de nombres y dorsales, los ajustes de
velocidad y fuerza, y la llegada de uniformes y fichas a los jugadores):

```bash
python verificar_navegacion.py
```

## Cambios de esta versión

- Se añadió el guardado en SQLite: sonido, escudo, uniformes, formación
  y las 22 fichas del editor de jugadores se guardan en
  `futbol_silueta.sqlite` al empezar un partido y al cerrar, y se
  recuperan al arrancar.
- La base de datos se crea sola en el primer arranque y es tolerante a
  fallos: si el archivo está dañado o bloqueado, el juego sigue
  funcionando con los valores en memoria.
- Se añadieron las repeticiones de gol: el partido graba en continuo los
  últimos 4 segundos y, tras la celebración, revive la jugada completa
  en cámara lenta (0,4×) con la cartela REPETICIÓN; ESPACIO la salta y
  saca de centro.
- Se añadieron las tácticas: en Opciones → Tácticas se elige la
  formación del equipo entre 4-4-2, 4-3-3, 3-5-2 y 5-3-2, con vista
  previa en vivo del campo, el portero marcado y la formación en uso
  resaltada.
- Elegir una formación recoloca a los 22 jugadores conservando nombres,
  dorsales y atributos; el visitante usa la misma formación reflejada y,
  si se cambia durante la pausa, el equipo se recoloca con un saque al
  centro.
- Se añadió el editor de jugadores: nombres editables con el teclado,
  dorsales del 1 al 99, velocidad y fuerza por jugador (cuatro niveles
  cada una), rol táctico y posición sobre un mini campo, para cada uno
  de los once huecos de los dos equipos.
- La velocidad y la fuerza elegidas afectan al juego: la IA mueve a
  cada jugador según su factor de velocidad y los disparos, pases y
  despejes se escalan con su factor de fuerza.
- Las flechas ←/→ de los menús ahora ajustan la opción elegida hacia
  atrás o adelante, además de ENTER y el clic para avanzar.
- Se corrigió el bloqueo de la navegación: tras visitar la pantalla de
  personalización de escudo, `Volver` y `ESC` en Opciones ya no se
  quedan atrapados volviendo a Opciones (y en pausa ya se puede regresar
  al partido).
- La navegación de menús usa una pila de pantallas: `Volver` y `ESC`
  deshacen la ruta paso a paso (Pausa → Opciones → Uniformes vuelve por
  donde entró) y los saltos grandes, como empezar el partido, limpian la
  pila.
- Se reordenó la pantalla de Opciones para dar cabida a sonido,
  tácticas, uniformes, escudo, editor y volver, y sus textos al pie ya
  no se superponen con el último botón.
- Se añadieron los uniformes personalizados: color de camiseta, pantalón
  y medias para LOCAL y VISITANTE por separado, con diez colores por
  prenda y vista previa de ambos equipos.
- Se añadieron dorsales del 1 al 11 en las camisetas, activables y
  desactivables desde el menú, con color automático para contrastar con
  la camiseta.
- La figura de los jugadores pasó de un círculo plano a una silueta con
  equipación: camiseta, pantalón, medias y dorsal.
- Opciones ahora ofrece: sonido, tácticas, uniformes, personalización
  de escudo, editor de jugadores y volver.
- El marcador y los mensajes de gol hablan de LOCAL y VISITANTE en vez
  de ROJO y AZUL, ya que los colores de las camisetas ya no fijan la
  identidad de los equipos.
- Se integraron las cuatro ilustraciones del juego como menú principal,
  configuración, pausa y ayuda.
- Se añadieron las imágenes de los escudos, uno por nivel
  (`imagenes/escudos/escudo_01.jpeg` a `escudo_11.jpeg`).
- Se dividió el juego en una campaña de niveles: cada nivel es un escudo
  rival distinto y aumenta la dificultad de la IA de forma progresiva.
- Al finalizar un nivel se avanza al siguiente; la campaña vuelve al
  nivel 1 tras el último.
- Se añadió la pantalla de personalización de escudo con colores y
  formas seleccionables para el jugador, con vista previa en vivo.
- El marcador muestra el escudo del jugador, el resultado, el nombre del
  rival y la imagen del escudo del nivel en curso.
- Cada uno de los once niveles tiene su propio color de escudo.
- Tras el último tiempo, el mensaje final invita a pasar al siguiente
  nivel de la campaña.
- El menú principal aparece al arrancar y sus botones inician la partida,
  abren las opciones, muestran la ayuda o cierran el juego.
- `ESC` durante el partido abre el menú de pausa en lugar de salir.
- La pausa permite continuar, reiniciar el partido, abrir la
  configuración o volver al menú principal.
- Los botones se pueden pulsar con el ratón o navegar con las flechas,
  `W/S`, `ENTER` y `ESPACIO`; la selección se resalta sobre la imagen.
- La configuración incluye un interruptor de sonido que afecta a todos
  los efectos del juego.
- Se añadió un triángulo cian para identificar al jugador controlado
  aunque no tenga el balón.
- Los perseguidores de la IA ya no descuentan al jugador humano: el
  equipo conserva sus dos presionadores automáticos.
- El delantero inicial se elige por distancia real al centro del campo,
  no solo por su coordenada vertical.
- La lógica de disparo de la IA y del humano se unificó en `_chutar()`.
- Se añadió una suite de pruebas headless con `unittest` para la
  simulación y los menús.
- El bucle principal se trasladó a `aplicacion.py`; `juego.py` conserva
  solo la lógica y los estados del partido.
- Los fondos se escalan y recortan para cubrir la ventana, y las zonas
  clicables se calculan con la misma transformación que la imagen.
- Se añadió `build_exe.ps1` para crear un ejecutable autónomo con
  PyInstaller, incluyendo las imágenes dentro del `.exe`.
- Se documentaron las reglas arcade y los indicadores de la interfaz.
- Código dividido en módulos con responsabilidades claras.
- `Equipo`, `Estado` y `Rol` son enums: se evitan cadenas mágicas y errores
  de escritura.
- Se eliminó lógica duplicada de límites del campo, paneles y superficies
  con fondo.
- La detección de colisiones usa distancia al cuadrado y solo calcula la
  raíz cuadrada cuando hay solapamiento real.
- Los marcajes usan distancias al cuadrado, evitando raíces innecesarias.
- La síntesis de audio avanza el ángulo de fase en lugar de recalcular el
  tiempo en cada muestra.
- Se conservan las cachés de sprites, campo, marcador y reloj.
- Se añadieron tipos y docstrings para facilitar el mantenimiento.
