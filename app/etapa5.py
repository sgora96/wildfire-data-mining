"""Blueprint de la Etapa 5: analisis multidimensional con modelo estrella.
"""
from __future__ import annotations

import json

from flask import Blueprint, jsonify, render_template, request

from app.olap import ErrorConsulta, ejecutar

etapa5_bp = Blueprint("etapa5", __name__, url_prefix="/etapa-5")
olap_api_bp = Blueprint("olap_api", __name__, url_prefix="/api/olap")

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


@olap_api_bp.route("/consulta")
def consulta():
    texto = request.args.get("spec")
    if not texto:
        return jsonify(ok=False, error="Falta el parametro 'spec'."), 400
    try:
        return jsonify(ejecutar(json.loads(texto)))
    except json.JSONDecodeError:
        return jsonify(ok=False, error="'spec' no es un JSON valido."), 400
    except ErrorConsulta as error:
        return jsonify(ok=False, error=str(error)), 400