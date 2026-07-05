# Plan: caniarun CLI → TUI (Textual) + integración de Benchmark Run Log

Documento para ejecutar paso a paso con un agente de código (Antigravity).
Cada fase es un ticket chico, testeable de forma independiente. No pasar a la
siguiente fase hasta confirmar que la anterior corre.

---

## 0. Decisión técnica

- **Framework:** [Textual](https://textual.textualize.io/) (Python puro, corre
  en cualquier terminal, soporta mouse + teclado, CSS-like styling, widgets
  reactivos como `DataTable`, `TabbedContent`, `Input`, `OptionList`).
- **Por qué y no otra cosa:** ya estás en Python, cero necesidad de reescribir
  la lógica core (`hardware.py`, `compat.py`, `models/`, `gpu_db.py`) — Textual
  solo reemplaza la capa de `print()`/`input()` por widgets. Además la
  actividad académica lista explícitamente "Textual" como opción válida de
  interfaz.
- **Instalación:**
  ```fish
  pip install textual textual-dev --break-system-packages
  ```
  `textual-dev` da hot-reload y un inspector visual (`textual run --dev app.py`).

**Regla de oro para todo el plan:** la lógica de negocio (detección de
hardware, cálculo de compatibilidad, catálogo de modelos, normalización de
benchmarks) NUNCA vive dentro de un archivo de pantalla (`Screen`). Las
pantallas solo llaman funciones que ya existen y renderizan el resultado. Así
no rompés nada de lo que ya funciona y la separación de responsabilidades
queda intacta (importa para la nota técnica también).

---

## 1. Estructura de archivos propuesta

```
src/caniarun/
├── hardware.py            # SIN CAMBIOS
├── compat.py               # SIN CAMBIOS
├── gpu_db.py                # SIN CAMBIOS
├── models/                   # SIN CAMBIOS
├── benchmarklog/              # el módulo que ya armamos, movido aquí tal cual
│   ├── schema.py
│   ├── source_detection.py
│   ├── normalizer.py
│   ├── validator.py
│   ├── metrics.py
│   └── config/rules_config.json
└── tui/                        # TODO LO NUEVO vive acá
    ├── app.py                   # clase App principal, define screens y bindings
    ├── styles.tcss                # theming (colores verde/naranja/cyan del screenshot)
    ├── widgets/
    │   ├── hardware_banner.py     # el panel "Your Hardware"
    │   └── status_badge.py         # el [🧈 Smooth as butter] coloreado
    └── screens/
        ├── home.py                  # menú principal
        ├── all_models.py             # opción 1
        ├── filter_family.py           # opción 2
        ├── compat_table.py             # opción 3
        ├── export_log.py                # opción 4
        └── benchmark_log/                # opción 6 (nueva)
            ├── screen.py                  # TabbedContent con las 4 vistas
            ├── tab_valid.py
            ├── tab_filter.py
            ├── tab_invalid.py
            └── tab_metrics.py
```

`data.py` legacy (el script actual de `caniarun.sh`) queda intacto hasta la
Fase 5, por si algo sale mal y necesitás volver atrás rápido.

---

## 2. Fases (tickets para el agente, en orden)

### Fase 0 — Setup mínimo
- Agregar `textual` y `textual-dev` a dependencias del proyecto.
- Crear `src/caniarun/tui/app.py` con una `App` vacía que solo muestra un
  `Static("hola caniarun")`.
- **Criterio de aceptación:** `textual run src/caniarun/tui/app.py` abre una
  ventana con ese texto, sin errores.

### Fase 1 — Home screen (paridad visual con el screenshot actual)
- Widget `HardwareBanner`: reproduce el panel superior ("Your Hardware",
  GPU/VRAM/RAM/OS/Share ID) leyendo de la función que ya usa `hardware.py`
  hoy (no reimplementar detección, solo consumirla).
- Widget del ASCII art del logo (`('v') caniarun`) como `Static`.
- `HomeScreen`: menú con `OptionList` mostrando las mismas 5 opciones actuales
  + una nueva `[6] Benchmark Run Log`.
- **Criterio de aceptación:** se ve igual que el screenshot, navegable con
  flechas + Enter, sin lógica de negocio todavía (las opciones no hacen nada).

### Fase 2 — Migrar las 5 pantallas existentes
Portar cada opción actual a un `Screen` de Textual, sin cambiar el
comportamiento, solo el renderizado:

| # | Pantalla | Widget principal | Nota |
|---|---|---|---|
| 1 | Show all models (log format) | `DataTable` | columnas: timestamp, familia, modelo, vibe, tok/s |
| 2 | Filter by family | `Input` + `DataTable` reactivo | filtra la tabla de la opción 1 en vivo con `on_input_changed` |
| 3 | Full compatibility table | `DataTable` | agregar color por estado (`can-run`=verde, `tight`=amarillo, `can-run-slow`=naranja, `cannot-run`=rojo) usando estilos de celda |
| 4 | Export log file | `Static` + confirmación | reusa la función de export actual, solo cambia el `print` final por un mensaje en pantalla |
| 5 | Exit | binding `q` / `escape` | Textual lo da gratis con `Binding("q", "quit")` |

