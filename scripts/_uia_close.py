from pywinauto import Application
from pywinauto.keyboard import send_keys
import time, ctypes

app = Application(backend="uia").connect(process=44296, timeout=20)
win = app.top_window()
print("closing", win.window_text())
win.close()
time.sleep(2)
print("windows after close:", [w.window_text() for w in app.windows()])
# look for save confirmation dialog
for w in app.windows():
    try:
        print("WIN", repr(w.window_text()), w.rectangle())
        for b in w.descendants(control_type="Button"):
            print("  BTN", repr(b.window_text()), b.rectangle())
    except Exception as e:
        print("ERR", e)
