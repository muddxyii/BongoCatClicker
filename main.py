import pydirectinput
import win32gui
import win32con
import time
import random
import threading
import keyboard
import tkinter as tk
from tkinter import font as tkfont

pydirectinput.PAUSE = 0

# ── CONFIG ──────────────────────────────────────────────────────────────────
BONGO_WINDOW_TITLE = "BongoCat" # adjust if title differs in your language
WINDOW_TITLE = "Bongo Cat Clicker"   # adjust if title differs in your language
TOGGLE_KEY   = "P"
INTERVAL_MIN = 0.02
INTERVAL_MAX = 0.03
HOLD_MIN     = 0.03
HOLD_MAX     = 0.04
DEBOUNCE     = 0.4
# ────────────────────────────────────────────────────────────────────────────
KEYS = [
    'a','b','c','d','e','g','h','i','j','k','l','m',
    'n','o','p','q','r','s','t','u','v','w','x','y',
    'z','0','1','2','3','4','5','6','7','8','9'
]

if TOGGLE_KEY.lower() in KEYS:
    KEYS.remove(TOGGLE_KEY.lower())

running      = False
lock         = threading.Lock()
_last_toggle = 0.0
status_label = None
btn_toggle   = None
root         = None

def find_and_focus():
    hwnd = win32gui.FindWindow(None, BONGO_WINDOW_TITLE)
    if hwnd and win32gui.IsWindow(hwnd):
        return True
    return False

def press_key(key):
    try:
        pydirectinput.keyDown(key)
        time.sleep(random.uniform(HOLD_MIN, HOLD_MAX))
        pydirectinput.keyUp(key)
    except Exception as e:
        print(f"[press] Error on '{key}': {e}")

def auto_press_loop():
    global running
    last_focus = 0.0
    while True:
        with lock:
            is_running = running

        if not is_running:
            time.sleep(0.05)
            continue

        # check if Bongo Cat is still running every 10 seconds
        now = time.time()
        if now - last_focus > 10.0:
            find_and_focus()
            last_focus = now

        try:
            press_key(random.choice(KEYS))
        except Exception as e:
            print(f"[loop] Error: {e}")

        time.sleep(random.uniform(INTERVAL_MIN, INTERVAL_MAX))

def set_status(text, color):
    if status_label and root:
        root.after(0, lambda: status_label.config(text=text, fg=color))

def toggle_running():
    global running, _last_toggle
    now = time.time()
    if now - _last_toggle < DEBOUNCE:
        return
    _last_toggle = now

    with lock:
        running = not running
        state = running

    if state:
        if not find_and_focus():
            set_status("Window not found", "#ffaa00")
            with lock:
                running = False
            return
        set_status("● Running", "#00ff88")
        btn_toggle.config(text="■ Stop  [" + TOGGLE_KEY + "]")
    else:
        set_status("● Stopped", "#ff4444")
        btn_toggle.config(text="▶ Start  [" + TOGGLE_KEY + "]")

def on_hotkey(event):
    root.focus_force()
    toggle_running()

def on_close():
    global running
    with lock:
        running = False
    root.destroy()

def on_focus_out(event):
    global running
    if running and event.widget == root:
        root.focus_force()


def build_gui():
    global root, status_label, btn_toggle

    root = tk.Tk()
    root.title(WINDOW_TITLE)
    root.geometry("280x160")
    root.resizable(False, False)
    root.configure(bg="#1e1e2e")
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.attributes('-topmost', True)
    root.attributes('-alpha', 0.95)

    f_title  = tkfont.Font(family="Segoe UI", size=13, weight="bold")
    f_status = tkfont.Font(family="Segoe UI", size=11)
    f_btn    = tkfont.Font(family="Segoe UI", size=10)
    f_hint   = tkfont.Font(family="Segoe UI", size=8)

    tk.Label(root, text="Bongo Cat Clicker",
             font=f_title, bg="#1e1e2e", fg="#cdd6f4").pack(pady=(14, 2))

    status_label = tk.Label(root, text="● Stopped",
                             font=f_status, bg="#1e1e2e", fg="#ff4444")
    status_label.pack(pady=2)

    btn_toggle = tk.Button(
        root, text="▶ Start  [" + TOGGLE_KEY + "]", font=f_btn,
        bg="#313244", fg="#cdd6f4", activebackground="#45475a",
        relief="flat", padx=12, pady=6, cursor="hand2",
        command=toggle_running
    )
    btn_toggle.pack(pady=10)

    tk.Label(root, text="Bongo Cat must be open to start",
             font=f_hint, bg="#1e1e2e", fg="#6c7086").pack()
    # root.bind("<FocusIn>"8, on_focus_in)
    root.bind("<FocusOut>", on_focus_out)

    return root

if __name__ == "__main__":
    keyboard.on_press_key(TOGGLE_KEY, on_hotkey)
    threading.Thread(target=auto_press_loop, daemon=True).start()
    root = build_gui()
    print("[INFO] " + TOGGLE_KEY + " = Start/Stop | Close window to exit")
    root.mainloop()