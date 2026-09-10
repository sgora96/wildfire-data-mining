"""Estructura del menu lateral: modulos > submodulos > paginas.

Un solo lugar para construir el sidebar compartido (`templates/_shell.html`)
y el breadcrumb de cada pagina. Para agregar una nueva etapa del proyecto,
se agrega aqui un nuevo submodulo dentro de "etapas" con su propia lista
de paginas; el sidebar y el breadcrumb se actualizan solos.
"""

from __future__ import annotations

from app.etapa1 import SUBMENU as _ETAPA1_PAGINAS
from app.etapa2 import SUBMENU as _ETAPA2_PAGINAS

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
