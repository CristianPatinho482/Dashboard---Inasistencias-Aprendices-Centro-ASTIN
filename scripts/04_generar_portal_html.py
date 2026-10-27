# -*- coding: utf-8 -*-
"""Build a single-file, offline-capable ASTIN dashboard from processed aggregates.

Only aggregate records are embedded. No apprentice identifiers, names, documents,
instructors, or free-text justifications are written to the portal.
"""
from __future__ import annotations

import base64
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
OUT = ROOT / "outputs" / "portal_astin.html"
CHART_JS = ROOT / "tools" / "chartjs" / "chart.umd.min.js"
LOGO = ROOT / "CaracterizacionAprendicesASTIN.Report" / "StaticResources" / "RegisteredResources" / "sena_logo.png"


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def n(row: dict[str, str], key: str) -> int:
    try:
        return int(float(row.get(key, "") or 0))
    except (TypeError, ValueError):
        return 0


def f(row: dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, "") or 0)
    except (TypeError, ValueError):
        return 0.0


def compact_records(groups: dict, dimensions: tuple[str, ...], fields: tuple[str, ...]) -> list[dict]:
    result = []
    for key, metrics in groups.items():
        if not isinstance(key, tuple):
            key = (key,)
        item = dict(zip(dimensions, key))
        item.update({field: len(metrics[field]) if isinstance(metrics[field], set) else metrics[field] for field in fields})
        result.append(item)
    return result


def build_payload() -> dict:
    summary = json.loads((DATA / "00_resumen_etl.json").read_text(encoding="utf-8"))
    programs_src = read_csv("DIM_PROGRAMA.csv")
    fichas_src = read_csv("DIM_FICHA.csv")
    learners_src = read_csv("DIM_APRENDIZ.csv")
    facts = read_csv("FACT_INASISTENCIAS.csv")

    program_names = {r["ProgramaID"]: r["NombrePrograma"] for r in programs_src}
    months: dict[tuple, dict] = defaultdict(lambda: {"events": 0, "hours": 0, "learners": set(), "fichas": set(), "programs": set()})
    reasons: dict[tuple, dict] = defaultdict(lambda: {"events": 0, "hours": 0})
    yearly: dict[tuple, dict] = defaultdict(lambda: {"events": 0, "hours": 0, "notJustHours": 0, "learners": set(), "fichas": set()})
    yearly_totals: dict[str, dict] = defaultdict(lambda: {"events": 0, "hours": 0, "learners": set(), "fichas": set(), "programs": set()})
    program_fichas: dict[str, set[str]] = defaultdict(set)

    for row in facts:
        program = row["ProgramaID"]
        year = row["Fecha"][:4]
        month = row["Fecha"][:7]
        apprentice = row["AprendizID"]
        ficha = row["FichaID"]
        hours = n(row, "CantidadHoras")
        bucket = months[(program, year, month)]
        bucket["events"] += 1
        bucket["hours"] += hours
        bucket["learners"].add(apprentice)
        bucket["fichas"].add(ficha)
        bucket["programs"].add(program)
        bucket = yearly[(program, year)]
        bucket["events"] += 1
        bucket["hours"] += hours
        if n(row, "EsNoJustificada") == 1:
            bucket["notJustHours"] += hours
        bucket["learners"].add(apprentice)
        bucket["fichas"].add(ficha)
        bucket = yearly_totals[year]
        bucket["events"] += 1
        bucket["hours"] += hours
        bucket["learners"].add(apprentice)
        bucket["fichas"].add(ficha)
        bucket["programs"].add(program)
        program_fichas[program].add(ficha)
        reason = row.get("CategoriaJustificacion") or "Sin información"
        bucket = reasons[(program, year, reason)]
        bucket["events"] += 1
        bucket["hours"] += hours

    programs = []
    for row in programs_src:
        program = row["ProgramaID"]
        programs.append({
            "id": program,
            "name": row["NombrePrograma"],
            "line": row.get("LineaFormacion", "Sin dato"),
            "learners": n(row, "Aprendices"),
            "events": n(row, "Inasistencias"),
            "hours": n(row, "Horas"),
            "hoursNotJust": n(row, "HorasNoJustificadas"),
            "pctNotJust": f(row, "PctHorasNoJust"),
            "riskIndex": f(row, "IndiceRiesgoCorte"),
            "risk": row.get("NivelRiesgoCorte", "Sin dato"),
            "sample": n(row, "MuestraSuficiente"),
            "fichas": len(program_fichas.get(program, set())),
        })

    # Ficha-level rows are aggregate-only and exclude low-sample groups.
    fichas = []
    for row in fichas_src:
        if n(row, "MuestraSuficiente") != 1 or n(row, "Aprendices") < 5:
            continue
        fichas.append({
            "id": row["FichaID"],
            "program": row["ProgramaID"],
            "programName": program_names.get(row["ProgramaID"], "Programa sin catálogo"),
            "learners": n(row, "Aprendices"),
            "events": n(row, "Inasistencias"),
            "hours": n(row, "Horas"),
            "riskIndex": f(row, "IndiceRiesgoCorte"),
            "risk": row.get("NivelRiesgoCorte", "Sin dato"),
        })

    learner_risk: dict[tuple, int] = defaultdict(int)
    learner_flags: dict[str, dict] = defaultdict(lambda: {"recurrent": 0, "highRecurrent": 0, "dropoutAlerts": 0})
    for row in learners_src:
        program = row.get("ProgramaPrincipal", "")
        learner_risk[(program, row.get("NivelRiesgo", "Sin dato"))] += 1
        flags = learner_flags[program]
        flags["recurrent"] += n(row, "EsReincidente")
        flags["highRecurrent"] += n(row, "EsReincidenteAlto")
        flags["dropoutAlerts"] += n(row, "AlertaDesercion")

    quality = summary.get("calidad", {})
    return {
        "generatedAt": summary.get("corte", ""),
        "summary": {
            "events": n(summary, "registros_validos"),
            "hours": n(summary, "horas_perdidas"),
            "learners": n(summary, "aprendices_unicos"),
            "fichas": n(summary, "fichas"),
            "programs": n(summary, "programas"),
            "pctJustified": f(summary, "pct_inasistencias_justificadas") / 100,
            "pctNotJustified": f(summary, "pct_inasistencias_no_justificadas") / 100,
            "pctUnknown": f(summary, "pct_inasistencias_sin_informacion") / 100,
            "duplicateRows": n(summary, "duplicados_exactos"),
            "invalidRows": n(summary, "registros_invalidos"),
            "reviewRows": n(summary, "registros_requieren_revision"),
            "reviewPct": f(summary, "pct_registros_requieren_revision") / 100,
            "outlierRows": n(summary, "registros_outlier_horas"),
            "unclassifiedRows": n(summary, "registros_no_clasificados"),
            "missingReasonRows": n(summary, "registros_sin_justificacion"),
            "supportedRows": n(summary, "registros_con_soporte"),
            "uniqueReasons": n(summary, "justificaciones_unicas"),
            "coverage": quality,
            "fichaRiskCounts": summary.get("fichas_evaluadas", 0),
            "highRiskFichas": n(summary, "fichas_alto_riesgo"),
            "highRiskPrograms": n(summary, "programas_alto_riesgo"),
            "dropoutAlerts": n(summary, "aprendices_alerta_desercion"),
        },
        "programs": programs,
        "fichas": fichas,
        "months": compact_records(months, ("program", "year", "month"), ("events", "hours", "learners", "fichas")),
        "years": compact_records(yearly, ("program", "year"), ("events", "hours", "notJustHours", "learners", "fichas")),
        "yearTotals": compact_records(yearly_totals, ("year",), ("events", "hours", "learners", "fichas", "programs")),
        "reasons": compact_records(reasons, ("program", "year", "reason"), ("events", "hours")),
        "learnerRisk": [{"program": p, "risk": risk, "learners": count} for (p, risk), count in learner_risk.items()],
        "learnerFlags": [{"program": p, **values} for p, values in learner_flags.items()],
    }


