#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera un único HTML local con las seis vistas del portal, incluida la 05 nominal.

El archivo resultante está pensado para abrirse con doble clic en el equipo del
instructor o coordinador autorizado. No se publica, no se sube a Git y contiene
nombres de aprendices; por eso se escribe en outputs/ y está excluido por
.gitignore.

Uso:
    python scripts/12_generar_portal_local.py
    python scripts/12_generar_portal_local.py --demo
    python scripts/12_generar_portal_local.py --out outputs/mi_portal.html

La vista 05 usa la misma agregación semanal que la API y el navegador
(api/src/shared/aggregate.js), con datos embebidos para que funcione desde
file:// sin un servidor HTTP.
"""
from __future__ import annotations

import argparse
import base64
import csv
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RESTRICTED = ROOT / "data" / "restricted"
SUMMARY = PROCESSED / "00_resumen_etl.json"
FACTS = PROCESSED / "FACT_INASISTENCIAS.csv"
IDENTITIES = RESTRICTED / "DIM_APRENDIZ_PII.csv"
DEMO_DATA = ROOT / "web" / "data" / "demo_consulta.json"
PORTAL_SCRIPT = ROOT / "scripts" / "04_generar_portal_html.py"
AGGREGATE_SOURCE = ROOT / "api" / "src" / "shared" / "aggregate.js"
AGGREGATE_FALLBACK = ROOT / "web" / "assets" / "aggregate.js"
DEFAULT_OUT = ROOT / "outputs" / "portal_local_completo.html"
DEMO_OUT = ROOT / "outputs" / "portal_local_demo.html"

PAGE_CSS = r"""
.nominal-filters{justify-content:flex-start;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:14px;box-shadow:var(--shadow);margin:0 0 14px}
.nominal-filters .filter input{min-width:150px;border:1px solid var(--line);border-radius:7px;background:#fff;color:var(--ink);padding:9px 11px;box-shadow:0 2px 5px rgba(0,48,77,.03)}
.nominal-filters .filter input[type=date]{min-width:145px}
.nominal-filters .filter.search{flex:1 1 220px}
.nominal-filters .filter.search input{width:100%;min-width:210px}
.nominal-actions{display:flex;gap:8px;align-items:end;margin-left:auto}
.button{border:0;border-radius:7px;padding:10px 15px;color:#fff;background:var(--green);font-weight:700;font-size:12px;cursor:pointer}
.button:hover{background:var(--green-dark)}
.button.secondary{background:#fff;color:var(--navy);border:1px solid var(--line)}
.button.secondary:hover{background:#eef5ea;color:var(--green-dark)}
.button:disabled{opacity:.55;cursor:not-allowed}
.nominal-table-wrap{max-height:62vh;border:1px solid #eef3ef;border-radius:8px}
.nominal-table td.name{white-space:normal;min-width:230px;font-weight:600}
.badge.green{background:#e8f5e2;color:#276900}
.badge.yellow{background:#fff5d6;color:#765b00}
.badge.red{background:#fde8e7;color:#a62219}
.local-warning{border-left-color:var(--red);background:#fdecec;color:#7a1a12}
.local-warning strong{color:#7a1a12}
.local-flag{display:block;margin-top:10px;color:var(--yellow);font-weight:800;letter-spacing:.05em;line-height:1.4}
body.nominal-view .topbar .filters{display:none}
@media(max-width:760px){.nominal-filters .filter{flex:1 1 100%}.nominal-filters .filter input{width:100%;min-width:0}.nominal-actions{margin-left:0;width:100%}.nominal-actions .button{width:100%}}
"""

PAGE_HTML = r"""
  <section class="page" id="page-consulta" aria-labelledby="title-consulta">
   <h2 id="title-consulta" class="sr-only">Consulta semanal nominal</h2>
   <div class="notice local-warning">@@WARNING@@</div>
   <section class="filters nominal-filters" aria-label="Filtros de la consulta nominal">
    <label class="filter">Ficha<select id="nominalFicha" aria-label="Filtrar por ficha"><option value="">Todas las fichas</option></select></label>
    <label class="filter">Instructor<select id="nominalInstructor" aria-label="Filtrar por instructor"><option value="">Todos los instructores</option></select></label>
    <label class="filter">Desde<input id="nominalDesde" type="date" aria-label="Fecha inicial del intervalo"></label>
    <label class="filter">Hasta<input id="nominalHasta" type="date" aria-label="Fecha final del intervalo"></label>
    <label class="filter search">Buscar aprendiz<input id="nominalSearch" type="search" placeholder="Nombre o parte del nombre" autocomplete="off" aria-label="Buscar por nombre de aprendiz"></label>
    <div class="nominal-actions"><button class="button secondary" id="nominalReset" type="button">Restablecer</button></div>
   </section>
   <div class="kpis" id="nominalKpis"></div>
   <section class="panel" aria-labelledby="nominalTableTitle">
    <div class="panel-head">
     <div><h2 id="nominalTableTitle">Aprendices del intervalo</h2><p class="note" id="nominalMeta">Seleccione un intervalo para consultar.</p></div>
     <div class="panel-actions"><button class="button secondary" id="nominalExport" type="button">Exportar CSV</button></div>
    </div>
    <div class="table-wrap nominal-table-wrap">
     <table class="table nominal-table">
      <thead><tr><th scope="col">Aprendiz</th><th scope="col">Ficha</th><th scope="col" class="num">Inasistencias</th><th scope="col" class="num">Horas totales</th><th scope="col" class="num">No justificadas</th><th scope="col" class="num">Peor semana</th><th scope="col">Semáforo</th></tr></thead>
      <tbody id="nominalRows"></tbody>
     </table>
     <div class="empty" id="nominalEmpty" hidden>No hay aprendices para los filtros seleccionados.</div>
    </div>
    <div class="table-foot"><span id="nominalCount">Sin datos</span><button class="button secondary" id="nominalMore" type="button" hidden>Mostrar más</button></div>
   </section>
  </section>
"""

PAGE_JS = r"""
(function () {
  'use strict';

  var dataElement = document.getElementById('nominal-data');
  var aggregate = window.ASTINAggregate;
  var metaElement = document.getElementById('nominalMeta');

  if (!dataElement || !aggregate) {
    if (metaElement) metaElement.textContent = 'No fue posible cargar el módulo de consulta nominal.';
    return;
  }

  var dataset;
  try {
    dataset = JSON.parse(dataElement.textContent);
  } catch (error) {
    if (metaElement) metaElement.textContent = 'El archivo local no tiene un bloque de datos válido.';
    return;
  }

  var $ = function (id) { return document.getElementById(id); };
  var els = {
    ficha: $('nominalFicha'),
    instructor: $('nominalInstructor'),
    desde: $('nominalDesde'),
    hasta: $('nominalHasta'),
    search: $('nominalSearch'),
    reset: $('nominalReset'),
    exportCsv: $('nominalExport'),
    kpis: $('nominalKpis'),
    meta: $('nominalMeta'),
    rows: $('nominalRows'),
    empty: $('nominalEmpty'),
    count: $('nominalCount'),
    more: $('nominalMore')
  };
  var pageSize = 100;
  var visible = pageSize;
  var current = null;
  var number = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 1 });
  var dateFormatter = new Intl.DateTimeFormat('es-CO', {
    day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC'
  });

  function formatNumber(value) {
    return number.format(Number(value) || 0);
  }

  function formatDate(value) {
    var text = String(value == null ? '' : value);
    if (!text) return 'sin fecha';
    var date = new Date(text.length === 10 ? text + 'T00:00:00Z' : text);
    if (Number.isNaN(date.valueOf())) return text;
    return dateFormatter.format(date);
  }

  function fillSelect(select, values, placeholder) {
    var currentValue = select.value;
    var list = Array.isArray(values) ? values.map(String) : [];
    select.replaceChildren();
    var first = document.createElement('option');
    first.value = '';
    first.textContent = placeholder;
    select.append(first);
    list.forEach(function (value) {
      var option = document.createElement('option');
      option.value = value;
      option.textContent = value;
      select.append(option);
    });
    select.value = list.indexOf(currentValue) !== -1 ? currentValue : '';
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

  function buildMeta(data) {
    var parts = [];
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

  function renderKpis(data) {
    var values = [
      { label: 'Aprendices', value: data.kpis.aprendices, hint: 'Personas únicas en el intervalo' },
      { label: 'Inasistencias', value: data.kpis.inasistencias, hint: 'Registros de novedad' },
      { label: 'Horas totales', value: data.kpis.horas, hint: 'Horas perdidas en el intervalo' },
      { label: 'Horas no justificadas', value: data.kpis.noJustificadas, hint: 'Prioridad para seguimiento' }
    ];
    els.kpis.innerHTML = values.map(function (item) {
      return '<article class="kpi"><div class="label">' + item.label + '</div>' +
        '<div class="value">' + formatNumber(item.value) + '</div>' +
        '<div class="hint">' + item.hint + '</div></article>';
    }).join('');
  }

  function badgeClass(semaforo) {
    if (semaforo === 'Rojo') return 'red';
    if (semaforo === 'Amarillo') return 'yellow';
    return 'green';
  }

  function appendCell(row, value, className) {
    var cell = document.createElement('td');
    if (className) cell.className = className;
    cell.textContent = value == null ? '' : String(value);
    row.append(cell);
  }

  function renderRows() {
    if (!current) return;
    var rows = current.rows || [];
    els.rows.replaceChildren();

    if (!rows.length) {
      els.empty.hidden = false;
      els.more.hidden = true;
      els.count.textContent = '0 aprendices/ficha';
      return;
    }

    els.empty.hidden = true;
    var shown = rows.slice(0, visible);
    var fragment = document.createDocumentFragment();

    shown.forEach(function (row) {
      var tr = document.createElement('tr');
      appendCell(tr, row.aprendiz, 'name');
      appendCell(tr, row.ficha);
      appendCell(tr, formatNumber(row.inasistencias), 'num');
      appendCell(tr, formatNumber(row.horas), 'num');
      appendCell(tr, formatNumber(row.noJustificadas), 'num');
      appendCell(tr, formatNumber(row.peorSemana), 'num');

      var cell = document.createElement('td');
      var badge = document.createElement('span');
      badge.className = 'badge ' + badgeClass(row.semaforo);
      badge.textContent = row.semaforo || 'Sin dato';
      cell.append(badge);
      tr.append(cell);
      fragment.append(tr);
    });

    els.rows.append(fragment);
    els.count.textContent = formatNumber(rows.length) + ' aprendices/ficha · mostrando ' + formatNumber(shown.length);
    els.more.hidden = rows.length <= visible;
    if (!els.more.hidden) {
      els.more.textContent = 'Mostrar ' + formatNumber(Math.min(pageSize, rows.length - visible)) + ' más';
    }
  }

  function render() {
    var result;
    try {
      result = aggregate.aggregate(dataset, readFilters());
    } catch (error) {
      els.meta.textContent = 'No fue posible consultar los datos: ' + (error.message || 'revise los filtros.');
      return;
    }

    current = result;
    renderKpis(result);
    els.meta.textContent = buildMeta(result);
    renderRows();
  }

  function reset() {
    els.ficha.value = '';
    els.instructor.value = '';
    els.search.value = '';
    var all = aggregate.aggregate(dataset, {});
    els.desde.value = all.filters.minDate || '';
    els.hasta.value = all.filters.maxDate || '';
    visible = pageSize;
    render();
  }

  function csvCell(value) {
    var text = String(value == null ? '' : value);
    if (/[;"\r\n]/.test(text)) return '"' + text.replace(/"/g, '""') + '"';
    return text;
  }

  function exportCsv() {
    if (!current || !current.rows || current.rows.length === 0) {
      els.meta.textContent = 'No hay datos para exportar con los filtros actuales.';
      return;
    }

    var confirmed = window.confirm(
      'El archivo CSV contiene nombres y datos personales de aprendices. ' +
      'Úselo solo para gestión disciplinaria o de Bienestar y no lo comparta por canales abiertos. ¿Desea continuar?'
    );
    if (!confirmed) return;

    var headers = ['Aprendiz', 'Ficha', 'Inasistencias', 'Horas totales', 'Horas no justificadas', 'Peor semana', 'Semáforo'];
    var lines = [headers];
    current.rows.forEach(function (row) {
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

    var csv = lines.map(function (line) {
      return line.map(csvCell).join(';');
    }).join('\r\n');
    var blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' });
    var link = document.createElement('a');
    var prefix = current.meta.synthetic ? 'demo_' : 'local_';
    link.href = URL.createObjectURL(blob);
    link.download = 'consulta_semanal_' + prefix + new Date().toISOString().slice(0, 10) + '.csv';
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(link.href);
  }

  function debounce(fn, wait) {
    var timer = null;
    return function () {
      window.clearTimeout(timer);
      timer = window.setTimeout(fn, wait);
    };
  }

  function init() {
    if (!dataset || !Array.isArray(dataset.records)) {
      els.meta.textContent = 'La fuente local no tiene el formato esperado.';
      return;
    }

    var all;
    try {
      all = aggregate.aggregate(dataset, {});
    } catch (error) {
      els.meta.textContent = 'No fue posible preparar la consulta: ' + (error.message || 'revise los datos.');
      return;
    }

    fillSelect(els.ficha, all.filters.fichas, 'Todas las fichas');
    fillSelect(els.instructor, all.filters.instructores, 'Todos los instructores');
    els.desde.value = all.filters.minDate || '';
    els.hasta.value = all.filters.maxDate || '';

    ['ficha', 'instructor', 'desde', 'hasta'].forEach(function (key) {
      els[key].addEventListener('change', function () {
        visible = pageSize;
        render();
      });
    });
    els.search.addEventListener('input', debounce(function () {
      visible = pageSize;
      render();
    }, 300));
    els.reset.addEventListener('click', reset);
    els.exportCsv.addEventListener('click', exportCsv);
    els.more.addEventListener('click', function () {
      visible += pageSize;
      renderRows();
    });

    function syncNominalView(button) {
      document.body.classList.toggle('nominal-view', Boolean(button && button.dataset.page === 'consulta'));
    }
    document.querySelectorAll('.nav button').forEach(function (button) {
      button.addEventListener('click', function () { syncNominalView(button); });
    });
    syncNominalView(document.querySelector('.nav button.active'));

    render();
  }

  init();
})();
"""


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def as_float(value: str | None) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def load_portal_module():
    if not PORTAL_SCRIPT.exists():
        raise FileNotFoundError(f"No se encontró el generador del portal: {PORTAL_SCRIPT}")
    spec = importlib.util.spec_from_file_location("portal_generator", PORTAL_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar {PORTAL_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_nominal_payload() -> dict:
    if not FACTS.exists():
        raise FileNotFoundError(
            f"No existe {FACTS}. Ejecute primero scripts/01_etl_modelo_estrella.py "
            "o el pipeline scripts/actualizar_datos.ps1."
        )
    if not IDENTITIES.exists():
        raise FileNotFoundError(
            f"No existe {IDENTITIES}. El ETL genera esta tabla restringida; "
            "verifique que el archivo fuente se haya procesado correctamente."
        )

    identities = {
        row["AprendizID"]: row["NombreCompleto"]
        for row in read_csv(IDENTITIES)
        if row.get("AprendizID") and row.get("NombreCompleto")
    }

    records: list[dict] = []
    for row in read_csv(FACTS):
        apprentice_id = row.get("AprendizID", "")
        name = identities.get(apprentice_id)
        if not name:
            continue
        hours = as_float(row.get("CantidadHoras"))
        records.append({
            "id": apprentice_id,
            "name": name,
            "date": row.get("Fecha", ""),
            "ficha": row.get("FichaID", ""),
            "instructor": row.get("Instructor", "") or "Sin instructor",
            "hours": round(hours, 2),
            "unjustified": round(hours if row.get("EsNoJustificada") == "1" else 0.0, 2),
        })

    records.sort(key=lambda item: (item["date"], item["id"], item["ficha"]))
    summary = json.loads(SUMMARY.read_text(encoding="utf-8")) if SUMMARY.exists() else {}
    return {
        "schemaVersion": 1,
        "generatedAt": summary.get("corte", ""),
        "downloadedAt": summary.get("ultima_descarga", ""),
        "sourceLabel": "Corte institucional",
        "synthetic": False,
        "records": records,
    }


def build_demo_payload() -> dict:
    if not DEMO_DATA.exists():
        raise FileNotFoundError(
            f"No existe {DEMO_DATA}. Genérelo con: python scripts/07_exportar_consulta_web.py --demo"
        )
    payload = json.loads(DEMO_DATA.read_text(encoding="utf-8"))
    if not isinstance(payload.get("records"), list):
        raise ValueError(f"{DEMO_DATA} no tiene una lista de registros válida.")
    return payload


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"No se encontró el punto de inserción esperado: {label}")
    return text.replace(old, new, 1)


def build_portal_html(nominal: dict, synthetic: bool) -> str:
    portal = load_portal_module()
    if not portal.CHART_JS.exists():
        raise FileNotFoundError(f"No se encontró Chart.js: {portal.CHART_JS}")

    data = portal.build_payload()
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    chart_js = portal.CHART_JS.read_text(encoding="utf-8").replace("</script>", "<\\/script>")
    logo = base64.b64encode(portal.LOGO.read_bytes()).decode("ascii") if portal.LOGO.exists() else ""
    html = (
        portal.HTML_TEMPLATE
        .replace("@@DATA@@", data_json)
        .replace("@@CHARTJS@@", chart_js)
        .replace("@@LOGO@@", logo)
    )

    nav_old = '<button data-page="calidad">04 · Calidad de datos</button>'
    nav_new = nav_old + '<button data-page="consulta">05 · Consulta semanal</button>'
    html = replace_once(html, nav_old, nav_new, "navegación de la página 05")

    flag = "MODO LOCAL · DEMOSTRACIÓN" if synthetic else "MODO LOCAL · DATOS NOMINALES"
    sidebar_old = (
        '<div class="sidebar-foot">ÚLTIMA DESCARGA<strong id="sideDate"></strong>'
        '<span id="sideRows"></span></div>'
    )
    sidebar_new = (
        '<div class="sidebar-foot">ÚLTIMA DESCARGA<strong id="sideDate"></strong>'
        '<span id="sideRows"></span><span class="local-flag">' + flag + '</span></div>'
    )
    html = replace_once(html, sidebar_old, sidebar_new, "nota del modo local")

    warning = (
        "<strong>Demostración sintética.</strong> Los nombres, fichas e instructores son ficticios. "
        "Este archivo sirve para revisar la interfaz, no para gestión real."
        if synthetic
        else "<strong>Información sensible.</strong> Este archivo contiene nombres reales de aprendices. "
        "Úselo solo en el equipo autorizado, no lo comparta por canales abiertos y elimínelo cuando termine."
    )
    page_html = PAGE_HTML.replace("@@WARNING@@", warning)
    html = replace_once(html, "</style>", PAGE_CSS + "\n</style>", "estilos de la página 05")
    html = replace_once(
        html,
        ' <footer class="page-footer">',
        page_html + '\n <footer class="page-footer">',
        "sección de la página 05",
    )

    nominal_json = (
        json.dumps(nominal, ensure_ascii=False, separators=(",", ":"))
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    aggregate_path = AGGREGATE_SOURCE if AGGREGATE_SOURCE.exists() else AGGREGATE_FALLBACK
    if not aggregate_path.exists():
        raise FileNotFoundError("No se encontró la lógica de agregación compartida.")
    aggregate_js = aggregate_path.read_text(encoding="utf-8").replace("</script>", "<\\/script>")

    injection = (
        '<script id="nominal-data" type="application/json">' + nominal_json + '</script>\n'
        '<script>' + aggregate_js + '</script>\n'
        '<script>' + PAGE_JS + '</script>\n'
    )
    html = replace_once(html, "</body>", injection + "</body>", "scripts de la página 05")
    return html


def write_output(html: str, destination: Path) -> None:
    resolved = destination.resolve()
    forbidden = [ROOT / "web", ROOT / "github-pages", ROOT / "data", ROOT / "api"]
    for folder in forbidden:
        try:
            resolved.relative_to(folder.resolve())
        except ValueError:
            continue
        raise SystemExit(
            f"ERROR: no escriba el portal local dentro de {folder}. "
            "Use outputs/ para no mezclar datos nominales con archivos publicables."
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(html, encoding="utf-8")


def summarize(nominal: dict, destination: Path) -> str:
    records = nominal.get("records", [])
    dates = [record.get("date", "") for record in records if record.get("date")]
    learners = {record.get("id") for record in records if record.get("id")}
    return (
        f"{destination} · {len(records):,} registros · {len(learners):,} aprendices · "
        f"{min(dates) if dates else 'sin fecha'} a {max(dates) if dates else 'sin fecha'} · "
        f"{destination.stat().st_size:,} bytes"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Usa datos sintéticos de web/data/demo_consulta.json.")
    parser.add_argument("--out", type=Path, help="Ruta de salida alternativa (fuera de web/ y data/).")
    args = parser.parse_args()

    nominal = build_demo_payload() if args.demo else build_nominal_payload()
    if not nominal.get("records"):
        print("AVISO: no hay registros nominales para incrustar. El portal se generará sin datos en la página 05.")
    destination = args.out or (DEMO_OUT if args.demo else DEFAULT_OUT)
    html = build_portal_html(nominal, synthetic=args.demo)
    write_output(html, destination)

    print(f"Portal local generado: {destination}")
    print(summarize(nominal, destination))
    if args.demo:
        print("Modo demostración: los nombres son sintéticos y el archivo puede compartirse para revisión de interfaz.")
    else:
        print("AVISO: este HTML contiene datos personales. No lo agregue a Git, no lo publique y elimínelo cuando termine.")
        print("Para borrarlo: .\\scripts\\11_limpiar_consulta_local.ps1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
