"""Blueprint del entregable R1 - Etapa 1: Del problema a los datos.

Cada una de las 8 vistas corresponde a un submenu obligatorio del
entregable (ver docs/R1MineriaDatos.pdf y docs/entregable-semana-1.txt).
El contenido de cada pagina vive en su propia plantilla bajo
`templates/etapa1/`, de modo que cada integrante del grupo pueda
trabajar su seccion sin tocar las demas ni las rutas compartidas.
"""

from __future__ import annotations

import json
from pathlib import Path

from flask import Blueprint, current_app, render_template

etapa1_bp = Blueprint("etapa1", __name__, url_prefix="/etapa-1")

# Orden y metadatos del submenu obligatorio (mismo orden en las 8 fuentes:
# PDF, txt del entregable y este blueprint).
SUBMENU = [
    {"slug": "problema", "label": "1. Problema y contexto"},
    {"slug": "preguntas", "label": "2. Pregunta principal y secundarias"},
    {"slug": "necesidades", "label": "3. Necesidades de informacion"},
    {"slug": "fuentes", "label": "4. Fuentes de datos"},
    {"slug": "dataset", "label": "5. Dataset"},
    {"slug": "diccionario", "label": "6. Diccionario de datos"},
    {"slug": "calidad", "label": "7. Calidad inicial de los datos"},
    {"slug": "limitaciones", "label": "8. Limitaciones y consideraciones"},
]


