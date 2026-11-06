"""ETL del modelo estrella de incendios (IDEAM, 2010-2024).

Lee el CSV tratado en la Etapa 2, construye las 6 dimensiones y la tabla de
hechos segun sql/schema.sql y carga todo en una base SQLite.

Uso (desde la raiz del repositorio):
    python scripts/etl/build_dw.py

Salida:
    data/warehouse/incendios_dw.db
    app/static/olap/incendios_dw.db   (copia para Flask y el sitio estatico)

Es determinista: las dimensiones se ordenan antes de asignar claves subrogadas.
"""

import re
import shutil
import sqlite3
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
CSV = RAIZ / "data" / "processed" / "incendios_ideam_tratado_2010_2024.csv"
ESQUEMA = RAIZ / "sql" / "schema.sql"
DB = RAIZ / "data" / "warehouse" / "incendios_dw.db"
DB_APP = RAIZ / "app" / "static" / "olap" / "incendios_dw.db"

ANIOS = range(2010, 2025)

MESES = {
    "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5, "Junio": 6,
    "Julio": 7, "Agosto": 8, "Septiembre": 9, "Octubre": 10, "Noviembre": 11,
    "Diciembre": 12,
}
NOMBRE_MES = {m: n for n, m in MESES.items()}

# Region natural por departamento (supuesto: cada departamento va a una sola
# region; referencia: regiones naturales de Colombia, IGAC).
REGIONES = {
    "Amazonia": ["Amazonas", "Caqueta", "Guainia", "Guaviare", "Putumayo", "Vaupes"],
    "Orinoquia": ["Arauca", "Casanare", "Meta", "Vichada"],
    "Caribe": ["Atlantico", "Bolivar", "Cesar", "Cordoba", "La Guajira", "Magdalena", "Sucre"],
    "Pacifica": ["Choco", "Valle del Cauca", "Cauca", "Narino"],
    "Insular": ["San Andres, Providencia y Santa Catalina"],
    "Andina": ["Antioquia", "Boyaca", "Caldas", "Cundinamarca", "Huila",
               "Norte de Santander", "Quindio", "Risaralda", "Santander", "Tolima",
               "Bogota, D.C."],
}

# Causas (claves de dim_causa). Las reglas son las de la Etapa 4.
CAUSAS = {
    0: ("Sin causa registrada", "Sin causa registrada"),
    1: ("Intencional", "Con causa registrada"),
    2: ("Quema fuera de control", "Con causa registrada"),
    3: ("Descuido o negligencia", "Con causa registrada"),
    4: ("Accidental", "Con causa registrada"),
    5: ("Reactivacion de focos", "Con causa registrada"),
    6: ("Otra", "Con causa registrada"),
    7: ("Mas de una causa", "Mas de una causa"),
}
CAUSA_DE_COLUMNA = {
    "CAUSA_QUEMA_FUERA_CONTROL": 2,
    "CAUSA_DESCUIDO_NEGLIGENCIA": 3,
    "CAUSA_INTENCIONAL": 1,
    "CAUSA_ACCIDENTAL": 4,
    "CAUSA_REACTIVACION_FOCOS": 5,
    "CAUSA_OTRA": 6,
}
MARCAS_AFIRMATIVAS = {"x", "1", "si"}
LETRAS_DE_CAUSA = {"q", "d", "i", "a", "r", "o"}
TEXTO_A_CAUSA = {
    "accidental": 4,
    "intencional": 1,
    "quemas fuera de control": 2,
    "descuido y negligencia": 3,
    "otros": 6,
    "rayo seco": 6,
    "reactivacion de focos": 5,
}
MARCAS_DESCARTADAS = {"0", "sin definir", "controlada"}

