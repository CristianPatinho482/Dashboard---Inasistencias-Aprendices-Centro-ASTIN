from pywinauto import Application

app = Application(backend="uia").connect(process=44296, timeout=20)
win = app.top_window()
for ctype in ("Button", "Hyperlink", "MenuItem", "TabItem"):
    try:
        elems = win.descendants(control_type=ctype)
    except Exception as e:
        print("ERR", ctype, e)
        continue
    print(f"--- {ctype}: {len(elems)}")
    for e in elems[:80]:
        try:
            name = e.window_text()
            if name:
                print(repr(name), e.rectangle(), e.element_info.automation_id)
        except Exception:
            pass
