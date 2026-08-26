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
    {"campo": "MES", "descripcion": "Mes de ocurrencia, en texto. Sin normalizar: segun la hoja de origen aparece en MAYUSCULAS o Capitalizado, e incluye el valor \"SIN REPORTE\" cuando no se registro el mes.", "tipo": "Categorica ordinal", "dominio": "ENERO..DICIEMBRE (mayusculas o capitalizado, inconsistente) + SIN REPORTE", "fuente": "IDEAM", "ejemplo": "ENERO"},
    {"campo": "FECHA_REGISTRO", "descripcion": "Fecha del evento. Ojo: el IDEAM llama a este campo \"DIA\" pero almacena la fecha completa (no solo el numero del dia); se normalizo a formato ISO.", "tipo": "Temporal (fecha)", "dominio": "2010-01-01 .. 2024-12-31", "fuente": "IDEAM", "ejemplo": "2023-08-14"},
    {"campo": "DEPARTAMENTO", "descripcion": "Departamento colombiano donde ocurrio el incendio. Sin normalizar: el mismo departamento aparece escrito de formas distintas segun la hoja de origen (con/sin tilde, MAYUSCULAS/Capitalizado, p.ej. \"BOLIVAR\", \"BOLÍVAR\" y \"BOLíVAR\" coexisten), por lo que hay ~46 valores de texto distintos para los 32 departamentos + Bogota D.C. reales (ver calidad_resumen.json: departamentos_distintos).", "tipo": "Categorica nominal / Geografica", "dominio": "32 departamentos + Bogota D.C. (en ~46 variantes de texto sin normalizar)", "fuente": "IDEAM (Divipola)", "ejemplo": "CUNDINAMARCA"},
    {"campo": "MUNICIPIO", "descripcion": "Municipio donde ocurrio el incendio. Mismo problema de normalizacion que DEPARTAMENTO (tildes y mayusculas inconsistentes entre hojas).", "tipo": "Categorica nominal / Geografica", "dominio": "~1.997 valores de texto distintos (municipios de Colombia, sin normalizar)", "fuente": "IDEAM (Divipola)", "ejemplo": "Facatativa"},
    {"campo": "VEREDA_CORREGIMIENTO", "descripcion": "Vereda o corregimiento del evento, cuando el reporte lo incluye.", "tipo": "Categorica nominal", "dominio": "Texto libre", "fuente": "IDEAM", "ejemplo": "El Rosal"},
    {"campo": "PREDIO_BARRIO", "descripcion": "Predio, barrio o area de manejo especial asociada.", "tipo": "Categorica nominal", "dominio": "Texto libre", "fuente": "IDEAM", "ejemplo": "Vereda La Esperanza"},
    {"campo": "AREA_PROTEGIDA_NACIONAL", "descripcion": "Nombre del area protegida de orden nacional (PNN, santuario de flora y fauna, via parque, etc.) donde ocurrio el evento, cuando aplica. OJO: pese al nombre de la columna NO es un indicador Si/No, es texto libre con el nombre del area; vacio cuando el evento no ocurrio dentro de una. Solo viene diligenciado en las hojas 2010-2020 y 2021 (580 de 40.010 registros, ~1.4%).", "tipo": "Categorica nominal", "dominio": "Nombres de areas protegidas de Colombia (ej. Parque Nacional Natural Chingaza) o vacio", "fuente": "IDEAM", "ejemplo": "Parque Nacional Natural Chingaza"},
    {"campo": "LATITUD", "descripcion": "Latitud del evento. Formato original inconsistente (grados.minutos.segundos como texto, algunos sin segundos); requiere limpieza antes de usarse como coordenada numerica. Solo diligenciada en la hoja 2010-2020 (91.6% de nulos en el total del dataset).", "tipo": "Geografica", "dominio": "Texto tipo 06.08.39,5", "fuente": "IDEAM", "ejemplo": "06.08.39,5"},
    {"campo": "LONGITUD", "descripcion": "Longitud del evento. Mismo problema de formato y misma cobertura (solo hoja 2010-2020) que LATITUD.", "tipo": "Geografica", "dominio": "Texto tipo 75.34.38,0", "fuente": "IDEAM", "ejemplo": "75.34.38,0"},
    {"campo": "ELEVACION_MSNM", "descripcion": "Elevacion del sitio sobre el nivel del mar. Solo diligenciada en la hoja 2010-2020 (97.2% de nulos en el total); incluye al menos un valor -1 que probablemente es un codigo de error/dato no disponible, no una elevacion real.", "tipo": "Numerica continua", "dominio": "metros s.n.m., -1 a 5.788 en los datos observados (revisar el -1 como posible valor invalido)", "fuente": "IDEAM", "ejemplo": "2600"},
    {"campo": "AREA_COPA_HA", "descripcion": "Hectareas afectadas por incendio de copa. OJO: la columna mezcla numeros con texto residual (marcadores de tipo de incendio como \"C\", \"X\", nombres de ciudad como \"Bogota\"); requiere limpieza para tratarla como numerica. Casi exclusiva de la hoja 2010-2020 (98% de nulos en el total).", "tipo": "Numerica continua (sucia: mezcla texto)", "dominio": "hectareas (ha) o texto/marcador segun el registro", "fuente": "IDEAM", "ejemplo": "3.5"},
    {"campo": "AREA_SUPERFICIAL_HA", "descripcion": "Hectareas afectadas por incendio superficial. Mismo problema de mezcla numero/texto que AREA_COPA_HA (valores como \"SUP\", \"X\", \"No selecionado\"). Casi exclusiva de la hoja 2010-2020 (81.8% de nulos en el total).", "tipo": "Numerica continua (sucia: mezcla texto)", "dominio": "hectareas (ha) o texto/marcador segun el registro", "fuente": "IDEAM", "ejemplo": "5"},
    {"campo": "AREA_SUBTERRANEO_HA", "descripcion": "Hectareas afectadas por incendio subterraneo. Extremadamente escasa (99.7% de nulos): los pocos valores no vacios observados son marcadores de texto (\"SUB\", \"X\"), no numeros.", "tipo": "Numerica continua (sucia: mezcla texto)", "dominio": "hectareas (ha) o texto/marcador segun el registro", "fuente": "IDEAM", "ejemplo": "0"},
    {"campo": "AREA_MIXTO_HA", "descripcion": "Hectareas afectadas por incendio de tipo mixto. Mismo problema de mezcla numero/texto (\"MX\", \"X\", \"SI\"). Casi exclusiva de la hoja 2010-2020 (99.1% de nulos en el total).", "tipo": "Numerica continua (sucia: mezcla texto)", "dominio": "hectareas (ha) o texto/marcador segun el registro", "fuente": "IDEAM", "ejemplo": "1.2"},
    {"campo": "AREA_OTRO_TIPO_HA", "descripcion": "Hectareas afectadas por un tipo de incendio no clasificado en las categorias anteriores. Mismo problema de mezcla numero/texto (\"O\", \"X\", \"Otros\"). Presente en las hojas 2010-2020 y 2022 (96.9% de nulos en el total).", "tipo": "Numerica continua (sucia: mezcla texto)", "dominio": "hectareas (ha) o texto/marcador segun el registro", "fuente": "IDEAM", "ejemplo": "0.8"},
    {"campo": "CAUSA_QUEMA_FUERA_CONTROL", "descripcion": "Marca si la causa reportada fue una quema agricola/controlada que se salio de control. El marcador NO es homogeneo: segun el registro aparece como letra (\"Q\"), \"X\"/\"x\", \"1\"/\"0\", \"SI\", o el texto completo \"Quemas fuera de control\". Casi exclusiva de la hoja 2010-2020 (95.8% de nulos en el total; practicamente ausente 2022-2024).", "tipo": "Categorica nominal", "dominio": "Q, X, x, 1, 0, SI, \"Quemas fuera de control\", o vacio", "fuente": "IDEAM", "ejemplo": "X"},
    {"campo": "CAUSA_DESCUIDO_NEGLIGENCIA", "descripcion": "Marca si la causa reportada fue descuido o negligencia. Mismo problema de marcador no homogeneo que CAUSA_QUEMA_FUERA_CONTROL. Casi exclusiva de la hoja 2010-2020 (98.8% de nulos en el total).", "tipo": "Categorica nominal", "dominio": "D, X, x, 1, 0, \"Descuido y negligencia\", o vacio", "fuente": "IDEAM", "ejemplo": "D"},
    {"campo": "CAUSA_INTENCIONAL", "descripcion": "Marca si la causa reportada fue intencional. Mismo problema de marcador no homogeneo. Casi exclusiva de la hoja 2010-2020 (97.3% de nulos en el total).", "tipo": "Categorica nominal", "dominio": "I, X, x, 1, 0, SI, o vacio", "fuente": "IDEAM", "ejemplo": "I"},
    {"campo": "CAUSA_ACCIDENTAL", "descripcion": "Marca si la causa reportada fue accidental. Mismo problema de marcador no homogeneo. Extremadamente escasa (99.5% de nulos en el total).", "tipo": "Categorica nominal", "dominio": "A, X, x, 1, SI, \"Accidental\", o vacio", "fuente": "IDEAM", "ejemplo": "A"},
    {"campo": "CAUSA_REACTIVACION_FOCOS", "descripcion": "Marca si el evento fue una reactivacion de un foco previo. Mismo problema de marcador no homogeneo. Es la causa mas escasa de todas (99.9% de nulos en el total).", "tipo": "Categorica nominal", "dominio": "R, X, x, 1, 0, \"Reactivacion de focos\", o vacio", "fuente": "IDEAM", "ejemplo": "R"},
    {"campo": "CAUSA_OTRA", "descripcion": "Marca si la causa reportada no encaja en las categorias anteriores. Mismo problema de marcador no homogeneo; incluye ademas valores libres como \"rayo seco\" o \"CONTROLADA\". Presente en las hojas 2010-2020 y 2022 (97.3% de nulos en el total).", "tipo": "Categorica nominal", "dominio": "O, X, x, 1, 0, texto libre (ej. \"rayo seco\"), o vacio", "fuente": "IDEAM", "ejemplo": "O"},
    {"campo": "COB_BOSQUE_NATURAL_DENSO", "descripcion": "Hectareas de bosque natural denso afectadas. Mayoritariamente numerica, pero ~3.7% de los valores no vacios son texto residual (\"X\", \"SD\", nombres de cobertura sueltos como \"Manglar\").", "tipo": "Numerica continua (residuo de texto)", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": "5"},
    {"campo": "COB_BOSQUE_INTERVENIDO", "descripcion": "Hectareas de bosque intervenido afectadas. Mayoritariamente numerica, ~3.2% de los valores no vacios son marcadores de texto (\"X\"/\"x\").", "tipo": "Numerica continua (residuo de texto)", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": "1"},
    {"campo": "COB_BOSQUE_PLANTADO", "descripcion": "Hectareas de bosque plantado afectadas. Mayoritariamente numerica, ~5.1% de los valores no vacios son marcadores de texto (\"X\"/\"x\").", "tipo": "Numerica continua (residuo de texto)", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": "2"},
    {"campo": "COB_BOSQUE_SECO", "descripcion": "Hectareas de bosque seco afectadas. Mayoritariamente numerica, ~3.7% de los valores no vacios son marcadores de texto (\"X\"/\"x\").", "tipo": "Numerica continua (residuo de texto)", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": "2"},
    {"campo": "COB_CULTIVOS", "descripcion": "Hectareas de cultivos afectadas. Mayoritariamente numerica, ~4.9% de los valores no vacios son texto residual (\"X\", \"SD\").", "tipo": "Numerica continua (residuo de texto)", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": "12"},
    {"campo": "COB_PARAMOS", "descripcion": "Hectareas de paramo afectadas. Mayoritariamente numerica, ~7.4% de los valores no vacios son marcadores de texto (\"X\"/\"x\").", "tipo": "Numerica continua (residuo de texto)", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": "4"},
    {"campo": "COB_SABANAS_PASTIZALES", "descripcion": "Hectareas de sabanas o pastizales afectadas. Mayoritariamente numerica, ~6.2% de los valores no vacios son texto residual (\"X\", \"SD\", o valores mal formados).", "tipo": "Numerica continua (residuo de texto)", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": "3"},
    {"campo": "COB_PASTOS_MANEJADOS", "descripcion": "Hectareas de pastos manejados afectadas. Mayoritariamente numerica, ~6.2% de los valores no vacios son marcadores de texto (\"X\"/\"x\").", "tipo": "Numerica continua (residuo de texto)", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": "5"},
    {"campo": "COB_RASTROJO", "descripcion": "Hectareas de rastrojo afectadas. Es la columna COB_* con mas texto residual: ~14.5% de los valores no vacios son marcadores (\"X\", \"SD\") en vez de numeros.", "tipo": "Numerica continua (residuo de texto)", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": "1"},
    {"campo": "COB_VEGETACION_SECA", "descripcion": "Hectareas de vegetacion seca afectadas. Mayoritariamente numerica, ~9.3% de los valores no vacios son texto residual (\"X\", nombres de cobertura sueltos como \"Humedales\").", "tipo": "Numerica continua (residuo de texto)", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": "1"},
    {"campo": "COB_COBERTURA_SIN_DETERMINAR", "descripcion": "Hectareas afectadas cuya cobertura no fue determinada. A diferencia de las demas columnas COB_*, esta es 100% numerica en los valores no vacios revisados.", "tipo": "Numerica continua", "dominio": "hectareas (ha)", "fuente": "IDEAM", "ejemplo": "3"},
    {"campo": "AREA_TOTAL_HA", "descripcion": "Area total afectada por el evento (variable objetivo para analisis de severidad). A diferencia de las columnas AREA_*_HA por tipo de incendio, esta si es limpia: 100% numerica en los 35.500 registros no nulos revisados (11.3% de nulos en el total).", "tipo": "Numerica continua", "dominio": "hectareas (ha), 0 - 41.079 (media ~45.6 ha)", "fuente": "IDEAM", "ejemplo": "15"},
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
