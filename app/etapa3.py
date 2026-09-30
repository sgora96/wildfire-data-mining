"""Blueprint de la Etapa 3: ETL y limpieza de datos con SSIS.
"""
from __future__ import annotations

import json
from pathlib import Path

from flask import Blueprint, current_app, render_template

etapa3_bp = Blueprint("etapa3", __name__, url_prefix="/etapa-3")

SUBMENU = [
    {"slug": "resultados", "label": "1. Resultados de las 3 iteraciones"},
    {"slug": "recursos", "label": "2. Informe tecnico y video"},
]


def _resumen() -> dict:
    path = Path(current_app.config["PROCESSED_DATA_DIR"]) / "calidad_r3_resumen.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _render(slug: str, **extra):
    return render_template(f"etapa3/{slug}.html", resumen=_resumen(), **extra)


@etapa3_bp.route("/")
@etapa3_bp.route("/resultados/")
def resultados():
    return _render("resultados")


@etapa3_bp.route("/recursos/")
def recursos():
    return _render("recursos")
