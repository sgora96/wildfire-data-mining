/* =========================================================================
 * Wildfire Data Mining · logica del dashboard
 *
 * Dos modos de operacion:
 *   - "live"   : hay backend Flask; los datos vienen de /api/*.
 *   - "static" : build congelado (GitHub Pages); se carga api/dataset.json
 *                una sola vez y los calculos se replican en el navegador.
 * ========================================================================= */

(() => {
  'use strict';

  // ----------------------------------------------------------------------- //
  // Constantes compartidas con app/services.py
  // ----------------------------------------------------------------------- //
  const MONTH_ORDER = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                       'jul', 'aug', 'sep', 'oct', 'nov', 'dec'];
  const MONTH_LABELS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                        'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
  const CLIMATE_COLUMNS = ['temp', 'RH', 'wind', 'rain', 'FFMC', 'DMC', 'DC', 'ISI'];
  const RISK_BINS = [[0, 25, 'Bajo'], [25, 50, 'Moderado'],
                     [50, 75, 'Alto'], [75, 101, 'Extremo']];

  const PALETTE = {
    ember: '#f97316',
    amber: '#fbbf24',
    sky: '#38bdf8',
    emerald: '#34d399',
    red: '#ef4444',
    grid: 'rgba(148, 163, 184, 0.12)',
    text: '#94a3b8',
  };

  const state = {
    mode: 'live',
    records: [],          // usado solo en modo static
    source: '—',
    charts: {},
    months: new Set(),
  };

  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => Array.from(document.querySelectorAll(selector));

  // ----------------------------------------------------------------------- //
  // Utilidades numericas
  // ----------------------------------------------------------------------- //
  const num = (value, fallback = NaN) => {
    const parsed = typeof value === 'number' ? value : parseFloat(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  };

  const round = (value, digits = 2) => {
    if (!Number.isFinite(value)) return 0;
    const factor = 10 ** digits;
    return Math.round(value * factor) / factor;
  };

  const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

  const mean = (values) => (values.length
    ? values.reduce((acc, v) => acc + v, 0) / values.length
    : 0);

  // ----------------------------------------------------------------------- //
  // Motor de calculo local (espejo de app/services.py para el modo static)
  // ----------------------------------------------------------------------- //
  const Engine = {
    riskIndex(row) {
      const temp = num(row.temp, 20);
      const wind = num(row.wind, 4);
      const rh = num(row.RH, 50);
      const rain = num(row.rain, 0);

      const tempN = clamp(temp / 45, 0, 1);
      const windN = clamp(wind / 25, 0, 1);
      const dryN = clamp(1 - rh / 100, 0, 1);
      const wetPenalty = clamp(rain / 6, 0, 1);

      const score = (0.42 * tempN + 0.28 * windN + 0.30 * dryN) * (1 - 0.55 * wetPenalty);
      return round(score * 100, 1);
    },

    applyFilters(records, filters) {
      return records.filter((row) => {
        const ranges = [
          ['temp', filters.temp_min, filters.temp_max],
          ['wind', filters.wind_min, filters.wind_max],
          ['RH', filters.rh_min, filters.rh_max],
        ];
        for (const [column, min, max] of ranges) {
          const value = num(row[column]);
          if (!Number.isFinite(value)) continue;
          if (min !== null && value < min) return false;
          if (max !== null && value > max) return false;
        }
        if (filters.months && filters.months.length &&
            !filters.months.includes(String(row.month).toLowerCase().slice(0, 3))) {
          return false;
        }
        if (filters.only_burned && num(row.area, 0) <= 0) return false;
        return true;
      });
    },

    computeKpis(records) {
      const areas = records.map((r) => num(r.area, 0));
      const burned = areas.filter((a) => a > 0);
      const risks = records.map((r) => Engine.riskIndex(r));
      const columnMean = (column) => {
        const values = records.map((r) => num(r[column])).filter(Number.isFinite);
        return round(mean(values), 1);
      };

      return {
        total_fires: records.length,
        active_events: burned.length,
        total_area: round(areas.reduce((acc, v) => acc + v, 0), 1),
        avg_area: round(mean(burned), 2),
        max_area: round(areas.length ? Math.max(...areas) : 0, 1),
        avg_risk: round(mean(risks), 1),
        avg_temp: columnMean('temp'),
        avg_wind: columnMean('wind'),
        avg_humidity: columnMean('RH'),
        high_risk_share: round(records.length
          ? (risks.filter((r) => r >= 50).length / records.length) * 100
          : 0, 1),
      };
    },

    monthly(records) {
      const fires = new Array(12).fill(0);
      const area = new Array(12).fill(0);
      records.forEach((row) => {
        const index = MONTH_ORDER.indexOf(String(row.month).toLowerCase().slice(0, 3));
        if (index === -1) return;
        fires[index] += 1;
        area[index] += num(row.area, 0);
      });
      return { labels: MONTH_LABELS, fires, area: area.map((v) => round(v, 1)) };
    },

    riskDistribution(records) {
      const counts = RISK_BINS.map(() => 0);
      records.forEach((row) => {
        const score = Engine.riskIndex(row);
        const index = RISK_BINS.findIndex(([low, high]) => score >= low && score < high);
        if (index !== -1) counts[index] += 1;
      });
      return { labels: RISK_BINS.map(([, , label]) => label), counts };
    },

    scatter(records, maxPoints = 320) {
      const points = records
        .filter((r) => Number.isFinite(num(r.temp)) && Number.isFinite(num(r.area)))
        .map((r) => ({
          x: round(num(r.temp), 1),
          y: round(Math.log1p(Math.max(num(r.area, 0), 0)), 3),
          r: round(3 + num(r.wind, 0) / 4, 1),
        }));
      const step = Math.max(1, Math.ceil(points.length / maxPoints));
      return { points: points.filter((_, i) => i % step === 0) };
    },

    correlation(records) {
      const columns = [...CLIMATE_COLUMNS, 'area'].filter((column) =>
        records.some((row) => Number.isFinite(num(row[column]))));
      if (columns.length < 2) return { labels: [], matrix: [] };

      const series = columns.map((column) => records.map((row) => num(row[column], 0)));
      const pearson = (a, b) => {
        const ma = mean(a);
        const mb = mean(b);
        let cov = 0; let va = 0; let vb = 0;
        for (let i = 0; i < a.length; i += 1) {
          const da = a[i] - ma;
          const db = b[i] - mb;
          cov += da * db;
          va += da * da;
          vb += db * db;
        }
        const denominator = Math.sqrt(va * vb);
        return denominator === 0 ? 0 : round(cov / denominator, 3);
      };

      return {
        labels: columns,
        matrix: series.map((a) => series.map((b) => pearson(a, b))),
      };
    },

    windProfile(records, bins = 8) {
      const winds = records.map((r) => num(r.wind)).filter(Number.isFinite);
      if (winds.length < 2) return { labels: [], risk: [] };

      const min = Math.min(...winds);
      const max = Math.max(...winds);
      if (max === min) return { labels: [], risk: [] };

      const width = (max - min) / bins;
      const buckets = Array.from({ length: bins }, () => []);
      records.forEach((row) => {
        const wind = num(row.wind);
        if (!Number.isFinite(wind)) return;
        const index = clamp(Math.floor((wind - min) / width), 0, bins - 1);
        buckets[index].push(Engine.riskIndex(row));
      });

      const labels = [];
      const risk = [];
      buckets.forEach((values, index) => {
        if (!values.length) return;
        labels.push(`${Math.round(min + index * width)}-${Math.round(min + (index + 1) * width)}`);
        risk.push(round(mean(values), 1));
      });
      return { labels, risk };
    },

    analysis(records) {
      return {
        monthly: Engine.monthly(records),
        risk_distribution: Engine.riskDistribution(records),
        scatter: Engine.scatter(records),
        correlation: Engine.correlation(records),
        wind_profile: Engine.windProfile(records),
      };
    },
  };

  // ----------------------------------------------------------------------- //
  // Capa de acceso a datos
  // ----------------------------------------------------------------------- //
  const readFilters = () => {
    const value = (id) => {
      const input = $(`#${id}`);
      return input ? parseFloat(input.value) : null;
    };
    return {
      temp_min: value('temp_min'),
      temp_max: value('temp_max'),
      wind_min: value('wind_min'),
      wind_max: value('wind_max'),
      rh_min: value('rh_min'),
      rh_max: value('rh_max'),
      months: Array.from(state.months),
      only_burned: Boolean($('#only_burned') && $('#only_burned').checked),
    };
  };

  const toQuery = (filters) => {
    const params = new URLSearchParams();
    ['temp_min', 'temp_max', 'wind_min', 'wind_max', 'rh_min', 'rh_max']
      .forEach((key) => {
        if (filters[key] !== null && !Number.isNaN(filters[key])) {
          params.set(key, filters[key]);
        }
      });
    filters.months.forEach((month) => params.append('month', month));
    if (filters.only_burned) params.set('only_burned', '1');
    return params.toString();
  };

  const getJSON = async (url) => {
    const response = await fetch(url, { headers: { Accept: 'application/json' } });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  };

  const Data = {
    async detectMode() {
      if (window.STATIC_EXPORT) return Data.bootStatic();
      try {
        await getJSON('/api/health');
        state.mode = 'live';
        setStatus('online', 'API conectada');
      } catch (error) {
        await Data.bootStatic();
      }
    },

    async bootStatic() {
      state.mode = 'static';
      try {
        const payload = await getJSON('api/dataset.json');
        state.records = payload.records || [];
        state.source = payload.source || 'dataset congelado';
        setStatus('static', 'Modo estatico');
      } catch (error) {
        state.records = [];
        setStatus('offline', 'Sin datos');
      }
    },

    async kpis(filters) {
      if (state.mode === 'live') {
        return getJSON(`/api/kpis?${toQuery(filters)}`);
      }
      const filtered = Engine.applyFilters(state.records, filters);
      return {
        ok: true,
        source: state.source,
        matched: filtered.length,
        total: state.records.length,
        kpis: Engine.computeKpis(filtered),
      };
    },

    async analysis(filters) {
      if (state.mode === 'live') {
        return getJSON(`/api/analysis?${toQuery(filters)}`);
      }
      const filtered = Engine.applyFilters(state.records, filters);
      return { ok: true, matched: filtered.length, charts: Engine.analysis(filtered) };
    },

    async records(filters, limit = 12) {
      if (state.mode === 'live') {
        return getJSON(`/api/records?${toQuery(filters)}&limit=${limit}`);
      }
      const filtered = Engine.applyFilters(state.records, filters).slice(0, limit);
      const rows = filtered.map((row) => ({ ...row, risk: Engine.riskIndex(row) }));
      return {
        ok: true,
        total: filtered.length,
        columns: rows.length ? Object.keys(rows[0]) : [],
        rows,
      };
    },

    async datasets() {
      if (state.mode === 'live') return getJSON('/api/datasets');
      return { ok: true, datasets: [{ name: state.source, stage: 'frozen', size_kb: 0 }] };
    },
  };

  // ----------------------------------------------------------------------- //
  // Render
  // ----------------------------------------------------------------------- //
  function setStatus(kind, label) {
    const dot = $('#api-status-dot');
    const text = $('#api-status-text');
    if (!dot || !text) return;
    const colors = {
      online: 'bg-emerald-400',
      static: 'bg-sky-400',
      offline: 'bg-red-500',
    };
    dot.className = `h-2 w-2 rounded-full ${colors[kind] || 'bg-amber-400'}`;
    text.textContent = label;
  }

  function renderKpis(payload) {
    const kpis = payload.kpis || {};
    Object.entries(kpis).forEach(([key, value]) => {
      const target = document.querySelector(`[data-kpi="${key}"]`);
      if (target) target.textContent = value;
    });

    const bar = $('#risk-bar');
    if (bar) bar.style.width = `${clamp(num(kpis.avg_risk, 0), 0, 100)}%`;

    const matches = $('#match-count');
    if (matches) matches.textContent = payload.matched ?? 0;

    const source = $('#dataset-source');
    if (source && payload.source) source.textContent = payload.source;
  }

  function baseChartOptions(extra = {}) {
    return {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { intersect: false, mode: 'index' },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#0f172a',
          borderColor: 'rgba(148,163,184,.2)',
          borderWidth: 1,
          padding: 10,
        },
      },
      scales: {
        x: { grid: { color: PALETTE.grid }, ticks: { color: PALETTE.text } },
        y: { grid: { color: PALETTE.grid }, ticks: { color: PALETTE.text }, beginAtZero: true },
      },
      ...extra,
    };
  }

  function upsertChart(key, canvasId, config) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === 'undefined') return;

    if (state.charts[key]) {
      state.charts[key].data = config.data;
      state.charts[key].update();
      return;
    }
    state.charts[key] = new Chart(canvas.getContext('2d'), config);
  }

  function renderCharts(charts) {
    const { monthly, risk_distribution: risk, scatter, wind_profile: wind } = charts;

    upsertChart('monthly', 'chart-monthly', {
      type: 'bar',
      data: {
        labels: monthly.labels,
        datasets: [
          {
            label: 'Incendios',
            data: monthly.fires,
            backgroundColor: 'rgba(249,115,22,.75)',
            borderRadius: 6,
            yAxisID: 'y',
          },
          {
            label: 'Hectareas',
            data: monthly.area,
            type: 'line',
            borderColor: PALETTE.amber,
            backgroundColor: 'rgba(251,191,36,.15)',
            borderWidth: 2,
            tension: 0.35,
            fill: true,
            pointRadius: 3,
            yAxisID: 'y1',
          },
        ],
      },
      options: baseChartOptions({
        scales: {
          x: { grid: { display: false }, ticks: { color: PALETTE.text } },
          y: {
            position: 'left',
            grid: { color: PALETTE.grid },
            ticks: { color: PALETTE.text },
            beginAtZero: true,
          },
          y1: {
            position: 'right',
            grid: { display: false },
            ticks: { color: PALETTE.amber },
            beginAtZero: true,
          },
        },
      }),
    });

    upsertChart('risk', 'chart-risk', {
      type: 'doughnut',
      data: {
        labels: risk.labels,
        datasets: [{
          data: risk.counts,
          backgroundColor: ['#34d399', '#fbbf24', '#f97316', '#ef4444'],
          borderColor: '#0f172a',
          borderWidth: 3,
          hoverOffset: 6,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '62%',
        plugins: {
          legend: { position: 'bottom', labels: { color: PALETTE.text, boxWidth: 12, padding: 14 } },
          tooltip: { backgroundColor: '#0f172a' },
        },
      },
    });

    upsertChart('wind', 'chart-wind', {
      type: 'bar',
      data: {
        labels: wind.labels,
        datasets: [{
          label: 'Riesgo medio',
          data: wind.risk,
          backgroundColor: 'rgba(56,189,248,.7)',
          borderRadius: 6,
        }],
      },
      options: baseChartOptions(),
    });

    upsertChart('scatter', 'chart-scatter', {
      type: 'bubble',
      data: {
        datasets: [{
          label: 'Eventos',
          data: scatter.points,
          backgroundColor: 'rgba(249,115,22,.45)',
          borderColor: 'rgba(249,115,22,.8)',
        }],
      },
      options: baseChartOptions({
        interaction: { intersect: true, mode: 'nearest' },
        scales: {
          x: {
            title: { display: true, text: 'Temperatura (C)', color: PALETTE.text },
            grid: { color: PALETTE.grid },
            ticks: { color: PALETTE.text },
          },
          y: {
            title: { display: true, text: 'log(1 + area)', color: PALETTE.text },
            grid: { color: PALETTE.grid },
            ticks: { color: PALETTE.text },
            beginAtZero: true,
          },
        },
      }),
    });

    renderCorrelation(charts.correlation);
  }

  function renderCorrelation({ labels, matrix }) {
    const container = $('#correlation-grid');
    if (!container) return;

    if (!labels.length) {
      container.innerHTML = '<p class="py-6 text-center text-slate-500">Sin variables numericas suficientes.</p>';
      return;
    }

    const cellColor = (value) => (value >= 0
      ? `rgba(249,115,22,${clamp(Math.abs(value), 0.06, 0.9).toFixed(2)})`
      : `rgba(56,189,248,${clamp(Math.abs(value), 0.06, 0.9).toFixed(2)})`);

    const header = ['<div></div>', ...labels.map((label) =>
      `<div class="pb-1 text-center font-semibold text-slate-400">${label}</div>`)].join('');

    const rows = matrix.map((row, i) => [
      `<div class="pr-2 text-right font-semibold text-slate-400">${labels[i]}</div>`,
      ...row.map((value) =>
        `<div class="rounded-sm py-1.5 text-center font-mono text-white/90"
              style="background:${cellColor(value)}" title="${value}">${value.toFixed(2)}</div>`),
    ].join('')).join('');

    container.style.display = 'grid';
    container.style.gridTemplateColumns = `minmax(48px, auto) repeat(${labels.length}, minmax(46px, 1fr))`;
    container.style.gap = '3px';
    container.innerHTML = header + rows;
  }

  function renderRecords(payload) {
    const head = $('#records-head');
    const body = $('#records-body');
    if (!head || !body) return;

    if (!payload.rows.length) {
      head.innerHTML = '';
      body.innerHTML = '<tr><td class="px-3 py-6 text-center text-slate-500">Ningun registro coincide con los filtros.</td></tr>';
      return;
    }

    head.innerHTML = `<tr>${payload.columns.map((column) =>
      `<th class="whitespace-nowrap px-3 py-2 font-semibold uppercase tracking-wider">${column}</th>`).join('')}</tr>`;

    body.innerHTML = payload.rows.map((row) =>
      `<tr class="transition hover:bg-white/5">${payload.columns.map((column) =>
        `<td class="whitespace-nowrap px-3 py-2">${row[column] ?? ''}</td>`).join('')}</tr>`).join('');
  }

  function renderDatasets(payload) {
    const list = $('#dataset-list');
    if (!list) return;

    if (!payload.datasets.length) {
      list.innerHTML = '<li class="italic text-slate-600">Aun no hay datasets cargados.</li>';
      return;
    }

    const badge = { raw: 'bg-amber-500/15 text-amber-400', processed: 'bg-emerald-500/15 text-emerald-400' };
    list.innerHTML = payload.datasets.map((item) => `
      <li class="flex items-center justify-between gap-2 rounded-md bg-white/5 px-2.5 py-1.5">
        <span class="truncate text-slate-300" title="${item.name}">${item.name}</span>
        <span class="shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase ${badge[item.stage] || 'bg-sky-500/15 text-sky-400'}">${item.stage}</span>
      </li>`).join('');
  }

  // ----------------------------------------------------------------------- //
  // Ciclo de actualizacion
  // ----------------------------------------------------------------------- //
  async function refresh() {
    const filters = readFilters();
    const containers = $$('.chart-shell');
    containers.forEach((element) => element.classList.add('is-loading'));

    try {
      const [kpis, analysis, records] = await Promise.all([
        Data.kpis(filters),
        Data.analysis(filters),
        Data.records(filters),
      ]);
      renderKpis(kpis);
      renderCharts(analysis.charts);
      renderRecords(records);
    } catch (error) {
      console.error('[wildfire] fallo al actualizar el dashboard:', error);
      setStatus('offline', 'Error de datos');
    } finally {
      containers.forEach((element) => element.classList.remove('is-loading'));
    }
  }

  // ----------------------------------------------------------------------- //
  // Carga de datasets
  // ----------------------------------------------------------------------- //
  function showFeedback(message, kind = 'info') {
    const box = $('#upload-feedback');
    if (!box) return;
    const styles = {
      info: 'border-sky-500/30 bg-sky-500/10 text-sky-300',
      success: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
      error: 'border-red-500/30 bg-red-500/10 text-red-300',
    };
    box.className = `mt-4 rounded-lg border px-3 py-2 text-xs ${styles[kind]}`;
    box.textContent = message;
  }

  function renderProfile(profile) {
    const panel = $('#upload-profile');
    if (!panel) return;
    $('#profile-rows').textContent = profile.rows;
    $('#profile-cols').textContent = profile.columns;
    $('#profile-nulls').textContent = profile.missing_total;
    $('#profile-columns').innerHTML = profile.column_names.map((column) =>
      `<span class="rounded bg-white/5 px-1.5 py-0.5 text-[10px] text-slate-400">${column}</span>`).join('');
    panel.classList.remove('hidden');
  }

  /** Parser CSV minimo para el modo estatico (sin comillas anidadas). */
  function parseCSV(text) {
    const lines = text.trim().split(/\r?\n/).filter(Boolean);
    if (lines.length < 2) return [];
    const headers = lines[0].split(',').map((h) => h.trim().replace(/^"|"$/g, ''));
    return lines.slice(1).map((line) => {
      const cells = line.split(',');
      return headers.reduce((row, header, index) => {
        const raw = (cells[index] ?? '').trim().replace(/^"|"$/g, '');
        const parsed = parseFloat(raw);
        row[header] = raw !== '' && !Number.isNaN(parsed) && /^-?[\d.]+$/.test(raw) ? parsed : raw;
        return row;
      }, {});
    });
  }

  async function handleUpload(file) {
    if (!file) return;
    showFeedback(`Procesando ${file.name}…`, 'info');

    if (state.mode === 'static') {
      if (!file.name.toLowerCase().endsWith('.csv')) {
        showFeedback('En el demo estatico solo se admiten archivos CSV.', 'error');
        return;
      }
      const records = parseCSV(await file.text());
      if (!records.length) {
        showFeedback('El CSV no contiene filas legibles.', 'error');
        return;
      }
      state.records = records;
      state.source = file.name;
      renderProfile({
        rows: records.length,
        columns: Object.keys(records[0]).length,
        missing_total: 0,
        column_names: Object.keys(records[0]),
      });
      showFeedback(`${file.name} cargado en memoria (${records.length} filas).`, 'success');
      await refresh();
      return;
    }

    const body = new FormData();
    body.append('file', file);
    try {
      const response = await fetch('/api/upload', { method: 'POST', body });
      const payload = await response.json();
      if (!payload.ok) {
        showFeedback(payload.error || 'No se pudo cargar el archivo.', 'error');
        return;
      }
      renderProfile(payload.profile);
      showFeedback(`${payload.filename} guardado en ${payload.stored_in}.`, 'success');
      await Promise.all([refresh(), Data.datasets().then(renderDatasets)]);
    } catch (error) {
      showFeedback('Error de red al subir el archivo.', 'error');
    }
  }

  // ----------------------------------------------------------------------- //
  // Enlace de eventos
  // ----------------------------------------------------------------------- //
  function bindRangeOutputs() {
    $$('input[type="range"]').forEach((input) => {
      const output = document.getElementById(input.dataset.output);
      const unit = input.dataset.unit || '';
      const sync = () => { if (output) output.textContent = `${input.value}${unit}`; };
      input.addEventListener('input', sync);
      sync();
    });
  }

  function bindMonthChips() {
    $$('.month-chip').forEach((chip) => {
      chip.addEventListener('click', () => {
        const month = chip.dataset.month;
        if (state.months.has(month)) {
          state.months.delete(month);
          chip.classList.remove('is-active');
        } else {
          state.months.add(month);
          chip.classList.add('is-active');
        }
      });
    });
  }

  function bindDropzone() {
    const dropzone = $('#dropzone');
    const input = $('#file-input');
    if (!dropzone || !input) return;

    input.addEventListener('change', () => handleUpload(input.files[0]));

    ['dragenter', 'dragover'].forEach((event) =>
      dropzone.addEventListener(event, (e) => {
        e.preventDefault();
        dropzone.classList.add('dropzone-active');
      }));

    ['dragleave', 'drop'].forEach((event) =>
      dropzone.addEventListener(event, (e) => {
        e.preventDefault();
        dropzone.classList.remove('dropzone-active');
      }));

    dropzone.addEventListener('drop', (e) => handleUpload(e.dataTransfer.files[0]));
  }

  function resetFilters() {
    $$('input[type="range"]').forEach((input) => {
      input.value = input.id.endsWith('_min') ? input.min : input.max;
      input.dispatchEvent(new Event('input'));
    });
    $$('.month-chip').forEach((chip) => chip.classList.remove('is-active'));
    state.months.clear();
    const onlyBurned = $('#only_burned');
    if (onlyBurned) onlyBurned.checked = false;
    refresh();
  }

  // ----------------------------------------------------------------------- //
  // Arranque
  // ----------------------------------------------------------------------- //
  async function init() {
    const year = $('#year');
    if (year) year.textContent = new Date().getFullYear();

    bindRangeOutputs();
    bindMonthChips();
    bindDropzone();

    const form = $('#filter-form');
    if (form) form.addEventListener('submit', (e) => { e.preventDefault(); refresh(); });

    const reset = $('#btn-reset');
    if (reset) reset.addEventListener('click', resetFilters);

    const refreshButton = $('#btn-refresh');
    if (refreshButton) refreshButton.addEventListener('click', refresh);

    await Data.detectMode();
    await refresh();
    Data.datasets().then(renderDatasets).catch(() => {});
  }

  document.addEventListener('DOMContentLoaded', init);
})();
