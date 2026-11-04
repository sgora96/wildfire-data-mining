"""Verificaciones del modelo estrella de incendios (IDEAM, 2010-2024).

Ejecuta las consultas de sql/validaciones.sql sobre data/warehouse/incendios_dw.db
y las compara con los valores esperados, calculados con pandas sobre el CSV
tratado (o tomados de las cifras de control del equipo cuando el CSV no las
trae, como las regiones). Imprime OK / FALLA con los dos valores comparados y
escribe docs/olap/validaciones.md.

Uso (desde la raiz del repositorio, despues de build_dw.py):
    python scripts/etl/validar_dw.py

Devuelve codigo de salida 1 si alguna verificacion falla.
"""

import re
import sqlite3
import sys
from collections import Counter

import pandas as pd

from build_dw import (ANIOS, CAUSA_DE_COLUMNA, CAUSAS, COBERTURAS, DB, MESES, RAIZ,
                      causas_de_celda, clave_municipio, leer_csv)

SQL = RAIZ / "sql" / "validaciones.sql"
MD = RAIZ / "docs" / "olap" / "validaciones.md"

# Cifras de control del equipo (calculadas con pandas sobre el CSV tratado).
HA_POR_REGION = {"Orinoquia": 796581, "Andina": 468957, "Caribe": 179877,
                 "Pacifica": 133028, "Amazonia": 34361, "Insular": 113, "Sin region": 0}
EVENTOS_POR_REGION = {"Orinoquia": 3714, "Andina": 23469, "Caribe": 3833,
                      "Pacifica": 3347, "Amazonia": 912, "Insular": 37, "Sin region": 43}
EVENTOS_POR_CAUSA = {"Sin causa registrada": 31207, "Intencional": 1402,
                     "Quema fuera de control": 974, "Accidental": 598,
                     "Descuido o negligencia": 583, "Otra": 499,
                     "Mas de una causa": 49, "Reactivacion de focos": 43}
EVENTOS_POR_GRUPO = {"No informada": 20448, "Sin determinar": 8495,
                     "Vegetacion arbustiva y seca": 1622, "Bosques": 1533,
                     "Pastos y sabanas": 1531, "Varios tipos": 1285,
                     "Cultivos": 313, "Paramos": 128}
HA_POR_GRUPO = {"No informada": 943500, "Sin determinar": 475905, "Bosques": 62590,
                "Pastos y sabanas": 55063, "Varios tipos": 48925,
                "Vegetacion arbustiva y seca": 15083, "Cultivos": 6891, "Paramos": 4962}
# Etapa 4 (docs/powerbi/dax_base.md y A4): filas evento-causa y "Intencional".
E4_FILAS_CAUSA = 4198
E4_INTENCIONAL = 1415
E4_HA_COBERTURA = 669358


def fmt(valor, decimales=0):
    """Formato espanol: punto para miles y coma para decimales."""
    if valor is None:
        return "NULL"
    if isinstance(valor, dict):
        return f"{len(valor)} filas, suma {fmt(sum(valor.values()), decimales)}"
    if isinstance(valor, (list, tuple)):
        return ", ".join(f"{k} {fmt(v)}" for k, v in valor)
    if isinstance(valor, str):
        return valor
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "#").replace(".", ",").replace("#", ".")


class Verificador:
    def __init__(self, con):
        self.con = con
        self.resultados = []
        consultas = re.split(r"^-- @(\w+)[^\n]*\n", SQL.read_text(encoding="utf-8"),
                             flags=re.M)
        self.consultas = {nombre: cuerpo for nombre, cuerpo
                          in zip(consultas[1::2], consultas[2::2])}

    def filas(self, nombre):
        sql = "\n".join(l for l in self.consultas[nombre].splitlines()
                        if not l.startswith("--")).strip().rstrip(";")
        return self.con.execute(sql).fetchall()

    def escalar(self, nombre):
        return self.filas(nombre)[0][0]

    def comparar(self, grupo, nombre, modelo, esperado, tol=0.0, decimales=0, nota=""):
        if isinstance(modelo, dict):
            ok = set(modelo) == set(esperado) and all(
                abs(modelo[k] - esperado[k]) <= tol for k in modelo)
        elif isinstance(modelo, (list, tuple)):
            ok = list(modelo) == list(esperado)
        else:
            ok = abs(modelo - esperado) <= tol
        marca = "OK    " if ok else "FALLA "
        print(f"[{marca}] {nombre}: modelo = {fmt(modelo, decimales)} | "
              f"esperado = {fmt(esperado, decimales)}")
        self.resultados.append({"grupo": grupo, "nombre": nombre, "ok": ok, "nota": nota,
                                "modelo": fmt(modelo, decimales),
                                "esperado": fmt(esperado, decimales)})
        return ok


