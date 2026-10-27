from pywinauto import Application
import time

app = Application(backend="uia").connect(process=44296, timeout=20)
win = app.window(handle=528040) if False else app.top_window()
print("TITLE:", win.window_text())
print("RECT:", win.rectangle())

def walk(ctrl, depth=0, maxdepth=4):
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
        except Exception:
            continue
        if name and ("actual" in name.lower() or "refresh" in name.lower() or "datos" in name.lower() or "modelo" in name.lower()):
            print("  " * depth + f"[{ctype}] {name!r} rect={ch.rectangle()}")
        walk(ch, depth + 1, maxdepth)

walk(win, 0, 5)
