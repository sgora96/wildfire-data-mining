"""Cruce de resultados de la Etapa 6: grupos de departamentos (clustering) x incendios grandes (supervisado).

Cruza los tres perfiles de departamentos que obtuvo el clustering (k-Means, k = 3, ver
docs/etapa6/informe_clustering.md) con la variable "grande" (mas de 100 ha) del ejercicio supervisado
(data/etapa6/supervisado/incendios_supervisado.tab). Responde: los grupos que se distinguen por su
calendario, tambien se distinguen por la proporcion de incendios grandes?

Uso (desde la raiz del repositorio):
    python scripts/etapa6/cruce_resultados.py

Salida:
    data/etapa6/integracion/cruce_grupos_grandes.csv   (una fila por grupo)
    data/etapa6/integracion/cruce_departamentos.csv    (una fila por departamento)
"""

import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
ENTRADA = RAIZ / "data" / "etapa6" / "supervisado" / "incendios_supervisado.tab"
SALIDA = RAIZ / "data" / "etapa6" / "integracion"

# Pertenencia a los grupos segun el informe de clustering (k-Means, k = 3, 32 departamentos).
GRUPOS = {
    "A. Andinos grandes y extendidos": ["Cundinamarca", "Antioquia", "Boyacá", "Santander"],
    "B. Pico en julio-septiembre": ["Huila", "Tolima", "Nariño", "Valle del Cauca", "Cauca",
                                    "Norte de Santander", "Quindío", "Amazonas"],
    "C. Pico en enero-marzo, menos eventos": [
        "Casanare", "Meta", "Arauca", "Vichada", "Guaviare", "Guainía", "Caquetá", "Putumayo", "Magdalena",
        "Cesar", "Atlántico", "Bolívar", "Córdoba", "Sucre", "La Guajira", "Caldas", "Risaralda",
        "Bogotá, D.C.", "Chocó", "San Andrés, Providencia y Santa Catalina"],
}
# Los cinco departamentos con mayor proporcion de incendios grandes (con al menos 100 eventos).
MAYOR_PROPORCION = ["Vichada", "Arauca", "Casanare", "Meta", "Caquetá"]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    df = pd.read_csv(ENTRADA, sep="\t", skiprows=[1, 2], encoding="utf-8", dtype=str)
    df["grande"] = (df["clase"] == "Grande").astype(int)
    grupo_de = {dep: g for g, deps in GRUPOS.items() for dep in deps}
    fuera = sorted(set(df["departamento"]) - set(grupo_de))
    d = df[df["departamento"].isin(grupo_de)].copy()
    d["grupo"] = d["departamento"].map(grupo_de)
    total_eventos, total_grandes = len(d), int(d["grande"].sum())

    por_grupo = d.groupby("grupo").agg(eventos=("grande", "size"), grandes=("grande", "sum")).reset_index()
    por_grupo["pct_grandes"] = (100 * por_grupo["grandes"] / por_grupo["eventos"]).round(2)
    por_grupo["pct_de_eventos"] = (100 * por_grupo["eventos"] / total_eventos).round(1)
    por_grupo["pct_de_grandes"] = (100 * por_grupo["grandes"] / total_grandes).round(1)

    por_dep = (d.groupby(["grupo", "departamento"]).agg(eventos=("grande", "size"), grandes=("grande", "sum"))
               .reset_index())
    por_dep["pct_grandes"] = (100 * por_dep["grandes"] / por_dep["eventos"]).round(1)
    por_dep = por_dep.sort_values(["grupo", "pct_grandes"], ascending=[True, False])

    SALIDA.mkdir(parents=True, exist_ok=True)
    por_grupo.to_csv(SALIDA / "cruce_grupos_grandes.csv", index=False, encoding="utf-8")
    por_dep.to_csv(SALIDA / "cruce_departamentos.csv", index=False, encoding="utf-8")

    print(f"Eventos con area y anio del archivo supervisado: {len(df):,} ({int(df['grande'].sum()):,} grandes).")
    print(f"Fuera del cruce (no estan en el clustering): {', '.join(fuera)}.")
    print(f"Eventos en los 32 departamentos agrupados: {total_eventos:,}; grandes: {total_grandes:,} "
          f"({100 * total_grandes / total_eventos:.2f} %).\n")
    print(por_grupo.to_string(index=False))

    cinco = d[d["departamento"].isin(MAYOR_PROPORCION)]
    resto_c = d[d["grupo"].str.startswith("C") & ~d["departamento"].isin(MAYOR_PROPORCION)]
    print(f"\nCinco departamentos de mayor proporcion ({', '.join(MAYOR_PROPORCION)}), todos del grupo C:")
    print(f"  {int(cinco['grande'].sum()):,} incendios grandes de {total_grandes:,} "
          f"({100 * cinco['grande'].sum() / total_grandes:.1f} %) con {len(cinco):,} eventos "
          f"({100 * len(cinco) / total_eventos:.1f} %).")
    print(f"  Resto del grupo C: {len(resto_c):,} eventos, {int(resto_c['grande'].sum()):,} grandes "
          f"({100 * resto_c['grande'].mean():.2f} %).")
    print(f"\nArchivos escritos en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
