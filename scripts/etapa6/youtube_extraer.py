"""Extraccion de videos y comentarios de YouTube sobre incendios forestales (Etapa 6).

Proposito de analisis: que causas, responsables, emociones y expectativas expresan
los usuarios sobre los incendios forestales en Colombia, y en que coinciden o
difieren con lo que muestran los datos del IDEAM (ver A5.3 de la guia de la etapa).

Usa unicamente la libreria estandar (urllib) para llamar a la YouTube Data API v3,
mas python-dotenv (ya es dependencia del proyecto) para leer la clave desde .env.
La clave NUNCA se imprime ni se guarda en los archivos de salida.

Uso (desde la raiz del repositorio, con un archivo .env que tenga YOUTUBE_API_KEY):
    python scripts/etapa6/youtube_extraer.py

Salida:
    data/etapa6/youtube/raw/<video_id>.json   (comentarios crudos, uno por video;
                                                ignorado por git)
    data/etapa6/youtube/videos_consultados.csv
"""

import csv
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
import os

RAIZ = Path(__file__).resolve().parents[2]
RAW_DIR = RAIZ / "data" / "etapa6" / "youtube" / "raw"
VIDEOS_CSV = RAIZ / "data" / "etapa6" / "youtube" / "videos_consultados.csv"

API_BASE = "https://www.googleapis.com/youtube/v3"

# --- Consultas de busqueda (en espanol, acotadas a Colombia) -----------------
# Cada consulta cubre un angulo distinto del tema para diversificar las fuentes.
CONSULTAS = [
    "incendios forestales Colombia",
    "causas incendios forestales Colombia",
    "prevencion incendios forestales Colombia",
    "incendios forestales Colombia bomberos",
    "incendios forestales Colombia cambio climatico",
    "incendios forestales Colombia IDEAM",
    "emergencia incendios forestales Colombia departamentos",
    "incendios forestales Colombia medio ambiente",
]

VIDEOS_POR_CONSULTA = 15  # resultados de busqueda a revisar por consulta
MIN_COMENTARIOS = 15      # se descartan videos con muy pocos comentarios
MAX_VIDEOS_FINALES = 8    # tope de videos seleccionados (A5.3: 6 a 10)
MIN_VIDEOS_FINALES = 6

# Palabras de fuentes "oficiales" o de divulgacion, para preferir diversidad de
# canales (no es un filtro excluyente, solo ayuda a documentar el criterio).


def leer_clave():
    load_dotenv(RAIZ / ".env")
    clave = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not clave:
        print("ERROR: no se encontro YOUTUBE_API_KEY en el archivo .env", file=sys.stderr)
        print("Crea un archivo .env en la raiz del repo con la linea:", file=sys.stderr)
        print("YOUTUBE_API_KEY=tu_clave", file=sys.stderr)
        sys.exit(1)
    return clave


def llamar_api(endpoint, params, clave, reintentos=3):
    params = dict(params)
    params["key"] = clave
    url = f"{API_BASE}/{endpoint}?{urllib.parse.urlencode(params)}"
    for intento in range(1, reintentos + 1):
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            cuerpo = e.read().decode("utf-8", errors="replace")
            try:
                detalle = json.loads(cuerpo)
                razon = detalle.get("error", {}).get("errors", [{}])[0].get("reason", "")
                mensaje = detalle.get("error", {}).get("message", "")
            except json.JSONDecodeError:
                razon, mensaje = "", cuerpo
            if e.code == 403:
                # Puede ser cuota agotada o comentarios desactivados: lo maneja
                # quien llama (distinto tratamiento segun el endpoint).
                raise PermisoDenegado(razon, mensaje) from None
            if e.code in (500, 503) and intento < reintentos:
                time.sleep(2 * intento)
                continue
            raise RuntimeError(f"HTTP {e.code} en {endpoint}: {mensaje} ({razon})") from None
        except urllib.error.URLError:
            if intento < reintentos:
                time.sleep(2 * intento)
                continue
            raise
    raise RuntimeError(f"No se pudo completar la llamada a {endpoint} tras {reintentos} intentos")


