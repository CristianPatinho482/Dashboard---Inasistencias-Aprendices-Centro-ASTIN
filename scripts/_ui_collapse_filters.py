# -*- coding: utf-8 -*-
import time

from pywinauto import Application

app = Application(backend="uia").connect(process=10116, timeout=20)
win = app.top_window()
win.set_focus()
time.sleep(1)

for b in win.descendants(control_type="Button"):
    text = b.window_text() or ""
    if text.startswith("Contrae o expande"):
        print("clicking", b.rectangle())
        b.click_input()
        time.sleep(3)
        break
print("done")