HTML_TEMPLATE = r'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Portal ejecutivo de caracterización e inasistencias del Centro ASTIN.">
<meta name="theme-color" content="#00304d">
<title>Reportes de Inasistencias · Centro ASTIN</title>
<style>
:root{--navy:#00304d;--green:#39a900;--green-dark:#007a33;--cyan:#50e5f9;--yellow:#fdc300;--ink:#153849;--muted:#617982;--paper:#f3f7f4;--surface:#fff;--line:#dce7e1;--red:#b42318;--shadow:0 8px 24px rgba(0,48,77,.06)}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:"Work Sans","Segoe UI",Arial,sans-serif;font-size:14px}button,select{font:inherit}.app{min-height:100vh}.sidebar{position:fixed;inset:0 auto 0 0;width:230px;background:var(--navy);color:#fff;padding:22px 14px;display:flex;flex-direction:column;z-index:5}.brand{display:flex;align-items:center;gap:12px;padding:0 8px 22px;border-bottom:1px solid rgba(255,255,255,.14)}.brand img{width:48px;height:48px;object-fit:contain;background:#fff;padding:5px}.brand strong{display:block;font-size:15px;letter-spacing:.12em}.brand span{display:block;color:#b8d0dc;font-size:11px;margin-top:4px}.nav-label{font-size:10px;letter-spacing:.12em;color:#99b3c0;margin:24px 10px 9px}.nav{display:grid;gap:5px}.nav button{border:0;color:#c3d3dc;text-align:left;background:transparent;padding:11px 12px;border-radius:7px;font-weight:600;font-size:13px;cursor:pointer}.nav button:hover{background:rgba(255,255,255,.08);color:#fff}.nav button.active{background:var(--green);color:#fff}.sidebar-foot{margin-top:auto;border-top:1px solid rgba(255,255,255,.14);padding:15px 9px 0;color:#b8cbd5;font-size:11px;line-height:1.7}.sidebar-foot strong{display:block;color:#fff;font-size:12px}.main{margin-left:230px;min-height:100vh;padding:28px clamp(20px,3vw,48px) 35px;max-width:1800px}.topbar{display:flex;justify-content:space-between;align-items:flex-start;gap:18px;margin-bottom:20px}.eyebrow{color:var(--green-dark);font-size:11px;font-weight:800;letter-spacing:.12em;text-transform:uppercase}.topbar h1{font-size:clamp(25px,2.4vw,36px);line-height:1.12;color:var(--navy);margin:7px 0 7px;letter-spacing:-.025em}.subtitle{color:var(--muted);font-size:14px;margin:0;max-width:720px}.filters{display:flex;gap:10px;flex-wrap:wrap;justify-content:flex-end}.filter{display:grid;gap:5px;color:var(--muted);font-weight:700;font-size:11px}.filter select{min-width:150px;border:1px solid var(--line);border-radius:7px;background:#fff;color:var(--ink);padding:9px 30px 9px 11px;box-shadow:0 2px 5px rgba(0,48,77,.03)}.page{display:none}.page.active{display:block}.kpis{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin:18px 0}.kpi{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:15px 16px;box-shadow:var(--shadow);min-height:98px}.kpi .label{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);font-weight:700}.kpi .value{font-size:clamp(22px,2vw,30px);font-weight:800;color:var(--navy);margin-top:10px;line-height:1}.kpi .hint{font-size:11px;color:var(--muted);margin-top:7px}.grid{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:14px;margin-bottom:14px}.panel{grid-column:span 6;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:16px 17px;box-shadow:var(--shadow);min-width:0}.panel.span-12{grid-column:span 12}.panel.span-8{grid-column:span 8}.panel.span-4{grid-column:span 4}.panel h2{font-size:15px;margin:0;color:var(--navy)}.panel .desc{font-size:12px;color:var(--muted);margin:5px 0 12px}.chart-wrap{height:285px;position:relative}.chart-wrap.tall{height:345px}.chart-wrap.short{height:230px}.table-wrap{overflow:auto}.table{width:100%;border-collapse:collapse;font-size:12px}.table th{text-align:left;color:var(--navy);font-size:10px;text-transform:uppercase;letter-spacing:.05em;background:#edf5ea;position:sticky;top:0}.table td,.table th{padding:10px 9px;border-bottom:1px solid #e8efeb;white-space:nowrap}.table td.num,.table th.num{text-align:right;font-variant-numeric:tabular-nums}.table tr:last-child td{border-bottom:0}.badge{display:inline-flex;padding:4px 8px;border-radius:20px;font-weight:700;font-size:10px;background:#e8f5e2;color:#276900}.badge.medium{background:#fff5d6;color:#765b00}.badge.high{background:#fde8e7;color:#a62219}.notice{border-left:4px solid var(--yellow);background:#fff9e6;padding:12px 14px;border-radius:0 7px 7px 0;color:#634d00;font-size:12px;line-height:1.5;margin:12px 0}.quality-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.quality-item{border-bottom:1px solid var(--line);padding:12px 4px}.quality-item span{display:block;color:var(--muted);font-size:11px}.quality-item strong{display:block;margin-top:5px;font-size:20px;color:var(--navy)}.page-footer{display:flex;justify-content:space-between;gap:12px;border-top:1px solid var(--line);padding-top:14px;color:#788b91;font-size:11px;margin-top:22px}.empty{color:var(--muted);padding:22px;text-align:center}.mobile-nav{display:none}
 .sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
@media(max-width:1100px){.sidebar{width:205px}.main{margin-left:205px;padding:22px}.kpis{grid-template-columns:repeat(3,minmax(0,1fr))}.panel.span-8,.panel.span-4{grid-column:span 6}}
@media(max-width:760px){.sidebar{position:sticky;top:0;width:auto;height:auto;padding:10px 12px;display:block}.brand{padding:0 4px 9px;border:0}.brand img{width:36px;height:36px}.brand strong{font-size:13px}.nav-label,.sidebar-foot{display:none}.nav{display:flex;overflow:auto;padding:4px 0 2px;gap:4px}.nav button{white-space:nowrap;padding:9px 10px;font-size:12px}.main{margin:0;padding:18px 14px 24px}.topbar{display:grid}.filters{justify-content:flex-start}.filter select{min-width:135px}.kpis{grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.kpi{min-height:88px;padding:13px}.kpi .value{font-size:24px}.panel,.panel.span-8,.panel.span-4{grid-column:span 12;padding:14px}.chart-wrap{height:260px}.chart-wrap.tall{height:300px}.quality-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.page-footer{display:grid}}
</style>
</head>
<body>
<div class="app">
<aside class="sidebar" aria-label="Navegación principal">
 <div class="brand"><img src="data:image/png;base64,@@LOGO@@" alt="Logo SENA"><div><strong>SENA</strong><span>Centro ASTIN · Regional Valle</span></div></div>
 <div class="nav-label">PORTAL ACADÉMICO</div>
 <nav class="nav" aria-label="Secciones del portal">
  <button class="active" data-page="inicio">00 · Inicio</button><button data-page="caracterizacion">01 · Caracterización</button><button data-page="riesgo">02 · Fichas y programas en riesgo</button><button data-page="detalle">03 · Análisis detallado</button><button data-page="calidad">04 · Calidad de datos</button>
 </nav>
 <div class="sidebar-foot">CORTE DE INFORMACIÓN<strong id="sideDate"></strong><span id="sideRows"></span></div>
</aside>
<main class="main">
 <header class="topbar"><div><div class="eyebrow">Centro ASTIN · Valle del Cauca</div><h1>Reportes de Inasistencias</h1><p class="subtitle">Seguimiento ejecutivo de inasistencias, horas perdidas y alertas para orientar el acompañamiento académico.</p></div>
  <div class="filters"><label class="filter">Programa<select id="programFilter" aria-label="Filtrar por programa"><option value="all">Todos los programas</option></select></label><label class="filter">Año<select id="yearFilter" aria-label="Filtrar por año"><option value="all">Todos los años</option></select></label></div>
 </header>

 <section class="page active" id="page-inicio" aria-labelledby="title-inicio">
  <h2 id="title-inicio" class="sr-only">Resumen ejecutivo</h2>
  <div class="kpis" id="kpis"></div>
  <div class="grid"><article class="panel span-8"><h2>Tendencia de inasistencias</h2><p class="desc">Novedades y horas perdidas por mes de inicio.</p><div class="chart-wrap"><canvas id="monthlyChart" role="img" aria-label="Tendencia mensual de inasistencias y horas"></canvas></div></article>
   <article class="panel span-4"><h2>Clasificación de justificación</h2><p class="desc">Participación de registros por categoría.</p><div class="chart-wrap"><canvas id="reasonChart" role="img" aria-label="Distribución de inasistencias justificadas y no justificadas"></canvas></div></article></div>
  <div class="grid"><article class="panel"><h2>Top 10 fichas por horas perdidas</h2><p class="desc">Solo fichas con muestra suficiente (cinco o más aprendices).</p><div class="chart-wrap tall"><canvas id="fichaChart" role="img" aria-label="Top diez fichas por horas perdidas"></canvas></div></article>
   <article class="panel"><h2>Programas con más horas perdidas</h2><p class="desc">Selecciona una barra para filtrar el portal por programa.</p><div class="chart-wrap tall"><canvas id="programChart" role="img" aria-label="Programas ordenados por horas perdidas"></canvas></div></article></div>
 </section>

 <section class="page" id="page-caracterizacion" aria-labelledby="title-caracterizacion">
  <div class="grid"><article class="panel span-4"><h2>Aprendices por nivel de riesgo</h2><p class="desc">Clasificación operativa del último corte.</p><div class="chart-wrap"><canvas id="learnerRiskChart" role="img" aria-label="Aprendices por nivel de riesgo"></canvas></div></article>
   <article class="panel span-8"><h2>Aprendices afectados por programa</h2><p class="desc">Conteo de aprendices únicos asociados a novedades.</p><div class="chart-wrap"><canvas id="learnerProgramChart" role="img" aria-label="Aprendices afectados por programa"></canvas></div></article></div>
  <div class="grid"><article class="panel span-12"><h2>Distribución por línea de formación</h2><p class="desc">Programas, aprendices y horas perdidas del conjunto seleccionado.</p><div class="table-wrap" id="lineTable"></div></article></div>
 </section>

 <section class="page" id="page-riesgo" aria-labelledby="title-riesgo">
  <div class="kpis" id="riskKpis"></div>
  <div class="grid"><article class="panel"><h2>Fichas con mayor índice de riesgo</h2><p class="desc">Puntuación relativa para priorizar revisión, no probabilidad de deserción.</p><div class="chart-wrap tall"><canvas id="fichaRiskChart" role="img" aria-label="Fichas priorizadas por índice de riesgo"></canvas></div></article>
   <article class="panel"><h2>Programas con mayor índice de riesgo</h2><p class="desc">Solo programas con tamaño muestral suficiente.</p><div class="chart-wrap tall"><canvas id="programRiskChart" role="img" aria-label="Programas priorizados por índice de riesgo"></canvas></div></article></div>
  <div class="grid"><article class="panel span-12"><h2>Fichas priorizadas</h2><div class="table-wrap" id="riskTable"></div></article></div>
 </section>

 <section class="page" id="page-detalle" aria-labelledby="title-detalle">
  <div class="grid"><article class="panel span-12"><h2>Programas · volumen y participación</h2><p class="desc">Horas perdidas, aprendices afectados y porcentaje de las horas del conjunto seleccionado.</p><div class="table-wrap" id="programTable"></div></article></div>
  <div class="grid"><article class="panel span-12"><h2>Motivos de inasistencia</h2><p class="desc">Clasificación basada en reglas auditables; los casos sin información requieren revisión.</p><div class="table-wrap" id="reasonTable"></div></article></div>
 </section>

 <section class="page" id="page-calidad" aria-labelledby="title-calidad">
  <div class="notice">Las alertas y clasificaciones son señales de análisis para validar con el equipo académico. No constituyen decisiones sobre matrícula, sanciones ni deserción.</div>
  <article class="panel span-12"><h2>Indicadores de calidad</h2><p class="desc">Control del archivo fuente y de las reglas de preparación.</p><div class="quality-grid" id="qualityGrid"></div></article>
  <div class="grid" style="margin-top:14px"><article class="panel span-12"><h2>Cobertura disponible</h2><div id="coverage"></div></article></div>
 </section>

 <footer class="page-footer"><span>SENA · Centro ASTIN · Regional Valle del Cauca</span><span>Fuente: archivo Inasistencias · Datos agregados para seguimiento institucional</span></footer>
</main>
</div>
<script id="portal-data" type="application/json">@@DATA@@</script>
<script>@@CHARTJS@@</script>
<script>
"use strict";
const D=JSON.parse(document.getElementById("portal-data").textContent);
const C={green:"#39a900",greenDark:"#007a33",navy:"#00304d",cyan:"#148da4",yellow:"#c99b00",red:"#b42318",muted:"#617982",line:"#dce7e1"};
const byId=id=>document.getElementById(id), money=n=>new Intl.NumberFormat("es-CO").format(Math.round(n||0)), pct=n=>new Intl.NumberFormat("es-CO",{style:"percent",maximumFractionDigits:1}).format(n||0), riskClass=x=>x==="Alto"?"high":x==="Medio"?"medium":"";
const programFilter=byId("programFilter"),yearFilter=byId("yearFilter"),charts={};
const programName=id=>D.programs.find(x=>x.id===id)?.name||"Programa sin catálogo";
const sortBy=(a,key)=>[...a].sort((x,y)=>(y[key]||0)-(x[key]||0));
const filterRows=(rows,p,y)=>rows.filter(x=>(p==="all"||x.program===p)&&(y==="all"||x.year===y));
function current(){return {p:programFilter.value,y:yearFilter.value}}
function scopedPrograms(p){return D.programs.filter(x=>p==="all"||x.id===p)}
function periodPrograms(p,y){if(y==="all")return scopedPrograms(p);return D.years.filter(x=>x.year===y&&(p==="all"||x.program===p)).map(x=>{const base=D.programs.find(a=>a.id===x.program)||{};return {...base,events:x.events,hours:x.hours,learners:x.learners,fichas:x.fichas,pctNotJust:x.hours?x.notJustHours/x.hours:0}})}
function kpiValues(){const {p,y}=current();let events=0,hours=0,learners=0,fichas=0,programs=0;
 if(y==="all"&&p==="all"){({events,hours,learners,fichas,programs}=D.summary)}
 else if(y==="all") {const x=D.programs.find(a=>a.id===p);if(x){events=x.events;hours=x.hours;learners=x.learners;fichas=x.fichas;programs=1}}
 else if(p==="all"){const x=D.yearTotals.find(a=>a.year===y);if(x){events=x.events;hours=x.hours;learners=x.learners;fichas=x.fichas;programs=x.programs}}
 else {const x=D.years.find(a=>a.program===p&&a.year===y);if(x){events=x.events;hours=x.hours;learners=x.learners;fichas=x.fichas;programs=1}}
 return [{label:"Total inasistencias",value:events,hint:"Registros depurados"},{label:"Horas perdidas",value:hours,hint:"Horas reportadas"},{label:"Aprendices afectados",value:learners,hint:"Conteo único en el filtro"},{label:"Fichas afectadas",value:fichas,hint:"Fichas con novedades"},{label:"Programas afectados",value:programs,hint:"Programas con novedades"}];}
function renderKpis(){byId("kpis").innerHTML=kpiValues().map(x=>`<article class="kpi"><div class="label">${x.label}</div><div class="value">${money(x.value)}</div><div class="hint">${x.hint}</div></article>`).join("")}
function upsert(id,type,data,options){if(charts[id]){charts[id].data=data;charts[id].options=options;charts[id].update()}else charts[id]=new Chart(byId(id),{type,data,options})}
const baseOptions={responsive:true,maintainAspectRatio:false,animation:{duration:280},plugins:{legend:{labels:{usePointStyle:true,boxWidth:8,font:{family:"Segoe UI",size:11},color:C.muted}},tooltip:{backgroundColor:C.navy,padding:10,titleFont:{size:12},bodyFont:{size:11}}}};
function renderMonthly(){const {p,y}=current();const rows=filterRows(D.months,p,y).sort((a,b)=>a.month.localeCompare(b.month));const labels=[...new Set(rows.map(x=>x.month))];const events=labels.map(m=>rows.filter(x=>x.month===m).reduce((s,x)=>s+x.events,0));const hours=labels.map(m=>rows.filter(x=>x.month===m).reduce((s,x)=>s+x.hours,0));upsert("monthlyChart","line",{labels,datasets:[{label:"Inasistencias",data:events,borderColor:C.green,backgroundColor:C.green,tension:.28,yAxisID:"y",pointRadius:2},{label:"Horas perdidas",data:hours,borderColor:C.navy,backgroundColor:C.navy,tension:.28,yAxisID:"y1",pointRadius:2}]},{...baseOptions,interaction:{mode:"index",intersect:false},scales:{x:{grid:{display:false},ticks:{color:C.muted,maxRotation:0,autoSkip:true}},y:{beginAtZero:true,title:{display:true,text:"Inasistencias"},grid:{color:"#edf2ef"},ticks:{color:C.muted}},y1:{beginAtZero:true,position:"right",title:{display:true,text:"Horas"},grid:{drawOnChartArea:false},ticks:{color:C.muted}}}})}
function renderReasons(){const {p,y}=current();const rows=filterRows(D.reasons,p,y).reduce((m,x)=>{const a=m.get(x.reason)||{events:0,hours:0};a.events+=x.events;a.hours+=x.hours;m.set(x.reason,a);return m},new Map());const labels=[...rows.keys()];const vals=labels.map(k=>rows.get(k).events);upsert("reasonChart","doughnut",{labels,datasets:[{data:vals,backgroundColor:[C.green,C.navy,C.yellow,"#50a69a","#7aa8b8"],borderWidth:0,hoverOffset:5}]},{...baseOptions,cutout:"67%",plugins:{...baseOptions.plugins,legend:{position:"bottom",labels:{...baseOptions.plugins.legend.labels,padding:13}}}})}
function renderFichas(){const {p}=current();const rows=sortBy(D.fichas.filter(x=>p==="all"||x.program===p),"hours").slice(0,10).reverse();upsert("fichaChart","bar",{labels:rows.map(x=>x.id),datasets:[{label:"Horas perdidas",data:rows.map(x=>x.hours),backgroundColor:C.green,borderRadius:4,maxBarThickness:22}]},{...baseOptions,indexAxis:"y",plugins:{...baseOptions.plugins,legend:{display:false},tooltip:{...baseOptions.plugins.tooltip,callbacks:{afterLabel:c=>`${programName(rows[c.dataIndex].program)} · ${money(rows[c.dataIndex].learners)} aprendices`}}},scales:{x:{beginAtZero:true,grid:{color:"#edf2ef"},ticks:{color:C.muted}},y:{grid:{display:false},ticks:{color:C.ink||C.navy,font:{size:10}}}}})}
function renderPrograms(){const {p,y}=current();const rows=sortBy(periodPrograms(p,y),"hours").slice(0,10).reverse();upsert("programChart","bar",{labels:rows.map(x=>x.name),datasets:[{label:"Horas perdidas",data:rows.map(x=>x.hours),backgroundColor:C.green,borderRadius:4,maxBarThickness:22}]},{...baseOptions,indexAxis:"y",onClick:(e,els)=>{if(els.length){programFilter.value=rows[els[0].index].id;renderAll()}},plugins:{...baseOptions.plugins,legend:{display:false},tooltip:{...baseOptions.plugins.tooltip,callbacks:{afterLabel:c=>`${money(rows[c.dataIndex].learners)} aprendices · ${pct(rows[c.dataIndex].hours/(kpiValues()[1].value||1))} de horas seleccionadas`}}},scales:{x:{beginAtZero:true,grid:{color:"#edf2ef"},ticks:{color:C.muted}},y:{grid:{display:false},ticks:{color:C.navy,font:{size:10},callback:function(v){const label=this.getLabelForValue(v);return label.length>35?label.slice(0,33)+"…":label}}}}})}
function renderLearnerRisk(){const {p}=current();const rows=D.learnerRisk.filter(x=>p==="all"||x.program===p).reduce((m,x)=>{m[x.risk]=(m[x.risk]||0)+x.learners;return m},{});const labels=["Bajo","Medio","Alto"],colors=[C.green,C.yellow,C.red];upsert("learnerRiskChart","doughnut",{labels,datasets:[{data:labels.map(x=>rows[x]||0),backgroundColor:colors,borderWidth:0}]},{...baseOptions,cutout:"64%",plugins:{...baseOptions.plugins,legend:{position:"bottom",labels:baseOptions.plugins.legend.labels}}})}
function renderLearnerPrograms(){const {p,y}=current();const rows=sortBy(periodPrograms(p,y),"learners").slice(0,12).reverse();upsert("learnerProgramChart","bar",{labels:rows.map(x=>x.name),datasets:[{label:"Aprendices afectados",data:rows.map(x=>x.learners),backgroundColor:C.navy,borderRadius:4,maxBarThickness:23}]},{...baseOptions,indexAxis:"y",plugins:{...baseOptions.plugins,legend:{display:false}},scales:{x:{beginAtZero:true,grid:{color:"#edf2ef"},ticks:{color:C.muted}},y:{grid:{display:false},ticks:{color:C.navy,font:{size:10},callback:function(v){const s=this.getLabelForValue(v);return s.length>35?s.slice(0,33)+"…":s}}}}})}
function renderRisk(){const {p}=current();const fs=sortBy(D.fichas.filter(x=>(p==="all"||x.program===p)&&x.riskIndex>0),"riskIndex").slice(0,10).reverse();upsert("fichaRiskChart","bar",{labels:fs.map(x=>x.id),datasets:[{label:"Índice de riesgo",data:fs.map(x=>x.riskIndex),backgroundColor:fs.map(x=>x.risk==="Alto"?C.red:x.risk==="Medio"?C.yellow:C.green),borderRadius:4}]},{...baseOptions,indexAxis:"y",plugins:{...baseOptions.plugins,legend:{display:false}},scales:{x:{min:0,max:100,grid:{color:"#edf2ef"},ticks:{color:C.muted}},y:{grid:{display:false},ticks:{color:C.navy}}}});const ps=sortBy(scopedPrograms(p).filter(x=>x.sample===1),"riskIndex").slice(0,10).reverse();upsert("programRiskChart","bar",{labels:ps.map(x=>x.name),datasets:[{label:"Índice de riesgo",data:ps.map(x=>x.riskIndex),backgroundColor:ps.map(x=>x.risk==="Alto"?C.red:x.risk==="Medio"?C.yellow:C.green),borderRadius:4}]},{...baseOptions,indexAxis:"y",plugins:{...baseOptions.plugins,legend:{display:false}},scales:{x:{min:0,max:100,grid:{color:"#edf2ef"},ticks:{color:C.muted}},y:{grid:{display:false},ticks:{color:C.navy,font:{size:10},callback:function(v){const s=this.getLabelForValue(v);return s.length>35?s.slice(0,33)+"…":s}}}}});byId("riskKpis").innerHTML=[{label:"Fichas en riesgo alto",value:D.summary.highRiskFichas},{label:"Programas en riesgo alto",value:D.summary.highRiskPrograms},{label:"Aprendices con alerta",value:D.summary.dropoutAlerts}].map(x=>`<article class="kpi"><div class="label">${x.label}</div><div class="value">${money(x.value)}</div><div class="hint">Corte ${D.generatedAt}</div></article>`).join("");const data=sortBy(D.fichas.filter(x=>(p==="all"||x.program===p)&&x.riskIndex>0),"riskIndex").slice(0,12);byId("riskTable").innerHTML=table(["Ficha","Programa","Aprendices","Horas","Índice","Nivel"],data.map(x=>[x.id,x.programName,money(x.learners),money(x.hours),x.riskIndex.toFixed(1),`<span class="badge ${riskClass(x.risk)}">${x.risk}</span>`]),[2,3,4])}
function table(headers,rows,numeric=[]){if(!rows.length)return'<div class="empty">Sin datos para los filtros seleccionados.</div>';return`<table class="table"><thead><tr>${headers.map((x,i)=>`<th class="${numeric.includes(i)?"num":""}">${x}</th>`).join("")}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map((x,i)=>`<td class="${numeric.includes(i)?"num":""}">${x}</td>`).join("")}</tr>`).join("")}</tbody></table>`}
function renderTables(){const {p}=current();const progs=sortBy(scopedPrograms(p),"hours");byId("lineTable").innerHTML=table(["Programa","Línea de formación","Aprendices","Inasistencias","Horas perdidas","% no justificadas"],progs.map(x=>[x.name,x.line,money(x.learners),money(x.events),money(x.hours),pct(x.pctNotJust)],[2,3,4,5]));byId("programTable").innerHTML=table(["Programa","Aprendices afectados","Inasistencias","Horas perdidas","Participación de horas","% horas no justificadas","Riesgo"],progs.slice(0,15).map(x=>[x.name,money(x.learners),money(x.events),money(x.hours),pct(x.hours/(kpiValues()[1].value||1)),pct(x.pctNotJust),`<span class="badge ${riskClass(x.risk)}">${x.risk}</span>`],[1,2,3,4,5]));const {y}=current();const reasonRows=filterRows(D.reasons,p,y).reduce((m,x)=>{const v=m.get(x.reason)||{events:0,hours:0};v.events+=x.events;v.hours+=x.hours;m.set(x.reason,v);return m},new Map());byId("reasonTable").innerHTML=table(["Clasificación","Novedades","Horas perdidas","Participación"],[...reasonRows.entries()].sort((a,b)=>b[1].hours-a[1].hours).map(([k,v])=>[k,money(v.events),money(v.hours),pct(v.hours/(kpiValues()[1].value||1))],[1,2,3]))}
function renderQuality(){const q=D.summary;const values=[["Filas recibidas",money(q.events+q.duplicateRows+q.invalidRows)],["Duplicados removidos",money(q.duplicateRows)],["Fechas/rangos inválidos",money(q.invalidRows)],["Registros sin texto de justificación",money(q.missingReasonRows)],["Registros no clasificados",money(q.unclassifiedRows)],["Casos marcados para revisión",`${money(q.reviewRows)} · ${pct(q.reviewPct)}`],["Horas atípicas",money(q.outlierRows)],["Justificaciones únicas",money(q.uniqueReasons)],["Casos con soporte identificado",money(q.supportedRows)]];byId("qualityGrid").innerHTML=values.map(x=>`<div class="quality-item"><span>${x[0]}</span><strong>${x[1]}</strong></div>`).join("");byId("coverage").innerHTML=`<div class="notice">El archivo de inasistencias no aporta cobertura oficial suficiente de jornada, modalidad, estado académico, matrícula ni centro de costo maestro. Esos campos se presentan como no informados o inferidos y no deben interpretarse como datos oficiales.</div><div class="quality-grid"><div class="quality-item"><span>Jornada reportada</span><strong>${pct(q.coverage?.jornada_cobertura_pct||0)}</strong></div><div class="quality-item"><span>Modalidad reportada</span><strong>${pct(q.coverage?.modalidad_cobertura_pct||0)}</strong></div><div class="quality-item"><span>Estado académico oficial</span><strong>No disponible</strong></div><div class="quality-item"><span>Matrícula oficial</span><strong>No disponible</strong></div></div>`}
function esc(value){return String(value??"").replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]))}
function table(headers,rows,numeric=[]){if(!rows.length)return'<div class="empty">Sin datos para los filtros seleccionados.</div>';return`<table class="table"><thead><tr>${headers.map((x,i)=>`<th class="${numeric.includes(i)?"num":""}">${esc(x)}</th>`).join("")}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map((x,i)=>{const trusted=typeof x==="string"&&/^<span class="badge(?: medium| high)?">(?:Alto|Medio|Bajo|Sin dato)<\/span>$/.test(x);return`<td class="${numeric.includes(i)?"num":""}">${trusted?x:esc(x)}</td>`}).join("")}</tr>`).join("")}</tbody></table>`}
function renderTables(){const {p,y}=current();const progs=sortBy(periodPrograms(p,y),"hours");byId("lineTable").innerHTML=table(["Programa","Línea de formación","Aprendices","Inasistencias","Horas perdidas","% no justificadas"],progs.map(x=>[x.name,x.line,money(x.learners),money(x.events),money(x.hours),pct(x.pctNotJust)],[2,3,4,5]));byId("programTable").innerHTML=table(["Programa","Aprendices afectados","Inasistencias","Horas perdidas","Participación de horas","% horas no justificadas","Riesgo"],progs.slice(0,15).map(x=>[x.name,money(x.learners),money(x.events),money(x.hours),pct(x.hours/(kpiValues()[1].value||1)),pct(x.pctNotJust),`<span class="badge ${riskClass(x.risk)}">${x.risk}</span>`],[1,2,3,4,5]));const reasonRows=filterRows(D.reasons,p,y).reduce((m,x)=>{const v=m.get(x.reason)||{events:0,hours:0};v.events+=x.events;v.hours+=x.hours;m.set(x.reason,v);return m},new Map());byId("reasonTable").innerHTML=table(["Clasificación","Novedades","Horas perdidas","Participación"],[...reasonRows.entries()].sort((a,b)=>b[1].hours-a[1].hours).map(([k,v])=>[k,money(v.events),money(v.hours),pct(v.hours/(kpiValues()[1].value||1))],[1,2,3]))}
function renderAll(){renderKpis();renderMonthly();renderReasons();renderFichas();renderPrograms();renderLearnerRisk();renderLearnerPrograms();renderRisk();renderTables();renderQuality()}
function init(){for(const p of sortBy(D.programs,"learners")){const o=document.createElement("option");o.value=p.id;o.textContent=p.name;programFilter.append(o)}for(const y of [...new Set(D.months.map(x=>x.month.slice(0,4)))].sort()){const o=document.createElement("option");o.value=y;o.textContent=y;yearFilter.append(o)}const d=new Date(D.generatedAt+"T12:00:00");byId("sideDate").textContent=new Intl.DateTimeFormat("es-CO",{day:"numeric",month:"short",year:"numeric"}).format(d);byId("sideRows").textContent=`${money(D.summary.events)} registros válidos`;document.querySelectorAll(".nav button").forEach(b=>b.addEventListener("click",()=>{document.querySelectorAll(".nav button").forEach(x=>x.classList.toggle("active",x===b));document.querySelectorAll(".page").forEach(x=>x.classList.toggle("active",x.id===`page-${b.dataset.page}`));setTimeout(()=>Object.values(charts).forEach(c=>c.resize()),30)}));programFilter.addEventListener("change",renderAll);yearFilter.addEventListener("change",renderAll);renderAll()}
init();
</script>
</body>
</html>'''


def main() -> None:
    if not CHART_JS.exists():
        raise FileNotFoundError(f"No se encontró la distribución local de Chart.js: {CHART_JS}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    data_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    chart_js = CHART_JS.read_text(encoding="utf-8").replace("</script>", "<\\/script>")
    logo = base64.b64encode(LOGO.read_bytes()).decode("ascii") if LOGO.exists() else ""
    html = HTML_TEMPLATE.replace("@@DATA@@", data_json).replace("@@CHARTJS@@", chart_js).replace("@@LOGO@@", logo)
    OUT.write_text(html, encoding="utf-8")
    print(f"Portal generado: {OUT}")
    print(f"Corte: {payload['generatedAt']} · tamaño: {OUT.stat().st_size:,} bytes · datos agregados incrustados")


if __name__ == "__main__":
    main()
