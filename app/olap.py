"""Capa de consultas del modelo estrella de la Etapa 5.

Genera SQL desde una especificacion validada contra consultas.json.
Los valores de los filtros siempre viajan como parametros.
"""
from __future__ import annotations

import json
import sqlite3
import time
from functools import lru_cache
from pathlib import Path

CARPETA_OLAP = Path(__file__).resolve().parent / "static" / "olap"
RUTA_BASE = CARPETA_OLAP / "incendios_dw.db"
RUTA_CATALOGO = CARPETA_OLAP / "consultas.json"
LIMITE_MAXIMO = 50000
ORDENES = {"valor_desc", "etiqueta"}


class ErrorConsulta(ValueError):
    """La especificacion recibida no es valida."""


@lru_cache(maxsize=1)
def catalogo() -> dict:
    return json.loads(RUTA_CATALOGO.read_text(encoding="utf-8"))


def _nivel(nivel_id: object, campo: str) -> dict:
    niveles = catalogo()["niveles"]
    if not isinstance(nivel_id, str) or nivel_id not in niveles:
        raise ErrorConsulta(f"Nivel no permitido en '{campo}': {nivel_id}")
    return niveles[nivel_id]


def _validar_filtros(filtros: object) -> dict:
    if filtros is None:
        return {}
    if not isinstance(filtros, dict):
        raise ErrorConsulta("'filtros' debe ser un objeto.")
    for nivel_id, valores in filtros.items():
        _nivel(nivel_id, "filtros")
        if not isinstance(valores, list) or not valores:
            raise ErrorConsulta(f"El filtro '{nivel_id}' debe ser una lista con valores.")
        if not all(isinstance(valor, (str, int)) for valor in valores):
            raise ErrorConsulta(f"El filtro '{nivel_id}' tiene valores no validos.")
    return filtros


def _validar_limite(limite: object) -> int:
    if limite is None:
        return LIMITE_MAXIMO
    if isinstance(limite, bool) or not isinstance(limite, int) or limite < 1:
        raise ErrorConsulta("'limite' debe ser un entero mayor que cero.")
    return min(limite, LIMITE_MAXIMO)


def _expresion_orden(nivel: dict, alias: str) -> str:
    return f"MIN({nivel['orden']})" if "orden" in nivel else alias


def construir_sql(spec: object) -> tuple[str, list]:
    """Convierte una especificacion en SQL y parametros."""
    if not isinstance(spec, dict):
        raise ErrorConsulta("La especificacion debe ser un objeto JSON.")

    datos = catalogo()
    medida = datos["medidas"].get(spec.get("medida"))
    if medida is None:
        raise ErrorConsulta(f"Medida no permitida: {spec.get('medida')}")

    nivel_filas = _nivel(spec.get("filas"), "filas")
    nivel_columnas = None
    if spec.get("columnas") is not None:
        nivel_columnas = _nivel(spec["columnas"], "columnas")
        if spec["columnas"] == spec["filas"]:
            raise ErrorConsulta("'filas' y 'columnas' deben ser niveles diferentes.")

    filtros = _validar_filtros(spec.get("filtros"))
    limite = _validar_limite(spec.get("limite"))
    orden = spec.get("orden", "etiqueta")
    if orden not in ORDENES:
        raise ErrorConsulta(f"Orden no permitido: {orden}")

    usadas = {nivel_filas["dimension"]}
    if nivel_columnas:
        usadas.add(nivel_columnas["dimension"])
    usadas.update(datos["niveles"][nivel_id]["dimension"] for nivel_id in filtros)

    columna = nivel_columnas["columna"] if nivel_columnas else "NULL"
    lineas = [
        f"SELECT {nivel_filas['columna']} AS fila, {columna} AS col, "
        f"{medida['expresion']} AS valor, "
        "SUM(f.n_eventos) AS eventos, SUM(f.con_area) AS eventos_con_area",
        f"FROM {datos['hechos']['tabla']} {datos['hechos']['alias']}",
    ]
    for nombre, dimension in datos["dimensiones"].items():
        if nombre in usadas:
            lineas.append(
                f"JOIN {dimension['tabla']} {dimension['alias']} "
                f"ON f.{dimension['clave']} = {dimension['alias']}.{dimension['clave']}"
            )

    parametros: list = []
    condiciones = []
    for nivel_id, valores in filtros.items():
        marcas = ", ".join("?" for _ in valores)
        condiciones.append(f"{datos['niveles'][nivel_id]['columna']} IN ({marcas})")
        parametros.extend(str(valor) for valor in valores)
    if condiciones:
        lineas.append("WHERE " + " AND ".join(condiciones))

    lineas.append("GROUP BY fila, col")
    orden_filas = _expresion_orden(nivel_filas, "fila")
    orden_columnas = _expresion_orden(nivel_columnas, "col") if nivel_columnas else "col"
    if orden == "valor_desc":
        lineas.append(f"ORDER BY valor DESC, {orden_filas}, {orden_columnas}")
    else:
        lineas.append(f"ORDER BY {orden_filas}, {orden_columnas}")
    lineas.append("LIMIT ?")
    parametros.append(limite)

    return "\n".join(lineas), parametros


def ejecutar(spec: object) -> dict:
    """Ejecuta la consulta con la base abierta en solo lectura."""
    sql, parametros = construir_sql(spec)
    inicio = time.perf_counter()
    conexion = sqlite3.connect(f"{RUTA_BASE.as_uri()}?mode=ro", uri=True)
    conexion.row_factory = sqlite3.Row
    try:
        cursor = conexion.execute(sql, parametros)
        columnas = [item[0] for item in cursor.description]
        filas = [dict(fila) for fila in cursor.fetchall()]
    finally:
        conexion.close()
    return {
        "columnas": columnas,
        "filas": filas,
        "sql": sql,
        "parametros": parametros,
        "ms": round((time.perf_counter() - inicio) * 1000, 2),
    }