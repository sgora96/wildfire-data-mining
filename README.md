# 🔥 Wildfire Data Mining

Plataforma de **minería de datos aplicada a incendios forestales**: análisis exploratorio
de variables climáticas, carga de datasets, cálculo de indicadores de riesgo y base lista
para entrenar modelos predictivos.

Construida con **Flask** (Application Factory), **pandas / scikit-learn** para el análisis
y **Tailwind CSS + Chart.js** para el dashboard. El sitio se publica automáticamente en
**GitHub Pages** mediante `Frozen-Flask` y GitHub Actions.

---

## 🔥 Etapas del proyecto

Cada entregable del curso vive dentro de la misma app, bajo el menú lateral
**Etapas del proyecto** (submódulo por etapa, con sus páginas obligatorias):

| Etapa | Tema | Estado | Ruta |
|-------|------|--------|------|
| 1 | Del problema a los datos | Completa | `/etapa-1/...` |
| 2 | Calidad de datos | Completa | `/etapa-2/...` |
| 3 | ETL y limpieza con SSIS | Completa | `/etapa-3/...` |
| 4 | Conocimiento evidente (Power BI) | Completa | `/etapa-4/` |



---

## 📑 Tabla de contenidos

- [Características](#-características)
- [Estructura del proyecto](#-estructura-del-proyecto)
- [Etapa 4 — Conocimiento evidente (Power BI)](#-etapa-4--conocimiento-evidente-power-bi)
- [Inicio rápido](#-inicio-rápido)
- [API disponible](#-api-disponible)
- [Datos y modelado](#-datos-y-modelado)
- [Despliegue a GitHub Pages](#-despliegue-a-github-pages)
- [Conexión con Git](#-conexión-con-git)
- [Próximos pasos](#-próximos-pasos)

---

## ✨ Características

| Área | Detalle |
|------|---------|
| **Dashboard** | KPIs, estacionalidad, distribución de riesgo, dispersión temperatura/área y matriz de correlación |
| **Filtros** | Rangos de temperatura, viento y humedad, selección de meses y filtro de eventos con área quemada |
| **Datasets** | Carga por *drag & drop* de CSV/Excel con perfilado automático (filas, columnas, nulos, duplicados, resumen numérico) |
| **API JSON** | Endpoints desacoplados que alimentan el frontend y sirven para integrar notebooks o clientes externos |
| **Modo estático** | El build de GitHub Pages sigue siendo interactivo: los filtros se recalculan en el navegador con un motor JS espejo de `services.py` |
| **Arquitectura** | Application Factory + blueprints + capa de servicios, sin lógica de negocio en las rutas |

---

## 🗂 Estructura del proyecto

```
wildfire-data-mining/
├── app/
│   ├── __init__.py           # create_app(): factory, blueprints y errores
│   ├── routes.py             # Vistas del dashboard y endpoints /api/*
│   ├── services.py           # Carga, filtrado, KPIs y análisis exploratorio
│   ├── static/
│   │   ├── css/styles.css    # Complementos a Tailwind (sliders, heatmap, scrollbar)
│   │   └── js/main.js        # Consumo de la API, gráficos y modo estático
│   └── templates/
│       └── index.html        # UI principal con Tailwind CSS
├── data/
│   ├── raw/                  # Datasets sin procesar (ignorados por git)
│   └── processed/            # Datasets limpios listos para modelar
├── models/                   # Modelos entrenados (.pkl / .joblib)
├── powerbi/                  # Informe de Power BI (.pbix) y tema visual (Etapa 4)
├── docs/powerbi/             # Medidas DAX y conocimientos evidentes (Etapa 4)
├── .github/workflows/
│   └── deploy.yml            # CI/CD: congelado + publicación en gh-pages
├── config.py                 # Perfiles de configuración
├── freeze.py                 # Exportación del sitio estático
├── run.py                    # Entry point local
├── requirements.txt
└── README.md
```

> **Nota de arquitectura:** `app/services.py` no aparecía en el diseño inicial; se añadió
> para mantener `routes.py` delgado y concentrar toda la lógica de minería de datos en un
> único módulo reutilizable desde notebooks o scripts de entrenamiento.

---

## 📈 Etapa 4 — Conocimiento evidente (Power BI)

Análisis exploratorio del mismo dataset de las etapas anteriores, presentado en un
informe de Power BI con cuatro tableros (uno por pregunta de análisis) e integrado en
la app en `/etapa-4/`.

### Datos utilizados

- Archivo: `data/processed/incendios_ideam_tratado_2010_2024.csv` (35.355 eventos, 2010-2024).
- Fuente: Base de Datos de Incendios de la Cobertura Vegetal (BD-ICV) del IDEAM, ya
  tratada en la Etapa 2 (ver `/etapa-2/tratamiento/`).
- Unidad de análisis: cada fila es un evento de incendio de cobertura vegetal reportado.
- Fuente original: https://ideam.gov.co/nuestra-entidad/ecosistemas-e-informacion-ambiental/incendios-de-la-cobertura-vegetal/base-de-datos-de-eventos-de-incendios-de-la

### Tableros y documentación

| Tablero | Tema | Medidas DAX | Conocimientos evidentes |
|---------|------|-------------|-------------------------|
| 1. Composición | Tamaño, cobertura y causa de los incendios | [`dax_p1_composicion.md`](docs/powerbi/dax_p1_composicion.md) | [`conocimientos_p1_composicion.md`](docs/powerbi/conocimientos_p1_composicion.md) |
| 2. Territorial | Departamentos y tamaño típico | [`dax_p2_territorial.md`](docs/powerbi/dax_p2_territorial.md) | [`conocimientos_camila.md`](docs/powerbi/conocimientos_camila.md) |
| 3. Temporal | Evolución anual y estacionalidad | [`dax_p3_temporal.md`](docs/powerbi/dax_p3_temporal.md) | [`conocimientos_p3_temporal.md`](docs/powerbi/conocimientos_p3_temporal.md) |
| 4. Multivariado | Departamento, temporada y tamaño | [`dax_p4_multivariado.md`](docs/powerbi/dax_p4_multivariado.md) | [`conocimientos_p4_multivariado.md`](docs/powerbi/conocimientos_p4_multivariado.md) |

El modelo de datos y las medidas comunes están en [`dax_base.md`](docs/powerbi/dax_base.md).
El archivo del informe es `powerbi/Wildfire_ConocimientoEvidente.pbix` y el tema visual
`powerbi/tema_wildfire.json`.

### Abrir y actualizar el informe

1. Instala **Power BI Desktop** (solo Windows) y abre `powerbi/Wildfire_ConocimientoEvidente.pbix`.
2. En `Inicio > Transformar datos > Editar parámetros`, cambia `RutaCSV` por la ruta local
   de `data/processed/incendios_ideam_tratado_2010_2024.csv` y pulsa **Cerrar y aplicar**.
3. Para actualizar con datos nuevos, reemplaza el CSV por otro con el mismo esquema y pulsa
   **Actualizar** en Power BI Desktop.
4. En cada página, el botón "Ver conocimientos" abre los tres conocimientos evidentes y
   "Cerrar" los oculta (en Power BI Desktop se activan con `Ctrl` + clic).

### Cambios realizados en la aplicación web

- `app/etapa4.py`: blueprint de la Etapa 4 (`/etapa-4/`).
- `app/templates/etapa4/`: página "Conocimiento evidente" con el propósito de la etapa,
  las cuatro preguntas, la fuente y el periodo, y el informe de Power BI.
- `app/navigation.py` y `app/__init__.py`: la Etapa 4 se agrega al menú lateral y se registra el blueprint.
- `freeze.py`: la página se incluye en el sitio estático de GitHub Pages.
- `app/templates/index.html`: el inicio muestra las tarjetas de las Etapas 1 a 4.

### Enlaces

- Repositorio: https://github.com/sgora96/wildfire-data-mining
- Aplicación publicada: https://sgora96.github.io/wildfire-data-mining/
- Página de la etapa: https://sgora96.github.io/wildfire-data-mining/etapa-4/
- Informe de Power BI: https://app.powerbi.com/view?r=eyJrIjoiNDBjZTk3MjItNTQ4NS00NjNkLTk4YTAtODEzOWY4M2Y5MTdiIiwidCI6IjA3ZGE2N2EwLTFmNDMtNGU4Yy05NzdmLTVmODhiNjQ3MGVlNiIsImMiOjR9

---

## 🚀 Inicio rápido

### 1. Clonar e instalar

```bash
git clone https://github.com/sgora96/wildfire-data-mining.git
cd wildfire-data-mining
```

**Windows (PowerShell)**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar el entorno (opcional)

```bash
cp .env.example .env     # en PowerShell: Copy-Item .env.example .env
```

### 3. Ejecutar

```bash
python run.py
```

Abre **http://127.0.0.1:5000**.

> Sin datasets propios, el dashboard arranca con un **dataset sintético reproducible**
> (517 registros con el mismo esquema que *UCI Forest Fires*), de modo que todas las
> vistas y gráficos funcionan desde el primer arranque.

### 4. Generar el sitio estático

```bash
python freeze.py     # genera build/
```

---

## 🔌 API disponible

Todos los endpoints devuelven JSON y aceptan los filtros como *query params*
(`temp_min`, `temp_max`, `wind_min`, `wind_max`, `rh_min`, `rh_max`,
`month` repetible, `only_burned`).

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET`  | `/` | Dashboard principal |
| `GET`  | `/api/health` | Sonda de disponibilidad |
| `GET`  | `/api/meta` | Fuente activa, dimensiones y columnas del dataset |
| `GET`  | `/api/kpis` | KPIs del subconjunto filtrado |
| `GET`  | `/api/analysis` | Series y matrices listas para graficar |
| `GET`  | `/api/records` | Muestra paginada (`limit`, `offset`) con índice de riesgo |
| `GET`  | `/api/datasets` | Inventario de `data/raw` y `data/processed` |
| `POST` | `/api/upload` | Carga un CSV/Excel y devuelve su perfilado |
| `POST` | `/api/predict` | Score de riesgo para un escenario climático puntual |

**Ejemplo**

```bash
curl "http://127.0.0.1:5000/api/kpis?temp_min=20&wind_max=10&month=aug&only_burned=1"
```

```bash
curl -X POST http://127.0.0.1:5000/api/predict \
     -H "Content-Type: application/json" \
     -d '{"temp": 34, "wind": 9, "RH": 22, "rain": 0}'
# {"ok": true, "risk_score": 65.2, "risk_level": "Alto", ...}
```

---

## 📊 Datos y modelado

### Esquema esperado

Basado en el dataset *Forest Fires* (UCI Machine Learning Repository):

| Columna | Descripción |
|---------|-------------|
| `X`, `Y` | Coordenadas espaciales dentro del parque |
| `month`, `day` | Temporalidad (`jan`…`dec`, `mon`…`sun`) |
| `FFMC`, `DMC`, `DC`, `ISI` | Índices del sistema *Fire Weather Index* |
| `temp` | Temperatura (°C) |
| `RH` | Humedad relativa (%) |
| `wind` | Velocidad del viento (km/h) |
| `rain` | Precipitación (mm/m²) |
| `area` | Superficie quemada (ha) — variable objetivo |

`services.normalize_columns()` reconoce alias frecuentes (`temperatura`, `humedad`,
`viento`, `burned_area`, …) y los mapea al esquema canónico.

### Prioridad de carga

```
data/processed/  →  data/raw/  →  dataset sintético
```

Se toma el archivo **más reciente** de cada carpeta.

### Índice de riesgo

Hoy es una heurística interpretable definida en `services.risk_index()`:

```
riesgo = (0.42·temp_n + 0.28·wind_n + 0.30·sequedad_n) · (1 − 0.55·penalización_lluvia) · 100
```

Cuando entrenes tu modelo, guárdalo en `models/` y sustituye la llamada dentro de
`routes.predict()` por `joblib.load(...)`: el frontend no necesita ningún cambio.

```python
# models/train.py (sugerido)
import joblib
from sklearn.ensemble import RandomForestRegressor

model = RandomForestRegressor(n_estimators=300, random_state=42).fit(X_train, y_train)
joblib.dump(model, "models/wildfire_rf.joblib")
```

---

## 🌍 Despliegue a GitHub Pages

El workflow [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) se ejecuta en
cada `push` a `main` y:

1. Instala las dependencias con Python 3.11.
2. Verifica que la app arranca.
3. Ejecuta `python freeze.py` → genera `build/`.
4. Publica `build/` en la rama **`gh-pages`** con `peaceiris/actions-gh-pages@v4`.

### Qué contiene el build

```
build/
├── index.html          # dashboard renderizado
├── static/             # CSS y JS
├── api/
│   ├── dataset.json    # dataset completo (filtrado en el navegador)
│   ├── kpis.json
│   ├── analysis.json
│   └── meta.json
└── .nojekyll
```

`freeze.py` usa **URLs relativas**, por lo que el sitio funciona igual en la raíz de un
dominio que en `usuario.github.io/repositorio/`. Si prefieres URLs absolutas, define
`FREEZER_BASE_URL`.

### Activar Pages (una sola vez)

Tras el primer despliegue exitoso:

**Settings → Pages → Build and deployment → Source: `Deploy from a branch` →
Branch: `gh-pages` / `(root)` → Save**

El dashboard quedará en `https://sgora96.github.io/wildfire-data-mining/`.

> **Modo estático:** en GitHub Pages no hay backend, pero el dashboard sigue siendo
> interactivo. `main.js` detecta el modo, carga `api/dataset.json` y recalcula KPIs,
> gráficos y filtros en el navegador con un motor que replica `services.py`.
> La carga de archivos acepta CSV en memoria (sin persistencia).

---

## 🔗 Conexión con Git

Desde la raíz del proyecto:

```bash
git init
git branch -M main
git add .
git commit -m "feat: estructura base del proyecto Wildfire Data Mining"
git remote add origin https://github.com/sgora96/wildfire-data-mining.git
git push -u origin main
```

Si el repositorio remoto ya tiene commits (por ejemplo un README creado desde GitHub):

```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```

Flujo de trabajo posterior:

```bash
git add .
git commit -m "feat: descripcion del cambio"
git push
```

---

## 🧭 Próximos pasos

- [ ] Sustituir el dataset sintético por datos reales en `data/raw/`
- [ ] Notebook de EDA y limpieza → volcado a `data/processed/`
- [ ] Entrenar el modelo de predicción de área quemada y guardarlo en `models/`
- [ ] Conectar `/api/predict` al modelo entrenado
- [ ] Añadir pruebas con `pytest` sobre `services.py`
- [ ] Incluir un mapa geoespacial con las coordenadas `X`/`Y`

---

## 📄 Licencia

Proyecto de uso académico e investigativo.
