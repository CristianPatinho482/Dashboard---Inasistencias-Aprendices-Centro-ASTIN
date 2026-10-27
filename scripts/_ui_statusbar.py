# -*- coding: utf-8 -*-
from pywinauto import Application

app = Application(backend="uia").connect(process=10116, timeout=20)
win = app.top_window()

for c in win.descendants():
    try:
        r = c.rectangle()
    except Exception:
        continue
    if r.top >= 1030 and r.left <= 250:
        print(c.element_info.control_type, repr(c.window_text()), r)
