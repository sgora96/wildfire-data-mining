"""Blueprint de la Etapa 4: descubrimiento de conocimiento evidente con Power BI.
"""
from __future__ import annotations

from flask import Blueprint, render_template

etapa4_bp = Blueprint("etapa4", __name__, url_prefix="/etapa-4")

SUBMENU = [
    {"slug": "conocimiento", "label": "1. Conocimiento evidente"},
]


@etapa4_bp.route("/")
@etapa4_bp.route("/conocimiento/")
def conocimiento():
    return render_template("etapa4/conocimiento.html")