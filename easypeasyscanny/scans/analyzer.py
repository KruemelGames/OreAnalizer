from typing import Dict
import time
from ..config import Settings
from ..rocks.store import RockStore
from .store import ScanHistoryStore
from .models import ScanResult

class MiningAnalyzer:
    def __init__(self, rocks: RockStore, history: ScanHistoryStore, settings: Settings):
        self.rocks_store = rocks
        self.history = history
        self.settings = settings

    def score_composition(self, composition: Dict[str, float]) -> float:
        # Beispielhaftes Scoring – anpassbar
        weights = {"Quantanium": 5.0, "Bexalite": 3.0}
        return sum(weights.get(k, 1.0) * v for k, v in composition.items())

    def analyze_scan(self, composition: Dict[str, float]) -> ScanResult:
        score = self.score_composition(composition)
        result = ScanResult(
            timestamp=time.time(),
            system=self.settings.selected_system,
            rock_id=None,
            composition=composition,
            score=score,
        )
        self.history.append(result)
        return result

    def switch_system(self, new_system: str):
        self.settings.selected_system = new_system
