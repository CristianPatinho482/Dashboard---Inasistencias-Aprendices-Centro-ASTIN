from pywinauto import Application
import time

app = Application(backend="uia").connect(process=44296, timeout=20)
win = app.top_window()
btns = [b for b in win.descendants(control_type="Button") if b.window_text() == "Cerrar"]
print("close buttons", [(b.rectangle(), b.element_info.automation_id) for b in btns])
if btns:
    btns[0].click_input()
time.sleep(2)
print("process still?", end=" ")
try:
    print(app.is_process_running())
except Exception as e:
    print("err", e)
for w in app.windows():
    try:
        print("WIN", repr(w.window_text()), w.rectangle())
        for b in w.descendants(control_type="Button"):
            print("  BTN", repr(b.window_text()), b.rectangle())
    except Exception as e:
        print("ERR", e)