# Diccionario de datos del dataset consolidado IDEAM (data/processed/
# incendios_ideam_2010_2024.csv e incendios_ideam_cundinamarca_2010_2024.csv).
# Generado a partir del esquema oficial "BD_ICV" del IDEAM
# (ver scripts/Build-IdeamDataset.ps1). Revisar y ajustar la columna
# "descripcion" si al inspeccionar mas filas se identifica un significado
# mas preciso: varias etiquetas originales del IDEAM son ambiguas.
DICCIONARIO = [
    {"campo": "ANIO", "descripcion": "Ano en que ocurrio o se reporto el evento.", "tipo": "Numerica discreta", "dominio": "2010-2024", "fuente": "IDEAM", "ejemplo": "2023"},
    {"campo": "MES", "descripcion": "Mes de ocurrencia, en texto.", "tipo": "Categorica ordinal", "dominio": "Enero...Diciembre", "fuente": "IDEAM", "ejemplo": "Enero"},
    {"campo": "FECHA_REGISTRO", "descripcion": "Fecha del evento. Ojo: el IDEAM llama a este campo \"DIA\" pero almacena la fecha completa (no solo el numero del dia); se normalizo a formato ISO.", "tipo": "Temporal (fecha)", "dominio": "2010-01-01 .. 2024-12-31", "fuente": "IDEAM", "ejemplo": "2023-08-14"},
    {"campo": "DEPARTAMENTO", "descripcion": "Departamento colombiano donde ocurrio el incendio.", "tipo": "Categorica nominal / Geografica", "dominio": "32 departamentos + Bogota D.C.", "fuente": "IDEAM (Divipola)", "ejemplo": "Cundinamarca"},
    {"campo": "MUNICIPIO", "descripcion": "Municipio donde ocurrio el incendio.", "tipo": "Categorica nominal / Geografica", "dominio": "Municipios de Colombia", "fuente": "IDEAM (Divipola)", "ejemplo": "Facatativa"},
    {"campo": "VEREDA_CORREGIMIENTO", "descripcion": "Vereda o corregimiento del evento, cuando el reporte lo incluye.", "tipo": "Categorica nominal", "dominio": "Texto libre", "fuente": "IDEAM", "ejemplo": "El Rosal"},
    {"campo": "PREDIO_BARRIO", "descripcion": "Predio, barrio o area de manejo especial asociada.", "tipo": "Categorica nominal", "dominio": "Texto libre", "fuente": "IDEAM", "ejemplo": "Vereda La Esperanza"},
    {"campo": "AREA_PROTEGIDA_NACIONAL", "descripcion": "Indica si el evento ocurrio dentro de un area protegida de orden nacional.", "tipo": "Categorica nominal (Si/No)", "dominio": "S, N, NA", "fuente": "IDEAM", "ejemplo": "N"},
    {"campo": "LATITUD", "descripcion": "Latitud del evento. Formato original inconsistente (grados.minutos.segundos como texto); requiere limpieza antes de usarse como coordenada numerica.", "tipo": "Geografica", "dominio": "Texto tipo 06.08.39,5", "fuente": "IDEAM", "ejemplo": "06.08.39,5"},
    {"campo": "LONGITUD", "descripcion": "Longitud del evento. Mismo problema de formato que LATITUD.", "tipo": "Geografica", "dominio": "Texto tipo 75.34.38,0", "fuente": "IDEAM", "ejemplo": "75.34.38,0"},
    {"campo": "ELEVACION_MSNM", "descripcion": "Elevacion del sitio sobre el nivel del mar.", "tipo": "Numerica continua", "dominio": "metros s.n.m.", "fuente": "IDEAM", "ejemplo": "2600"},
    {"campo": "AREA_COPA_HA", "descripcion": "Hectareas afectadas por incendio de copa.", "tipo": "Numerica continua", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": "3.5"},
    {"campo": "AREA_SUPERFICIAL_HA", "descripcion": "Hectareas afectadas por incendio superficial.", "tipo": "Numerica continua", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": "5"},
    {"campo": "AREA_SUBTERRANEO_HA", "descripcion": "Hectareas afectadas por incendio subterraneo.", "tipo": "Numerica continua", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": "0"},
    {"campo": "AREA_MIXTO_HA", "descripcion": "Hectareas afectadas por incendio de tipo mixto.", "tipo": "Numerica continua", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": "1.2"},
    {"campo": "AREA_OTRO_TIPO_HA", "descripcion": "Hectareas afectadas por un tipo de incendio no clasificado en las categorias anteriores.", "tipo": "Numerica continua", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": "0.8"},
    {"campo": "CAUSA_QUEMA_FUERA_CONTROL", "descripcion": "Marca si la causa reportada fue una quema agricola/controlada que se salio de control.", "tipo": "Categorica nominal", "dominio": "Marcador de causa (X / vacio)", "fuente": "IDEAM", "ejemplo": "X"},
    {"campo": "CAUSA_DESCUIDO_NEGLIGENCIA", "descripcion": "Marca si la causa reportada fue descuido o negligencia.", "tipo": "Categorica nominal", "dominio": "Marcador de causa (X / vacio)", "fuente": "IDEAM", "ejemplo": ""},
    {"campo": "CAUSA_INTENCIONAL", "descripcion": "Marca si la causa reportada fue intencional.", "tipo": "Categorica nominal", "dominio": "Marcador de causa (I / vacio)", "fuente": "IDEAM", "ejemplo": "I"},
    {"campo": "CAUSA_ACCIDENTAL", "descripcion": "Marca si la causa reportada fue accidental.", "tipo": "Categorica nominal", "dominio": "Marcador de causa (X / vacio)", "fuente": "IDEAM", "ejemplo": ""},
    {"campo": "CAUSA_REACTIVACION_FOCOS", "descripcion": "Marca si el evento fue una reactivacion de un foco previo.", "tipo": "Categorica nominal", "dominio": "Marcador de causa (X / vacio)", "fuente": "IDEAM", "ejemplo": ""},
    {"campo": "CAUSA_OTRA", "descripcion": "Marca si la causa reportada no encaja en las categorias anteriores.", "tipo": "Categorica nominal", "dominio": "Marcador de causa (O / vacio)", "fuente": "IDEAM", "ejemplo": "O"},
    {"campo": "COB_BOSQUE_NATURAL_DENSO", "descripcion": "Hectareas de bosque natural denso afectadas.", "tipo": "Numerica continua", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": ""},
    {"campo": "COB_BOSQUE_INTERVENIDO", "descripcion": "Hectareas de bosque intervenido afectadas.", "tipo": "Numerica continua", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": ""},
    {"campo": "COB_BOSQUE_PLANTADO", "descripcion": "Hectareas de bosque plantado afectadas.", "tipo": "Numerica continua", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": ""},
    {"campo": "COB_BOSQUE_SECO", "descripcion": "Hectareas de bosque seco afectadas.", "tipo": "Numerica continua", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": ""},
    {"campo": "COB_CULTIVOS", "descripcion": "Hectareas de cultivos afectadas.", "tipo": "Numerica continua", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": ""},
    {"campo": "COB_PARAMOS", "descripcion": "Hectareas de paramo afectadas.", "tipo": "Numerica continua", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": ""},
    {"campo": "COB_SABANAS_PASTIZALES", "descripcion": "Hectareas de sabanas o pastizales afectadas.", "tipo": "Numerica continua", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": ""},
    {"campo": "COB_PASTOS_MANEJADOS", "descripcion": "Hectareas de pastos manejados afectadas.", "tipo": "Numerica continua", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": ""},
    {"campo": "COB_RASTROJO", "descripcion": "Hectareas de rastrojo afectadas.", "tipo": "Numerica continua", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": ""},
    {"campo": "COB_VEGETACION_SECA", "descripcion": "Hectareas de vegetacion seca afectadas.", "tipo": "Numerica continua", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": ""},
    {"campo": "COB_COBERTURA_SIN_DETERMINAR", "descripcion": "Hectareas afectadas cuya cobertura no fue determinada.", "tipo": "Numerica continua", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": ""},
    {"campo": "AREA_TOTAL_HA", "descripcion": "Area total afectada por el evento (variable objetivo para analisis de severidad).", "tipo": "Numerica continua", "dominio": "hectareas (ha), >= 0", "fuente": "IDEAM", "ejemplo": "15"},
    {"campo": "ENTIDAD_REPORTA", "descripcion": "Entidad que reporto el evento. Solo presente en la hoja 2024 (campo nuevo en la plantilla de ese ano); vacio en 2010-2023.", "tipo": "Categorica nominal", "dominio": "Ej. UNGRD", "fuente": "IDEAM", "ejemplo": "UNGRD"},
    {"campo": "FUENTE_HOJA", "descripcion": "Hoja/archivo original de donde proviene el registro (trazabilidad de la consolidacion).", "tipo": "Categorica nominal", "dominio": "BD_ICV_2010_2020, BD_ICV_2021, BD_ICV_2022, BD_ICV_2023, BD_ICV_2024", "fuente": "Generado en la consolidacion", "ejemplo": "BD_ICV_2023"},
]


def _quality_summary() -> dict:
    """Lee el diagnostico de calidad generado por scripts/Build-IdeamDataset.ps1.

    Devuelve un dict vacio (la plantilla debe manejarlo) si el dataset
    procesado todavia no existe en este checkout.
    """
    path = Path(current_app.config["PROCESSED_DATA_DIR"]) / "calidad_resumen.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _render(slug: str, **extra):
    return render_template(
        f"etapa1/{slug}.html",
        submenu=SUBMENU,
        active_slug=slug,
        **extra,
    )


@etapa1_bp.route("/")
@etapa1_bp.route("/problema")
def problema():
    return _render("problema")


@etapa1_bp.route("/preguntas")
def preguntas():
    return _render("preguntas")


@etapa1_bp.route("/necesidades")
def necesidades():
    return _render("necesidades")


@etapa1_bp.route("/fuentes")
def fuentes():
    return _render("fuentes")


@etapa1_bp.route("/dataset")
def dataset():
    return _render("dataset", calidad=_quality_summary())


@etapa1_bp.route("/diccionario")
def diccionario():
    return _render("diccionario", diccionario=DICCIONARIO)


@etapa1_bp.route("/calidad")
def calidad():
    return _render("calidad", calidad=_quality_summary())


@etapa1_bp.route("/limitaciones")
def limitaciones():
    return _render("limitaciones")
