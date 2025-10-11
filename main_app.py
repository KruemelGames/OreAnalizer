from datetime import datetime
import threading

# Importiere die neuen Module
from config_manager import ConfigManager
from rock_analyzer import RockAnalyzer
from overlay_manager import OverlayManager
from gaming_mode import GamingMode, GLOBAL_HOTKEYS_AVAILABLE

try:
    import webview

    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False
    print("[ERROR] webview nicht installiert! Installiere mit: pip install pywebview")


class MiningAPI:
    """Haupt-API für die Mining-Analyzer Anwendung"""

    def __init__(self):
        # Module initialisieren
        self.config_manager = ConfigManager()
        self.rock_analyzer = RockAnalyzer()
        self.overlay_manager = OverlayManager(self.config_manager)

        # Gaming-Modus mit Callback
        self.gaming_mode = GamingMode(self.safe_evaluate_js)

        # Aktuelles System
        self.current_system = self.config_manager.config.get('selected_system', 'STANTON')
        self.rock_analyzer.build_rock_database(self.current_system)

        # Lade gespeicherten Gaming-Modus Status
        if self.config_manager.config.get('gaming_mode_enabled', False) and GLOBAL_HOTKEYS_AVAILABLE:
            try:
                result = self.gaming_mode.toggle()
                if result['success']:
                    print("[INFO] Gaming-Modus automatisch aktiviert")
                else:
                    print(f"[WARNING] Gaming-Modus konnte nicht aktiviert werden: {result.get('error')}")
            except Exception as e:
                print(f"[WARNING] Gaming-Modus konnte nicht automatisch aktiviert werden: {e}")

    def safe_evaluate_js(self, js_code):
        """Sichere JavaScript-Evaluation"""
        try:
            if not webview.windows or len(webview.windows) == 0:
                print("[WARNING] Kein Webview-Fenster verfügbar")
                return False

            main_window = webview.windows[0]
            if main_window is None:
                print("[WARNING] Hauptfenster ist None")
                return False

            main_window.evaluate_js(js_code)
            return True
        except (IndexError, AttributeError, RuntimeError) as e:
            print(f"[ERROR] JavaScript-Evaluation fehlgeschlagen: {e}")
            return False

    # ==================== API-Methoden für JavaScript ====================

    def search_signal(self, signal_value):
        """API: Suche nach Signal"""
        try:
            signal_value = int(signal_value)
            matches = self.rock_analyzer.find_matching_rocks(signal_value)

            # Erweitere matches mit Mineralien und Stats
            for match in matches:
                match['minerals'] = self.rock_analyzer.generate_mineral_composition(match)
                match['stats'] = self.rock_analyzer.calculate_rock_stats(match, signal_value)

            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

            # Füge zur Historie hinzu
            history = self.config_manager.add_scan_to_history(
                self.current_system,
                signal_value,
                timestamp
            )

            self.config_manager.save_config(self.current_system, self.gaming_mode.is_active())

            # Zeige Overlay wenn aktiviert
            if matches and self.config_manager.config.get('overlay_enabled', True):
                minerals = matches[0]['minerals']
                self.overlay_manager.show_overlay(signal_value, matches[0], minerals)

            # Hole Timestamps für dieses Signal
            timestamps = []
            for entry in history:
                if entry['signal'] == signal_value:
                    timestamps = entry.get('timestamps', [])
                    break

            return {
                'success': True,
                'signal': signal_value,
                'matches': matches,
                'history': history,
                'timestamps': timestamps
            }
        except ValueError:
            return {'success': False, 'error': 'Ungültiger Signalwert'}

    def get_cached_results(self, signal_value):
        """API: Hole gecachte Ergebnisse ohne neuen Scan"""
        try:
            signal_value = int(signal_value)
            matches = self.rock_analyzer.find_matching_rocks(signal_value)

            for match in matches:
                match['minerals'] = self.rock_analyzer.generate_mineral_composition(match)
                match['stats'] = self.rock_analyzer.calculate_rock_stats(match, signal_value)

            # Finde Timestamps
            history = self.config_manager.get_current_history(self.current_system)
            timestamps = []
            for entry in history:
                if entry['signal'] == signal_value:
                    timestamps = entry.get('timestamps', [])
                    break

            return {
                'success': True,
                'signal': signal_value,
                'matches': matches,
                'timestamps': timestamps,
                'cached': True
            }
        except ValueError:
            return {'success': False, 'error': 'Ungültiger Signalwert'}

    def get_history(self):
        """API: Hole aktuelle System-Scan-Historie"""
        return self.config_manager.get_current_history(self.current_system)

    def reset_scans(self):
        """API: Lösche Scan-Historie des aktuellen Systems"""
        self.config_manager.reset_history(self.current_system)
        self.config_manager.save_config(self.current_system, self.gaming_mode.is_active())
        return {
            'success': True,
            'message': f'Scan-Historie für {self.current_system} wurde gelöscht'
        }

    def get_initial_state(self):
        """API: Hole initialen Status der Modi"""
        current_history = self.config_manager.get_current_history(self.current_system)
        state = {
            'gaming_mode': self.gaming_mode.is_active(),
            'overlay_enabled': self.config_manager.config.get('overlay_enabled', True),
            'overlay_auto_hide_seconds': self.config_manager.config.get('overlay_auto_hide_seconds', 10),
            'selected_system': self.current_system,
            'history': current_history
        }
        print(f"[DEBUG] Initial State: System={self.current_system}, Historie={len(current_history)} Einträge")
        return state

    def change_system(self, system):
        """API: Wechsle zwischen Stanton und Pyro"""
        try:
            if system not in ['STANTON', 'PYRO']:
                return {'success': False, 'error': 'Ungültiges System'}

            old_system = self.current_system
            self.current_system = system
            self.rock_analyzer.build_rock_database(system)
            self.config_manager.config['selected_system'] = system
            self.config_manager.save_config(system, self.gaming_mode.is_active())

            new_history = self.config_manager.get_current_history(system)

            print(f"[INFO] System gewechselt von {old_system} zu {system}")
            print(f"[DEBUG] Historie für {system}: {len(new_history)} Einträge")

            return {
                'success': True,
                'system': system,
                'rocks_count': len(self.rock_analyzer.rock_database),
                'history': new_history,
                'message': f'System gewechselt zu {system}'
            }
        except Exception as e:
            print(f"[ERROR] Systemwechsel fehlgeschlagen: {e}")
            return {'success': False, 'error': str(e)}

    def set_overlay_timer(self, seconds):
        """API: Setze Overlay Auto-Hide Timer"""
        try:
            seconds = int(seconds)
            if seconds < 1 or seconds > 300:
                return {'success': False, 'error': 'Timer muss zwischen 1 und 300 Sekunden sein'}

            self.config_manager.config['overlay_auto_hide_seconds'] = seconds
            self.config_manager.save_config(self.current_system, self.gaming_mode.is_active())
            return {
                'success': True,
                'seconds': seconds,
                'message': f'Overlay-Timer auf {seconds} Sekunden gesetzt'
            }
        except (ValueError, TypeError) as e:
            return {'success': False, 'error': f'Ungültiger Wert: {e}'}

    def toggle_gaming_mode(self):
        """API: Gaming-Modus umschalten"""
        result = self.gaming_mode.toggle()
        if result['success']:
            self.config_manager.save_config(self.current_system, self.gaming_mode.is_active())
        return result

    def pause_gaming_listener(self):
        """API: Pausiere Gaming-Listener temporär"""
        return self.gaming_mode.pause_listener()

    def resume_gaming_listener(self):
        """API: Setze Gaming-Listener fort"""
        return self.gaming_mode.resume_listener()

    def toggle_overlay(self):
        """API: Overlay ein/ausschalten"""
        self.config_manager.config['overlay_enabled'] = not self.config_manager.config.get('overlay_enabled', True)
        if not self.config_manager.config['overlay_enabled']:
            self.overlay_manager.hide_overlay()
        self.config_manager.save_config(self.current_system, self.gaming_mode.is_active())
        return {
            'success': True,
            'enabled': self.config_manager.config['overlay_enabled'],
            'message': f"Overlay {'aktiviert' if self.config_manager.config['overlay_enabled'] else 'deaktiviert'}"
        }

    def toggle_price_overlay(self):
        """API: Zeige/Verstecke Preisliste"""
        return self.overlay_manager.toggle_price_overlay()

    def save_config(self):
        """Speichere finale Konfiguration"""
        self.config_manager.save_config(self.current_system, self.gaming_mode.is_active())


