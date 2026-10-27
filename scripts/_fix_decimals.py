"""Fix locale-safe decimal parsing in the TMDL partitions.

Csv.Document has no Culture option in this Power BI version. The model culture
es-CO interprets a dot as a thousands separator, so values such as 91.4 were
loaded as 914 and 0.9865 as a huge integer. Decimal columns are therefore kept
as text by Csv.Document and converted explicitly with Number.FromText(_, "en-US").
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLES = os.path.join(ROOT, "CaracterizacionAprendicesASTIN.SemanticModel", "definition", "tables")

DOUBLES = {
    "DIM_APRENDIZ": ["ScoreRiesgo"],
    "DIM_CALENDARIO": [],
    "DIM_FICHA": ["PctHorasNoJust", "HorasPorAprendiz", "InasPorAprendiz", "IndiceRiesgoCorte"],
    "DIM_PROGRAMA": ["PctHorasNoJust", "HorasPorAprendiz", "InasPorAprendiz", "IndiceRiesgoCorte"],
    "FACT_INASISTENCIAS": ["HorasPorDia"],
}


def decimal_expr(col: str) -> str:
    return (
        f'{{"{col}", each if _ = null then null else if Text.Trim(_) = "" then null '
        f'else Number.FromText(Text.Trim(_), "en-US"), type number}}'
    )


def patch_table(path: str, table: str) -> None:
    text = io.open(path, encoding="utf-8").read()
    text = text.replace(', Culture="en-US"', "")
    if "Decimales = Table.TransformColumns" in text:
        io.open(path, "w", encoding="utf-8", newline="").write(text)
        print(f"skipped decimals (already patched) {table}")
        return

    decimals = DOUBLES.get(table, [])
    m = re.search(r"^(\s*)Tipos = Table\.TransformColumnTypes\(Encabezados,\{(.*)\}\)$", text, re.M)
    if not m:
        raise SystemExit(f"Tipos step not found in {path}")
    indent, body = m.group(1), m.group(2)
    entries = re.findall(r'\{"[^"]+", [^}]+\}', body)
    kept = [e for e in entries if re.match(r'\{"([^"]+)"', e).group(1) not in decimals]
    if len(kept) != len(entries) - len(decimals):
        raise SystemExit(f"Could not split all decimal columns in {path}: {entries}")

    tipos = f"Table.TransformColumnTypes(Encabezados,{{{', '.join(kept)}}})" if kept else "Encabezados"
    lineas = [f"{indent}Tipos = {tipos},"]
    if decimals:
        lineas.append(f"{indent}Decimales = Table.TransformColumns(Tipos,{{")
        lineas.extend(f"{indent}\t{decimal_expr(c)}," for c in decimals[:-1])
        lineas.append(f"{indent}\t{decimal_expr(decimals[-1])}")
        lineas.append(f"{indent}}})")
    else:
        lineas[-1] = lineas[-1].rstrip(",")
    text = text[: m.start()] + "\n".join(lineas) + text[m.end():]
    if decimals:
        text = re.sub(r"(\n\s*in\s*\n\s*)Tipos(\s*)$", r"\1Decimales\2", text)
    io.open(path, "w", encoding="utf-8", newline="").write(text)
    print(f"patched {table}: {len(kept)} typed cols, {len(decimals)} decimals")


def main() -> None:
    for table in DOUBLES:
        patch_table(os.path.join(TABLES, f"{table}.tmdl"), table)


if __name__ == "__main__":
    main()
