try:
    import webview
except ImportError:
    webview = None
from .infra.logger import get_logger
logger = get_logger(__name__)
class Api:
    def __init__(self, settings, on_change_system, on_toggle_debug):
        self.settings = settings; self._set_sys = on_change_system; self._set_dbg = on_toggle_debug
    def change_system(self, system: str): self._set_sys(system); return {"ok": True, "system": system}
    def toggle_debug(self, enabled: bool): self._set_dbg(bool(enabled)); return {"ok": True, "debug": bool(enabled)}
def start_ui(settings, on_change_system, on_toggle_debug):
    if webview is None:
        logger.info("pywebview nicht installiert – UI wird nicht gestartet (CLI/Hotkeys aktiv)."); return
    api = Api(settings, on_change_system, on_toggle_debug)
    win = webview.create_window("EasyPeasyScanny", html="<h3>EasyPeasyScanny</h3>", js_api=api, width=360, height=200)
    webview.start(private_mode=True, debug=False)
