# -*- coding: utf-8 -*-
import time

from pywinauto import Application

app = Application(backend="uia").connect(process=42444, timeout=20)
win = app.top_window()

view_tab = None
for t in win.descendants(control_type="TabItem"):
    if (t.window_text() or "") == "Ver":
        view_tab = t
        break

if view_tab is None:
    raise SystemExit("view tab not found")

view_tab.select()
time.sleep(2)

for b in win.descendants():
    try:
        text = b.window_text() or ""
        rect = b.rectangle()
        ctype = b.element_info.control_type
    except Exception:
        continue
    if text and rect.top < 220 and ctype in ("Button", "SplitButton", "ComboBox", "Text"):
        print(ctype, repr(text), rect)
