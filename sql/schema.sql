-- Modelo estrella de incendios de la cobertura vegetal (IDEAM, 2010-2024).
-- Granularidad de la tabla de hechos: un evento de incendio reportado.
-- Motor: SQLite. Se ejecuta desde scripts/etl/build_dw.py sobre una base nueva.

PRAGMA foreign_keys = ON;

-- Dimension tiempo. Jerarquia: h_anio -> h_trimestre -> h_mes.
CREATE TABLE dim_tiempo (
  tiempo_key   INTEGER PRIMARY KEY,   -- AAAAMM; AAAA00 = anio sin mes valido; 0 = sin fecha
  anio         INTEGER,               -- NULL en tiempo_key 0
  trimestre    INTEGER,               -- 1..4; NULL si el mes se desconoce
  mes_num      INTEGER,               -- 1..12; NULL si se desconoce
  mes_nombre   TEXT NOT NULL,         -- 'Enero'..'Diciembre' | 'Sin mes' | 'Sin fecha'
  temporada    TEXT NOT NULL,         -- '1. Ene-Mar' | '2. Jul-Sep' | '3. Abr-Jun y Oct-Dic' | 'Sin dato'
  h_anio       TEXT NOT NULL,         -- nivel 1: '2024' | 'Sin fecha'
  h_trimestre  TEXT NOT NULL,         -- nivel 2: '2024-T1' | '2014-sin trimestre' | 'Sin fecha'
  h_mes        TEXT NOT NULL          -- nivel 3: '2024-01' | '2014-sin mes' | 'Sin fecha'
);

-- Dimension territorio. Jerarquia: h_region -> h_departamento -> h_municipio.
CREATE TABLE dim_territorio (
  territorio_key  INTEGER PRIMARY KEY,   -- subrogada; 0 = desconocido total
  region          TEXT NOT NULL,         -- region natural; 'Sin region'
  departamento    TEXT NOT NULL,         -- 'Sin departamento'
  municipio       TEXT NOT NULL,         -- nombre para mostrar; 'Sin municipio'
  municipio_clave TEXT NOT NULL,         -- normalizado: MAYUSCULAS, sin tildes, sin espacios sobrantes
  h_region        TEXT NOT NULL,         -- nivel 1: = region
  h_departamento  TEXT NOT NULL,         -- nivel 2: = departamento (unico entre regiones)
  h_municipio     TEXT NOT NULL,         -- nivel 3: departamento || ' / ' || municipio (distingue homonimos)
  UNIQUE (departamento, municipio_clave)
);

-- Dimension tamano del incendio (clases por hectareas).
CREATE TABLE dim_tamano (
  tamano_key  INTEGER PRIMARY KEY,   -- 0 Sin dato | 1 | 2 | 3 | 4
  clase       TEXT NOT NULL,         -- 'Sin dato' | '<= 1 ha' | '1-10 ha' | '10-100 ha' | '> 100 ha'
  orden       INTEGER NOT NULL,      -- para ordenar
  es_grande   INTEGER NOT NULL       -- 1 solo para '> 100 ha'
);

-- Dimension causa. Jerarquia: registro -> causa.
CREATE TABLE dim_causa (
  causa_key  INTEGER PRIMARY KEY,   -- 0 sin causa | 1 Intencional | 2 Quema fuera de control
                                    -- | 3 Descuido o negligencia | 4 Accidental | 5 Reactivacion de focos
                                    -- | 6 Otra | 7 Mas de una causa
  causa      TEXT NOT NULL,
  registro   TEXT NOT NULL          -- 'Con causa registrada' | 'Mas de una causa' | 'Sin causa registrada'
);

-- Dimension cobertura. Jerarquia: grupo_cobertura -> tipo_cobertura.
CREATE TABLE dim_cobertura (
  cobertura_key    INTEGER PRIMARY KEY,   -- 0 Sin cobertura informada | 1..11 tipos | 12 Mas de un tipo
  grupo_cobertura  TEXT NOT NULL,         -- nivel 1
  tipo_cobertura   TEXT NOT NULL          -- nivel 2
);

-- Dimension fuente. Jerarquia: h_hoja -> h_entidad.
CREATE TABLE dim_fuente (
  fuente_key    INTEGER PRIMARY KEY,
  hoja          TEXT NOT NULL,        -- 'BD_ICV_2010_2020' | 'BD_ICV_2021' | ... | 'BD_ICV_2024'
  periodo_hoja  TEXT NOT NULL,        -- '2010-2020' | '2021' | ... | '2024'
  entidad       TEXT NOT NULL,        -- ENTIDAD_REPORTA | 'No aplica (hoja sin ese campo)' | 'Sin dato'
  h_hoja        TEXT NOT NULL,        -- nivel 1 = hoja
  h_entidad     TEXT NOT NULL,        -- nivel 2 = hoja || ' / ' || entidad
  UNIQUE (hoja, entidad)
);

-- Tabla de hechos: una fila por evento reportado.
CREATE TABLE fact_incendio (
  id_evento       INTEGER PRIMARY KEY,   -- 1..35.355 en el orden del CSV (clave del evento)
  tiempo_key      INTEGER NOT NULL REFERENCES dim_tiempo(tiempo_key),
  territorio_key  INTEGER NOT NULL REFERENCES dim_territorio(territorio_key),
  tamano_key      INTEGER NOT NULL REFERENCES dim_tamano(tamano_key),
  causa_key       INTEGER NOT NULL REFERENCES dim_causa(causa_key),
  cobertura_key   INTEGER NOT NULL REFERENCES dim_cobertura(cobertura_key),
  fuente_key      INTEGER NOT NULL REFERENCES dim_fuente(fuente_key),
  n_eventos       INTEGER NOT NULL DEFAULT 1,  -- medida: conteo de eventos
  area_total_ha   REAL,                        -- medida: hectareas; NULL si no hay dato (no se convierte a 0)
  con_area        INTEGER NOT NULL             -- 1 si area_total_ha NO es NULL, 0 si es NULL
);

CREATE INDEX ix_fact_tiempo     ON fact_incendio (tiempo_key);
CREATE INDEX ix_fact_territorio ON fact_incendio (territorio_key);
CREATE INDEX ix_fact_tamano     ON fact_incendio (tamano_key);
CREATE INDEX ix_fact_causa      ON fact_incendio (causa_key);
CREATE INDEX ix_fact_cobertura  ON fact_incendio (cobertura_key);
CREATE INDEX ix_fact_fuente     ON fact_incendio (fuente_key);
