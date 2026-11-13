"""Genera el flujo de Orange orange/supervisado/modelos_supervisados.ows.

Construye el flujo con las propias herramientas de Orange (sin abrir la ventana): crea los
widgets, fija sus parametros, los conecta, los ejecuta con los datos y guarda el resultado.
Al abrir el .ows en Orange se ven los mismos widgets, conexiones y parametros que se
documentan en el informe.

Requiere Orange 3.40 (se ejecuta con el Python que trae Orange):
    <carpeta de Orange>\\python.exe scripts/etapa6/generar_flujo_supervisado.py

Antes hay que generar los datos: python scripts/etapa6/preparar_supervisado.py
"""

import base64
import os
import pickle
import re
import sys
import time
import warnings
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

from AnyQt.QtWidgets import QApplication  # noqa: E402

APP = QApplication([])

import orangecanvas.config as occ  # noqa: E402
import orangecanvas.registry as registro  # noqa: E402
from orangecanvas.scheme import SchemeLink, SchemeNode, SchemeTextAnnotation  # noqa: E402
from orangewidget.utils.filedialogs import RecentPath  # noqa: E402
from orangewidget.workflow.widgetsscheme import WidgetsScheme  # noqa: E402
from Orange.canvas import config as config_orange  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
FLUJO = RAIZ / "orange" / "supervisado" / "modelos_supervisados.ows"
RUTA_DATOS = "../../data/etapa6/supervisado/incendios_supervisado.tab"  # relativa al .ows

W = "Orange.widgets."
WIDGETS = {
    "file": W + "data.owfile.OWFile",
    "select": W + "data.owselectrows.OWSelectRows",
    "lr": W + "model.owlogisticregression.OWLogisticRegression",
    "rf": W + "model.owrandomforest.OWRandomForest",
    "knn": W + "model.owknn.OWKNNLearner",
    "test": W + "evaluate.owtestandscore.OWTestAndScore",
    "confusion": W + "evaluate.owconfusionmatrix.OWConfusionMatrix",
    "roc": W + "evaluate.owrocanalysis.OWROCAnalysis",
    "nomogram": W + "visualize.ownomogram.OWNomogram",
}

configuracion = config_orange.Config()
occ.set_default(configuracion)
REGISTRO = registro.WidgetRegistry()
configuracion.widget_discovery(REGISTRO).run(configuracion.widgets_entry_points())

ESQUEMA = WidgetsScheme()
ESQUEMA.set_runtime_env("basedir", str(FLUJO.parent))


def nodo(clave, titulo, posicion, **ajustes):
    """Crea un widget, fija sus parametros y lo agrega al flujo."""
    n = SchemeNode(REGISTRO.widget(WIDGETS[clave]), title=titulo, position=posicion)
    if clave == "file":
        n.properties = {"recent_paths": [RecentPath(str(RAIZ / RUTA_DATOS[6:]), "basedir", RUTA_DATOS)],
                        "source": 0}
    ESQUEMA.add_node(n)
    widget = ESQUEMA.widget_for_node(n)
    for nombre, valor in ajustes.items():
        setattr(widget, nombre, valor)
    return n, widget


def enlace(origen, canal_origen, destino, canal_destino):
    ESQUEMA.add_link(SchemeLink(origen, canal_origen, destino, canal_destino))


def nota(x, y, ancho, alto, texto):
    ESQUEMA.add_annotation(SchemeTextAnnotation((x, y, ancho, alto), texto,
                                                content_type="text/plain",
                                                font={"size": 13}))


def esperar(condicion, segundos=900, mensaje=""):
    limite = time.time() + segundos
    while time.time() < limite:
        APP.processEvents()
        if condicion():
            return True
        time.sleep(0.05)
    raise TimeoutError(mensaje or "tiempo agotado")


