from pywinauto import Application

app = Application(backend="uia").connect(process=44296, timeout=20)
for w in app.windows():
    try:
        print(repr(w.window_text()), w.element_info.control_type, w.rectangle(), w.element_info.automation_id)
    except Exception as e:
        print("ERR", e)
