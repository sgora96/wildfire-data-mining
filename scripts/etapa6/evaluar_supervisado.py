"""Evaluacion de los tres modelos supervisados de la Etapa 6 con la libreria de Orange.

Reproduce, por codigo, lo que hace el flujo orange/supervisado/modelos_supervisados.ows:
las mismas clases de aprendizaje que usan los widgets de Orange, los mismos parametros y la
misma validacion cruzada estratificada de 10 pliegues con semilla 42 (la del widget Test and
Score). Sirve para comprobar los resultados que muestra Orange y para el informe.

Requiere Orange 3.40 (se ejecuta con el Python que trae Orange):
    <carpeta de Orange>\\python.exe scripts/etapa6/evaluar_supervisado.py

Antes hay que generar los datos: python scripts/etapa6/preparar_supervisado.py
"""

import csv
import sys
import warnings
from pathlib import Path

import numpy as np
import Orange
from Orange.classification import KNNLearner, LogisticRegressionLearner, RandomForestLearner
from Orange.evaluation import AUC, CA, F1, CrossValidation, Precision, Recall, TestOnTestData

warnings.filterwarnings("ignore")

RAIZ = Path(__file__).resolve().parents[2]
DATOS = RAIZ / "data" / "etapa6" / "supervisado" / "incendios_supervisado.tab"
SALIDA = RAIZ / "data" / "etapa6" / "supervisado" / "metricas_esperadas.csv"

PLIEGUES = 10
SEMILLA = 42  # la que usa el widget Test and Score


def modelos_principales():
    """Los tres modelos comparados (mismos parametros que en los widgets del flujo)."""
    return {
        "Regresion logistica": LogisticRegressionLearner(
            penalty="l2", C=1.0, class_weight="balanced", max_iter=10000, random_state=0),
        "Random Forest": RandomForestLearner(
            n_estimators=300, min_samples_split=20, class_weight="balanced", random_state=0),
        "kNN": KNNLearner(n_neighbors=25, metric="euclidean", weights="uniform"),
    }


def modelos_sensibilidad():
    """Los mismos algoritmos SIN balancear las clases: muestran el efecto del desbalance."""
    return {
        "Regresion logistica sin balancear": LogisticRegressionLearner(
            penalty="l2", C=1.0, max_iter=10000, random_state=0),
        "Random Forest sin balancear": RandomForestLearner(
            n_estimators=300, min_samples_split=20, random_state=0),
    }


def metricas(resultados, indice_grande):
    g = indice_grande
    filas = []
    actual = resultados.actual.astype(int)
    for i, predicho in enumerate(resultados.predicted):
        predicho = predicho.astype(int)
        tp = int(((actual == g) & (predicho == g)).sum())
        fn = int(((actual == g) & (predicho != g)).sum())
        fp = int(((actual != g) & (predicho == g)).sum())
        tn = int(((actual != g) & (predicho != g)).sum())
        filas.append({
            "auc": float(AUC(resultados)[i]), "accuracy": float(CA(resultados)[i]),
            "f1": float(F1(resultados, target=g)[i]),
            "precision": float(Precision(resultados, target=g)[i]),
            "recall": float(Recall(resultados, target=g)[i]),
            "vp": tp, "fn": fn, "fp": fp, "vn": tn,
        })
    return filas


def imprimir(titulo, nombres, filas):
    print(f"\n{titulo}")
    print(f"  {'Modelo':36s} {'AUC':>6s} {'Accuracy':>9s} {'F1':>6s} {'Precision':>10s} {'Recall':>7s}")
    for nombre, m in zip(nombres, filas):
        print(f"  {nombre:36s} {m['auc']:6.3f} {m['accuracy']:9.3f} {m['f1']:6.3f} "
              f"{m['precision']:10.3f} {m['recall']:7.3f}")
    print("\n  Matriz de confusion (filas = real, columnas = predicho; clase 'Grande'):")
    print(f"  {'Modelo':36s} {'VP':>7s} {'FN':>7s} {'FP':>7s} {'VN':>7s}")
    for nombre, m in zip(nombres, filas):
        print(f"  {nombre:36s} {m['vp']:7,} {m['fn']:7,} {m['fp']:7,} {m['vn']:7,}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    datos = Orange.data.Table(str(DATOS))
    g = list(datos.domain.class_var.values).index("Grande")
    n_grandes = int((datos.Y == g).sum())
    base = 100 * (len(datos) - n_grandes) / len(datos)
    print(f"Datos: {len(datos):,} eventos; {n_grandes:,} grandes ({100 * n_grandes / len(datos):.2f} %).")
    print(f"Linea base (siempre 'No grande'): accuracy {base:.2f} %, recall de 'Grande' 0 %.")
    print(f"Validacion: cruzada estratificada de {PLIEGUES} pliegues, semilla {SEMILLA}.")

    cv = CrossValidation(k=PLIEGUES, random_state=SEMILLA, stratified=True)
    todo = []

    principales = modelos_principales()
    filas = metricas(cv(datos, list(principales.values())), g)
    imprimir("1. Los tres modelos (mismas condiciones)", list(principales), filas)
    todo += [("principal", n, m) for n, m in zip(principales, filas)]

    sensibles = modelos_sensibilidad()
    filas = metricas(cv(datos, list(sensibles.values())), g)
    imprimir("2. Sensibilidad al desbalance (sin balancear las clases)", list(sensibles), filas)
    todo += [("sensibilidad", n, m) for n, m in zip(sensibles, filas)]

    # Verificacion temporal: entrenar con 2010-2022 y probar en 2023-2024.
    anio = datos.get_column("anio")
    entrenamiento, prueba = datos[anio <= 2022], datos[anio >= 2023]
    prueba_g = int((prueba.Y == g).sum())
    print(f"\n3. Verificacion temporal: entrenamiento 2010-2022 ({len(entrenamiento):,} eventos, "
          f"{int((entrenamiento.Y == g).sum()):,} grandes) y prueba 2023-2024 "
          f"({len(prueba):,} eventos, {prueba_g:,} grandes = {100 * prueba_g / len(prueba):.2f} %).")
    resultados = TestOnTestData()(entrenamiento, prueba, list(principales.values()))
    filas = metricas(resultados, g)
    imprimir("   Resultados en 2023-2024", list(principales), filas)
    todo += [("temporal", n, m) for n, m in zip(principales, filas)]

    with open(SALIDA, "w", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow(["escenario", "modelo", "auc", "accuracy", "f1", "precision",
                           "recall", "vp", "fn", "fp", "vn"])
        for escenario, nombre, m in todo:
            escritor.writerow([escenario, nombre] + [round(m[k], 4) if isinstance(m[k], float) else m[k]
                                                     for k in ("auc", "accuracy", "f1", "precision",
                                                               "recall", "vp", "fn", "fp", "vn")])
    print(f"\nMetricas guardadas en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
