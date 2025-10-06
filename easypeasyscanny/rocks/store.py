import json
from typing import List
from .models import Rock

class RockStore:
    def __init__(self, path: str, system: str):
        self.path = path
        self.system = system
        self._rocks: List[Rock] = self._load()

    def _load(self) -> List[Rock]:
        with open(self.path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        # Erwartet Struktur: { "STANTON": [ {id, composition, ...}, ... ] }
        rocks_raw = raw.get(self.system, [])
        return [Rock(**r) for r in rocks_raw]

    def all(self) -> List[Rock]:
        return self._rocks
