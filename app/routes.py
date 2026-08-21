"""Rutas del dashboard y endpoints JSON del proyecto.

Dos blueprints:
    * `main_bp` -> vistas HTML renderizadas con Jinja.
    * `api_bp`  -> API JSON consumida por `static/js/main.js`
                   (montada bajo el prefijo /api en el factory).
"""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, current_app, jsonify, render_template, request
from werkzeug.utils import secure_filename

from app import services

main_bp = Blueprint("main", __name__)
api_bp = Blueprint("api", __name__)


# --------------------------------------------------------------------------- #
# Utilidades compartidas
# --------------------------------------------------------------------------- #
def _dataset():
    """Carga el dataset activo respetando la jerarquia processed -> raw -> demo."""
    return services.load_dataset(current_app.config)


def _filters_from_request() -> dict:
    """Traduce los query params del dashboard a un dict de filtros."""

    def number(key):
        raw = request.args.get(key)
        if raw in (None, "", "null"):
            return None
        try:
            return float(raw)
        except ValueError:
            return None

    months = request.args.getlist("month") or None
    if months:
        months = [m.strip().lower()[:3] for m in months]

    return {
        "temp_min": number("temp_min"),
        "temp_max": number("temp_max"),
        "wind_min": number("wind_min"),
        "wind_max": number("wind_max"),
        "rh_min": number("rh_min"),
        "rh_max": number("rh_max"),
        "months": months,
        "only_burned": request.args.get("only_burned") in ("1", "true", "on", "yes"),
    }


def _allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


# --------------------------------------------------------------------------- #
# Vistas
# --------------------------------------------------------------------------- #
@main_bp.route("/")
def index():
    """Dashboard principal."""
    df, source = _dataset()
    return render_template(
        "index.html",
        kpis=services.compute_kpis(df),
        dataset_source=source,
        month_labels=services.MONTH_LABELS,
        month_order=services.MONTH_ORDER,
    )


# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #
@api_bp.get("/health")
def health():
    """Sonda de disponibilidad para monitoreo y CI."""
    return jsonify(ok=True, status="healthy", service=current_app.config["PROJECT_NAME"])


@api_bp.get("/meta")
def meta():
    """Metadatos del dataset activo: fuente, dimensiones y columnas."""
    df, source = _dataset()
    return jsonify(
        ok=True,
        source=source,
        rows=int(len(df)),
        columns=[str(c) for c in df.columns],
        months=[m for m in services.MONTH_ORDER if m in set(df.get("month", []))],
        climate_columns=[c for c in services.CLIMATE_COLUMNS if c in df.columns],
    )


@api_bp.get("/kpis")
def kpis():
    """KPIs recalculados sobre el subconjunto filtrado."""
    df, source = _dataset()
    filtered = services.apply_filters(df, _filters_from_request())
    return jsonify(
        ok=True,
        source=source,
        matched=int(len(filtered)),
        total=int(len(df)),
        kpis=services.compute_kpis(filtered),
    )


@api_bp.get("/analysis")
def analysis():
    """Series y matrices listas para graficar en el frontend."""
    df, source = _dataset()
    filtered = services.apply_filters(df, _filters_from_request())
    return jsonify(
        ok=True,
        source=source,
        matched=int(len(filtered)),
        charts=services.build_analysis(filtered),
    )


@api_bp.get("/records")
def records():
    """Muestra paginada de registros para la tabla de exploracion."""
    df, _ = _dataset()
    filtered = services.apply_filters(df, _filters_from_request())

    try:
        limit = max(1, min(int(request.args.get("limit", 25)), 500))
        offset = max(0, int(request.args.get("offset", 0)))
    except ValueError:
        limit, offset = 25, 0

    page = filtered.iloc[offset : offset + limit].copy()
    if not page.empty:
        page["risk"] = services.risk_index(page)

    return jsonify(
        ok=True,
        total=int(len(filtered)),
        limit=limit,
        offset=offset,
        columns=[str(c) for c in page.columns],
        rows=page.fillna("").astype(str).to_dict(orient="records"),
    )


@api_bp.get("/datasets")
def datasets():
    """Inventario de datasets disponibles en data/raw y data/processed."""
    inventory = []
    for stage in ("RAW_DATA_DIR", "PROCESSED_DATA_DIR"):
        directory = Path(current_app.config[stage])
        for path in sorted(directory.glob("*")):
            if path.name.startswith(".") or not path.is_file():
                continue
            inventory.append(
                {
                    "name": path.name,
                    "stage": "raw" if stage == "RAW_DATA_DIR" else "processed",
                    "size_kb": round(path.stat().st_size / 1024, 1),
                }
            )
    return jsonify(ok=True, datasets=inventory)


@api_bp.post("/upload")
def upload():
    """Carga un CSV/Excel a data/raw y devuelve su perfilado inicial."""
    file = request.files.get("file")
    if file is None or not file.filename:
        return jsonify(ok=False, error="No se recibio ningun archivo"), 400

    if not _allowed_file(file.filename):
        permitted = ", ".join(sorted(current_app.config["ALLOWED_EXTENSIONS"]))
        return jsonify(ok=False, error=f"Formato no permitido. Usa: {permitted}"), 400

    filename = secure_filename(file.filename)
    destination = Path(current_app.config["UPLOAD_FOLDER"]) / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    file.save(destination)

    try:
        df = services.normalize_columns(services.read_tabular(destination))
    except Exception as exc:
        destination.unlink(missing_ok=True)
        return jsonify(ok=False, error=f"No se pudo leer el archivo: {exc}"), 422

    if df.empty:
        destination.unlink(missing_ok=True)
        return jsonify(ok=False, error="El dataset no contiene filas"), 422

    return jsonify(
        ok=True,
        filename=filename,
        stored_in="data/raw",
        profile=services.profile_dataframe(df),
        kpis=services.compute_kpis(df),
    )


@api_bp.post("/predict")
def predict():
    """Scoring de riesgo para un escenario climatico puntual.

    Hoy usa la heuristica de `services.risk_index`. Cuando exista un
    modelo entrenado en `models/`, basta con sustituir esta llamada por
    `joblib.load(...).predict(features)` sin tocar el frontend.
    """
    payload = request.get_json(silent=True) or {}
    try:
        scenario = {
            "temp": float(payload.get("temp", 20)),
            "wind": float(payload.get("wind", 4)),
            "RH": float(payload.get("RH", 50)),
            "rain": float(payload.get("rain", 0)),
        }
    except (TypeError, ValueError):
        return jsonify(ok=False, error="Valores climaticos invalidos"), 400

    import pandas as pd

    score = float(services.risk_index(pd.DataFrame([scenario])).iloc[0])
    level = next(
        label for low, high, label in services.RISK_BINS if low <= score < high
    )
    return jsonify(ok=True, scenario=scenario, risk_score=score, risk_level=level)