- **Criterio de aceptación:** las 4 pantallas de datos (1,2,3,4) muestran
  exactamente los mismos datos que la versión CLI actual, solo que en TUI.

### Fase 3 — Integrar Benchmark Run Log como nueva sección
- Mover el módulo `benchmarklog/` (ya armado y probado, 7 válidos / 7
  inválidos con los datos de prueba) a `src/caniarun/benchmarklog/` tal cual.
- Escribir un test rápido (`pytest` o incluso un script suelto) que confirme
  que `process_records()` sigue devolviendo 7/7 después del move — así sabés
  que no rompiste nada al reubicar imports.
- Nueva pantalla `BenchmarkLogScreen` con `TabbedContent` (4 tabs):
  - **Tab "Runs válidos":** `DataTable` (igual a la que ya armamos en la CLI, pero interactiva: click en columna para ordenar).
  - **Tab "Filtrar":** dos `Input` (estado, modelo) que filtran la tabla de arriba en vivo.
  - **Tab "Inválidos":** `DataTable` con columnas fuente/motivos.
  - **Tab "Métricas":** panel con los números de `compute_metrics()` (total, válidas, inválidas, por estado, por quant tier, promedios) — se puede mostrar como texto formateado o con `Sparkline`/barras simples si querés algo más visual.
- Conectar `[6] Benchmark Run Log` del menú principal a esta pantalla.
- **Criterio de aceptación:** navegás Home → [6] → ves las 4 tabs, los
  filtros funcionan sin recargar la pantalla.

### Fase 4 — Polish
- Archivo `styles.tcss` con la paleta del screenshot (verde `#00ff9c`-ish,
  naranja para el título, cyan para hardware) aplicada consistentemente en
  todas las pantallas nuevas.
- `Footer` widget de Textual (da los hints de teclado gratis, tipo "q Quit").
- Si la detección de hardware puede demorar, usar un `Worker` de Textual
  (async) para no bloquear la UI, con un `LoadingIndicator` mientras tanto.
- Manejo de error: si `hardware.py` no detecta VRAM (como en tu screenshot,
  "VRAM: N/A"), mostrar un aviso claro en el banner en vez de dejarlo vacío.

### Fase 5 — Cleanup
- Confirmar que `caniarun.sh` ahora invoca la TUI directamente, reemplazando
  el script viejo de prints. **Decisión: reemplazo total, sin flag `--legacy`.**
- Eliminar por completo el código de menú basado en `input()`/`print()` una
  vez que la TUI esté validada (no dejarlo muerto en el repo).
- Actualizar el `README.md` del proyecto con instrucciones de instalación de
  `textual` y screenshot nuevo.

---

## 3. Orden sugerido de tickets para tu agente (uno por vez)

1. Setup Textual + App vacía (Fase 0)
2. HardwareBanner widget + ASCII logo (Fase 1)
3. HomeScreen con OptionList y navegación esqueleto (Fase 1)
4. Pantalla "Show all models" con DataTable (Fase 2)
5. Pantalla "Filter by family" reactiva (Fase 2)
6. Pantalla "Compatibility table" con colores por estado (Fase 2)
7. Pantalla "Export log" (Fase 2)
8. Mover `benchmarklog/` al proyecto real + test de regresión 7/7 (Fase 3)
9. `BenchmarkLogScreen` con las 4 tabs (Fase 3)
10. Conectar `[6]` en el menú principal (Fase 3)
11. `styles.tcss` + Footer + manejo de loading/errores (Fase 4)
12. Cleanup del modo viejo + README (Fase 5)

Cada ticket debe terminar con algo corrible (`textual run`) antes de pasar al
siguiente — así si el agente rompe algo en el ticket 9, no perdiste los 8
anteriores.

---

## 4. Riesgos a tener en cuenta

- **Terminal sin true-color:** Textual degrada solo, pero probá en la
  terminal real que usás (fish + CachyOS) antes de asumir que los colores del
  screenshot se ven igual.
- **Bloqueo de UI en detección de hardware:** si `nvidia-smi`/`lspci` tardan,
  usá workers async de Textual (Fase 4), no lo dejes síncrono en `on_mount`.
- **No mezclar capas:** si en algún punto el agente empieza a escribir lógica
  de compatibilidad o de normalización dentro de un archivo de `screens/`,
  pará y movela a su módulo correspondiente. Esa separación es la que te va a
  salvar cuando quieras testear o reusar la lógica sin la TUI.
