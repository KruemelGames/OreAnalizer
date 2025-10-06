# Extracted hotkey utilities from ui/webapp.py
from typing import Callable, Optional

# === Migrated Hotkey Blocks ===
def run_webapp(analyzer, title: str):
    if webview is None:
        print("pywebview nicht installiert – CLI-Fallback aktiv.")
        print("Beispielscan:", analyzer.analyze_scan({"Quantanium": 0.4, "Inert": 0.6}))
        return
    api = Api(analyzer)
    window = webview.create_window(title, html="<h1>EasyPeasyScanny</h1>", js_api=api)
    webview.start(debug=False)


# === Migrated from big file: UI/Webview ===

# --- block 1 ---
import json
import os
import math
from datetime import datetime
import threading
import time

# Webview für moderne UI
try:
    import webview

    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False
    print("[ERROR] webview nicht installiert! Installiere mit: pip install pywebview")

# Für globale Hotkeys (Gaming-Modus)
try:
    from pynput import keyboard

    GLOBAL_HOTKEYS_AVAILABLE = True
except ImportError:
    GLOBAL_HOTKEYS_AVAILABLE = False
    print("[INFO] pynput nicht installiert - Gaming-Modus nicht verfügbar")

# --- block 2 ---