class PermisoDenegado(Exception):
    def __init__(self, razon, mensaje):
        super().__init__(mensaje)
        self.razon = razon
        self.mensaje = mensaje


def buscar_videos(consulta, clave):
    """search.list: 100 unidades de cuota por llamada."""
    data = llamar_api("search", {
        "part": "snippet",
        "q": consulta,
        "type": "video",
        "regionCode": "CO",
        "relevanceLanguage": "es",
        "maxResults": VIDEOS_POR_CONSULTA,
        "order": "relevance",
    }, clave)
    return [item["id"]["videoId"] for item in data.get("items", [])]


def detalles_videos(video_ids, clave):
    """videos.list: 1 unidad de cuota por llamada (hasta 50 ids a la vez)."""
    if not video_ids:
        return {}
    data = llamar_api("videos", {
        "part": "snippet,statistics",
        "id": ",".join(video_ids),
    }, clave)
    detalles = {}
    for item in data.get("items", []):
        detalles[item["id"]] = {
            "titulo": item["snippet"]["title"],
            "canal": item["snippet"]["channelTitle"],
            "descripcion": item["snippet"].get("description", ""),
            "fecha_publicacion": item["snippet"]["publishedAt"],
            "comment_count": int(item.get("statistics", {}).get("commentCount", 0)),
        }
    return detalles


def _sin_tildes(texto):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", texto)
                   if unicodedata.category(c) != "Mn")


# Canales de noticias/entidades colombianas conocidos: si el titulo o la
# descripcion no menciona "Colombia" explicitamente, se acepta igual si el
# canal es uno de estos (para no descartar, por ejemplo, un reporte regional
# que da por sentado el pais).
CANALES_COLOMBIANOS_CONOCIDOS = {
    "noticias caracol", "caracol radio", "canal rcn", "noticias rcn",
    "el espectador", "el tiempo", "semana", "blu radio", "w radio colombia",
    "ideam", "colombia", "canal 1 colombia", "city tv bogota",
}


def es_sobre_colombia(det):
    """Filtra videos que no sean claramente sobre incendios forestales en Colombia.

    El parametro regionCode=CO de la busqueda solo prioriza resultados para esa
    region, no garantiza que el contenido sea sobre Colombia (por ejemplo,
    aparecio un video sobre un incendio en Madrid, Espana): por eso se exige
    que el titulo o la descripcion mencionen "colombia", o que el canal sea uno
    de entidades/medios colombianos reconocidos.
    """
    texto = _sin_tildes((det["titulo"] + " " + det["descripcion"]).lower())
    if "colombia" in texto:
        return True
    return _sin_tildes(det["canal"].lower()) in CANALES_COLOMBIANOS_CONOCIDOS


def extraer_comentarios(video_id, clave):
    """commentThreads.list con paginacion, hasta 100 por pagina.

    No se piden las respuestas anidadas (replies): se documenta como
    restriccion (A5.3 pide registrar las restricciones encontradas).
    """
    comentarios = []
    token = None
    while True:
        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": 100,
            "textFormat": "plainText",
            "order": "relevance",
        }
        if token:
            params["pageToken"] = token
        try:
            data = llamar_api("commentThreads", params, clave)
        except PermisoDenegado as e:
            if e.razon == "commentsDisabled":
                return None  # comentarios desactivados en este video
            raise
        for item in data.get("items", []):
            top = item["snippet"]["topLevelComment"]["snippet"]
            comentarios.append({
                "fecha": top["publishedAt"],
                "likes": int(top.get("likeCount", 0)),
                "texto": top["textDisplay"],
            })
        token = data.get("nextPageToken")
        if not token:
            break
    return comentarios


