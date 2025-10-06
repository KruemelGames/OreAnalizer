from pathlib import Path

# Resolve project root based on this package location
# constants.py is at <root>/easypeasyscanny/constants.py
BASE_DIR = Path(__file__).resolve().parent.parent

APP_NAME = "EasyPeasyScanny"
DEFAULT_SYSTEM = "STANTON"

# Use absolute, repo-relative paths
HISTORY_DIR = str(BASE_DIR / "scan_history")
ROCKS_PATH = str(BASE_DIR / "rocks.json")
CONFIG_PATH = str(BASE_DIR / "mining_analyzer_config.json")
