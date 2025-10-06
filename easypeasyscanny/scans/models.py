from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class ScanResult:
    timestamp: float
    system: str
    rock_id: Optional[str]
    composition: Dict[str, float]
    score: float
