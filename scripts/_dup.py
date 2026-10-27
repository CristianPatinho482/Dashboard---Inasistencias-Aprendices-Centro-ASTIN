# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path

base = Path(__file__).resolve().parents[1]
fa = pd.read_csv(base / "data/processed/FACT_INASISTENCIAS.csv", parse_dates=["Fecha", "FechaFin"])
d = fa[fa.InasistenciaID.duplicated(keep=False)].sort_values("InasistenciaID")
print(d.to_string())