class StarCitizenMiningAnalyzer:
    """Hauptanwendung mit UI"""

    def __init__(self):
        if not WEBVIEW_AVAILABLE:
            print("[ERROR] webview ist nicht installiert!")
            print("Installiere mit: pip install pywebview")
            return

        self.api = MiningAPI()
        self.create_window()

    def create_window(self):
        """Erstelle Hauptfenster mit UI"""

        # Hier kommt der komplette HTML/CSS/JavaScript Code
        # Ich kürze ihn hier ab, da er sehr lang ist (ca. 1000 Zeilen)
        html_content = '''
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Regolith Mining Analyzer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            background: linear-gradient(135deg, rgba(26, 26, 46, 0.95), rgba(15, 52, 96, 0.95)); 
            color: #00d4ff; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
        }
        .container { max-width: 1000px; margin: 0 auto; padding: 20px; }
        .header { 
            text-align: center; 
            margin-bottom: 30px; 
            padding: 20px; 
            background: rgba(15, 52, 96, 0.3); 
            border: 2px solid #00d4ff; 
            border-radius: 10px; 
        }
        h1 { 
            font-size: 2.5em; 
            background: linear-gradient(45deg, #00d4ff, #45b7d1); 
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .controls { 
            background: rgba(22, 33, 62, 0.8); 
            border: 2px solid rgba(0, 212, 255, 0.3); 
            border-radius: 15px; 
            padding: 25px; 
            margin-bottom: 25px; 
        }
        #signalInput { 
            width: 100%; 
            padding: 15px; 
            font-size: 1.5em; 
            text-align: center; 
            background: rgba(15, 20, 25, 0.9); 
            border: 2px solid rgba(0, 212, 255, 0.5); 
            border-radius: 8px; 
            color: #00d4ff; 
        }
        .btn { 
            padding: 12px 20px; 
            border: none; 
            border-radius: 8px; 
            font-size: 1em; 
            font-weight: bold; 
            cursor: pointer; 
            transition: all 0.3s ease; 
        }
        .btn-gaming { background: #27ae60; color: white; }
        .btn-gaming.active { background: #e74c3c; }
        .btn-overlay { background: #9b59b6; color: white; }
        .btn-overlay.active { background: #2ecc71; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛰️ REGOLITH MINING ANALYZER</h1>
            <p>Star Citizen Signal Detection System</p>
        </div>
        <div class="controls">
            <div class="input-group">
                <label for="signalInput">Signal Stärke eingeben:</label>
                <input type="text" id="signalInput" placeholder="1800" maxlength="6">
            </div>
            <div class="input-group">
                <label for="systemSelect">System:</label>
                <select id="systemSelect">
                    <option value="STANTON">STANTON</option>
                    <option value="PYRO">PYRO</option>
                </select>
            </div>
            <button id="gamingBtn" class="btn btn-gaming">🎮 GAMING-MODUS</button>
            <button id="overlayBtn" class="btn btn-overlay">🎯 SC-OVERLAY</button>
        </div>
        <div id="results"></div>
    </div>
    <script>
        // JavaScript Code hier...
        // (würde die komplette UI-Logik enthalten)
    </script>
</body>
</html>
        '''

        webview.create_window(
            'Star Citizen Mining Analyzer',
            html=html_content,
            js_api=self.api,
            width=1000,
            height=780,
            min_size=(800, 650),
            resizable=True
        )


def main():
    """Hauptfunktion"""
    if not WEBVIEW_AVAILABLE:
        print("[ERROR] webview nicht installiert!")
        return

    analyzer = StarCitizenMiningAnalyzer()
    webview.start(debug=False)

    # Cleanup
    try:
        analyzer.api.save_config()
        analyzer.api.overlay_manager.hide_overlay()
        analyzer.api.gaming_mode.cleanup()
    except Exception as e:
        print(f"[WARNING] Cleanup fehlgeschlagen: {e}")


if __name__ == "__main__":
    main()