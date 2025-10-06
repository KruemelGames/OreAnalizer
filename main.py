from easypeasyscanny.config import load_settings
from easypeasyscanny.constants import APP_NAME, ROCKS_PATH, HISTORY_DIR
from easypeasyscanny.rocks.store import RockStore
from easypeasyscanny.scans.store import ScanHistoryStore
from easypeasyscanny.scans.analyzer import MiningAnalyzer
from easypeasyscanny.ui.webapp import run_webapp

def main():
    settings = load_settings()
    rocks = RockStore(ROCKS_PATH, settings.selected_system)
    history = ScanHistoryStore(HISTORY_DIR)
    analyzer = MiningAnalyzer(rocks, history, settings)
    run_webapp(analyzer, APP_NAME)

if __name__ == "__main__":
    main()
