"""Preparacion de datos del modelo supervisado de la Etapa 6.

Pregunta: dado un incendio de cobertura vegetal reportado, con la informacion disponible al
momento del reporte, puede predecirse si sera grande (mas de 100 ha)?

Lee el CSV tratado de la Etapa 2 y escribe data/etapa6/supervisado/incendios_supervisado.tab,
un archivo en el formato nativo de Orange (tres filas de encabezado: nombres, tipos y roles),
de modo que el widget File ya reconoce la variable objetivo y la columna de identificacion.

Uso (desde la raiz del repositorio):
    python scripts/etapa6/preparar_supervisado.py
"""

import csv
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
ENTRADA = RAIZ / "data" / "processed" / "incendios_ideam_tratado_2010_2024.csv"
SALIDA = RAIZ / "data" / "etapa6" / "supervisado" / "incendios_supervisado.tab"

UMBRAL_HA = 100  # un incendio es "grande" si su area total supera este valor

# Columnas que NO se usan como predictoras y por que (se imprimen en el resumen).
EXCLUIDAS = {
    "AREA_*_HA, AREA_TOTAL_HA, AREA_TOTAL_HA_NUM, AREA_*_NUM":
        "expresan el area: contienen la respuesta (fuga de informacion)",
    "AREA_TOTAL_ATIPICO": "se deriva del area (los incendios grandes estan todos marcados)",
    "COB_*, COB_*_NUM": "hectareas por tipo de cobertura: expresan el area (fuga de informacion)",
    "CAUSA_*": "se conoce despues del evento y falta en la mayoria de los registros",
    "LATITUD_DEC, LONGITUD_DEC, ELEVACION_MSNM_NUM": "nulas en el 97 % de los eventos con area",
    "AREA_PROTEGIDA_NACIONAL": "nula en el 98 % de los eventos con area y respuestas inconsistentes",
    "MUNICIPIO_NORM": "demasiadas categorias (mas de mil) para el tamano de la muestra",
    "ENTIDAD_REPORTA": "solo existe en la hoja 2024",
}

ENCABEZADO = ["clase", "anio", "mes", "departamento", "hoja_origen", "id_evento"]
TIPOS = ["discrete", "continuous", "discrete", "discrete", "discrete", "string"]
ROLES = ["class", "", "", "", "", "meta"]


def leer():
    df = pd.read_csv(ENTRADA, encoding="utf-8-sig", dtype=str,
                     keep_default_na=False, na_values=[""])
    df["id_evento"] = range(1, len(df) + 1)  # mismo indice que el modelo estrella
    return df


def preparar(df):
    area = pd.to_numeric(df["AREA_TOTAL_HA_NUM"])
    anio = pd.to_numeric(df["ANIO"])
    resumen = {"filas_entrada": len(df), "sin_area": int(area.isna().sum())}

    con_area = df[area.notna()].copy()
    anio = anio[area.notna()]
    resumen["con_area"] = len(con_area)
    resumen["sin_anio"] = int(anio.isna().sum())

    con_area = con_area[anio.notna()].copy()
    area = area[con_area.index]
    salida = pd.DataFrame({
        "clase": (area > UMBRAL_HA).map({True: "Grande", False: "No grande"}),
        "anio": anio[con_area.index].astype(int),
        "mes": con_area["MES_NORM"].replace("Sin reporte", pd.NA).fillna("Sin mes"),
        "departamento": con_area["DEPARTAMENTO_NORM"].fillna("Sin departamento"),
        "hoja_origen": con_area["FUENTE_HOJA"],
        "id_evento": con_area["id_evento"],
    })[ENCABEZADO]
    resumen["filas_salida"] = len(salida)
    return salida, resumen


def escribir(salida):
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f, delimiter="\t", lineterminator="\n")
        escritor.writerow(ENCABEZADO)
        escritor.writerow(TIPOS)
        escritor.writerow(ROLES)
        escritor.writerows(salida.itertuples(index=False, name=None))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    salida, r = preparar(leer())
    escribir(salida)

    grandes = int((salida["clase"] == "Grande").sum())
    print(f"Filas del CSV tratado:           {r['filas_entrada']:>7,}")
    print(f"  sin area (descartadas):        {r['sin_area']:>7,}")
    print(f"  con area:                      {r['con_area']:>7,}")
    print(f"  sin anio (descartadas):        {r['sin_anio']:>7,}")
    print(f"Filas del archivo para Orange:   {r['filas_salida']:>7,}")
    print(f"  Grande (> {UMBRAL_HA} ha):             {grandes:>7,}  ({100 * grandes / len(salida):.2f} %)")
    print(f"  No grande:                     {len(salida) - grandes:>7,}  ({100 * (len(salida) - grandes) / len(salida):.2f} %)")
    print(f"  Linea base (siempre 'No grande'): accuracy {100 * (len(salida) - grandes) / len(salida):.2f} %")
    print("\nPredictoras: anio (numerica), mes, departamento y hoja_origen (categoricas).")
    print("Columnas excluidas y motivo:")
    for columnas, motivo in EXCLUIDAS.items():
        print(f"  - {columnas}: {motivo}")
    print(f"\nArchivo escrito: {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
