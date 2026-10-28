# -*- coding: utf-8 -*-
"""
ETL · Caracterización de Aprendices Centro ASTIN
------------------------------------------------
Construye el modelo estrella a partir de data/raw/Inasistencias.xls.

Entradas:
    data/raw/Inasistencias.xls

Salidas:
    data/processed/DIM_CALENDARIO.csv
    data/processed/DIM_APRENDIZ.csv
    data/processed/DIM_FICHA.csv
    data/processed/DIM_PROGRAMA.csv
    data/processed/FACT_INASISTENCIAS.csv
    data/processed/00_resumen_etl.json
    data/restricted/DIM_APRENDIZ_PII.csv   (NO publicar: contiene PII)

Criterios:
    * Se eliminan duplicados exactos.
    * Se conservan los registros con rangos de fechas; la fecha de imputación
      analítica es Fecha Inicio.
    * La clasificación de justificaciones es por reglas documentadas y
      auditables. Los casos dudosos se marcan para revisión.
    * El scoring de riesgo es una heurística operativa, no un modelo
      predictivo ni una decisión académica.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

BASE = Path(__file__).resolve().parents[1]
RAW = Path(os.environ.get(
    "INASISTENCIAS_SOURCE",
    str(
        Path.home()
        / "OneDrive - Servicio Nacional de Aprendizaje"
        / "Equipo ASTIN-DESAROLLOS POWER-BI - RAPS ASTIN 2026"
        / "Inasistencias.xls"
    ),
))
OUT = BASE / "data" / "processed"
RESTRICTED = BASE / "data" / "restricted"
OUT.mkdir(parents=True, exist_ok=True)
RESTRICTED.mkdir(parents=True, exist_ok=True)

# El corte se calcula desde los datos en cada ejecución; evita congelar el
# score de riesgo cuando se reemplaza el archivo por un extracto más reciente.
CENTRO = "ASTIN - Palmira"
CENTRO_COSTO = "ASTIN-PALMIRA"
REGIONAL = "Valle del Cauca"

MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}
MESES_CORTOS = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
}
DIAS = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"}


# ---------------------------------------------------------------------------
# Utilidades de texto
# ---------------------------------------------------------------------------
def norm(texto: Any) -> str:
    """Mayúsculas, sin tildes, sin signos y con espacios colapsados."""
    if texto is None or (isinstance(texto, float) and math.isnan(texto)):
        return ""
    s = str(texto).strip().upper()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def limpiar_espacios(texto: Any) -> str:
    if texto is None or (isinstance(texto, float) and math.isnan(texto)):
        return ""
    return re.sub(r"\s+", " ", str(texto).replace("\t", " ")).strip()


def titulo_programa(texto: str) -> str:
    """Título legible conservando siglas y nombres propios."""
    base = limpiar_espacios(texto).rstrip(".").strip()
    base = re.sub(r"\s+", " ", base)
    palabras = []
    minusculas = {"de", "del", "la", "las", "los", "el", "en", "y", "para", "por", "con", "a", "al"}
    for i, palabra in enumerate(base.split(" ")):
        low = palabra.lower()
        if i > 0 and low in minusculas:
            palabras.append(low)
        elif palabra.isupper() and len(palabra) <= 4:
            palabras.append(palabra)
        else:
            palabras.append(palabra.capitalize())
    return " ".join(palabras)


def hash_id(prefijo: str, valor: str, largo: int = 10) -> str:
    return f"{prefijo}-{hashlib.sha1(valor.encode('utf-8')).hexdigest()[:largo].upper()}"


def rank_pct(serie: pd.Series, mascara: pd.Series) -> pd.Series:
    """Percentil 0-100 calculado solo sobre las unidades elegibles."""
    return serie.where(mascara).rank(pct=True, method="average") * 100


# ---------------------------------------------------------------------------
# Programa: taxonomía derivada (documentada)
# ---------------------------------------------------------------------------
LINEA_POR_PROGRAMA = {
    "COORDINACION EN SISTEMAS INTEGRADOS DE GESTION": "Gestión y calidad",
    "MONITOREO AMBIENTAL": "Ambiental",
    "MODELADO 3D PARA LA INDUSTRIA": "Diseño y manufactura",
    "GESTION DE PROYECTOS DE DESARROLLO ECONOMICO Y SOCIAL": "Gestión y proyectos",
    "DESARROLLO DE COMPONENTES MECANICOS": "Manufactura",
    "APLICACION DE PROCEDIMIENTOS DE LABORATORIO QUIMICO": "Química y laboratorio",
    "DESARROLLO Y MODELADO DE PRODUCTOS INDUSTRIALES.": "Diseño y manufactura",
    "GESTIÓN DE LA PRODUCCIÓN INDUSTRIAL": "Manufactura",
    "FABRICACIÓN DE MOLDES Y TROQUELES": "Manufactura",
    "TRABAJO DE LA MADERA": "Manufactura",
    "FABRICACIÓN DE PRODUCTOS PLÁSTICOS POR INYECCIÓN Y SOPLADO": "Manufactura",
    "ANÁLISIS DE MATERIALES PARA LA INDUSTRIA": "Química y laboratorio",
    "COORDINACION DE PROCESOS LOGISTICOS": "Logística",
    "TRANSFORMACION DE POLIMEROS POR EXTRUSION DE PELICULA": "Manufactura",
    "PROCESOS DE MANUFACTURA.": "Manufactura",
    "SISTEMAS TELEINFORMÁTICOS": "Sistemas y TI",
    "ALISTAMIENTO DE LABORATORIOS DE ANALISIS Y ENSAYOS PARA LA INDUSTRIA": "Química y laboratorio",
    "QUÍMICA APLICADA A LA INDUSTRIA": "Química y laboratorio",
    "TRANSFORMACION DE POLIMEROS POR INYECCION": "Manufactura",
    "ENGLISH DOES WORK - LEVEL 11": "Idiomas",
    "ORIENTACION DEL PROYECTO DE VIDA CON EL USO DE ESTRATEGIAS INSPIRADORAS": "Complementaria",
    "INGLES BASICO - NIVEL 2": "Idiomas",
    "MANEJO BASICO DE LA HERRAMIENTA DE HOJAS DE CALCULO EXCEL": "Complementaria",
    "GESTION DEL DESARROLLO ADMINISTRATIVO E INNOVACION": "Gestión y proyectos",
    "PROGRAMACION DE APLICACIONES PARA DISPOSITIVOS MOVILES": "Sistemas y TI",
    "DESARROLLO MULTIMEDIA Y WEB": "Sistemas y TI",
}

COMPLEMENTARIAS = {
    "ENGLISH DOES WORK - LEVEL 11",
    "INGLES BASICO - NIVEL 2",
    "MANEJO BASICO DE LA HERRAMIENTA DE HOJAS DE CALCULO EXCEL",
    "ORIENTACION DEL PROYECTO DE VIDA CON EL USO DE ESTRATEGIAS INSPIRADORAS",
}

# Las llaves del modelo se normalizan (sin tildes, sin signos), por lo que los
# catálogos anteriores deben normalizarse para que el cruce sea exacto.
LINEA_POR_PROGRAMA_NORM = {norm(k): v for k, v in LINEA_POR_PROGRAMA.items()}
COMPLEMENTARIAS_NORM = {norm(k) for k in COMPLEMENTARIAS}


# ---------------------------------------------------------------------------
# Clasificación de justificaciones
# ---------------------------------------------------------------------------
# Frases que niegan de manera explícita la justificación. Tienen prioridad
# sobre cualquier palabra de salud/familia que aparezca en el mismo texto.
NEGACION_EXPLICITA = [
    "SIN JUSTIFIC", "SIN JUSTIC", "SIN JUSTIFI", "SIN JUSTIFICACON", "SIN JUSTIFIACION",
    "SIN JSUTIF", "SIN JUDTIF", "SIN JUSTIFICAICON", "SIN JUSTIFICACION",
    "SIN LA DEBIDA JUSTIFICACION", "SIN DEBIDA JUSTIFICACION", "SIN JUSTIFICACION DEBIDA",
    "NO JUSTIFICAD", "INJUSTIFICAD", "NO HAY JUSTIFICACION", "NO EXISTE JUSTIFICACION",
    "NO PRESENTA JUSTIFICACION", "NO PRESENTO JUSTIFICACION", "NO ENVIA JUSTIFICACION",
    "NO TIENE JUSTIFICACION", "NO CUENTA CON JUSTIFICACION",
    "SIN EXCUSA", "NO PRESENTA EXCUSA", "NO PRESENTO EXCUSA", "NO ENVIA EXCUSA",
    "NO EXCUSA", "NO HAY EXCUSA", "NO TIENE EXCUSA", "NO CUENTA CON EXCUSA",
    "NO ENVIO EXCUSA", "NO ENVIO SOPORTE", "NO ENVIA SOPORTE", "NO PRESENTA SOPORTE",
    "NO PRESENTO SOPORTE", "SIN SOPORTE", "NO ADJUNTA", "NO DOCUMENTA",
    "NO APORTA SOPORTE", "NO CUENTA CON SOPORTE", "NO PRESENTA EL SOPORTE",
]
NEGACION_SIN_INFO = [
    "SIN INFORMACION", "NO INFORMA", "NO INFORMO", "NO REPORTA", "NO HAY INFORMACION",
    "NO EXISTE INFORMACION", "NO SE TIENE INFORMACION", "SIN DATO", "SIN DATOS",
]

# Razones que, si existen, justifican la novedad (si no hay negación explícita).
SALUD = [
    "INCAPACIDAD", "INCAPACITAD", "MEDICA", "MEDICO", "ENFERMEDAD", "ENFERMA", "ENFERMO",
    "PROBLEMAS DE SALUD", "SALUD", "CITA", "TERAPIA", "TERAPIAS", "CIRUGIA", "HOSPITAL",
    "CLINICA", "EPS", "ACCIDENTE", "REPOSO", "LICENCIA", "COVID", "ODONTOLOG", "OPTICA",
    "URGENCIA", "DOLOR", "INDISPUESTA", "INDISPUESTO", "DISCAPACIDAD", "EMBARAZO",
    "CONTROL MEDICO", "EXAMEN MEDICO", "TRATAMIENTO", "FISIOTERAPIA", "PSICOLOG",
    "SALUD MENTAL", "ATENCION MEDICA", "RX", "EXAMENES", "PATOLOGIA", "DIAGNOSTICO",
    "QUIMIOTERAPIA", "RECUPERACION", "POSTOPERATORIO", "OPERACION", "TRANSPLANTE",
]
FAMILIA = [
    "CALAMIDAD", "FALLECIMIENTO", "FALLECIO", "LUTO", "DUELO", "EMERGENCIA FAMILIAR",
    "SITUACION URGENTE", "SITUACION FAMILIAR", "PROBLEMAS FAMILIARES", "ACCIDENTE FAMILIAR",
    "HIJO", "HIJA", "MADRE", "PADRE", "ABUEL", "FAMILIAR", "CUIDADO", "ACOMPANAMIENTO",
    "ACOMPANA", "ENFERMEDAD DE", "HOSPITALIZACION",
]
INSTITUCIONAL = [
    "PERMISO", "EXCUSA", "AUTORIZACION", "REUNION", "VOCERO", "VOCERIA", "REPRESENTANTE",
    "DELEGADO", "COMITE", "CONSEJO", "ASAMBLEA", "EVENTO", "COMPETENCIA", "DEPORTIVO",
    "OLIMPIADA", "FERIA", "SEMINARIO", "CAPACITACION", "CONGRESO", "FORO", "MESA",
    "SINDICAL", "CELEBRACION", "BIENESTAR", "CULTURAL", "ARTISTICO", "WORLDSKILLS",
    "WORLD SKILLS", "SENA", "TRASLADO DE SEDE", "CAMBIO DE JORNADA", "DOMICILIARIA",
    "VACACIONES", "VACIONES",
]
TRANSPORTE = [
    "TRANSPORTE", "MOVILIDAD", "PARO", "BLOQUEO", "VIA", "BUS", "TAXI", "MOTO",
    "ACCIDENTE DE TRANSITO", "LLUVIA", "INUNDACION", "SISMO", "TERREMOTO", "CLIMA",
    "DERRUMBE", "MARCHA", "COMBUSTIBLE", "PICO Y PLACA",
]
CONECTIVIDAD = [
    "INTERNET", "CONEXION", "CONECTIVIDAD", "SENAL", "ENERGIA", "LUZ", "PLATAFORMA",
    "VIRTUAL", "WIFI", "COMPUTADOR", "EQUIPO", "DATOS",
]
LEGAL = [
    "CITA LEGAL", "JUZGADO", "FISCALIA", "POLICIA", "ICBF", "MIGRACION", "NOTARIA",
    "TRAMITE", "DOCUMENTO", "CEDULA", "PASAPORTE", "VISA", "BANCO", "REGISTRO",
    "DECLARACION", "AUDIENCIA", "DEMANDA", "ABOGADO", "COMISARIA", "INSPECCION",
    "SALIO EN LIBERTAD", "DETENIDO", "CARCEL",
]

DESERCION = [
    "DESERCION", "EN PROCESO DE DESERCION", "PENDIENTE DESERCION", "RETIRO", "SE RETIRO",
    "SE RETIRA", "EN PROCESO DE RETIRO", "APLAZAMIENTO", "SOLICITO APLAZAMIENTO",
    "REINGRESO", "NUNCA INGRESO", "NUNCA SE PRESENTO", "NO VOLVIO", "NO REGRESO",
    "DEJO DE ASISTIR", "NO CONTINUO", "NO CONTINUA", "NO APARECIO", "SE AUSENTO",
    "NO QUIERE", "NO QUERER", "NO PODRA SEGUIR", "NO PUEDE SEGUIR", "OTROS COMPROMISOS",
    "POR MOTIVOS PERSONALES", "PROBLEMAS PERSONALES", "MOTIVOS PERSONALES",
    "NO INGRESA HACE", "NO INGRESO HACE", "NO INGRESA A PLATAFORMA HACE",
]
RETARDO = [
    "RETARDO", "RETRASO", "LLEGO TARDE", "LLEGA TARDE", "LLEGADA TARDE", "SE PRESENTO TARDE",
    "INGRESA DESPUES", "INGRESO DESPUES", "SALIO ANTES", "SE RETIRO ANTES", "SE RETIRA ANTES",
    "LLEGO 30 MINUTOS TARDE", "LLEGO TARDE 30 MINUTOS", "TARDE A LA FORMACION",
]
PERSONAL = [
    "TRABAJO", "TRABAJAR", "LABORAL", "PERSONAL", "ECONOMIC", "DINERO", "TRASTEO",
    "MUDANZA", "COMPROMISO", "NO PUEDE", "NO PODRA", "SALIO EN LIBERTAD", "LIBERTAD",
    "DETENIDO", "CARCEL", "NO TIENE EL TIEMPO", "DIFICULTADES", "PRIORIDAD LABORAL",
]
NO_ASISTENCIA = [
    "NO ASISTE", "NO ASISTIO", "NO ASISTI", "NO SE PRESENTA", "NO PRESENTA", "NO LLEGO",
    "NO LLEGA", "NO INGRESO", "NO INGRESA", "NUNCA", "NO SE CONECTO", "NO SE CONECTA",
    "AUSENTE", "AUSENCIA", "FALTO", "FALTA", "NO VINO", "NO ESTUVO", "NO ESTA",
    "NO SE ENCUENTRA", "NO APARECIO", "NO SE PRESENTO",
]
NO_JUSTIFICACION_SIMPLE = ["NO", "NINGUNA", "NINGUNO", "NO TIENE", "NO HAY", "NO APLICA", "N A"]
# Excusas genéricas: acreditan una excusa, pero no permiten conocer la causa.
# Se clasifican como justificadas con confianza baja y revisión obligatoria.
EXCUSA_SIN_DETALLE = {
    "EXCUSA", "CON EXCUSA", "EXCUSA ACUDIENTE", "CON EXCUSA ACUDIENTE",
    "EXCUSA DEL ACUDIENTE", "EXCUSA POR PARTE DEL ACUDIENTE",
    "PRESENTA EXCUSA", "PRESENTO EXCUSA", "PRESENTA EXCUSA ACUDIENTE",
    "PRESENTO EXCUSA ACUDIENTE", "JUSTIFICACION", "CON JUSTIFICACION",
    "PRESENTA JUSTIFICACION", "PRESENTO JUSTIFICACION", "JUSTIFICADO",
}


def contiene(texto: str, patrones: list[str]) -> str | None:
    for p in patrones:
        if p in texto:
            return p
    return None


def clasificar_justificacion(valor: Any, es_retardo_texto: bool) -> dict[str, Any]:
    """
    Devuelve categoría, tipo, confianza, requiere_revision, regla y soporte.
    """
    t = norm(valor)
    if not t or t in {"NAN", "NONE", "NULL"}:
        return dict(categoria="Sin información", tipo="Sin información", confianza="Baja",
                    revision=1, regla="Vacío / nulo", soporte=0)

    # 1. Negación explícita de justificación o soporte
    p = contiene(t, NEGACION_EXPLICITA)
    if p:
        tipo = "Falta de soporte" if "SOPORTE" in p or "ADJUNTA" in p or "DOCUMENTA" in p else "Sin justificación"
        return dict(categoria="No justificada", tipo=tipo, confianza="Alta",
                    revision=0, regla=f"Negación explícita: {p}", soporte=0)

    # 2. No informa / no reporta
    p = contiene(t, NEGACION_SIN_INFO)
    if p:
        return dict(categoria="No justificada", tipo="No informa", confianza="Alta",
                    revision=0, regla=f"No informa: {p}", soporte=0)

    # 3. Razones justificables (si no hay negación)
    p_salud = contiene(t, SALUD)
    p_familia = contiene(t, FAMILIA)
    p_inst = contiene(t, INSTITUCIONAL)
    p_trans = contiene(t, TRANSPORTE)
    p_conn = contiene(t, CONECTIVIDAD)
    p_legal = contiene(t, LEGAL)

    soporte = 1 if any(x in t for x in ["SOPORTE", "CERTIFICADO", "ADJUNTO", "DOCUMENTO", "INCAPACIDAD", "AUTORIZACION", "EVIDENCIA"]) else 0
    pendiente = "PENDIENTE" in t

    if p_salud or p_familia:
        if p_salud:
            tipo = "Incapacidad / salud"
            regla = f"Salud: {p_salud}"
        else:
            tipo = "Calamidad doméstica"
            regla = f"Familia: {p_familia}"
        confianza = "Alta" if soporte or "INCAPACIDAD" in t else "Media"
        return dict(categoria="Justificada", tipo=tipo, confianza=confianza,
                    revision=1 if pendiente or not soporte else 0, regla=regla, soporte=soporte)

    if p_legal:
        return dict(categoria="Justificada", tipo="Trámite legal", confianza="Media",
                    revision=1 if pendiente or not soporte else 0, regla=f"Legal: {p_legal}", soporte=soporte)

    if t in EXCUSA_SIN_DETALLE:
        return dict(categoria="Justificada", tipo="Excusa sin detalle", confianza="Baja",
                    revision=1, regla="Excusa genérica sin causa", soporte=soporte)

    if p_inst:
        tipo = "Permiso institucional"
        if any(x in t for x in ["VACACIONES", "VACIONES"]):
            tipo = "Vacaciones / permiso"
        confianza = "Alta" if soporte or "REUNION" in t or "VOCERO" in t or "EVENTO" in t else "Baja"
        return dict(categoria="Justificada", tipo=tipo, confianza=confianza,
                    revision=1 if confianza == "Baja" or pendiente else 0, regla=f"Institucional: {p_inst}", soporte=soporte)

    if p_trans:
        return dict(categoria="Justificada", tipo="Transporte / movilidad", confianza="Media",
                    revision=1 if pendiente else 0, regla=f"Transporte: {p_trans}", soporte=soporte)

    if p_conn:
        return dict(categoria="Justificada", tipo="Conectividad", confianza="Media",
                    revision=1 if pendiente else 0, regla=f"Conectividad: {p_conn}", soporte=soporte)

    # 4. Deserción / retiro
    p = contiene(t, DESERCION)
    if p:
        return dict(categoria="No justificada", tipo="Deserción / retiro", confianza="Alta",
                    revision=0, regla=f"Deserción: {p}", soporte=0)

    # 5. Retardo
    if es_retardo_texto or contiene(t, RETARDO):
        p = contiene(t, RETARDO) or "Retardo"
        return dict(categoria="No justificada", tipo="Retardo", confianza="Alta",
                    revision=0, regla=f"Retardo: {p}", soporte=0)

    # 6. Motivo personal / trabajo
    p = contiene(t, PERSONAL)
    if p:
        return dict(categoria="No justificada", tipo="Motivo personal", confianza="Media",
                    revision=1, regla=f"Motivo personal: {p}", soporte=0)

    # 7. No asistencia genérica
    p = contiene(t, NO_ASISTENCIA)
    if p:
        return dict(categoria="No justificada", tipo="No asistió", confianza="Alta",
                    revision=0, regla=f"No asistencia: {p}", soporte=0)

    if t in NO_JUSTIFICACION_SIMPLE:
        return dict(categoria="No justificada", tipo="Sin justificación", confianza="Alta",
                    revision=0, regla="Negación simple", soporte=0)

    # 8. Casos dudosos
    if t.startswith("NO "):
        return dict(categoria="No justificada", tipo="No justificada (otro)", confianza="Baja",
                    revision=1, regla="Texto inicia con NO", soporte=0)

    return dict(categoria="Sin información", tipo="No clasificado", confianza="Baja",
                revision=1, regla="Sin regla", soporte=0)


# ---------------------------------------------------------------------------
# Lectura y limpieza
# ---------------------------------------------------------------------------
def main() -> None:
    print(f"Leyendo {RAW}")
    df = pd.read_excel(RAW, sheet_name="Sheet1")
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={
        "Instructor": "Instructor",
        "Ficha": "Ficha",
        "Programa": "Programa",
        "Apellidos": "NombreCompleto",
        "Nombres": "Nombres",
        "Identificacion Aprendiz": "DocumentoRaw",
        "Fecha Inicio": "FechaInicio",
        "Fecha Fin": "FechaFin",
        "Cant.horas": "Horas",
        "Justificacion": "JustificacionRaw",
    })

    registros_origen = len(df)
    df["NombreCompleto"] = df["NombreCompleto"].map(limpiar_espacios)
    df["ProgramaRaw"] = df["Programa"].map(limpiar_espacios)
    df["Instructor"] = df["Instructor"].map(limpiar_espacios)
    df["DocumentoRaw"] = df["DocumentoRaw"].map(limpiar_espacios)
    df["JustificacionRaw"] = df["JustificacionRaw"].map(limpiar_espacios)

    # Fechas y horas
    df["FechaInicio"] = pd.to_datetime(df["FechaInicio"], errors="coerce").dt.date
    df["FechaFin"] = pd.to_datetime(df["FechaFin"], errors="coerce").dt.date
    df["Horas"] = pd.to_numeric(df["Horas"], errors="coerce").fillna(0).astype(int)

    # Fechas inválidas: se descartan
    invalidas = df["FechaInicio"].isna() | df["FechaFin"].isna() | (df["FechaFin"] < df["FechaInicio"])
    n_invalidas = int(invalidas.sum())
    df = df.loc[~invalidas].copy()

    # Documento
    doc_split = df["DocumentoRaw"].str.extract(r"^\s*([A-Za-z]+)\s*-\s*([0-9]+)\s*$")
    df["TipoDocumento"] = doc_split[0].fillna("OTRO").str.upper()
    df["Documento"] = doc_split[1].fillna(df["DocumentoRaw"].str.replace(r"\D", "", regex=True))
    df["Documento"] = df["Documento"].replace("", pd.NA)

    # Ficha y programa
    df["FichaID"] = df["Ficha"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    df["ProgramaKey"] = df["ProgramaRaw"].map(norm)
    df["NombrePrograma"] = df["ProgramaRaw"].map(titulo_programa)

    # Deduplicación: se normalizan espacios, fechas, horas y el texto de la
    # justificación para detectar duplicados que difieren solo en tildes/mayúsculas.
    df["_just_norm"] = df["JustificacionRaw"].map(norm)
    cols_dup = ["Instructor", "FichaID", "ProgramaRaw", "NombreCompleto", "DocumentoRaw",
                "FechaInicio", "FechaFin", "Horas", "_just_norm"]
    antes = len(df)
    df["_dup"] = df.duplicated(subset=cols_dup, keep="first")
    duplicados = int(df["_dup"].sum())
    df = df.loc[~df["_dup"]].drop(columns=["_dup"]).copy()
    print(f"Registros origen={registros_origen:,} · inválidos={n_invalidas} · duplicados={duplicados:,} · válidos={len(df):,}")

    # Fecha de corte: máximo FechaFin observado
    corte = df["FechaFin"].max()
    df["DiasCubiertos"] = (pd.to_datetime(df["FechaFin"]) - pd.to_datetime(df["FechaInicio"])).dt.days + 1
    df["HorasPorDia"] = df["Horas"] / df["DiasCubiertos"].clip(lower=1)
    df["EsOutlierHoras"] = ((df["Horas"] > 60) | (df["HorasPorDia"] > 12)).astype(int)
    df["EsRetardoTexto"] = df["JustificacionRaw"].map(norm).str.contains(
        "|".join(re.escape(x) for x in RETARDO), regex=True
    )

    # Clasificación
    clas = df.apply(lambda r: clasificar_justificacion(r["JustificacionRaw"], bool(r["EsRetardoTexto"])), axis=1)
    clas_df = pd.DataFrame(list(clas))
    for c in clas_df.columns:
        df[c] = clas_df[c].values
    df["EsRetardo"] = ((df["tipo"] == "Retardo") | df["EsRetardoTexto"]).astype(int)
    df["EsAusencia"] = (1 - df["EsRetardo"]).astype(int)
    df["EsJustificada"] = (df["categoria"] == "Justificada").astype(int)
    df["EsNoJustificada"] = (df["categoria"] == "No justificada").astype(int)
    df["EsSinInformacion"] = (df["categoria"] == "Sin información").astype(int)

    # IDs
    df["AprendizKey"] = df["TipoDocumento"].fillna("OTRO") + "|" + df["Documento"].fillna(df["NombreCompleto"]).astype(str)
    df["AprendizID"] = df["AprendizKey"].map(lambda x: hash_id("APR", x))
    df["ProgramaID"] = df["ProgramaKey"].map(lambda x: hash_id("PRG", x, 8))
    df["InasistenciaID"] = df.apply(
        lambda r: hash_id("INA", "|".join([
            r["AprendizKey"], r["FichaID"], str(r["FechaInicio"]), str(r["FechaFin"]),
            str(r["Horas"]), norm(r["JustificacionRaw"]), r["Instructor"],
        ]), 12), axis=1
    )

    # Ficha -> programa consistente; instructor principal = moda
    ficha_prog = df.groupby("FichaID")["ProgramaID"].agg(lambda s: s.value_counts().index[0])
    ficha_instructor = df.groupby("FichaID")["Instructor"].agg(lambda s: s.value_counts().index[0])
    ficha_n_instructores = df.groupby("FichaID")["Instructor"].nunique()

    # ------------------------------------------------------------------
    # Dimensiones
    # ------------------------------------------------------------------
    # DIM_PROGRAMA
    prog = df.groupby(["ProgramaID", "ProgramaKey"], as_index=False).agg(
        NombrePrograma=("NombrePrograma", "first"),
        NombreOriginal=("ProgramaRaw", "first"),
        Aprendices=("AprendizID", "nunique"),
        Inasistencias=("InasistenciaID", "size"),
        Horas=("Horas", "sum"),
        PrimeraNovedad=("FechaInicio", "min"),
        UltimaNovedad=("FechaFin", "max"),
    )
    prog["HorasNoJustificadas"] = prog["ProgramaID"].map(
        df.loc[df["EsNoJustificada"] == 1].groupby("ProgramaID")["Horas"].sum()
    ).fillna(0).astype(int)
    prog["PctHorasNoJust"] = prog["HorasNoJustificadas"] / prog["Horas"].clip(lower=1)
    prog["HorasPorAprendiz"] = prog["Horas"] / prog["Aprendices"].clip(lower=1)
    prog["InasPorAprendiz"] = prog["Inasistencias"] / prog["Aprendices"].clip(lower=1)
    prog["LineaFormacion"] = prog["ProgramaKey"].map(LINEA_POR_PROGRAMA_NORM).fillna("Otra línea")
    prog["TipoFormacion"] = prog["ProgramaKey"].map(
        lambda x: "Complementaria" if x in COMPLEMENTARIAS_NORM else "Titulada"
    )
    prog["CentroCosto"] = CENTRO_COSTO
    prog["CentroFormacion"] = CENTRO
    prog["Regional"] = REGIONAL
    prog["NivelFormacion"] = "No informado"

    # Índice de riesgo de programa: percentiles ponderados solo entre programas
    # con evidencia suficiente (>= 5 aprendices y >= 100 horas).
    mask_prog = (prog["Aprendices"] >= 5) & (prog["Horas"] >= 100)
    prog["MuestraSuficiente"] = mask_prog.astype(int)
    prog_score = (
        0.40 * rank_pct(prog["HorasPorAprendiz"], mask_prog)
        + 0.25 * rank_pct(prog["InasPorAprendiz"], mask_prog)
        + 0.20 * rank_pct(prog["PctHorasNoJust"], mask_prog)
        + 0.15 * rank_pct(prog["Horas"], mask_prog)
    )
    prog["IndiceRiesgoCorte"] = prog_score.round(1)
    prog["NivelRiesgoCorte"] = pd.cut(
        prog["IndiceRiesgoCorte"], bins=[-0.01, 45, 70, 100.01], labels=["Bajo", "Medio", "Alto"]
    ).astype(str)
    prog.loc[~mask_prog, "NivelRiesgoCorte"] = "Muestra baja"

    prog = prog.sort_values(["Horas"], ascending=False).reset_index(drop=True)
    prog["RankingHoras"] = range(1, len(prog) + 1)
    prog_out = prog[[
        "ProgramaID", "NombrePrograma", "NombreOriginal", "LineaFormacion", "TipoFormacion",
        "CentroCosto", "CentroFormacion", "Regional", "NivelFormacion",
        "Aprendices", "Inasistencias", "Horas", "HorasNoJustificadas", "PctHorasNoJust",
        "HorasPorAprendiz", "InasPorAprendiz", "MuestraSuficiente", "IndiceRiesgoCorte",
        "NivelRiesgoCorte", "RankingHoras", "PrimeraNovedad", "UltimaNovedad",
    ]].copy()
    prog_out["NombreOriginal"] = prog_out["NombreOriginal"].str.rstrip(".")
    prog_out.to_csv(OUT / "DIM_PROGRAMA.csv", index=False, encoding="utf-8")

    # DIM_FICHA
    ficha = df.groupby("FichaID", as_index=False).agg(
        ProgramaID=("ProgramaID", "first"),
        Aprendices=("AprendizID", "nunique"),
        Inasistencias=("InasistenciaID", "size"),
        Horas=("Horas", "sum"),
        HorasNoJustificadas=("Horas", lambda s: int(df.loc[s.index][df.loc[s.index, "EsNoJustificada"] == 1]["Horas"].sum())),
        PrimeraNovedad=("FechaInicio", "min"),
        UltimaNovedad=("FechaFin", "max"),
    )
    ficha["InstructorPrincipal"] = ficha["FichaID"].map(ficha_instructor)
    ficha["TotalInstructores"] = ficha["FichaID"].map(ficha_n_instructores).fillna(1).astype(int)
    ficha["Jornada"] = "No informada"
    ficha["Modalidad"] = "No informada"
    ficha["Sede"] = CENTRO
    ficha["CentroCosto"] = CENTRO_COSTO
    ficha["EstadoFicha"] = ficha["UltimaNovedad"].map(
        lambda d: "Con novedad reciente" if (corte - d).days <= 30 else "Sin novedad reciente"
    )
    ficha["DiasSinNovedad"] = ficha["UltimaNovedad"].map(lambda d: (corte - d).days)
    ficha["LineaFormacion"] = ficha["ProgramaID"].map(prog.set_index("ProgramaID")["LineaFormacion"])

    # Métricas para scoring estático al corte
    ficha["HorasPorAprendiz"] = ficha["Horas"] / ficha["Aprendices"].clip(lower=1)
    ficha["InasPorAprendiz"] = ficha["Inasistencias"] / ficha["Aprendices"].clip(lower=1)
    ficha["PctHorasNoJust"] = ficha["HorasNoJustificadas"] / ficha["Horas"].clip(lower=1)

    # Índice de riesgo de ficha: percentiles ponderados solo entre fichas con
    # evidencia suficiente (>= 5 aprendices y >= 100 horas). Evita que cursos
    # complementarios de 1 aprendiz distorsionen el ranking.
    mask_ficha = (ficha["Aprendices"] >= 5) & (ficha["Horas"] >= 100)
    ficha["MuestraSuficiente"] = mask_ficha.astype(int)
    score = (
        0.40 * rank_pct(ficha["HorasPorAprendiz"], mask_ficha)
        + 0.25 * rank_pct(ficha["InasPorAprendiz"], mask_ficha)
        + 0.20 * rank_pct(ficha["PctHorasNoJust"], mask_ficha)
        + 0.15 * rank_pct(ficha["Horas"], mask_ficha)
    )
    ficha["IndiceRiesgoCorte"] = score.round(1)
    ficha["NivelRiesgoCorte"] = pd.cut(
        ficha["IndiceRiesgoCorte"], bins=[-0.01, 45, 70, 100.01], labels=["Bajo", "Medio", "Alto"]
    ).astype(str)
    ficha.loc[~mask_ficha, "NivelRiesgoCorte"] = "Muestra baja"

    ficha_out = ficha[[
        "FichaID", "ProgramaID", "InstructorPrincipal", "TotalInstructores", "Jornada", "Modalidad",
        "Sede", "CentroCosto", "LineaFormacion", "EstadoFicha", "DiasSinNovedad",
        "Aprendices", "Inasistencias", "Horas", "HorasNoJustificadas", "PctHorasNoJust",
        "HorasPorAprendiz", "InasPorAprendiz", "MuestraSuficiente", "IndiceRiesgoCorte",
        "NivelRiesgoCorte", "PrimeraNovedad", "UltimaNovedad",
    ]].sort_values(["IndiceRiesgoCorte", "Horas"], ascending=[False, False])
    ficha_out.to_csv(OUT / "DIM_FICHA.csv", index=False, encoding="utf-8")

    # DIM_APRENDIZ (anonimizado)
    ap = df.groupby("AprendizID", as_index=False).agg(
        TipoDocumento=("TipoDocumento", "first"),
        Documento=("Documento", "first"),
        NombreCompleto=("NombreCompleto", "first"),
        FichaPrincipal=("FichaID", lambda s: s.value_counts().index[0]),
        ProgramaPrincipal=("ProgramaID", lambda s: s.value_counts().index[0]),
        Inasistencias=("InasistenciaID", "size"),
        Horas=("Horas", "sum"),
        Justificadas=("EsJustificada", "sum"),
        NoJustificadas=("EsNoJustificada", "sum"),
        Retardos=("EsRetardo", "sum"),
        HorasNoJustificadas=("Horas", lambda s: int(df.loc[s.index][df.loc[s.index, "EsNoJustificada"] == 1]["Horas"].sum())),
        PrimeraNovedad=("FechaInicio", "min"),
        UltimaNovedad=("FechaFin", "max"),
        TextoDesercion=("JustificacionRaw", lambda s: int(any(
            any(k in norm(x) for k in ["DESERCION", "RETIRO", "NO VOLVIO", "NO REGRESO", "APLAZAMIENTO", "NO QUIERE", "NO PODRA SEGUIR", "NO INGRESA HACE", "NO INGRESO HACE"])
            for x in s
        ))),
    )
    ap["DocumentoEnmascarado"] = ap.apply(
        lambda r: f"{r['TipoDocumento']}-****{str(r['Documento'])[-4:]}" if pd.notna(r["Documento"]) else "SIN DOCUMENTO",
        axis=1,
    )
    ap["Iniciales"] = ap["NombreCompleto"].map(
        lambda n: " ".join([p[0] for p in n.split()[:2]]) + "." if n else "N.D."
    )
    ap["DiasDesdeUltimaNovedad"] = ap["UltimaNovedad"].map(lambda d: (corte - d).days)
    ap["ScoreRiesgo"] = (
        0.70 * (ap["NoJustificadas"] / 20).clip(upper=1) * 100
        + 0.30 * (ap["Horas"] / 100).clip(upper=1) * 100
    ).round(1)
    ap["NivelRiesgo"] = pd.cut(ap["ScoreRiesgo"], bins=[-0.01, 45, 70, 100.01], labels=["Bajo", "Medio", "Alto"]).astype(str)
    ap["EsReincidente"] = (ap["Inasistencias"] >= 3).astype(int)
    ap["EsReincidenteAlto"] = (ap["Inasistencias"] >= 8).astype(int)
    ap["AlertaPorPatron"] = (
        (ap["DiasDesdeUltimaNovedad"] <= 45)
        & (ap["NoJustificadas"] >= 10)
        & (ap["HorasNoJustificadas"] >= 80)
    ).astype(int)
    ap["AlertaDesercion"] = ((ap["TextoDesercion"] == 1) | (ap["AlertaPorPatron"] == 1)).astype(int)
    ap["MotivoAlertaDesercion"] = ap.apply(
        lambda r: "Texto y patrón" if r["TextoDesercion"] == 1 and r["AlertaPorPatron"] == 1
        else ("Texto de retiro/deserción" if r["TextoDesercion"] == 1
              else ("Patrón de ausencias" if r["AlertaPorPatron"] == 1 else "Sin alerta")),
        axis=1,
    )
    ap["EstadoAsistencia"] = ap["NivelRiesgo"].map(
        {"Bajo": "Estable", "Medio": "En seguimiento", "Alto": "Crítico"}
    )
    ap["FichaPrincipal"] = ap["FichaPrincipal"].astype(str)

    ap_out = ap[[
        "AprendizID", "TipoDocumento", "DocumentoEnmascarado", "Iniciales",
        "FichaPrincipal", "ProgramaPrincipal", "Inasistencias", "Horas",
        "Justificadas", "NoJustificadas", "Retardos", "HorasNoJustificadas",
        "ScoreRiesgo", "NivelRiesgo", "EstadoAsistencia", "EsReincidente", "EsReincidenteAlto",
        "AlertaDesercion", "MotivoAlertaDesercion", "DiasDesdeUltimaNovedad",
        "PrimeraNovedad", "UltimaNovedad",
    ]].sort_values("Horas", ascending=False)
    ap_out.to_csv(OUT / "DIM_APRENDIZ.csv", index=False, encoding="utf-8")

    # PII restringida (no se publica en Power BI)
    pii = ap[["AprendizID", "NombreCompleto", "TipoDocumento", "Documento", "FichaPrincipal", "ProgramaPrincipal", "Horas"]].copy()
    pii = pii.merge(prog[["ProgramaID", "NombrePrograma"]], left_on="ProgramaPrincipal", right_on="ProgramaID", how="left")
    pii = pii[["AprendizID", "NombreCompleto", "TipoDocumento", "Documento", "FichaPrincipal", "NombrePrograma", "Horas"]]
    pii.to_csv(RESTRICTED / "DIM_APRENDIZ_PII.csv", index=False, encoding="utf-8")

    # DIM_CALENDARIO
    fecha_min_cal = pd.Timestamp(df["FechaInicio"].min()).normalize().replace(month=1, day=1)
    fecha_max_cal = pd.Timestamp(max(corte, df["FechaFin"].max())).normalize().replace(month=12, day=31)
    cal = pd.DataFrame({"Fecha": pd.date_range(fecha_min_cal, fecha_max_cal, freq="D")})
    cal["Anio"] = cal["Fecha"].dt.year
    cal["Trimestre"] = cal["Fecha"].dt.quarter
    cal["Mes"] = cal["Fecha"].dt.month
    cal["NombreMes"] = cal["Mes"].map(MESES)
    cal["MesCorto"] = cal["Mes"].map(MESES_CORTOS)
    cal["AnioMes"] = cal["Fecha"].dt.strftime("%Y-%m")
    cal["EtiquetaMes"] = cal.apply(lambda r: f"{r['MesCorto']} {r['Anio']}", axis=1)
    cal["OrdenAnioMes"] = cal["Anio"] * 100 + cal["Mes"]
    cal["SemanaISO"] = cal["Fecha"].dt.isocalendar().week.astype(int)
    cal["InicioSemana"] = cal["Fecha"] - pd.to_timedelta(cal["Fecha"].dt.weekday, unit="D")
    cal["Dia"] = cal["Fecha"].dt.day
    cal["NombreDia"] = cal["Fecha"].dt.dayofweek.map(DIAS)
    cal["EsFinSemana"] = cal["Fecha"].dt.dayofweek.isin([5, 6]).astype(int)
    cal["Periodo"] = cal.apply(lambda r: f"{r['Anio']}-T{r['Trimestre']}", axis=1)
    cal["EsMesCompleto"] = cal.apply(
        lambda r: 1 if (date(r["Anio"], r["Mes"], 1).replace(day=28) + pd.Timedelta(days=4)).replace(day=1) <= corte.replace(day=1) else 0,
        axis=1,
    )
    cal["FechaCorte"] = corte
    cal["DiasDesdeCorte"] = (corte - cal["Fecha"].dt.date).map(lambda d: d.days)
    cal["FechaKey"] = cal["Fecha"].dt.strftime("%Y%m%d").astype(int)
    cal_out = cal[[
        "Fecha", "Anio", "Trimestre", "Mes", "NombreMes", "MesCorto", "AnioMes", "EtiquetaMes",
        "OrdenAnioMes", "SemanaISO", "InicioSemana", "Dia", "NombreDia", "EsFinSemana", "Periodo",
        "EsMesCompleto", "FechaCorte", "DiasDesdeCorte", "FechaKey",
    ]].copy()
    cal_out["Fecha"] = cal_out["Fecha"].dt.strftime("%Y-%m-%d")
    cal_out["InicioSemana"] = cal_out["InicioSemana"].dt.strftime("%Y-%m-%d")
    cal_out["FechaCorte"] = cal_out["FechaCorte"].astype(str)
    cal_out.to_csv(OUT / "DIM_CALENDARIO.csv", index=False, encoding="utf-8")

    # FACT_INASISTENCIAS
    fact = df[[
        "InasistenciaID", "FechaInicio", "FechaFin", "FichaID", "AprendizID", "ProgramaID",
        "Instructor", "Horas", "DiasCubiertos", "HorasPorDia", "EsOutlierHoras",
        "JustificacionRaw", "categoria", "tipo", "confianza", "revision", "regla", "soporte",
        "EsRetardo", "EsAusencia", "EsJustificada", "EsNoJustificada", "EsSinInformacion",
    ]].copy()

    # Banderas a nivel aprendiz repetidas en el hecho para que los KPIs de riesgo
    # respeten cualquier filtro de la página (programa, ficha, mes, etc.).
    fact["EsReincidenteAprendiz"] = fact["AprendizID"].map(ap.set_index("AprendizID")["EsReincidente"]).fillna(0).astype(int)
    fact["EsReincidenteAltoAprendiz"] = fact["AprendizID"].map(ap.set_index("AprendizID")["EsReincidenteAlto"]).fillna(0).astype(int)
    fact["EsAlertaDesercionAprendiz"] = fact["AprendizID"].map(ap.set_index("AprendizID")["AlertaDesercion"]).fillna(0).astype(int)
    fact["NivelRiesgoAprendiz"] = fact["AprendizID"].map(ap.set_index("AprendizID")["NivelRiesgo"]).fillna("Bajo")
    fact["TieneDocumentoAprendiz"] = fact["AprendizID"].map(
        ap.set_index("AprendizID")["DocumentoEnmascarado"].ne("SIN DOCUMENTO").astype(int)
    ).fillna(0).astype(int)

    fact = fact.rename(columns={
        "InasistenciaID": "InasistenciaID", "FechaInicio": "Fecha", "FechaFin": "FechaFin",
        "Horas": "CantidadHoras", "DiasCubiertos": "DiasCubiertos", "HorasPorDia": "HorasPorDia",
        "EsOutlierHoras": "EsOutlierHoras", "JustificacionRaw": "JustificacionOriginal",
        "categoria": "CategoriaJustificacion", "tipo": "TipoJustificacion",
        "confianza": "ConfianzaClasificacion", "revision": "RequiereRevision",
        "regla": "ReglaClasificacion", "soporte": "TieneSoporte",
        "EsRetardo": "EsRetardo", "EsAusencia": "EsAusencia", "EsJustificada": "EsJustificada",
        "EsNoJustificada": "EsNoJustificada", "EsSinInformacion": "EsSinInformacion",
    })
    fact["Anio"] = pd.to_datetime(fact["Fecha"]).dt.year
    fact["Mes"] = pd.to_datetime(fact["Fecha"]).dt.month
    fact["Fecha"] = pd.to_datetime(fact["Fecha"]).dt.strftime("%Y-%m-%d")
    fact["FechaFin"] = pd.to_datetime(fact["FechaFin"]).dt.strftime("%Y-%m-%d")
    fact["HorasPorDia"] = fact["HorasPorDia"].round(2)
    fact = fact.sort_values(["Fecha", "FichaID", "AprendizID"]).reset_index(drop=True)
    fact.to_csv(OUT / "FACT_INASISTENCIAS.csv", index=False, encoding="utf-8")

    # ------------------------------------------------------------------
    # Resumen ETL / hallazgos
    # ------------------------------------------------------------------
    total_horas = int(fact["CantidadHoras"].sum())
    total_inas = len(fact)
    total_ap = fact["AprendizID"].nunique()
    total_fichas = fact["FichaID"].nunique()
    total_prog = fact["ProgramaID"].nunique()
    pct_horas_no_just = fact.loc[fact["EsNoJustificada"] == 1, "CantidadHoras"].sum() / max(total_horas, 1)
    pct_inas_no_just = (fact["EsNoJustificada"] == 1).mean()
    pct_just = (fact["EsJustificada"] == 1).mean()
    pct_sin_info = (fact["EsSinInformacion"] == 1).mean()

    por_mes = fact.groupby("Mes").agg(
        inasistencias=("InasistenciaID", "size"),
        horas=("CantidadHoras", "sum"),
        aprendices=("AprendizID", "nunique"),
    ).reset_index()
    por_mes["mes"] = por_mes["Mes"].map(MESES)
    por_mes["variacion_horas_pct"] = por_mes["horas"].pct_change().replace([float("inf"), float("-inf")], None) * 100

    top_fichas = ficha_out.head(10)[["FichaID", "IndiceRiesgoCorte", "NivelRiesgoCorte", "Horas", "Aprendices", "Inasistencias"]].to_dict(orient="records")
    top_programas = prog_out.head(10)[["NombrePrograma", "Horas", "Aprendices", "Inasistencias"]].to_dict(orient="records")

    fecha_descarga = datetime.fromtimestamp(RAW.stat().st_mtime).astimezone()
    resumen = {
        "fuente": str(RAW),
        "corte": str(corte),
        "ultima_descarga": fecha_descarga.isoformat(timespec="minutes"),
        "registros_origen": registros_origen,
        "registros_invalidos": n_invalidas,
        "duplicados_exactos": duplicados,
        "registros_validos": total_inas,
        "aprendices_unicos": total_ap,
        "fichas": total_fichas,
        "programas": total_prog,
        "horas_perdidas": total_horas,
        "pct_inasistencias_justificadas": round(pct_just * 100, 2),
        "pct_inasistencias_no_justificadas": round(pct_inas_no_just * 100, 2),
        "pct_inasistencias_sin_informacion": round(pct_sin_info * 100, 2),
        "pct_horas_no_justificadas": round(pct_horas_no_just * 100, 2),
        "retardos": int(fact["EsRetardo"].sum()),
        "horas_retardo": int(fact.loc[fact["EsRetardo"] == 1, "CantidadHoras"].sum()),
        "registros_outlier_horas": int(fact["EsOutlierHoras"].sum()),
        "registros_requieren_revision": int(fact["RequiereRevision"].sum()),
        "pct_registros_requieren_revision": round(fact["RequiereRevision"].mean() * 100, 2),
        "registros_con_soporte": int(fact["TieneSoporte"].sum()),
        "registros_sin_justificacion": int((fact["JustificacionOriginal"].fillna("") == "").sum()),
        "registros_no_clasificados": int((fact["TipoJustificacion"] == "No clasificado").sum()),
        "justificaciones_unicas": int(fact["JustificacionOriginal"].nunique()),
        "aprendices_reincidentes": int(ap["EsReincidente"].sum()),
        "aprendices_reincidentes_altos": int(ap["EsReincidenteAlto"].sum()),
        "aprendices_alerta_desercion": int(ap["AlertaDesercion"].sum()),
        "aprendices_alerta_texto": int((ap["TextoDesercion"] == 1).sum()),
        "aprendices_alerta_patron": int((ap["AlertaPorPatron"] == 1).sum()),
        "aprendices_riesgo_alto": int((ap["NivelRiesgo"] == "Alto").sum()),
        "fichas_alto_riesgo": int((ficha["NivelRiesgoCorte"] == "Alto").sum()),
        "fichas_evaluadas": int(ficha["MuestraSuficiente"].sum()),
        "fichas_muestra_baja": int((ficha["MuestraSuficiente"] == 0).sum()),
        "programas_alto_riesgo": int((prog["NivelRiesgoCorte"] == "Alto").sum()),
        "programas_evaluados": int(prog["MuestraSuficiente"].sum()),
        "programas_muestra_baja": int((prog["MuestraSuficiente"] == 0).sum()),
        "por_mes": por_mes.to_dict(orient="records"),
        "top_fichas": top_fichas,
        "top_programas": top_programas,
        "scoring": {
            "tipo": "Índice compuesto de percentiles (priorización relativa, no probabilidad)",
            "universo": "Fichas y programas con >= 5 aprendices y >= 100 horas",
            "pesos": {"intensidad_horas_aprendiz": 0.40, "frecuencia_inas_aprendiz": 0.25,
                      "pct_horas_no_justificadas": 0.20, "volumen_horas": 0.15},
            "cortes": {"bajo": "<45", "medio": "45-69.9", "alto": ">=70"},
            "aprendiz": {
                "formula": "70% faltas no justificadas (tope 20) + 30% horas (tope 100)",
                "cortes": {"bajo": "<45", "medio": "45-69.9", "alto": ">=70"},
            },
            "alerta_desercion": "Texto explícito de retiro/deserción o (última novedad <=45 días y >=10 faltas no justificadas y >=80 horas no justificadas)",
        },
        "calidad": {
            "jornada_cobertura_pct": 0.0,
            "modalidad_cobertura_pct": 0.0,
            "estado_academico_oficial": False,
            "matricula_total_oficial": False,
            "centro_costo_inferido": CENTRO_COSTO,
            "duplicados_metodo": "Duplicados exactos tras normalizar espacios, fechas y horas",
        },
    }

    resumen["top_programas_riesgo"] = (
        prog.sort_values("IndiceRiesgoCorte", ascending=False).head(10)
        [["NombrePrograma", "IndiceRiesgoCorte", "NivelRiesgoCorte", "Horas", "Inasistencias",
          "Aprendices", "PctHorasNoJust", "MuestraSuficiente"]]
        .round(2).to_dict(orient="records")
    )

    with open(OUT / "00_resumen_etl.json", "w", encoding="utf-8") as fh:
        json.dump(resumen, fh, ensure_ascii=False, indent=2, default=str)

    print("\nResumen:")
    print(json.dumps({k: resumen[k] for k in [
        "registros_origen", "duplicados_exactos", "registros_validos", "aprendices_unicos",
        "fichas", "programas", "horas_perdidas", "pct_horas_no_justificadas",
        "retardos", "registros_outlier_horas", "aprendices_reincidentes",
        "aprendices_alerta_desercion", "fichas_alto_riesgo", "programas_alto_riesgo",
    ]}, ensure_ascii=False, indent=2))

    print("\nClasificación de justificaciones:")
    print(fact.groupby(["CategoriaJustificacion", "TipoJustificacion"]).size().sort_values(ascending=False).to_string())

    print("\nCasos sin regla / revisión (top 30):")
    rev = fact[fact["RequiereRevision"] == 1]
    print(rev.groupby(["JustificacionOriginal", "CategoriaJustificacion", "TipoJustificacion"]).size().sort_values(ascending=False).head(30).to_string())

    print("\nDistribución de riesgo de fichas:")
    print(ficha["NivelRiesgoCorte"].value_counts().to_string())
    print("\nTop 10 fichas por índice de riesgo:")
    print(ficha_out.head(10)[["FichaID", "Horas", "Aprendices", "HorasPorAprendiz", "PctHorasNoJust", "IndiceRiesgoCorte", "NivelRiesgoCorte"]].to_string(index=False))


if __name__ == "__main__":
    main()
