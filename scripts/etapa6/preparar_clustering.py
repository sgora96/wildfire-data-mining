"""Perfil de incendios por departamento para el clustering de la Etapa 6.

Genera una fila por departamento. No usa el area, las hectareas ni la clase
de tamano, porque el tamano es el objetivo del ejercicio supervisado.

Uso:
    python scripts/etapa6/preparar_clustering.py
"""
from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
ENTRADA = RAIZ / "data" / "processed" / "incendios_ideam_tratado_2010_2024.csv"
CARPETA_SALIDA = RAIZ / "data" / "etapa6" / "clustering"
SALIDA = CARPETA_SALIDA / "perfil_departamentos.csv"
SALIDA_EXCLUIDOS = CARPETA_SALIDA / "departamentos_excluidos.csv"
ANIOS = range(2010, 2025)
# Minimo de eventos con mes valido para que los porcentajes por trimestre sean estables.
MIN_EVENTOS_MES = 30

COLUMNAS = ["ANIO", "MES_NORM", "DEPARTAMENTO_NORM", "MUNICIPIO_NORM"]
MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}


def sin_tildes(valor: object) -> str | None:
    """Quita tildes y espacios sobrantes; devuelve None si no hay texto."""
    if pd.isna(valor):
        return None
    texto = unicodedata.normalize("NFKD", str(valor))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = " ".join(texto.split())
    return texto or None


def mes_numero(valor: object) -> float:
    """Convierte el mes normalizado en 1..12; 'Sin reporte' o nulo -> NaN."""
    texto = sin_tildes(valor)
    if texto is None:
        return np.nan
    texto = texto.lower()
    try:
        numero = int(float(texto))
        return numero if 1 <= numero <= 12 else np.nan
    except ValueError:
        return MESES.get(texto, np.nan)


def clave_municipio(valor: object) -> str | None:
    texto = sin_tildes(valor)
    return texto.upper() if texto else None


def main() -> int:
    df = pd.read_csv(
        ENTRADA, encoding="utf-8-sig", dtype=str,
        keep_default_na=False, na_values=[""],
    )
    faltan = [c for c in COLUMNAS if c not in df.columns]
    if faltan:
        print("Faltan columnas:", faltan)
        parecidas = [c for c in df.columns if any(p in c for p in ("ANIO", "MES", "DEPART", "MUNIC"))]
        print("Columnas parecidas:", parecidas)
        return 1

    df["anio"] = pd.to_numeric(df["ANIO"], errors="coerce")
    df["mes"] = df["MES_NORM"].map(mes_numero)
    df["departamento"] = df["DEPARTAMENTO_NORM"].str.strip()
    df["municipio_clave"] = df["MUNICIPIO_NORM"].map(clave_municipio)

    sin_depto = df["departamento"].isna()
    sin_anio = df["anio"].isna()
    base = df[~sin_depto & ~sin_anio].copy()
    base["anio"] = base["anio"].astype(int)

    filas = []
    for departamento, grupo in base.groupby("departamento"):
        con_mes = grupo[grupo["mes"].notna()]
        n_mes = len(con_mes)
        por_anio = grupo["anio"].value_counts().reindex(ANIOS, fill_value=0)
        media = por_anio.mean()
        filas.append({
            "departamento": departamento,
            "n_eventos": len(grupo),
            "eventos_mes_valido": n_mes,
            "log10_eventos": round(float(np.log10(len(grupo))), 4),
            "pct_t1": round(100 * con_mes["mes"].between(1, 3).sum() / n_mes, 2) if n_mes else np.nan,
            "pct_t3": round(100 * con_mes["mes"].between(7, 9).sum() / n_mes, 2) if n_mes else np.nan,
            "n_municipios": int(grupo["municipio_clave"].nunique()),
            "cv_anual": round(float(por_anio.std(ddof=0) / media), 4) if media else np.nan,
        })

    perfil = pd.DataFrame(filas).sort_values("n_eventos", ascending=False)
    excluidos = perfil[perfil["eventos_mes_valido"] < MIN_EVENTOS_MES]
    incluidos = perfil[perfil["eventos_mes_valido"] >= MIN_EVENTOS_MES]

    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
    incluidos.to_csv(SALIDA, index=False, encoding="utf-8")
    excluidos.to_csv(SALIDA_EXCLUIDOS, index=False, encoding="utf-8")

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 20)
    print(f"Filas de entrada: {len(df)}")
    print(f"Sin departamento: {int(sin_depto.sum())}")
    print(f"Con departamento pero sin anio: {int((~sin_depto & sin_anio).sum())}")
    print(f"Eventos usados: {len(base)}")
    print(f"Departamentos: {len(perfil)}")
    print(f"Excluidos (menos de {MIN_EVENTOS_MES} eventos con mes valido): {len(excluidos)}")
    print(f"Departamentos para el clustering: {len(incluidos)}\n")
    print(perfil.to_string(index=False))
    if len(excluidos):
        print("\nExcluidos:", ", ".join(excluidos["departamento"]))
    print(f"\nArchivo: {SALIDA.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())