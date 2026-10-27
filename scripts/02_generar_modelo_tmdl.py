# -*- coding: utf-8 -*-
"""
Genera el modelo semántico TMDL del proyecto Caracterización de Aprendices ASTIN.

El modelo se construye por código para mantener consistencia entre columnas,
tipos, relaciones y carpetas de medidas. Se puede regenerar sin abrir Power BI.
"""
from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
MODEL = BASE / "CaracterizacionAprendicesASTIN.SemanticModel"
DEF = MODEL / "definition"
TABLES_DIR = DEF / "tables"
DATA = BASE / "data" / "processed"

RESUMEN = json.loads((DATA / "00_resumen_etl.json").read_text(encoding="utf-8"))

MODEL_NAME = "CaracterizacionAprendicesASTIN"
REPORT_NAME = "Caracterización de Aprendices Centro ASTIN"
# Ruta de carpeta del modelo, relativa al proyecto para que este sea portable.
RUTA_DATOS = str(DATA)


# ---------------------------------------------------------------------------
# Definición de tablas y columnas
# ---------------------------------------------------------------------------
def c(nombre, tipo, fmt=None, oculta=False, orden=None, resumen="none"):
    return dict(nombre=nombre, tipo=tipo, fmt=fmt, oculta=oculta, orden=orden, resumen=resumen)


TABLAS = {
    "DIM_CALENDARIO": {
        "archivo": "DIM_CALENDARIO.csv",
        "fecha": True,
        "columnas": [
            c("Fecha", "dateTime", "yyyy-MM-dd"),
            c("Anio", "int64", "0"), c("Trimestre", "int64", "0"),
            c("Mes", "int64", "0"), c("NombreMes", "string", orden="Mes"),
            c("MesCorto", "string", orden="Mes"), c("AnioMes", "string"),
            c("EtiquetaMes", "string", orden="OrdenAnioMes"),
            c("OrdenAnioMes", "int64", "0"),
            c("SemanaISO", "int64", "0"), c("Dia", "int64", "0"),
            c("NombreDia", "string"), c("EsFinSemana", "int64", "0"),
            c("Periodo", "string"), c("EsMesCompleto", "int64", "0"),
            c("FechaCorte", "dateTime", "yyyy-MM-dd"),
            c("DiasDesdeCorte", "int64", "0"), c("FechaKey", "int64", "0"),
        ],
    },
    "DIM_APRENDIZ": {
        "archivo": "DIM_APRENDIZ.csv",
        "columnas": [
            c("AprendizID", "string", oculta=True),
            c("TipoDocumento", "string"), c("DocumentoEnmascarado", "string"),
            c("Iniciales", "string"), c("FichaPrincipal", "string"),
            c("ProgramaPrincipal", "string", oculta=True),
            c("Inasistencias", "int64", "#,##0"), c("Horas", "int64", "#,##0"),
            c("Justificadas", "int64", "#,##0"), c("NoJustificadas", "int64", "#,##0"),
            c("Retardos", "int64", "#,##0"), c("HorasNoJustificadas", "int64", "#,##0"),
            c("ScoreRiesgo", "double", "0.0"), c("NivelRiesgo", "string"),
            c("EstadoAsistencia", "string"), c("EsReincidente", "int64", "0"),
            c("EsReincidenteAlto", "int64", "0"), c("AlertaDesercion", "int64", "0"),
            c("MotivoAlertaDesercion", "string"),
            c("DiasDesdeUltimaNovedad", "int64", "#,##0"),
            c("PrimeraNovedad", "dateTime", "yyyy-MM-dd"),
            c("UltimaNovedad", "dateTime", "yyyy-MM-dd"),
        ],
    },
    "DIM_FICHA": {
        "archivo": "DIM_FICHA.csv",
        "columnas": [
            c("FichaID", "string"), c("ProgramaID", "string", oculta=True),
            c("InstructorPrincipal", "string"), c("TotalInstructores", "int64", "0"),
            c("Jornada", "string"), c("Modalidad", "string"), c("Sede", "string"),
            c("CentroCosto", "string"), c("LineaFormacion", "string"),
            c("EstadoFicha", "string"), c("DiasSinNovedad", "int64", "0"),
            c("Aprendices", "int64", "#,##0"), c("Inasistencias", "int64", "#,##0"),
            c("Horas", "int64", "#,##0"), c("HorasNoJustificadas", "int64", "#,##0"),
            c("PctHorasNoJust", "double", "0.0%"),
            c("HorasPorAprendiz", "double", "#,##0.0"),
            c("InasPorAprendiz", "double", "#,##0.0"),
            c("MuestraSuficiente", "int64", "0"),
            c("IndiceRiesgoCorte", "double", "0.0"),
            c("NivelRiesgoCorte", "string"),
            c("PrimeraNovedad", "dateTime", "yyyy-MM-dd"),
            c("UltimaNovedad", "dateTime", "yyyy-MM-dd"),
        ],
    },
    "DIM_PROGRAMA": {
        "archivo": "DIM_PROGRAMA.csv",
        "columnas": [
            c("ProgramaID", "string", oculta=True),
            c("NombrePrograma", "string"), c("NombreOriginal", "string", oculta=True),
            c("LineaFormacion", "string"), c("TipoFormacion", "string"),
            c("CentroCosto", "string"), c("CentroFormacion", "string"),
            c("Regional", "string"), c("NivelFormacion", "string"),
            c("Aprendices", "int64", "#,##0"), c("Inasistencias", "int64", "#,##0"),
            c("Horas", "int64", "#,##0"), c("HorasNoJustificadas", "int64", "#,##0"),
            c("PctHorasNoJust", "double", "0.0%"),
            c("HorasPorAprendiz", "double", "#,##0.0"),
            c("InasPorAprendiz", "double", "#,##0.0"),
            c("MuestraSuficiente", "int64", "0"),
            c("IndiceRiesgoCorte", "double", "0.0"),
            c("NivelRiesgoCorte", "string"),
            c("RankingHoras", "int64", "0", oculta=True),
            c("PrimeraNovedad", "dateTime", "yyyy-MM-dd"),
            c("UltimaNovedad", "dateTime", "yyyy-MM-dd"),
        ],
    },
    "FACT_INASISTENCIAS": {
        "archivo": "FACT_INASISTENCIAS.csv",
        "columnas": [
            c("InasistenciaID", "string", oculta=True),
            c("Fecha", "dateTime", "yyyy-MM-dd"),
            c("FechaFin", "dateTime", "yyyy-MM-dd"),
            c("FichaID", "string", oculta=True),
            c("AprendizID", "string", oculta=True),
            c("ProgramaID", "string", oculta=True),
            c("Instructor", "string"),
            c("CantidadHoras", "int64", "#,##0"),
            c("DiasCubiertos", "int64", "0"),
            c("HorasPorDia", "double", "#,##0.00"),
            c("EsOutlierHoras", "int64", "0"),
            c("JustificacionOriginal", "string"),
            c("CategoriaJustificacion", "string"),
            c("TipoJustificacion", "string"),
            c("ConfianzaClasificacion", "string"),
            c("RequiereRevision", "int64", "0"),
            c("ReglaClasificacion", "string"),
            c("TieneSoporte", "int64", "0"),
            c("EsRetardo", "int64", "0"),
            c("EsAusencia", "int64", "0"),
            c("EsJustificada", "int64", "0"),
            c("EsNoJustificada", "int64", "0"),
            c("EsSinInformacion", "int64", "0"),
            c("EsReincidenteAprendiz", "int64", "0", oculta=True),
            c("EsReincidenteAltoAprendiz", "int64", "0", oculta=True),
            c("EsAlertaDesercionAprendiz", "int64", "0", oculta=True),
            c("NivelRiesgoAprendiz", "string", oculta=True),
            c("TieneDocumentoAprendiz", "int64", "0", oculta=True),
            c("Anio", "int64", "0", oculta=True),
            c("Mes", "int64", "0", oculta=True),
        ],
    },
}

