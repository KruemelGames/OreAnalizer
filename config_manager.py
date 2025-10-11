import json
import os


class ConfigManager:
    """Verwaltet alle Konfigurationen und Einstellungen"""

    def __init__(self, config_file="mining_analyzer_config.json"):
        self.config_file = config_file
        self.config = self.load_config()

        # Historien für beide Systeme
        self.scan_history_stanton = []
        self.scan_history_pyro = []

        # Lade gespeicherte Historien
        if self.config.get('scan_history_STANTON'):
            self.scan_history_stanton = self.config['scan_history_STANTON']
            print(f"[INFO] STANTON Historie geladen: {len(self.scan_history_stanton)} Einträge")
        if self.config.get('scan_history_PYRO'):
            self.scan_history_pyro = self.config['scan_history_PYRO']
            print(f"[INFO] PYRO Historie geladen: {len(self.scan_history_pyro)} Einträge")

    def load_config(self):
        """Lade Konfiguration aus Datei"""
        default_config = {
            'window_geometry': '1000x700',
            'window_position': {'x': 100, 'y': 100},
            'last_signals': [],
            'scan_history_size': 10,
            'overlay_enabled': True,
            'overlay_position': {'x': 20, 'y': 20},
            'price_overlay_position': {'x': 850, 'y': 250},
            'overlay_auto_hide_seconds': 10,
            'gaming_mode_enabled': False,
            'selected_system': 'STANTON'
        }

        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
                    return default_config
            else:
                return default_config
        except (IOError, json.JSONDecodeError) as e:
            print(f"[WARNING] Konfiguration konnte nicht geladen werden: {e}")
            return default_config

    def save_config(self, current_system, gaming_mode):
        """Speichere Konfiguration"""
        try:
            self.config['scan_history_STANTON'] = self.scan_history_stanton[:10]
            self.config['scan_history_PYRO'] = self.scan_history_pyro[:10]
            self.config['gaming_mode_enabled'] = gaming_mode
            self.config['overlay_enabled'] = self.config.get('overlay_enabled', True)
            self.config['overlay_auto_hide_seconds'] = self.config.get('overlay_auto_hide_seconds', 10)
            self.config['selected_system'] = current_system

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"[INFO] Config gespeichert: Gaming={gaming_mode}, System={current_system}")
        except (IOError, TypeError) as e:
            print(f"[WARNING] Konfiguration konnte nicht gespeichert werden: {e}")

    def get_current_history(self, system):
        """Hole die Historie für ein System"""
        if system == 'STANTON':
            return self.scan_history_stanton
        else:
            return self.scan_history_pyro

    def set_current_history(self, system, history):
        """Setze die Historie für ein System"""
        if system == 'STANTON':
            self.scan_history_stanton = history
        else:
            self.scan_history_pyro = history

    def add_scan_to_history(self, system, signal_value, timestamp):
        """Füge einen Scan zur Historie hinzu"""
        history = self.get_current_history(system)

        # Prüfe ob Signal bereits existiert
        existing_entry = None
        for entry in history:
            if entry['signal'] == signal_value:
                existing_entry = entry
                break

        if existing_entry:
            # Aktualisiere existierenden Eintrag
            if 'timestamps' not in existing_entry:
                existing_entry['timestamps'] = [existing_entry.get('time', timestamp)]
            existing_entry['timestamps'].append(timestamp)
            existing_entry['count'] = len(existing_entry['timestamps'])
            existing_entry['time'] = timestamp
        else:
            # Neuer Eintrag
            history.insert(0, {
                'signal': signal_value,
                'time': timestamp,
                'count': 1,
                'timestamps': [timestamp]
            })

        # Behalte nur Top 10
        history = history[:10]
        self.set_current_history(system, history)

        return history

    def reset_history(self, system):
        """Lösche Historie für ein System"""
        self.set_current_history(system, [])