def valores_esperados(df):
    """Todo lo que se calcula con pandas sobre el CSV tratado."""
    area = df["AREA_TOTAL_HA_NUM"]
    anio = pd.to_numeric(df["ANIO"])
    mes = df["MES_NORM"].map(MESES)
    dep = df["DEPARTAMENTO_NORM"]
    cols_cob = [c for c, _, _, _ in COBERTURAS]
    n_tipos = (df[cols_cob] > 0).sum(axis=1)
    hoja_2024 = df["FUENTE_HOJA"] == "BD_ICV_2024"
    ent_2024 = df.loc[hoja_2024, "ENTIDAD_REPORTA"]

    pares = set(zip(dep.fillna("Sin departamento"),
                    df["MUNICIPIO_NORM"].fillna("Sin municipio").map(clave_municipio)))
    pares.add(("Sin departamento", "SIN MUNICIPIO"))  # fila 0 del modelo

    causas = [{causas_de_celda(v, c) for v, c in zip(f, CAUSA_DE_COLUMNA)} - {None}
              for f in df[list(CAUSA_DE_COLUMNA)].itertuples(index=False)]

    return {
        "n": len(df),
        "ha": area.sum(),
        "con_area": int(area.notna().sum()),
        "area_nula": int(area.isna().sum()),
        "area_cero": int((area == 0).sum()),
        "sin_fecha": int(anio.isna().sum()),
        "anio_sin_mes": int((anio.notna() & mes.isna()).sum()),
        "calendario": int((anio.notna() & mes.notna()).sum()),
        "sin_departamento": int(dep.isna().sum()),
        "sin_municipio": int(df["MUNICIPIO_NORM"].isna().sum()),
        "departamentos": int(dep.nunique()),
        "pares_territorio": len(pares),
        "por_anio": {int(a): int(n) for a, n in anio.dropna().value_counts().items()},
        "por_departamento": dep.dropna().value_counts().to_dict(),
        "por_hoja": df["FUENTE_HOJA"].value_counts().to_dict(),
        "filas_fuente": int(df.loc[~hoja_2024, "FUENTE_HOJA"].nunique()
                            + ent_2024.dropna().nunique() + int(ent_2024.isna().any())),
        "fuente_no_aplica": int((~hoja_2024).sum()),
        "fuente_sin_dato": int(ent_2024.isna().sum()),
        "sin_cobertura": int((n_tipos == 0).sum()),
        "un_tipo": int((n_tipos == 1).sum()),
        "varios_tipos": int((n_tipos >= 2).sum()),
        "ha_cobertura_e4": float(df[cols_cob].sum().sum()),
        "causas_por_evento": causas,
    }


