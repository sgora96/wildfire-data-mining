# Mapeo de variables y transformaciones del ETL

Procedimiento reproducible de transformación y carga del modelo estrella:

```bash
python scripts/etl/build_dw.py     # construye la base y la copia a app/static/olap/
python scripts/etl/validar_dw.py   # verifica el modelo y escribe docs/olap/validaciones.md
```

- **Entrada:** `data/processed/incendios_ideam_tratado_2010_2024.csv` (UTF-8 con BOM, separador
  coma, 35.355 filas, 80 columnas). Es el resultado del tratamiento de la Etapa 2
  (40.010 → 35.355 registros, departamentos de 45 variantes a 33, meses de 25 variantes a 12 más
  "Sin reporte").
- **Salida:** `data/warehouse/incendios_dw.db` (SQLite), creada desde `sql/schema.sql`, y una
  copia idéntica en `app/static/olap/incendios_dw.db`, que es la que sirven Flask y el sitio
  estático.
- **Dependencias:** solo `pandas`, `numpy` y `sqlite3` (ya en el proyecto).

## 1. Correspondencia variable original → campo del modelo

| Variable original (CSV) | Campo del modelo | Transformación |
|---|---|---|
| (posición de la fila, 1 a N) | `fact_incendio.id_evento` | Índice en el orden del archivo |
| `ANIO`, `MES_NORM` | `fact_incendio.tiempo_key` → `dim_tiempo` | Año × 100 + mes; sin mes válido → año × 100; sin año → 0 |
| `DEPARTAMENTO_NORM`, `MUNICIPIO_NORM` | `fact_incendio.territorio_key` → `dim_territorio` | Par (departamento, municipio normalizado); nulos → "Sin departamento" / "Sin municipio" |
| `AREA_TOTAL_HA_NUM` | `fact_incendio.area_total_ha` | Sin cambios; `NULL` se conserva |
| `AREA_TOTAL_HA_NUM` | `fact_incendio.con_area` | 1 si tiene dato, 0 si es nulo |
| `AREA_TOTAL_HA_NUM` | `fact_incendio.tamano_key` → `dim_tamano` | Clase por rangos (sección 2.3) |
| `CAUSA_QUEMA_FUERA_CONTROL`, `CAUSA_DESCUIDO_NEGLIGENCIA`, `CAUSA_INTENCIONAL`, `CAUSA_ACCIDENTAL`, `CAUSA_REACTIVACION_FOCOS`, `CAUSA_OTRA` | `fact_incendio.causa_key` → `dim_causa` | Reglas de la Etapa 4 (sección 2.4) |
| `COB_BOSQUE_NATURAL_DENSO_NUM`, `COB_BOSQUE_INTERVENIDO_NUM`, `COB_BOSQUE_PLANTADO_NUM`, `COB_BOSQUE_SECO_NUM`, `COB_SABANAS_PASTIZALES_NUM`, `COB_PASTOS_MANEJADOS_NUM`, `COB_CULTIVOS_NUM`, `COB_PARAMOS_NUM`, `COB_RASTROJO_NUM`, `COB_VEGETACION_SECA_NUM`, `COB_COBERTURA_SIN_DETERMINAR_NUM` | `fact_incendio.cobertura_key` → `dim_cobertura` | Columnas con valor mayor que 0 (sección 2.5) |
| `FUENTE_HOJA`, `ENTIDAD_REPORTA` | `fact_incendio.fuente_key` → `dim_fuente` | Par (hoja, entidad) (sección 2.6) |
| (constante) | `fact_incendio.n_eventos` | Siempre 1 |

Las demás columnas del CSV (coordenadas, elevación, áreas por tipo de incendio, banderas de
calidad y columnas `*_TEXTO_RESIDUAL`) no se cargan: no intervienen en las cuatro preguntas del
análisis multidimensional.

## 2. Reglas de transformación por dimensión

### 2.1 dim_tiempo

- Se generan todas las combinaciones: 15 años (2010-2024) × 12 meses, más un miembro "año sin
  mes" por año y un miembro "sin fecha" (`tiempo_key = 0`): 196 filas.
- `MES_NORM` (texto) se convierte a número de mes (Enero = 1 … Diciembre = 12). "Sin reporte" y
  nulo quedan sin mes.
- Trimestre = (mes − 1) ÷ 3 + 1. Temporada: T1 → "1. Ene-Mar"; T3 → "2. Jul-Sep"; T2 y T4 →
  "3. Abr-Jun y Oct-Dic".
- Un evento con mes pero sin año va a "sin fecha": el mes no se puede ubicar sin el año.