M_TIPO = {
    "string": "type text",
    "int64": "Int64.Type",
    "double": "type number",
    "dateTime": "type date",
    "boolean": "type logical",
}


# ---------------------------------------------------------------------------
# Medidas DAX
# ---------------------------------------------------------------------------
MEDIDAS = [
    # -- 00 KPIs -----------------------------------------------------------
    ("00 KPIs", "Total horas perdidas", "SUM ( FACT_INASISTENCIAS[CantidadHoras] )", "#,##0"),
    ("00 KPIs", "Total inasistencias", "COUNTROWS ( FACT_INASISTENCIAS )", "#,##0"),
    ("00 KPIs", "Aprendices con inasistencias", "DISTINCTCOUNT ( FACT_INASISTENCIAS[AprendizID] )", "#,##0"),
    ("00 KPIs", "Fichas con inasistencias", "DISTINCTCOUNT ( FACT_INASISTENCIAS[FichaID] )", "#,##0"),
    ("00 KPIs", "Programas con inasistencias", "DISTINCTCOUNT ( FACT_INASISTENCIAS[ProgramaID] )", "#,##0"),
    ("00 KPIs", "% horas no justificadas", "DIVIDE ( [Horas no justificadas], [Total horas perdidas] )", "0.0%"),
    ("00 KPIs", "% horas justificadas", "DIVIDE ( [Horas justificadas], [Total horas perdidas] )", "0.0%"),
    ("00 KPIs", "% horas sin información", "DIVIDE ( [Horas sin información], [Total horas perdidas] )", "0.0%"),
    ("00 KPIs", "Horas por inasistencia", "DIVIDE ( [Total horas perdidas], [Total inasistencias] )", "#,##0.0"),
    ("00 KPIs", "Días con inasistencias", "DISTINCTCOUNT ( FACT_INASISTENCIAS[Fecha] )", "#,##0"),
    ("00 KPIs", "Fichas en riesgo alto", 'CALCULATE ( DISTINCTCOUNT ( FACT_INASISTENCIAS[FichaID] ), DIM_FICHA[NivelRiesgoCorte] = "Alto" )', "#,##0"),
    ("00 KPIs", "Programas en riesgo alto", 'CALCULATE ( DISTINCTCOUNT ( FACT_INASISTENCIAS[ProgramaID] ), DIM_PROGRAMA[NivelRiesgoCorte] = "Alto" )', "#,##0"),
    ("00 KPIs", "Casos posible deserción", "CALCULATE ( [Aprendices con inasistencias], FACT_INASISTENCIAS[EsAlertaDesercionAprendiz] = 1 )", "#,##0"),
    # -- 01 Inasistencias ---------------------------------------------------
    ("01 Inasistencias", "Horas justificadas", "CALCULATE ( [Total horas perdidas], FACT_INASISTENCIAS[EsJustificada] = 1 )", "#,##0"),
    ("01 Inasistencias", "Horas no justificadas", "CALCULATE ( [Total horas perdidas], FACT_INASISTENCIAS[EsNoJustificada] = 1 )", "#,##0"),
    ("01 Inasistencias", "Horas sin información", "CALCULATE ( [Total horas perdidas], FACT_INASISTENCIAS[EsSinInformacion] = 1 )", "#,##0"),
    ("01 Inasistencias", "Inasistencias justificadas", "CALCULATE ( [Total inasistencias], FACT_INASISTENCIAS[EsJustificada] = 1 )", "#,##0"),
    ("01 Inasistencias", "Inasistencias no justificadas", "CALCULATE ( [Total inasistencias], FACT_INASISTENCIAS[EsNoJustificada] = 1 )", "#,##0"),
    ("01 Inasistencias", "Inasistencias sin información", "CALCULATE ( [Total inasistencias], FACT_INASISTENCIAS[EsSinInformacion] = 1 )", "#,##0"),
    ("01 Inasistencias", "% inasistencias no justificadas", "DIVIDE ( [Inasistencias no justificadas], [Total inasistencias] )", "0.0%"),
    ("01 Inasistencias", "% inasistencias justificadas", "DIVIDE ( [Inasistencias justificadas], [Total inasistencias] )", "0.0%"),
    ("01 Inasistencias", "% inasistencias sin información", "DIVIDE ( [Inasistencias sin información], [Total inasistencias] )", "0.0%"),
    ("01 Inasistencias", "Horas de retardo", "CALCULATE ( [Total horas perdidas], FACT_INASISTENCIAS[EsRetardo] = 1 )", "#,##0"),
    ("01 Inasistencias", "Cantidad de retardos", "CALCULATE ( [Total inasistencias], FACT_INASISTENCIAS[EsRetardo] = 1 )", "#,##0"),
    ("01 Inasistencias", "% horas de retardo", "DIVIDE ( [Horas de retardo], [Total horas perdidas] )", "0.0%"),
    ("01 Inasistencias", "Horas no justificadas por inasistencia", "DIVIDE ( [Horas no justificadas], [Inasistencias no justificadas] )", "#,##0.0"),
    ("01 Inasistencias", "Horas de ausencia", "CALCULATE ( [Total horas perdidas], FACT_INASISTENCIAS[EsAusencia] = 1 )", "#,##0"),
    ("01 Inasistencias", "Inasistencias sin retardo", "CALCULATE ( [Total inasistencias], FACT_INASISTENCIAS[EsAusencia] = 1 )", "#,##0"),
    # -- 02 Riesgo ----------------------------------------------------------
    ("02 Riesgo", "Fichas en riesgo medio", 'CALCULATE ( DISTINCTCOUNT ( FACT_INASISTENCIAS[FichaID] ), DIM_FICHA[NivelRiesgoCorte] = "Medio" )', "#,##0"),
    ("02 Riesgo", "Fichas muestra insuficiente", 'CALCULATE ( DISTINCTCOUNT ( FACT_INASISTENCIAS[FichaID] ), DIM_FICHA[NivelRiesgoCorte] = "Muestra baja" )', "#,##0"),
    ("02 Riesgo", "% fichas en riesgo alto", "DIVIDE ( [Fichas en riesgo alto], [Fichas con inasistencias] )", "0.0%"),
    ("02 Riesgo", "Programas en riesgo medio", 'CALCULATE ( DISTINCTCOUNT ( FACT_INASISTENCIAS[ProgramaID] ), DIM_PROGRAMA[NivelRiesgoCorte] = "Medio" )', "#,##0"),
    ("02 Riesgo", "Programas muestra insuficiente", 'CALCULATE ( DISTINCTCOUNT ( FACT_INASISTENCIAS[ProgramaID] ), DIM_PROGRAMA[NivelRiesgoCorte] = "Muestra baja" )', "#,##0"),
    ("02 Riesgo", "Índice de riesgo promedio de fichas", "AVERAGEX ( VALUES ( FACT_INASISTENCIAS[FichaID] ), CALCULATE ( MAX ( DIM_FICHA[IndiceRiesgoCorte] ) ) )", "0.0"),
    ("02 Riesgo", "Índice de riesgo promedio de programas", "AVERAGEX ( VALUES ( FACT_INASISTENCIAS[ProgramaID] ), CALCULATE ( MAX ( DIM_PROGRAMA[IndiceRiesgoCorte] ) ) )", "0.0"),
    ("02 Riesgo", "Máximo índice de riesgo de ficha", "MAXX ( VALUES ( FACT_INASISTENCIAS[FichaID] ), CALCULATE ( MAX ( DIM_FICHA[IndiceRiesgoCorte] ) ) )", "0.0"),
    ("02 Riesgo", "Ficha crítica principal",
     "VAR Ranking = ADDCOLUMNS ( VALUES ( FACT_INASISTENCIAS[FichaID] ), \"@Score\", CALCULATE ( MAX ( DIM_FICHA[IndiceRiesgoCorte] ) ) )\n"
     "VAR Top1 = TOPN ( 1, FILTER ( Ranking, NOT ISBLANK ( [@Score] ) ), [@Score], DESC )\n"
     "RETURN CONCATENATEX ( Top1, FACT_INASISTENCIAS[FichaID], \", \" )", None),
    ("02 Riesgo", "Programa crítico principal",
     "VAR Ranking = ADDCOLUMNS ( VALUES ( FACT_INASISTENCIAS[ProgramaID] ), \"@Score\", CALCULATE ( MAX ( DIM_PROGRAMA[IndiceRiesgoCorte] ) ) )\n"
     "VAR Top1 = TOPN ( 1, FILTER ( Ranking, NOT ISBLANK ( [@Score] ) ), [@Score], DESC )\n"
     "RETURN CONCATENATEX ( Top1, DIM_PROGRAMA[NombrePrograma], \", \" )", None),
    ("02 Riesgo", "Aprendices en riesgo alto", 'CALCULATE ( [Aprendices con inasistencias], FACT_INASISTENCIAS[NivelRiesgoAprendiz] = "Alto" )', "#,##0"),
    ("02 Riesgo", "% aprendices en riesgo alto", "DIVIDE ( [Aprendices en riesgo alto], [Aprendices con inasistencias] )", "0.0%"),
    ("02 Riesgo", "Aprendices en riesgo medio", 'CALCULATE ( [Aprendices con inasistencias], FACT_INASISTENCIAS[NivelRiesgoAprendiz] = "Medio" )', "#,##0"),
    ("02 Riesgo", "Aprendices en riesgo bajo", 'CALCULATE ( [Aprendices con inasistencias], FACT_INASISTENCIAS[NivelRiesgoAprendiz] = "Bajo" )', "#,##0"),
    ("02 Riesgo", "Horas no justificadas por aprendiz", "DIVIDE ( [Horas no justificadas], [Aprendices con inasistencias] )", "#,##0.0"),
    ("02 Riesgo", "Casos con alerta por texto", "CALCULATE ( [Aprendices con inasistencias], FACT_INASISTENCIAS[EsAlertaDesercionAprendiz] = 1, DIM_APRENDIZ[MotivoAlertaDesercion] IN { \"Texto de retiro/deserción\", \"Texto y patrón\" } )", "#,##0"),
    ("02 Riesgo", "Casos con alerta por patrón", "CALCULATE ( [Aprendices con inasistencias], FACT_INASISTENCIAS[EsAlertaDesercionAprendiz] = 1, DIM_APRENDIZ[MotivoAlertaDesercion] IN { \"Patrón de ausencias\", \"Texto y patrón\" } )", "#,##0"),
    ("02 Riesgo", "% aprendices con alerta", "DIVIDE ( [Casos posible deserción], [Aprendices con inasistencias] )", "0.0%"),
    ("02 Riesgo", "Horas no justificadas en fichas de alto riesgo", 'CALCULATE ( [Horas no justificadas], DIM_FICHA[NivelRiesgoCorte] = "Alto" )', "#,##0"),
    ("02 Riesgo", "Aprendices afectados en fichas de alto riesgo", 'CALCULATE ( [Aprendices con inasistencias], DIM_FICHA[NivelRiesgoCorte] = "Alto" )', "#,##0"),
    # -- 03 Aprendices ------------------------------------------------------
    ("03 Aprendices", "Horas promedio por aprendiz", "DIVIDE ( [Total horas perdidas], [Aprendices con inasistencias] )", "#,##0.0"),
    ("03 Aprendices", "Inasistencias promedio por aprendiz", "DIVIDE ( [Total inasistencias], [Aprendices con inasistencias] )", "#,##0.0"),
    ("03 Aprendices", "Mediana de inasistencias por aprendiz", "MEDIANX ( VALUES ( FACT_INASISTENCIAS[AprendizID] ), CALCULATE ( [Total inasistencias] ) )", "#,##0.0"),
    ("03 Aprendices", "Máximo de inasistencias por aprendiz", "MAXX ( VALUES ( FACT_INASISTENCIAS[AprendizID] ), CALCULATE ( [Total inasistencias] ) )", "#,##0"),
    ("03 Aprendices", "Aprendices reincidentes", "CALCULATE ( [Aprendices con inasistencias], FACT_INASISTENCIAS[EsReincidenteAprendiz] = 1 )", "#,##0"),
    ("03 Aprendices", "Aprendices reincidentes altos", "CALCULATE ( [Aprendices con inasistencias], FACT_INASISTENCIAS[EsReincidenteAltoAprendiz] = 1 )", "#,##0"),
    ("03 Aprendices", "Tasa de reincidencia", "DIVIDE ( [Aprendices reincidentes], [Aprendices con inasistencias] )", "0.0%"),
    ("03 Aprendices", "% aprendices reincidentes", "DIVIDE ( [Aprendices reincidentes], [Aprendices con inasistencias] )", "0.0%"),
    ("03 Aprendices", "Aprendices con una sola inasistencia", "COUNTROWS ( FILTER ( VALUES ( FACT_INASISTENCIAS[AprendizID] ), CALCULATE ( [Total inasistencias] ) = 1 ) )", "#,##0"),
    ("03 Aprendices", "% aprendices con una sola inasistencia", "DIVIDE ( [Aprendices con una sola inasistencia], [Aprendices con inasistencias] )", "0.0%"),
    ("03 Aprendices", "Aprendices en más de una ficha", "COUNTROWS ( FILTER ( VALUES ( FACT_INASISTENCIAS[AprendizID] ), CALCULATE ( DISTINCTCOUNT ( FACT_INASISTENCIAS[FichaID] ) ) > 1 ) )", "#,##0"),
    ("03 Aprendices", "% aprendices en más de una ficha", "DIVIDE ( [Aprendices en más de una ficha], [Aprendices con inasistencias] )", "0.0%"),
    ("03 Aprendices", "Aprendices con retardo", "CALCULATE ( [Aprendices con inasistencias], FACT_INASISTENCIAS[EsRetardo] = 1 )", "#,##0"),
    ("03 Aprendices", "% aprendices con retardo", "DIVIDE ( [Aprendices con retardo], [Aprendices con inasistencias] )", "0.0%"),
    ("03 Aprendices", "Aprendices con horas no justificadas", "CALCULATE ( [Aprendices con inasistencias], FACT_INASISTENCIAS[EsNoJustificada] = 1 )", "#,##0"),
    ("03 Aprendices", "% aprendices con horas no justificadas", "DIVIDE ( [Aprendices con horas no justificadas], [Aprendices con inasistencias] )", "0.0%"),
    # -- 04 Tendencias ------------------------------------------------------
    ("04 Tendencias", "Horas último mes",
     "VAR FechaMax = CALCULATE ( MAX ( FACT_INASISTENCIAS[Fecha] ), REMOVEFILTERS ( DIM_CALENDARIO ) )\n"
     "VAR InicioMes = DATE ( YEAR ( FechaMax ), MONTH ( FechaMax ), 1 )\n"
     "RETURN CALCULATE ( [Total horas perdidas], DIM_CALENDARIO[Fecha] >= InicioMes && DIM_CALENDARIO[Fecha] <= FechaMax )", "#,##0"),
    ("04 Tendencias", "Horas mes anterior",
     "VAR FechaMax = CALCULATE ( MAX ( FACT_INASISTENCIAS[Fecha] ), REMOVEFILTERS ( DIM_CALENDARIO ) )\n"
     "VAR InicioMes = DATE ( YEAR ( FechaMax ), MONTH ( FechaMax ), 1 )\n"
     "VAR InicioAnterior = EDATE ( InicioMes, -1 )\n"
     "RETURN CALCULATE ( [Total horas perdidas], DIM_CALENDARIO[Fecha] >= InicioAnterior && DIM_CALENDARIO[Fecha] < InicioMes )", "#,##0"),
    ("04 Tendencias", "Variación % horas mes", "DIVIDE ( [Horas último mes] - [Horas mes anterior], [Horas mes anterior] )", "+0.0%;-0.0%;0.0%"),
    ("04 Tendencias", "Horas YTD",
     "VAR FechaMax = CALCULATE ( MAX ( FACT_INASISTENCIAS[Fecha] ), REMOVEFILTERS ( DIM_CALENDARIO ) )\n"
     "RETURN CALCULATE ( [Total horas perdidas], DATESYTD ( DIM_CALENDARIO[Fecha] ), DIM_CALENDARIO[Fecha] <= FechaMax )", "#,##0"),
    ("04 Tendencias", "Inasistencias último mes",
     "VAR FechaMax = CALCULATE ( MAX ( FACT_INASISTENCIAS[Fecha] ), REMOVEFILTERS ( DIM_CALENDARIO ) )\n"
     "VAR InicioMes = DATE ( YEAR ( FechaMax ), MONTH ( FechaMax ), 1 )\n"
     "RETURN CALCULATE ( [Total inasistencias], DIM_CALENDARIO[Fecha] >= InicioMes && DIM_CALENDARIO[Fecha] <= FechaMax )", "#,##0"),
    ("04 Tendencias", "Inasistencias mes anterior",
     "VAR FechaMax = CALCULATE ( MAX ( FACT_INASISTENCIAS[Fecha] ), REMOVEFILTERS ( DIM_CALENDARIO ) )\n"
     "VAR InicioMes = DATE ( YEAR ( FechaMax ), MONTH ( FechaMax ), 1 )\n"
     "VAR InicioAnterior = EDATE ( InicioMes, -1 )\n"
     "RETURN CALCULATE ( [Total inasistencias], DIM_CALENDARIO[Fecha] >= InicioAnterior && DIM_CALENDARIO[Fecha] < InicioMes )", "#,##0"),
    ("04 Tendencias", "Variación % inasistencias mes", "DIVIDE ( [Inasistencias último mes] - [Inasistencias mes anterior], [Inasistencias mes anterior] )", "+0.0%;-0.0%;0.0%"),
    ("04 Tendencias", "Aprendices último mes",
     "VAR FechaMax = CALCULATE ( MAX ( FACT_INASISTENCIAS[Fecha] ), REMOVEFILTERS ( DIM_CALENDARIO ) )\n"
     "VAR InicioMes = DATE ( YEAR ( FechaMax ), MONTH ( FechaMax ), 1 )\n"
     "RETURN CALCULATE ( [Aprendices con inasistencias], DIM_CALENDARIO[Fecha] >= InicioMes && DIM_CALENDARIO[Fecha] <= FechaMax )", "#,##0"),
    ("04 Tendencias", "Horas no justificadas último mes",
     "VAR FechaMax = CALCULATE ( MAX ( FACT_INASISTENCIAS[Fecha] ), REMOVEFILTERS ( DIM_CALENDARIO ) )\n"
     "VAR InicioMes = DATE ( YEAR ( FechaMax ), MONTH ( FechaMax ), 1 )\n"
     "RETURN CALCULATE ( [Horas no justificadas], DIM_CALENDARIO[Fecha] >= InicioMes && DIM_CALENDARIO[Fecha] <= FechaMax )", "#,##0"),
    ("04 Tendencias", "% horas no justificadas último mes", "DIVIDE ( [Horas no justificadas último mes], [Horas último mes] )", "0.0%"),
    ("04 Tendencias", "Promedio mensual de horas",
     "VAR Meses = FILTER ( VALUES ( DIM_CALENDARIO[AnioMes] ), CALCULATE ( [Total inasistencias] ) > 0 )\n"
     "RETURN AVERAGEX ( Meses, CALCULATE ( [Total horas perdidas] ) )", "#,##0"),
    ("04 Tendencias", "Mes con más horas",
     "VAR Meses = ADDCOLUMNS ( FILTER ( VALUES ( DIM_CALENDARIO[EtiquetaMes] ), CALCULATE ( [Total inasistencias] ) > 0 ), \"@Horas\", CALCULATE ( [Total horas perdidas] ) )\n"
     "RETURN MAXX ( TOPN ( 1, Meses, [@Horas], DESC ), DIM_CALENDARIO[EtiquetaMes] )", None),
    ("04 Tendencias", "Horas del mes pico",
     "VAR Meses = ADDCOLUMNS ( FILTER ( VALUES ( DIM_CALENDARIO[EtiquetaMes] ), CALCULATE ( [Total inasistencias] ) > 0 ), \"@Horas\", CALCULATE ( [Total horas perdidas] ) )\n"
     "RETURN MAXX ( TOPN ( 1, Meses, [@Horas], DESC ), [@Horas] )", "#,##0"),
    ("04 Tendencias", "Promedio móvil 3 meses de horas",
     "VAR FechaMax = CALCULATE ( MAX ( FACT_INASISTENCIAS[Fecha] ), REMOVEFILTERS ( DIM_CALENDARIO ) )\n"
     "VAR Fin = EOMONTH ( FechaMax, 0 )\n"
     "RETURN CALCULATE ( AVERAGEX ( VALUES ( DIM_CALENDARIO[AnioMes] ), [Total horas perdidas] ), DATESINPERIOD ( DIM_CALENDARIO[Fecha], Fin, -3, MONTH ) )", "#,##0"),
    # -- Calidad de datos (carpeta 00 KPIs) --------------------------------
    ("00 KPIs", "Registros origen", str(RESUMEN["registros_origen"]), "#,##0"),
    ("00 KPIs", "Duplicados removidos", str(RESUMEN["duplicados_exactos"]), "#,##0"),
    ("00 KPIs", "% duplicados removidos", f"DIVIDE ( {RESUMEN['duplicados_exactos']}, {RESUMEN['registros_origen']} )", "0.00%"),
    ("00 KPIs", "Registros sin justificación", "CALCULATE ( COUNTROWS ( FACT_INASISTENCIAS ), ISBLANK ( FACT_INASISTENCIAS[JustificacionOriginal] ) )", "#,##0"),
    ("00 KPIs", "Registros no clasificados", 'CALCULATE ( COUNTROWS ( FACT_INASISTENCIAS ), FACT_INASISTENCIAS[CategoriaJustificacion] = "Sin información" )', "#,##0"),
    ("00 KPIs", "Registros que requieren revisión", "CALCULATE ( COUNTROWS ( FACT_INASISTENCIAS ), FACT_INASISTENCIAS[RequiereRevision] = 1 )", "#,##0"),
    ("00 KPIs", "% registros que requieren revisión", "DIVIDE ( [Registros que requieren revisión], [Total inasistencias] )", "0.0%"),
    ("00 KPIs", "Registros con horas atípicas", "CALCULATE ( COUNTROWS ( FACT_INASISTENCIAS ), FACT_INASISTENCIAS[EsOutlierHoras] = 1 )", "#,##0"),
    ("00 KPIs", "Justificaciones únicas", "DISTINCTCOUNT ( FACT_INASISTENCIAS[JustificacionOriginal] )", "#,##0"),
    ("00 KPIs", "Cobertura jornada", "0", "0.0%"),
    ("00 KPIs", "Cobertura modalidad", "0", "0.0%"),
    ("00 KPIs", "Cobertura estado académico", "0", "0.0%"),
    ("00 KPIs", "Cobertura matrícula", "0", "0.0%"),
    ("00 KPIs", "Cobertura documento", "DIVIDE ( CALCULATE ( [Aprendices con inasistencias], FACT_INASISTENCIAS[TieneDocumentoAprendiz] = 1 ), [Aprendices con inasistencias] )", "0.0%"),
    ("00 KPIs", "Fichas sin jornada", 'CALCULATE ( DISTINCTCOUNT ( FACT_INASISTENCIAS[FichaID] ), DIM_FICHA[Jornada] = "No informada" )', "#,##0"),
    ("00 KPIs", "Programas sin nivel formativo", 'CALCULATE ( DISTINCTCOUNT ( FACT_INASISTENCIAS[ProgramaID] ), DIM_PROGRAMA[NivelFormacion] = "No informado" )', "#,##0"),
    ("00 KPIs", "Fecha mínima de novedad", "MIN ( FACT_INASISTENCIAS[Fecha] )", "dd/mm/yyyy"),
    ("00 KPIs", "Fecha máxima de novedad", "MAX ( FACT_INASISTENCIAS[Fecha] )", "dd/mm/yyyy"),
    ("00 KPIs", "Días de cobertura", "DATEDIFF ( MIN ( FACT_INASISTENCIAS[Fecha] ), MAX ( FACT_INASISTENCIAS[Fecha] ), DAY ) + 1", "#,##0"),
    # -- Rankings ----------------------------------------------------------
    ("01 Inasistencias", "Top 10 Horas Ficha",
     "VAR Ranking = RANKX ( ALLSELECTED ( DIM_FICHA[FichaID] ), [Total horas perdidas], , DESC, Dense )\n"
     "RETURN IF ( NOT ISBLANK ( [Total horas perdidas] ) && Ranking <= 10, [Total horas perdidas] )", "#,##0"),
    ("01 Inasistencias", "Top 10 Horas No Justificadas Ficha",
     "VAR Ranking = RANKX ( ALLSELECTED ( DIM_FICHA[FichaID] ), [Horas no justificadas], , DESC, Dense )\n"
     "RETURN IF ( NOT ISBLANK ( [Horas no justificadas] ) && Ranking <= 10, [Horas no justificadas] )", "#,##0"),
    ("01 Inasistencias", "Top 10 Horas Programa",
     "VAR Ranking = RANKX ( ALLSELECTED ( DIM_PROGRAMA[NombrePrograma] ), [Total horas perdidas], , DESC, Dense )\n"
     "RETURN IF ( NOT ISBLANK ( [Total horas perdidas] ) && Ranking <= 10, [Total horas perdidas] )", "#,##0"),
    ("01 Inasistencias", "Top 10 Horas No Justificadas Programa",
     "VAR Ranking = RANKX ( ALLSELECTED ( DIM_PROGRAMA[NombrePrograma] ), [Horas no justificadas], , DESC, Dense )\n"
     "RETURN IF ( NOT ISBLANK ( [Horas no justificadas] ) && Ranking <= 10, [Horas no justificadas] )", "#,##0"),
    ("03 Aprendices", "Top 10 Aprendices Programa",
     "VAR Ranking = RANKX ( ALLSELECTED ( DIM_PROGRAMA[NombrePrograma] ), [Aprendices con inasistencias], , DESC, Dense )\n"
     "RETURN IF ( NOT ISBLANK ( [Aprendices con inasistencias] ) && Ranking <= 10, [Aprendices con inasistencias] )", "#,##0"),
    ("02 Riesgo", "Top 10 Índice de Riesgo Ficha",
     "VAR Universo = FILTER ( ALLSELECTED ( DIM_FICHA[FichaID] ), CALCULATE ( MAX ( DIM_FICHA[MuestraSuficiente] ) ) = 1 )\n"
     "VAR Ranking = RANKX ( Universo, [Índice de riesgo promedio de fichas], , DESC, Dense )\n"
     "RETURN IF ( CALCULATE ( MAX ( DIM_FICHA[MuestraSuficiente] ) ) = 1 && Ranking <= 10, [Índice de riesgo promedio de fichas] )", "0.0"),
]


