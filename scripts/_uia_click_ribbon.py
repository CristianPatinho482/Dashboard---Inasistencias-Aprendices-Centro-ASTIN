from pywinauto import Application
from pywinauto import mouse
import ctypes, time

app = Application(backend="uia").connect(process=44296, timeout=20)
win = app.top_window()
ctypes.windll.user32.SetForegroundWindow(528040)
time.sleep(0.5)
btn = win.child_window(title="Actualizar", control_type="Button")
print("buttons:", len(win.descendants(title="Actualizar", control_type="Button")))
for b in win.descendants(title="Actualizar", control_type="Button"):
    print(b.rectangle(), b.is_enabled(), b.element_info.automation_id)
    try:
        b.set_focus()
    except Exception as e:
        print("focus err", e)
    b.click_input()
    time.sleep(1)
    break
time.sleep(5)
print("windows:", [(w.window_text(), w.rectangle()) for w in app.windows()])
