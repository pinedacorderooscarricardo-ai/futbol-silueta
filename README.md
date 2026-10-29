# Fútbol Silueta

Juego 2D de fútbol para dos equipos de 11 jugadores, hecho con **pygame**.
Incluye IA para el equipo visitante, conducción de balón, pases, robos,
sprint con energía, atajadas, marcaje, un partido de dos tiempos de
3 minutos y menús ilustrados con botones clicables.

## Requisitos

- Python **3.11 o superior** (se usa `StrEnum`).
- `pygame` o `pygame-ce`.

Instalación recomendada:

```bash
pip install -r requirements.txt
```

## Cómo ejecutar

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
carpeta temporal.

## Controles

| Tecla | Acción |
| --- | --- |
| `WASD` o flechas | Mover al jugador controlado |
| `SHIFT` | Sprintar mientras quede energía |
| `ESPACIO` | Chutar / continuar tras un gol, descanso o final |
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
| Aro amarillo | Jugador que lleva el balón |
| Triángulo cian | Jugador controlado por el humano |
| Aro cian | Compañero al que iría el próximo pase (con balón) |
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
- **Opciones:** activa o desactiva los efectos de sonido. El ajuste se
  aplica al instante y se conserva mientras el juego esté abierto.
- **Cómo jugar:** resume los controles, los indicadores en pantalla y
  las reglas del partido.

`ESC` también funciona como botón "volver" en las pantallas de
configuración y ayuda.

## Estructura del proyecto

```text
proyecto0000000000.1/
├── main.py                     # Punto de entrada
├── build_exe.ps1               # Empaquetado con PyInstaller
├── FutbolSilueta.spec          # Configuración generada por PyInstaller
├── dist/
│   └── FutbolSilueta.exe       # Ejecutable listo para usar
├── requirements.txt
├── README.md
├── imagenes/
│   ├── menu_principal.jpeg
│   ├── menu_opciones.jpeg
│   ├── menu_pausa.jpeg
│   └── ayuda_controles.jpeg
├── tests/
│   ├── __init__.py
│   ├── test_juego.py           # Pruebas de la simulación
│   ├── test_menus.py           # Pruebas de menús y botones
│   └── test_aplicacion.py      # Pruebas del bucle y las pantallas
└── futbol_silueta/
    ├── __init__.py
    ├── configuracion.py        # Constantes, colores, formación y textos
    ├── utilidades.py           # Funciones de ayuda (límites, goles, etc.)
    ├── audio.py                # Efectos de sonido sintetizados
    ├── entidades.py            # Jugador, Balón y creación de equipos
    ├── vista.py                # Todo el dibujo de la partida
    ├── menus.py                # Fondos, botones y pantallas de menú
    ├── aplicacion.py           # Bucle principal y cambios de pantalla
    └── juego.py                # Lógica, IA, posesión y estados
```

## Pruebas

La suite usa SDL en modo headless, así que no abre ventana ni necesita
audio real. Incluye 25 pruebas de simulación, menús, botones, bucle
principal y dibujo:

```bash
python -m unittest discover -s tests -t . -v
```

También se pueden ejecutar los archivos de pruebas directamente:

```bash
python tests/test_juego.py
python tests/test_menus.py
python tests/test_aplicacion.py
```

## Cambios de esta versión

- Se integraron las cuatro ilustraciones del juego como menú principal,
  configuración, pausa y ayuda.
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
