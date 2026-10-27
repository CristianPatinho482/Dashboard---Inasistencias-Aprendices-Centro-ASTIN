# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from pathlib import Path

base = Path(__file__).resolve().parents[1]
a = pd.read_csv(base / "data/processed/DIM_APRENDIZ.csv")
f = pd.read_csv(base / "data/processed/DIM_FICHA.csv")
p = pd.read_csv(base / "data/processed/DIM_PROGRAMA.csv")
fact = pd.read_csv(base/"data/processed/FACT_INASISTENCIAS.csv")

texto = (fact["TipoJustificacion"] == "Deserción / retiro").groupby(fact["AprendizID"]).max()
a["TextoDesercion"] = a["AprendizID"].map(texto).fillna(False).astype(int)

crit = [
 ("text", a["TextoDesercion"] == 1),
 ("text+recent45+nj3+i4", (a["TextoDesercion"]==1) | ((a["DiasDesdeUltimaNovedad"]<=45)&(a["NoJustificadas"]>=3)&(a["Inasistencias"]>=4))),
 ("text+recent30+nj5+h30", (a["TextoDesercion"]==1) | ((a["DiasDesdeUltimaNovedad"]<=30)&(a["NoJustificadas"]>=5)&(a["HorasNoJustificadas"]>=30))),
 ("text+recent30+nj8+h60", (a["TextoDesercion"]==1) | ((a["DiasDesdeUltimaNovedad"]<=30)&(a["NoJustificadas"]>=8)&(a["HorasNoJustificadas"]>=60))),
 ("text+recent45+nj10+h80", (a["TextoDesercion"]==1) | ((a["DiasDesdeUltimaNovedad"]<=45)&(a["NoJustificadas"]>=10)&(a["HorasNoJustificadas"]>=80))),
 ("text+recent60+nj10+h80", (a["TextoDesercion"]==1) | ((a["DiasDesdeUltimaNovedad"]<=60)&(a["NoJustificadas"]>=10)&(a["HorasNoJustificadas"]>=80))),
]
for n,c in crit:
    print(f"{n}: {int(c.sum())}")

print("\nReincidencia thresholds")
for k in [3,4,5,6,8,10,12,15,20]:
    print(k, int((a["Inasistencias"]>=k).sum()))

pc = lambda s: s.rank(pct=True, method="average")*100
print("\nTop fichas score percentiles")
f["HorasPorAprendiz"] = f["Horas"]/f["Aprendices"].clip(lower=1)
f["InasPorAprendiz"] = f["Inasistencias"]/f["Aprendices"].clip(lower=1)
f["score"] = .40*pc(f["HorasPorAprendiz"]) + .25*pc(f["InasPorAprendiz"]) + .20*pc(f["PctHorasNoJust"]) + .15*pc(f["Horas"])
f["nivel"] = pd.cut(f["score"], [-0.01,45,70,100.01], labels=["Bajo","Medio","Alto"]).astype(str)
print(f.sort_values("score",ascending=False).head(15)[["FichaID","Horas","Aprendices","HorasPorAprendiz","InasPorAprendiz","PctHorasNoJust","score","nivel"]].round(2).to_string(index=False))
print(f["nivel"].value_counts().to_string())

print("\nTop programas score percentiles")
p["HorasPorAprendiz"] = p["Horas"]/p["Aprendices"].clip(lower=1)
p["InasPorAprendiz"] = p["Inasistencias"]/p["Aprendices"].clip(lower=1)
g = fact.groupby("ProgramaID").apply(lambda d: pd.Series({"PctNJ": d.loc[d["EsNoJustificada"]==1,"CantidadHoras"].sum()/max(d["CantidadHoras"].sum(),1)}), include_groups=False)
p = p.merge(g, left_on="ProgramaID", right_index=True, how="left")
p["score"] = .40*pc(p["HorasPorAprendiz"]) + .25*pc(p["InasPorAprendiz"]) + .20*pc(p["PctNJ"]) + .15*pc(p["Horas"])
p["nivel"] = pd.cut(p["score"], [-0.01,45,70,100.01], labels=["Bajo","Medio","Alto"]).astype(str)
print(p.sort_values("score",ascending=False)[["NombrePrograma","Horas","Aprendices","HorasPorAprendiz","InasPorAprendiz","PctNJ","score","nivel"]].round(2).to_string(index=False))
print(p["nivel"].value_counts().to_string())
