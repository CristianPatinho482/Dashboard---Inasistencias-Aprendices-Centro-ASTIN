# -*- coding: utf-8 -*-
"""Genera un portal local de consulta nominal. No se debe publicar en GitHub Pages."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RESTRICTED = ROOT / "data" / "restricted"
OUTPUT = ROOT / "outputs" / "consulta_interna.html"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def as_float(value: str | None) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def build_payload() -> dict:
    identities = {
        row["AprendizID"]: row["NombreCompleto"]
        for row in read_csv(RESTRICTED / "DIM_APRENDIZ_PII.csv")
        if row.get("AprendizID") and row.get("NombreCompleto")
    }
    records = []
    for row in read_csv(PROCESSED / "FACT_INASISTENCIAS.csv"):
        apprentice_id = row.get("AprendizID", "")
        name = identities.get(apprentice_id)
        if not name:
            continue
        records.append({
            "id": apprentice_id,
            "name": name,
            "date": row.get("Fecha", ""),
            "ficha": row.get("FichaID", ""),
            "instructor": row.get("Instructor", "") or "Sin instructor",
            "hours": as_float(row.get("CantidadHoras")),
            "unjustified": as_float(row.get("CantidadHoras")) if row.get("EsNoJustificada") == "1" else 0,
        })
    records.sort(key=lambda item: (item["date"], item["id"]))
    return {"records": records}


def main() -> None:
    payload_data = build_payload()
    payload = json.dumps(payload_data, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    html = r'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Consulta interna de inasistencias · Centro ASTIN</title>
<style>
:root{--navy:#00304d;--green:#39a900;--yellow:#fdc300;--red:#b42318;--ink:#153849;--muted:#617982;--paper:#f3f7f4;--line:#dce7e1}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:14px "Segoe UI",Arial,sans-serif}.wrap{max-width:1500px;margin:auto;padding:30px}.head{display:flex;justify-content:space-between;align-items:start;gap:20px}.tag{color:#007832;text-transform:uppercase;letter-spacing:.12em;font-size:11px;font-weight:800}h1{margin:7px 0;color:var(--navy);font-size:30px}.sub{color:var(--muted);margin:0 0 20px}.local{background:#fff5d6;color:#765b00;padding:9px 12px;border-radius:7px;font-weight:700;font-size:12px}.filters,.kpis,.panel{background:white;border:1px solid var(--line);border-radius:10px;box-shadow:0 8px 24px rgba(0,48,77,.05)}.filters{display:flex;gap:14px;align-items:end;padding:16px;flex-wrap:wrap}.filter{display:grid;gap:5px;color:var(--muted);font-size:11px;font-weight:700}.filter select,.filter input{min-width:190px;border:1px solid var(--line);border-radius:7px;padding:9px;color:var(--ink);background:white}.filter input[type=date]{min-width:155px}.button{border:0;border-radius:7px;padding:10px 15px;color:#fff;background:var(--green);font-weight:700;cursor:pointer}.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding:14px;margin:14px 0}.kpi span{display:block;font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);font-weight:700}.kpi strong{display:block;color:var(--navy);font-size:24px;margin-top:6px}.panel{padding:16px}.panel h2{font-size:16px;color:var(--navy);margin:0 0 5px}.note{color:var(--muted);font-size:12px;margin:0 0 13px}.table-wrap{overflow:auto;max-height:62vh}.table{width:100%;border-collapse:collapse;font-size:12px}.table th{position:sticky;top:0;background:#edf5ea;color:var(--navy);text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:.04em}.table td,.table th{padding:10px;border-bottom:1px solid #e8efeb;white-space:nowrap}.num{text-align:right;font-variant-numeric:tabular-nums}.badge{display:inline-block;padding:5px 9px;border-radius:20px;font-weight:800}.green{background:#e8f5e2;color:#276900}.yellow{background:#fff5d6;color:#765b00}.red{background:#fde8e7;color:#a62219}.empty{text-align:center;padding:30px;color:var(--muted)}@media(max-width:760px){.wrap{padding:16px}.head{display:block}.local{display:inline-block;margin-bottom:10px}.kpis{grid-template-columns:repeat(2,1fr)}.kpi strong{font-size:20px}}
</style></head><body><main class="wrap">
<header class="head"><div><div class="tag">Centro ASTIN · Valle del Cauca</div><h1>Consulta semanal de aprendices</h1><p class="sub">Inasistencias y horas no justificadas por ficha, instructor e intervalo de consulta.</p></div><div class="local">Vista interna local · No publicar ni compartir por GitHub Pages</div></header>
<section class="filters" aria-label="Filtros de consulta">
<label class="filter">Ficha<select id="ficha"><option value="">Todas</option></select></label>
<label class="filter">Instructor<select id="instructor"><option value="">Todos</option></select></label>
<label class="filter">Desde<input id="desde" type="date"></label>
<label class="filter">Hasta<input id="hasta" type="date"></label>
<button class="button" id="limpiar">Restablecer</button></section>
<section class="kpis" aria-label="Indicadores del intervalo"><div class="kpi"><span>Aprendices</span><strong id="k-aprendices">0</strong></div><div class="kpi"><span>Inasistencias</span><strong id="k-registros">0</strong></div><div class="kpi"><span>Horas totales</span><strong id="k-horas">0</strong></div><div class="kpi"><span>Horas no justificadas</span><strong id="k-nojust">0</strong></div></section>
<section class="panel"><h2>Aprendices del intervalo</h2><p class="note">El semáforo toma la peor semana dentro del intervalo. Verde: &lt;12 h; amarillo: 12–16 h inclusive; rojo: &gt;16 h no justificadas.</p><div class="table-wrap"><table class="table"><thead><tr><th>Aprendiz</th><th>Ficha</th><th class="num">Inasistencias</th><th class="num">Horas totales</th><th class="num">Horas no justificadas</th><th class="num">Peor semana</th><th>Semáforo</th></tr></thead><tbody id="rows"></tbody></table></div><div id="empty" class="empty" hidden>No hay registros para los filtros seleccionados.</div></section>
</main><script>
const DATA=@@DATA@@;const $=id=>document.getElementById(id);const fmt=n=>new Intl.NumberFormat('es-CO',{maximumFractionDigits:1}).format(n);const uniq=a=>[...new Set(a)].filter(Boolean).sort((a,b)=>a.localeCompare(b,'es'));const startDate=DATA.records[0]?.date||'';const endDate=DATA.records.at(-1)?.date||'';
function fillSelect(id,items){for(const value of items){const o=document.createElement('option');o.value=value;o.textContent=value;$(id).append(o)}}
function weekStart(value){const [y,m,d]=value.split('-').map(Number);const date=new Date(Date.UTC(y,m-1,d));date.setUTCDate(date.getUTCDate()-((date.getUTCDay()+6)%7));return date.toISOString().slice(0,10)}
function render(){const ficha=$('ficha').value,instructor=$('instructor').value,desde=$('desde').value,hasta=$('hasta').value;const picked=DATA.records.filter(r=>(!ficha||r.ficha===ficha)&&(!instructor||r.instructor===instructor)&&(!desde||r.date>=desde)&&(!hasta||r.date<=hasta));const groups=new Map();let events=0,hours=0,unjustified=0;for(const r of picked){events++;hours+=r.hours;unjustified+=r.unjustified;const key=`${r.id}|${r.ficha}`;const g=groups.get(key)||{id:r.id,name:r.name,ficha:r.ficha,events:0,hours:0,unjustified:0,weeks:new Map()};g.events++;g.hours+=r.hours;g.unjustified+=r.unjustified;const week=weekStart(r.date);g.weeks.set(week,(g.weeks.get(week)||0)+r.unjustified);groups.set(key,g)}const learners=[...groups.values()].map(g=>({...g,maxWeek:Math.max(0,...g.weeks.values())})).sort((a,b)=>b.maxWeek-a.maxWeek||b.unjustified-a.unjustified||a.name.localeCompare(b.name,'es'));$('k-aprendices').textContent=fmt(new Set(learners.map(g=>g.id)).size);$('k-registros').textContent=fmt(events);$('k-horas').textContent=fmt(hours);$('k-nojust').textContent=fmt(unjustified);$('empty').hidden=learners.length>0;$('rows').innerHTML=learners.map(g=>{const risk=g.maxWeek<12?'green':g.maxWeek<=16?'yellow':'red';const label=risk==='green'?'Verde':risk==='yellow'?'Amarillo':'Rojo';return `<tr><td>${escapeHtml(g.name)}</td><td>${escapeHtml(g.ficha)}</td><td class="num">${fmt(g.events)}</td><td class="num">${fmt(g.hours)}</td><td class="num">${fmt(g.unjustified)}</td><td class="num">${fmt(g.maxWeek)}</td><td><span class="badge ${risk}">${label}</span></td></tr>`}).join('')}
function escapeHtml(v){return String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function reset(){ $('ficha').value='';$('instructor').value='';$('desde').value=startDate;$('hasta').value=endDate;render() }
fillSelect('ficha',uniq(DATA.records.map(r=>r.ficha)));fillSelect('instructor',uniq(DATA.records.map(r=>r.instructor)));$('desde').value=startDate;$('hasta').value=endDate;['ficha','instructor','desde','hasta'].forEach(id=>$(id).addEventListener('change',render));$('limpiar').addEventListener('click',reset);render();
</script></body></html>'''
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html.replace("@@DATA@@", payload), encoding="utf-8")
    print(f"Consulta interna generada localmente: {OUTPUT} ({len(payload_data['records']):,} registros)")


if __name__ == "__main__":
    main()
