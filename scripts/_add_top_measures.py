# -*- coding: utf-8 -*-
"""Add Top 10 ranking measures and the top-risk apprentice flag to the TMDL."""
from __future__ import annotations

import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLES = os.path.join(ROOT, "CaracterizacionAprendicesASTIN.SemanticModel", "definition", "tables")

MEDIDAS = [
    (
        "01 Inasistencias",
        "Top 10 Horas Ficha",
        """VAR Ranking =
    RANKX ( ALLSELECTED ( DIM_FICHA[FichaID] ), [Total horas perdidas], , DESC, Dense )
RETURN
    IF ( NOT ISBLANK ( [Total horas perdidas] ) && Ranking <= 10, [Total horas perdidas] )""",
        "#,##0",
    ),
    (
        "01 Inasistencias",
        "Top 10 Horas No Justificadas Ficha",
        """VAR Ranking =
    RANKX ( ALLSELECTED ( DIM_FICHA[FichaID] ), [Horas no justificadas], , DESC, Dense )
RETURN
    IF ( NOT ISBLANK ( [Horas no justificadas] ) && Ranking <= 10, [Horas no justificadas] )""",
        "#,##0",
    ),
    (
        "01 Inasistencias",
        "Top 10 Horas Programa",
        """VAR Ranking =
    RANKX ( ALLSELECTED ( DIM_PROGRAMA[NombrePrograma] ), [Total horas perdidas], , DESC, Dense )
RETURN
    IF ( NOT ISBLANK ( [Total horas perdidas] ) && Ranking <= 10, [Total horas perdidas] )""",
        "#,##0",
    ),
    (
        "01 Inasistencias",
        "Top 10 Horas No Justificadas Programa",
        """VAR Ranking =
    RANKX ( ALLSELECTED ( DIM_PROGRAMA[NombrePrograma] ), [Horas no justificadas], , DESC, Dense )
RETURN
    IF ( NOT ISBLANK ( [Horas no justificadas] ) && Ranking <= 10, [Horas no justificadas] )""",
        "#,##0",
    ),
    (
        "03 Aprendices",
        "Top 10 Aprendices Programa",
        """VAR Ranking =
    RANKX ( ALLSELECTED ( DIM_PROGRAMA[NombrePrograma] ), [Aprendices con inasistencias], , DESC, Dense )
RETURN
    IF ( NOT ISBLANK ( [Aprendices con inasistencias] ) && Ranking <= 10, [Aprendices con inasistencias] )""",
        "#,##0",
    ),
    (
        "02 Riesgo",
        "Top 10 Índice de Riesgo Ficha",
        """VAR Universo =
    FILTER ( ALLSELECTED ( DIM_FICHA[FichaID] ), CALCULATE ( MAX ( DIM_FICHA[MuestraSuficiente] ) ) = 1 )
VAR Ranking =
    RANKX ( Universo, [Índice de riesgo promedio de fichas], , DESC, Dense )
RETURN
    IF (
        CALCULATE ( MAX ( DIM_FICHA[MuestraSuficiente] ) ) = 1 && Ranking <= 10,
        [Índice de riesgo promedio de fichas]
    )""",
        "0.0",
    ),
]

FICHA_RIESGO = """column EsTopRiesgo = IF ( RANKX ( ALL ( DIM_APRENDIZ[AprendizID] ), DIM_APRENDIZ[ScoreRiesgo], , DESC, Dense ) <= 15, 1, 0 )
\t\tdataType: int64
\t\tformatString: 0
\t\tisHidden
\t\tsummarizeBy: none

"""


def measure_block(carpeta: str, medida: str, dax: str, fmt: str) -> str:
    lines = [f"\tmeasure '{medida}' = ```"]
    lines.extend("\t\t\t" + ln if ln else "" for ln in dax.splitlines())
    lines.append("\t\t\t```")
    lines.append(f"\t\tformatString: {fmt}")
    lines.append(f"\t\tdisplayFolder: {carpeta}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    path = os.path.join(TABLES, "FACT_INASISTENCIAS.tmdl")
    text = io.open(path, encoding="utf-8").read()
    marker = "\tcolumn InasistenciaID\n"
    if marker not in text:
        raise SystemExit("column marker not found")
    block = "".join(measure_block(*m) for m in MEDIDAS)
    text = text.replace(marker, block + marker, 1)
    io.open(path, "w", encoding="utf-8", newline="").write(text)
    print("measures added:", len(MEDIDAS))

    path = os.path.join(TABLES, "DIM_APRENDIZ.tmdl")
    text = io.open(path, encoding="utf-8").read()
    marker = "\tpartition DIM_APRENDIZ = m"
    if marker not in text:
        raise SystemExit("partition marker not found")
    text = text.replace(marker, FICHA_RIESGO + marker, 1)
    io.open(path, "w", encoding="utf-8", newline="").write(text)
    print("EsTopRiesgo added")


if __name__ == "__main__":
    main()
