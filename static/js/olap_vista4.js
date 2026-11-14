/* Vista 4: causa y tamano. Usa solo la API de olap.js. */
(function () {
  "use strict";

  const el = (id) => document.getElementById(id);
  const selectMedida = el("v4-medida");
  const GRANDE = "> 100 ha";
  const NOMBRES = {
    eventos: "eventos",
    hectareas: "hectáreas",
    ha_por_evento: "hectáreas por evento",
    pct_grandes: "% de eventos grandes",
  };
  const EJEMPLOS = {
    inicial: { medida: "eventos", filas: "causa.causa", columnas: "tamano.clase", filtros: {} },
    sliceOrinoquia: {
      medida: "eventos",
      filas: "causa.causa",
      columnas: "tamano.clase",
      filtros: { "territorio.region": ["Orinoquia"] },
    },
    dice: {
      medida: "hectareas",
      filas: "causa.causa",
      columnas: "territorio.region",
      filtros: {
        "causa.causa": ["Intencional", "Otra"],
        "territorio.region": ["Orinoquia", "Andina"],
      },
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

  function mayorDe(filas) {
    return filas.reduce((a, b) => ((b.valor ?? -1) > (a?.valor ?? -1) ? b : a), null);
  }

  /* Los indicadores salen de partes aditivas (eventos, eventos con area y hectareas por
     clase de tamano); el % de grandes y las ha/evento se recalculan aqui, nunca se suman
     entre causas. */
  function pintarIndicadores(porTamano) {
    const zona = el("v4-indicadores");
    const filas = porTamano.filas;
    const hectareas = filas.reduce((s, f) => s + (f.valor || 0), 0);
    const eventos = filas.reduce((s, f) => s + f.eventos, 0);
    const conArea = filas.reduce((s, f) => s + f.eventos_con_area, 0);
    const grandes = filas.filter((f) => f.fila === GRANDE).reduce((s, f) => s + f.eventos, 0);
    const pct = conArea > 0 ? (100 * grandes) / conArea : null;
    const haEvento = conArea > 0 ? hectareas / conArea : null;

    zona.replaceChildren();
    Olap.tarjeta(zona, {
      titulo: "% de eventos grandes (> 100 ha)",
      valor: Olap.formato(pct, "%"),
      detalle: `${Olap.formato(grandes, "eventos")} de ${Olap.formato(conArea, "eventos")} eventos con área.`,
    });
    Olap.tarjeta(zona, {
      titulo: "Hectáreas por evento",
      valor: Olap.formato(haEvento, "ha"),
      detalle: `${Olap.formato(hectareas, "ha")} / ${Olap.formato(conArea, "eventos")} eventos con área.`,
    });
    Olap.tarjeta(zona, {
      titulo: "Eventos con área",
      valor: Olap.formato(conArea, "eventos"),
      detalle: `De ${Olap.formato(eventos, "eventos")} eventos. "Sin causa registrada" no significa "sin causa": es un dato faltante.`,
    });
  }

  function escalas(unidad) {
    return {
      x: { ticks: { color: "#cbd5e1" }, grid: { color: "rgba(255,255,255,0.08)" } },
      y: {
        beginAtZero: true,
        title: { display: true, text: unidad, color: "#94a3b8" },
        ticks: { color: "#cbd5e1" },
        grid: { color: "rgba(255,255,255,0.08)" },
      },
    };
  }

  function configuracionBarras(resultado, unidad) {
    const filas = resultado.filas;
    return {
      type: "bar",
      data: {
        labels: filas.map((f) => f.fila),
        datasets: [{
          label: unidad,
          data: filas.map((f) => f.valor),
          backgroundColor: "#ea580c",
          borderColor: "#fb923c",
        }],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `${Olap.formato(ctx.raw, unidad)} (base: ${Olap.formato(filas[ctx.dataIndex].eventos_con_area, "eventos")} eventos con área)`,
            },
          },
        },
        scales: escalas(unidad),
      },
    };
  }

  /* Si tamano.clase queda en filas o columnas, pct_grandes solo puede dar 0% o 100%
     en cada celda porque la condicion de la medida ya coincide con el grupo. */
  function avisoMatriz(spec) {
    const aviso = el("v4-aviso");
    const conTamano = spec.filas === "tamano.clase" || spec.columnas === "tamano.clase";
    if (conTamano && spec.medida === "pct_grandes") {
      aviso.textContent = "Con la clase de tamaño en la matriz, el % de grandes de cada celda solo puede ser 0 % o 100 %. Para leer la proporción, usa eventos, hectáreas o hectáreas por evento.";
      aviso.classList.remove("hidden");
    } else {
      aviso.classList.add("hidden");
    }
  }

  async function pintar(base) {
    const actual = ++turno;
    const medida = selectMedida.value;
    const spec = { ...base, medida };
    const unidad = catalogo.medidas[medida].unidad;
    el("v4-error").classList.add("hidden");
    avisoMatriz(spec);

    try {
      const [matriz, porTamano, pctCausa, haCausa] = await Promise.all([
        Olap.consultar(spec),
        Olap.consultar({ medida: "hectareas", filas: "tamano.clase", filtros: spec.filtros }),
        Olap.consultar({ medida: "pct_grandes", filas: "causa.causa", filtros: spec.filtros, orden: "valor_desc" }),
        Olap.consultar({ medida: "ha_por_evento", filas: "causa.causa", filtros: spec.filtros, orden: "valor_desc" }),
      ]);
      if (actual !== turno) return;

      barra.registrarConsulta(matriz);
      pintarIndicadores(porTamano);
      await Olap.renderMatriz(el("v4-matriz"), matriz, {
        medida,
        etiquetaFila: catalogo.niveles[spec.filas].etiqueta,
        onClickFila: (miembro) => barra.drillMiembro(miembro),
      });
      Olap.grafica(el("v4-grafica-1"), configuracionBarras(pctCausa, "%"));
      Olap.grafica(el("v4-grafica-2"), configuracionBarras(haCausa, "ha/evento"));

      const seleccion = textoSeleccion(spec);
      const pMax = mayorDe(pctCausa.filas.filter((f) => f.eventos_con_area >= 10));
      el("v4-interp-1").textContent = pMax
        ? `${seleccion}, la causa con mayor % de eventos grandes (entre las que tienen al menos 10 eventos con área) es "${pMax.fila}": ${Olap.formato(pMax.valor, "%")} (${Olap.formato(pMax.eventos, "eventos")} eventos, ${Olap.formato(pMax.eventos_con_area, "eventos")} con área). El porcentaje se recalcula para cada causa y no se suma con las demás.`
        : `${seleccion}, no hay causas con al menos 10 eventos con área para esta comparación.`;
      const hMax = mayorDe(haCausa.filas.filter((f) => f.eventos_con_area >= 10));
      el("v4-interp-2").textContent = hMax
        ? `${seleccion}, la causa con mayor promedio de hectáreas por evento es "${hMax.fila}": ${Olap.formato(hMax.valor, "ha/evento")}, con ${Olap.formato(hMax.eventos_con_area, "eventos")} eventos con área. Un grupo con pocos eventos y un incendio enorme eleva mucho este promedio.`
        : `${seleccion}, no hay causas con al menos 10 eventos con área para esta comparación.`;
      const m = mayorDe(matriz.filas);
      el("v4-interp-3").textContent = m
        ? `${seleccion}, la celda con mayor ${NOMBRES[medida]} es "${m.fila}"${m.col !== null ? ` / ${m.col}` : ""}: ${Olap.formato(m.valor, unidad)}, con ${Olap.formato(m.eventos, "eventos")} eventos y ${Olap.formato(m.eventos_con_area, "eventos")} con área. Las celdas con pocos eventos (por ejemplo, Accidental en Orinoquia tiene 1) no deben leerse como una tendencia.`
        : `${seleccion}, no hay datos para esta matriz.`;
    } catch (error) {
      if (actual !== turno) return;
      el("v4-error").textContent = `No se pudo ejecutar la consulta: ${error.message}`;
      el("v4-error").classList.remove("hidden");
    }
  }

  async function iniciar() {
    try {
      catalogo = await Olap.catalogo();
      barra = await Olap.crearControles(el("v4-controles"), {
        medida: selectMedida.value,
        filas: "causa.causa",
        columnas: "tamano.clase",
        filtros: ["territorio.region", "tiempo.anio"],
        niveles: [
          "causa.registro", "causa.causa", "tamano.clase",
          "territorio.region", "territorio.departamento", "tiempo.anio",
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
      el("v4-error").textContent = `No se pudo iniciar la vista: ${error.message}`;
      el("v4-error").classList.remove("hidden");
    }
  }

  iniciar();
})();