def verificar(v, esp):
    g1, g2, g3 = "Integridad", "Faltantes y desconocidos", "Comparación con los datos tratados"

    # -- 1. Integridad
    v.comparar(g1, "Filas de fact_incendio", v.escalar("filas_hechos"), esp["n"])
    v.comparar(g1, "Suma de n_eventos", v.escalar("suma_eventos"), esp["n"])
    v.comparar(g1, "id_evento repetidos", v.escalar("ids_repetidos"), 0)
    v.comparar(g1, "JOIN de los hechos con las 6 dimensiones (filas)",
               v.escalar("join_seis_dimensiones"), esp["n"],
               nota="El JOIN no multiplica ni pierde filas.")
    huerfanas = len(v.con.execute("PRAGMA foreign_key_check").fetchall())
    v.comparar(g1, "PRAGMA foreign_key_check (claves foráneas huérfanas)", huerfanas, 0)
    for dim in ("tiempo", "territorio", "tamano", "causa", "cobertura", "fuente"):
        v.comparar(g1, f"Hechos sin miembro en dim_{dim}", v.escalar(f"huerfanos_{dim}"), 0)
        v.comparar(g1, f"Claves primarias repetidas en dim_{dim}",
                   v.escalar(f"pk_repetidas_{dim}"), 0)
        v.comparar(g1, f"Miembros repetidos (clave natural) en dim_{dim}",
                   v.escalar(f"natural_repetida_{dim}"), 0)
    v.comparar(g1, "con_area coherente con area_total_ha",
               v.escalar("con_area_inconsistente"), 0)

    # -- 2. Faltantes y desconocidos
    v.comparar(g2, "Eventos sin año (tiempo_key = 0)", v.escalar("tiempo_sin_fecha"),
               esp["sin_fecha"])
    v.comparar(g2, "Eventos con año y sin mes válido", v.escalar("tiempo_anio_sin_mes"),
               esp["anio_sin_mes"])
    v.comparar(g2, "Eventos con año y mes válidos", v.escalar("tiempo_calendario_valido"),
               esp["calendario"])
    v.comparar(g2, "Eventos sin departamento", v.escalar("territorio_sin_departamento"),
               esp["sin_departamento"])
    v.comparar(g2, "Eventos sin municipio", v.escalar("territorio_sin_municipio"),
               esp["sin_municipio"])
    v.comparar(g2, "Eventos sin área (tamano_key = 0)", v.escalar("tamano_sin_dato"),
               esp["area_nula"])
    v.comparar(g2, "Eventos con área NULL (no convertida a 0)", v.escalar("area_nula"),
               esp["area_nula"])
    v.comparar(g2, "Eventos con área exactamente 0 (valor real, no faltante)",
               v.escalar("area_cero"), esp["area_cero"])
    v.comparar(g2, "Eventos sin causa registrada", v.escalar("causa_sin_registro"),
               EVENTOS_POR_CAUSA["Sin causa registrada"])
    v.comparar(g2, "Eventos con más de una causa", v.escalar("causa_varias"),
               sum(1 for c in esp["causas_por_evento"] if len(c) >= 2))
    v.comparar(g2, "Eventos sin cobertura informada", v.escalar("cobertura_sin_informar"),
               esp["sin_cobertura"])
    v.comparar(g2, "Eventos con más de un tipo de cobertura",
               v.escalar("cobertura_varios_tipos"), esp["varios_tipos"])
    v.comparar(g2, "Eventos de hojas sin ENTIDAD_REPORTA ('No aplica')",
               v.escalar("fuente_no_aplica"), esp["fuente_no_aplica"])
    v.comparar(g2, "Eventos de 2024 sin entidad ('Sin dato')", v.escalar("fuente_sin_dato"),
               esp["fuente_sin_dato"])

    # -- 3. Comparación con los datos tratados (pandas)
    v.comparar(g3, "Suma de hectáreas (ha)", v.escalar("suma_hectareas"), esp["ha"],
               tol=0.01, decimales=2)
    v.comparar(g3, "Eventos con área", v.escalar("eventos_con_area"), esp["con_area"])
    v.comparar(g3, "Filas de dim_tiempo (15 años x 12 meses + 15 'año sin mes' + 1)",
               v.escalar("filas_dim_tiempo"), len(ANIOS) * 13 + 1)
    v.comparar(g3, "Filas de dim_territorio (pares departamento-municipio normalizado)",
               v.escalar("filas_dim_territorio"), esp["pares_territorio"])
    v.comparar(g3, "Filas de dim_fuente (hoja-entidad)", v.escalar("filas_dim_fuente"),
               esp["filas_fuente"])
    v.comparar(g3, "Departamentos distintos", v.escalar("departamentos_distintos"),
               esp["departamentos"])
    por_anio = dict(v.filas("eventos_por_anio"))
    v.comparar(g3, "Eventos por año (15 años)", por_anio, esp["por_anio"])
    por_dep = dict(v.filas("eventos_por_departamento"))
    v.comparar(g3, "Eventos por departamento (33 departamentos)", por_dep,
               esp["por_departamento"])
    top5_modelo = list(por_dep.items())[:5]
    top5_pandas = list(esp["por_departamento"].items())[:5]
    v.comparar(g3, "Top 5 departamentos por eventos", top5_modelo, top5_pandas)
    v.comparar(g3, "Eventos por hoja de origen", dict(v.filas("eventos_por_hoja")),
               esp["por_hoja"])
    region = {r: (ha, ev) for r, ha, ev in v.filas("hectareas_por_region")}
    v.comparar(g3, "Hectáreas por región (ha, redondeadas)",
               {r: round(ha or 0) for r, (ha, _) in region.items()}, HA_POR_REGION,
               tol=1, nota="La región no existe en el CSV; se compara con la cifra de control del equipo.")
    v.comparar(g3, "Eventos por región", {r: ev for r, (_, ev) in region.items()},
               EVENTOS_POR_REGION)
    v.comparar(g3, "Eventos por causa", dict(v.filas("eventos_por_causa")),
               EVENTOS_POR_CAUSA)
    grupos = {g: (ev, ha) for g, ev, ha in v.filas("eventos_por_grupo_cobertura")}
    v.comparar(g3, "Eventos por grupo de cobertura",
               {g: ev for g, (ev, _) in grupos.items()}, EVENTOS_POR_GRUPO)
    v.comparar(g3, "Hectáreas por grupo de cobertura (ha, redondeadas)",
               {g: round(ha or 0) for g, (_, ha) in grupos.items()}, HA_POR_GRUPO, tol=1,
               nota="Área total del evento asignada a su cobertura; no es la de la Etapa 4.")
    con_causa = sum(1 for c in esp["causas_por_evento"] if c)
    v.comparar(g3, "Eventos con causa (4.099 con una + 49 con varias)",
               v.escalar("filas_hechos") - v.escalar("causa_sin_registro"), con_causa)
    v.comparar(g3, "Eventos con cobertura (13.622 con un tipo + 1.285 con varios)",
               v.escalar("filas_hechos") - v.escalar("cobertura_sin_informar"),
               esp["un_tipo"] + esp["varios_tipos"])

    # -- Reconciliación con la Etapa 4 (las diferencias se explican en el documento)
    e4 = Counter(c for conj in esp["causas_por_evento"] for c in conj)
    v.comparar(g3, "Filas evento-causa con las reglas de la Etapa 4 (dax_base.md)",
               sum(e4.values()), E4_FILAS_CAUSA)
    v.comparar(g3, "Eventos 'Intencional' en la Etapa 4 (A4)", e4[1], E4_INTENCIONAL)
    return por_anio, por_dep, region, grupos, e4


