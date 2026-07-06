# Nota Técnica: Cómo se adaptó la tarea a mi proyecto "Caniarun"

## 1. ¿De qué trata esto?

La tarea pedía hacer un sistema para "normalizar transacciones", que normalmente se haría simulando un banco. Pero en lugar de hacer algo genérico, decidí aplicar esos mismos conceptos a un proyecto real que estoy construyendo llamado **Caniarun** (una herramienta que te dice qué modelos de Inteligencia Artificial pueden correr en tu dispositivo).

Para cumplir con la tarea, pensé: **"Voy a tratar la evaluación de cada modelo de IA como si fuera una transacción bancaria"**. Así cumplo con todos los requisitos técnicos, pero construyendo algo divertido y útil.

## 2. ¿Cómo cumplí los requisitos de la tarea?

Aquí explico cómo transformé los requisitos de la rúbrica a mi proyecto:

### A. Normalización de Datos

- **Leer desde JSON:** En mi programa, el sistema lee las evaluaciones de los modelos desde archivos JSON (`data/eval_dirty.json`).
- **Conversión de montos:** En lugar de convertir dólares a euros, mi programa toma los Gigabytes de memoria que pide un modelo y le aplica una fórmula matemática para "convertirlo" al consumo real que tendrá en la computadora.
- **Mapeo de estados y monedas:** En vez de monedas, yo uso el **Proveedor del modelo** (Meta, Google, etc.). Y en vez de estados bancarios (aprobado/rechazado), uso estados de hardware (como convertir el texto raro "can-run" a un estado normalizado "runnable").
- **Manejo de Fechas:** Cada evaluación que pasa por el sistema recibe un `timestamp` (fecha y hora) con un formato estándar.

### B. Validación y Métricas

- **Identificar datos inválidos:** Tengo un archivo que revisa si los datos tienen sentido. Por ejemplo, si una "transacción" (modelo) dice que requiere memoria negativa o si su puntuación es mayor a 100, el sistema la marca como inválida y la separa.
- **Métricas:** El sistema cuenta cuántas evaluaciones procesó, cuántas fueron válidas o inválidas, y agrupa los totales por proveedor (en lugar de totales por moneda).

### C. Interfaz Interactiva

Para no mostrar los datos con simples `prints` aburridos en la consola, construí una interfaz gráfica directamente en la terminal usando una librería llamada **Textual**.
Esta interfaz tiene menús interactivos, pestañas, filtros para buscar modelos específicos y un panel (Dashboard) donde se muestran las métricas de validación.

## 3. Estructura del Código

Dividí el código en archivos separados para mantener todo ordenado (Separación de responsabilidades):

- `normalizer.py`: Se encarga de limpiar los datos crudos y darles un formato común.
- `validator.py`: Decide si los datos son válidos o tienen errores.
- `metrics.py`: Saca las cuentas y totales.
- `rules.py`: Es un archivo simple que guarda las reglas de conversión y diccionarios de estados.
- `tui/`: Es la carpeta que contiene todo lo visual (la interfaz interactiva).

## 4. El rol de la Inteligencia Artificial

Usé la IA como un asistente de programación, principalmente para:

- Ayudarme a darle estilo visual a la interfaz gráfica.
- Sugerir formas de organizar mejor los archivos para que el código quede limpio.

Sin embargo, la IA **no tomó las decisiones importantes**. Fui yo quien decidió cómo adaptar el problema del banco al hardware de IA, y fui yo quien definió manualmente las reglas estrictas de qué hace que una evaluación de hardware sea válida o inválida para que las métricas finales tengan sentido lógico.