# ---------------------------------------------------------------------------
# Escritura TMDL
# ---------------------------------------------------------------------------
def tmdl_type(tipo: str) -> str:
    return {
        "string": "string", "int64": "int64", "double": "double",
        "dateTime": "dateTime", "boolean": "boolean",
    }[tipo]


def escribir_tabla(nombre: str, spec: dict) -> None:
    lineas = [f"table {nombre}"]
    if spec.get("fecha"):
        lineas.append("\tdataCategory: Time")
    lineas.append("")

    if nombre == "FACT_INASISTENCIAS":
        for carpeta, medida, dax, fmt in MEDIDAS:
            lineas.append(f"\tmeasure '{medida}' = ```")
            for ln in dax.split("\n"):
                lineas.append("\t\t\t" + ln)
            lineas.append("\t\t\t```")
            if fmt:
                lineas.append(f"\t\tformatString: {fmt}")
            lineas.append(f"\t\tdisplayFolder: {carpeta}")
            lineas.append("")

    for col in spec["columnas"]:
        lineas.append(f"\tcolumn {col['nombre']}")
        lineas.append(f"\t\tdataType: {tmdl_type(col['tipo'])}")
        if col["nombre"] == "Fecha" and spec.get("fecha"):
            lineas.append("\t\tisKey")
        if col["fmt"]:
            lineas.append(f"\t\tformatString: {col['fmt']}")
        if col["oculta"]:
            lineas.append("\t\tisHidden")
        if col["resumen"] is not None:
            lineas.append(f"\t\tsummarizeBy: {col['resumen']}")
        if col["orden"]:
            lineas.append(f"\t\tsortByColumn: {col['orden']}")
        lineas.append(f"\t\tsourceColumn: {col['nombre']}")
        lineas.append("")

    if nombre == "DIM_APRENDIZ":
        lineas.extend([
            "\tcolumn EsTopRiesgo =",
            "\t\tIF ( RANKX ( ALL ( DIM_APRENDIZ[AprendizID] ), DIM_APRENDIZ[ScoreRiesgo], , DESC, Dense ) <= 15, 1, 0)",
            "\t\tdataType: int64",
            "\t\tformatString: 0",
            "\t\tisHidden",
            "\t\tsummarizeBy: none",
            "",
        ])

    tipos = ", ".join(
        f'{{"{col["nombre"]}", {M_TIPO[col["tipo"]]}}}'
        for col in spec["columnas"] if col["tipo"] != "double"
    )
    dobles = [col["nombre"] for col in spec["columnas"] if col["tipo"] == "double"]
    pasos = [
        f'\t\t\t\tOrigen = Csv.Document(File.Contents(RutaDatos & "\\{spec["archivo"]}"),[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        "\t\t\t\tEncabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars=true]),",
        f"\t\t\t\tTipos = Table.TransformColumnTypes(Encabezados,{{{tipos}}})",
    ]
    if dobles:
        # En una expresión let de M, cada paso debe separarse con coma.
        # El paso Tipos necesita coma antes de añadir Decimales.
        pasos[2] += ","
        decs = ",\n".join(
            f'\t\t\t\t\t{{"{c}", each if _ = null then null else if Text.Trim(_) = "" then null '
            f'else Number.FromText(Text.Trim(_), "en-US"), type number}}'
            for c in dobles
        )
        pasos.append(f"\t\t\t\tDecimales = Table.TransformColumns(Tipos,{{\n{decs}\n\t\t\t\t}})")
    pasos.extend(["\t\t\tin", f"\t\t\t\t{'Decimales' if dobles else 'Tipos'}", ""])
    lineas.extend([
        f"\tpartition {nombre} = m",
        "\t\tmode: import",
        "\t\tsource =",
        "\t\t\tlet",
        *pasos,
    ])

    (TABLES_DIR / f"{nombre}.tmdl").write_text("\n".join(lineas), encoding="utf-8")


