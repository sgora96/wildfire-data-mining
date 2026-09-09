# Wildfire Data Mining — contexto para Claude Code

Este archivo se carga automaticamente en cada sesion de Claude Code que trabaje en este
repo. Leelo completo antes de tocar codigo.

## Que es este proyecto

Proyecto academico de la materia **Mineria de Datos** (Ingenieria de Sistemas). Tema
asignado: **incendios forestales**, analizado en tres escalas: **global**, **nacional
(Colombia)** y **regional (Cundinamarca)**.

El curso entrega el proyecto por etapas sucesivas; la aplicacion Flask es la bitacora
tecnica que crece con cada una (nunca se reemplaza por documentos aislados).

## Estado actual

**Etapa 1 — "Del problema a los datos" — completa** (problema/contexto, preguntas de
investigacion, necesidades de informacion, fuentes de datos, dataset, diccionario de
datos, diagnostico de calidad y limitaciones).

Dataset base ya consolidado, real (no sintetico):

- `data/processed/incendios_ideam_2010_2024.csv` — **40.010 registros**, nacional (Colombia), 2010-2024.
- `data/processed/incendios_ideam_cundinamarca_2010_2024.csv` — **6.027 registros**,
  subconjunto filtrado por `DEPARTAMENTO = CUNDINAMARCA`.
- `data/processed/calidad_resumen.json` — nulos por columna, duplicados, rango de anios,
  etc. Consumido por `/etapa-1/dataset` y `/etapa-1/calidad` (y por el inicio del sitio).
- `data/raw/ideam_incendios_*.csv` — extraccion cruda por hoja/ano (trazabilidad).
- Generado por `scripts/Build-IdeamDataset.ps1` a partir de los `.xlsx` originales del
  IDEAM (no estan en el repo, son binarios pesados — pedirlos al dueno del repo si hay
  que regenerar el dataset).
- 6 fuentes de datos documentadas en `/etapa-1/fuentes` (2 por escala): NASA FIRMS y
  Global Forest Watch Fires (global), IDEAM y Emergencias UNGRD (nacional), subconjunto
  IDEAM-Cundinamarca y CAR-RICV (regional).

Las siguientes etapas del semestre se agregan sobre esta misma base — ver
"Arquitectura de navegacion" abajo para saber donde enganchar cada una.

## Arquitectura de la aplicacion

```
app/
  __init__.py       # Application Factory: registra blueprints y el context_processor
                     # que inyecta `modulos` y `nav_index` (sidebar) a TODAS las plantillas.
  navigation.py      # Unica fuente de verdad del menu lateral: modulos > submodulos > paginas.
  routes.py          # Blueprint `main` (pagina de inicio) y `api` (endpoints JSON, sin usar en R1).
  etapa1.py          # Blueprint `etapa1`: rutas + DICCIONARIO de datos de la Etapa 1.
  services.py        # Logica del dashboard analitico (pandas) — hoy sin usar, ver mas abajo.
  templates/
    _shell.html       # Layout compartido: header, sidebar de modulos, footer. TODA pagina lo extiende.
    index.html         # Inicio: resumen del proyecto + progreso por etapa.
    etapa1/
      _layout.html      # Solo hace `{% extends "_shell.html" %}` (no le agregues logica propia).
      problema.html, preguntas.html, necesidades.html, fuentes.html,
      dataset.html, diccionario.html, calidad.html, limitaciones.html,
      tareas.html       # Las 8 paginas oficiales de la Etapa 1 + su pagina de equipo/tareas.
```

### Sidebar / modulos (`app/navigation.py`)

El menu lateral se arma en un solo lugar: `MODULOS` es una lista de modulos, cada uno con
`submodulos`, y cada submodulo con una lista `paginas` (`{"endpoint": "...", "label": "..."}`).
`_shell.html` recorre esa estructura para pintar el sidebar y resaltar la pagina activa
comparando contra `request.endpoint` — no hace falta pasar nada especial desde cada ruta.

**Para agregar una etapa nueva** (Etapa 2, Etapa 3, ...):
1. Crear su blueprint (ej. `app/etapa2.py`, mismo patron que `app/etapa1.py`) y sus
   plantillas en `app/templates/etapa2/` (con `_layout.html` que solo hace
   `{% extends "_shell.html" %}`, igual que Etapa 1).
2. Registrar el blueprint en `app/__init__.py`.
3. Agregar un nuevo submodulo dentro de `MODULOS["etapas"]` en `app/navigation.py`, con
   la misma forma que el de Etapa 1 (`id`, `label`, `sublabel`, `estado`, `paginas`).
   El sidebar y el breadcrumb se actualizan solos, no hay que tocar `_shell.html`.
