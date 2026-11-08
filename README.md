# Fútbol Silueta

Juego 2D de fútbol para dos equipos de 11 jugadores, hecho con **pygame**.
Incluye IA para el equipo visitante, conducción de balón, pases, robos,
sprint con energía, atajadas, marcaje, un partido de dos tiempos de
3 minutos, menús ilustrados con botones clicables, una campaña de
niveles, la personalización del escudo del jugador, uniformes
personalizados, un editor de jugadores con nombres, dorsales,
atributos y posiciones, tácticas con cuatro formaciones seleccionables
(4-4-2, 4-3-3, 3-5-2 y 5-3-2) y un banquillo de suplentes con
sustituciones en vivo desde la pausa.

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

## Suplentes y sustituciones

La plantilla completa son **18 jugadores por equipo** (formato 18-23 del
fútbol): los once titulares que se ven en el editor más un **banquillo
de 7 suplentes** con dorsales del 12 al 18 — un portero, dos defensas,
dos medios y dos delanteros. Los suplentes comparten el sistema del
editor: cada uno tiene su nombre, dorsal, rol y atributos por defecto,
y el tamaño del banquillo es ajustable en `configuracion.py`
(`NUMERO_SUPLENTES`, hasta 12 para un acta de 23).

Los cambios se hacen desde el partido: `ESC` abre la pausa y el botón
**Cambios de jugadores** muestra la pantalla de sustituciones, con los
once jugadores en campo a la izquierda y el banquillo disponible a la
derecha. Se marca al que sale y al que entra (con clic o con el teclado,
segundo toque para desmarcar) y el botón **Confirmar** ejecuta el
cambio; la pareja elegida queda resaltada y cada equipo dispone de
**5 cambios por partido** (tope ajustable con `SUSTITUCIONES_MAXIMAS`).

El sustituto hereda el hueco táctico del que sale (rol y posición),
conservando su nombre, su dorsal y sus atributos, y el que sale pasa al
banquillo (no puede volver a entrar este partido, como en el fútbol
real, porque ya no está disponible en la lista de suplentes). El cambio
se aplica en el momento sin cortar la jugada: si el que salía era el
jugador controlado o llevaba el balón, el control y la posesión pasan al
que entra. Al empezar o reiniciar una partida el banquillo y el cupo de
cambios vuelven a su estado original.

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
| `ajustes` | Sonido, escudo (color, borde y forma), dorsales visibles, formación táctica, los uniformes de los dos equipos y el estadio (césped, momento, diseño y gradas) |
| `jugadores` | Las 22 fichas de la plantilla: nombre, dorsal, rol, posición y factores de velocidad y fuerza |

Los datos se guardan al empezar o reiniciar un partido y al cerrar el
juego (por cualquier vía, incluso cerrando la ventana). Si la base no
existe se crea con los valores por defecto; si está dañada o bloqueada,
el juego sigue funcionando con los valores en memoria y no guarda, sin
avisos ni fallos. La carga es atómica: una base con datos a medias no
deja los menús en un estado mezclado.

## Estadios personalizados

En **Opciones → Estadio** se configura el escenario del partido con
vista previa en vivo del conjunto:

- **Césped:** claro, oscuro o artificial (este último, más uniforme y
  con un tono azulado).
- **Momento:** de día, a plena luz, o de noche, con todo el estadio
  atenuado y el público apagado.
- **Clima:** despejado, lluvia o nieve. No es solo visual: con lluvia
  el balón rueda más (menos fricción) y con nieve se frena antes. La
  lluvia dibuja chubascos sobre el campo y la nieve, copos a la deriva.
- **Gradas:** con aficionados sentados alrededor de la cancha o un
  cordón de césped vacío. El público se genera con una semilla fija,
  así que cada estadio se ve igual en todas las partidas.
- **Diseño de cancha:** clásico (liso), rayas de corte, ajedrez o
  anillos concéntricos desde el círculo central.

El estadio elegido se aplica al iniciar o reiniciar una partida: el
fondo se pre-renderiza una sola vez por configuración, así que no
cuesta nada por fotograma. También queda guardado en la base de datos
junto al resto de la personalización. La opción en curso se marca en
la etiqueta de cada botón y las flechas ←/→ ajustan césped, momento,
clima y diseño hacia atrás o adelante.

## Porteros inteligentes

Los dos porteros ya no se limitan a seguir el balón: cubren el ángulo,
**anticipan los disparos**, **se lanzan** y **cometen errores** según
su calidad. Cuando detectan un disparo rápido hacia su arco, esperan
su tiempo de reacción, predicen dónde cruzará el balón proyectando su
trayectoria y se lanzan si el punto queda fuera de su alcance; durante
el lance sus manos llegan más lejos (aro blanco sobre el portero).