def main() -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    for nombre, spec in TABLAS.items():
        escribir_tabla(nombre, spec)

    refs = "\n".join(f"ref table {n}" for n in TABLAS)
    (DEF / "model.tmdl").write_text(
        f"""model {MODEL_NAME}
\tculture: es-CO
\tdefaultPowerBIDataSourceVersion: powerBI_V3
\tsourceQueryCulture: es-CO

{refs}
""",
        encoding="utf-8",
    )

    (DEF / "expressions.tmdl").write_text(
        f'''expression RutaDatos = "{RUTA_DATOS}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]
\tannotation PBI_ResultType = Text
''',
        encoding="utf-8",
    )

    relaciones = [
        ("1f2d8a10-6c1d-4a5e-9f01-8c4b7d2e6a01", "FACT_INASISTENCIAS.Fecha", "DIM_CALENDARIO.Fecha"),
        ("2a3e9b21-7d2e-4b6f-8a12-9d5c8e3f7b02", "FACT_INASISTENCIAS.FichaID", "DIM_FICHA.FichaID"),
        ("3b4f0c32-8e3f-4c70-9b23-0e6d9f4a8c03", "FACT_INASISTENCIAS.AprendizID", "DIM_APRENDIZ.AprendizID"),
        ("4c5a1d43-9f40-4d81-8c34-1f7ea05b9d04", "FACT_INASISTENCIAS.ProgramaID", "DIM_PROGRAMA.ProgramaID"),
    ]
    (DEF / "relationships.tmdl").write_text(
        "\n".join(f"relationship {rid}\n\tfromColumn: {fc}\n\ttoColumn: {tc}\n" for rid, fc, tc in relaciones),
        encoding="utf-8",
    )

    (DEF / "database.tmdl").write_text("database\n\tcompatibilityLevel: 1604\n", encoding="utf-8")

    (MODEL / "definition.pbism").write_text(
        json.dumps({
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
            "version": "4.0",
            "settings": {},
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    (MODEL / ".platform").write_text(
        json.dumps({
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {"type": "SemanticModel", "displayName": MODEL_NAME},
            "config": {"version": "2.0", "logicalId": "a7c1e4f2-3b5d-4e6a-9f70-1c2d3e4f5a6b"},
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    (BASE / "CaracterizacionAprendicesASTIN.pbip").write_text(
        json.dumps({
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
            "version": "1.0",
            "artifacts": [
                {"report": {"path": "CaracterizacionAprendicesASTIN.Report"}},
            ],
            "settings": {"enableAutoRecovery": True},
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Modelo generado: {len(TABLAS)} tablas, {len(MEDIDAS)} medidas.")
    print(f"Ruta de datos: {DATA}")


if __name__ == "__main__":
    main()
