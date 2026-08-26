# Wildfire Data Mining — contexto para Claude Code

Este archivo se carga automaticamente en cada sesion de Claude Code que trabaje en este
repo. Leelo completo antes de tocar codigo: evita que cada integrante reinvente la
estructura o rompa el trabajo de los demas.

## Que es este proyecto

Proyecto academico de la materia **Mineria de Datos** (Ingenieria de Sistemas). Tema
asignado: **incendios forestales**, analizado en tres escalas: **global**, **nacional
(Colombia)** y **regional (Cundinamarca)**.

Este primer entregable (**R1 — "Del problema a los datos"**) NO busca todavia el mejor
modelo predictivo. Busca demostrar que el grupo:
1. Entiende y delimito el problema.
2. Formulo una pregunta principal + minimo 3 secundarias, respondibles con datos.
3. Identifico y justifico fuentes de datos (primaria/secundaria/terciaria, minimo 2 por
   escala: global, nacional, regional).
4. Construyo un dataset inicial que cumple: **≥10.000 registros, ≥10 variables, ≥3
   numericas, ≥3 categoricas, ≥1 temporal, ≥1 geografica**.
5. Documento un diccionario de datos completo.
6. Hizo un diagnostico inicial de calidad (sin limpiar todavia).
7. Documento limitaciones.

