import json, os
from typing import List
from .models import ScanResult

class ScanHistoryStore:
    def __init__(self, folder: str):
        self.folder = folder
        os.makedirs(self.folder, exist_ok=True)

    def _file(self, system: str) -> str:
        safe = system.replace(os.sep, "_")
        return os.path.join(self.folder, f"history_{safe}.json")

    def load(self, system: str) -> List[ScanResult]:
        path = self._file(system)
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [ScanResult(**d) for d in data]

    def append(self, result: ScanResult):
        lst = self.load(result.system)
        lst.append(result)
        with open(self._file(result.system), "w", encoding="utf-8") as f:
            json.dump([r.__dict__ for r in lst], f, indent=2, ensure_ascii=False)
