"""Exportacion del dashboard a un sitio estatico (GitHub Pages).

Uso:
    python freeze.py

Genera `build/` con:
    index.html          vista principal renderizada
    static/...          CSS y JS
    api/dataset.json    dataset completo (el frontend filtra en el navegador)
    api/kpis.json       KPIs precalculados
    api/analysis.json   series listas para graficar
    api/meta.json       metadatos de la fuente
    .nojekyll           evita que GitHub Pages ignore rutas con guion bajo
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

from flask_frozen import Freezer, MissingURLGeneratorWarning

from app import create_app, services

# Los endpoints /api/* no se congelan como rutas: se exportan a mano en
# `export_api()` con extension .json para que GitHub Pages los sirva bien.
warnings.filterwarnings("ignore", category=MissingURLGeneratorWarning)

app = create_app("freeze")
freezer = Freezer(app, with_no_argument_rules=False)


@freezer.register_generator
def dashboard_pages():
    """Vistas HTML a congelar (endpoint, parametros de ruta)."""
    yield "main.index", {}
    for endpoint in (
        "etapa1.problema",
        "etapa1.preguntas",
        "etapa1.necesidades",
        "etapa1.fuentes",
        "etapa1.dataset",
        "etapa1.diccionario",
        "etapa1.calidad",
        "etapa1.limitaciones",
    ):
        yield endpoint, {}


def _jsonable(df):
    """Convierte un DataFrame a listas/dicts nativos serializables."""
    return json.loads(df.to_json(orient="records"))


def export_api(build_dir: Path) -> list[str]:
    """Escribe las respuestas de la API como archivos JSON estaticos."""
    with app.app_context():
        df, source = services.load_dataset(app.config)

        payloads = {
            "dataset.json": {
                "ok": True,
                "source": source,
                "rows": int(len(df)),
                "columns": [str(c) for c in df.columns],
                "records": _jsonable(df),
            },
            "meta.json": {
                "ok": True,
                "source": source,
                "rows": int(len(df)),
                "columns": [str(c) for c in df.columns],
                "climate_columns": [
                    c for c in services.CLIMATE_COLUMNS if c in df.columns
                ],
            },
            "kpis.json": {
                "ok": True,
                "source": source,
                "matched": int(len(df)),
                "total": int(len(df)),
                "kpis": services.compute_kpis(df),
            },
            "analysis.json": {
                "ok": True,
                "source": source,
                "matched": int(len(df)),
                "charts": services.build_analysis(df),
            },
        }

    api_dir = build_dir / "api"
    api_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        (api_dir / name).write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )
    return sorted(payloads)


def main() -> int:
    build_dir = Path(app.config["FREEZER_DESTINATION"])

    print("Congelando vistas HTML…")
    urls = list(freezer.freeze_yield())
    for page in urls:
        print(f"  · {page.url}")

    print("Exportando API estatica…")
    for name in export_api(build_dir):
        print(f"  · api/{name}")

    # GitHub Pages ignora por defecto los directorios que empiezan por "_".
    (build_dir / ".nojekyll").write_text("", encoding="utf-8")

    total = sum(1 for _ in build_dir.rglob("*") if _.is_file())
    print(f"\nSitio estatico listo en '{build_dir}' ({total} archivos).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
