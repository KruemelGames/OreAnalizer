try:
    import webview
except ImportError:
    webview = None
from ..infra.logger import get_logger
logger = get_logger(__name__)
class Overlays:
    def __init__(self):
        self._info_win = None
        self._price_win = None
    def show_info(self, payload: dict):
        if webview is None:
            logger.info("[Overlay] INFO: %s", payload)
            return
        html = f"""<html><body style='font-family:sans-serif'>
            <h3>Signal: {payload.get('signal','?')}</h3>
            <div>Rock: {payload.get('rock')}</div>
            <pre style='white-space:pre-wrap'>{payload}</pre>
        </body></html>"""
        if self._info_win is None:
            self._info_win = webview.create_window("Info", html=html, width=420, height=300)
            webview.start(private_mode=True, debug=False)
        else:
            self._info_win.load_html(html)
    def toggle_prices(self, html_content: str = "<h3>Mineable Ore Prices</h3>"):
        if webview is None:
            logger.info("[Overlay] PRICE TOGGLE")
            return
        if self._price_win is None:
            self._price_win = webview.create_window("Prices", html=html_content, width=480, height=640)
            webview.start(private_mode=True, debug=False)
        else:
            try:
                self._price_win.destroy(); self._price_win=None
            except Exception:
                self._price_win=None
