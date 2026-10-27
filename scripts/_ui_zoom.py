# -*- coding: utf-8 -*-
import time

from pywinauto import Application

app = Application(backend="uia").connect(process=10116, timeout=20)
win = app.top_window()
win.set_focus()
time.sleep(1)

target = None
for b in win.descendants(control_type="Button"):
    text = b.window_text() or ""
    if "Nivel de zoom" in text:
        target = b
        break

if target is None:
    raise SystemExit("zoom button not found")

print("clicking", repr(target.window_text()), target.rectangle())
target.click_input()
time.sleep(2)

for c in win.descendants():
    try:
        text = c.window_text() or ""
    except Exception:
        continue
    if text and c.element_info.control_type in ("MenuItem", "ListItem", "Button", "Text"):
        try:
            r = c.rectangle()
        except Exception:
            continue
        if r.top > 900 and r.left > 1600:
            print(c.element_info.control_type, repr(text), r)
