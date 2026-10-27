# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path

base = Path(__file__).resolve().parents[1]
f = pd.read_csv(base / "data/processed/DIM_FICHA.csv")
f["HorasPorAprendiz"] = f["Horas"] / f["Aprendices"].clip(lower=1)
f["InasPorAprendiz"] = f["Inasistencias"] / f["Aprendices"].clip(lower=1)
mask = (f["Aprendices"] >= 5) & (f["Horas"] >= 100)
print("elegibles", mask.sum(), "de", len(f))
pc = lambda s: s.where(mask).rank(pct=True, method="average") * 100
f["score"] = .40 * pc(f["HorasPorAprendiz"]) + .25 * pc(f["InasPorAprendiz"]) + .20 * pc(f["PctHorasNoJust"]) + .15 * pc(f["Horas"])
f["nivel"] = pd.cut(f["score"], [-0.01, 45, 70, 100.01], labels=["Bajo", "Medio", "Alto"]).astype(str)
print(f.loc[mask, "nivel"].value_counts().to_string())
print(f.loc[mask].sort_values("score", ascending=False).head(20)[["FichaID", "Horas", "Aprendices", "HorasPorAprendiz", "InasPorAprendiz", "PctHorasNoJust", "score", "nivel"]].round(2).to_string(index=False))
print("muestra baja", (~mask).sum())