Los requisitos completos del profesor estan en `docs/R1MineriaDatos.pdf` y
`docs/entregable-semana-1.txt` (cópialos ahí si no existen — ver seccion "Documentos
fuente" abajo). **La entrega es para el 2026-08-26.**

## Como esta resuelto hoy (2026-08-25)

Ya existe una **fuente de datos real y suficiente por si sola** para nacional y regional:
la Base de Datos de Incendios de la Cobertura Vegetal del **IDEAM** (2010-2024), que el
usuario aporto en dos archivos `.xlsx`. Se extrajo y consolido con
`scripts/Build-IdeamDataset.ps1` (PowerShell puro, sin depender de pandas, porque esta
maquina no tenia Python instalado) hacia:

- `data/processed/incendios_ideam_2010_2024.csv` — **40.010 registros**, nacional, 2010-2024.
- `data/processed/incendios_ideam_cundinamarca_2010_2024.csv` — **6.027 registros**,
  subconjunto filtrado por `DEPARTAMENTO = CUNDINAMARCA`.
- `data/processed/calidad_resumen.json` — nulos por columna, duplicados, rango de anios,
  etc. Ya consumido por las paginas `/etapa-1/dataset` y `/etapa-1/calidad`.
- `data/raw/ideam_incendios_*.csv` — extraccion cruda por hoja/ano (trazabilidad).

**Esto ya cumple de sobra el minimo de 10.000 registros / 10 variables / tipos de
variable para los niveles nacional y regional.** Lo que falta y es prioritario:

- **Fuente(s) de nivel global** (ninguna fuente actual tiene alcance mundial). Ejemplos
  razonables: NASA FIRMS/MODIS (incendios activos satelitales), Global Forest Watch
  Fires, EFFIS (Europa), FAO. Elegir 2, documentarlas en `/etapa-1/fuentes`.
  - **CSV/GeoJSON o API que ya trae fecha, pais/lat-lon**: es la opcion mas facil de
    integrar con el dataset IDEAM (join por año o análisis comparativo lado a lado, no
    necesariamente merge fila a fila).
- Una **segunda fuente nacional** y una **segunda fuente regional** (independientes de
  IDEAM), aunque sea para contraste/validacion — la primera ya esta cubierta y sobra en
  volumen, el requisito es de *cantidad de fuentes distintas*, no de mas registros.
- El **contenido narrativo**: problema/contexto, preguntas, interpretacion de los
  hallazgos de calidad — eso lo genera el equipo, no se puede fabricar.

Los archivos `.xlsx` originales del IDEAM **no estan en este repo** (son binarios
pesados, ver `.gitignore`); si necesitas volver a correr el script de extraccion, pide al
dueño del repo los dos archivos `bd_icv_nacional_*.xlsx` y colocalos un nivel arriba de
la carpeta del proyecto (o pasa `-SourceDir` al script).

## Estructura del entregable R1 dentro de la app

Menu principal **"Etapa 1"** (visible en el header del dashboard) con 8 submenus
obligatorios. Cada submenu es una ruta Flask + una plantilla Jinja **propia** (para que
cada integrante edite un archivo distinto y no haya conflictos de merge):

| # | Submenu | Ruta | Plantilla | Responsable | Brief |
|---|---|---|---|---|---|
| 1 | Problema y contexto | `/etapa-1/problema` | `app/templates/etapa1/problema.html` | **Sergio Gómez** | `docs/tareas/sergio.md` |
| 2 | Pregunta principal y secundarias | `/etapa-1/preguntas` | `app/templates/etapa1/preguntas.html` | **Sergio Gómez** | `docs/tareas/sergio.md` |
| 3 | Necesidades de informacion | `/etapa-1/necesidades` | `app/templates/etapa1/necesidades.html` | **Sara Vargas** | `docs/tareas/sara.md` |
| 4 | Fuentes de datos | `/etapa-1/fuentes` | `app/templates/etapa1/fuentes.html` | **Sara Vargas** | `docs/tareas/sara.md` |
| 5 | Dataset | `/etapa-1/dataset` | `app/templates/etapa1/dataset.html` | **Laura Bautista** | `docs/tareas/laura.md` |
| 6 | Diccionario de datos | `/etapa-1/diccionario` | `app/templates/etapa1/diccionario.html` | **Laura Bautista** | `docs/tareas/laura.md` |
| 7 | Calidad inicial de los datos | `/etapa-1/calidad` | `app/templates/etapa1/calidad.html` | **Camila** | `docs/tareas/camila.md` |
| 8 | Limitaciones y consideraciones | `/etapa-1/limitaciones` | `app/templates/etapa1/limitaciones.html` | **Camila** | `docs/tareas/camila.md` |

Cada quien puede swapear su parte con otra persona si les hace mas sentido — lo importante
es que cada pagina tenga UN solo dueño para evitar choques de merge.

Logica compartida (NO editar sin avisar al grupo, es codigo comun a las 8 paginas):
- `app/etapa1.py` — blueprint, rutas, lista `SUBMENU`, lista `DICCIONARIO` (fuente de
  verdad del diccionario de datos, consumida por `diccionario.html`).
- `app/templates/etapa1/_layout.html` — header + submenu compartido por las 8 paginas.
- `app/__init__.py` — registra el blueprint `etapa1_bp`.
- `freeze.py` — ya actualizado para exportar las 8 paginas al build estatico de GitHub Pages.

Cada plantilla de pagina ya trae una insignia "Responsable de esta pagina" y comentarios
`<!-- TODO: ... -->` con instrucciones exactas de que redactar. Buscar `TODO` en el
archivo asignado es el punto de partida de cada integrante.

## Flujo de git (leer antes de hacer el primer commit)

Rama de integracion de esta etapa: **`feature/etapa-1`** (ya creada a partir de `main`,
con toda la base descrita arriba, ya en GitHub). **Nadie desarrolla directo sobre `main`
ni directo sobre `feature/etapa-1`.**

Cada integrante crea su propia sub-rama a partir de `feature/etapa-1`:

| Integrante | Rama |
|---|---|
| Sergio Gómez | `feature/etapa-1-sergio` |
| Sara Vargas | `feature/etapa-1-sara` |
| Laura Bautista | `feature/etapa-1-laura` |
| Camila | `feature/etapa-1-camila` |

Pasos (ver tambien la seccion "Como empezar" mas abajo, con el detalle por maquina):
1. `git fetch origin`
2. `git checkout feature/etapa-1 && git pull`
3. `git checkout -b feature/etapa-1-<tu-nombre>`
4. Edita **solo** los archivos de tu fila en la tabla de arriba (plus, si tu fuente
   agrega variables nuevas al dataset, tambien puedes anadir entradas a la lista
   `DICCIONARIO` en `app/etapa1.py` — avisa en el chat del grupo antes de tocar ese
   archivo porque lo comparten los 4).
5. Commits pequenos y descriptivos: `git commit -m "docs(etapa1): completa pregunta principal y secundarias"`.
6. `git push -u origin feature/etapa-1-<tu-nombre>`
7. Abre un Pull Request de tu rama hacia **`feature/etapa-1`** (no hacia `main`).
8. Cuando los 4 PR esten mergeados a `feature/etapa-1` y revisados, se abre un PR final de
   `feature/etapa-1` hacia `main` — eso dispara el deploy automatico a GitHub Pages
   (`.github/workflows/deploy.yml`). Este ultimo merge lo hace Sergio.

## Como empezar (cada quien en su propia maquina, con Claude Code)

1. Clonar el repo (solo la primera vez):
   ```bash
   git clone https://github.com/sgora96/wildfire-data-mining.git
   cd wildfire-data-mining
   ```
2. Traer la rama de la Etapa 1 y crear tu propia rama (reemplaza `<tu-nombre>` por
   `sergio` / `sara` / `laura` / `camila`):
   ```bash
   git fetch origin
   git checkout feature/etapa-1
   git pull
   git checkout -b feature/etapa-1-<tu-nombre>
   ```
3. Abrir Claude Code **en esta carpeta** (`wildfire-data-mining`) — al iniciar, Claude
   Code lee automaticamente este `CLAUDE.md`, asi que ya tiene el contexto del proyecto.
4. Abrir tu archivo de tarea (`docs/tareas/<tu-nombre>.md`) y pegarle a Claude Code el
   prompt sugerido que esta al final de ese archivo (cada brief ya trae uno listo para
   copiar y pegar).
5. Revisar juntos (vos + Claude Code) el resultado en el navegador:
   ```bash
   python -m venv .venv
   # Windows: .venv\Scripts\Activate.ps1   |   Linux/Mac: source .venv/bin/activate
   pip install -r requirements.txt
   python run.py
   ```
   y abrir la pagina que te corresponde, ej. `http://127.0.0.1:5000/etapa-1/fuentes`.
6. Cuando este listo, pedirle a Claude Code que haga commit y push de **tus** archivos
   (los que lista tu brief) y le abrís el Pull Request hacia `feature/etapa-1` desde
   GitHub (o con `gh pr create` si tienen la CLI de GitHub instalada).

**No hace falta tocar nada del dashboard principal (la seccion comentada en
`app/templates/index.html`, `services.py`, `/api/predict`, etc.) — eso es de una entrega
futura, no de R1. Si Claude Code propone "mejorar" o "activar" el dashboard, dile que no,
que esta entrega es solo la Etapa 1.**

Como cada integrante toca archivos distintos, los merges deberian ser sin conflictos. Si
igual aparece un conflicto, casi seguro es en `app/etapa1.py` (DICCIONARIO compartido) —
resuelvelo conservando ambas listas de entradas, no borres la del compañero.

## Correr el proyecto localmente

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1   |   Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Abre `http://127.0.0.1:5000/etapa-1/problema` para ver la Etapa 1 directamente.

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
- Estilo visual: Tailwind (via CDN) siguiendo la paleta ya usada en `index.html` y
  `etapa1/_layout.html` (colores `ember`/`ash`) — no introduzcas otro framework CSS.
- No fabriques cifras, URLs de fuentes o citas que no puedas verificar: si no tienes el
  dato, deja el `TODO` explicito en vez de inventar un numero o un enlace.
- No es necesario (ni se pide en R1) entrenar un modelo predictivo todavia — no gastes
  tiempo en `models/` ni en `/api/predict` para esta entrega.
