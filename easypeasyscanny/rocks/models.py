from dataclasses import dataclass
from typing import Dict

@dataclass
class Rock:
    id: str
    composition: Dict[str, float]
    mass: float
    location: str
