"""Perfilamiento, evaluacion de calidad y tratamiento del dataset de la Etapa 2.

Lee el dataset consolidado de la Etapa 1 (data/processed/incendios_ideam_2010_2024.csv),
que se trata como dataset "crudo" para esta etapa (no se modifica), y genera:

  - data/processed/incendios_ideam_tratado_2010_2024.csv
      Version tratada, con columnas nuevas de apoyo (_NUM, _NORM, _FLAG) y sin
      duplicados exactos. Las columnas originales se conservan (no se sobreescriben)
      para poder comparar antes/despues campo a campo.

  - data/processed/calidad_r2_resumen.json
      Resumen estructurado que consume la seccion "Calidad de Datos" de la app
      Flask: perfilamiento, las 6 dimensiones con su metrica, inventario de
      problemas, y comparacion antes/despues.

Uso:
    python scripts/data_quality_r2.py
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_PATH = BASE_DIR / "data" / "processed" / "incendios_ideam_2010_2024.csv"
OUT_CSV = BASE_DIR / "data" / "processed" / "incendios_ideam_tratado_2010_2024.csv"
OUT_JSON = BASE_DIR / "data" / "processed" / "calidad_r2_resumen.json"

HOY = date(2026, 9, 10)

# --------------------------------------------------------------------------- #
# 1. Carga
# --------------------------------------------------------------------------- #
df = pd.read_csv(RAW_PATH, encoding="utf-8-sig", dtype=str)
N0 = len(df)
COLS = list(df.columns)

# --------------------------------------------------------------------------- #
# 2. Perfilamiento (sobre el dataset crudo, antes de tratar)
# --------------------------------------------------------------------------- #
NUMERIC_ISH = [
    "ELEVACION_MSNM", "AREA_COPA_HA", "AREA_SUPERFICIAL_HA", "AREA_SUBTERRANEO_HA",
    "AREA_MIXTO_HA", "AREA_OTRO_TIPO_HA", "COB_BOSQUE_NATURAL_DENSO",
    "COB_BOSQUE_INTERVENIDO", "COB_BOSQUE_PLANTADO", "COB_BOSQUE_SECO",
    "COB_CULTIVOS", "COB_PARAMOS", "COB_SABANAS_PASTIZALES", "COB_PASTOS_MANEJADOS",
    "COB_RASTROJO", "COB_VEGETACION_SECA", "COB_COBERTURA_SIN_DETERMINAR",
    "AREA_TOTAL_HA",
]


def to_numeric_safe(series: pd.Series) -> pd.Series:
    """Extrae el numero de una celda que puede traer texto residual.

    Ej.: "SUP" -> NaN, "5" -> 5.0, "3.5" -> 3.5, "Bogota" -> NaN.
    """
    cleaned = series.astype(str).str.strip().str.replace(",", ".", regex=False)
    is_number = cleaned.str.fullmatch(r"-?\d+(\.\d+)?")
    out = pd.to_numeric(cleaned.where(is_number), errors="coerce")
    return out


profiling_columns = {}
for col in COLS:
    s = df[col]
    nulos = int(s.isna().sum())
    profiling_columns[col] = {
        "tipo_declarado": "texto",
        "valores_unicos": int(s.nunique(dropna=True)),
        "nulos": nulos,
        "pct_nulos": round(100 * nulos / N0, 2),
    }
    if col in NUMERIC_ISH:
        num = to_numeric_safe(s)
        no_numericos = int(s.notna().sum() - num.notna().sum())
        profiling_columns[col].update(
            {
                "tipo_declarado": "numerico (con texto residual)",
                "valores_no_numericos": no_numericos,
                "min": None if num.dropna().empty else float(num.min()),
                "max": None if num.dropna().empty else float(num.max()),
                "promedio": None if num.dropna().empty else round(float(num.mean()), 2),
            }
        )

duplicados_exactos = int(df.duplicated(keep="first").sum())

# --------------------------------------------------------------------------- #
# 3. Homologacion de DEPARTAMENTO (verificada manualmente, ver docs/tareas)
# --------------------------------------------------------------------------- #
CANONICAL_DEPTOS = [
    "Amazonas", "Antioquia", "Arauca", "Atlántico", "Bolívar", "Boyacá", "Caldas",
    "Caquetá", "Casanare", "Cauca", "Cesar", "Chocó", "Córdoba", "Cundinamarca",
    "Guainía", "Guaviare", "Huila", "La Guajira", "Magdalena", "Meta", "Nariño",
    "Norte de Santander", "Putumayo", "Quindío", "Risaralda",
    "San Andrés, Providencia y Santa Catalina", "Santander", "Sucre", "Tolima",
    "Valle del Cauca", "Vaupés", "Vichada", "Bogotá, D.C.",
]


def fold(s: str) -> str:
    s = str(s).upper().strip()
    s = s.replace("�", "")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace(".", "").replace(",", "")
    return " ".join(s.split())


_canon_folded = {fold(c): c for c in CANONICAL_DEPTOS}
_folded_keys = list(_canon_folded.keys())


def homologar_depto(raw) -> str | None:
    if pd.isna(raw):
        return None
    f = fold(raw)
    if f in _canon_folded:
        return _canon_folded[f]
    contains = sorted((k for k in _folded_keys if f in k or k in f), key=len)
    if contains:
        return _canon_folded[contains[0]]
    return None  # no se encontro homologo confiable -> queda nulo, no se inventa


depto_raw_values = sorted(df["DEPARTAMENTO"].dropna().unique().tolist())
depto_map = {raw: homologar_depto(raw) for raw in depto_raw_values}
depto_sin_homologar = [r for r, c in depto_map.items() if c is None]

# --------------------------------------------------------------------------- #
# 4. Homologacion de MES
# --------------------------------------------------------------------------- #
MESES_CANON = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
    "Septiembre", "Octubre", "Noviembre", "Diciembre",
]
_mes_map = {m.upper(): m for m in MESES_CANON}


def homologar_mes(raw):
    if pd.isna(raw):
        return None
    key = str(raw).strip().upper()
    if key == "SIN REPORTE":
        return "Sin reporte"
    return _mes_map.get(key, None)


# --------------------------------------------------------------------------- #
# 5. Parseo de coordenadas
# --------------------------------------------------------------------------- #
# Colombia continental + insular: latitud aprox. -4.2 a 13.5, longitud aprox. -82 a -66.
LAT_RANGE = (-4.5, 13.6)
LON_RANGE = (-82.0, -66.0)

# LATITUD/LONGITUD mezclan MULTIPLES sistemas/formatos sin documentarlo:
#   (a) grados.minutos.segundos,decimo con punto como separador de componente
#       (ej. "06.08.39,5") -- formato dominante, hoja 2010-2020.
#   (b) grados decimales ya convertidos, con precision de punto flotante
#       (ej. "7.010833333").
#   (c) grados-minutos-segundos con simbolos (°, ', ") y a veces con la
#       latitud y la longitud concatenadas en una sola celda (ej.
#       "N12°31'13.7\" W081°42'52.8\"").
#   (d) coordenadas PLANAS en el sistema de referencia MAGNA-SIRGAS
#       (proyectado, en metros -- no son grados y no se pueden convertir con
#       una formula de grados/minutos/segundos; requieren una transformacion
#       geodesica con el EPSG correcto, fuera del alcance de esta etapa).
# Tratamiento adoptado: solo se convierten automaticamente los formatos (a) y
# (b) -- numericos, sin letras ni simbolos. Los formatos (c) y (d) se dejan
# sin convertir y se cuantifican como hallazgo (ver inventario de problemas).
_COORD_NUMERICA = re.compile(r"-?\d+(\.\d+)*(,\d+)?")


def parse_coord(raw, es_longitud: bool) -> float | None:
    if pd.isna(raw):
        return None
    txt = str(raw).strip()
    if not txt or not _COORD_NUMERICA.fullmatch(txt):
        return None
    partes = txt.split(".")
    try:
        if len(partes) == 1:
            decimal = float(partes[0].replace(",", "."))
        elif len(partes) == 2 and len(partes[1].split(",")[0]) > 2:
            # Ya viene como decimal con varios decimales (formato b)
            decimal = float(txt.replace(",", "."))
        else:
            grados = int(partes[0])
            minutos = int(partes[1]) if len(partes) > 1 and partes[1] else 0
            seg_txt = ".".join(partes[2:]).replace(",", ".") if len(partes) > 2 and partes[2] else "0"
            segundos = float(seg_txt) if seg_txt else 0.0
            decimal = grados + minutos / 60 + segundos / 3600
    except ValueError:
        return None
    if es_longitud:
        decimal = -abs(decimal)  # Colombia esta al oeste del meridiano de Greenwich
    if abs(decimal) > 200:
        return None  # magnitud no plausible como coordenada -> no se fuerza la conversion
    return round(decimal, 6)


def es_formato_no_convertible(raw) -> bool:
    """Coordenada presente pero en un formato (c)/(d) que esta etapa no convierte."""
    if pd.isna(raw):
        return False
    txt = str(raw).strip()
    return bool(txt) and not _COORD_NUMERICA.fullmatch(txt)


lat_dec = df["LATITUD"].apply(lambda v: parse_coord(v, es_longitud=False))
lon_dec = df["LONGITUD"].apply(lambda v: parse_coord(v, es_longitud=True))
lat_en_rango = lat_dec.between(*LAT_RANGE)
lon_en_rango = lon_dec.between(*LON_RANGE)
coord_valida = lat_dec.notna() & lon_dec.notna() & lat_en_rango & lon_en_rango
coord_fuera_de_rango = int(((lat_dec.notna() & ~lat_en_rango) | (lon_dec.notna() & ~lon_en_rango)).sum())
coord_formato_no_convertible = int(
    (df["LATITUD"].apply(es_formato_no_convertible) | df["LONGITUD"].apply(es_formato_no_convertible)).sum()
)

# --------------------------------------------------------------------------- #
# 6. Consistencia ANIO vs FECHA_REGISTRO
# --------------------------------------------------------------------------- #
fecha_dt = pd.to_datetime(df["FECHA_REGISTRO"], format="%Y-%m-%d", errors="coerce")
anio_num = pd.to_numeric(df["ANIO"], errors="coerce")
anio_vs_fecha_inconsistente = int(
    (fecha_dt.notna() & anio_num.notna() & (fecha_dt.dt.year != anio_num)).sum()
)

# --------------------------------------------------------------------------- #
# 7. Elevacion: valor invalido conocido (-1) y rango plausible para Colombia
# --------------------------------------------------------------------------- #
elev_num = to_numeric_safe(df["ELEVACION_MSNM"])
ELEV_RANGE = (0, 5800)
elev_invalida = int(((elev_num < ELEV_RANGE[0]) | (elev_num > ELEV_RANGE[1])).sum())

# --------------------------------------------------------------------------- #
# 8. Area total: outliers por rango intercuartilico (IQR)
# --------------------------------------------------------------------------- #
area_total_num = to_numeric_safe(df["AREA_TOTAL_HA"])
q1, q3 = area_total_num.quantile(0.25), area_total_num.quantile(0.75)
iqr = q3 - q1
limite_superior = q3 + 1.5 * iqr
area_total_atipicos = int((area_total_num > limite_superior).sum())
area_total_negativos = int((area_total_num < 0).sum())

# --------------------------------------------------------------------------- #
# 9. Construccion del dataset tratado
# --------------------------------------------------------------------------- #
tratado = df.copy()

# 9.1 Deduplicacion (se conserva la primera aparicion)
tratado = tratado.drop_duplicates(keep="first").reset_index(drop=True)
n_tras_dedup = len(tratado)

# 9.2 Homologacion de texto
tratado["DEPARTAMENTO_NORM"] = tratado["DEPARTAMENTO"].apply(homologar_depto)
tratado["MES_NORM"] = tratado["MES"].apply(homologar_mes)
tratado["MUNICIPIO_NORM"] = tratado["MUNICIPIO"].astype(str).str.strip()
tratado.loc[tratado["MUNICIPIO"].isna(), "MUNICIPIO_NORM"] = None

# 9.3 Coordenadas a decimal + bandera de validez
tratado["LATITUD_DEC"] = tratado["LATITUD"].apply(lambda v: parse_coord(v, es_longitud=False))
tratado["LONGITUD_DEC"] = tratado["LONGITUD"].apply(lambda v: parse_coord(v, es_longitud=True))
lat_ok = tratado["LATITUD_DEC"].between(*LAT_RANGE)
lon_ok = tratado["LONGITUD_DEC"].between(*LON_RANGE)
tratado["COORDENADAS_VALIDAS"] = (
    tratado["LATITUD_DEC"].notna() & tratado["LONGITUD_DEC"].notna() & lat_ok & lon_ok
)
# Coordenadas fuera del rango esperado no se usan como validas (se dejan nulas para analisis geoespacial)
tratado.loc[~tratado["COORDENADAS_VALIDAS"], ["LATITUD_DEC", "LONGITUD_DEC"]] = None

# 9.4 Elevacion: el valor -1 (y cualquier fuera de rango) se trata como dato invalido, no como 0
tratado["ELEVACION_MSNM_NUM"] = to_numeric_safe(tratado["ELEVACION_MSNM"])
elev_fuera_rango_mask = (tratado["ELEVACION_MSNM_NUM"] < ELEV_RANGE[0]) | (
    tratado["ELEVACION_MSNM_NUM"] > ELEV_RANGE[1]
)
tratado.loc[elev_fuera_rango_mask, "ELEVACION_MSNM_NUM"] = None

# 9.5 Columnas de area/cobertura: version numerica limpia + bandera de si tenian texto residual
for col in NUMERIC_ISH:
    if col in ("ELEVACION_MSNM",):
        continue
    raw_col = tratado[col]
    num_col = to_numeric_safe(raw_col)
    tratado[f"{col}_NUM"] = num_col
    tratado[f"{col}_TEXTO_RESIDUAL"] = raw_col.notna() & num_col.isna()

# 9.6 Marca de registros con identificacion incompleta (sin fecha/ubicacion basica)
tratado["REGISTRO_INCOMPLETO"] = (
    tratado["ANIO"].isna()
    & tratado["MES"].isna()
    & tratado["FECHA_REGISTRO"].isna()
    & tratado["DEPARTAMENTO"].isna()
)

# 9.7 Consistencia ANIO vs FECHA_REGISTRO (se prioriza el ANIO del registro, se deja evidencia)
fecha_dt_tr = pd.to_datetime(tratado["FECHA_REGISTRO"], format="%Y-%m-%d", errors="coerce")
anio_num_tr = pd.to_numeric(tratado["ANIO"], errors="coerce")
tratado["ANIO_FECHA_INCONSISTENTE"] = (
    fecha_dt_tr.notna() & anio_num_tr.notna() & (fecha_dt_tr.dt.year != anio_num_tr)
)

# 9.8 Area total: version numerica limpia + bandera de valor atipico (no se elimina, se marca)
tratado["AREA_TOTAL_HA_NUM"] = to_numeric_safe(tratado["AREA_TOTAL_HA"])
tratado["AREA_TOTAL_ATIPICO"] = tratado["AREA_TOTAL_HA_NUM"] > limite_superior

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
tratado.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

# --------------------------------------------------------------------------- #
# 10. Metricas "despues" para la comparacion antes/despues
# --------------------------------------------------------------------------- #
depto_distintos_despues = int(tratado["DEPARTAMENTO_NORM"].nunique(dropna=True))
mes_distintos_despues = int(tratado["MES_NORM"].nunique(dropna=True))
coordenadas_validas_despues = int(tratado["COORDENADAS_VALIDAS"].sum())

# --------------------------------------------------------------------------- #
# 11. Dimensiones de calidad (6), con metrica y resultado
# --------------------------------------------------------------------------- #
campos_clave = ["ANIO", "MES", "FECHA_REGISTRO", "DEPARTAMENTO", "MUNICIPIO", "AREA_TOTAL_HA"]
completitud_por_campo = {
    c: round(100 * df[c].notna().sum() / N0, 2) for c in campos_clave
}
completitud_promedio = round(sum(completitud_por_campo.values()) / len(completitud_por_campo), 2)

dimensiones = {
    "completitud": {
        "definicion": "Proporcion de valores presentes (no nulos) sobre el total de registros.",
        "formula": "1 - (nulos / total), promediado sobre los campos clave",
        "campos_clave": completitud_por_campo,
        "resultado_pct": completitud_promedio,
    },
    "exactitud": {
        "definicion": "Proporcion de valores que representan correctamente el dato real esperado (no marcadores de texto en campos numericos, ni valores fuera de rango fisico).",
        "formula": "1 - (valores_no_numericos_en_campos_de_area + elevaciones_fuera_de_rango) / total_de_celdas_evaluadas",
        "valores_no_numericos_en_areas_cobertura": sum(
            profiling_columns[c].get("valores_no_numericos", 0)
            for c in NUMERIC_ISH
            if c != "ELEVACION_MSNM"
        ),
        "elevaciones_fuera_de_rango_fisico": elev_invalida,
        "resultado_pct": round(
            100
            * (
                1
                - (
                    sum(
                        profiling_columns[c].get("valores_no_numericos", 0)
                        for c in NUMERIC_ISH
                        if c != "ELEVACION_MSNM"
                    )
                    + elev_invalida
                )
                / (N0 * (len(NUMERIC_ISH)))
            ),
            2,
        ),
    },
    "consistencia": {
        "definicion": "Proporcion de registros donde campos relacionados entre si no se contradicen (ej. el año de ANIO coincide con el año de FECHA_REGISTRO).",
        "formula": "1 - (registros_inconsistentes / registros_con_ambos_campos_diligenciados)",
        "anio_vs_fecha_inconsistentes": anio_vs_fecha_inconsistente,
        "registros_evaluables": int((fecha_dt.notna() & anio_num.notna()).sum()),
        "resultado_pct": round(
            100 * (1 - anio_vs_fecha_inconsistente / max(int((fecha_dt.notna() & anio_num.notna()).sum()), 1)),
            2,
        ),
    },
    "unicidad": {
        "definicion": "Proporcion de registros que no estan duplicados exactamente.",
        "formula": "1 - (registros_duplicados / total_de_registros)",
        "registros_duplicados": duplicados_exactos,
        "resultado_pct": round(100 * (1 - duplicados_exactos / N0), 2),
    },
    "validez": {
        "definicion": "Proporcion de valores que pertenecen al dominio esperado de la variable (departamento dentro de la lista oficial de 33, mes dentro de los 12 meses, coordenadas dentro del territorio colombiano).",
        "formula": "promedio de (valores_en_dominio / valores_no_nulos) para DEPARTAMENTO, MES y coordenadas",
        "departamento_sin_homologar": len(depto_sin_homologar),
        "coordenadas_fuera_de_rango": coord_fuera_de_rango,
        "resultado_pct": round(
            100
            * (
                (1 - len(depto_sin_homologar) / max(len(depto_raw_values), 1))
                + (1 - coord_fuera_de_rango / max(int((lat_dec.notna() | lon_dec.notna()).sum()), 1))
            )
            / 2,
            2,
        ),
    },
    "actualidad": {
        "definicion": "Que tan reciente es la informacion disponible respecto a la fecha de analisis.",
        "formula": "hoy - fecha_del_registro_mas_reciente (en anios)",
        "fecha_analisis": HOY.isoformat(),
        "anio_maximo_en_datos": int(anio_num.max()) if anio_num.notna().any() else None,
        "brecha_anios": (HOY.year - int(anio_num.max())) if anio_num.notna().any() else None,
        "nota": "Es un registro administrativo historico (no un feed en tiempo real); una brecha de 1-2 anios es esperable mientras el IDEAM consolida y publica el reporte del ultimo anio.",
    },
}

# --------------------------------------------------------------------------- #
# 12. Inventario de problemas
# --------------------------------------------------------------------------- #
problemas = [
    {
        "variable": "DEPARTAMENTO",
        "descripcion": "El mismo departamento aparece escrito de formas distintas entre hojas (con/sin tilde, mayusculas/minusculas, con/sin coma antes de D.C.): 45 valores de texto para 33 departamentos reales.",
        "registros_afectados": int(df["DEPARTAMENTO"].notna().sum()),
        "dimension": "Validez / Consistencia",
        "nivel_impacto": "Alto",
        "evidencia": f"{len(depto_raw_values)} valores de texto distintos -> homologados a {depto_distintos_despues} despues del tratamiento.",
    },
    {
        "variable": "MES",
        "descripcion": "Mayusculas/minusculas inconsistentes entre hojas, mas el valor 'SIN REPORTE' sin documentar.",
        "registros_afectados": int(df["MES"].notna().sum()),
        "dimension": "Validez",
        "nivel_impacto": "Medio",
        "evidencia": f"{int(df['MES'].nunique())} valores distintos -> {mes_distintos_despues} despues de homologar.",
    },
    {
        "variable": "AREA_*_HA (5 columnas por tipo de incendio)",
        "descripcion": "Columnas pensadas como numericas (hectareas) que mezclan marcadores de texto (ej. 'SUP', 'X', nombres de ciudad) con numeros.",
        "registros_afectados": sum(
            profiling_columns[c].get("valores_no_numericos", 0)
            for c in ["AREA_COPA_HA", "AREA_SUPERFICIAL_HA", "AREA_SUBTERRANEO_HA", "AREA_MIXTO_HA", "AREA_OTRO_TIPO_HA"]
        ),
        "dimension": "Exactitud",
        "nivel_impacto": "Alto",
        "evidencia": "Ver columna 'valores_no_numericos' del perfilamiento para cada campo.",
    },
    {
        "variable": "COB_* (11 columnas de cobertura vegetal)",
        "descripcion": "Columnas mayoritariamente numericas con un porcentaje menor de texto residual (marcadores o nombres de cobertura sueltos).",
        "registros_afectados": sum(
            profiling_columns[c].get("valores_no_numericos", 0)
            for c in NUMERIC_ISH
            if c.startswith("COB_")
        ),
        "dimension": "Exactitud",
        "nivel_impacto": "Medio",
        "evidencia": "Ver columna 'valores_no_numericos' del perfilamiento para cada campo COB_*.",
    },
    {
        "variable": "LATITUD / LONGITUD",
        "descripcion": "Formato de texto grados.minutos.segundos con separador decimal de coma, con variantes (a veces sin segundos); ademas ausentes en la gran mayoria de registros.",
        "registros_afectados": int(df["LATITUD"].notna().sum()),
        "dimension": "Completitud / Validez",
        "nivel_impacto": "Alto",
        "evidencia": f"{profiling_columns['LATITUD']['pct_nulos']}% nulos; de las presentes, {coord_fuera_de_rango} quedaron fuera del rango geografico de Colombia al convertir.",
    },
    {
        "variable": "LATITUD / LONGITUD",
        "descripcion": "Ademas del formato dominante, una parte de los registros usa sistemas de referencia distintos sin documentarlo: grados-minutos-segundos con simbolos (°, ', \") -a veces con latitud y longitud concatenadas en una sola celda-, y coordenadas planas en el sistema MAGNA-SIRGAS (proyectado en metros, no en grados). Estos formatos no son convertibles con una formula de grados/minutos/segundos: requieren una transformacion geodesica con el EPSG correcto.",
        "registros_afectados": coord_formato_no_convertible,
        "dimension": "Validez / Consistencia",
        "nivel_impacto": "Medio",
        "evidencia": f"{coord_formato_no_convertible} registros con coordenada presente en un formato no numerico simple; no se convirtieron en esta etapa (se documentan como limitacion, ver plan de tratamiento).",
    },
    {
        "variable": "ELEVACION_MSNM",
        "descripcion": "Incluye al menos un valor -1, fisicamente invalido como elevacion sobre el nivel del mar en Colombia.",
        "registros_afectados": elev_invalida,
        "dimension": "Exactitud",
        "nivel_impacto": "Bajo",
        "evidencia": f"{elev_invalida} registros fuera del rango plausible 0-5800 msnm.",
    },
    {
        "variable": "(registro completo)",
        "descripcion": "Registros duplicados exactamente en todas las columnas.",
        "registros_afectados": duplicados_exactos,
        "dimension": "Unicidad",
        "nivel_impacto": "Alto",
        "evidencia": f"{duplicados_exactos} de {N0} registros ({round(100*duplicados_exactos/N0,1)}%) son duplicados exactos.",
    },
    {
        "variable": "ANIO / MES / FECHA_REGISTRO / DEPARTAMENTO",
        "descripcion": "Registros sin ninguno de los campos de fecha ni ubicacion diligenciados; no permiten analisis temporal ni geografico.",
        "registros_afectados": int(tratado["REGISTRO_INCOMPLETO"].sum()),
        "dimension": "Completitud",
        "nivel_impacto": "Medio",
        "evidencia": f"{int(tratado['REGISTRO_INCOMPLETO'].sum())} registros sin fecha ni ubicacion.",
    },
    {
        "variable": "ANIO vs FECHA_REGISTRO",
        "descripcion": "El año del campo ANIO no coincide con el año contenido en FECHA_REGISTRO para el mismo registro.",
        "registros_afectados": anio_vs_fecha_inconsistente,
        "dimension": "Consistencia",
        "nivel_impacto": "Bajo",
        "evidencia": f"{anio_vs_fecha_inconsistente} registros con año inconsistente entre ambos campos.",
    },
    {
        "variable": "AREA_TOTAL_HA",
        "descripcion": "Valores atipicos (muy por encima del resto de la distribucion) segun el criterio de rango intercuartilico (IQR).",
        "registros_afectados": area_total_atipicos,
        "dimension": "Exactitud",
        "nivel_impacto": "Bajo",
        "evidencia": f"Limite superior IQR = {round(limite_superior,2)} ha; {area_total_atipicos} registros lo superan (no se eliminaron: se marcaron, ver plan de tratamiento).",
    },
]

# --------------------------------------------------------------------------- #
# 13. Comparacion antes / despues
# --------------------------------------------------------------------------- #
comparacion = {
    "registros": {"antes": N0, "despues": n_tras_dedup, "eliminados_por_duplicado": N0 - n_tras_dedup},
    "departamentos_distintos": {"antes": len(depto_raw_values), "despues": depto_distintos_despues},
    "meses_distintos": {"antes": int(df["MES"].nunique()), "despues": mes_distintos_despues},
    "coordenadas_utilizables": {"antes": int(coord_valida.sum()), "despues": coordenadas_validas_despues},
    "elevaciones_invalidas": {"antes": elev_invalida, "despues": 0},
    "duplicados_exactos": {"antes": duplicados_exactos, "despues": int(tratado.duplicated(keep="first").sum())},
}

# --------------------------------------------------------------------------- #
# 14. Plan de tratamiento aplicado (para documentar en la app / informe)
# --------------------------------------------------------------------------- #
plan_tratamiento = [
    {
        "accion": "Eliminacion de duplicados",
        "detalle": f"Se eliminaron {N0 - n_tras_dedup} registros exactamente duplicados, conservando la primera aparicion.",
        "justificacion": "Duplicados exactos no aportan informacion nueva y sobreestiman la frecuencia de incendios si no se retiran.",
    },
    {
        "accion": "Homologacion de categorias (DEPARTAMENTO, MES)",
        "detalle": f"Se normalizaron {len(depto_raw_values)} variantes de texto de DEPARTAMENTO a los 33 departamentos oficiales, y las variantes de MES a 12 meses + 'Sin reporte'.",
        "justificacion": "Sin esta homologacion, un analisis por departamento o por mes subestima cada categoria real al repartir los conteos entre variantes de texto.",
    },
    {
        "accion": "Correccion de tipos de datos",
        "detalle": "Se generaron columnas numericas limpias (_NUM) para las 17 columnas de area/cobertura/elevacion, separando el valor numerico del marcador de texto (columna _TEXTO_RESIDUAL).",
        "justificacion": "Permite usar esas columnas en calculos estadisticos sin que un texto como 'SUP' rompa la operacion o se interprete como 0.",
    },
    {
        "accion": "Estandarizacion de coordenadas",
        "detalle": f"Se convirtieron a decimal (LATITUD_DEC, LONGITUD_DEC) unicamente los formatos numericos simples (grados.minutos.segundos con punto, o decimal ya convertido), validando que caigan dentro del territorio colombiano: {int(coord_valida.sum())} registros quedaron con coordenadas utilizables.",
        "justificacion": "El formato original no es utilizable directamente en un mapa; ademas permite detectar coordenadas mal capturadas (fuera del pais).",
    },
    {
        "accion": "Coordenadas en formato no convertible (decision de alcance)",
        "detalle": f"Los {coord_formato_no_convertible} registros con coordenada en sistema MAGNA-SIRGAS (planas) o con simbolos °/'/\" concatenando latitud y longitud NO se convirtieron.",
        "justificacion": "Convertirlas requiere una transformacion geodesica con el EPSG correcto (no una simple formula de grados/minutos/segundos); forzar una conversion incorrecta produciria coordenadas falsas, peor que dejarlas nulas. Se documenta como limitacion para una etapa posterior.",
    },
    {
        "accion": "Validacion de rangos",
        "detalle": "ELEVACION_MSNM fuera de 0-5800 msnm (incluye el valor -1) se trata como invalida (nula), no como un dato real.",
        "justificacion": "Un -1 no es una elevacion posible; mantenerlo como numero distorsionaria cualquier promedio o minimo.",
    },
    {
        "accion": "Tratamiento justificado de valores atipicos",
        "detalle": f"Los {area_total_atipicos} registros de AREA_TOTAL_HA por encima del limite IQR se marcaron (AREA_TOTAL_ATIPICO = True) en vez de eliminarse.",
        "justificacion": "Un incendio con area muy grande es un evento real y relevante para el problema de investigacion (severidad); eliminarlo sesgaria el analisis hacia abajo. Se deja marcado para que cualquier analisis posterior decida si lo excluye o no.",
    },
    {
        "accion": "Tratamiento de valores nulos",
        "detalle": "No se imputan valores para LATITUD/LONGITUD/ELEVACION ni para las columnas de causa/cobertura (su ausencia refleja que el campo no fue diligenciado en el reporte original, no un error de captura). Los registros sin fecha ni ubicacion se marcan (REGISTRO_INCOMPLETO) en vez de eliminarse.",
        "justificacion": "Inventar un valor para un campo que el IDEAM nunca reporto introduciria informacion falsa; es preferible dejar el nulo explicito y que el analisis lo tenga en cuenta.",
    },
]

# --------------------------------------------------------------------------- #
# 15. Ensamble del resumen final
# --------------------------------------------------------------------------- #
resumen = {
    "generado": HOY.isoformat(),
    "fuente": "data/processed/incendios_ideam_2010_2024.csv (dataset de la Etapa 1)",
    "perfilamiento": {
        "registros": N0,
        "variables": len(COLS),
        "registros_duplicados": duplicados_exactos,
        "columnas": profiling_columns,
    },
    "dimensiones": dimensiones,
    "problemas": problemas,
    "plan_tratamiento": plan_tratamiento,
    "comparacion_antes_despues": comparacion,
    "dataset_tratado": {
        "archivo": "data/processed/incendios_ideam_tratado_2010_2024.csv",
        "registros": n_tras_dedup,
        "columnas_nuevas": [
            "DEPARTAMENTO_NORM", "MES_NORM", "MUNICIPIO_NORM", "LATITUD_DEC", "LONGITUD_DEC",
            "COORDENADAS_VALIDAS", "ELEVACION_MSNM_NUM", "REGISTRO_INCOMPLETO",
            "ANIO_FECHA_INCONSISTENTE", "AREA_TOTAL_HA_NUM", "AREA_TOTAL_ATIPICO",
        ] + [f"{c}_NUM" for c in NUMERIC_ISH if c != "ELEVACION_MSNM"]
          + [f"{c}_TEXTO_RESIDUAL" for c in NUMERIC_ISH if c != "ELEVACION_MSNM"],
    },
}

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(resumen, f, ensure_ascii=False, indent=2)

print(f"Registros originales: {N0}")
print(f"Registros tras deduplicar: {n_tras_dedup} (-{N0 - n_tras_dedup})")
print(f"Departamentos: {len(depto_raw_values)} -> {depto_distintos_despues}")
print(f"Meses: {int(df['MES'].nunique())} -> {mes_distintos_despues}")
print(f"Coordenadas utilizables: {int(coord_valida.sum())} -> {coordenadas_validas_despues}")
print(f"Escrito: {OUT_CSV}")
print(f"Escrito: {OUT_JSON}")
