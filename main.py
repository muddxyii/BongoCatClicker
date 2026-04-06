import os
import sys
import ctypes

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

import json
import pydirectinput
import win32gui
import win32api
import time
import random
import threading
import keyboard
import tkinter as tk
from tkinter import font as tkfont
import cv2
import numpy as np
import mss

pydirectinput.PAUSE = 0

# ── CONFIG ──────────────────────────────────────────────────────────────────
BONGO_WINDOW_TITLE = "BongoCat"  # adjust if title differs in your language
WINDOW_TITLE = "Bongo Cat Manager"  # adjust if title differs in your language
TOGGLE_KEY = "F8"
INTERVAL_MIN = 0.005
INTERVAL_MAX = 0.01
HOLD_MIN = 0.008
HOLD_MAX = 0.015
DEBOUNCE = 0.4
TEMPLATE_THRESHOLD = 0.8
# ────────────────────────────────────────────────────────────────────────────

if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

REDEEM_ICONS = [
    os.path.join(BASE_DIR, "icons", "redeem-accessories-icon.png"),
    os.path.join(BASE_DIR, "icons", "redeem-emojis-icon.png"),
]
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")


def load_config():
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(data):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"[config] Failed to save: {e}")


KEYS = [
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "numpad0",
    "numpad1",
    "numpad2",
    "numpad3",
    "numpad4",
    "numpad5",
    "numpad6",
    "numpad7",
    "numpad8",
    "numpad9",
]

if TOGGLE_KEY.lower() in KEYS:
    KEYS.remove(TOGGLE_KEY.lower())
INPUTS = KEYS

running = False
lock = threading.Lock()
_last_toggle = 0.0
redeeming = False
status_label = None
btn_toggle = None
root = None
auto_press_enabled = None
auto_redeem_enabled = None
redeem_countdown_label = None


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


def press_inputs(inputs):
    try:
        for input_name in inputs:
            pydirectinput.keyDown(input_name)
        time.sleep(random.uniform(HOLD_MIN, HOLD_MAX))
        for input_name in inputs:
            pydirectinput.keyUp(input_name)
    except Exception as e:
        print(f"[press_inputs] Error: {e}")


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

        if auto_press_enabled and auto_press_enabled.get() and not redeeming:
            try:
                press_inputs(INPUTS)
            except Exception as e:
                print(f"[loop] Error: {e}")

        time.sleep(random.uniform(INTERVAL_MIN, INTERVAL_MAX))


def capture_bongo_window():
    hwnd = win32gui.FindWindow(None, BONGO_WINDOW_TITLE)
    if not hwnd or not win32gui.IsWindow(hwnd):
        return None, None
    rect = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = rect
    with mss.mss() as sct:
        monitor = {
            "top": top,
            "left": left,
            "width": right - left,
            "height": bottom - top,
        }
        img = sct.grab(monitor)
        return np.array(img), rect


def click_position(hwnd, x, y):
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.1)
    pydirectinput.click(x, y)


def find_and_click_icons():
    """Returns the number of icons successfully found and clicked."""
    hwnd = win32gui.FindWindow(None, BONGO_WINDOW_TITLE)
    if not hwnd or not win32gui.IsWindow(hwnd):
        print("[redeem] Bongo Cat window not found")
        return 0

    screenshot, window_rect = capture_bongo_window()
    if screenshot is None:
        return 0

    screenshot_bgr = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
    clicked = 0
    original_pos = win32api.GetCursorPos()

    for icon_path in REDEEM_ICONS:
        if not os.path.exists(icon_path):
            print(f"[redeem] Icon not found: {icon_path}")
            continue
        template = cv2.imread(icon_path)
        if template is None:
            print(f"[redeem] Failed to load icon: {icon_path}")
            continue
        result = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val >= TEMPLATE_THRESHOLD:
            h, w = template.shape[:2]
            cx = window_rect[0] + max_loc[0] + w // 2
            cy = window_rect[1] + max_loc[1] + h // 2
            click_position(hwnd, cx, cy)
            clicked += 1
            print(
                f"[redeem] Clicked {os.path.basename(icon_path)} (confidence: {max_val:.2f})"
            )
            time.sleep(0.5)
        else:
            print(
                f"[redeem] {os.path.basename(icon_path)} not found (confidence: {max_val:.2f})"
            )

    win32api.SetCursorPos(original_pos)
    return clicked


def update_redeem_countdown(text):
    if redeem_countdown_label and root:
        root.after(0, lambda: redeem_countdown_label.config(text=text))


