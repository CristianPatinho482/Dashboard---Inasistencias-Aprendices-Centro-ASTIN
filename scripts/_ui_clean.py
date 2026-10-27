# -*- coding: utf-8 -*-
import time

from pywinauto import Application

app = Application(backend="uia").connect(process=10116, timeout=20)
win = app.top_window()

print("window", win.rectangle())

buttons = win.descendants(control_type="Button")
for b in buttons:
    text = b.window_text() or ""
    if any(key in text for key in ("Ajustar", "Contraer", "Filtros", "Visualizaciones", "Datos")):
        try:
            print(repr(text), b.rectangle())
        except Exception as exc:
            print(repr(text), "rect-error", exc)
