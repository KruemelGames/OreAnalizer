
"""
Legacy-Compatibility API
Ziel: Alle (typischen) Funktionen aus der alten mining_analyer.py als Funktions-API verfügbar machen.
Diese Funktionen rufen die neue modulare Implementierung auf.
"""
from typing import Any, Dict, Optional, List
from ..config import load_settings, save_settings, Settings
from ..infra.logger import get_logger
from ..infra.hotkeys import STATE
from ..scans.analyzer import MiningAnalyzer
from ..scans.store import ScansStore
from ..rocks.store import RocksRepo

logger = get_logger(__name__)

# Singleton-ähnliche Container (einfach für Kompatibilität)
class _Ctx:
    settings: Optional[Settings] = None
    rocks: Optional[RocksRepo] = None
    scans: Optional[ScansStore] = None
    analyzer: Optional[MiningAnalyzer] = None
CTX = _Ctx()

def _ensure_ctx():
    if CTX.settings is None:
        CTX.settings = load_settings()
    if CTX.rocks is None:
        CTX.rocks = RocksRepo(lambda: CTX.settings.selected_system)
    if CTX.scans is None:
        CTX.scans = ScansStore()
    if CTX.analyzer is None:
        CTX.analyzer = MiningAnalyzer(CTX.rocks, CTX.scans, CTX.settings)

# ===== Legacy-ähnliche API-Funktionen =====

def change_system(system: str) -> Dict[str, Any]:
    """Legacy-kompatibel: System wechseln und speichern."""
    _ensure_ctx()
    CTX.settings.selected_system = system
    save_settings(CTX.settings)
    logger.info("System gewechselt: %s", system)
    return {"ok": True, "system": system}

def toggle_debug(enabled: Optional[bool] = None) -> Dict[str, Any]:
    """Legacy-kompatibel: Debug toggeln (optional mit Zielwert)."""
    _ensure_ctx()
    if enabled is None:
        CTX.settings.debug_logging = not CTX.settings.debug_logging
    else:
        CTX.settings.debug_logging = bool(enabled)
    save_settings(CTX.settings)
    return {"ok": True, "debug": CTX.settings.debug_logging}

def get_settings() -> Dict[str, Any]:
    """Legacy-kompatibel: Settings auslesen."""
    _ensure_ctx()
    return {
        "selected_system": CTX.settings.selected_system,
        "debug_logging": CTX.settings.debug_logging,
        "systems": ["STANTON", "PYRO"],
    }

def get_history(system: Optional[str] = None) -> List[Dict[str, Any]]:
    """Legacy-kompatibel: Scanhistorie lesen (aktuelles System default)."""
    _ensure_ctx()
    sysname = system or CTX.settings.selected_system
    return CTX.scans.read_all(sysname)

def clear_history(system: Optional[str] = None) -> Dict[str, Any]:
    """Optional: Historie löschen (nicht zwingend im Legacy vorhanden)."""
    _ensure_ctx()
    sysname = system or CTX.settings.selected_system
    # implement: leere Datei
    import json, os
    path = CTX.scans._file(sysname)  # type: ignore
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([], f)
    return {"ok": True, "system": sysname, "count": 0}

def find_matching_rocks(signal_value: int) -> Dict[str, Any]:
    """Legacy-kompatibel: Kernfunktion zum Finden des Gesteins für ein Signal."""
    _ensure_ctx()
    return CTX.analyzer.resolve_by_signal(int(signal_value))

def analyze_signal(signal_value: int) -> Dict[str, Any]:
    """Legacy-kompatibel: Analyse + Persistierung."""
    _ensure_ctx()
    return CTX.analyzer.analyze_and_store(int(signal_value))

def search_signal(signal_value: int) -> Dict[str, Any]:
    """Alias: entspricht Analyse im Legacy-Flow (UI-Button/Numpad+)."""
    return analyze_signal(signal_value)

# Gaming / Preis-Overlay / Focus

def toggle_price_list() -> Dict[str, Any]:
    """Legacy-Name: Preisliste toggeln (Numpad−). UI-layer macht das eigentliche Fenster."""
    # Diese Funktion wird in main über overlay aufgerufen – wir lassen hier nur ein Log.
    logger.info("toggle_price_list() - Overlay wird von UI/main gehandhabt.")
    return {"ok": True}

def pause_gaming_listener():
    STATE.active = False
    return {"ok": True, "active": STATE.active}

def resume_gaming_listener():
    STATE.active = True
    return {"ok": True, "active": STATE.active}

def set_focus_state(focused: bool):
    STATE.focused = bool(focused)
    return {"ok": True, "focused": STATE.focused}

# Zusätzliche Legacy-Funktionsnamen (No-ops oder Delegates)

def generate_mineral_composition(rock: Dict[str, Any]) -> Dict[str, Any]:
    """In der neuen Struktur besorgt RocksRepo die Materialdaten – hier Rückgabe kompatibel halten."""
    _ensure_ctx()
    key = rock.get("rock") or rock.get("rock_key")
    details = CTX.rocks.describe_materials(key) if key else {}
    return {"rock": key, "materials": details}

def calculate_rock_stats(rock: Dict[str, Any], signal: int) -> Dict[str, Any]:
    """Platzhalter: Stats-Berechnung kann aus Legacy portiert werden. Hier basic-Gerüst."""
    return {"cluster": {"min": 1, "max": 10, "med": 6}}