# Coberturas (claves de dim_cobertura): columna del CSV -> (clave, grupo, tipo).
COBERTURAS = [
    ("COB_BOSQUE_NATURAL_DENSO_NUM", 1, "Bosques", "Bosque natural denso"),
    ("COB_BOSQUE_INTERVENIDO_NUM", 2, "Bosques", "Bosque intervenido"),
    ("COB_BOSQUE_PLANTADO_NUM", 3, "Bosques", "Bosque plantado"),
    ("COB_BOSQUE_SECO_NUM", 4, "Bosques", "Bosque seco"),
    ("COB_SABANAS_PASTIZALES_NUM", 5, "Pastos y sabanas", "Sabanas y pastizales"),
    ("COB_PASTOS_MANEJADOS_NUM", 6, "Pastos y sabanas", "Pastos manejados"),
    ("COB_CULTIVOS_NUM", 7, "Cultivos", "Cultivos"),
    ("COB_PARAMOS_NUM", 8, "Paramos", "Paramos"),
    ("COB_RASTROJO_NUM", 9, "Vegetacion arbustiva y seca", "Rastrojo"),
    ("COB_VEGETACION_SECA_NUM", 10, "Vegetacion arbustiva y seca", "Vegetacion seca"),
    ("COB_COBERTURA_SIN_DETERMINAR_NUM", 11, "Sin determinar", "Cobertura sin determinar"),
]
COB_VARIOS = (12, "Varios tipos", "Mas de un tipo de cobertura")
COB_NINGUNA = (0, "No informada", "Sin cobertura informada")

CLASES_TAMANO = [
    (0, "Sin dato", 0, 0),
    (1, "<= 1 ha", 1, 0),
    (2, "1-10 ha", 2, 0),
    (3, "10-100 ha", 3, 0),
    (4, "> 100 ha", 4, 1),
]

SIN_ENTIDAD_HOJA = "No aplica (hoja sin ese campo)"


def sin_tildes(texto):
    descompuesto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def clave_municipio(nombre):
    """MAYUSCULAS, sin tildes y sin espacios sobrantes."""
    return re.sub(r"\s+", " ", sin_tildes(nombre).strip()).upper()


def leer_csv():
    df = pd.read_csv(CSV, encoding="utf-8-sig", dtype=str,
                     keep_default_na=False, na_values=[""])
    df["AREA_TOTAL_HA_NUM"] = pd.to_numeric(df["AREA_TOTAL_HA_NUM"])
    for col, _, _, _ in COBERTURAS:
        df[col] = pd.to_numeric(df[col])
    df.insert(0, "id_evento", np.arange(1, len(df) + 1))
    return df


# ---------------------------------------------------------------- dimensiones

def construir_dim_tiempo():
    filas = [(0, None, None, None, "Sin fecha", "Sin dato",
              "Sin fecha", "Sin fecha", "Sin fecha")]
    for anio in ANIOS:
        filas.append((anio * 100, anio, None, None, "Sin mes", "Sin dato",
                      str(anio), f"{anio}-sin trimestre", f"{anio}-sin mes"))
        for mes in range(1, 13):
            trimestre = (mes - 1) // 3 + 1
            if trimestre == 1:
                temporada = "1. Ene-Mar"
            elif trimestre == 3:
                temporada = "2. Jul-Sep"
            else:
                temporada = "3. Abr-Jun y Oct-Dic"
            filas.append((anio * 100 + mes, anio, trimestre, mes, NOMBRE_MES[mes],
                          temporada, str(anio), f"{anio}-T{trimestre}",
                          f"{anio}-{mes:02d}"))
    return sorted(filas)


def clave_tiempo(df):
    anio = pd.to_numeric(df["ANIO"])
    mes = df["MES_NORM"].map(MESES)
    clave = np.where(anio.isna(), 0, anio * 100 + mes.fillna(0))
    return pd.Series(clave, index=df.index).astype(int)


