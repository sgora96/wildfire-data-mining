/* Motor de consultas y componentes compartidos de la Etapa 5. */
(function (global) {
  "use strict";

  const cfg = global.OLAP_CONFIG || {};
  const LIMITE_MAXIMO = 50000;
  const ORDEN_TAMANO = ["Sin dato", "<= 1 ha", "1-10 ha", "10-100 ha", "> 100 ha"];
  const MAX_FILAS_MATRIZ = 200;
  let promesaCatalogo = null;
  let promesaBase = null;

  function catalogo() {
    if (!promesaCatalogo) {
      promesaCatalogo = fetch(cfg.catalogo).then((r) => {
        if (!r.ok) throw new Error("No se pudo cargar el catalogo de consultas.");
        return r.json();
      });
    }
    return promesaCatalogo;
  }

  function validarNivel(datos, id, campo) {
    if (typeof id !== "string" || !Object.hasOwn(datos.niveles, id)) {
      throw new Error(`Nivel no permitido en '${campo}': ${id}`);
    }
    return datos.niveles[id];
  }

  function validarLimite(limite) {
    if (limite === undefined || limite === null) return LIMITE_MAXIMO;
    if (!Number.isInteger(limite) || limite < 1) {
      throw new Error("'limite' debe ser un entero mayor que cero.");
    }
    return Math.min(limite, LIMITE_MAXIMO);
  }

  function expresionOrden(nivel, alias) {
    return nivel.orden ? `MIN(${nivel.orden})` : alias;
  }

  /* Misma logica de construir_sql en app/olap.py. */
  function construirSql(spec, datos) {
    if (!spec || typeof spec !== "object" || Array.isArray(spec)) {
      throw new Error("La especificacion debe ser un objeto JSON.");
    }
    if (!Object.hasOwn(datos.medidas, spec.medida)) {
      throw new Error(`Medida no permitida: ${spec.medida}`);
    }
    const medida = datos.medidas[spec.medida];
    const nivelFilas = validarNivel(datos, spec.filas, "filas");
    let nivelColumnas = null;
    if (spec.columnas !== undefined && spec.columnas !== null) {
      nivelColumnas = validarNivel(datos, spec.columnas, "columnas");
      if (spec.columnas === spec.filas) {
        throw new Error("'filas' y 'columnas' deben ser niveles diferentes.");
      }
    }

    const filtros = spec.filtros || {};
    if (typeof filtros !== "object" || Array.isArray(filtros)) {
      throw new Error("'filtros' debe ser un objeto.");
    }
    Object.entries(filtros).forEach(([id, valores]) => {
      validarNivel(datos, id, "filtros");
      if (!Array.isArray(valores) || !valores.length) {
        throw new Error(`El filtro '${id}' debe ser una lista con valores.`);
      }
      if (!valores.every((v) => typeof v === "string" || Number.isInteger(v))) {
        throw new Error(`El filtro '${id}' tiene valores no validos.`);
      }
    });

    const limite = validarLimite(spec.limite);
    const orden = spec.orden || "etiqueta";
    if (orden !== "valor_desc" && orden !== "etiqueta") {
      throw new Error(`Orden no permitido: ${orden}`);
    }

    const usadas = new Set([nivelFilas.dimension]);
    if (nivelColumnas) usadas.add(nivelColumnas.dimension);
    Object.keys(filtros).forEach((id) => usadas.add(datos.niveles[id].dimension));

    const columna = nivelColumnas ? nivelColumnas.columna : "NULL";
    const lineas = [
      `SELECT ${nivelFilas.columna} AS fila, ${columna} AS col, ` +
        `${medida.expresion} AS valor, ` +
        "SUM(f.n_eventos) AS eventos, SUM(f.con_area) AS eventos_con_area",
      `FROM ${datos.hechos.tabla} ${datos.hechos.alias}`,
    ];
    Object.entries(datos.dimensiones).forEach(([nombre, d]) => {
      if (usadas.has(nombre)) {
        lineas.push(`JOIN ${d.tabla} ${d.alias} ON f.${d.clave} = ${d.alias}.${d.clave}`);
      }
    });

    const parametros = [];
    const condiciones = [];
    Object.entries(filtros).forEach(([id, valores]) => {
      const marcas = valores.map(() => "?").join(", ");
      condiciones.push(`${datos.niveles[id].columna} IN (${marcas})`);
      valores.forEach((v) => parametros.push(String(v)));
    });
    if (condiciones.length) lineas.push("WHERE " + condiciones.join(" AND "));

    lineas.push("GROUP BY fila, col");
    const ordenFilas = expresionOrden(nivelFilas, "fila");
    const ordenColumnas = nivelColumnas ? expresionOrden(nivelColumnas, "col") : "col";
    if (orden === "valor_desc") {
      lineas.push(`ORDER BY valor DESC, ${ordenFilas}, ${ordenColumnas}`);
    } else {
      lineas.push(`ORDER BY ${ordenFilas}, ${ordenColumnas}`);
    }
    lineas.push("LIMIT ?");
    parametros.push(limite);
    return { sql: lineas.join("\n"), parametros };
  }

  function base() {
    if (!promesaBase) {
      promesaBase = (async () => {
        const SQL = await global.initSqlJs({
          locateFile: (f) => "https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.10.3/" + f,
        });
        const respuesta = await fetch(cfg.base);
        if (!respuesta.ok) throw new Error("No se pudo cargar la base de datos.");
        return new SQL.Database(new Uint8Array(await respuesta.arrayBuffer()));
      })();
    }
    return promesaBase;
  }

  async function consultarSqlJs(spec) {
    const { sql, parametros } = construirSql(spec, await catalogo());
    const db = await base();
    const inicio = performance.now();
    const stmt = db.prepare(sql);
    try {
      stmt.bind(parametros);
      const columnas = stmt.getColumnNames();
      const filas = [];
      while (stmt.step()) filas.push(stmt.getAsObject());
      return {
        columnas,
        filas,
        sql,
        parametros,
        ms: Math.round((performance.now() - inicio) * 100) / 100,
      };
    } finally {
      stmt.free();
    }
  }

  async function consultarApi(spec) {
    const url = `${cfg.api}?spec=${encodeURIComponent(JSON.stringify(spec))}`;
    const respuesta = await fetch(url);
    const datos = await respuesta.json();
    if (!respuesta.ok) throw new Error(datos.error || "Error al ejecutar la consulta.");
    return datos;
  }

  function consultar(spec) {
    return global.OLAP_MODE === "sqljs" ? consultarSqlJs(spec) : consultarApi(spec);
  }

  function crear(etiqueta, clases, texto) {
    const el = document.createElement(etiqueta);
    if (clases) el.className = clases;
    if (texto !== undefined) el.textContent = texto;
    return el;
  }

  function formato(valor, unidad) {
    if (valor === null || valor === undefined) return "Sin dato";
    const decimales = unidad === "eventos" ? 0 : 1;
    const texto = Number(valor).toLocaleString("es-CO", {
      minimumFractionDigits: decimales,
      maximumFractionDigits: decimales,
    });
    if (unidad === "%") return `${texto} %`;
    return unidad && unidad !== "eventos" ? `${texto} ${unidad}` : texto;
  }

  function compararColumnas(a, b) {
    const ia = ORDEN_TAMANO.indexOf(a);
    const ib = ORDEN_TAMANO.indexOf(b);
    if (ia >= 0 && ib >= 0) return ia - ib;
    return String(a).localeCompare(String(b), "es", { numeric: true });
  }

  /* Matriz con mapa de calor; solo muestra totales en medidas aditivas. */
  async function renderMatriz(contenedor, resultado, opciones) {
    const datos = await catalogo();
    const medida = datos.medidas[opciones.medida];
    const filasBrutas = resultado.filas;
    contenedor.replaceChildren();
    if (!filasBrutas.length) {
      contenedor.append(crear("p", "text-sm text-slate-400", "No hay datos con esta seleccion."));
      return;
    }

    const hayColumnas = filasBrutas.some((f) => f.col !== null);
    const nombresFila = [...new Set(filasBrutas.map((f) => f.fila))];
    const nombresCol = hayColumnas
      ? [...new Set(filasBrutas.map((f) => f.col))].sort(compararColumnas)
      : [null];
    const celdas = new Map(filasBrutas.map((f) => [`${f.fila}|||${f.col}`, f]));
    const valores = filasBrutas.map((f) => f.valor).filter((v) => v !== null);
    const maximo = Math.max(...valores, 0);
    const conTotales = medida.aditiva;

    const envoltura = crear("div", "overflow-x-auto rounded-xl border border-white/10");
    const tabla = crear("table", "w-full border-collapse text-left text-xs text-slate-200");
    const thead = crear("thead", "bg-white/5 text-slate-300");
    const encabezado = crear("tr");
    encabezado.append(crear("th", "px-3 py-2 font-semibold", opciones.etiquetaFila || "Grupo"));
    nombresCol.forEach((c) => {
      encabezado.append(crear("th", "px-3 py-2 text-right font-semibold", c === null ? medida.unidad : c));
    });
    if (conTotales && hayColumnas) encabezado.append(crear("th", "px-3 py-2 text-right font-semibold", "Total"));
    thead.append(encabezado);

    const tbody = crear("tbody");
    const totalesColumna = new Map();
    nombresFila.slice(0, MAX_FILAS_MATRIZ).forEach((nombre) => {
      const tr = crear("tr", "border-t border-white/5");
      const celdaNombre = crear("th", "px-3 py-2 font-medium", nombre);
      if (opciones.onClickFila) {
        celdaNombre.classList.add("cursor-pointer", "hover:text-white", "hover:underline");
        celdaNombre.title = "Bajar un nivel en este miembro";
        celdaNombre.addEventListener("click", () => opciones.onClickFila(nombre));
      }
      tr.append(celdaNombre);
      let totalFila = 0;
      nombresCol.forEach((c) => {
        const celda = celdas.get(`${nombre}|||${c}`);
        const valor = celda ? celda.valor : null;
        const td = crear("td", "px-3 py-2 text-right tabular-nums", celda ? formato(valor, medida.unidad) : "-");
        if (celda) {
          td.title = `Eventos: ${formato(celda.eventos, "eventos")} | Con area: ${formato(celda.eventos_con_area, "eventos")}`;
        }
        if (valor !== null && maximo > 0) {
          td.style.backgroundColor = `rgba(234, 88, 12, ${(0.08 + 0.62 * (valor / maximo)).toFixed(3)})`;
        }
        tr.append(td);
        totalFila += valor || 0;
        totalesColumna.set(c, (totalesColumna.get(c) || 0) + (valor || 0));
      });
      if (conTotales && hayColumnas) {
        tr.append(crear("td", "px-3 py-2 text-right font-semibold tabular-nums", formato(totalFila, medida.unidad)));
      }
      tbody.append(tr);
    });

    tabla.append(thead, tbody);
    if (conTotales && nombresFila.length <= MAX_FILAS_MATRIZ) {
      const tfoot = crear("tfoot", "border-t border-white/20 bg-white/5 font-semibold");
      const tr = crear("tr");
      tr.append(crear("th", "px-3 py-2", "Total"));
      let general = 0;
      nombresCol.forEach((c) => {
        const total = totalesColumna.get(c) || 0;
        general += total;
        tr.append(crear("td", "px-3 py-2 text-right tabular-nums", formato(total, medida.unidad)));
      });
      if (hayColumnas) tr.append(crear("td", "px-3 py-2 text-right tabular-nums", formato(general, medida.unidad)));
      tfoot.append(tr);
      tabla.append(tfoot);
    }
    envoltura.append(tabla);
    contenedor.append(envoltura);

    if (!conTotales) {
      contenedor.append(crear("p", "mt-2 text-xs text-slate-500", "Esta medida no es aditiva: se recalcula en cada grupo y no se muestran totales."));
    }
    if (nombresFila.length > MAX_FILAS_MATRIZ) {
      contenedor.append(crear("p", "mt-2 text-xs text-slate-500", `Se muestran ${MAX_FILAS_MATRIZ} de ${nombresFila.length} filas. Usa filtros para acotar la seleccion.`));
    }
  }

  function tarjeta(contenedor, { titulo, valor, detalle }) {
    const el = crear("article", "rounded-xl border border-white/10 bg-white/5 p-4");
    el.append(
      crear("p", "text-xs font-semibold uppercase tracking-wider text-slate-400", titulo),
      crear("p", "mt-2 text-2xl font-extrabold text-white", valor),
      crear("p", "mt-1 text-xs text-slate-400", detalle || "")
    );
    contenedor.append(el);
    return el;
  }

  function grafica(contenedor, configuracion) {
    if (contenedor._grafica) contenedor._grafica.destroy();
    contenedor.replaceChildren();
    const lienzo = crear("canvas");
    contenedor.append(lienzo);
    contenedor._grafica = new global.Chart(lienzo, configuracion);
    return contenedor._grafica;
  }

  function padreEHijo(datos, nivel) {
    for (const orden of Object.values(datos.jerarquias)) {
      const i = orden.indexOf(nivel);
      if (i >= 0) return { padre: orden[i - 1] || null, hijo: orden[i + 1] || null };
    }
    return { padre: null, hijo: null };
  }

  /* Barra de controles: niveles, operaciones, filtros, chips y SQL. */
  async function crearControles(contenedor, opciones) {
    const datos = await catalogo();
    const estado = {
      medida: opciones.medida,
      filas: opciones.filas,
      columnas: opciones.columnas || null,
      filtros: {},
    };
    const niveles = opciones.niveles || Object.keys(datos.niveles);
    const casillas = new Map();

    const raiz = crear("div", "space-y-3 rounded-xl border border-white/10 bg-white/5 p-4");
    const fila = crear("div", "flex flex-wrap items-end gap-3");
    const zonaFiltros = crear("div", "flex flex-wrap items-start gap-3");
    const zonaChips = crear("div", "flex flex-wrap items-center gap-2");
    const botonSql = crear("button", "rounded-lg border border-white/20 px-3 py-1.5 text-xs font-semibold text-slate-200 hover:bg-white/10", "Ver consulta SQL");
    botonSql.type = "button";
    const zonaSql = crear("pre", "hidden overflow-x-auto rounded-lg bg-black/40 p-3 text-xs text-slate-300");

    function selector(texto, conVacio) {
      const etiqueta = crear("label", "text-xs font-semibold text-slate-400", texto);
      const select = crear("select", "mt-1 block rounded-lg border border-white/20 bg-slate-900 px-2 py-1.5 text-xs text-slate-200");
      if (conVacio) select.append(new Option("Sin columnas", ""));
      niveles.forEach((id) => select.append(new Option(datos.niveles[id].etiqueta, id)));
      etiqueta.append(select);
      fila.append(etiqueta);
      return select;
    }

    function boton(texto, accion) {
      const b = crear("button", "rounded-lg bg-ember-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-ember-500 disabled:cursor-not-allowed disabled:opacity-40", texto);
      b.type = "button";
      b.addEventListener("click", accion);
      fila.append(b);
      return b;
    }

    function espec() {
      const spec = {
        medida: estado.medida,
        filas: estado.filas,
        filtros: JSON.parse(JSON.stringify(estado.filtros)),
        orden: opciones.orden || "etiqueta",
      };
      if (estado.columnas) spec.columnas = estado.columnas;
      return spec;
    }

    function pintar() {
      selectFilas.value = estado.filas;
      selectColumnas.value = estado.columnas || "";
      const relFilas = padreEHijo(datos, estado.filas);
      const relCols = estado.columnas ? padreEHijo(datos, estado.columnas) : { padre: null, hijo: null };
      btnDrillFilas.disabled = !relFilas.hijo;
      btnRollFilas.disabled = !relFilas.padre;
      btnDrillCols.disabled = !relCols.hijo;
      btnRollCols.disabled = !relCols.padre;
      btnPivot.disabled = !estado.columnas;

      casillas.forEach((lista, nivel) => {
        const activos = estado.filtros[nivel] || [];
        lista.forEach((c) => { c.checked = activos.includes(c.value); });
      });

      zonaChips.replaceChildren();
      const chip = (texto) => crear("span", "rounded-full bg-white/10 px-2.5 py-1 text-xs text-slate-200", texto);
      zonaChips.append(chip(`Filas: ${datos.niveles[estado.filas].etiqueta}`));
      zonaChips.append(chip(`Columnas: ${estado.columnas ? datos.niveles[estado.columnas].etiqueta : "ninguna"}`));
      Object.entries(estado.filtros).forEach(([nivel, valores]) => {
        const c = chip(`${datos.niveles[nivel].etiqueta}: ${valores.join(", ")} `);
        const quitar = crear("button", "ml-1 font-bold text-ember-300", "x");
        quitar.type = "button";
        quitar.setAttribute("aria-label", `Quitar filtro ${datos.niveles[nivel].etiqueta}`);
        quitar.addEventListener("click", () => {
          delete estado.filtros[nivel];
          cambiar();
        });
        c.append(quitar);
        zonaChips.append(c);
      });
      zonaChips.append(botonSql);
    }

    function cambiar() {
      pintar();
      if (opciones.onCambio) opciones.onCambio(espec());
    }

    function mover(eje, nivelNuevo) {
      const otro = eje === "filas" ? "columnas" : "filas";
      if (estado[otro] === nivelNuevo) return;
      estado[eje] = nivelNuevo;
      delete estado.filtros[nivelNuevo];
      cambiar();
    }

    const selectFilas = selector("Filas", false);
    const selectColumnas = selector("Columnas", true);
    selectFilas.addEventListener("change", () => {
      if (selectFilas.value === estado.columnas) estado.columnas = null;
      estado.filas = selectFilas.value;
      cambiar();
    });
    selectColumnas.addEventListener("change", () => {
      if (selectColumnas.value && selectColumnas.value === estado.filas) {
        pintar();
        return;
      }
      estado.columnas = selectColumnas.value || null;
      cambiar();
    });

    const btnDrillFilas = boton("Drill-down filas", () => mover("filas", padreEHijo(datos, estado.filas).hijo));
    const btnRollFilas = boton("Roll-up filas", () => mover("filas", padreEHijo(datos, estado.filas).padre));
    const btnDrillCols = boton("Drill-down columnas", () => mover("columnas", padreEHijo(datos, estado.columnas).hijo));
    const btnRollCols = boton("Roll-up columnas", () => mover("columnas", padreEHijo(datos, estado.columnas).padre));
    const btnPivot = boton("Pivot", () => {
      [estado.filas, estado.columnas] = [estado.columnas, estado.filas];
      cambiar();
    });

    for (const nivel of opciones.filtros || []) {
      const resultado = await consultar({ medida: "eventos", filas: nivel });
      const bloque = crear("details", "min-w-48 rounded-lg border border-white/20 bg-slate-900 px-3 py-2 text-xs text-slate-200");
      bloque.append(crear("summary", "cursor-pointer font-semibold", `Filtro: ${datos.niveles[nivel].etiqueta}`));
      const lista = crear("div", "mt-2 max-h-48 space-y-1 overflow-y-auto");
      const controles = [];
      resultado.filas.forEach((f) => {
        const etiqueta = crear("label", "flex items-center gap-2");
        const casilla = crear("input");
        casilla.type = "checkbox";
        casilla.value = f.fila;
        casilla.addEventListener("change", () => {
          const activos = controles.filter((c) => c.checked).map((c) => c.value);
          if (activos.length) estado.filtros[nivel] = activos;
          else delete estado.filtros[nivel];
          cambiar();
        });
        controles.push(casilla);
        etiqueta.append(casilla, crear("span", "", f.fila));
        lista.append(etiqueta);
      });
      casillas.set(nivel, controles);
      bloque.append(lista);
      zonaFiltros.append(bloque);
    }

    botonSql.addEventListener("click", () => {
      zonaSql.classList.toggle("hidden");
    });

    raiz.append(fila, zonaFiltros, zonaChips, zonaSql);
    contenedor.replaceChildren(raiz);
    pintar();

    return {
      obtenerSpec: espec,
      /* Aplica una seleccion completa: la usan los botones de slice y dice. */
      aplicar(cambios) {
        if (cambios.filas) estado.filas = cambios.filas;
        if ("columnas" in cambios) estado.columnas = cambios.columnas;
        if (cambios.filtros) estado.filtros = JSON.parse(JSON.stringify(cambios.filtros));
        cambiar();
      },
      /* Baja un nivel en las filas y conserva el miembro elegido como filtro. */
      drillMiembro(miembro) {
        const hijo = padreEHijo(datos, estado.filas).hijo;
        if (!hijo || estado.columnas === hijo) return;
        estado.filtros[estado.filas] = [String(miembro)];
        estado.filas = hijo;
        cambiar();
      },
      registrarConsulta(resultado) {
        zonaSql.textContent = `${resultado.sql}\n\nParametros: ${JSON.stringify(resultado.parametros)}`;
      },
    };
  }

  global.Olap = {
    consultar,
    catalogo,
    construirSql,
    formato,
    renderMatriz,
    tarjeta,
    grafica,
    crearControles,
  };
})(window);