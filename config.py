"""Configuracion centralizada de la aplicacion Flask.

Se expone `config_by_name` para que el Application Factory
(`app.create_app`) seleccione el perfil adecuado en tiempo de arranque.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Valores comunes a todos los entornos."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-cambiar-en-produccion")

    PROJECT_NAME = "Wildfire Data Mining"
    PROJECT_TAGLINE = "Analisis predictivo de incendios forestales"

    # --- Rutas del proyecto -------------------------------------------------
    BASE_DIR = BASE_DIR
    DATA_DIR = BASE_DIR / "data"
    RAW_DATA_DIR = DATA_DIR / "raw"
    PROCESSED_DATA_DIR = DATA_DIR / "processed"
    MODELS_DIR = BASE_DIR / "models"

    # --- Carga de datasets --------------------------------------------------
    UPLOAD_FOLDER = RAW_DATA_DIR
    ALLOWED_EXTENSIONS = {"csv", "xls", "xlsx"}
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32 MB por archivo

    # --- Serializacion JSON -------------------------------------------------
    JSON_SORT_KEYS = False

    @staticmethod
    def init_app(app):
        """Hook de inicializacion: crea los directorios de trabajo."""
        for directory in (
            Config.RAW_DATA_DIR,
            Config.PROCESSED_DATA_DIR,
            Config.MODELS_DIR,
        ):
            directory.mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(Config):
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False


class FreezeConfig(ProductionConfig):
    """Perfil usado por `freeze.py` para exportar el sitio estatico."""

    FREEZER_DESTINATION = str(BASE_DIR / "build")
    # URLs relativas: el sitio funciona igual en la raiz de un dominio que en
    # un subdirectorio de GitHub Pages (usuario.github.io/repositorio/).
    FREEZER_RELATIVE_URLS = True
    FREEZER_REMOVE_EXTRA_FILES = True
    FREEZER_IGNORE_MIMETYPE_WARNINGS = True

    # Opcional: fuerza URLs absolutas si defines FREEZER_BASE_URL en el entorno.
    if os.getenv("FREEZER_BASE_URL"):
        FREEZER_BASE_URL = os.environ["FREEZER_BASE_URL"]
        FREEZER_RELATIVE_URLS = False
    # En modo estatico no hay backend: el frontend lee los JSON congelados.
    STATIC_EXPORT = True


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "freeze": FreezeConfig,
    "default": DevelopmentConfig,
}
