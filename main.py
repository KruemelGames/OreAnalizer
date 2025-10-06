import time, json
from easypeasyscanny.config import load_settings, save_settings
from easypeasyscanny.infra.logger import get_logger, set_level
from easypeasyscanny.rocks.store import RocksRepo
from easypeasyscanny.scans.store import ScansStore
from easypeasyscanny.scans.analyzer import MiningAnalyzer
from easypeasyscanny.ui.overlay import Overlays
from easypeasyscanny.infra.hotkeys import NumpadListener, STATE
from easypeasyscanny.ui.webapp import start_ui

logger = get_logger(__name__)

def main():
    settings = load_settings(); set_level(settings.debug_logging)
    logger.info("App-Start (system=%s, debug=%s)", settings.selected_system, settings.debug_logging)
    rocks = RocksRepo(lambda: settings.selected_system)
    scans = ScansStore()
    analyzer = MiningAnalyzer(rocks, scans, settings)
    overlays = Overlays()

    def on_plus(val: int):
        if val<=0: logger.info("Leerer/ungueltiger Wert – ignoriert."); return
        payload = analyzer.analyze_and_store(val)
        overlays.show_info(payload)

    def on_minus():
        overlays.toggle_prices(prices=[{"name":"Quantanium","raw":88,"refined":110},{"name":"Bexalite","raw":54,"refined":72}])

    listener = NumpadListener(on_number=lambda n: None, on_plus=on_plus, on_minus=on_minus)
    listener.start()

    # Start UI
    start_ui(settings, analyzer, scans)

    try:
        while True: time.sleep(1.0)
    except KeyboardInterrupt:
        logger.info("Beendet.")

if __name__ == "__main__":
    main()
