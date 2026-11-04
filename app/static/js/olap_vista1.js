/* Vista 1: territorio y tiempo. Usa solo la API de olap.js. */
(function () {
  "use strict";

  const el = (id) => document.getElementById(id);
  const selectMedida = el("v1-medida");
  const NOMBRES = {
    hectareas: "hectáreas",
    eventos: "eventos",
    pct_total: "participación de eventos",
  };
  const EJEMPLOS = {
    regiones: { medida: "hectareas", filas: "territorio.region", columnas: null, filtros: {} },
    temporadas: { medida: "hectareas", filas: "territorio.region", columnas: "tiempo.temporada", filtros: {} },
    orinoquia: {
      medida: "hectareas",
      filas: "tiempo.trimestre",
      columnas: null,
      filtros: { "territorio.region": ["Orinoquia"] },
    },
  };
  let barra;
  let catalogo;
  let turno = 0;

  function textoSeleccion(spec) {
    const partes = Object.entries(spec.filtros || {}).map(
      ([nivel, valores]) => `${catalogo.niveles[nivel].etiqueta}: ${valores.join(", ")}`
    );
    return partes.length ? `Con los filtros en ${partes.join("; ")}` : "Sin filtros";
  }

  function pintarIndicadores(resultado) {
    const zona = el("v1-indicadores");
    const filas = resultado.filas;
    const hectareas = filas.reduce((suma, f) => suma + (f.valor || 0), 0);
    const eventos = filas.reduce((suma, f) => suma + f.eventos, 0);
    const conArea = filas.reduce((suma, f) => suma + f.eventos_con_area, 0);
    const mayor = filas.reduce((a, b) => ((b.valor || 0) > (a?.valor || 0) ? b : a), null);
    const porcentaje = mayor && hectareas > 0 ? (100 * mayor.valor) / hectareas : null;

    zona.replaceChildren();
    Olap.tarjeta(zona, {
      titulo: "Hectáreas",
      valor: Olap.formato(hectareas, "ha"),
      detalle: `Suma de ${Olap.formato(conArea, "eventos")} eventos con área.`,
    });
    Olap.tarjeta(zona, {
      titulo: "Eventos",
      valor: Olap.formato(eventos, "eventos"),
      detalle: `${Olap.formato(eventos - conArea, "eventos")} sin área registrada.`,
    });
    Olap.tarjeta(zona, {
      titulo: "Grupo con más hectáreas",
      valor: mayor ? mayor.fila : "Sin dato",
      detalle: porcentaje === null
        ? "No hay hectáreas en esta selección."
        : `${Olap.formato(porcentaje, "%")} de ${Olap.formato(hectareas, "ha")} de la selección.`,
    });
  }

  function configuracion(tipo, resultado, unidad, horizontal) {
    return {
      type: tipo,
      data: {
        labels: resultado.filas.map((f) => f.fila),
        datasets: [{
          label: unidad,
          data: resultado.filas.map((f) => f.valor),
          backgroundColor: "#ea580c",
          borderColor: "#fb923c",
          tension: 0.2,
        }],
      },
      options: {
        indexAxis: horizontal ? "y" : "x",
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: "#cbd5e1" }, grid: { color: "rgba(255,255,255,0.08)" } },
          y: { ticks: { color: "#cbd5e1" }, grid: { color: "rgba(255,255,255,0.08)" } },
        },
      },
    };
  }

  function mayorDe(filas) {
    return filas.reduce((a, b) => ((b.valor || 0) > (a?.valor || 0) ? b : a), null);
  }

  async function pintar(base) {
    const actual = ++turno;
    const medida = selectMedida.value;
    const spec = { ...base, medida };
    const unidad = catalogo.medidas[medida].unidad;
    const ejeDos = spec.columnas || (spec.filas.startsWith("tiempo") ? "territorio.region" : "tiempo.anio");
    el("v1-error").classList.add("hidden");

    try {
      const [matriz, indicadores, grupos, distribucion] = await Promise.all([
        Olap.consultar(spec),
        Olap.consultar({ medida: "hectareas", filas: spec.filas, filtros: spec.filtros }),
        Olap.consultar({ medida, filas: spec.filas, filtros: spec.filtros, orden: "valor_desc", limite: 12 }),
        Olap.consultar({
          medida,
          filas: ejeDos,
          filtros: spec.filtros,
          orden: ejeDos.startsWith("tiempo") ? "etiqueta" : "valor_desc",
          limite: ejeDos.startsWith("tiempo") ? 500 : 12,
        }),
      ]);
      if (actual !== turno) return;

      barra.registrarConsulta(matriz);
      pintarIndicadores(indicadores);
      await Olap.renderMatriz(el("v1-matriz"), matriz, {
        medida,
        etiquetaFila: catalogo.niveles[spec.filas].etiqueta,
        onClickFila: (miembro) => barra.drillMiembro(miembro),
      });
      Olap.grafica(el("v1-grafica-1"), configuracion("bar", grupos, unidad, true));
      Olap.grafica(el("v1-grafica-2"), configuracion(ejeDos.startsWith("tiempo") ? "line" : "bar", distribucion, unidad, false));

      const seleccion = textoSeleccion(spec);
      const nombre = NOMBRES[medida];
      const g = mayorDe(grupos.filas);
      const d = mayorDe(distribucion.filas);
      const m = mayorDe(matriz.filas);
      el("v1-interp-1").textContent = g
        ? `${seleccion}, el mayor valor de ${nombre} está en ${g.fila}: ${Olap.formato(g.valor, unidad)}. La gráfica muestra hasta 12 grupos.`
        : `${seleccion}, no hay datos para esta gráfica.`;
      el("v1-interp-2").textContent = d
        ? `${seleccion}, en ${catalogo.niveles[ejeDos].etiqueta.toLowerCase()} el mayor valor de ${nombre} está en ${d.fila}: ${Olap.formato(d.valor, unidad)}.`
        : `${seleccion}, no hay datos para esta gráfica.`;
      el("v1-interp-3").textContent = m
        ? `${seleccion}, la celda con mayor ${nombre} es ${m.fila}${m.col !== null ? ` / ${m.col}` : ""}: ${Olap.formato(m.valor, unidad)}, con ${Olap.formato(m.eventos, "eventos")} eventos y ${Olap.formato(m.eventos_con_area, "eventos")} con área.`
        : `${seleccion}, no hay datos para esta matriz.`;
    } catch (error) {
      if (actual !== turno) return;
      el("v1-error").textContent = `No se pudo ejecutar la consulta: ${error.message}`;
      el("v1-error").classList.remove("hidden");
    }
  }

  async function iniciar() {
    try {
      catalogo = await Olap.catalogo();
      barra = await Olap.crearControles(el("v1-controles"), {
        medida: selectMedida.value,
        filas: "territorio.region",
        columnas: "tiempo.trimestre",
        filtros: ["tamano.clase", "fuente.hoja"],
        niveles: [
          "territorio.region", "territorio.departamento", "territorio.municipio",
          "tiempo.anio", "tiempo.trimestre", "tiempo.mes", "tiempo.temporada",
        ],
        onCambio: pintar,
      });
      selectMedida.addEventListener("change", () => pintar(barra.obtenerSpec()));
      document.querySelectorAll("[data-ejemplo]").forEach((boton) => {
        boton.addEventListener("click", () => {
          const ejemplo = EJEMPLOS[boton.dataset.ejemplo];
          selectMedida.value = ejemplo.medida;
          barra.aplicar(ejemplo);
        });
      });
      await pintar(barra.obtenerSpec());
    } catch (error) {
      el("v1-error").textContent = `No se pudo iniciar la vista: ${error.message}`;
      el("v1-error").classList.remove("hidden");
    }
  }

  iniciar();
})();