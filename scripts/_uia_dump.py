from pywinauto import Application

app = Application(backend="uia").connect(process=44296, timeout=20)
win = app.top_window()
print("TITLE:", win.window_text())

def walk(ctrl, depth=0, maxdepth=5):
    if depth > maxdepth:
        return
    try:
        children = ctrl.children()
    except Exception:
        return
    for ch in children:
        try:
            name = ch.window_text()
            ctype = ch.element_info.control_type
            auto = ch.element_info.automation_id
        except Exception:
            continue
        print("  " * depth + f"[{ctype}] name={name!r} auto={auto!r}")
        walk(ch, depth + 1, maxdepth)

walk(win, 0, 4)
