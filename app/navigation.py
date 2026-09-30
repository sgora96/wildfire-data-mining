"""Estructura del menu lateral: modulos > submodulos > paginas.
"""

from __future__ import annotations

from app.etapa1 import SUBMENU as _ETAPA1_PAGINAS
from app.etapa2 import SUBMENU as _ETAPA2_PAGINAS
from app.etapa3 import SUBMENU as _ETAPA3_PAGINAS

MODULOS: list[dict] = [
    {
        "id": "etapas",
        "label": "Etapas del proyecto",
        "submodulos": [
            {
                "id": "etapa-1",
                "label": "Etapa 1",
                "sublabel": "Del problema a los datos",
                "estado": "Completa",
                "paginas": (
                    [
                        {"endpoint": f"etapa1.{p['slug']}", "label": p["label"]}
                        for p in _ETAPA1_PAGINAS
                    ]
                    + [
                        {
                            "endpoint": "etapa1.tareas",
                            "label": "Equipo y tareas",
                            "divider": True,
                        }
                    ]
                ),
            },
            {
                "id": "etapa-2",
                "label": "Etapa 2",
                "sublabel": "Calidad de datos",
                "estado": "Completa",
                "paginas": [
                    {"endpoint": f"etapa2.{p['slug']}", "label": p["label"]}
                    for p in _ETAPA2_PAGINAS
                ],
            },
            {
                "id": "etapa-3",
                "label": "Etapa 3",
                "sublabel": "ETL y limpieza con SSIS",
                "estado": "Completa",
                "paginas": [
                    {"endpoint": f"etapa3.{p['slug']}", "label": p["label"]}
                    for p in _ETAPA3_PAGINAS
                ],
            },
            # Las siguientes etapas del semestre se agregan aqui, con la
            # misma forma: {"id", "label", "sublabel", "estado", "paginas"}.
        ],
    },
]


def _build_index() -> dict[str, dict[str, str]]:
    """Mapa endpoint -> {modulo, submodulo, item} para breadcrumbs."""
    index: dict[str, dict[str, str]] = {}
    for modulo in MODULOS:
        for sub in modulo.get("submodulos", []):
            for item in sub.get("paginas", []):
                index[item["endpoint"]] = {
                    "modulo": modulo["label"],
                    "submodulo": sub["label"],
                    "item": item["label"],
                }
    return index


NAV_INDEX = _build_index()
