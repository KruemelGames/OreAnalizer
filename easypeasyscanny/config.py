import json, os
from dataclasses import dataclass, asdict
from .infra.paths import CONFIG_PATH
from .infra.logger import get_logger
logger = get_logger(__name__)
@dataclass
class Settings:
    selected_system: str = "STANTON"
    debug_logging: bool = False
def load_settings() -> Settings:
    if not os.path.exists(CONFIG_PATH):
        s = Settings(); save_settings(s); return s
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    base = asdict(Settings())
    base.update(data or {})
    return Settings(**base)
def save_settings(s: Settings):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(asdict(s), f, indent=2, ensure_ascii=False)
    logger.info("Settings gespeichert (debug=%s, system=%s)", s.debug_logging, s.selected_system)
