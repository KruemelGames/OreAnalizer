from dataclasses import dataclass, asdict
import json
from .constants import CONFIG_PATH, DEFAULT_SYSTEM

@dataclass
class Settings:
    selected_system: str = DEFAULT_SYSTEM
    gaming_mode_enabled: bool = False
    # weitere Felder hier ergänzen

def load_settings(path: str = CONFIG_PATH) -> Settings:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Settings(**data)
    except FileNotFoundError:
        return Settings()

def save_settings(settings: Settings, path: str = CONFIG_PATH) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(settings), f, indent=2, ensure_ascii=False)
