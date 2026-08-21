"""Capa de servicios: carga, filtrado y analisis exploratorio del dataset.

Las rutas (`app/routes.py`) permanecen delgadas y toda la logica de
mineria de datos vive aqui, lista para crecer hacia modelos de ML
serializados en `models/`.

Esquema de columnas esperado (basado en el dataset UCI "Forest Fires"):
    X, Y        -> coordenadas espaciales del parque
    month, day  -> temporalidad
    FFMC, DMC, DC, ISI -> indices del sistema FWI
    temp        -> temperatura (C)
    RH          -> humedad relativa (%)
    wind        -> velocidad del viento (km/h)
    rain        -> lluvia (mm/m2)
    area        -> superficie quemada (ha)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

MONTH_ORDER = [
    "jan", "feb", "mar", "apr", "may", "jun",
    "jul", "aug", "sep", "oct", "nov", "dec",
]
MONTH_LABELS = {
    "jan": "Ene", "feb": "Feb", "mar": "Mar", "apr": "Abr",
    "may": "May", "jun": "Jun", "jul": "Jul", "aug": "Ago",
    "sep": "Sep", "oct": "Oct", "nov": "Nov", "dec": "Dic",
}
DAY_ORDER = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
CLIMATE_COLUMNS = ["temp", "RH", "wind", "rain", "FFMC", "DMC", "DC", "ISI"]

RISK_BINS = [
    (0, 25, "Bajo"),
    (25, 50, "Moderado"),
    (50, 75, "Alto"),
    (75, 101, "Extremo"),
]


# --------------------------------------------------------------------------- #
# Generacion / carga de datos
# --------------------------------------------------------------------------- #
def synthetic_dataset(n_rows: int = 517, seed: int = 42) -> pd.DataFrame:
    """Dataset sintetico reproducible con la misma forma que UCI Forest Fires.

    Sirve como semilla del dashboard mientras no se cargue un CSV real,
    de modo que la UI y las APIs siempre tengan datos que mostrar.
    """
    rng = np.random.default_rng(seed)

    month = rng.choice(
        MONTH_ORDER,
        size=n_rows,
        p=[0.03, 0.03, 0.06, 0.05, 0.03, 0.10, 0.13, 0.25, 0.18, 0.07, 0.03, 0.04],
    )
    month_index = np.array([MONTH_ORDER.index(m) for m in month])
    # Estacionalidad: pico termico en verano (hemisferio norte).
    seasonal = np.sin((month_index - 2) / 12 * 2 * np.pi)

    temp = np.clip(18 + 9 * seasonal + rng.normal(0, 3.5, n_rows), 1, 45)
    rh = np.clip(58 - 22 * seasonal + rng.normal(0, 12, n_rows), 12, 100)
    wind = np.clip(rng.gamma(shape=4.0, scale=1.1, size=n_rows), 0.4, 22)
    rain = np.where(rng.random(n_rows) < 0.93, 0.0, rng.exponential(1.4, n_rows))

    ffmc = np.clip(88 + 0.35 * (temp - 18) - 0.06 * (rh - 50) - 4 * rain, 60, 99)
    dmc = np.clip(90 + seasonal * 20 + rng.normal(0, 30, n_rows), 5, 300)
    dc = np.clip(500 + 180 * seasonal + rng.normal(0, 120, n_rows), 10, 900)
    isi = np.clip(0.5 * wind + 0.12 * (ffmc - 80) + rng.normal(0, 1.6, n_rows), 0, 30)

    # La superficie quemada es fuertemente sesgada: mayoria de ceros y
    # una cola larga de eventos catastroficos.
    severity = 0.05 * temp + 0.08 * wind - 0.02 * rh + 0.06 * isi
    burned = rng.lognormal(mean=np.clip(severity, -1, 4), sigma=1.25)
    area = np.where(rng.random(n_rows) < 0.47, 0.0, burned).round(2)

    return pd.DataFrame(
        {
            "X": rng.integers(1, 10, n_rows),
            "Y": rng.integers(2, 10, n_rows),
            "month": month,
            "day": rng.choice(DAY_ORDER, n_rows),
            "FFMC": ffmc.round(1),
            "DMC": dmc.round(1),
            "DC": dc.round(1),
            "ISI": isi.round(1),
            "temp": temp.round(1),
            "RH": rh.round(0).astype(int),
            "wind": wind.round(1),
            "rain": rain.round(2),
            "area": area,
        }
    )


def _first_tabular_file(directory: Path) -> Path | None:
    """Devuelve el dataset mas reciente de un directorio, si existe."""
    if not directory.exists():
        return None
    candidates = [
        path
        for pattern in ("*.csv", "*.xlsx", "*.xls")
        for path in directory.glob(pattern)
        if not path.name.startswith(".")
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def read_tabular(path: Path) -> pd.DataFrame:
    """Lee un CSV o Excel detectando la extension."""
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path)


def load_dataset(config) -> tuple[pd.DataFrame, str]:
    """Estrategia de carga: processed -> raw -> sintetico.

    Returns:
        (dataframe, nombre_de_la_fuente)
    """
    for key in ("PROCESSED_DATA_DIR", "RAW_DATA_DIR"):
        path = _first_tabular_file(Path(config[key]))
        if path is None:
            continue
        try:
            df = read_tabular(path)
        except Exception:  # dataset corrupto o ilegible: seguimos buscando
            continue
        if not df.empty:
            return normalize_columns(df), path.name
    return synthetic_dataset(), "dataset sintetico (demo)"


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Homogeneiza nombres de columnas frecuentes en datasets de incendios."""
    aliases = {
        "temperature": "temp",
        "temperatura": "temp",
        "humidity": "RH",
        "humedad": "RH",
        "rh": "RH",
        "viento": "wind",
        "wind_speed": "wind",
        "lluvia": "rain",
        "precipitation": "rain",
        "burned_area": "area",
        "area_quemada": "area",
        "mes": "month",
        "dia": "day",
    }
    renamed = {c: aliases.get(str(c).strip().lower(), c) for c in df.columns}
    df = df.rename(columns=renamed)
    if "month" in df.columns:
        df["month"] = df["month"].astype(str).str.strip().str.lower().str[:3]
    return df


