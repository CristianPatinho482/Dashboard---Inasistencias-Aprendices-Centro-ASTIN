# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path

base = Path(__file__).resolve().parents[1]
a = pd.read_csv(base / "data/processed/DIM_APRENDIZ.csv")

for capn, caph in [(20, 100), (15, 80), (25, 120)]:
    s = 70 * (a["NoJustificadas"] / capn).clip(upper=1) + 30 * (a["Horas"] / caph).clip(upper=1)
    print(f"\ncap nojust={capn}, horas={caph}")
    print(s.describe(percentiles=[.25, .5, .75, .9]).round(1).to_string())
    print(pd.cut(s, [-0.01, 45, 70, 100.01], labels=["Bajo", "Medio", "Alto"]).value_counts().to_string())
