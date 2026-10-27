# -*- coding: utf-8 -*-
import time

from pywinauto import Application

app = Application(backend="uia").connect(process=10116, timeout=20)
win = app.top_window()

target = None
for b in win.descendants(control_type="Button"):
    text = b.window_text() or ""
    if text.startswith("Ajustar a la"):
        target = b
        break

if target is None:
    raise SystemExit("fit button not found")

print("invoking", repr(target.window_text()), target.rectangle())
target.invoke()
time.sleep(3)
print("done")