def construir_dim_territorio(df):
    region_de = {}
    for region, departamentos in REGIONES.items():
        for dep in departamentos:
            region_de[sin_tildes(dep).lower()] = region

    dep = df["DEPARTAMENTO_NORM"].fillna("Sin departamento")
    mun = df["MUNICIPIO_NORM"].fillna("Sin municipio")
    clave = mun.map(clave_municipio)

    sin_region = sorted(set(d for d in dep.unique()
                            if d != "Sin departamento"
                            and sin_tildes(d).lower() not in region_de))
    if sin_region:
        raise ValueError(f"Departamentos sin region asignada: {sin_region}")

    # Nombre para mostrar: la variante mas frecuente entre las que comparten
    # (departamento, clave); si empatan, la primera en orden alfabetico.
    conteo = Counter(zip(dep, clave, mun))
    mejor = {}
    for (d, k, m), n in sorted(conteo.items(), key=lambda x: (-x[1], x[0][2])):
        mejor.setdefault((d, k), m)

    pares = sorted(mejor, key=lambda p: (
        region_de.get(sin_tildes(p[0]).lower(), "Sin region"), p[0], p[1]))
    pares = [p for p in pares if p != ("Sin departamento", "SIN MUNICIPIO")]

    def fila(key, d, k):
        region = region_de.get(sin_tildes(d).lower(), "Sin region")
        nombre = mejor.get((d, k), "Sin municipio")
        return (key, region, d, nombre, k, region, d, f"{d} / {nombre}")

    filas = [fila(0, "Sin departamento", "SIN MUNICIPIO")]
    filas += [fila(i, d, k) for i, (d, k) in enumerate(pares, start=1)]
    llaves = {(f[2], f[4]): f[0] for f in filas}
    claves = pd.Series([llaves[(d, k)] for d, k in zip(dep, clave)], index=df.index)
    return filas, claves


def construir_dim_tamano():
    return list(CLASES_TAMANO)


def clave_tamano(area):
    return np.select(
        [area.isna(), area <= 1, area <= 10, area <= 100],
        [0, 1, 2, 3], default=4).astype(int)


def causas_de_celda(valor, columna):
    """Devuelve la causa (clave 1..6) que expresa una celda, o None."""
    if pd.isna(valor):
        return None
    texto = sin_tildes(str(valor)).strip().lower()
    if texto in MARCAS_DESCARTADAS:
        return None
    if texto in MARCAS_AFIRMATIVAS or texto in LETRAS_DE_CAUSA:
        return CAUSA_DE_COLUMNA[columna]
    if texto in TEXTO_A_CAUSA:
        return TEXTO_A_CAUSA[texto]
    raise ValueError(f"Valor de causa no reconocido en {columna}: {valor!r}")


def clave_causa(df):
    resultado = []
    for fila in df[list(CAUSA_DE_COLUMNA)].itertuples(index=False):
        causas = {causas_de_celda(v, c) for v, c in zip(fila, CAUSA_DE_COLUMNA)}
        causas.discard(None)
        if not causas:
            resultado.append(0)
        elif len(causas) == 1:
            resultado.append(causas.pop())
        else:
            resultado.append(7)
    return pd.Series(resultado, index=df.index)


def construir_dim_cobertura():
    filas = [COB_NINGUNA] + [(k, g, t) for _, k, g, t in COBERTURAS] + [COB_VARIOS]
    return sorted(filas)


def clave_cobertura(df):
    columnas = [c for c, _, _, _ in COBERTURAS]
    presentes = (df[columnas] > 0).to_numpy()
    cuantos = presentes.sum(axis=1)
    clave_unica = np.array([k for _, k, _, _ in COBERTURAS])[presentes.argmax(axis=1)]
    return pd.Series(np.select([cuantos == 0, cuantos == 1],
                               [COB_NINGUNA[0], clave_unica], default=COB_VARIOS[0]),
                     index=df.index).astype(int)