def main():
    # ---- Datos
    archivo, _ = nodo("file", "Incendios (clase, anio, mes, departamento, hoja)", (60, 240))

    # ---- Los tres modelos (mismos datos y misma validacion)
    lr, _ = nodo("lr", "Regresion logistica", (290, 110),
                 learner_name="Regresion logistica", penalty_type=1, C_index=61, class_weight=True)
    rf, _ = nodo("rf", "Random Forest", (290, 240),
                 learner_name="Random Forest", n_estimators=300, use_min_samples_split=True,
                 min_samples_split=20, class_weight=True, use_random_state=True)
    knn, _ = nodo("knn", "kNN", (290, 370),
                  learner_name="kNN", n_neighbors=25, metric_index=0, weight_index=0)

    # ---- 1. Comparacion principal: validacion cruzada estratificada de 10 pliegues
    prueba1, w1 = nodo("test", "1. Test and Score (validacion cruzada 10 pliegues)", (540, 240),
                       resampling=0, n_folds=3, cv_stratified=True)
    matriz, _ = nodo("confusion", "Matriz de confusion", (780, 190))
    roc, _ = nodo("roc", "Curvas ROC", (780, 300))
    nomograma, _ = nodo("nomogram", "Nomograma (regresion logistica)", (540, 90))

    # ---- 2. Verificacion temporal: entrenar con 2010-2022 y probar en 2023-2024
    hasta22, w_h22 = nodo("select", "Eventos 2010-2022 (entrenamiento)", (290, 540))
    desde23, w_d23 = nodo("select", "Eventos 2023-2024 (prueba)", (290, 650))
    prueba2, w2 = nodo("test", "2. Test and Score (entrenar 2010-2022, probar 2023-2024)", (540, 590),
                       resampling=5)

    # ---- 3. Sensibilidad al desbalance: los mismos algoritmos sin balancear las clases
    lr2, _ = nodo("lr", "Regresion logistica sin balancear", (290, 800),
                  learner_name="Regresion logistica sin balancear", penalty_type=1, C_index=61,
                  class_weight=False)
    rf2, _ = nodo("rf", "Random Forest sin balancear", (290, 910),
                  learner_name="Random Forest sin balancear", n_estimators=300,
                  use_min_samples_split=True, min_samples_split=20, class_weight=False,
                  use_random_state=True)
    prueba3, w3 = nodo("test", "3. Test and Score (sin balancear las clases)", (540, 850),
                       resampling=0, n_folds=3, cv_stratified=True)

    # ---- Conexiones
    for aprendiz in (lr, rf, knn):
        enlace(archivo, "Data", aprendiz, "Data")
        enlace(aprendiz, "Learner", prueba1, "Learner")
        enlace(aprendiz, "Learner", prueba2, "Learner")
    enlace(archivo, "Data", prueba1, "Data")
    enlace(prueba1, "Evaluation Results", matriz, "Evaluation Results")
    enlace(prueba1, "Evaluation Results", roc, "Evaluation Results")
    enlace(lr, "Model", nomograma, "Classifier")
    enlace(archivo, "Data", nomograma, "Data")
    enlace(archivo, "Data", hasta22, "Data")
    enlace(archivo, "Data", desde23, "Data")
    enlace(hasta22, "Matching Data", prueba2, "Data")
    enlace(desde23, "Matching Data", prueba2, "Test Data")
    enlace(archivo, "Data", lr2, "Data")
    enlace(archivo, "Data", rf2, "Data")
    enlace(lr2, "Learner", prueba3, "Learner")
    enlace(rf2, "Learner", prueba3, "Learner")
    enlace(archivo, "Data", prueba3, "Data")

    nota(40, 20, 380, 40, "1. COMPARACION PRINCIPAL: tres modelos, mismos datos, validacion cruzada "
                          "estratificada de 10 pliegues (semilla 42). Clase objetivo: Grande.")
    nota(40, 480, 380, 40, "2. VERIFICACION TEMPORAL: entrenar con 2010-2022 y probar en 2023-2024.")
    nota(40, 740, 380, 40, "3. SENSIBILIDAD AL DESBALANCE: los mismos algoritmos sin balancear las clases.")

    # ---- Ejecucion con los datos
    ESQUEMA.signal_manager.start()  # sin esto las senales no viajan entre widgets
    ESQUEMA.widget_for_node(archivo).load_data()  # reenvia los datos ya con las conexiones hechas
    print("Cargando datos en el widget File...")
    esperar(lambda: ESQUEMA.widget_for_node(archivo).data is not None, 120, "no cargo el archivo")
    print("  filas cargadas:", len(ESQUEMA.widget_for_node(archivo).data))

    # Orange procesa las senales en cola y espera a que termine cada Test and Score:
    # los widgets siguientes reciben los datos despues, por eso las esperas son largas.
    # Los valores van como enteros: Orange los lee con la configuracion regional del equipo
    # (en espanol la coma es el separador decimal) y "2022.0" no se interpretaria.
    for w, operador, valor in ((w_h22, 3, 2022), (w_d23, 5, 2023)):  # <= 2022, >= 2023
        esperar(lambda w=w: w.data is not None, 1200, "Select Rows sin datos")
        w.remove_all_rows()
        w.add_row(w.data.domain["anio"], operador, (valor,))
        w.conditions_changed()
        w.commit.now()
    total = len(w1.data)
    # Test and Score 2 debe recibir los datos YA filtrados (menos filas que el total).
    esperar(lambda: w2.data is not None and w2.test_data is not None
            and len(w2.data) < total and len(w2.test_data) < total, 600,
            "Test and Score 2 no recibio los datos filtrados")
    print("  entrenamiento 2010-2022:", len(w2.data), "| prueba 2023-2024:", len(w2.test_data))

    def listo(w, n):
        return len(w.learners) == n and all(s.results is not None for s in w.learners.values())

    esperar(lambda: listo(w1, 3) and listo(w2, 3) and listo(w3, 2), 1800, "evaluacion no termino")
    for w in (w1, w2, w3):
        w.class_selection = "Grande"
    APP.processEvents()

    # ---- Resultados de los widgets (para compararlos con evaluar_supervisado.py)
    from Orange.evaluation import AUC, CA, F1, Precision, Recall
    print("\nResultados calculados por los widgets (clase objetivo: Grande)")
    for titulo, w in (("1. Validacion cruzada", w1), ("2. 2010-2022 -> 2023-2024", w2),
                      ("3. Sin balancear", w3)):
        print(f"\n{titulo}")
        for slot in w.learners.values():
            r = slot.results.value
            g = list(r.domain.class_var.values).index("Grande")
            print(f"  {slot.learner.name:36s} AUC {float(AUC(r)[0]):.3f} | CA {float(CA(r)[0]):.3f} | "
                  f"F1 {float(F1(r, target=g)[0]):.3f} | Prec {float(Precision(r, target=g)[0]):.3f} | "
                  f"Rec {float(Recall(r, target=g)[0]):.3f}")

    # ---- Guardar (la ruta absoluta que guarda el widget File se quita despues de escribir)
    ESQUEMA.sync_node_properties() if hasattr(ESQUEMA, "sync_node_properties") else None
    ESQUEMA.title = "Etapa 6 - Modelos supervisados: incendio grande (mas de 100 ha)"
    ESQUEMA.description = ("Tres modelos (regresion logistica, Random Forest y kNN) evaluados con validacion "
                           "cruzada estratificada, verificacion temporal y sensibilidad al desbalance.")
    FLUJO.parent.mkdir(parents=True, exist_ok=True)
    with open(FLUJO, "wb") as f:
        from orangecanvas.scheme.readwrite import scheme_to_ows_stream
        scheme_to_ows_stream(ESQUEMA, f, pretty=True, pickle_fallback=True)
    limpiar_rutas_absolutas(FLUJO)
    print(f"\nFlujo guardado en {FLUJO.relative_to(RAIZ)}")


