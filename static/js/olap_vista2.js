/* Vista 2: tiempo y tamano. Usa solo la API de olap.js. */
(function () {
  "use strict";

  const el = (id) => document.getElementById(id);
  const selectMedida = el("v2-medida");
  const GRANDE = "> 100 ha";
  const NOMBRES = {
    eventos: "eventos",
    eventos_con_area: "eventos con área",
    pct_grandes: "% de eventos grandes",
    ha_por_evento: "hectáreas por evento",
  };
  const EJEMPLOS = {
    inicial: { medida: "eventos", filas: "tiempo.anio", columnas: "tamano.clase", filtros: {} },
    slice2024: {
      medida: "eventos",
      filas: "tiempo.trimestre",
      columnas: "tamano.clase",
      filtros: { "tiempo.anio": ["2024"] },
    },
    equivalentes: { medida: "pct_grandes", filas: "tiempo.anio", columnas: "tiempo.temporada", filtros: {} },
    entidad2024: {
      medida: "pct_grandes",
      filas: "fuente.entidad",
      columnas: "tiempo.temporada",
      filtros: { "tiempo.anio": ["2024"] },
    },
  };
  const COLORES = ["#ea580c", "#38bdf8", "#a3a3a3", "#facc15"];
  let barra;
  let catalogo;
  let turno = 0;

  const esPeriodoValido = (etiqueta) => !/sin/i.test(String(etiqueta));

  function textoSeleccion(spec) {
    const partes = Object.entries(spec.filtros || {}).map(
      ([nivel, valores]) => `${catalogo.niveles[nivel].etiqueta}: ${valores.join(", ")}`
    );
    return partes.length ? `Con los filtros en ${partes.join("; ")}` : "Sin filtros";
  }

  /* Los indicadores se recalculan desde partes aditivas (eventos, eventos con area y hectareas
     por clase de tamano); nunca se promedian porcentajes de grupos. */
  function pintarIndicadores(resultado) {
    const zona = el("v2-indicadores");
    const filas = resultado.filas;
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
      detalle: `De ${Olap.formato(eventos, "eventos")} eventos. Sin área (fuera de los porcentajes): ${Olap.formato(eventos - conArea, "eventos")}.`,
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

  /* Grafica 1: una linea por temporada, eje x = anio (periodos equivalentes). */
  function configuracionLineas(resultado) {
    const filas = resultado.filas.filter((f) => esPeriodoValido(f.fila) && esPeriodoValido(f.col));
    const anios = [...new Set(filas.map((f) => f.fila))];
    const temporadas = [...new Set(filas.map((f) => f.col))].sort();
    const celdas = new Map(filas.map((f) => [`${f.fila}|${f.col}`, f]));
    return {
      type: "line",
      data: {
        labels: anios,
        datasets: temporadas.map((t, i) => ({
          label: t,
          data: anios.map((a) => celdas.get(`${a}|${t}`)?.valor ?? null),
          denominadores: anios.map((a) => celdas.get(`${a}|${t}`)?.eventos_con_area ?? null),
          borderColor: COLORES[i % COLORES.length],
          backgroundColor: COLORES[i % COLORES.length],
          tension: 0.2,
          spanGaps: true,
        })),
      },
      options: {
        responsive: true,
        plugins: {
          legend: { labels: { color: "#cbd5e1" } },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: ${Olap.formato(ctx.raw, "%")} (base: ${Olap.formato(ctx.dataset.denominadores[ctx.dataIndex], "eventos")} eventos con área)`,
            },
          },
        },
        scales: escalas("%"),
      },
    };
  }

  function configuracionBarras(resultado, unidad) {
    const filas = resultado.filas.filter((f) => esPeriodoValido(f.fila));
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

  function mayorDe(filas) {
    return filas.reduce((a, b) => ((b.valor ?? -1) > (a?.valor ?? -1) ? b : a), null);
  }

  function interpretarLineas(resultado, seleccion) {
    const filas = resultado.filas.filter((f) => esPeriodoValido(f.fila) && f.valor !== null);
    const t1 = new Map(filas.filter((f) => String(f.col).startsWith("1.")).map((f) => [f.fila, f]));
    const t3 = new Map(filas.filter((f) => String(f.col).startsWith("2.")).map((f) => [f.fila, f]));
    const comunes = [...t1.keys()].filter((a) => t3.has(a));
    if (!comunes.length) return `${seleccion}, no hay años con datos en enero-marzo y julio-septiembre a la vez.`;
    const invertidos = comunes.filter((a) => t3.get(a).valor > t1.get(a).valor);
    const lista = invertidos.length ? ` Julio-septiembre supera a enero-marzo en: ${invertidos.join(", ")}.` : "";
    return `${seleccion}, enero-marzo tiene un % de grandes igual o mayor que julio-septiembre en ${comunes.length - invertidos.length} de ${comunes.length} años con datos en ambas temporadas.${lista}`;
  }

  function avisoMatriz(spec) {
    const aviso = el("v2-aviso");
    const conTamano = spec.filas === "tamano.clase" || spec.columnas === "tamano.clase";
    if (conTamano && spec.medida === "pct_grandes") {
      aviso.textContent = "Con la clase de tamaño en la matriz, el % de grandes de cada celda solo puede ser 0 % o 100 %. Para leer la proporción, usa eventos o cambia el eje de tamaño por temporada o entidad.";
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
    el("v2-error").classList.add("hidden");
    avisoMatriz(spec);

    /* Con un filtro de tiempo (por ejemplo, slice anio = 2024) las graficas bajan a trimestre. */
    const conFiltroTiempo = Object.keys(spec.filtros || {}).some((n) => n.startsWith("tiempo."));
    const nivelGraficas = conFiltroTiempo ? "tiempo.trimestre" : "tiempo.anio";
    el("v2-titulo-1").textContent = conFiltroTiempo
      ? "% de eventos grandes por trimestre"
      : "% de eventos grandes por año y temporada";
    el("v2-titulo-2").textContent = conFiltroTiempo
      ? "Hectáreas por evento según el trimestre"
      : "Hectáreas por evento según el año";

    try {
      const [matriz, indicadores, lineas, barras] = await Promise.all([
        Olap.consultar(spec),
        Olap.consultar({ medida: "hectareas", filas: "tamano.clase", filtros: spec.filtros }),
        conFiltroTiempo
          ? Olap.consultar({ medida: "pct_grandes", filas: "tiempo.trimestre", filtros: spec.filtros })
          : Olap.consultar({ medida: "pct_grandes", filas: "tiempo.anio", columnas: "tiempo.temporada", filtros: spec.filtros }),
        Olap.consultar({ medida: "ha_por_evento", filas: nivelGraficas, filtros: spec.filtros }),
      ]);
      if (actual !== turno) return;

      barra.registrarConsulta(matriz);
      pintarIndicadores(indicadores);
      await Olap.renderMatriz(el("v2-matriz"), matriz, {
        medida,
        etiquetaFila: catalogo.niveles[spec.filas].etiqueta,
        onClickFila: (miembro) => barra.drillMiembro(miembro),
      });
      Olap.grafica(el("v2-grafica-1"), conFiltroTiempo ? configuracionBarras(lineas, "%") : configuracionLineas(lineas));
      Olap.grafica(el("v2-grafica-2"), configuracionBarras(barras, "ha/evento"));

      const seleccion = textoSeleccion(spec);
      if (conFiltroTiempo) {
        const t = mayorDe(lineas.filas.filter((f) => esPeriodoValido(f.fila)));
        el("v2-interp-1").textContent = t
          ? `${seleccion}, el trimestre con mayor % de grandes es ${t.fila}: ${Olap.formato(t.valor, "%")} (base: ${Olap.formato(t.eventos_con_area, "eventos")} eventos con área). Cada porcentaje se recalcula con su propio denominador; no se suman entre trimestres.`
          : `${seleccion}, no hay datos para esta gráfica.`;
      } else {
        el("v2-interp-1").textContent = interpretarLineas(lineas, seleccion);
      }
      const b = mayorDe(barras.filas.filter((f) => esPeriodoValido(f.fila)));
      el("v2-interp-2").textContent = b
        ? `${seleccion}, el mayor promedio está en ${b.fila}: ${Olap.formato(b.valor, "ha/evento")}, con ${Olap.formato(b.eventos_con_area, "eventos")} eventos con área. Un periodo con pocos eventos y algunos incendios enormes eleva mucho el promedio.`
        : `${seleccion}, no hay datos para esta gráfica.`;
      const m = mayorDe(matriz.filas.filter((f) => esPeriodoValido(f.fila)));
      el("v2-interp-3").textContent = m
        ? `${seleccion}, la celda con mayor ${NOMBRES[medida]} es ${m.fila}${m.col !== null ? ` / ${m.col}` : ""}: ${Olap.formato(m.valor, unidad)}, con ${Olap.formato(m.eventos, "eventos")} eventos y ${Olap.formato(m.eventos_con_area, "eventos")} con área.`
        : `${seleccion}, no hay datos para esta matriz.`;
    } catch (error) {
      if (actual !== turno) return;
      el("v2-error").textContent = `No se pudo ejecutar la consulta: ${error.message}`;
      el("v2-error").classList.remove("hidden");
    }
  }

  async function iniciar() {
    try {
      catalogo = await Olap.catalogo();
      barra = await Olap.crearControles(el("v2-controles"), {
        medida: selectMedida.value,
        filas: "tiempo.anio",
        columnas: "tamano.clase",
        filtros: ["territorio.region", "fuente.hoja"],
        niveles: [
          "tiempo.anio", "tiempo.trimestre", "tiempo.mes", "tiempo.temporada",
          "tamano.clase", "fuente.hoja", "fuente.entidad",
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
      el("v2-error").textContent = `No se pudo iniciar la vista: ${error.message}`;
      el("v2-error").classList.remove("hidden");
    }
  }

  iniciar();
})();
