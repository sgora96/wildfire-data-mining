"""Limpieza de comentarios de YouTube para la Etapa 6.

Lee los JSON crudos de data/etapa6/youtube/raw/ (uno por video) y construye
comentarios_limpios.csv con las columnas de A5.3, sin ningun dato de autor
(nunca se leyo el nombre, canal ni foto del autor desde el JSON crudo).

Descarta, en este orden, y cuenta cada motivo:
  1. vacios o solo espacios
  2. duplicados exactos (texto identico, incluso de otro video)
  3. solo emojis o solo enlaces (sin texto legible)
  4. muy cortos (menos de 3 palabras)
  5. en otro idioma distinto de espanol (heuristica simple de palabras funcionales)

texto_limpio: minusculas, sin URLs ni menciones (@usuario), sin saltos de linea
repetidos. Tambien se eliminan del texto correos y numeros de telefono
evidentes (dato personal, aunque no sea el autor del comentario).

Uso (desde la raiz del repositorio, despues de youtube_extraer.py):
    python scripts/etapa6/youtube_limpiar.py

Salida:
    data/etapa6/youtube/comentarios_limpios.csv
"""

import csv
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RAW_DIR = RAIZ / "data" / "etapa6" / "youtube" / "raw"
SALIDA = RAIZ / "data" / "etapa6" / "youtube" / "comentarios_limpios.csv"

RE_URL = re.compile(r"https?://\S+|www\.\S+")
RE_MENCION = re.compile(r"@\w+")
RE_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
RE_TELEFONO = re.compile(r"\b(?:\+?57)?[ .-]?\(?3\d{2}\)?[ .-]?\d{3}[ .-]?\d{4}\b")
RE_SOLO_EMOJI_O_SIMBOLOS = re.compile(
    r"^[\W_\s"
    r"\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF"
    r"]*$"
)

# Heuristica simple de idioma: palabras funcionales muy frecuentes en espanol.
# Si un comentario con varias palabras no contiene ninguna, se marca como "otro idioma".
PALABRAS_ES = {
    "el", "la", "los", "las", "de", "del", "que", "y", "a", "en", "un", "una",
    "es", "por", "para", "con", "no", "se", "su", "lo", "como", "mas", "pero",
    "esta", "este", "esto", "muy", "son", "ya", "si", "al", "nos", "le", "les",
}


def redactar_datos_personales(texto):
    """Quita correos, telefonos y menciones @usuario de un texto que se va a publicar.

    No detecta nombres propios escritos en prosa libre (requeriria NER); eso
    queda documentado como limitacion en el informe.
    """
    t = RE_EMAIL.sub("[correo]", texto)
    t = RE_TELEFONO.sub("[telefono]", t)
    t = RE_MENCION.sub("[mencion]", t)
    return t


def limpiar_texto(texto):
    t = texto.replace("\r", " ").replace("\n", " ")
    t = RE_URL.sub(" ", t)
    t = RE_MENCION.sub(" ", t)
    t = RE_EMAIL.sub(" ", t)
    t = RE_TELEFONO.sub(" ", t)
    t = t.lower()
    t = re.sub(r"\s+", " ", t).strip()
    return t


def es_espanol(texto_limpio):
    palabras = texto_limpio.split()
    if len(palabras) < 4:
        return True  # muy corto para decidir por idioma; se filtra por longitud
    return any(p in PALABRAS_ES for p in palabras)


def motivo_descarte(texto_original, texto_limpio, vistos):
    if not texto_original or not texto_original.strip():
        return "vacio"
    if RE_SOLO_EMOJI_O_SIMBOLOS.match(texto_original.strip()):
        return "solo_emojis_o_simbolos"
    if texto_limpio in vistos:
        return "duplicado_exacto"
    if len(texto_limpio.split()) < 3:
        return "muy_corto"
    if not es_espanol(texto_limpio):
        return "otro_idioma"
    return None


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    if not RAW_DIR.exists() or not any(RAW_DIR.glob("*.json")):
        print(f"ERROR: no hay JSON en {RAW_DIR}. Corre primero youtube_extraer.py", file=sys.stderr)
        sys.exit(1)

    contadores = {
        "vacio": 0, "solo_emojis_o_simbolos": 0, "duplicado_exacto": 0,
        "muy_corto": 0, "otro_idioma": 0,
    }
    obtenidos = 0
    finales = []
    vistos = set()

    for archivo in sorted(RAW_DIR.glob("*.json")):
        data = json.loads(archivo.read_text(encoding="utf-8"))
        video_id = data["video_id"]
        for c in data["comentarios"]:
            obtenidos += 1
            texto = c["texto"]
            limpio = limpiar_texto(texto)
            motivo = motivo_descarte(texto, limpio, vistos)
            if motivo:
                contadores[motivo] += 1
                continue
            vistos.add(limpio)
            finales.append({
                "video_id": video_id,
                "fecha": c["fecha"],
                "likes": c["likes"],
                "texto": redactar_datos_personales(texto),
                "texto_limpio": limpio,
            })

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with SALIDA.open("w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.DictWriter(f, fieldnames=[
            "id_comentario", "video_id", "fecha", "likes", "texto", "texto_limpio",
        ])
        escritor.writeheader()
        for i, fila in enumerate(finales, start=1):
            escritor.writerow({"id_comentario": f"c{i:04d}", **fila})

    descartados = sum(contadores.values())
    print(f"Comentarios obtenidos (crudos): {obtenidos}")
    for motivo, n in contadores.items():
        print(f"  Descartados por {motivo}: {n}")
    print(f"Total descartados: {descartados}")
    print(f"Comentarios finales: {len(finales)}")
    print(f"Escrito: {SALIDA}")


if __name__ == "__main__":
    main()
