# -*- coding: utf-8 -*-
from pywinauto import Application

app = Application(backend="uia").connect(process=10116, timeout=20)
win = app.top_window()

for c in win.descendants():
    try:
        r = c.rectangle()
    except Exception:
        continue
    if r.left >= 1140 and r.top <= 420 and r.top >= 370:
        print(c.element_info.control_type, repr(c.window_text()), r)
