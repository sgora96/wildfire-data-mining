/* Vista 3: cobertura y territorio. Usa solo la API de olap.js. */
(function () {
  "use strict";

  const el = (id) => document.getElementById(id);
  const selectMedida = el("v3-medida");
  const NOMBRES = {
    hectareas: "hectáreas",
    eventos: "eventos",
    pct_total: "participación de eventos",
  };
  const SIN_COBERTURA = "No informada";
  const ANIOS_HASTA_2020 = Array.from({ length: 11 }, (_, i) => String(2010 + i));
  const EJEMPLOS = {
    grupos: { medida: "hectareas", filas: "cobertura.grupo", columnas: "territorio.region", filtros: {} },
    tipos: { medida: "hectareas", filas: "cobertura.tipo", columnas: "territorio.region", filtros: {} },
    hasta2020: {
      medida: "eventos",
      filas: "cobertura.grupo",
      columnas: "territorio.region",
      filtros: { "tiempo.anio": ANIOS_HASTA_2020 },
    },
    dice: {
      medida: "hectareas",
      filas: "cobertura.tipo",
      columnas: "territorio.region",
      filtros: {
        "territorio.region": ["Orinoquia", "Andina"],
        "cobertura.grupo": ["Bosques"],
        "tiempo.anio": ANIOS_HASTA_2020,
      },
    },
  };
  let barra;
  let catalogo;
  let turno = 0;

  function resumirValores(nivel, valores) {
    if (nivel === "tiempo.anio") {
      const numeros = valores.map(Number).sort((a, b) => a - b);
      const seguidos = numeros.every((n, i) => i === 0 || n === numeros[i - 1] + 1);
      if (numeros.length > 3 && seguidos) return `${numeros[0]} a ${numeros[numeros.length - 1]}`;
    }
    return valores.join(", ");
  }

  function textoSeleccion(filtros) {
    const partes = Object.entries(filtros || {}).map(
      ([nivel, valores]) => `${catalogo.niveles[nivel].etiqueta}: ${resumirValores(nivel, valores)}`
    );
    return partes.length ? `Con los filtros en ${partes.join("; ")}` : "Sin filtros";
  }

  /* El denominador del porcentaje de cobertura informada es el total de eventos, por eso
     la gráfica de regiones no aplica los filtros de cobertura. */
  function sinFiltrosDeCobertura(filtros) {
    const copia = { ...filtros };
    delete copia["cobertura.grupo"];
    delete copia["cobertura.tipo"];
    return copia;
  }

  function porcentaje(parte, total) {
    return total > 0 ? (100 * parte) / total : null;
  }

  function pintarIndicadores(resultado) {
    const zona = el("v3-indicadores");
    const filas = resultado.filas;
    const hectareas = filas.reduce((suma, f) => suma + (f.valor || 0), 0);
    const eventos = filas.reduce((suma, f) => suma + f.eventos, 0);
    const sin = filas.find((f) => f.fila === SIN_COBERTURA);
    const hectareasSin = sin ? sin.valor || 0 : 0;
    const eventosSin = sin ? sin.eventos : 0;
    const hectareasCon = hectareas - hectareasSin;
    const eventosCon = eventos - eventosSin;
    const pctHectareasCon = porcentaje(hectareasCon, hectareas);
    const pctHectareasSin = porcentaje(hectareasSin, hectareas);
    const pctEventosCon = porcentaje(eventosCon, eventos);

    zona.replaceChildren();
    Olap.tarjeta(zona, {
      titulo: "Hectáreas con cobertura informada",
      valor: Olap.formato(hectareasCon, "ha"),
      detalle: pctHectareasCon === null
        ? "No hay hectáreas en esta selección."
        : `${Olap.formato(pctHectareasCon, "%")} de ${Olap.formato(hectareas, "ha")} de la selección.`,
    });
    Olap.tarjeta(zona, {
      titulo: "Eventos con cobertura informada",
      valor: pctEventosCon === null ? "Sin dato" : Olap.formato(pctEventosCon, "%"),
      detalle: `${Olap.formato(eventosCon, "eventos")} de ${Olap.formato(eventos, "eventos")} eventos de la selección.`,
    });
    Olap.tarjeta(zona, {
      titulo: "Hectáreas sin cobertura informada",
      valor: Olap.formato(hectareasSin, "ha"),
      detalle: pctHectareasSin === null
        ? "No hay hectáreas en esta selección."
        : `${Olap.formato(pctHectareasSin, "%")} de ${Olap.formato(hectareas, "ha")}; ${Olap.formato(eventosSin, "eventos")} eventos.`,
    });
  }

  const EJES = {
    x: { ticks: { color: "#cbd5e1" }, grid: { color: "rgba(255,255,255,0.08)" } },
    y: { ticks: { color: "#cbd5e1" }, grid: { color: "rgba(255,255,255,0.08)" } },
  };

  function configuracionValores(resultado, unidad) {
    return {
      type: "bar",
      data: {
        labels: resultado.filas.map((f) => f.fila),
        datasets: [{
          label: unidad,
          data: resultado.filas.map((f) => f.valor),
          backgroundColor: "#ea580c",
          borderColor: "#fb923c",
        }],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { x: EJES.x, y: { ...EJES.y, ticks: { ...EJES.y.ticks, autoSkip: false } } },
      },
    };
  }

  function configuracionPorcentajes(regiones) {
    return {
      type: "bar",
      data: {
        labels: regiones.map((r) => r.region),
        datasets: [{
          label: "% de eventos con cobertura informada",
          data: regiones.map((r) => r.pct),
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
              label: (ctx) => {
                const r = regiones[ctx.dataIndex];
                return `${Olap.formato(r.pct, "%")} (${Olap.formato(r.informados, "eventos")} de ${Olap.formato(r.total, "eventos")} eventos)`;
              },
            },
          },
        },
        scales: { x: EJES.x, y: { ...EJES.y, min: 0, max: 100 } },
      },
    };
  }

  function regionesInformadas(resultado) {
    const mapa = new Map();
    resultado.filas.forEach((f) => {
      const r = mapa.get(f.fila) || { region: f.fila, total: 0, informados: 0 };
      r.total += f.eventos;
      if (f.col !== SIN_COBERTURA) r.informados += f.eventos;
      mapa.set(f.fila, r);
    });
    return [...mapa.values()]
      .map((r) => ({ ...r, pct: porcentaje(r.informados, r.total) }))
      .filter((r) => r.pct !== null)
      .sort((a, b) => b.pct - a.pct);
  }

  function mayorDe(filas) {
    return filas.reduce((a, b) => ((b.valor || 0) > (a?.valor || 0) ? b : a), null);
  }

  async function pintar(base) {
    const actual = ++turno;
    const medida = selectMedida.value;
    const spec = { ...base, medida };
    const unidad = catalogo.medidas[medida].unidad;
    const filtrosRegion = sinFiltrosDeCobertura(spec.filtros || {});
    el("v3-error").classList.add("hidden");

    try {
      const [matriz, indicadores, grupos, regiones] = await Promise.all([
        Olap.consultar(spec),
        Olap.consultar({ medida: "hectareas", filas: "cobertura.grupo", filtros: spec.filtros }),
        Olap.consultar({ medida, filas: spec.filas, filtros: spec.filtros, orden: "valor_desc", limite: 12 }),
        Olap.consultar({
          medida: "eventos",
          filas: "territorio.region",
          columnas: "cobertura.grupo",
          filtros: filtrosRegion,
        }),
      ]);
      if (actual !== turno) return;

      barra.registrarConsulta(matriz);
      pintarIndicadores(indicadores);
      await Olap.renderMatriz(el("v3-matriz"), matriz, {
        medida,
        etiquetaFila: catalogo.niveles[spec.filas].etiqueta,
        onClickFila: (miembro) => barra.drillMiembro(miembro),
      });
      Olap.grafica(el("v3-grafica-1"), configuracionValores(grupos, unidad));
      const porRegion = regionesInformadas(regiones);
      Olap.grafica(el("v3-grafica-2"), configuracionPorcentajes(porRegion));

      const seleccion = textoSeleccion(spec.filtros);
      const nombre = NOMBRES[medida];
      const g = mayorDe(grupos.filas);
      const m = mayorDe(matriz.filas);
      el("v3-interp-1").textContent = g
        ? `${seleccion}, el mayor valor de ${nombre} está en ${g.fila}: ${Olap.formato(g.valor, unidad)}. La gráfica muestra hasta 12 miembros.`
        : `${seleccion}, no hay datos para esta gráfica.`;

      /* "Sin region" agrupa los eventos sin departamento: no es una region para comparar. */
      const comparables = porRegion.filter((r) => r.region !== "Sin region");
      if (comparables.length) {
        const mayor = comparables[0];
        const menor = comparables[comparables.length - 1];
        const anios = (spec.filtros || {})["tiempo.anio"] || [];
        const incluyeSinRegistro = !anios.length || anios.some((a) => Number(a) > 2020);
        const detalle = (r) =>
          `${r.region}: ${Olap.formato(r.pct, "%")} (${Olap.formato(r.informados, "eventos")} de ${Olap.formato(r.total, "eventos")} eventos)`;
        el("v3-interp-2").textContent =
          `${textoSeleccion(filtrosRegion)}, el mayor porcentaje de eventos con cobertura informada es ${detalle(mayor)} y el menor, ${detalle(menor)}. ` +
          "Esta gráfica no aplica los filtros de cobertura porque el denominador es el total de eventos de cada región." +
          (incluyeSinRegistro
            ? " Las hojas 2021-2024 no registran cobertura y bajan los porcentajes; para comparar periodos equivalentes, filtra los años 2010 a 2020."
            : "");
      } else {
        el("v3-interp-2").textContent = `${textoSeleccion(filtrosRegion)}, no hay datos para esta gráfica.`;
      }

      el("v3-interp-3").textContent = m
        ? `${seleccion}, la celda con mayor ${nombre} es ${m.fila}${m.col !== null ? ` / ${m.col}` : ""}: ${Olap.formato(m.valor, unidad)}, con ${Olap.formato(m.eventos, "eventos")} eventos y ${Olap.formato(m.eventos_con_area, "eventos")} con área.`
        : `${seleccion}, no hay datos para esta matriz.`;
    } catch (error) {
      if (actual !== turno) return;
      el("v3-error").textContent = `No se pudo ejecutar la consulta: ${error.message}`;
      el("v3-error").classList.remove("hidden");
    }
  }

  async function iniciar() {
    try {
      catalogo = await Olap.catalogo();
      barra = await Olap.crearControles(el("v3-controles"), {
        medida: selectMedida.value,
        filas: "cobertura.grupo",
        columnas: "territorio.region",
        filtros: ["tiempo.anio", "tamano.clase"],
        niveles: [
          "cobertura.grupo", "cobertura.tipo",
          "territorio.region", "territorio.departamento",
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
      el("v3-error").textContent = `No se pudo iniciar la vista: ${error.message}`;
      el("v3-error").classList.remove("hidden");
    }
  }

  iniciar();
})();
