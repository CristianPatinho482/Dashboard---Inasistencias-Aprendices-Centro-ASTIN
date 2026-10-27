# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path

base = Path(__file__).resolve().parents[1]
p = base / "data/processed"
cal = pd.read_csv(p / "DIM_CALENDARIO.csv", parse_dates=["Fecha"])
ap = pd.read_csv(p / "DIM_APRENDIZ.csv")
fi = pd.read_csv(p / "DIM_FICHA.csv")
pr = pd.read_csv(p / "DIM_PROGRAMA.csv")
fa = pd.read_csv(p / "FACT_INASISTENCIAS.csv", parse_dates=["Fecha", "FechaFin"])

print("Shapes", cal.shape, ap.shape, fi.shape, pr.shape, fa.shape)
print("\nUnique keys", ap.AprendizID.is_unique, fi.FichaID.is_unique, pr.ProgramaID.is_unique, cal.Fecha.is_unique)
print("Fact duplicate IDs", fa.InasistenciaID.duplicated().sum())
print("Fact nulls", fa.isna().sum()[fa.isna().sum() > 0].to_dict())
print("\nFK coverage:")
print("  fecha", fa.Fecha.isin(cal.Fecha).mean())
print("  aprendiz", fa.AprendizID.isin(ap.AprendizID).mean())
print("  ficha", fa.FichaID.isin(fi.FichaID).mean())
print("  programa", fa.ProgramaID.isin(pr.ProgramaID).mean())
print("  ficha.programa", fi.ProgramaID.isin(pr.ProgramaID).mean())
print("\nFechas", fa.Fecha.min(), fa.Fecha.max())
print("Calendar months", cal.Fecha.dt.month.nunique(), "EsMesCompleto")
print(cal.groupby(cal.Fecha.dt.month)["EsMesCompleto"].first().to_dict())
print("\nProgramas por linea")
print(pr.groupby(["LineaFormacion", "TipoFormacion"]).size().to_string())
print("\nProgram risk")
print(pr[["NombrePrograma", "MuestraSuficiente", "IndiceRiesgoCorte", "NivelRiesgoCorte"]].sort_values("IndiceRiesgoCorte", ascending=False).head(12).to_string(index=False))
print("\nApprentice risk")
print(ap.NivelRiesgo.value_counts().to_string())
print(ap.EstadoAsistencia.value_counts().to_string())
print("Alertas", ap.AlertaDesercion.sum(), ap.MotivoAlertaDesercion.value_counts().to_dict())
print("Reincidentes", ap.EsReincidente.sum(), "altos", ap.EsReincidenteAlto.sum())
print("\nHours by category")
print(fa.groupby("CategoriaJustificacion").agg(n=("InasistenciaID", "size"), horas=("CantidadHoras", "sum")).to_string())
print("\nRetardos", fa.EsRetardo.sum(), "ausencias", fa.EsAusencia.sum())
print("\nOutliers top")
print(fa[fa.EsOutlierHoras == 1].nlargest(8, "CantidadHoras")[["FichaID", "CantidadHoras", "DiasCubiertos", "HorasPorDia", "Fecha", "JustificacionOriginal"]].to_string(index=False))
