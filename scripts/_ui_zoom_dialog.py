# -*- coding: utf-8 -*-
import time

from pywinauto import Application

app = Application(backend="uia").connect(process=42444, timeout=20)
win = app.top_window()

target = None
for b in win.descendants(control_type="Button"):
    if "Nivel de zoom" in (b.window_text() or ""):
        target = b
        break

if target is None:
    raise SystemExit("zoom button not found")

print("invoking", target.rectangle())
target.invoke()
time.sleep(2)

for c in win.descendants():
    try:
        text = c.window_text() or ""
        rect = c.rectangle()
    except Exception:
        continue
    if text and rect.top > 800:
        print(c.element_info.control_type, repr(text), rect)
