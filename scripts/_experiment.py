# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from pathlib import Path

base = Path(__file__).resolve().parents[1]
f = pd.read_csv(base / "data/processed/DIM_FICHA.csv")
a = pd.read_csv(base / "data/processed/DIM_APRENDIZ.csv")
p = pd.read_csv(base / "data/processed/DIM_PROGRAMA.csv")

f["HorasPorAprendiz"] = f["Horas"] / f["Aprendices"].clip(lower=1)
f["InasPorAprendiz"] = f["Inasistencias"] / f["Aprendices"].clip(lower=1)

def show(name, s):
    print(f"\n{name}")
    print(s.describe(percentiles=[.1, .25, .5, .75, .9]).round(1).to_string())
    print(pd.cut(s, [-0.01, 45, 70, 100.01], labels=["Bajo", "Medio", "Alto"]).value_counts().to_string())

# A: p90 caps
cap_h, cap_i, cap_v = f["HorasPorAprendiz"].quantile(.9), f["InasPorAprendiz"].quantile(.9), f["Horas"].quantile(.9)
sa = 40*(f["HorasPorAprendiz"]/cap_h).clip(upper=1)*100/100 + 25*(f["InasPorAprendiz"]/cap_i).clip(upper=1) + 20*f["PctHorasNoJust"].clip(0,1) + 15*(f["Horas"]/cap_v).clip(upper=1)
show("A p90 caps", sa)

# B: sqrt p90 caps
sb = 40*np.sqrt((f["HorasPorAprendiz"]/cap_h).clip(upper=1)) + 25*np.sqrt((f["InasPorAprendiz"]/cap_i).clip(upper=1)) + 20*f["PctHorasNoJust"].clip(0,1) + 15*np.sqrt((f["Horas"]/cap_v).clip(upper=1))
show("B sqrt p90", sb)

# C: percentile weighted
pc = lambda s: s.rank(pct=True, method="average")*100
sc = .40*pc(f["HorasPorAprendiz"]) + .25*pc(f["InasPorAprendiz"]) + .20*pc(f["PctHorasNoJust"]) + .15*pc(f["Horas"])
show("C percentiles", sc)

# D: percentile weighted, pct no just only among fichas with >=5 absent hours? keep
print("\ncorr components")
print(f[["HorasPorAprendiz","InasPorAprendiz","PctHorasNoJust","Horas"]].corr().round(2).to_string())

# Apprentice variants
cap_ah, cap_an = a["Horas"].quantile(.9), a["NoJustificadas"].quantile(.9)
ap1 = 60*(a["Horas"]/cap_ah).clip(upper=1) + 40*(a["NoJustificadas"]/cap_an).clip(upper=1)
show("AP p90 caps", ap1)
ap2 = 60*np.sqrt((a["Horas"]/cap_ah).clip(upper=1)) + 40*np.sqrt((a["NoJustificadas"]/cap_an).clip(upper=1))
show("AP sqrt p90", ap2)
ap3 = .5*pc(a["Horas"]) + .5*pc(a["NoJustificadas"])
show("AP percentiles", ap3)
print("\nAP old")
show("AP old", a["ScoreRiesgo"])