def main():
    # La consola de Windows (cp1252) no puede mostrar emojis de los titulos;
    # esto solo afecta lo que se imprime en pantalla, no los datos guardados.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    clave = leer_clave()
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Buscar candidatos por cada consulta y quitar duplicados.
    candidatos = []
    vistos = set()
    cuota_usada = 0
    for consulta in CONSULTAS:
        ids = buscar_videos(consulta, clave)
        cuota_usada += 100
        for vid in ids:
            if vid not in vistos:
                vistos.add(vid)
                candidatos.append((vid, consulta))

    print(f"Candidatos encontrados: {len(candidatos)} (cuota usada en busquedas: {cuota_usada} unidades)")

    # 2) Pedir detalles (titulo, canal, fecha, cantidad de comentarios) en lotes de 50.
    info = {}
    ids_candidatos = [vid for vid, _ in candidatos]
    for i in range(0, len(ids_candidatos), 50):
        lote = ids_candidatos[i:i + 50]
        info.update(detalles_videos(lote, clave))
        cuota_usada += 1

    # 3) Seleccionar videos: priorizar distintos canales y suficientes comentarios.
    # Se ordenan los candidatos validos por cantidad de comentarios (descendente)
    # para quedarse, por cada canal, con su video de mayor participacion.
    validos = []
    for vid, consulta in candidatos:
        det = info.get(vid)
        if not det or not es_sobre_colombia(det) or det["comment_count"] < MIN_COMENTARIOS:
            continue
        validos.append((vid, consulta, det))
    validos.sort(key=lambda t: t[2]["comment_count"], reverse=True)

    seleccionados = []
    canales_usados = set()
    # primera pasada: el video de mas comentarios de cada canal distinto
    for vid, consulta, det in validos:
        if det["canal"] in canales_usados:
            continue
        seleccionados.append((vid, consulta, det))
        canales_usados.add(det["canal"])
        if len(seleccionados) >= MAX_VIDEOS_FINALES:
            break

    # segunda pasada: completar hasta el minimo si hace falta, permitiendo
    # repetir canal (se documenta igual con el motivo).
    if len(seleccionados) < MIN_VIDEOS_FINALES:
        ya = {vid for vid, _, _ in seleccionados}
        for vid, consulta, det in validos:
            if vid in ya:
                continue
            seleccionados.append((vid, consulta, det))
            ya.add(vid)
            if len(seleccionados) >= MIN_VIDEOS_FINALES:
                break

    print(f"Videos seleccionados: {len(seleccionados)}")

    # 4) Extraer comentarios de cada video seleccionado.
    filas_csv = []
    fecha_extraccion = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for vid, consulta, det in seleccionados:
        print(f"Extrayendo comentarios de {vid} ({det['titulo'][:60]!r})...")
        comentarios = extraer_comentarios(vid, clave)
        disponibles = comentarios is not None
        obtenidos = len(comentarios) if comentarios else 0
        if comentarios:
            (RAW_DIR / f"{vid}.json").write_text(
                json.dumps({"video_id": vid, "comentarios": comentarios}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        motivo = (
            f"resultado relevante para la busqueda '{consulta}', canal '{det['canal']}', "
            f"{det['comment_count']} comentarios reportados por la API"
        )
        if not disponibles:
            motivo += " -- comentarios desactivados, no se pudieron extraer"
        filas_csv.append({
            "video_id": vid,
            "titulo": det["titulo"],
            "canal": det["canal"],
            "url": f"https://www.youtube.com/watch?v={vid}",
            "fecha_publicacion": det["fecha_publicacion"],
            "fecha_extraccion": fecha_extraccion,
            "comentarios_disponibles": "si" if disponibles else "no",
            "comentarios_obtenidos": obtenidos,
            "motivo_seleccion": motivo,
        })

    VIDEOS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with VIDEOS_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.DictWriter(f, fieldnames=[
            "video_id", "titulo", "canal", "url", "fecha_publicacion",
            "fecha_extraccion", "comentarios_disponibles", "comentarios_obtenidos",
            "motivo_seleccion",
        ])
        escritor.writeheader()
        escritor.writerows(filas_csv)

    total_comentarios = sum(f["comentarios_obtenidos"] for f in filas_csv)
    sin_comentarios = sum(1 for f in filas_csv if f["comentarios_disponibles"] == "no")
    print(f"\nResumen: {len(filas_csv)} videos registrados, {total_comentarios} comentarios "
          f"extraidos, {sin_comentarios} con comentarios desactivados.")
    print(f"Escrito: {VIDEOS_CSV}")
    print(f"JSON crudo en: {RAW_DIR}")


if __name__ == "__main__":
    main()
