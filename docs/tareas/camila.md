# Tarea Camila — Dimensiones e inventario de problemas (Etapa 2)

Este documento es autosuficiente. Es la Etapa 2 (R2) de Minería de Datos: "Calidad de
Datos" sobre el dataset de incendios forestales. Lee también `CLAUDE.md` en la raíz del
repo.

## Punto de partida (ya resuelto)

`app/templates/etapa2/dimensiones.html` ya muestra, calculado desde
`data/processed/calidad_r2_resumen.json`:

- Las **6 dimensiones de calidad** (completitud, exactitud, consistencia, unicidad,
  validez, actualidad), cada una con su definición, fórmula y resultado en %.
- El **inventario de problemas** completo: variable afectada, descripción, registros
  afectados, dimensión relacionada, nivel de impacto y evidencia (10 problemas
  documentados).

Esto ya cubre el diagnóstico de calidad. Vos ya hiciste este tipo de análisis en la
Etapa 1 (calidad inicial), así que este es terreno conocido.

## Qué debes producir

### `app/templates/etapa2/dimensiones.html`

Reemplazá el bloque `TODO` final ("Análisis de causas") explicando **por qué** ocurren
los problemas principales del inventario (no solo qué son, sino su origen). El archivo
ya trae pistas identificadas durante el perfilamiento en un comentario oculto —
ábrelo con tu editor de código para verlas — sobre: plantillas de captura distintas
entre años, captura manual sin validación, campos opcionales en el formulario de campo,
mezcla de sistemas de coordenadas entre entidades, y posible doble reporte de un mismo
evento. Desarrollá esas ideas (y las que veas necesarias) en 5-8 líneas.

## Archivos que SÍ podés editar

- `app/templates/etapa2/dimensiones.html`

## Archivos que NO debés tocar

Cualquier otro archivo, incluyendo `scripts/data_quality_r2.py` (si creés que una
métrica está mal calculada, avisá en el chat del grupo).

## Flujo de git

```bash
git fetch origin
git checkout feature/etapa-2
git pull
git checkout -b feature/etapa-2-camila

# ... editás el archivo ...

git add app/templates/etapa2/dimensiones.html
git commit -m "docs(etapa2): analisis de causas de los problemas de calidad"
git push -u origin feature/etapa-2-camila
```

Abrí un Pull Request de `feature/etapa-2-camila` hacia `feature/etapa-2` (NO hacia
`main`).

## Checklist antes de dar por terminada tu parte

- [ ] El análisis de causas cubre al menos los problemas de mayor impacto del
      inventario (duplicados, homologación de departamento/mes, formatos numéricos
      mixtos).
- [ ] Cada causa está conectada con un problema específico del inventario, no es
      genérica.
- [ ] No quedó ningún `TODO` sin resolver en el archivo.
- [ ] Corriste `python run.py` y viste `/etapa-2/dimensiones/` en el navegador, con las
      6 dimensiones, la tabla de problemas y tu análisis de causas.

## Prompt sugerido para tu sesión de Claude Code

> Estoy en la rama feature/etapa-2-camila del repo wildfire-data-mining. Lee CLAUDE.md
> y docs/tareas/camila.md completos, y también data/processed/calidad_r2_resumen.json.
> Ayudame a redactar el análisis de causas en app/templates/etapa2/dimensiones.html
> siguiendo exactamente las instrucciones del documento (incluido el comentario oculto
> con pistas dentro del archivo), reemplazando el TODO. No toques ningún otro archivo.
