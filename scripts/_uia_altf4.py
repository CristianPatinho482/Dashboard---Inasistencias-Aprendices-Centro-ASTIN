from pywinauto import Application
from pywinauto.keyboard import send_keys
import time, ctypes

app = Application(backend="uia").connect(process=44296, timeout=20)
win = app.top_window()
ctypes.windll.user32.SetForegroundWindow(528040)
time.sleep(0.5)
send_keys('%{F4}')
time.sleep(3)
print("running", app.is_process_running())
for w in app.windows():
    try:
        print("WIN", repr(w.window_text()), w.rectangle())
        for b in w.descendants(control_type="Button")[:30]:
            print("  BTN", repr(b.window_text()), b.rectangle())
    except Exception as e:
        print("ERR", e)