La calidad del **portero rival** escala con el nivel de la campaña: en
los primeros niveles se equivoca a menudo (se lanza al palo equivocado
o llega tarde), tarda en reaccionar y adivina poco la trayectoria; en
los últimos casi no falla. El **portero local** tiene calidad fija:
seguro pero no perfecto. Cuando un portero "falla" un disparo, se lanza
igualmente —al sitio equivocado— y el balón se le escapa entre las
manos. Los ajustes de lances y errores están en `configuracion.py` y
las calidades por nivel en `porteros.py`.

## Estadísticas y palmarés

**Estadísticas del partido:** en el descanso y en el final, el panel
del mensaje muestra las cifras del encuentro de los dos equipos:
posesión (porcentaje de tiempo con el balón controlado), disparos,
pases (incluidos los despejes de los porteros) y atajadas. Los goles
están siempre en el marcador.

**Palmarés de la campaña** (**Opciones → Palmarés**), en tres columnas:

- **Posiciones:** la tabla de la campaña con TU CLUB y los 11 rivales:
  puntos (3 por victoria, 1 por empate), victorias, empates y derrotas,
  goles a favor y en contra, ordenada por puntos y diferencia.
- **Resultados:** el historial de los últimos partidos (nivel y
  marcador final), del más reciente al más viejo.
- **Trofeos:** los premios por logros — PRIMERA VICTORIA, GOLEADA
  (ganar por 3 o más), VALLA INVICTA, ARTILLERO (5 goles en un
  partido) y CAMPEÓN (completar la campaña ganando el nivel 11). Los
  logrados se muestran en oro y los que faltan, apagados.

Todo se registra automáticamente: al terminar un partido se actualizan
tabla, historial y trofeos (los nuevos se anuncian en el panel del
final), y la campaña continúa en el nivel donde quedó entre sesiones.
El guardado automático lo conserva todo en la base SQLite junto con
las personalizaciones.

## Narrador y repeticiones a demanda

Cada gol lleva su **comentario**: bajo el "¡GOOOL!" aparece una frase
del narrador con el nombre del autor (quien tocó el balón por última
vez antes de cruzar la línea), elegida entre varias variantes.

Además de la repetición automática de cada gol, con **R** (en juego
corriente) se vuelve a ver en cámara lenta la **última mejor jugada**
guardada: el partido se congela tal como está, se reproduce la jugada
con la cartela REPETICIÓN y, al terminar (o con ESPACIO), todo vuelve
exactamente a como estaba. Siempre están a mano las tres últimas.

## IA más impredecible

La rival ya no repite el mismo guion partido tras partido:

- **IA adaptativa:** cada 5 segundos muestrea tu estilo y ajusta su
  bloque: se corre hacia el lado por el que más atacas y, si disparas
  con frecuencia, presiona con un jugador más.
- **Contraataques:** al robar cerca de tu arco con la defensa lanzada,
  sale a la carrera: conduce más rápido y dispara desde más lejos
  durante unos segundos.
- **Cambios tácticos:** si va perdiendo en el segundo tiempo, pasa su
  bloque a la formación remontada (4-3-3) hasta la siguiente jugada.
- **Sustituciones:** los rivales se cansan persiguiendo y conduciendo
  (corren hasta un 30 % menos agotados) y la IA rota al compañero más
  fresco de su misma posición para cubrir la zona.
- **Marcaje individual:** cada defensa sigue siempre al mismo rival
  mientras sea válido; las parejas se heredan entre posesiones y solo
  se cubren los huecos nuevos.
- **Juego colectivo:** los dos compañeros más cercanos al portador
  buscan espacios para recibir, adelantados hacia el arco y abiertos a
  banda (también los tuyos, cuando la IA conduce por ti).

## Presentación de transmisión

- **Marcador televisivo:** el marcador es un bug de transmisión, con
  el escudo de cada equipo, el resultado en grande, el nivel y el
  rival debajo, un punto rojo de "EN VIVO" y una franja en el borde
  con el color de la camiseta de cada equipo.
- **Cámara dinámica:** el encuadre persigue al balón con suavizado y
  hace zoom cuando corre a toda velocidad o ronda las áreas; en juego
  tranquilo vuelve al plano completo. Los marcadores y mensajes
  siempre se ven enteros, como en televisión.
- **Animaciones:** los jugadores zancan al correr (la fase avanza con
  los pasos), saltan para celebrar los goles y caen al suelo cuando
  les roban el balón o cuando son batidos.
