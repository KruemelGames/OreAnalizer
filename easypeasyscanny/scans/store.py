import json, os, time
from typing import Any, Dict, List
from ..infra.paths import SCAN_HISTORY_DIR, system_file_path
from ..infra.logger import get_logger
logger = get_logger(__name__)

class ScansStore:
    def __init__(self):
        os.makedirs(SCAN_HISTORY_DIR, exist_ok=True)

    def _file(self, system: str) -> str:
        return system_file_path(system)

    def read_all(self, system: str) -> List[Dict[str, Any]]:
        path = self._file(system)
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Fehler beim Laden von {path}: {e}")
            return []

    def append_record(self, value: int, system: str, details: Dict[str, Any]):
        data = self.read_all(system)
        data.append({"timestamp": time.time(), "system": system, "input_value": value, "details": details})
        with open(self._file(system), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.debug("Scan appended: %s", value)