# ------------------------------------------------------------------ documento

def tabla(encabezados, filas):
    lineas = ["| " + " | ".join(encabezados) + " |",
              "|" + "|".join("---" for _ in encabezados) + "|"]
    lineas += ["| " + " | ".join(str(c) for c in f) + " |" for f in filas]
    return "\n".join(lineas)


def escribir_documento(v, esp, por_anio, por_dep, region, grupos, e4):
    ok = sum(r["ok"] for r in v.resultados)
    total = len(v.resultados)

    def seccion(grupo):
        filas = [(r["nombre"], r["modelo"], r["esperado"],
                  "OK" if r["ok"] else "**FALLA**", r["nota"])
                 for r in v.resultados if r["grupo"] == grupo]
        return tabla(["Verificación", "Modelo", "Esperado", "Resultado", "Nota"], filas)

    multi = [c for c in esp["causas_por_evento"] if len(c) >= 2]
    por_k = Counter(len(c) for c in multi)
    solo = {k: sum(1 for c in esp["causas_por_evento"] if c == {k}) for k in range(1, 7)}
    causas_filas = [(CAUSAS[k][0], fmt(e4[k]), fmt(solo[k]), fmt(e4[k] - solo[k]))
                    for k in range(1, 7)]
    ha_cob_modelo = v.escalar("hectareas_eventos_con_cobertura")

    md = f"""# Verificaciones del modelo estrella

Resultado de `python scripts/etl/validar_dw.py` sobre `data/warehouse/incendios_dw.db`.
Las consultas están en `sql/validaciones.sql`; los valores esperados se calculan con
pandas sobre `data/processed/incendios_ideam_tratado_2010_2024.csv` (35.355 eventos).

**Resumen: {ok} de {total} verificaciones en OK.**

Para reproducir:

```bash
python scripts/etl/build_dw.py
python scripts/etl/validar_dw.py
```

## 1. Integridad del modelo

Claves únicas, sin hechos huérfanos y sin duplicación de filas en la tabla de hechos.

{seccion("Integridad")}

## 2. Tratamiento de faltantes y desconocidos

Un faltante no se convierte en cero: el área ausente queda `NULL` (y `con_area = 0`); la
causa ausente o sin información va al miembro "Sin causa registrada"; el territorio, el
tiempo y la fuente desconocidos van a miembros explícitos ("Sin departamento",
"Sin municipio", "Sin fecha", "Sin mes", "Sin dato").

{seccion("Faltantes y desconocidos")}

## 3. Comparación del modelo con los datos tratados

{seccion("Comparación con los datos tratados")}

### Eventos por año (modelo y CSV)

{tabla(["Año", "Modelo", "CSV"], [(a, fmt(n), fmt(esp["por_anio"][a])) for a, n in por_anio.items()])}

### Cinco departamentos con más eventos

{tabla(["Departamento", "Modelo", "CSV"], [(d, fmt(n), fmt(esp["por_departamento"][d])) for d, n in list(por_dep.items())[:5]])}

### Hectáreas y eventos por región

{tabla(["Región", "Eventos", "Hectáreas"], [(r, fmt(ev), fmt(ha or 0, 1)) for r, (ha, ev) in region.items()])}

## 4. Diferencias frente a la Etapa 4 y su explicación

**Causas.** En la Etapa 4 un evento con varias causas contaba una vez en cada causa
({fmt(E4_FILAS_CAUSA)} filas evento-causa para 4.148 eventos). En el modelo una fila de
hechos es un evento, así que los {len(multi)} eventos con dos o más causas
({por_k[2]} con dos y {por_k.get(3, 0)} con tres) pasan al miembro "Mas de una causa"; así
ningún evento ni hectárea se cuenta dos veces. Por eso el modelo muestra menos eventos por
causa que la Etapa 4 (por ejemplo, Intencional {fmt(solo[1])} frente a {fmt(e4[1])}):

{tabla(["Causa", "Etapa 4 (eventos con esa causa)", "Modelo (solo esa causa)", "Diferencia (pasan a 'Mas de una causa')"], causas_filas)}

El total de eventos con causa no cambia: 4.148 en ambos.

**Hectáreas por cobertura.** La Etapa 4 sumó las columnas `COB_*` (hectáreas por tipo de
cobertura): {fmt(esp["ha_cobertura_e4"], 1)} ha. El modelo asigna el área **total** del evento
a su cobertura: los eventos con cobertura informada suman {fmt(ha_cob_modelo, 1)} ha
(diferencia de {fmt(ha_cob_modelo - esp["ha_cobertura_e4"], 1)} ha). La diferencia aparece
porque en 15 eventos la suma de coberturas supera el área total y en 75 es menor
(`docs/powerbi/dax_base.md`, sección 4). Además, en los eventos con varios tipos el modelo no
reparte el área entre tipos: la asigna a "Mas de un tipo de cobertura". Las dos cifras
responden preguntas distintas y no deben compararse entre sí.

**Calendario.** La Etapa 4 usaba un calendario de 180 meses y dejaba fuera 17 eventos sin
año o mes válido. El modelo tiene {fmt(v.escalar("filas_dim_tiempo"))} miembros de tiempo: los
180 meses, 15 miembros "año sin mes" (13 eventos) y "Sin fecha" (4 eventos), de modo que
esos 17 eventos siguen en el total y solo se excluyen al filtrar por un mes concreto.

**Municipios.** Los nombres de municipio traen variantes de mayúsculas y tildes. Se
normalizan (mayúsculas, sin tildes, sin espacios sobrantes) y la clave de territorio es el par
(departamento, municipio), porque hay municipios homónimos en distintos departamentos.
El resultado son {fmt(v.escalar("filas_dim_territorio"))} miembros, que coinciden con los pares
calculados con pandas.

**Nombres de miembros.** Los nombres de dimensiones se escriben sin tildes (por ejemplo
"Pacifica", "Paramos", "Reactivacion de focos") para que todas las vistas usen
exactamente las mismas cadenas en filtros y consultas. Los departamentos conservan la
escritura del CSV.
"""
    MD.parent.mkdir(parents=True, exist_ok=True)
    MD.write_text(md, encoding="utf-8")
    print(f"\nDocumento escrito en {MD.relative_to(RAIZ)}")
    return ok, total


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    df = leer_csv()
    esp = valores_esperados(df)
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    v = Verificador(con)
    detalle = verificar(v, esp)
    ok, total = escribir_documento(v, esp, *detalle)
    con.close()
    print(f"\n{ok} de {total} verificaciones en OK")
    sys.exit(0 if ok == total else 1)


if __name__ == "__main__":
    main()