- **Reacciones del portero:** atrapa de pie y celebra con un salto;
  si atrapa en pleno lance, cae al suelo; y cuando le marcan, se queda
  tumbado un buen rato.
- **Aficionados reaccionan:** la grada estalla con los goles y
  vitorea las ocasiones (atajadas): confeti animado en las tribunas
  cuya intensidad sube con la emoción y se apaga poco a poco.
- **Clima avanzado:** el viento cambia de dirección y fuerza de vez en
  cuando (según el clima: más tormenta, más viento) y empuja de verdad
  la trayectoria del balón libre; un indicador junto al reloj muestra
  hacia dónde sopla.

## Modos de juego

En **JUGAR** se abre el selector de **modos de juego**; la campaña es
el primero y el resto son nuevos:

- **Campaña:** los once niveles clásicos, uno tras otro.
- **Liga:** todos contra todos en 11 jornadas por puntos (3 por
  victoria, 1 por empate). Los demás partidos de cada jornada se
  simulan por la fuerza de cada equipo, así que la clasificación es
  una tabla real; el texto final muestra tu posición y el campeón.
- **Copa:** eliminación directa de 8 equipos (cuartos, semifinal y
  final). Un empate se decide por penaltis.
- **Copa de Campeones:** dos grupos de 4; los dos primeros de cada
  uno pasan a las semifinales cruzadas y luego a la gran final.
- **Supervivencia:** gana y el rival sube de nivel; pierde (o empata)
  y se acaba el intento, con tu racha como récord.
- **Entrenamiento:** campo abierto sin oposición ni reloj para
  practicar tiros, pases y regates contra el portero.
- **Dos jugadores:** dos personas en el mismo teclado. Jugador 1:
  WASD, SHIFT izquierdo, ESPACIO y E; jugador 2: flechas, SHIFT
  derecho, ENTER y CTRL derecho, cada uno con su barra de energía.

En los torneos, el marcador muestra la competición y la ronda en
curso (LIGA · J3/11, COPA · SEMIFINAL, ...), la pantalla final resume
tu situación y, al terminar el torneo, su desenlace antes de volver
al menú. Los torneos **se guardan en la base de datos** (tabla
`torneos`): al elegir un modo se reanuda el torneo guardado de ese
modo en el punto donde estaba —jornada, ronda, clasificación o
racha— y, una vez terminado, se borra para que el siguiente empiece
de cero. Como solo hay un torneo activo por modo, puedes tener una
Liga a medias y una Copa a medias a la vez.

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
| `Q` | Cambiar el jugador controlado (cicla entre los locales por cercanía al balón) |
| `R` | Volver a ver en cámara lenta la última mejor jugada |
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

También se puede cambiar de futbolista a mano con `Q`: cada pulsación
entrega el control al siguiente jugador de campo local más cercano al
balón, así que la primera ya toma al más conveniente y las siguientes
recorren al resto (diez pulsaciones dan la vuelta completa). Con
posesión local el control acompaña siempre a quien lleva el balón.

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

- El balón rebota en las bandas. En las líneas de fondo: gol si entra
  por la portería, córner si sale tras tocar al equipo defensor y
  rebote en cualquier otro caso (no hay saques de banda ni de puerta).
- Un gol se cuenta cuando el balón toca la línea de gol dentro de la
  portería.
- No hay fuera de juego, faltas ni tarjetas.

## Saques de esquina

Cuando el balón sale por una línea de fondo y el último toque fue de
un jugador del equipo que defiende ese arco, se pita **córner**: suena
el silbato, aparece la cartela CÓRNER y la jugada se congela un
instante. Después el balón se coloca en el vértice de la esquina por
la que salió (izquierda o derecha, arriba o abajo) y el jugador de
campo más cercano del equipo que cobra se sitúa junto a él para sacar
conduciendo; si el córner es del local, tomas tú el control del
cobrador. ESPACIO adelanta la colocación sin esperar la pausa. Si el
último toque fue del equipo atacante, el balón simplemente rebota.

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
  reiniciar el partido, abrir la configuración, volver al menú
  principal o hacer cambios de jugadores (sustituciones).
- **Opciones:** activa o desactiva los efectos de sonido (se aplica al
  instante y se conserva mientras el juego esté abierto), abre la
  elección de tácticas, la de uniformes, la del escudo, el editor de
  jugadores, la del estadio y el palmarés, o vuelve atrás.
- **Tácticas:** elige la formación del equipo (4-4-2, 4-3-3, 3-5-2 o
  5-3-2) con vista previa del campo; la formación en uso queda marcada.
