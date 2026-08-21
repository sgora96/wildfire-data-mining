"""Application Factory de Wildfire Data Mining.

Mantiene la app desacoplada de la configuracion y de los blueprints,
de modo que se puedan crear instancias distintas para desarrollo,
testing, produccion o congelado estatico.
"""

import os

from flask import Flask

from config import config_by_name

__version__ = "0.1.0"


def create_app(config_name: str | None = None) -> Flask:
    """Construye y devuelve una instancia configurada de Flask.

    Args:
        config_name: clave de `config.config_by_name`
            (development | production | testing | freeze).
    """
    config_name = config_name or os.getenv("FLASK_CONFIG", "development")
    config_class = config_by_name.get(config_name, config_by_name["default"])

    app = Flask(__name__)
    app.config.from_object(config_class)
    config_class.init_app(app)

    # Conserva el orden de insercion en las respuestas JSON (Flask >= 2.3).
    app.json.sort_keys = app.config.get("JSON_SORT_KEYS", True)

    # --- Blueprints ---------------------------------------------------------
    from app.routes import main_bp, api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # --- Manejo de errores en formato JSON para el prefijo /api -------------
    from flask import jsonify, request

    @app.errorhandler(404)
    def _not_found(error):
        if request.path.startswith("/api"):
            return jsonify(ok=False, error="Recurso no encontrado"), 404
        return render_error(app, 404, "Pagina no encontrada"), 404

    @app.errorhandler(413)
    def _too_large(error):
        limit_mb = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
        return (
            jsonify(ok=False, error=f"El archivo supera el limite de {limit_mb} MB"),
            413,
        )

    @app.errorhandler(500)
    def _server_error(error):  # pragma: no cover - defensivo
        if request.path.startswith("/api"):
            return jsonify(ok=False, error="Error interno del servidor"), 500
        return render_error(app, 500, "Error interno del servidor"), 500

    # --- Variables disponibles en todas las plantillas ----------------------
    @app.context_processor
    def _inject_globals():
        return {
            "project_name": app.config["PROJECT_NAME"],
            "project_tagline": app.config["PROJECT_TAGLINE"],
            "version": __version__,
            "static_export": app.config.get("STATIC_EXPORT", False),
        }

    return app


def render_error(app: Flask, code: int, message: str) -> str:
    """Pagina de error minima sin necesidad de plantilla adicional."""
    return (
        "<!doctype html><html lang='es'><head><meta charset='utf-8'>"
        "<title>Wildfire Data Mining</title>"
        "<script src='https://cdn.tailwindcss.com'></script></head>"
        "<body class='min-h-screen bg-slate-950 text-slate-100 flex items-center "
        "justify-center'><div class='text-center'>"
        f"<p class='text-7xl font-black text-orange-500'>{code}</p>"
        f"<p class='mt-3 text-lg text-slate-400'>{message}</p>"
        "<a href='/' class='mt-6 inline-block rounded-lg bg-orange-600 px-5 py-2.5 "
        "font-semibold hover:bg-orange-500'>Volver al dashboard</a>"
        "</div></body></html>"
    )