4. Opcional pero recomendado: agregar tambien una pagina "Equipo y tareas" para esa
   etapa (mismo patron que `etapa1/tareas.html`) documentando quien hizo que.
5. Agregar los nuevos endpoints a la lista de `freeze.py` para que se incluyan en el
   build estatico de GitHub Pages.

**IMPORTANTE — nada de rastro de herramientas de IA en la aplicacion:** las paginas
"Equipo y tareas" (y cualquier otro contenido visible del sitio) documentan **solo** el
reparto de trabajo entre las personas del grupo y el estado de cada parte — nunca
menciones herramientas, asistentes, prompts, ni el flujo de trabajo usado para producir
el contenido. Esa coordinacion (si hace falta dejarla por escrito para el grupo) se
maneja fuera del repo o en archivos que se eliminan apenas la etapa correspondiente
queda terminada por todos — no debe quedar rastro de eso en el historial ni en el sitio
publicado.

### Dashboard analitico (`services.py`, seccion comentada de `index.html`)

Hay una seccion de dashboard interactivo (KPIs, filtros climaticos, graficos, carga de
datasets, `/api/predict`) que **no forma parte del alcance actual** — esta comentada
dentro de `index.html` a proposito. No la actives ni la desarrolles salvo que una etapa
del curso lo pida explicitamente.

## Diccionario de datos (`app/etapa1.py` → `DICCIONARIO`)

Lista de 36 entradas, una por columna del dataset consolidado (mismo esquema en el
archivo nacional y en el regional). Ya fue revisada contra el CSV real: varias columnas
mezclan numeros con texto residual (ver descripciones), los marcadores de causa no son
homogeneos entre anios, y `AREA_PROTEGIDA_NACIONAL` es texto libre (no un indicador
Si/No pese al nombre). Si agregas una fuente nueva con variables propias, suma sus
entradas al final de esta misma lista, sin borrar las existentes.

## Flujo de git

Cada etapa se desarrolla en su propia rama de integracion (ej. `feature/etapa-1`,
`feature/etapa-2`, ...) creada a partir de `main`. Dentro de una etapa, cada persona del
grupo trabaja en su propia sub-rama (`feature/etapa-N-<nombre>`) tocando solo los
archivos de su parte, abre PR hacia la rama de integracion de esa etapa, y al final esa
rama se fusiona a `main` (lo que dispara `.github/workflows/deploy.yml` y publica en
GitHub Pages). Nadie desarrolla directo sobre `main` ni directo sobre una rama de
integracion compartida.

Como cada persona toca archivos distintos, los merges deberian ser sin conflictos. Si
aparece uno, lo mas probable es en un archivo compartido (`DICCIONARIO` en
`app/etapa1.py`, o `app/navigation.py` si dos etapas se agregan en paralelo) —
resolverlo conservando las entradas de ambas partes, nunca borrando las de otra persona.

## Correr el proyecto localmente

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1   |   Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Abre `http://127.0.0.1:5000/` (inicio) o `http://127.0.0.1:5000/etapa-1/problema`
(Etapa 1 directamente).

Si necesitas regenerar el dataset desde los `.xlsx` originales del IDEAM (Windows,
PowerShell, no requiere Python):

```powershell
./scripts/Build-IdeamDataset.ps1
```

**Nota de encoding:** los CSV en `data/raw/` y `data/processed/` tienen BOM UTF-8 (los
genero PowerShell). Si los lees con pandas, usa `pd.read_csv(path, encoding="utf-8-sig")`
para que el nombre de la primera columna no quede con `﻿` pegado.

## Convenciones

- Todo el contenido de la app es en **español**.
- Estilo visual: Tailwind (via CDN), paleta `ember`/`ash` ya definida en `_shell.html` —
  no introduzcas otro framework CSS ni redefinas la paleta en otro lado.
- Todas las paginas extienden `_shell.html` (directo, o via `etapa1/_layout.html` u otro
  layout de etapa equivalente) para heredar header, sidebar y footer automaticamente.
- Cuidado con nombres de clave que choquen con metodos de dict en Jinja (`items`,
  `keys`, `values`, `get`...): `dato.items` accede al METODO `dict.items`, no a una
  clave literal llamada `"items"` — por eso en `navigation.py` la lista de paginas de un
  submodulo se llama `paginas`, no `items`.
- No fabriques cifras, URLs de fuentes o citas que no puedas verificar: si no tienes el
  dato, dejalo pendiente en vez de inventar un numero o un enlace.
- Ninguna pagina visible del sitio debe mencionar herramientas de IA, asistentes o
  prompts (ver seccion "Sidebar / modulos" arriba).
