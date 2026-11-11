(function () {
  'use strict';

  const DEFAULTS = {
    demoMode: false,
    apiBase: '/api',
    requiredRole: 'nominal',
    loginUrl: '/.auth/login/aad?post_login_redirect_uri=/consulta.html',
    logoutUrl: '/.auth/logout?post_logout_redirect_uri=/',
    demoDataUrl: 'data/demo_consulta.json',
    pageSize: 100
  };

  const cfg = Object.assign({}, DEFAULTS, window.ASTIN_CONFIG || {});
  const $ = function (id) { return document.getElementById(id); };

  const els = {
    session: $('session'),
    sessionUser: $('sessionUser'),
    logoutLink: $('logoutLink'),
    demoBanner: $('demoBanner'),
    accessGate: $('accessGate'),
    gateTitle: $('gateTitle'),
    gateMessage: $('gateMessage'),
    gateActions: $('gateActions'),
    content: $('content'),
    errorBox: $('errorBox'),
    ficha: $('ficha'),
    instructor: $('instructor'),
    desde: $('desde'),
    hasta: $('hasta'),
    search: $('search'),
    reset: $('reset'),
    refresh: $('refresh'),
    exportCsv: $('exportCsv'),
    kpiAprendices: $('kpiAprendices'),
    kpiInasistencias: $('kpiInasistencias'),
    kpiHoras: $('kpiHoras'),
    kpiNoJustificadas: $('kpiNoJustificadas'),
    resultMeta: $('resultMeta'),
    loading: $('loading'),
    rows: $('rows'),
    empty: $('empty'),
    rowCount: $('rowCount'),
    showMore: $('showMore')
  };

  const state = {
    demoRecords: null,
    demoStarted: false,
    data: null,
    visible: cfg.pageSize,
    requestId: 0,
    controller: null,
    filtersReady: false
  };

  function init() {
    els.logoutLink.href = cfg.logoutUrl;
    els.demoBanner.hidden = !cfg.demoMode;

    els.refresh.addEventListener('click', function () { loadData(); });
    els.reset.addEventListener('click', resetFilters);
    els.exportCsv.addEventListener('click', exportCsv);
    els.showMore.addEventListener('click', function () {
      state.visible += cfg.pageSize;
      renderRows();
    });

    els.search.addEventListener('input', debounce(function () {
      state.visible = cfg.pageSize;
      loadData();
    }, 350));

    ['ficha', 'instructor', 'desde', 'hasta'].forEach(function (id) {
      els[id].addEventListener('change', function () {
        state.visible = cfg.pageSize;
        loadData();
      });
    });

    if (!window.ASTINAggregate) {
      showGate('error', 'No fue posible cargar la aplicación', 'Falta el módulo de agregación. Recargue la página o contacte al administrador.', [
        { label: 'Recargar', onClick: function () { window.location.reload(); } }
      ]);
      return;
    }

    if (cfg.demoMode) {
      startDemo();
    } else {
      checkAuth();
    }
  }

  async function startDemo() {
    cfg.demoMode = true;
    els.demoBanner.hidden = false;
    setSession({ userDetails: 'demostracion@local', userRoles: ['nominal', 'authenticated'] }, true);
    showContent();

    try {
      const response = await fetch(cfg.demoDataUrl, { cache: 'no-store' });
      if (!response.ok) throw new Error('No se encontró el archivo de demostración.');
      const data = await response.json();
      if (!data || !Array.isArray(data.records)) {
        throw new Error('El archivo de demostración no tiene el formato esperado.');
      }
      state.demoRecords = data.records;
      state.demoStarted = true;
      state.filtersReady = false;
      await loadData();
    } catch (error) {
      state.demoStarted = false;
      showGate('error', 'No fue posible cargar la demostración', error.message || 'Intente de nuevo.', [
        { label: 'Reintentar', onClick: startDemo },
        { label: 'Volver al portal', href: 'index.html', secondary: true }
      ]);
    }
  }

  async function checkAuth() {
    try {
      const response = await fetch('/.auth/me', {
        cache: 'no-store',
        credentials: 'same-origin'
      });
      if (!response.ok) throw new Error('auth-unavailable');
      const body = await response.json();
      const principal = body && body.clientPrincipal;

      if (!principal) {
        showLoginGate(false);
        return;
      }

      setSession(principal, false);
      const roles = Array.isArray(principal.userRoles) ? principal.userRoles : [];
      if (cfg.requiredRole && !roles.includes(cfg.requiredRole)) {
        showGate(
          'forbidden',
          'Sin autorización para datos nominales',
          'Su cuenta inició sesión, pero no pertenece al grupo autorizado para consultar nombres de aprendices. Solicite inclusión al administrador del sitio o a la Oficina de Bienestar.',
          [
            { label: 'Cerrar sesión', href: cfg.logoutUrl, secondary: true },
            { label: 'Volver al portal', href: 'index.html', secondary: true }
          ]
        );
        return;
      }

      showContent();
      await loadData();
    } catch (error) {
      showLoginGate(true);
    }
  }

  function showLoginGate(local) {
    const actions = [];
    if (local) {
      actions.push({ label: 'Ver demostración sintética', onClick: enableDemo });
      actions.push({ label: 'Volver al portal', href: 'index.html', secondary: true });
    } else {
      actions.push({ label: 'Iniciar sesión', href: cfg.loginUrl });
      actions.push({ label: 'Volver al portal', href: 'index.html', secondary: true });
    }

    const message = local
      ? 'El servidor local no expone la autenticación de Azure Static Web Apps. Puede revisar la interfaz con datos sintéticos o abrir la versión de Azure para iniciar sesión.'
      : 'Inicie sesión con su cuenta institucional para consultar datos nominales. Solo las personas autorizadas pueden ver los nombres de los aprendices.';

    showGate('login', 'Acceso restringido', message, actions);
  }

  function enableDemo() {
    startDemo();
  }

  function setSession(principal, demo) {
    els.session.hidden = false;
    els.sessionUser.textContent = (principal.userDetails || 'Sesión activa') + (demo ? ' · demostración' : '');
  }

  function showContent() {
    els.accessGate.hidden = true;
    els.content.hidden = false;
    clearError();
  }

  function showGate(kind, title, message, actions) {
    els.accessGate.hidden = false;
    els.content.hidden = true;
    els.gateTitle.textContent = title;
    els.gateMessage.textContent = message;
    els.gateActions.replaceChildren();

    const icon = els.accessGate.querySelector('.access-icon');
    if (icon) icon.textContent = kind === 'error' ? '⚠️' : '🔒';

    (actions || []).forEach(function (action) {
      let node;
      if (action.href) {
        node = document.createElement('a');
        node.href = action.href;
        node.textContent = action.label;
      } else {
        node = document.createElement('button');
        node.type = 'button';
        node.textContent = action.label;
        if (action.onClick) node.addEventListener('click', action.onClick);
      }
      node.className = 'button' + (action.secondary ? ' secondary' : '');
      els.gateActions.append(node);
    });
  }

  function readFilters() {
    return {
      ficha: els.ficha.value,
      instructor: els.instructor.value,
      desde: els.desde.value,
      hasta: els.hasta.value,
      q: els.search.value.trim()
    };
  }

  async function loadData() {
    const filters = readFilters();
    state.requestId += 1;
    const requestId = state.requestId;

    if (state.controller) state.controller.abort();
    state.controller = new AbortController();

    setLoading(true);
    clearError();

    try {
      let result;
      if (cfg.demoMode) {
        if (!state.demoRecords) throw new Error('Los datos de demostración aún no están disponibles.');
        result = window.ASTINAggregate.aggregate({
          generatedAt: new Date().toISOString(),
          sourceLabel: 'Datos sintéticos de demostración',
          synthetic: true,
          records: state.demoRecords
        }, filters);
      } else {
        result = await fetchFromApi(filters, state.controller.signal);
      }

      if (requestId !== state.requestId) return;
      if (!result) return;
      applyData(result);
    } catch (error) {
      if (error.name === 'AbortError') return;
      if (requestId !== state.requestId) return;
      showError('No fue posible consultar los datos. ' + (error.message || 'Intente de nuevo.'));
    } finally {
      if (requestId === state.requestId) setLoading(false);
    }
  }

  async function fetchFromApi(filters, signal) {
    const base = String(cfg.apiBase || '/api').replace(/\/+$/, '');
    const url = new URL(base + '/consulta', window.location.origin);
    if (filters.ficha) url.searchParams.set('ficha', filters.ficha);
    if (filters.instructor) url.searchParams.set('instructor', filters.instructor);
    if (filters.desde) url.searchParams.set('desde', filters.desde);
    if (filters.hasta) url.searchParams.set('hasta', filters.hasta);
    if (filters.q) url.searchParams.set('q', filters.q);

    const response = await fetch(url.toString(), {
      cache: 'no-store',
      credentials: 'same-origin',
      signal: signal,
      headers: { Accept: 'application/json' }
    });

    if (response.status === 401) {
      showLoginGate(false);
      return null;
    }
    if (response.status === 403) {
      showGate(
        'forbidden',
        'Sin autorización para datos nominales',
        'La sesión es válida, pero su cuenta no está autorizada para consultar nombres de aprendices. Solicite acceso a la Oficina de Bienestar o al administrador del sitio.',
        [
          { label: 'Cerrar sesión', href: cfg.logoutUrl, secondary: true },
          { label: 'Volver al portal', href: 'index.html', secondary: true }
        ]
      );
      return null;
    }

    const contentType = response.headers.get('content-type') || '';
    if (response.redirected || contentType.indexOf('text/html') !== -1) {
      showLoginGate(false);
      return null;
    }

    if (!response.ok) {
      let message = 'El servidor respondió con un error (' + response.status + ').';
      try {
        const body = await response.json();
        if (body && body.error && body.error.message) message = body.error.message;
      } catch (ignored) {
        /* respuesta sin JSON */
      }
      throw new Error(message);
    }

    if (contentType.indexOf('application/json') === -1) {
      throw new Error('La respuesta del servidor no tiene formato JSON.');
    }

    return response.json();
  }

  function applyData(data) {
    if (!data || !Array.isArray(data.rows) || !Array.isArray(data.filters.fichas)) {
      throw new Error('La respuesta de la API no tiene el formato esperado.');
    }

    state.data = data;
    els.kpiAprendices.textContent = formatNumber(data.kpis.aprendices);
    els.kpiInasistencias.textContent = formatNumber(data.kpis.inasistencias);
    els.kpiHoras.textContent = formatNumber(data.kpis.horas);
    els.kpiNoJustificadas.textContent = formatNumber(data.kpis.noJustificadas);

    fillSelect(els.ficha, data.filters.fichas, 'Todas las fichas');
    fillSelect(els.instructor, data.filters.instructores, 'Todos los instructores');

    if (!state.filtersReady) {
      els.desde.value = data.filters.minDate || '';
      els.hasta.value = data.filters.maxDate || '';
      state.filtersReady = true;
    }

    els.resultMeta.textContent = buildMeta(data);
    renderRows();
  }

  function buildMeta(data) {
    const parts = [];
    if (data.meta.synthetic) {
      parts.push('Demostración sintética');
    } else if (data.meta.generatedAt) {
      parts.push('Corte ' + formatDate(data.meta.generatedAt));
    } else {
      parts.push('Corte institucional');
    }
    parts.push(formatNumber(data.meta.totalRecords) + ' registros');
    parts.push(formatNumber(data.meta.totalLearners) + ' aprendices');
    if (data.meta.desde && data.meta.hasta) {
      parts.push('intervalo ' + formatDate(data.meta.desde) + ' a ' + formatDate(data.meta.hasta));
    }
    return parts.join(' · ');
  }

  function fillSelect(select, values, placeholder) {
    const current = select.value;
    const list = Array.isArray(values) ? values.map(String) : [];
    select.replaceChildren();

    const first = document.createElement('option');
    first.value = '';
    first.textContent = placeholder;
    select.append(first);

    list.forEach(function (value) {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = value;
      select.append(option);
    });

    select.value = list.indexOf(current) !== -1 ? current : '';
  }

  function renderRows() {
    const data = state.data;
    if (!data) return;

    const rows = data.rows || [];
    els.rows.replaceChildren();

    if (rows.length === 0) {
      els.empty.hidden = false;
      els.showMore.hidden = true;
      els.rowCount.textContent = '0 aprendices';
      return;
    }

    els.empty.hidden = true;
    const visible = rows.slice(0, state.visible);
    const fragment = document.createDocumentFragment();

    visible.forEach(function (row) {
      const tr = document.createElement('tr');
      appendCell(tr, row.aprendiz, 'name');
      appendCell(tr, row.ficha);
      appendCell(tr, formatNumber(row.inasistencias), 'num');
      appendCell(tr, formatNumber(row.horas), 'num');
      appendCell(tr, formatNumber(row.noJustificadas), 'num');
      appendCell(tr, formatNumber(row.peorSemana), 'num');

      const td = document.createElement('td');
      const badge = document.createElement('span');
      badge.className = 'badge ' + badgeClass(row.semaforo);
      badge.textContent = row.semaforo || 'Sin dato';
      td.append(badge);
      tr.append(td);
      fragment.append(tr);
    });

    els.rows.append(fragment);
    els.rowCount.textContent = formatNumber(rows.length) + ' aprendices · mostrando ' + formatNumber(visible.length);
    els.showMore.hidden = rows.length <= state.visible;
    if (!els.showMore.hidden) {
      els.showMore.textContent = 'Mostrar ' + formatNumber(Math.min(cfg.pageSize, rows.length - state.visible)) + ' más';
    }
  }

  function appendCell(tr, value, className) {
    const td = document.createElement('td');
    if (className) td.className = className;
    td.textContent = value == null ? '' : String(value);
    tr.append(td);
  }

  function badgeClass(semaforo) {
    if (semaforo === 'Rojo') return 'red';
    if (semaforo === 'Amarillo') return 'yellow';
    return 'green';
  }

  function resetFilters() {
    els.ficha.value = '';
    els.instructor.value = '';
    els.search.value = '';
    const min = state.data && state.data.filters ? state.data.filters.minDate : '';
    const max = state.data && state.data.filters ? state.data.filters.maxDate : '';
    els.desde.value = min || '';
    els.hasta.value = max || '';
    state.visible = cfg.pageSize;
    loadData();
  }

  function exportCsv() {
    if (!state.data || !state.data.rows || state.data.rows.length === 0) {
      showError('No hay datos para exportar con los filtros actuales.');
      return;
    }

    const confirmed = window.confirm(
      'El archivo CSV contiene nombres y datos personales de aprendices. ' +
      'Úselo solo para gestión disciplinaria o de Bienestar y no lo comparta por canales abiertos. ¿Desea continuar?'
    );
    if (!confirmed) return;

    const headers = ['Aprendiz', 'Ficha', 'Inasistencias', 'Horas totales', 'Horas no justificadas', 'Peor semana', 'Semáforo'];
    const lines = [headers];

    state.data.rows.forEach(function (row) {
      lines.push([
        row.aprendiz,
        row.ficha,
        formatNumber(row.inasistencias),
        formatNumber(row.horas),
        formatNumber(row.noJustificadas),
        formatNumber(row.peorSemana),
        row.semaforo
      ]);
    });

    const csv = lines.map(function (line) {
      return line.map(csvCell).join(';');
    }).join('\r\n');

    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' });
    const link = document.createElement('a');
    const prefix = cfg.demoMode ? 'demo_' : '';
    link.href = URL.createObjectURL(blob);
    link.download = 'consulta_semanal_' + prefix + new Date().toISOString().slice(0, 10) + '.csv';
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(link.href);
  }

  function csvCell(value) {
    const text = String(value == null ? '' : value);
    if (/[;"\r\n]/.test(text)) return '"' + text.replace(/"/g, '""') + '"';
    return text;
  }

  function setLoading(loading) {
    els.loading.hidden = !loading;
    els.refresh.disabled = loading;
    els.exportCsv.disabled = loading;
  }

  function showError(message) {
    els.errorBox.textContent = message;
    els.errorBox.hidden = false;
  }

  function clearError() {
    els.errorBox.textContent = '';
    els.errorBox.hidden = true;
  }

  function formatNumber(value) {
    return new Intl.NumberFormat('es-CO', { maximumFractionDigits: 1 }).format(Number(value) || 0);
  }

  function formatDate(value) {
    if (!value) return 'sin fecha';
    const date = new Date(String(value).length === 10 ? value + 'T00:00:00Z' : value);
    if (Number.isNaN(date.valueOf())) return String(value);
    return new Intl.DateTimeFormat('es-CO', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      timeZone: 'UTC'
    }).format(date);
  }

  function debounce(fn, wait) {
    let timer = null;
    return function () {
      window.clearTimeout(timer);
      timer = window.setTimeout(fn, wait);
    };
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