# --------------------------------------------------------------------------- #
# Filtrado e indice de riesgo
# --------------------------------------------------------------------------- #
def risk_index(df: pd.DataFrame) -> pd.Series:
    """Indice heuristico de riesgo 0-100 a partir de variables climaticas.

    Placeholder interpretable que sera reemplazado por el modelo de ML
    entrenado y persistido en `models/`.
    """
    if df.empty:
        return pd.Series(dtype=float)

    temp = _numeric(df, "temp", 20.0)
    wind = _numeric(df, "wind", 4.0)
    rh = _numeric(df, "RH", 50.0)
    rain = _numeric(df, "rain", 0.0)

    temp_n = (temp / 45).clip(0, 1)
    wind_n = (wind / 25).clip(0, 1)
    dry_n = (1 - rh / 100).clip(0, 1)
    wet_penalty = (rain / 6).clip(0, 1)

    score = (0.42 * temp_n + 0.28 * wind_n + 0.30 * dry_n) * (1 - 0.55 * wet_penalty)
    return (score * 100).round(1)


def _numeric(df: pd.DataFrame, column: str, default: float) -> pd.Series:
    """Serie numerica tolerante a columnas ausentes o con basura."""
    if column not in df.columns:
        return pd.Series(default, index=df.index, dtype=float)
    return pd.to_numeric(df[column], errors="coerce").fillna(default).astype(float)


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Aplica los filtros de variables climaticas enviados por la UI."""
    if df.empty:
        return df

    mask = pd.Series(True, index=df.index)
    numeric_ranges = {
        "temp": ("temp_min", "temp_max"),
        "wind": ("wind_min", "wind_max"),
        "RH": ("rh_min", "rh_max"),
    }
    for column, (min_key, max_key) in numeric_ranges.items():
        if column not in df.columns:
            continue
        series = pd.to_numeric(df[column], errors="coerce")
        if filters.get(min_key) is not None:
            mask &= series >= float(filters[min_key])
        if filters.get(max_key) is not None:
            mask &= series <= float(filters[max_key])

    months = filters.get("months")
    if months and "month" in df.columns:
        mask &= df["month"].isin(months)

    if filters.get("only_burned") and "area" in df.columns:
        mask &= pd.to_numeric(df["area"], errors="coerce").fillna(0) > 0

    return df[mask.fillna(False)]


# --------------------------------------------------------------------------- #
# KPIs y analisis exploratorio
# --------------------------------------------------------------------------- #
def _f(value, digits: int = 2) -> float:
    """Convierte numpy/NaN a float nativo serializable en JSON."""
    try:
        result = float(value)
    except (TypeError, ValueError):
        return 0.0
    if np.isnan(result) or np.isinf(result):
        return 0.0
    return round(result, digits)


def compute_kpis(df: pd.DataFrame) -> dict:
    """Tarjetas KPI del dashboard."""
    area = _numeric(df, "area", 0.0)
    risk = risk_index(df)
    burned = area[area > 0]

    return {
        "total_fires": int(len(df)),
        "active_events": int((area > 0).sum()),
        "total_area": _f(area.sum(), 1),
        "avg_area": _f(burned.mean() if not burned.empty else 0, 2),
        "max_area": _f(area.max() if not area.empty else 0, 1),
        "avg_risk": _f(risk.mean() if not risk.empty else 0, 1),
        "avg_temp": _f(_numeric(df, "temp", np.nan).mean(), 1),
        "avg_wind": _f(_numeric(df, "wind", np.nan).mean(), 1),
        "avg_humidity": _f(_numeric(df, "RH", np.nan).mean(), 1),
        "high_risk_share": _f((risk >= 50).mean() * 100 if not risk.empty else 0, 1),
    }


def monthly_series(df: pd.DataFrame) -> dict:
    """Serie temporal: numero de incendios y hectareas por mes."""
    empty = {"labels": [MONTH_LABELS[m] for m in MONTH_ORDER],
             "fires": [0] * 12, "area": [0] * 12}
    if "month" not in df.columns or df.empty:
        return empty

    grouped = (
        df.assign(_area=_numeric(df, "area", 0.0))
        .groupby("month")["_area"]
        .agg(["count", "sum"])
        .reindex(MONTH_ORDER)
        .fillna(0)
    )
    return {
        "labels": [MONTH_LABELS[m] for m in MONTH_ORDER],
        "fires": [int(v) for v in grouped["count"]],
        "area": [_f(v, 1) for v in grouped["sum"]],
    }


def risk_distribution(df: pd.DataFrame) -> dict:
    """Reparto de registros por franja de riesgo."""
    risk = risk_index(df)
    counts = [
        int(((risk >= low) & (risk < high)).sum()) if not risk.empty else 0
        for low, high, _ in RISK_BINS
    ]
    return {"labels": [label for _, _, label in RISK_BINS], "counts": counts}


def scatter_temp_area(df: pd.DataFrame, max_points: int = 320) -> dict:
    """Dispersion temperatura vs superficie quemada (escala log1p)."""
    if not {"temp", "area"}.issubset(df.columns) or df.empty:
        return {"points": []}

    subset = df[["temp", "area"]].apply(pd.to_numeric, errors="coerce").dropna()
    if subset.empty:
        return {"points": []}
    if len(subset) > max_points:
        subset = subset.sample(max_points, random_state=7)

    wind = _numeric(df, "wind", 0.0).reindex(subset.index).fillna(0)
    return {
        "points": [
            {"x": _f(t, 1), "y": _f(np.log1p(max(a, 0)), 3), "r": _f(3 + w / 4, 1)}
            for t, a, w in zip(subset["temp"], subset["area"], wind)
        ]
    }


def correlation_matrix(df: pd.DataFrame) -> dict:
    """Matriz de correlacion de Pearson entre variables climaticas."""
    columns = [c for c in CLIMATE_COLUMNS + ["area"] if c in df.columns]
    if len(columns) < 2 or df.empty:
        return {"labels": [], "matrix": []}

    numeric = df[columns].apply(pd.to_numeric, errors="coerce")
    corr = numeric.corr(numeric_only=True).fillna(0)
    if corr.empty:
        return {"labels": [], "matrix": []}

    return {
        "labels": [str(c) for c in corr.columns],
        "matrix": [[_f(v, 3) for v in row] for row in corr.to_numpy()],
    }


def wind_risk_profile(df: pd.DataFrame, bins: int = 8) -> dict:
    """Riesgo promedio por franja de velocidad de viento."""
    if "wind" not in df.columns or df.empty:
        return {"labels": [], "risk": []}

    frame = pd.DataFrame(
        {"wind": pd.to_numeric(df["wind"], errors="coerce"), "risk": risk_index(df)}
    ).dropna()
    if frame.empty or frame["wind"].nunique() < 2:
        return {"labels": [], "risk": []}

    frame["bucket"] = pd.cut(frame["wind"], bins=bins)
    grouped = frame.groupby("bucket", observed=True)["risk"].mean()
    return {
        "labels": [f"{i.left:.0f}-{i.right:.0f}" for i in grouped.index],
        "risk": [_f(v, 1) for v in grouped.to_numpy()],
    }


def build_analysis(df: pd.DataFrame) -> dict:
    """Payload completo para el contenedor de visualizaciones."""
    return {
        "monthly": monthly_series(df),
        "risk_distribution": risk_distribution(df),
        "scatter": scatter_temp_area(df),
        "correlation": correlation_matrix(df),
        "wind_profile": wind_risk_profile(df),
    }


def profile_dataframe(df: pd.DataFrame, preview_rows: int = 8) -> dict:
    """Perfilado rapido de un dataset recien cargado."""
    numeric = df.select_dtypes(include="number")
    return {
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "column_names": [str(c) for c in df.columns],
        "dtypes": {str(c): str(t) for c, t in df.dtypes.items()},
        "missing": {str(c): int(v) for c, v in df.isna().sum().items()},
        "missing_total": int(df.isna().sum().sum()),
        "duplicates": int(df.duplicated().sum()),
        "numeric_summary": {
            str(c): {
                "mean": _f(numeric[c].mean()),
                "std": _f(numeric[c].std()),
                "min": _f(numeric[c].min()),
                "max": _f(numeric[c].max()),
            }
            for c in numeric.columns
        },
        "preview": df.head(preview_rows).fillna("").astype(str).to_dict(orient="records"),
    }