def auto_redeem_loop():
    global redeeming
    next_redeem = 0.0  # 0 means search immediately
    while True:
        if not (auto_redeem_enabled and auto_redeem_enabled.get()):
            update_redeem_countdown("")
            next_redeem = 0.0
            time.sleep(1)
            continue

        with lock:
            is_running = running

        if not is_running:
            update_redeem_countdown("Waiting for start...")
            next_redeem = 0.0
            time.sleep(1)
            continue

        now = time.time()
        if next_redeem > now:
            remaining = next_redeem - now
            mins = int(remaining) // 60
            secs = int(remaining) % 60
            update_redeem_countdown(f"Redeem in: {mins:02d}:{secs:02d}")
            time.sleep(1)
            continue

        update_redeem_countdown("Searching...")
        redeeming = True
        time.sleep(0.1)
        clicked = find_and_click_icons()
        redeeming = False
        if clicked == len(REDEEM_ICONS):
            print("[redeem] Both icons clicked")
            next_redeem = time.time() + (30 * 60 + 5)
        time.sleep(5)


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
            set_status("Window not found", "#f5a97f")
            with lock:
                running = False
            return
        set_status("● Running", "#a6da95")
        btn_toggle.config(text="■ Stop  [" + TOGGLE_KEY + "]")
    else:
        set_status("● Stopped", "#ed8796")
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
    if running and not redeeming and event.widget == root:
        root.focus_force()


def build_gui():
    global \
        root, \
        status_label, \
        btn_toggle, \
        auto_press_enabled, \
        auto_redeem_enabled, \
        redeem_countdown_label

    # Catppuccin Macchiato
    C_BASE = "#24273a"
    C_SURFACE0 = "#363a4f"
    C_SURFACE1 = "#494d64"
    C_TEXT = "#cad3f5"
    C_SUBTEXT0 = "#a5adcb"
    C_SUBTEXT1 = "#b8c0e0"
    C_RED = "#ed8796"

    root = tk.Tk()
    root.title(WINDOW_TITLE)
    root.geometry("360x320")
    root.resizable(False, False)
    root.configure(bg=C_BASE)
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.attributes("-topmost", True)
    root.attributes("-alpha", 1.0)

    f_title = tkfont.Font(family="Segoe UI", size=15, weight="bold")
    f_status = tkfont.Font(family="Segoe UI", size=12)
    f_btn = tkfont.Font(family="Segoe UI", size=11)
    f_hint = tkfont.Font(family="Segoe UI", size=10)

    tk.Label(root, text="Bongo Cat Manager", font=f_title, bg=C_BASE, fg=C_TEXT).pack(
        pady=(24, 4)
    )

    status_label = tk.Label(root, text="● Stopped", font=f_status, bg=C_BASE, fg=C_RED)
    status_label.pack(pady=6)

    btn_toggle = tk.Button(
        root,
        text="▶ Start  [" + TOGGLE_KEY + "]",
        font=f_btn,
        bg=C_SURFACE0,
        fg=C_TEXT,
        activebackground=C_SURFACE1,
        activeforeground=C_TEXT,
        relief="flat",
        padx=20,
        pady=10,
        cursor="hand2",
        command=toggle_running,
    )
    btn_toggle.pack(pady=14)

    cfg = load_config()

    def on_setting_change(*_):
        save_config(
            {
                "auto_press": auto_press_enabled.get(),
                "auto_redeem": auto_redeem_enabled.get(),
            }
        )

    auto_press_enabled = tk.BooleanVar(value=cfg.get("auto_press", True))
    auto_press_enabled.trace_add("write", on_setting_change)
    tk.Checkbutton(
        root,
        text="Auto Press",
        variable=auto_press_enabled,
        font=f_btn,
        bg=C_BASE,
        fg=C_TEXT,
        activebackground=C_BASE,
        activeforeground=C_TEXT,
        selectcolor=C_SURFACE0,
        relief="flat",
        cursor="hand2",
    ).pack(pady=(0, 4))

    auto_redeem_enabled = tk.BooleanVar(value=cfg.get("auto_redeem", False))
    auto_redeem_enabled.trace_add("write", on_setting_change)
    tk.Checkbutton(
        root,
        text="Auto Redeem (every 30 min)",
        variable=auto_redeem_enabled,
        font=f_btn,
        bg=C_BASE,
        fg=C_TEXT,
        activebackground=C_BASE,
        activeforeground=C_TEXT,
        selectcolor=C_SURFACE0,
        relief="flat",
        cursor="hand2",
    ).pack(pady=(0, 4))

    redeem_countdown_label = tk.Label(
        root,
        text="",
        font=f_hint,
        bg=C_BASE,
        fg=C_SUBTEXT1,
    )
    redeem_countdown_label.pack(pady=2)

    bongo_status_label = tk.Label(
        root,
        text="",
        font=f_hint,
        bg=C_BASE,
        fg=C_SUBTEXT0,
    )
    bongo_status_label.pack(pady=(2, 12))

    def poll_bongo():
        if find_and_focus():
            bongo_status_label.config(text="● Bongo Cat detected", fg="#a6da95")
            btn_toggle.config(state="normal")
        else:
            bongo_status_label.config(text="● Bongo Cat not detected", fg="#ed8796")
            btn_toggle.config(state="disabled")
            with lock:
                was_running = running
            if was_running:
                toggle_running()
        root.after(1000, poll_bongo)

    poll_bongo()

    root.bind("<FocusOut>", on_focus_out)

    return root


if __name__ == "__main__":
    keyboard.on_press_key(TOGGLE_KEY, on_hotkey)
    threading.Thread(target=auto_press_loop, daemon=True).start()
    threading.Thread(target=auto_redeem_loop, daemon=True).start()
    root = build_gui()
    print("[INFO] " + TOGGLE_KEY + " = Start/Stop | Close window to exit")
    root.mainloop()