### 2.2 dim_territorio

- Clave natural: el par (departamento, `municipio_clave`). `municipio_clave` = nombre en
  mayúsculas, sin tildes y con espacios simplificados.
- El nombre para mostrar es la variante **más frecuente** entre las que comparten clave (en
  empate, la primera en orden alfabético).
- La región sale de un mapa departamento → región (ver [modelo_estrella.md](modelo_estrella.md),
  sección 7). Si un departamento del CSV no tuviera región, el ETL se detiene con un error.
- El miembro 0 es "Sin departamento / Sin municipio"; las claves restantes se asignan después de
  ordenar por (región, departamento, clave de municipio).

### 2.3 dim_tamano

| Área (`AREA_TOTAL_HA_NUM`) | `tamano_key` | `clase` |
|---|---|---|
| Nulo | 0 | Sin dato |
| ≤ 1 | 1 | <= 1 ha |
| > 1 y ≤ 10 | 2 | 1-10 ha |
| > 10 y ≤ 100 | 3 | 10-100 ha |
| > 100 | 4 | > 100 ha |

### 2.4 dim_causa

Se reutilizan exactamente las reglas de la Etapa 4 (`docs/powerbi/dax_base.md`). Cada celda de
las seis columnas `CAUSA_*` se clasifica así:

| Contenido de la celda | Decisión |
|---|---|
| `X`, `x`, `1`, `SI` | Marca afirmativa: se asigna la causa de la columna |
| `Q`, `D`, `I`, `A`, `R`, `O` | Letra de la propia causa: se asigna la causa de la columna |
| Texto que nombra una causa ("Accidental", "Intencional", "Quemas fuera de control", "Descuido y negligencia", "Reactivación de focos", "Otros", "rayo seco") | Se asigna la causa que nombra el texto, aunque esté en la columna de otra causa ("Otros" y "rayo seco" → Otra) |
| `0` | Respuesta negativa: se descarta |
| "Sin definir", "CONTROLADA" | No informativas: se descartan |
| Cualquier otro valor | El ETL se detiene con un error (no se adivina) |

Después se agrupan las causas distintas del evento: una causa → esa causa (claves 1 a 6); dos o
más → `causa_key = 7` ("Mas de una causa"); ninguna → `causa_key = 0` ("Sin causa registrada").

### 2.5 dim_cobertura

- Una columna `COB_*_NUM` mayor que 0 indica que el evento afectó ese tipo; 0 significa que no
  lo afectó y nulo que no se informó.
- Un tipo → esa cobertura (claves 1 a 11); dos o más → `cobertura_key = 12`
  ("Mas de un tipo de cobertura"); ninguno → `cobertura_key = 0` ("Sin cobertura informada").
- La clave de cada tipo sigue el orden de los grupos: Bosques (1 a 4), Pastos y sabanas (5 y 6),
  Cultivos (7), Paramos (8), Vegetacion arbustiva y seca (9 y 10), Cobertura sin determinar (11).

### 2.6 dim_fuente

- Las hojas 2010-2020, 2021, 2022 y 2023 no tienen `ENTIDAD_REPORTA`: su entidad es "No aplica
  (hoja sin ese campo)". Si apareciera una entidad fuera de la hoja 2024, el ETL se detiene.
- En la hoja 2024, la entidad vacía pasa a "Sin dato".
- `periodo_hoja` se deriva del nombre de la hoja (`BD_ICV_2010_2020` → "2010-2020").

## 3. Orden de ejecución y garantías

1. Se lee el CSV (`dtype=str`, vacíos como nulo) y se convierten a número el área y las columnas
   `COB_*_NUM`.
2. Se construyen las dimensiones y se calculan las claves de cada evento.
3. Se borra la base anterior, se crea la nueva con `sql/schema.sql` y se activa
   `PRAGMA foreign_keys = ON`.
4. Se cargan **primero las dimensiones** y después la tabla de hechos, para respetar las claves
   foráneas. Al final se ejecuta `PRAGMA foreign_key_check`; si devuelve filas, el ETL falla.
5. Se copia la base a `app/static/olap/` y se imprime el resumen (filas por tabla y totales de
   control).

**Determinismo.** Las dimensiones se ordenan antes de asignar claves subrogadas, de modo que
dos ejecuciones producen exactamente el mismo contenido.

**Verificación.** `scripts/etl/validar_dw.py` ejecuta las consultas de `sql/validaciones.sql` y
compara el modelo con los datos tratados (resultados en [validaciones.md](validaciones.md)).
