# Tarea Laura Bautista — Dataset y Diccionario de datos

Este documento es autosuficiente. El proyecto es la Etapa 1 (R1) de Mineria de Datos
sobre **incendios forestales**. Lee tambien `CLAUDE.md` en la raiz del repo.

## Punto de partida (ya resuelto)

El dataset base **ya existe y ya cumple los minimos de R1**:

- `data/processed/incendios_ideam_2010_2024.csv` — 40.010 registros nacionales, IDEAM,
  2010-2024, 35 variables (+ FUENTE_HOJA de trazabilidad = 36 columnas).
- `data/processed/incendios_ideam_cundinamarca_2010_2024.csv` — 6.027 registros,
  subconjunto regional (Cundinamarca).
- `data/processed/calidad_resumen.json` — metricas ya calculadas (usalas, no las
  recalcules a mano).
- Generado por `scripts/Build-IdeamDataset.ps1` (documentado, se puede volver a correr).
- El diccionario de datos de estas 36 columnas **ya esta escrito** en
  `app/etapa1.py` (lista `DICCIONARIO`) y se renderiza automaticamente en
  `app/templates/etapa1/diccionario.html` — revisalo con calma, no lo reescribas desde
  cero, pero SI corrigelo si al inspeccionar el CSV encuentras algo distinto a lo
  documentado (varias descripciones son "mejor esfuerzo" y dicen explicitamente que
  conviene revisar una muestra de filas).

## Que debes producir

### 1. Revision y ajuste de `app/etapa1.py` → lista `DICCIONARIO`

- Abre `data/processed/incendios_ideam_2010_2024.csv` (ojo: tiene BOM UTF-8, en Excel
  ábrelo con "Datos > Desde texto/CSV" o en pandas con `encoding="utf-8-sig"`) e inspecciona
  una muestra de filas por columna.
- Corrige cualquier descripcion, dominio o ejemplo que no coincida con lo que realmente
  ves en los datos.
- Este archivo es **compartido** con Sara Vargas (por si su fuente global agrega
  columnas nuevas). Antes de editarlo: `git pull` para traer los cambios mas recientes,
  y avisa en el chat del grupo que vas a tocarlo.

### 2. `app/templates/etapa1/dataset.html`

- Ya tiene las cifras reales (registros, variables, periodo) leidas dinamicamente de
  `calidad_resumen.json` — no hace falta que las escribas a mano, solo revisa que se
  vean bien en el navegador.
- Completa el bloque `TODO` final: una vez Sara Vargas defina la fuente global, aqui
  se documenta **como se integra** con el dataset IDEAM (¿join por año/pais? ¿analisis
  comparativo por separado, sin merge fila a fila?). Coordina con Sara Vargas.
- Si agregas una fuente global con un archivo de datos propio, guardalo en
  `data/raw/` (crudo) y/o `data/processed/` (limpio) siguiendo el mismo patron de
  nombres (`<fuente>_<cobertura>_<periodo>.csv`).

### 3. Diccionario de datos de la(s) fuente(s) nueva(s)

Si Sara Vargas trae una fuente global con datos propios (no solo un enlace), agrega
sus variables como entradas nuevas al final de la lista `DICCIONARIO` en
`app/etapa1.py`, siguiendo el mismo formato (campo, descripcion, tipo, dominio, fuente,
ejemplo).

## Archivos que SI puedes editar

- `app/etapa1.py` (**solo** la lista `DICCIONARIO`, no las rutas — coordina con el grupo)
- `app/templates/etapa1/dataset.html`
- Archivos nuevos que crees en `data/raw/` o `data/processed/`

## Archivos que NO debes tocar

Las plantillas de los otros integrantes, `_layout.html`, `freeze.py`, ni las rutas
Flask en `app/etapa1.py` (solo la lista `DICCIONARIO` al final del archivo).

## Flujo de git

```bash
git fetch origin
git checkout feature/etapa-1
git pull
git checkout -b feature/etapa-1-laura

# ... editas ...

git add app/etapa1.py app/templates/etapa1/dataset.html data/
git commit -m "docs(etapa1): revision del diccionario de datos y pagina de dataset"
git push -u origin feature/etapa-1-laura
```

Abre un Pull Request de `feature/etapa-1-laura` hacia `feature/etapa-1` (NO hacia
`main`).

## Checklist antes de dar por terminada tu parte

- [ ] Revisaste una muestra real del CSV, no solo confiaste en las descripciones
      generadas automaticamente.
- [ ] El diccionario de datos no tiene campos sin describir.
- [ ] `/etapa-1/dataset` muestra las cifras correctas (registros, variables, periodo) y
      el checklist de requisitos minimos de R1 en verde.
- [ ] `/etapa-1/diccionario` se ve bien en el navegador (tabla completa, sin errores).
- [ ] Si agregaste datos de la fuente global, estan en `data/raw/` o `data/processed/`
      con nombres de archivo claros.

## Prompt sugerido para tu sesion de Claude Code

> Estoy en la rama feature/etapa-1-laura del repo wildfire-data-mining. Lee
> CLAUDE.md y docs/tareas/laura.md completos. Ayudame a inspeccionar
> data/processed/incendios_ideam_2010_2024.csv (usa encoding utf-8-sig) y a revisar/
> corregir la lista DICCIONARIO en app/etapa1.py para que describa fielmente los datos
> reales. Luego revisa que app/templates/etapa1/dataset.html se vea bien. No toques las
> rutas de app/etapa1.py ni otras plantillas.
