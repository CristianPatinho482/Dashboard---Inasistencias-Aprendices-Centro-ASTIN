# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path

base = Path(__file__).resolve().parents[1]
f = pd.read_csv(base / "data/processed/DIM_FICHA.csv")
a = pd.read_csv(base / "data/processed/DIM_APRENDIZ.csv")
p = pd.read_csv(base / "data/processed/DIM_PROGRAMA.csv")

for col in ["HorasPorAprendiz", "InasPorAprendiz", "PctHorasNoJust", "Horas", "Aprendices"]:
    print("\nFICHA", col)
    print(f[col].describe(percentiles=[.25, .5, .75, .8, .9, .95, .99]).round(2).to_string())

for col in ["Horas", "HorasNoJustificadas", "NoJustificadas", "Inasistencias"]:
    print("\nAPRENDIZ", col)
    print(a[col].describe(percentiles=[.25, .5, .75, .8, .9, .95, .99]).round(2).to_string())

p["HorasPorAprendiz"] = p["Horas"] / p["Aprendices"].clip(lower=1)
p["InasPorAprendiz"] = p["Inasistencias"] / p["Aprendices"].clip(lower=1)
print("\nPROGRAMA metricas")
print(p[["HorasPorAprendiz", "InasPorAprendiz", "Horas"]].describe(percentiles=[.5, .75, .9, .95, .99]).round(2).to_string())

print("\nFicha score distribution")
print(f["IndiceRiesgoCorte"].describe().round(1).to_string())
print(f["NivelRiesgoCorte"].value_counts())
