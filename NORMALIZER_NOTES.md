# Nota Técnica: Sistema de Normalización de Transacciones (Evaluaciones IA)

## 1. Decisiones de Diseño y Adaptación del Contexto

Dado que `caniarun` ya posee un sistema robusto de evaluación de modelos de IA, se decidió adaptar el concepto de "normalización de transacciones" a este dominio, mapeando directamente los requerimientos del proyecto de la siguiente manera:

- **Transacciones = Evaluaciones de Modelos**: Cada evaluación de un modelo en un nivel de cuantización específico actúa como una "transacción".
- **Fuentes (Sources) = Familias de Modelos**: Meta (Llama), Alibaba (Qwen), Google (Gemma), etc.
- **Moneda = Nivel de Cuantización**: Las diferentes compresiones (Q4_K_M, Q8_0, F16) actúan como las diferentes monedas en las que se "cobra" la memoria.
- **Monto = Memoria VRAM**: Los GB de memoria requerida son el valor transaccional.
- **Reglas de Normalización**: 
  - *Conversión de Moneda/Monto*: Aplicación de un factor de overhead realista (1.12x o 12% adicional) sobre la VRAM teórica, debido a que en el mundo real se requiere espacio extra para caché (KV cache) y contexto del sistema operativo.
  - *Mapeo de Estados*: Se normalizaron estados técnicos (`can-run-slow`) a estados funcionales legibles (`degraded`, `blocked`).
  - *Asignación de "Vibe Level"*: Traducción de calificaciones (S, A, B...) a *slang* amigable ("Smooth as butter", "Trash mode").

Estas reglas están definidas **explícitamente** en `src/caniarun/rules.py`, aislando la lógica de negocio del proceso de ingesta.

## 2. Proceso de Normalización y Validación

Se estructuró el código separando responsabilidades:

1. **`normalizer.py`**: Ingesta objetos crudos de evaluación y genera registros planos `NormalizedEvaluation`. Aplica las reglas importadas de `rules.py`.
2. **`validator.py`**: Verifica condiciones indispensables (VRAM > 0, score válido, familia asignada). 
   - *Decisión técnica*: No se descartan los registros inválidos. Se marcan con `is_valid=False` y se les adjuntan las razones del fallo (`validation_errors`). Esto permite auditar la calidad de los datos en la interfaz.
3. **`metrics.py`**: Consume la lista de registros normalizados y genera un reporte estadístico completo (conteo por vibe, promedios, distribución de validez).

## 3. Interfaz Interactiva (TUI)

En lugar de construir una CLI básica de prints o depender de un servidor web pesado, se implementó una **Interfaz de Usuario de Terminal (TUI) completa usando la librería `textual`** (`src/caniarun/tui.py`).

Esta decisión ofrece una experiencia inmersiva "tipo escritorio" directamente en la consola:
- **Dashboard**: Panel principal con métricas agregadas (total de modelos, breakdown por Vibe, y promedios).
- **Filtros (Sidebar)**: Permite ocultar transacciones inválidas y filtrar dinámicamente por Fuente/Familia o por Vibe Level.
- **Tabla (DataTable)**: Un visor de registros estructurado y scrolleable.
- **Vistas de Detalles**: Al hacer clic (o Enter) sobre una fila, se levanta una pantalla modal con la información exhaustiva de la evaluación y los posibles errores de validación.

## 4. Uso de Inteligencia Artificial

La IA fue utilizada como un agente desarrollador colaborador:
- **Lo que SÍ hizo la IA**: Programó la interfaz de Textual (que requiere mucho scaffolding y diseño de componentes), generó datos ficticios en formato JSON para simular entradas correctas y corruptas (`eval_clean.json`, `eval_dirty.json`), e integró el subcomando `tui` al CLI existente (`cli.py`).
- **Lo que NO decidió la IA**: No definió el esquema de los datos (`NormalizedEvaluation`), ni el factor multiplicador de overhead (1.12), ni la política de qué hacer con los errores (mantenerlos vs descartarlos), ni los niveles de clasificación. Esas reglas fueron dictadas explícitamente en el plan inicial provisto al agente.
