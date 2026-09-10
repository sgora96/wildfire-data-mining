# Tarea Sara Vargas — Integración, homologación y tratamiento (Etapa 2)

Este documento es autosuficiente. Es la Etapa 2 (R2) de Minería de Datos: "Calidad de
Datos" sobre el dataset de incendios forestales. Lee también `CLAUDE.md` en la raíz del
repo.

## Punto de partida (ya resuelto)

`app/templates/etapa2/tratamiento.html` ya muestra, calculado desde
`data/processed/calidad_r2_resumen.json`:

- Un resumen de integración/homologación ya redactado (homologación de DEPARTAMENTO y
  MES, unidades de área consistentes entre hojas).
- El **plan de tratamiento completo** aplicado de verdad sobre el dataset (7 acciones:
  eliminación de duplicados, homologación de categorías, corrección de tipos de datos,
  estandarización de coordenadas, decisión de alcance sobre coordenadas no convertibles,
  validación de rangos, tratamiento de valores atípicos y de nulos), cada una con su
  justificación.
- La **comparación antes/después** en una tabla (registros, departamentos distintos,
  meses distintos, coordenadas utilizables, elevaciones inválidas, duplicados).
- El detalle del dataset tratado resultante
  (`data/processed/incendios_ideam_tratado_2010_2024.csv`).

Este es el terreno que ya conocés de la Etapa 1 (fuentes y necesidades de información),
así que la parte de integración de fuentes te queda natural.

## Qué debes producir

### `app/templates/etapa2/tratamiento.html`

Reemplazá el bloque `TODO` de la sección "Integración y homologación de los datos":

- Si el grupo decide incorporar alguna de las fuentes adicionales documentadas en la
  Etapa 1 (NASA FIRMS, Global Forest Watch Fires, Emergencias UNGRD, CAR-RICV) **en
  esta etapa**, documentá aquí cómo se homologarían sus campos contra el esquema de
  este dataset (nombres de columna, unidades, formato de fecha) — coordiná con el grupo
  si van a hacer esto o no.
- Si no se integra ninguna fuente adicional todavía (lo más probable dado el tiempo),
  dejalo indicado explícitamente como alcance de esta etapa y trabajo pendiente para una
  etapa posterior — no es un error, es una decisión de alcance válida y hay que
  declararla, no dejarla implícita.

## Archivos que SÍ podés editar

- `app/templates/etapa2/tratamiento.html`

## Archivos que NO debés tocar

Cualquier otro archivo, incluyendo `scripts/data_quality_r2.py` y el dataset tratado.

## Flujo de git

```bash
git fetch origin
git checkout feature/etapa-2
git pull
git checkout -b feature/etapa-2-sara

# ... editás el archivo ...

git add app/templates/etapa2/tratamiento.html
git commit -m "docs(etapa2): integracion y homologacion de fuentes"
git push -u origin feature/etapa-2-sara
```

Abrí un Pull Request de `feature/etapa-2-sara` hacia `feature/etapa-2` (NO hacia
`main`).

## Checklist antes de dar por terminada tu parte

- [ ] Queda claro si se integró o no una fuente adicional en esta etapa, y por qué.
- [ ] No quedó ningún `TODO` sin resolver en el archivo.
- [ ] Corriste `python run.py` y viste `/etapa-2/tratamiento/` en el navegador, con el
      plan de tratamiento, la tabla antes/después y tu sección de integración.

## Prompt sugerido para tu sesión de Claude Code

> Estoy en la rama feature/etapa-2-sara del repo wildfire-data-mining. Lee CLAUDE.md y
> docs/tareas/sara.md completos, y también app/templates/etapa1/fuentes.html (las
> fuentes ya documentadas en la Etapa 1). Ayudame a completar la sección de integración
> y homologación en app/templates/etapa2/tratamiento.html siguiendo exactamente las
> instrucciones del documento, reemplazando el TODO. No toques ningún otro archivo.
