import json
from typing import Any, Dict, Optional
from ..infra.paths import ROCKS_PATH
from ..infra.logger import get_logger
logger = get_logger(__name__)

class RocksRepo:
    def __init__(self, system_getter):
        self._system_getter = system_getter
        with open(ROCKS_PATH, "r", encoding="utf-8") as f:
            self._data = json.load(f)

    def describe_materials(self, rock_key: Optional[str]) -> Dict[str, Any]:
        system = self._system_getter()
        node = self._data.get(system) or {}
        return node.get(rock_key, {})
