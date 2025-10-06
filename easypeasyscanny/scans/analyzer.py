from dataclasses import dataclass
from typing import Dict, Any, Optional
from ..rocks.store import RocksRepo
from ..infra.logger import get_logger
logger = get_logger(__name__)
SIGNAL_DB: Dict[str, Dict[str, Any]] = {
            'CTYPE': {
                'signal': 1700, 'tier': 2, 'value': 5.1, 'color': '#696969',
                'type': 'Asteroid', 'rarity': 'C-Type',
                'description': 'Kohlenstoffreicher Asteroid mit organischen Verbindungen'
            }
@dataclass
class ScanRecord:
    timestamp: float
    system: str
    input_value: int
    rock_key: Optional[str]
    details: Dict[str, Any]
class MiningAnalyzer:
    def __init__(self, rocks: RocksRepo, scans_store, settings):
        self.rocks = rocks
        self.scans_store = scans_store
        self.settings = settings
    def resolve_by_signal(self, value: int) -> Dict[str, Any]:
        for k, v in SIGNAL_DB.items():
            try:
                if int(v.get('signal')) == int(value):
                    d = v.copy(); d['rock'] = k
                    return d
            except Exception:
                pass
        best = None; best_diff = 10**9
        for k, v in SIGNAL_DB.items():
            sig = v.get('signal')
            if isinstance(sig, (int, float)):
                diff = abs(int(sig) - int(value))
                if diff < best_diff:
                    best = (k, v); best_diff = diff
        if best:
            k, v = best; d = v.copy(); d['rock']=k; d['approx']=True; d['diff']=best_diff
            return d
        return {'rock': None, 'approx': True}
    def analyze_and_store(self, value: int) -> Dict[str, Any]:
        info = self.resolve_by_signal(value)
        details = self.rocks.describe_materials(info.get('rock'))
        merged = {**info, 'materials': details}
        logger.info('Analyze %s -> %s', value, info.get('rock'))
        self.scans_store.append_record(value=value, system=self.settings.selected_system, details=merged)
        return merged
