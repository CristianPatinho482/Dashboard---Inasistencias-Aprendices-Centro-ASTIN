# -*- coding: utf-8 -*-
"""Genera las seis páginas PBIR del tablero Caracterización de Aprendices ASTIN.

El script es idempotente: reconstruye definition/pages y registra el logo SENA.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, "CaracterizacionAprendicesASTIN.Report")
DEF = os.path.join(REPORT, "definition")
PAGES = os.path.join(DEF, "pages")
RESOURCES = os.path.join(REPORT, "StaticResources", "RegisteredResources")
VISUAL_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.12.0/schema.json"
PAGE_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"
MESES_CORTOS_ES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")


def fecha_descarga_texto() -> str:
    resumen_path = os.path.join(ROOT, "data", "processed", "00_resumen_etl.json")
    with open(resumen_path, encoding="utf-8") as stream:
        descarga = datetime.fromisoformat(json.load(stream)["ultima_descarga"])
    return (
        f"Descarga: {descarga.day} {MESES_CORTOS_ES[descarga.month - 1]} "
        f"{descarga.year} {descarga.hour:02d}:{descarga.minute:02d}"
    )


def total_registros_texto() -> str:
    resumen_path = os.path.join(ROOT, "data", "processed", "00_resumen_etl.json")
    with open(resumen_path, encoding="utf-8") as stream:
        total = json.load(stream)["registros_validos"]
    return f"{total:,}".replace(",", ".") + " registros válidos"

PAGE_IDS = [
    ("a0000000000000000000", "00 Inicio"),
    ("a0000000000000000001", "01 Caracterización Aprendices"),
    ("a0000000000000000002", "02 Fichas y Programas en Riesgo"),
    ("a0000000000000000003", "03 Análisis Detallado"),
    ("a0000000000000000004", "04 Calidad de Datos"),
    ("a0000000000000000005", "05 Consulta semanal"),
]

NAV = [
    ("00  Inicio", "a0000000000000000000"),
    ("01  Caracterización", "a0000000000000000001"),
    ("02  Fichas y programas", "a0000000000000000002"),
    ("03  Análisis detallado", "a0000000000000000003"),
    ("04  Calidad de datos", "a0000000000000000004"),
    ("05  Consulta semanal", "a0000000000000000005"),
]

NAVY = "#00304D"
GREEN = "#39A900"
DARK_GREEN = "#007832"
CYAN = "#50E5F9"
YELLOW = "#FDC300"
PURPLE = "#71277A"
TEXT = "#1F3B47"
MUTED = "#667A72"
LIGHT = "#F6F6F6"
WHITE = "#FFFFFF"
BORDER = "#DDE8E2"
PALE_GREEN = "#EAF5E7"
RED = "#C62828"


def lit(value: str) -> dict:
    return {"expr": {"Literal": {"Value": value}}}


def s(text: str) -> dict:
    clean = text.replace("'", "''")
    return lit("'" + clean + "'")


def num(value) -> dict:
    return lit(str(value).replace(".0", "") + "D")


def boolean(value: bool) -> dict:
    return lit("true" if value else "false")


def solid(color: str) -> dict:
    return {"solid": {"color": s(color)}}


def visual_id(*parts: str) -> str:
    return hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()[:20]


def col(entity: str, prop: str, active: bool = False, label: str | None = None) -> dict:
    field = {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}
    result = {"queryRef": f"{entity}.{prop}", "nativeQueryRef": label or prop, "field": field}
    if active:
        result["active"] = True
    return result


def meas(prop: str, label: str | None = None, entity: str = "FACT_INASISTENCIAS") -> dict:
    return {
        "queryRef": f"{entity}.{prop}",
        "nativeQueryRef": label or prop,
        "field": {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}},
    }


def sort_by(field: dict, direction: str = "Descending") -> dict:
    return {"sort": [{"field": field, "direction": direction}], "isDefaultSort": True}


def filter_in(entity: str, prop: str, values: list, numeric: bool = False) -> dict:
    vals = []
    for value in values:
        vals.append([{"Literal": {"Value": f"{value}L" if numeric else "'" + str(value) + "'"}}])
    return {
        "name": visual_id(entity, prop, ",".join(str(v) for v in values)),
        "field": {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}},
        "type": "Categorical",
        "howCreated": "User",
        "filter": {
            "Version": 2,
            "From": [{"Name": "d", "Entity": entity, "Type": 0}],
            "Where": [
                {
                    "Condition": {
                        "In": {
                            "Expressions": [
                                {"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": prop}}
                            ],
                            "Values": vals,
                        }
                    }
                }
            ],
        },
    }


def container(title: str | None = None, background: bool = True, border: bool = True) -> dict:
    result = {"visualHeader": [{"properties": {"show": boolean(False)}}]}
    if title is not None:
        result["title"] = [
            {
                "properties": {
                    "show": boolean(True),
                    "text": s(title),
                    "fontSize": lit("9.8D"),
                    "bold": boolean(True),
                    "alignment": s("left"),
                }
            }
        ]
    else:
        result["title"] = [{"properties": {"show": boolean(False)}}]
    result["background"] = [
        {"properties": {"show": boolean(background), "color": solid(WHITE), "transparency": lit("0D")}}
    ]
    result["border"] = [
        {"properties": {"show": boolean(border), "color": solid(BORDER), "radius": lit("8D")}}
    ]
    return result


def write_visual(page_id: str, key: str, payload: dict) -> None:
    vid = visual_id(page_id, key)
    folder = os.path.join(PAGES, page_id, "visuals", vid)
    os.makedirs(folder, exist_ok=True)
    data = {"$schema": VISUAL_SCHEMA, "name": vid, **payload}
    with open(os.path.join(folder, "visual.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def add_text(
    page_id: str,
    key: str,
    x: float,
    y: float,
    w: float,
    h: float,
    lines,
    size: float = 10,
    color: str = TEXT,
    link: str | None = None,
    z: int = 100,
) -> None:
    if isinstance(lines, str):
        lines = [lines]
    paragraphs = []
    for line in lines:
        paragraphs.append(
            {
                "textRuns": [
                    {
                        "value": line,
                        "textStyle": {"fontFamily": "Work Sans", "fontSize": f"{size}pt", "color": color},
                    }
                ]
            }
        )
    visual = {
        "visualType": "textbox",
        "objects": {"general": [{"properties": {"paragraphs": paragraphs}}]},
        "visualContainerObjects": {
            "title": [{"properties": {"show": boolean(False)}}],
            "background": [{"properties": {"show": boolean(False)}}],
            "border": [{"properties": {"show": boolean(False)}}],
        },
        "drillFilterOtherVisuals": True,
    }
    if link:
        visual["visualContainerObjects"]["visualLink"] = [
            {
                "properties": {
                    "show": boolean(True),
                    "type": s("PageNavigation"),
                    "navigationSection": s(link),
                }
            }
        ]
    write_visual(page_id, key, {"position": {"x": x, "y": y, "width": w, "height": h, "z": z}, "visual": visual})


def add_shape(
    page_id: str,
    key: str,
    x: float,
    y: float,
    w: float,
    h: float,
    fill: str = WHITE,
    line: str = BORDER,
    z: int = 0,
) -> None:
    visual = {
        "visualType": "shape",
        "objects": {
            "shape": [{"properties": {"tileShape": s("rectangle")}}],
            "fill": [
                {
                    "properties": {"fillColor": solid(fill), "transparency": lit("0D")},
                    "selector": {"id": "default"},
                }
            ],
            "outline": [
                {
                    "properties": {"lineColor": solid(line), "weight": lit("1D")},
                    "selector": {"id": "default"},
                }
            ],
        },
        "drillFilterOtherVisuals": True,
    }
    write_visual(page_id, key, {"position": {"x": x, "y": y, "width": w, "height": h, "z": z}, "visual": visual})


def add_image(page_id: str, key: str, x: float, y: float, w: float, h: float, item: str = "sena_logo.png", z: int = 10) -> None:
    visual = {
        "visualType": "image",
        "objects": {
            "image": [
                {
                    "properties": {
                        "sourceFile": {
                            "image": {
                                "name": s(item),
                                "url": {
                                    "expr": {
                                        "ResourcePackageItem": {
                                            "PackageName": "RegisteredResources",
                                            "PackageType": 1,
                                            "ItemName": item,
                                        }
                                    }
                                },
                                "scaling": s("Normal"),
                            }
                        }
                    }
                }
            ]
        },
        "visualContainerObjects": {
            "title": [{"properties": {"show": boolean(False)}}],
            "background": [{"properties": {"show": boolean(False)}}],
            "border": [{"properties": {"show": boolean(False)}}],
        },
        "drillFilterOtherVisuals": True,
    }
    write_visual(page_id, key, {"position": {"x": x, "y": y, "width": w, "height": h, "z": z}, "visual": visual})


def add_card(page_id: str, key: str, x: float, y: float, w: float, h: float, measure: str, label: str, z: int = 20) -> None:
    add_shape(page_id, key + "-tile", x, y, w, h, fill=WHITE, line=BORDER, z=z - 2)
    visual = {
        "visualType": "cardVisual",
        "query": {"queryState": {"Data": {"projections": [meas(measure)]}}},
        "objects": {
            "outline": [{"properties": {"show": boolean(False)}, "selector": {"id": "default"}}],
            "fillCustom": [{"properties": {"show": boolean(False)}}],
            "divider": [{"properties": {"show": boolean(False)}, "selector": {"id": "default"}}],
            "label": [{"properties": {"show": boolean(False)}, "selector": {"id": "default"}}],
            "value": [
                {
                    "properties": {
                        "fontFamily": s("Work Sans"),
                        "fontSize": lit("19D"),
                        "bold": boolean(True),
                        "color": solid(NAVY),
                        "horizontalAlignment": s("left"),
                    },
                    "selector": {"id": "default"},
                },
                {
                    "properties": {"labelDisplayUnits": lit("1D")},
                    "selector": {"metadata": f"FACT_INASISTENCIAS.{measure}"},
                },
            ],
        },
        "drillFilterOtherVisuals": True,
        "visualContainerObjects": {
            "title": [
                {
                    "properties": {
                        "show": boolean(True),
                        "text": s(label.upper()),
                        "fontSize": lit("8D"),
                        "fontColor": solid(MUTED),
                        "fontFamily": s("Work Sans"),
                        "bold": boolean(False),
                        "alignment": s("left"),
                    }
                }
            ],
            "background": [{"properties": {"show": boolean(False)}}],
            "border": [{"properties": {"show": boolean(False)}}],
            "visualHeader": [{"properties": {"show": boolean(False)}}],
            "padding": [
                {
                    "properties": {
                        "top": lit("0D"),
                        "bottom": lit("0D"),
                        "left": lit("2D"),
                        "right": lit("2D"),
                    }
                }
            ],
        },
    }
    write_visual(page_id, key, {"position": {"x": x + 9, "y": y + 20, "width": w - 18, "height": h - 24, "z": z + 1}, "visual": visual})


def add_sidebar_measure(page_id: str, key: str, y: float, measure: str, font_size: float = 9) -> None:
    """Muestra medidas del modelo en la barra lateral para que respondan al refresh."""
    visual = {
        "visualType": "cardVisual",
        "query": {"queryState": {"Data": {"projections": [meas(measure)]}}},
        "objects": {
            "outline": [{"properties": {"show": boolean(False)}, "selector": {"id": "default"}}],
            "fillCustom": [{"properties": {"show": boolean(False)}}],
            "divider": [{"properties": {"show": boolean(False)}, "selector": {"id": "default"}}],
            "label": [{"properties": {"show": boolean(False)}, "selector": {"id": "default"}}],
            "value": [{
                "properties": {
                    "fontFamily": s("Work Sans"),
                    "fontSize": lit(f"{font_size}D"),
                    "bold": boolean(True),
                    "color": solid(WHITE),
                    "horizontalAlignment": s("left"),
                },
                "selector": {"id": "default"},
            }],
        },
        "drillFilterOtherVisuals": True,
        "visualContainerObjects": {
            "title": [{"properties": {"show": boolean(False)}}],
            "background": [{"properties": {"show": boolean(False)}}],
            "border": [{"properties": {"show": boolean(False)}}],
            "visualHeader": [{"properties": {"show": boolean(False)}}],
            "padding": [{"properties": {"top": lit("0D"), "bottom": lit("0D"), "left": lit("0D"), "right": lit("0D")}}],
        },
    }
    write_visual(page_id, key, {"position": {"x": 20, "y": y, "width": 170, "height": 20, "z": 303}, "visual": visual})


def add_bar(
    page_id: str,
    key: str,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    category: tuple,
    measure: str,
    filters: list | None = None,
    z: int = 5,
) -> None:
    category_field = col(*category)
    visual = {
        "visualType": "barChart",
        "query": {
            "queryState": {
                "Category": {"projections": [category_field]},
                "Y": {"projections": [meas(measure)]},
            },
            "sortDefinition": sort_by(meas(measure)["field"]),
        },
        "objects": {
            "categoryAxis": [
                {
                    "properties": {
                        "fontSize": lit("8D"),
                        "labelColor": solid(TEXT),
                        "show": boolean(True),
                        "innerPadding": lit("0D"),
                    }
                }
            ],
            "valueAxis": [
                {
                    "properties": {
                        "show": boolean(False),
                        "gridlineShow": boolean(False),
                    }
                }
            ],
            "legend": [{"properties": {"show": boolean(False)}}],
            "labels": [
                {
                    "properties": {
                        "show": boolean(True),
                        "fontSize": lit("8.5D"),
                        "color": solid(TEXT),
                        "labelDisplayUnits": lit("1D"),
                    }
                }
            ],
        },
        "drillFilterOtherVisuals": True,
        "visualContainerObjects": container(title),
    }
    payload = {
        "position": {"x": x, "y": y, "width": w, "height": h, "z": z},
        "visual": visual,
    }
    if filters:
        payload["filterConfig"] = {"filters": filters}
    write_visual(page_id, key, payload)


def add_donut(
    page_id: str,
    key: str,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    category: tuple,
    measure: str,
    filters: list | None = None,
    z: int = 5,
) -> None:
    visual = {
        "visualType": "donutChart",
        "query": {
            "queryState": {
                "Category": {"projections": [col(*category)]},
                "Y": {"projections": [meas(measure)]},
            },
            "sortDefinition": sort_by(meas(measure)["field"]),
        },
        "objects": {
            "legend": [
                {
                    "properties": {
                        "show": boolean(True),
                        "showTitle": boolean(False),
                        "position": s("Right"),
                        "fontSize": lit("8.5D"),
                        "labelColor": solid(TEXT),
                    }
                }
            ],
            "labels": [{"properties": {"show": boolean(False)}}],
        },
        "drillFilterOtherVisuals": True,
        "visualContainerObjects": container(title),
    }
    payload = {
        "position": {"x": x, "y": y, "width": w, "height": h, "z": z},
        "visual": visual,
    }
    if filters:
        payload["filterConfig"] = {"filters": filters}
    write_visual(page_id, key, payload)


def add_line(
    page_id: str,
    key: str,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    category: tuple,
    measure: str,
    filters: list | None = None,
    z: int = 5,
) -> None:
    visual = {
        "visualType": "lineChart",
        "query": {
            "queryState": {
                "Category": {"projections": [col(*category)]},
                "Y": {"projections": [meas(measure)]},
            },
            "sortDefinition": {"sort": [{"field": col(*category)["field"], "direction": "Ascending"}], "isDefaultSort": True},
        },
        "objects": {
            "categoryAxis": [
                {
                    "properties": {
                        "fontSize": lit("8.5D"),
                        "labelColor": solid(TEXT),
                        "show": boolean(True),
                    }
                }
            ],
            "valueAxis": [
                {
                    "properties": {
                        "fontSize": lit("8.5D"),
                        "labelColor": solid(MUTED),
                        "gridlineShow": boolean(True),
                        "gridlineColor": solid(BORDER),
                    }
                }
            ],
            "legend": [{"properties": {"show": boolean(False)}}],
            "labels": [{"properties": {"show": boolean(False)}}],
        },
        "drillFilterOtherVisuals": True,
        "visualContainerObjects": container(title),
    }
    payload = {
        "position": {"x": x, "y": y, "width": w, "height": h, "z": z},
        "visual": visual,
    }
    if filters:
        payload["filterConfig"] = {"filters": filters}
    write_visual(page_id, key, payload)


def add_table(
    page_id: str,
    key: str,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    columns: list,
    sort_field: dict,
    direction: str = "Descending",
    filters: list | None = None,
    widths: dict | None = None,
    labels: dict | None = None,
    z: int = 5,
) -> None:
    projections = []
    for entity, prop, is_measure in columns:
        display = labels.get(prop) if labels else None
        proj = meas(prop, None, entity) if is_measure else col(entity, prop)
        if display:
            proj["displayName"] = display
        projections.append(proj)
    visual = {
        "visualType": "tableEx",
        "query": {
            "queryState": {"Values": {"projections": projections}},
            "sortDefinition": sort_by(sort_field, direction),
        },
        "objects": {
            "grid": [
                {
                    "properties": {
                        "gridVertical": boolean(False),
                        "gridHorizontal": boolean(True),
                        "gridHorizontalColor": solid(BORDER),
                        "gridHorizontalWeight": lit("1D"),
                        "outlineColor": solid(BORDER),
                        "outlineWeight": lit("0D"),
                        "rowPadding": lit("0D"),
                    }
                }
            ],
            "values": [{"properties": {"fontSize": lit("8.2D"), "fontFamily": s("Work Sans"), "color": solid(TEXT)}}],
            "columnHeaders": [
                {
                    "properties": {
                        "fontSize": lit("8.2D"),
                        "fontFamily": s("Work Sans"),
                        "bold": boolean(True),
                        "fontColor": solid(NAVY),
                        "backColor": solid(PALE_GREEN),
                    }
                }
            ],
            "total": [{"properties": {"show": boolean(False)}}],
        },
        "drillFilterOtherVisuals": True,
        "visualContainerObjects": container(title),
    }
    if widths:
        visual["objects"]["columnWidth"] = [
            {
                "properties": {"value": lit(f"{int(px)}D")},
                "selector": {"metadata": f"{entity}.{prop}"},
            }
            for entity, prop, is_measure in columns
            for px in [widths.get(prop)]
            if px
        ]
    payload = {
        "position": {"x": x, "y": y, "width": w, "height": h, "z": z},
        "visual": visual,
    }
    if filters:
        payload["filterConfig"] = {"filters": filters}
    write_visual(page_id, key, payload)


def add_slicer(
    page_id: str,
    key: str,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    entity: str,
    prop: str,
    mode: str = "Dropdown",
    z: int = 5,
) -> None:
    visual = {
        "visualType": "slicer",
        "query": {"queryState": {"Values": {"projections": [col(entity, prop, active=True)]}}},
        "objects": {
            "header": [{"properties": {"show": boolean(False)}}],
            "items": [{"properties": {"textSize": lit("8D"), "fontFamily": s("Work Sans")}}],
            "data": [{"properties": {"mode": s(mode)}}],
        },
        "drillFilterOtherVisuals": True,
        "visualContainerObjects": container(title),
    }
    write_visual(page_id, key, {"position": {"x": x, "y": y, "width": w, "height": h, "z": z}, "visual": visual})


def page_header(page_id: str, title: str, subtitle: str) -> None:
    add_text(page_id, "header-title", 224, 16, 760, 38, title, size=23, color=NAVY, z=200)
    add_text(page_id, "header-subtitle", 224, 55, 780, 22, subtitle, size=10.5, color=MUTED, z=200)
    add_shape(page_id, "header-accent", 224, 82, 56, 3, fill=GREEN, line=GREEN, z=201)
    add_text(page_id, "header-date", 980, 20, 276, 24, fecha_descarga_texto(), size=8.5, color=MUTED, z=200)


def page_footer(page_id: str) -> None:
    add_shape(page_id, "footer-line", 224, 684, 1032, 1, fill=BORDER, line=BORDER, z=201)
    add_text(
        page_id,
        "footer-left",
        224,
        688,
        560,
        24,
        "SENA · Centro ASTIN · Regional Valle del Cauca",
        size=8.2,
        color=MUTED,
        z=200,
    )
    add_text(
        page_id,
        "footer-right",
        850,
        688,
        406,
        24,
        "Fuente: Inasistencias.xls · Centro ASTIN",
        size=8.2,
        color=MUTED,
        z=200,
    )


def page_nav(page_id: str) -> None:
    add_shape(page_id, "nav-rail", 0, 0, 200, 720, fill=NAVY, line=NAVY, z=300)
    add_shape(page_id, "nav-logo-badge", 20, 20, 52, 52, fill=WHITE, line=WHITE, z=301)
    add_image(page_id, "nav-logo", 26, 26, 40, 40, z=302)
    add_text(page_id, "nav-brand", 84, 22, 110, 22, "SENA", size=15, color=WHITE, z=302)
    add_text(page_id, "nav-brand-sub", 84, 44, 110, 18, "Centro ASTIN", size=8.5, color="#BFD8CB", z=302)
    add_shape(page_id, "nav-divider", 20, 92, 160, 1, fill="#1D4B66", line="#1D4B66", z=301)
    add_text(page_id, "nav-section", 20, 104, 160, 16, "NAVEGACIÓN", size=8.2, color="#7FA3B5", z=302)

    for index, (label, target) in enumerate(NAV):
        y = 130 + index * 46
        active = target == page_id
        if active:
            add_shape(page_id, f"nav-active-{index}", 12, y, 176, 38, fill=GREEN, line=GREEN, z=301)
        add_text(
            page_id,
            f"nav-{index}",
            24,
            y + 9,
            160,
            22,
            label,
            size=9.2,
            color=WHITE if active else "#A9C0CE",
            link=target,
            z=302,
        )

    add_shape(page_id, "nav-bottom-line", 20, 620, 160, 1, fill="#1D4B66", line="#1D4B66", z=301)
    add_text(page_id, "nav-bottom-1", 20, 622, 160, 18, "ÚLTIMA DESCARGA", size=8.0, color="#7FA3B5", z=302)
    # La ETL vuelve a generar este rótulo tras cada descarga; así muestra
    # fecha y hora reales de la última actualización del archivo fuente.
    add_text(
        page_id,
        "nav-bottom-2",
        20,
        642,
        160,
        20,
        fecha_descarga_texto().replace("Descarga: ", ""),
        size=9.2,
        color="#EAF3F6",
        z=303,
    )
    add_sidebar_measure(page_id, "nav-bottom-3", 665, "Registros válidos al corte", font_size=8.0)


def kpi_row(page_id: str, items: list) -> None:
    for index, (label, measure) in enumerate(items):
        x = 224 + index * 209
        add_card(page_id, f"kpi-{index}", x, 96, 196, 92, measure, label)


def write_page(page_id: str, display_name: str) -> None:
    folder = os.path.join(PAGES, page_id)
    os.makedirs(folder, exist_ok=True)
    data = {
        "$schema": PAGE_SCHEMA,
        "name": page_id,
        "displayName": display_name,
        "width": 1280,
        "height": 720,
        "displayOption": "FitToPage",
    }
    with open(os.path.join(folder, "page.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def page_inicio(page_id: str) -> None:
    page_header(
        page_id,
        "Caracterización de Aprendices · Centro ASTIN",
        "Panorama ejecutivo de inasistencias, horas no justificadas y alertas de deserción · Regional Valle del Cauca",
    )
    kpi_row(
        page_id,
        [
            ("Aprendices con inasist.", "Aprendices con inasistencias"),
            ("Inasistencias", "Total inasistencias"),
            ("Horas no justificadas", "Horas no justificadas"),
            ("% horas no justificadas", "% horas no justificadas"),
            ("Posible deserción", "Casos posible deserción"),
        ],
    )
    add_line(
        page_id,
        "trend-hours",
        224,
        198,
        508,
        206,
        "Evolución mensual de horas",
        ("DIM_CALENDARIO", "EtiquetaMes"),
        "Total horas perdidas",
    )
    add_donut(
        page_id,
        "donut-just",
        744,
        198,
        512,
        206,
        "Horas por tipo de justificación",
        ("FACT_INASISTENCIAS", "CategoriaJustificacion"),
        "Total horas perdidas",
    )
    add_bar(
        page_id,
        "top-fichas",
        224,
        412,
        508,
        256,
        "Top 10 fichas por horas perdidas",
        ("DIM_FICHA", "FichaID"),
        "Top 10 Horas Ficha",
    )
    add_bar(
        page_id,
        "top-programas",
        744,
        412,
        512,
        256,
        "Top 10 programas por horas perdidas",
        ("DIM_PROGRAMA", "NombrePrograma"),
        "Top 10 Horas Programa",
    )


def page_caracterizacion(page_id: str) -> None:
    page_header(
        page_id,
        "Caracterización de aprendices",
        "Distribución por riesgo, reincidencia, programas con mayor volumen y casos que requieren seguimiento",
    )
    kpi_row(
        page_id,
        [
            ("Riesgo alto", "Aprendices en riesgo alto"),
            ("Reincidentes", "Aprendices reincidentes"),
            ("Reincidentes altos", "Aprendices reincidentes altos"),
            ("Tasa reincidencia", "Tasa de reincidencia"),
            ("Con retardos", "Aprendices con retardo"),
        ],
    )
    add_donut(
        page_id,
        "donut-riesgo",
        224,
        198,
        336,
        256,
        "Aprendices por nivel de riesgo",
        ("DIM_APRENDIZ", "NivelRiesgo"),
        "Aprendices con inasistencias",
    )
    add_bar(
        page_id,
        "top-programas-aprendices",
        572,
        198,
        336,
        256,
        "Top 10 programas por aprendices",
        ("DIM_PROGRAMA", "NombrePrograma"),
        "Top 10 Aprendices Programa",
    )
    add_bar(
        page_id,
        "horas-por-riesgo",
        920,
        198,
        336,
        256,
        "Horas no justificadas por nivel de riesgo",
        ("DIM_APRENDIZ", "NivelRiesgo"),
        "Horas no justificadas",
    )
    add_table(
        page_id,
        "top-aprendices",
        224,
        462,
        640,
        206,
        "Aprendices con mayor riesgo (Top 15)",
        [
            ("DIM_APRENDIZ", "Iniciales", False),
            ("DIM_APRENDIZ", "DocumentoEnmascarado", False),
            ("FACT_INASISTENCIAS", "FichaID", False),
            ("DIM_APRENDIZ", "NivelRiesgo", False),
            ("DIM_APRENDIZ", "ScoreRiesgo", False),
            ("DIM_APRENDIZ", "Inasistencias", False),
            ("DIM_APRENDIZ", "HorasNoJustificadas", False),
        ],
        {"Column": {"Expression": {"SourceRef": {"Entity": "DIM_APRENDIZ"}}, "Property": "ScoreRiesgo"}},
        filters=[filter_in("DIM_APRENDIZ", "EsTopRiesgo", [1], numeric=True)],
    )
    add_table(
        page_id,
        "desercion",
        876,
        462,
        380,
        206,
        "Posibles casos de deserción",
        [
            ("DIM_APRENDIZ", "Iniciales", False),
            ("DIM_APRENDIZ", "FichaPrincipal", False),
            ("DIM_APRENDIZ", "HorasNoJustificadas", False),
            ("DIM_APRENDIZ", "DiasDesdeUltimaNovedad", False),
            ("DIM_APRENDIZ", "MotivoAlertaDesercion", False),
        ],
        {"Column": {"Expression": {"SourceRef": {"Entity": "DIM_APRENDIZ"}}, "Property": "HorasNoJustificadas"}},
        filters=[filter_in("DIM_APRENDIZ", "AlertaDesercion", [1], numeric=True)],
    )


def page_fichas(page_id: str) -> None:
    page_header(
        page_id,
        "Fichas y programas en riesgo",
        "Priorización por índice de riesgo, horas no justificadas y afectación de aprendices",
    )
    kpi_row(
        page_id,
        [
            ("Fichas riesgo alto", "Fichas en riesgo alto"),
            ("Programas riesgo alto", "Programas en riesgo alto"),
            ("Horas no justif. · fichas alto", "Horas no justificadas en fichas de alto riesgo"),
            ("Aprendices afectados · alto", "Aprendices afectados en fichas de alto riesgo"),
            ("Índice riesgo fichas", "Índice de riesgo promedio de fichas"),
        ],
    )
    add_bar(
        page_id,
        "top-fichas-riesgo",
        224,
        198,
        640,
        256,
        "Top 10 fichas por índice de riesgo (muestra suficiente)",
        ("DIM_FICHA", "FichaID"),
        "Top 10 Índice de Riesgo Ficha",
    )
    add_bar(
        page_id,
        "fichas-nivel",
        876,
        198,
        380,
        256,
        "Fichas por nivel de riesgo",
        ("DIM_FICHA", "NivelRiesgoCorte"),
        "Fichas con inasistencias",
    )
    add_table(
        page_id,
        "tabla-fichas",
        224,
        462,
        552,
        206,
        "Fichas en riesgo alto y medio",
        [
            ("DIM_FICHA", "FichaID", False),
            ("DIM_FICHA", "Aprendices", False),
            ("DIM_FICHA", "Horas", False),
            ("DIM_FICHA", "PctHorasNoJust", False),
            ("DIM_FICHA", "IndiceRiesgoCorte", False),
            ("DIM_FICHA", "NivelRiesgoCorte", False),
        ],
        {"Column": {"Expression": {"SourceRef": {"Entity": "DIM_FICHA"}}, "Property": "IndiceRiesgoCorte"}},
        filters=[filter_in("DIM_FICHA", "NivelRiesgoCorte", ["Alto", "Medio"])],
        widths={
            "FichaID": 70,
            "Aprendices": 66,
            "Horas": 58,
            "PctHorasNoJust": 92,
            "IndiceRiesgoCorte": 58,
            "NivelRiesgoCorte": 60,
        },
        labels={
            "FichaID": "Ficha",
            "PctHorasNoJust": "% no justificado",
            "IndiceRiesgoCorte": "Índice",
            "NivelRiesgoCorte": "Nivel",
        },
    )
    add_table(
        page_id,
        "tabla-programas",
        788,
        462,
        464,
        206,
        "Programas en riesgo alto y medio",
        [
            ("DIM_PROGRAMA", "NombrePrograma", False),
            ("DIM_PROGRAMA", "IndiceRiesgoCorte", False),
            ("DIM_PROGRAMA", "NivelRiesgoCorte", False),
            ("DIM_PROGRAMA", "HorasNoJustificadas", False),
        ],
        {"Column": {"Expression": {"SourceRef": {"Entity": "DIM_PROGRAMA"}}, "Property": "IndiceRiesgoCorte"}},
        filters=[filter_in("DIM_PROGRAMA", "NivelRiesgoCorte", ["Alto", "Medio"])],
        widths={
            "NombrePrograma": 224,
            "IndiceRiesgoCorte": 58,
            "NivelRiesgoCorte": 56,
            "HorasNoJustificadas": 92,
        },
        labels={
            "NombrePrograma": "Programa",
            "IndiceRiesgoCorte": "Índice",
            "NivelRiesgoCorte": "Nivel",
            "HorasNoJustificadas": "Horas no justif.",
        },
    )


def page_detalle(page_id: str) -> None:
    page_header(
        page_id,
        "Análisis detallado de inasistencias",
        "Tendencia mensual, programas críticos y detalle de las inasistencias no justificadas de mayor duración",
    )
    kpi_row(
        page_id,
        [
            ("Total horas perdidas", "Total horas perdidas"),
            ("Horas por inasistencia", "Horas por inasistencia"),
            ("Cantidad de retardos", "Cantidad de retardos"),
            ("Registros por revisar", "Registros que requieren revisión"),
            ("% horas no justificadas", "% horas no justificadas"),
        ],
    )
    add_line(
        page_id,
        "trend-inas",
        224,
        198,
        508,
        256,
        "Tendencia mensual de inasistencias",
        ("DIM_CALENDARIO", "EtiquetaMes"),
        "Total inasistencias",
    )
    add_bar(
        page_id,
        "top-programas-horas",
        744,
        198,
        512,
        256,
        "Top 10 programas por horas perdidas",
        ("DIM_PROGRAMA", "NombrePrograma"),
        "Top 10 Horas Programa",
    )
    add_table(
        page_id,
        "detalle-inas",
        224,
        462,
        700,
        206,
        "Inasistencias no justificadas de mayor duración",
        [
            ("FACT_INASISTENCIAS", "Fecha", False),
            ("DIM_APRENDIZ", "Iniciales", False),
            ("DIM_FICHA", "FichaID", False),
            ("FACT_INASISTENCIAS", "CantidadHoras", False),
            ("FACT_INASISTENCIAS", "TipoJustificacion", False),
            ("FACT_INASISTENCIAS", "RequiereRevision", False),
        ],
        {"Column": {"Expression": {"SourceRef": {"Entity": "FACT_INASISTENCIAS"}}, "Property": "CantidadHoras"}},
        filters=[filter_in("FACT_INASISTENCIAS", "EsNoJustificada", [1], numeric=True)],
    )
    add_slicer(page_id, "slicer-mes", 936, 462, 320, 102, "Filtrar por mes", "DIM_CALENDARIO", "EtiquetaMes")
    add_slicer(
        page_id,
        "slicer-riesgo",
        936,
        572,
        320,
        96,
        "Filtrar por nivel de riesgo de ficha",
        "DIM_FICHA",
        "NivelRiesgoCorte",
    )


def page_consulta_semanal(page_id: str) -> None:
    config_path = os.path.join(ROOT, "config", "sharepoint.json")
    sharepoint_mode = False
    if os.path.isfile(config_path):
        with open(config_path, encoding="utf-8") as stream:
            sharepoint_mode = str(json.load(stream).get("mode", "Local")).strip().lower() == "sharepoint"
    campo_aprendiz = "AprendizID" if sharepoint_mode else "NombreCompleto"
    etiqueta_aprendiz = "Código seudónimo" if sharepoint_mode else "Aprendiz"
    titulo_tabla = "Aprendices y horas en el intervalo seleccionado"
    if sharepoint_mode:
        titulo_tabla = "Aprendices identificados por código seudónimo"
    page_header(
        page_id,
        "Consulta semanal de aprendices",
        ("Busca por ficha, instructor y fechas. La identidad se muestra mediante un código seudónimo; "
         "el semáforo evalúa la semana con más horas no justificadas del intervalo." if sharepoint_mode else
         "Busca por ficha, instructor y fechas; el semáforo evalúa la semana con más horas no justificadas del intervalo."),
    )
    add_slicer(page_id, "filtro-ficha-consulta", 224, 96, 218, 68, "Ficha", "DIM_FICHA", "FichaID")
    add_slicer(page_id, "filtro-instructor-consulta", 448, 96, 260, 68, "Instructor", "FACT_INASISTENCIAS", "Instructor")
    add_slicer(page_id, "filtro-fechas-consulta", 714, 96, 542, 68, "Intervalo de fechas", "DIM_CALENDARIO", "Fecha", mode="Between")
    add_text(
        page_id,
        "consulta-umbrales",
        224,
        168,
        1032,
        18,
        "Semáforo semanal sobre horas NO justificadas: menos de 12 = verde · 12 a 16 inclusive = amarillo · más de 16 = rojo.",
        size=9,
        color=MUTED,
        z=20,
    )
    cards = [
        ("Aprendices", "Aprendices con inasistencias"),
        ("Registros de inasistencia", "Total inasistencias"),
        ("Horas de inasistencia", "Total horas perdidas"),
        ("Horas no justificadas", "Horas no justificadas en periodo"),
        ("Máximo semanal no justificado", "Máximo semanal horas no justificadas"),
    ]
    for index, (label, measure) in enumerate(cards):
        add_card(page_id, f"consulta-kpi-{index}", 224 + index * 209, 190, 196, 78, measure, label, z=20)
    add_table(
        page_id,
        "consulta-aprendices",
        224,
        278,
        1032,
        397,
        titulo_tabla,
        [
            ("DIM_APRENDIZ", campo_aprendiz, False),
            ("DIM_APRENDIZ", "FichaPrincipal", False),
            ("FACT_INASISTENCIAS", "Total inasistencias", True),
            ("FACT_INASISTENCIAS", "Total horas perdidas", True),
            ("FACT_INASISTENCIAS", "Horas no justificadas en periodo", True),
            ("FACT_INASISTENCIAS", "Máximo semanal horas no justificadas", True),
            ("FACT_INASISTENCIAS", "Semáforo semanal", True),
        ],
        meas("Máximo semanal horas no justificadas")["field"],
        widths={campo_aprendiz: 245, "NombreCompleto": 245, "FichaID": 112, "Total inasistencias": 112,
                "Total horas perdidas": 105, "Horas no justificadas en periodo": 145,
                "Máximo semanal horas no justificadas": 160, "Semáforo semanal": 112},
        labels={campo_aprendiz: etiqueta_aprendiz, "NombreCompleto": "Aprendiz", "FichaID": "Ficha", "Total inasistencias": "Inasistencias",
                "Total horas perdidas": "Horas totales", "Horas no justificadas en periodo": "No justificadas · periodo",
                "Máximo semanal horas no justificadas": "Peor semana · no justificadas", "Semáforo semanal": "Semáforo"},
    )


def page_calidad(page_id: str) -> None:
    page_header(
        page_id,
        "Calidad de datos y trazabilidad",
        "Cobertura, depuración, clasificación de justificaciones y limitaciones de la fuente",
    )
    kpi_row(
        page_id,
        [
            ("Registros de origen", "Registros origen"),
            ("Duplicados removidos", "Duplicados removidos"),
            ("Registros por revisar", "Registros que requieren revisión"),
            ("Registros no clasificados", "Registros no clasificados"),
            ("Cobertura de documento", "Cobertura documento"),
        ],
    )
    add_bar(
        page_id,
        "confianza",
        224,
        198,
        508,
        214,
        "Registros por confianza de clasificación",
        ("FACT_INASISTENCIAS", "ConfianzaClasificacion"),
        "Total inasistencias",
    )
    add_table(
        page_id,
        "tabla-revision",
        744,
        198,
        512,
        214,
        "Registros que requieren revisión",
        [
            ("FACT_INASISTENCIAS", "Fecha", False),
            ("DIM_APRENDIZ", "Iniciales", False),
            ("FACT_INASISTENCIAS", "JustificacionOriginal", False),
            ("FACT_INASISTENCIAS", "ReglaClasificacion", False),
        ],
        {"Column": {"Expression": {"SourceRef": {"Entity": "FACT_INASISTENCIAS"}}, "Property": "Fecha"}},
        filters=[filter_in("FACT_INASISTENCIAS", "RequiereRevision", [1], numeric=True)],
    )
    add_table(
        page_id,
        "tabla-outliers",
        224,
        420,
        508,
        248,
        "Registros con horas atípicas",
        [
            ("FACT_INASISTENCIAS", "Fecha", False),
            ("DIM_APRENDIZ", "Iniciales", False),
            ("FACT_INASISTENCIAS", "CantidadHoras", False),
            ("FACT_INASISTENCIAS", "TipoJustificacion", False),
        ],
        {"Column": {"Expression": {"SourceRef": {"Entity": "FACT_INASISTENCIAS"}}, "Property": "CantidadHoras"}},
        filters=[filter_in("FACT_INASISTENCIAS", "EsOutlierHoras", [1], numeric=True)],
    )
    add_shape(page_id, "notas-tile", 744, 420, 512, 248, fill=WHITE, line=BORDER, z=3)
    add_text(
        page_id,
        "notas-title",
        760,
        432,
        480,
        22,
        "Notas metodológicas y limitaciones",
        size=11,
        color=NAVY,
        z=10,
    )
    add_text(
        page_id,
        "notas-body",
        760,
        458,
        480,
        196,
        [
            "• 16.691 registros de origen; 446 duplicados exactos removidos y 16.245 registros válidos.",
            "• Nombres y documentos se enmascaran; el detalle nominal está en data/restricted.",
            "• La clasificación de justificaciones es por reglas; 1.272 casos requieren revisión.",
            "• No se informa jornada, modalidad ni matrícula total: los indicadores se expresan sobre aprendices con inasistencias.",
            "• Las 33 horas atípicas se conservan y se señalan; no se imputan valores.",
            "• Índice de riesgo: 40% horas por aprendiz, 25% inasistencias por aprendiz, 20% horas no justificadas y 15% volumen; solo fichas con ≥5 aprendices y ≥100 horas.",
        ],
        size=8.2,
        color=MUTED,
        z=10,
    )


def ensure_resources() -> None:
    os.makedirs(RESOURCES, exist_ok=True)
    source_logo = os.path.join(os.environ.get("TEMP", ""), "opencode", "sena_logo_green.png")
    target_logo = os.path.join(RESOURCES, "sena_logo.png")
    if os.path.exists(source_logo):
        shutil.copyfile(source_logo, target_logo)
    if not os.path.exists(target_logo):
        raise SystemExit("Logo SENA no encontrado")

    report_json = os.path.join(DEF, "report.json")
    with open(report_json, encoding="utf-8") as fh:
        report = json.load(fh)
    packages = report.setdefault("resourcePackages", [])
    registered = next((p for p in packages if p.get("name") == "RegisteredResources"), None)
    if registered is None:
        registered = {"name": "RegisteredResources", "type": "RegisteredResources", "items": []}
        packages.append(registered)
    items = registered.setdefault("items", [])
    if not any(i.get("name") == "sena_logo.png" for i in items):
        items.append({"name": "sena_logo.png", "path": "sena_logo.png", "type": "Image"})
    with open(report_json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def main() -> None:
    ensure_resources()
    if os.path.isdir(PAGES):
        shutil.rmtree(PAGES)
    os.makedirs(PAGES, exist_ok=True)
    for page_id, display_name in PAGE_IDS:
        write_page(page_id, display_name)
        page_nav(page_id)
        page_footer(page_id)
    page_inicio(PAGE_IDS[0][0])
    page_caracterizacion(PAGE_IDS[1][0])
    page_fichas(PAGE_IDS[2][0])
    page_detalle(PAGE_IDS[3][0])
    page_calidad(PAGE_IDS[4][0])
    page_consulta_semanal(PAGE_IDS[5][0])
    pages_json = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
        "pageOrder": [p[0] for p in PAGE_IDS],
        "activePageName": PAGE_IDS[0][0],
    }
    with open(os.path.join(PAGES, "pages.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(pages_json, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print("pages:", len(PAGE_IDS))
    print("visuals:", sum(len(files) for _, _, files in os.walk(PAGES)))


if __name__ == "__main__":
    main()