- **Estadio:** personaliza el césped (claro, oscuro o artificial), el
  momento (día o noche), el clima (despejado, lluvia o nieve), las
  gradas con aficionados y el diseño de corte de la cancha, con vista
  previa en vivo.
- **Palmarés:** la tabla de posiciones de la campaña, el historial de
  resultados y los trofeos desbloqueados.
- **Cómo jugar:** resume los controles, los indicadores en pantalla y
  las reglas del partido.

`ESC` también funciona como botón "volver" en las pantallas de
configuración, ayuda, escudo, uniformes, editor, tácticas, estadio y
palmarés. La navegación usa una
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
│   ├── test_guardado.py        # Pruebas de la base de datos SQLite
│   ├── test_porteros.py        # Pruebas de los porteros inteligentes
│   └── test_modos.py           # Pruebas de liga, copa y demás modos
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
    ├── porteros.py             # IA de porteros: anticipación, lances y errores
    ├── modos.py                # Modos de juego: liga, copa, campeones, etc.
    ├── repeticion.py           # Instantes congelados para repetir goles
    ├── estadisticas.py         # Cifras del partido, tabla, historial y trofeos
    ├── estadios.py             # Césped, momento, gradas y diseño de cancha
    ├── niveles.py              # Niveles de la campaña y dificultad
    ├── vista.py                # Todo el dibujo de la partida
    ├── menus.py                # Fondos, botones y pantallas de menú
    ├── aplicacion.py           # Bucle principal y cambios de pantalla
    └── juego.py                # Lógica, IA, posesión y estados
