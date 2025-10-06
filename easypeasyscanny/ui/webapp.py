try:
    import webview  # pywebview optional
except ImportError:
    webview = None
from . import overlay as overlay_mod  # Overlay utilities extracted
from ..infra import hotkeys as hotkeys_mod  # Hotkey utilities extracted
class Api:
    def __init__(self, analyzer):
        self.analyzer = analyzer

    def change_system(self, new_system: str):
        self.analyzer.switch_system(new_system)
        return {"success": True, "system": new_system}

    def submit_scan(self, composition: dict):
        res = self.analyzer.analyze_scan(composition)
        return {"success": True, "score": res.score, "timestamp": res.timestamp}

def main():
    if not WEBVIEW_AVAILABLE:
        return

    analyzer = StarCitizenMiningAnalyzer()
    webview.start(debug=False)

    try:
        analyzer.api.save_config()
        analyzer.api.hide_overlay()
        if analyzer.api.global_listener:
            analyzer.api.global_listener.stop()
    except Exception as e:
        print(f"[WARNING] Cleanup fehlgeschlagen: {e}")


if __name__ == "__main__":
    main()


# --- Lightweight wrapper for project entrypoint ---
def run_webapp(analyzer, title: str):
    """Minimal UI launcher used by main.py.
    Falls pywebview fehlt, läuft ein CLI-Fallback; ansonsten ein einfaches Fenster mit API.
    """
    if webview is None:
        print("pywebview nicht installiert – CLI-Fallback aktiv.")
        try:
            sample = analyzer.analyze_scan({"Quantanium": 0.4, "Inert": 0.6})
            print("Beispielscan:", sample)
        except Exception as e:
            print("[ERROR] Analyzer-Aufruf fehlgeschlagen:", e)
        return

    api = Api(analyzer)
    window = webview.create_window(title, html="<h1>EasyPeasyScanny</h1>", js_api=api)
    webview.start(debug=False)
