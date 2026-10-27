# -*- coding: utf-8 -*-
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image
from pywinauto import Application, mouse

ROOT = Path(r"C:\Users\capatino\Documents\Inasistencias Sofía Plus")
PREVIEW = ROOT / "preview"
TEMP = Path(r"C:\Users\capatino\AppData\Local\Temp\opencode")
PREVIEW.mkdir(exist_ok=True)

PAGES = [
    ("00", "00_inicio"),
    ("01", "01_caracterizacion"),
    ("02", "02_fichas_programas"),
    ("03", "03_analisis_detallado"),
    ("04", "04_calidad_datos"),
]

app = Application(backend="uia").connect(process=int(sys.argv[1]) if len(sys.argv) > 1 else 10116, timeout=20)
win = app.top_window()
win.set_focus()
time.sleep(1)

for prefix, slug in PAGES:
    tab = None
    for t in win.descendants(control_type="TabItem"):
        if (t.window_text() or "").startswith(prefix + " "):
            tab = t
            break
    if tab is None:
        raise SystemExit(f"tab {prefix} not found")
    tab.select()
    time.sleep(4)
    mouse.move(coords=(10, 10))
    time.sleep(1)

    # Clear any object selection so no resize handles/scrollbars appear in the capture.
    try:
        from pywinauto.keyboard import send_keys

        win.set_focus()
        send_keys("{ESC}{ESC}")
        time.sleep(1)
    except Exception:
        pass

    raw = TEMP / f"capture_{prefix}.png"
    subprocess.run(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts" / "_capture_window.ps1"),
            "-ProcessId",
            str(app.process),
            "-OutFile",
            str(raw),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    im = Image.open(raw).convert("RGB")
    px = im.load()
    w, h = im.size

    xs = []
    ys = []
    for y in range(120, h - 40):
        for x in range(0, 340):
            r, g, b = px[x, y]
            if abs(r - 0) <= 4 and abs(g - 48) <= 4 and abs(b - 77) <= 5:
                xs.append(x)
                ys.append(y)

    if not xs:
        raise SystemExit(f"no navy rail found on page {prefix}")

    from collections import Counter

    cx = Counter(xs)
    cy = Counter(ys)
    rail_cols = [x for x, count in cx.items() if count > 250]
    rail_rows = [y for y, count in cy.items() if count > 100]
    left = min(rail_cols)
    right = max(rail_cols)
    top = min(rail_rows)
    bottom = max(rail_rows)
    scale = (right - left + 1) / 200.0

    box = (
        left,
        top,
        round(left + 1280 * scale),
        round(top + 720 * scale),
    )
    page = im.crop(box)
    if page.size != (1280, 720):
        page = page.resize((1280, 720), Image.LANCZOS)
    out = PREVIEW / f"{slug}.png"
    page.save(out)
    print(f"{prefix}: rail=({left},{top},{right},{bottom}) scale={scale:.3f} crop={box} -> {out.name}")