```

## Pruebas

La suite usa SDL en modo headless, así que no abre ventana ni necesita
audio real. Incluye 149 pruebas de simulación, modos de juego, IA adaptativa
y táctica rival, presentación de transmisión, porteros inteligentes,
repeticiones de gol, cambio de jugador, córners, estadísticas,
palmarés y clima, suplentes y sustituciones, banquillo por defecto,
estadios, menús, botones, tácticas, guardado, bucle principal, escudos,
utilidades (carga de imágenes con reserva y plantillas incompletas)
y dibujo:

```bash
python -m unittest discover -s tests -t . -v
```

Si necesitas capturar la salida en PowerShell con `2>&1`, hazlo dentro
de `cmd /c`: `unittest` escribe su progreso en `stderr` y PowerShell 5.1
puede interpretarlo como un error aunque la suite termine bien.

También se pueden ejecutar los archivos de pruebas directamente:

```bash
python tests/test_juego.py
python tests/test_menus.py
python tests/test_aplicacion.py
```

Además, `verificar_navegacion.py` recorre a mano los flujos de menús,
uniformes, editor, repeticiones, estadio, palmarés, córners, IA
adaptativa y cambio de jugador (la pila de vuelta, ESC en cada
pantalla, el ciclado de colores por prenda, la edición de nombres y
dorsales, los ajustes de velocidad y fuerza, el clima, el
re-visionado con R y la llegada de uniformes, fichas y estadio a los
jugadores):

```bash
python verificar_navegacion.py
```

## Cambios de esta versión

- Se añadieron los modos de juego: JUGAR abre un selector con la
  campaña clásica y seis modos nuevos —Liga por puntos con jornada y
  clasificación simulada, Copa de eliminación directa, Copa de
  Campeones con grupos y finales, Supervivencia de dificultad
  creciente, Entrenamiento sin oposición ni reloj y Dos jugadores en
  el mismo teclado con energías separadas.
- En los torneos el marcador muestra la ronda en curso y la pantalla
  final narra la situación; el desenlace del torneo se muestra antes
  de volver al menú principal.
- Los torneos se guardan en la base de datos y se reanudan al volver
  a elegir su modo: jornada y clasificación de la Liga, ronda de la
  Copa, fase y grupos de Campeones y racha de Supervivencia.
- Se añadieron los suplentes y las sustituciones: plantilla de 18
  jugadores (11 titulares + banquillo de 7, ampliable hasta 23) y
  cambios en vivo desde la pausa con la pantalla Cambios de jugadores,
  con tope de 5 cambios por equipo, transferencia del control y del
  balón al que entra y banquillo que se restablece en cada partido.
- Se añadió la presentación de transmisión: marcador televisivo con
  colores de equipo y aviso EN VIVO, cámara dinámica con zoom y
  seguimiento del balón, animaciones de carrera, salto y caída,
  celebraciones de gol, reacciones del portero según la atajada,
  aficionados que reaccionan a goles y ocasiones con confeti, y viento
  dinámico que desvía el balón según el clima.

- Se renovó la IA para hacer los partidos menos predecibles: aprende
  tu estilo (lado de ataque y frecuencia de disparo) y ajusta presión
  y bloque lateral; sale al contraataque cuando roba con espacios;
  cambia a la formación remontada al ir perdiendo; rota a sus
  jugadores cansados, que corren menos según se agotan; marca a un
  rival fijo por defensa y sus compañeros buscan espacios para
  recibir pases.
- Se añadieron los saques de esquina: si el balón sale por la línea de
  fondo tras tocar al equipo defensor, se pita córner con su cartela y
  el balón se coloca en el vértice para que cobre el jugador del equipo
  atacante más cercano; con ESPACIO se adelanta la colocación.
- Se añadieron las estadísticas del partido: posesión, disparos, pases
  y atajadas de los dos equipos, mostradas en el panel del descanso y
  del final (los goles, en el marcador).
- Se añadió el palmarés de la campaña en Opciones → Palmarés: tabla de
  posiciones con puntos, victorias, empates y derrotas contra los 11
  rivales, historial de los últimos resultados y sistema de trofeos
  (PRIMERA VICTORIA, GOLEADA, VALLA INVICTA, ARTILLERO y CAMPEÓN).
- Se añadió el narrador: cada gol muestra un comentario aleatorio con
  el nombre del autor bajo el mensaje de gol.
- Con `R` se vuelve a ver en cámara lenta la última mejor jugada: el
  partido se congela y se restaura exactamente tras la repetición.
- El guardado automático conserva ahora también la campaña (nivel en
  curso), la tabla, el historial y los trofeos; las bases anteriores se
  migran solas.
- Se añadió el clima dinámico al estadio: despejado, lluvia o nieve,
  con partículas sobre el campo y fricción del balón distinta por
  clima (con lluvia rueda más, con nieve se frena antes).
- Se añadió el cambio manual de jugador: con `Q` el control pasa al
  siguiente jugador de campo local más cercano al balón (la primera
  pulsación toma al más conveniente y el ciclo da la vuelta completa);
  con posesión local el control acompaña siempre a quien conduce.
- Se añadieron los porteros inteligentes: anticipan los disparos
  proyectando la trayectoria del balón, se lanzan hacia el punto de
  intercepción (con aro blanco y manos más amplias durante el lance) y
  cometen errores —llegan tarde, se lanzan al palo equivocado o dejan
  escapar el balón— según su calidad.
- La calidad del portero rival escala con el nivel de la campaña (en el
  1 falla mucho y en el 11 casi nada); el portero local mantiene una
  calidad fija, segura pero no perfecta.
- Robustez de assets: las imágenes (escudos y fondos de menú) se cargan
  con una reserva generada si el archivo falta o está dañado, en lugar
  de abortar al arrancar; el localizador de imágenes vive en un solo
  lugar (`utilidades`) y ya no está duplicado.
- La plantilla guardada se normaliza a once fichas por equipo al crear
  a los jugadores: si quedó corta o larga (datos antiguos o dañados), el
  campo siempre sale completo con los jugadores por defecto.
- Las formaciones de tácticas tienen un único catálogo (`FORMACIONES`):
  los nombres del menú se derivan de él, así que añadir una táctica
  nueva es una sola entrada.
- Los botones de menú validan su valor (tipo e índice) antes de usarlo
  y la puntería de la IA usa una constante documentada en vez de un
  número mágico.
- Se añadieron los estadios personalizados: césped claro, oscuro o
  artificial; estadio de día o de noche; gradas con aficionados
  generados con semilla fija; y cuatro diseños de corte de la cancha
  (clásico, rayas, ajedrez y círculos), todo con vista previa en vivo
  en Opciones → Estadio y aplicado al fondo del partido.
- Se añadió el guardado en SQLite: sonido, escudo, uniformes, formación,
  estadio y las 22 fichas del editor de jugadores se guardan en
  `futbol_silueta.sqlite` al empezar un partido y al cerrar, y se
  recuperan al arrancar. Las bases creadas antes de los estadios se
  migran solas con los valores por defecto.
- La base de datos se crea sola en el primer arranque y es tolerante a
  fallos: si el archivo está dañado o bloqueado, el juego sigue
  funcionando con los valores en memoria.
- La carga sanea cada campo por separado: los colores fuera de rango se
  recortan a 8 bits, las opciones o formaciones desconocidas usan su
  valor por defecto y una plantilla corta o con fichas dañadas se
  completa sin descartar las fichas válidas ni el resto de los ajustes.
- La miniatura del estadio y el cursor del ratón se cachean: la vista
  previa solo se repinta al cambiar el estadio y el cursor solo se
  actualiza cuando su estado realmente cambia.
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
