from pywinauto import Application
import time, sys

app = Application(backend="uia").connect(process=44296, timeout=20)
win = app.top_window()
btns = [b for b in win.descendants(control_type="Button") if b.window_text() == "Actualizar ahora"]
print("found", len(btns))
if btns:
    b = btns[-1] if len(btns) > 1 else btns[0]
    print("clicking", b.rectangle())
    b.click_input()
    print("clicked")
    time.sleep(3)
