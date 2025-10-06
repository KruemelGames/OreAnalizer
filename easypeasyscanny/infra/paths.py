from pathlib import Path
BASE_DIR = Path(__file__).resolve().parents[2]
SCAN_HISTORY_DIR = str(BASE_DIR / "scan_history")
ROCKS_PATH = str(BASE_DIR / "rocks.json")
CONFIG_PATH = str(BASE_DIR / "mining_analyer_config.json")
def system_file_path(system: str) -> str:
    safe = ''.join(c for c in system if c.isalnum() or c in ('_','-'))
    return str((Path(SCAN_HISTORY_DIR) / f"{safe}.json").resolve())
