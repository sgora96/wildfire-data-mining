"""Blueprint del entregable R2 - Etapa 2: Calidad de Datos.

Perfilamiento, evaluacion de las 6 dimensiones de calidad, inventario de
problemas y plan de tratamiento sobre el dataset consolidado de la Etapa 1.
Los datos que consumen estas plantillas se generan con
`scripts/data_quality_r2.py` (no se calculan en la request, se leen de
`data/processed/calidad_r2_resumen.json`).
"""

from __future__ import annotations

import json
from pathlib import Path

from flask import Blueprint, current_app, render_template

etapa2_bp = Blueprint("etapa2", __name__, url_prefix="/etapa-2")

SUBMENU = [
    {"slug": "descripcion", "label": "1. Descripción y requisitos de calidad"},
    {"slug": "perfilamiento", "label": "2. Perfilamiento de datos"},
    {"slug": "dimensiones", "label": "3. Dimensiones e inventario de problemas"},
    {"slug": "tratamiento", "label": "4. Integración, homologación y tratamiento"},
]


def _resumen() -> dict:
    """Lee el resumen generado por scripts/data_quality_r2.py.

    Devuelve un dict vacio (las plantillas deben manejarlo) si todavia no se
    ha corrido el script en este checkout.
    """
    path = Path(current_app.config["PROCESSED_DATA_DIR"]) / "calidad_r2_resumen.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _render(slug: str, **extra):
    return render_template(f"etapa2/{slug}.html", resumen=_resumen(), **extra)


@etapa2_bp.route("/")
@etapa2_bp.route("/descripcion/")
def descripcion():
    return _render("descripcion")


@etapa2_bp.route("/perfilamiento/")
def perfilamiento():
    return _render("perfilamiento")


@etapa2_bp.route("/dimensiones/")
def dimensiones():
    return _render("dimensiones")


@etapa2_bp.route("/tratamiento/")
def tratamiento():
    return _render("tratamiento")
