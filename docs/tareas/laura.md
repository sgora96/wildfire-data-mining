# Tarea Laura Bautista — Perfilamiento de datos (Etapa 2)

Este documento es autosuficiente. Es la Etapa 2 (R2) de Minería de Datos: "Calidad de
Datos" sobre el dataset de incendios forestales. Lee también `CLAUDE.md` en la raíz del
repo.

## Punto de partida (ya resuelto)

`app/templates/etapa2/perfilamiento.html` ya muestra, calculado automáticamente desde
`data/processed/calidad_r2_resumen.json`:

- KPIs generales (registros, variables, duplicados, % duplicados).
- Una tabla completa con el perfil de las 36 variables: tipo de dato, valores únicos,
  nulos, % nulos, y para las columnas numéricas (área, cobertura, elevación): valores no
  numéricos detectados, mínimo, máximo y promedio.

Vos ya conocés este dataset a fondo (lo revisaste en la Etapa 1), así que tenés ventaja
para interpretar estos resultados.

## Qué debes producir

### `app/templates/etapa2/perfilamiento.html`

Reemplazá el bloque `TODO` final ("Lectura del perfilamiento") con una interpretación de
4-6 líneas de los hallazgos más relevantes de la tabla. Ideas para guiar el análisis:

- ¿Qué variables están más completas (menos % de nulos) y cuáles casi vacías?
- ¿Qué columnas tienen más "valores no numéricos" (mezclan texto con números) y qué
  implica eso para poder usarlas en cálculos?
- ¿Qué variables tienen cardinalidad muy alta (MUNICIPIO, VEREDA_CORREGIMIENTO) y por
  qué eso las hace difíciles de homologar por completo?
- ¿Qué tan grande es el problema de duplicados exactos en proporción al total?

No hace falta recalcular nada a mano: todos los números ya están en la tabla, tu trabajo
es leerlos e interpretarlos.

## Archivos que SÍ podés editar

- `app/templates/etapa2/perfilamiento.html`

## Archivos que NO debés tocar

Cualquier otro archivo, incluyendo `scripts/data_quality_r2.py` y el dataset tratado (si
encontrás un error real en los números, avisá en el chat del grupo en vez de editarlos
vos misma).

## Flujo de git

```bash
git fetch origin
git checkout feature/etapa-2
git pull
git checkout -b feature/etapa-2-laura

# ... editás el archivo ...

git add app/templates/etapa2/perfilamiento.html
git commit -m "docs(etapa2): interpretacion del perfilamiento de datos"
git push -u origin feature/etapa-2-laura
```

Abrí un Pull Request de `feature/etapa-2-laura` hacia `feature/etapa-2` (NO hacia
`main`).

## Checklist antes de dar por terminada tu parte

- [ ] La interpretación cubre completitud, exactitud (texto residual) y cardinalidad.
- [ ] No quedó ningún `TODO` sin resolver en el archivo.
- [ ] Corriste `python run.py` y viste `/etapa-2/perfilamiento/` en el navegador, con la
      tabla completa y tu interpretación abajo.

## Prompt sugerido para tu sesión de Claude Code

> Estoy en la rama feature/etapa-2-laura del repo wildfire-data-mining. Lee CLAUDE.md y
> docs/tareas/laura.md completos, y también data/processed/calidad_r2_resumen.json.
> Ayudame a redactar la interpretación del perfilamiento en
> app/templates/etapa2/perfilamiento.html siguiendo exactamente las instrucciones del
> documento, reemplazando el TODO. No toques ningún otro archivo.
