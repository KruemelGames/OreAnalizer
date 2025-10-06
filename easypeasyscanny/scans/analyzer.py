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
            },
            'ETYPE': {
                'signal': 1900, 'tier': 3, 'value': 10.2, 'color': '#DC143C',
                'type': 'Asteroid', 'rarity': 'E-Type',
                'description': 'Seltener Enstatit-Asteroid mit hohem Wert'
            },
            'ITYPE': {
                'signal': 1660, 'tier': 3, 'value': 12.5, 'color': '#FF6347',
                'type': 'Asteroid', 'rarity': 'I-Type',
                'description': 'Seltener eisenreicher Asteroid'
            },
            'MTYPE': {
                'signal': 1850, 'tier': 2, 'value': 8.1, 'color': '#C0C0C0',
                'type': 'Asteroid', 'rarity': 'M-Type',
                'description': 'Metallreicher Asteroid mit Nickel und Eisen'
            },
            'PTYPE': {
                'signal': 1750, 'tier': 2, 'value': 6.2, 'color': '#8B4513',
                'type': 'Asteroid', 'rarity': 'P-Type',
                'description': 'Primitiver Asteroid mit niedrigem Albedo'
            },
            'QTYPE': {
                'signal': 1870, 'tier': 2, 'value': 7.6, 'color': '#DAA520',
                'type': 'Asteroid', 'rarity': 'Q-Type',
                'description': 'Quarzreicher Asteroid seltener Zusammensetzung'
            },
            'STYPE': {
                'signal': 1720, 'tier': 2, 'value': 5.8, 'color': '#CD853F',
                'type': 'Asteroid', 'rarity': 'S-Type',
                'description': 'Silikatreicher Asteroid mit Metallvorkommen'
            },
            'ATACAMITE': {
                'signal': 1800, 'tier': 2, 'value': 9.5, 'color': '#2ECC71',
                'type': 'Mineral', 'rarity': 'Selten',
                'description': 'Kupferhalogenid mit hohem Marktwert'
            },
            'FELSIC': {
                'signal': 1770, 'tier': 2, 'value': 6.9, 'color': '#F0E68C',
                'type': 'Magmatisch', 'rarity': 'Felsisch',
                'description': 'Felsisches Gestein reich an Feldspat und Quarz'
            },
            'GNEISS': {
                'signal': 1840, 'tier': 2, 'value': 6.5, 'color': '#D2B48C',
                'type': 'Metamorph', 'rarity': 'Metamorph',
                'description': 'Gebändertes metamorphes Gestein'
            },
            'GRANITE': {
                'signal': 1920, 'tier': 2, 'value': 7.3, 'color': '#A9A9A9',
                'type': 'Magmatisch', 'rarity': 'Plutonisch',
                'description': 'Plutonisches Tiefengestein hoher Härte'
            },
            'IGNEOUS': {
                'signal': 1950, 'tier': 2, 'value': 8.0, 'color': '#CD5C5C',
                'type': 'Magmatisch', 'rarity': 'Vulkanisch',
                'description': 'Magmatisches Gestein vulkanischen Ursprungs'
            },
            'OBSIDIAN': {
                'signal': 1790, 'tier': 2, 'value': 7.2, 'color': '#2F4F4F',
                'type': 'Vulkanisch', 'rarity': 'Vulkanisch',
                'description': 'Vulkanisches Glas mit scharfen Kanten'
            },
            'QUARTZITE': {
                'signal': 1820, 'tier': 2, 'value': 5.9, 'color': '#F5F5DC',
                'type': 'Metamorph', 'rarity': 'Metamorph',
                'description': 'Metamorphes Quarzgestein sehr hoher Härte'
            },
            'SHALE': {
                'signal': 1730, 'tier': 2, 'value': 4.7, 'color': '#708090',
                'type': 'Sediment', 'rarity': 'Sedimentär',
                'description': 'Geschichtetes Sedimentgestein mit Schieferstruktur'
            }
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
        # 1) exact
        for k,v in SIGNAL_DB.items():
            try:
                if int(v.get('signal')) == int(value):
                    d = v.copy(); d['rock'] = k; d['signal'] = int(value); return d
            except Exception: pass
        # 2) closest
        best = None; diff = 10**9
        for k,v in SIGNAL_DB.items():
            sig = v.get('signal')
            if isinstance(sig,(int,float)):
                d = abs(int(sig) - int(value))
                if d < diff:
                    diff = d; best = (k,v)
        if best:
            k,v = best; d = v.copy(); d['rock']=k; d['approx']=True; d['signal']=int(value); d['diff']=diff; return d
        return {'rock': None, 'approx': True, 'signal': int(value)}

    def analyze_and_store(self, value: int) -> Dict[str, Any]:
        info = self.resolve_by_signal(value)
        details = self.rocks.describe_materials(info.get('rock'))
        merged = {**info, 'materials': details}
        logger.info("Analyze %s -> %s", value, info.get('rock'))
        self.scans_store.append_record(value=value, system=self.settings.selected_system, details=merged)
        return merged
