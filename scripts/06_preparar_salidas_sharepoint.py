# -*- coding: utf-8 -*-
"""Copia solo salidas ETL autorizadas y elimina valores identificables antes de SharePoint."""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil

import pandas as pd

ARCHIVOS = (
    "DIM_CALENDARIO.csv",
    "DIM_APRENDIZ.csv",
    "DIM_FICHA.csv",
    "DIM_PROGRAMA.csv",
    "FACT_INASISTENCIAS.csv",
    "00_resumen_etl.json",
)
COLUMNAS_REDACTAR = {"DocumentoEnmascarado", "Iniciales", "NombreCompleto"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args()
    args.destination.mkdir(parents=True, exist_ok=True)
    for nombre in ARCHIVOS:
        origen = args.source / nombre
        if not origen.is_file():
            raise FileNotFoundError(f"Salida ETL requerida no encontrada: {origen}")
        destino = args.destination / nombre
        if nombre == "DIM_APRENDIZ.csv":
            df = pd.read_csv(origen, dtype=str, keep_default_na=False)
            for columna in COLUMNAS_REDACTAR.intersection(df.columns):
                df[columna] = ""
            df.to_csv(destino, index=False, encoding="utf-8")
        else:
            shutil.copy2(origen, destino)
    print(f"Salidas ETL preparadas en {args.destination}; no se copió DIM_APRENDIZ_PII.csv.")


if __name__ == "__main__":
    main()
