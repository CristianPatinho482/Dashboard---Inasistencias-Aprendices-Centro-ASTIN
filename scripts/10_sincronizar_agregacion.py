#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sincroniza la agregación compartida entre la API y el navegador.

La lógica canónica vive en api/src/shared/aggregate.js y se copia a
web/assets/aggregate.js para que la demostración local use exactamente las
mismas reglas que la API de Azure. Use --check en CI para detectar deriva.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "api" / "src" / "shared" / "aggregate.js"
TARGET = ROOT / "web" / "assets" / "aggregate.js"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Solo verifica que las copias coincidan.")
    args = parser.parse_args()

    if not SOURCE.exists():
        print(f"No se encontró la fuente: {SOURCE}", file=sys.stderr)
        return 2

    if args.check:
        if not TARGET.exists():
            print(f"Falta la copia del navegador: {TARGET}", file=sys.stderr)
            return 1
        if digest(SOURCE) != digest(TARGET):
            print("La agregación de la API y la del navegador están desincronizadas.", file=sys.stderr)
            print("Ejecute: python scripts/10_sincronizar_agregacion.py", file=sys.stderr)
            return 1
        print("Agregación sincronizada.")
        return 0

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE, TARGET)
    print(f"Agregación sincronizada: {TARGET}")
    print(f"SHA-256: {digest(TARGET)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