PATRON_PROPIEDADES = re.compile(r'(<properties node_id="\d+" format="pickle">)(.*?)(</properties>)', re.S)
PATRON_RUTA_ABSOLUTA = re.compile(r"[A-Za-z]:[\\/]")


def limpiar_rutas_absolutas(ruta):
    """Deja la ruta del archivo de datos en el .ows relativa a la carpeta del flujo.

    El widget File guarda la ruta absoluta del equipo y, si el archivo no esta dentro de la
    carpeta del flujo (aqui esta en data/, fuera de orange/), no guarda ninguna ruta relativa.
    Esta funcion calcula la relativa (prefijo "basedir") y vacia la absoluta, de modo que
    Orange encuentra el archivo en cualquier equipo. Despues comprueba que no quede ninguna
    ruta de unidad (C:\\...) en el archivo y lanza un error si queda alguna.
    """
    def quitar(objeto):
        if isinstance(objeto, RecentPath):
            if objeto.prefix is None and objeto.abspath:
                if not os.path.exists(objeto.abspath):
                    raise RuntimeError(
                        f"La ruta {objeto.abspath} no existe en este equipo: el flujo debe "
                        "limpiarse en el equipo donde se guardo, con el repositorio en su sitio.")
                relativa = os.path.relpath(objeto.abspath, ruta.parent).replace("\\", "/")
                objeto.prefix, objeto.relpath = "basedir", relativa
            objeto.abspath = ""
            return 1
        if isinstance(objeto, dict):
            return sum(quitar(v) for v in objeto.values())
        if isinstance(objeto, (list, tuple)):
            return sum(quitar(v) for v in objeto)
        return 0

    cambios = 0

    def reemplazar(m):
        nonlocal cambios
        objeto = pickle.loads(base64.b64decode(m.group(2)))
        n = quitar(objeto)
        if not n:
            return m.group(0)
        cambios += n
        nuevo = base64.encodebytes(pickle.dumps(objeto, protocol=4)).decode("ascii")
        return m.group(1) + nuevo + m.group(3)

    texto = ruta.read_bytes().decode("utf-8")
    ruta.write_bytes(PATRON_PROPIEDADES.sub(reemplazar, texto).encode("utf-8"))
    restantes = []
    texto = ruta.read_bytes().decode("utf-8")
    for m in PATRON_PROPIEDADES.finditer(texto):
        restantes += PATRON_RUTA_ABSOLUTA.findall(repr(pickle.loads(base64.b64decode(m.group(2)))))
    restantes += PATRON_RUTA_ABSOLUTA.findall(PATRON_PROPIEDADES.sub("", texto))
    if restantes:
        raise RuntimeError(f"Quedan {len(restantes)} rutas absolutas en {ruta.name}")
    print(f"Rutas absolutas quitadas: {cambios}. Verificado: ninguna ruta de unidad en {ruta.name}.")


if __name__ == "__main__":
    if "--limpiar-rutas" in sys.argv:
        # Solo limpia un .ows existente, sin volver a calcular. Sin argumento limpia el de esta
        # seccion; con una ruta limpia ese archivo: --limpiar-rutas orange/otra/flujo.ows
        posicion = sys.argv.index("--limpiar-rutas") + 1
        limpiar_rutas_absolutas(Path(sys.argv[posicion]).resolve() if len(sys.argv) > posicion else FLUJO)
    else:
        main()
