"""Blueprint de la Etapa 5: analisis multidimensional con modelo estrella.
"""
from __future__ import annotations

from flask import Blueprint, render_template

etapa5_bp = Blueprint("etapa5", __name__, url_prefix="/etapa-5")

SUBMENU = [
    {"slug": "multidimensional", "label": "Analisis multidimensional"},
    {"slug": "vista1", "label": "Vista 1 - Territorio y tiempo"},
    {"slug": "vista2", "label": "Vista 2 - Tiempo y tamano"},
    {"slug": "vista3", "label": "Vista 3 - Cobertura y territorio"},
    {"slug": "vista4", "label": "Vista 4 - Causa y tamano"},
]


@etapa5_bp.route("/")
def multidimensional():
    return render_template("etapa5/multidimensional.html")


@etapa5_bp.route("/vista-1/")
def vista1():
    return render_template("etapa5/vista1.html")


@etapa5_bp.route("/vista-2/")
def vista2():
    return render_template("etapa5/vista2.html")


@etapa5_bp.route("/vista-3/")
def vista3():
    return render_template("etapa5/vista3.html")


@etapa5_bp.route("/vista-4/")
def vista4():
    return render_template("etapa5/vista4.html")