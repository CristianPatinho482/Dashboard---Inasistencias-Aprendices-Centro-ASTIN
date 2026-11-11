#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Exporta la consulta nominal para Azure o genera datos sintéticos de demo.

Uso:
    python scripts/07_exportar_consulta_web.py --demo
    python scripts/07_exportar_consulta_web.py
    python scripts/07_exportar_consulta_web.py --desde 2026-08-01 --hasta 2026-10-31

El archivo real contiene nombres y datos personales. Se escribe en
data/private/ (ignorado por Git) y nunca debe copiarse a web/ ni publicarse.
El archivo de demostración es sintético y sí puede versionarse.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RESTRICTED = ROOT / "data" / "restricted"
DEMO_OUT = ROOT / "web" / "data" / "demo_consulta.json"
PRIVATE_OUT = ROOT / "data" / "private" / "consulta_web.json"
WEB_DIR = ROOT / "web"

DEMO_START = date(2026, 8, 3)
DEMO_WEEKS = 13
DEMO_FICHAS = [str(9000001 + index) for index in range(8)]
DEMO_INSTRUCTORS = [
    "Instructora Demo Ana",
    "Instructor Demo Carlos",
    "Instructora Demo Diana",
    "Instructor Demo Felipe",
    "Instructora Demo Laura",
    "Instructor Demo Mateo",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def as_float(value: str | None) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def build_real_payload(desde: str | None = None, hasta: str | None = None) -> dict:
    identities = {
        row["AprendizID"]: row["NombreCompleto"]
        for row in read_csv(RESTRICTED / "DIM_APRENDIZ_PII.csv")
        if row.get("AprendizID") and row.get("NombreCompleto")
    }

    records: list[dict] = []
    for row in read_csv(PROCESSED / "FACT_INASISTENCIAS.csv"):
        apprentice_id = row.get("AprendizID", "")
        name = identities.get(apprentice_id)
        if not name:
            continue
        day = row.get("Fecha", "")
        if desde and day < desde:
            continue
        if hasta and day > hasta:
            continue
        hours = as_float(row.get("CantidadHoras"))
        unjustified = hours if row.get("EsNoJustificada") == "1" else 0.0
        records.append({
            "id": apprentice_id,
            "name": name,
            "date": day,
            "ficha": row.get("FichaID", ""),
            "instructor": row.get("Instructor", "") or "Sin instructor",
            "hours": round(hours, 2),
            "unjustified": round(unjustified, 2),
        })

    records.sort(key=lambda item: (item["date"], item["id"], item["ficha"]))
    return {
        "schemaVersion": 1,
        "generatedAt": iso_now(),
        "sourceLabel": "Corte institucional",
        "synthetic": False,
        "records": records,
    }


def build_demo_payload() -> dict:
    rng = random.Random(20261111)
    records: list[dict] = []

    for index in range(72):
        apprentice_id = f"DEMO-{index + 1:04d}"
        name = f"Aprendiz Demo {index + 1:02d}"
        ficha = DEMO_FICHAS[index % len(DEMO_FICHAS)]
        instructor = DEMO_INSTRUCTORS[index % len(DEMO_INSTRUCTORS)]
        event_count = 2 + (index % 9)

        if index % 11 == 0:
            # Casos de alerta alta: varias novedades en una misma semana.
            week = rng.randrange(DEMO_WEEKS)
            for offset in range(3):
                day = DEMO_START + timedelta(weeks=week, days=min(offset, 4))
                hours = 8.0
                records.append({
                    "id": apprentice_id,
                    "name": name,
                    "date": day.isoformat(),
                    "ficha": ficha,
                    "instructor": instructor,
                    "hours": hours,
                    "unjustified": hours,
                })

        for _ in range(event_count):
            week = rng.randrange(DEMO_WEEKS)
            weekday = rng.randrange(5)
            day = DEMO_START + timedelta(weeks=week, days=weekday)
            hours = float(rng.choice([2, 3, 4, 5, 6, 8]))
            unjustified = hours if rng.random() < 0.74 else 0.0
            records.append({
                "id": apprentice_id,
                "name": name,
                "date": day.isoformat(),
                "ficha": ficha,
                "instructor": instructor,
                "hours": hours,
                "unjustified": unjustified,
            })

    records.sort(key=lambda item: (item["date"], item["id"], item["ficha"]))
    return {
        "schemaVersion": 1,
        "generatedAt": iso_now(),
        "sourceLabel": "Datos sintéticos de demostración",
        "synthetic": True,
        "records": records,
    }


def summarize(payload: dict) -> str:
    records = payload["records"]
    dates = [record["date"] for record in records if record.get("date")]
    learners = {record["id"] for record in records}
    return (
        f"{len(records):,} registros · {len(learners):,} aprendices · "
        f"{min(dates) if dates else 'sin fecha'} a {max(dates) if dates else 'sin fecha'}"
    )


def write_payload(payload: dict, destination: Path, pretty: bool) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if pretty:
        text = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    destination.write_text(text + "\n", encoding="utf-8")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    print(f"Archivo generado: {destination}")
    print(f"Contenido: {summarize(payload)}")
    print(f"Tamaño: {destination.stat().st_size:,} bytes · SHA-256: {digest}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Genera datos sintéticos para web/data/demo_consulta.json.")
    parser.add_argument("--out", type=Path, help="Ruta de salida alternativa.")
    parser.add_argument("--desde", help="Fecha inicial AAAA-MM-DD (solo datos reales).")
    parser.add_argument("--hasta", help="Fecha final AAAA-MM-DD (solo datos reales).")
    args = parser.parse_args()

    if args.desde and len(args.desde) != 10:
        parser.error("--desde debe tener formato AAAA-MM-DD")
    if args.hasta and len(args.hasta) != 10:
        parser.error("--hasta debe tener formato AAAA-MM-DD")

    if args.demo:
        payload = build_demo_payload()
        destination = args.out or DEMO_OUT
        if args.out is None:
            destination = DEMO_OUT
        write_payload(payload, destination.resolve(), pretty=True)
        return 0

    payload = build_real_payload(args.desde, args.hasta)
    destination = (args.out or PRIVATE_OUT).resolve()
    try:
        destination.relative_to(WEB_DIR.resolve())
    except ValueError:
        pass
    else:
        print(
            "ERROR: los datos reales no pueden escribirse dentro de web/. "
            "Use data/private/ y súbalos solo al Blob privado.",
            file=sys.stderr,
        )
        return 2

    write_payload(payload, destination, pretty=False)
    print("AVISO: este archivo contiene nombres y datos personales. No lo agregue a Git ni lo publique.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