def construir_dim_fuente(df):
    entidad = df["ENTIDAD_REPORTA"]
    hoja = df["FUENTE_HOJA"]
    fuera_de_2024 = hoja != "BD_ICV_2024"
    if entidad[fuera_de_2024].notna().any():
        raise ValueError("ENTIDAD_REPORTA trae datos fuera de la hoja 2024")
    entidad = entidad.where(~fuera_de_2024, SIN_ENTIDAD_HOJA).fillna("Sin dato")

    pares = sorted(set(zip(hoja, entidad)))
    filas = []
    for i, (h, e) in enumerate(pares, start=1):
        periodo = h.replace("BD_ICV_", "").replace("_", "-")
        filas.append((i, h, periodo, e, h, f"{h} / {e}"))
    llaves = {(f[1], f[3]): f[0] for f in filas}
    claves = pd.Series([llaves[p] for p in zip(hoja, entidad)], index=df.index)
    return filas, claves


# ---------------------------------------------------------------------- carga

def cargar(dims, hechos):
    DB.parent.mkdir(parents=True, exist_ok=True)
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript(ESQUEMA.read_text(encoding="utf-8"))
    con.execute("PRAGMA foreign_keys = ON")

    def insertar(tabla, filas):
        marcas = ",".join("?" * len(filas[0]))
        con.executemany(f"INSERT INTO {tabla} VALUES ({marcas})", filas)

    # Dimensiones primero para respetar las claves foraneas.
    for tabla, filas in dims:
        insertar(tabla, filas)
    insertar("fact_incendio", hechos)
    con.commit()
    huerfanas = con.execute("PRAGMA foreign_key_check").fetchall()
    if huerfanas:
        raise ValueError(f"Claves foraneas huerfanas: {len(huerfanas)}")
    return con


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    df = leer_csv()
    print(f"CSV leido: {len(df):,} filas, {df.shape[1] - 1} columnas")

    dim_tiempo = construir_dim_tiempo()
    dim_territorio, k_territorio = construir_dim_territorio(df)
    dim_fuente, k_fuente = construir_dim_fuente(df)
    area = df["AREA_TOTAL_HA_NUM"]

    hechos_df = pd.DataFrame({
        "id_evento": df["id_evento"],
        "tiempo_key": clave_tiempo(df),
        "territorio_key": k_territorio,
        "tamano_key": clave_tamano(area),
        "causa_key": clave_causa(df),
        "cobertura_key": clave_cobertura(df),
        "fuente_key": k_fuente,
        "n_eventos": 1,
        "area_total_ha": area,
        "con_area": area.notna().astype(int),
    })
    # NaN de pandas -> NULL de SQLite (no se convierte a 0).
    def a_sqlite(v):
        if isinstance(v, (float, np.floating)):
            return None if np.isnan(v) else float(v)
        return int(v)

    hechos = [tuple(a_sqlite(v) for v in fila)
              for fila in hechos_df.itertuples(index=False, name=None)]

    dims = [
        ("dim_tiempo", dim_tiempo),
        ("dim_territorio", dim_territorio),
        ("dim_tamano", construir_dim_tamano()),
        ("dim_causa", [(k, c, r) for k, (c, r) in sorted(CAUSAS.items())]),
        ("dim_cobertura", construir_dim_cobertura()),
        ("dim_fuente", dim_fuente),
    ]
    con = cargar(dims, hechos)

    print("\nFilas por tabla:")
    for tabla in [t for t, _ in dims] + ["fact_incendio"]:
        n = con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
        print(f"  {tabla:<16} {n:>7,}")

    print("\nTotales de control:")
    print("  eventos            ", con.execute("SELECT SUM(n_eventos) FROM fact_incendio").fetchone()[0])
    print("  eventos con area   ", con.execute("SELECT SUM(con_area) FROM fact_incendio").fetchone()[0])
    print("  hectareas          ", con.execute("SELECT ROUND(SUM(area_total_ha), 1) FROM fact_incendio").fetchone()[0])
    print("  con causa          ", con.execute("SELECT COUNT(*) FROM fact_incendio WHERE causa_key <> 0").fetchone()[0])
    print("  con cobertura      ", con.execute("SELECT COUNT(*) FROM fact_incendio WHERE cobertura_key <> 0").fetchone()[0])
    con.close()

    DB_APP.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(DB, DB_APP)
    print(f"\nBase escrita en {DB.relative_to(RAIZ)} y copiada a {DB_APP.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
