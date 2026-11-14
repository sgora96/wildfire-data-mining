"""Blueprint de la Etapa 6: conocimiento oculto (aprendizaje supervisado, clustering y comentarios de YouTube).
"""
from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from flask import Blueprint, render_template

etapa6_bp = Blueprint("etapa6", __name__, url_prefix="/etapa-6")

SUBMENU = [
    {"slug": "conocimiento_oculto", "label": "Conocimiento Oculto"},
]

# Enlace del video de sustentacion (maximo 10 minutos), con permiso "cualquier persona con el enlace".
# Mientras este vacio, la pagina muestra que el enlace esta pendiente. Si es de YouTube, se integra en la pagina.
VIDEO_URL = "https://youtu.be/eDYke3cpFs8"


def _video_embed(url: str) -> str | None:
    """Devuelve la URL para integrar el video si es de YouTube; en otro caso, None (solo se enlaza)."""
    if not url:
        return None
    partes = urlparse(url)
    host = partes.netloc.lower().removeprefix("www.")
    if host == "youtu.be" and partes.path.strip("/"):
        return f"https://www.youtube.com/embed/{partes.path.strip('/')}"
    if host in ("youtube.com", "m.youtube.com"):
        if partes.path == "/watch" and "v" in parse_qs(partes.query):
            return f"https://www.youtube.com/embed/{parse_qs(partes.query)['v'][0]}"
        if partes.path.startswith(("/embed/", "/shorts/")):
            return f"https://www.youtube.com/embed/{partes.path.split('/')[2]}"
    return None


@etapa6_bp.route("/")
def conocimiento_oculto():
    return render_template(
        "etapa6/conocimiento_oculto.html",
        video_url=VIDEO_URL,
        video_embed=_video_embed(VIDEO_URL),
    )
