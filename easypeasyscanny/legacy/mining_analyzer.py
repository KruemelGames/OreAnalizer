import json
import os
import math
from datetime import datetime
import threading
import time

# Webview für moderne UI
try:
    import webview

    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False
    print("[ERROR] webview nicht installiert! Installiere mit: pip install pywebview")

# Für globale Hotkeys (Gaming-Modus)
try:
    from pynput import keyboard

    GLOBAL_HOTKEYS_AVAILABLE = True
except ImportError:
    GLOBAL_HOTKEYS_AVAILABLE = False
    print("[INFO] pynput nicht installiert - Gaming-Modus nicht verfügbar")


class MiningAPI:
    def __init__(self):
        # Konfiguration
        self.config_file = "mining_analyzer_config.json"
        self.config = self.load_config()

        # Lade Mining-Datenbank aus JSON
        self.rocks_data = self.load_rocks_json()
        self.current_system = self.config.get('selected_system', 'STANTON')
        self.rock_database = self.build_rock_database(self.current_system)

        # Status-Variablen
        self.scan_history_stanton = []
        self.scan_history_pyro = []
        self.gaming_mode = False
        self.global_listener = None
        self.overlay_window = None
        self.overlay_lock = threading.Lock()
        self.hide_timer = None
        self.price_overlay_window = None
        self.price_overlay_lock = threading.Lock()

        # Lade gespeicherte Historien für beide Systeme
        if self.config.get('scan_history_STANTON'):
            self.scan_history_stanton = self.config['scan_history_STANTON']
            print(f"[INFO] STANTON Historie geladen: {len(self.scan_history_stanton)} Einträge")
        if self.config.get('scan_history_PYRO'):
            self.scan_history_pyro = self.config['scan_history_PYRO']
            print(f"[INFO] PYRO Historie geladen: {len(self.scan_history_pyro)} Einträge")

        # Lade gespeicherte Modi-Status
        if self.config.get('gaming_mode_enabled', False) and GLOBAL_HOTKEYS_AVAILABLE:
            try:
                self.gaming_mode = True
                self.global_listener = keyboard.Listener(
                    on_press=self.on_global_key_press,
                    suppress=False
                )
                self.global_listener.start()
                print("[INFO] Gaming-Modus automatisch aktiviert")
            except Exception as e:
                print(f"[WARNING] Gaming-Modus konnte nicht automatisch aktiviert werden: {e}")
                self.gaming_mode = False
                self.config['gaming_mode_enabled'] = False

    def load_config(self):
        """Lade Konfiguration aus Datei"""
        default_config = {
            'window_geometry': '1000x700',
            'window_position': {'x': 100, 'y': 100},
            'last_signals': [],
            'scan_history_size': 10,
            'overlay_enabled': True,
            'overlay_position': {'x': 20, 'y': 20},
            'price_overlay_position': {'x': 850, 'y': 250},  # Neue Position für Preis-Overlay
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

    def load_rocks_json(self):
        """Lade rocks.json Datei"""
        try:
            if os.path.exists('rocks.json'):
                with open('rocks.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print("[ERROR] rocks.json nicht gefunden!")
                return {}
        except (IOError, json.JSONDecodeError) as e:
            print(f"[ERROR] Fehler beim Laden von rocks.json: {e}")
            return {}

    def build_rock_database(self, system):
        """Erstelle Rock-Datenbank aus JSON für ein System"""
        database = []

        if not self.rocks_data or system not in self.rocks_data:
            print(f"[ERROR] System {system} nicht in rocks.json gefunden!")
            return database

        system_data = self.rocks_data[system]

        # Definiere Signal-Werte und andere Eigenschaften für jeden Rock-Typ
        rock_properties = {
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

        # Erstelle Einträge für jeden Rock-Typ
        for rock_type, rock_data in system_data.items():
            if rock_type in rock_properties:
                props = rock_properties[rock_type]

                # Extrahiere Stats aus JSON
                stats = {
                    'cluster_max': rock_data.get('clusterCount', {}).get('max', 11),
                    'mass_max': rock_data.get('mass', {}).get('max', 100),
                    'instability_max': int(rock_data.get('inst', {}).get('max', 500)),
                    'resistance_max': int(rock_data.get('res', {}).get('max', 0.8) * 100)
                }

                database.append({
                    'name': f"{rock_type.replace('TYPE', '-Type').title()}",
                    'signal': props['signal'],
                    'tier': props['tier'],
                    'value': props['value'],
                    'color': props['color'],
                    'type': props['type'],
                    'rarity': props['rarity'],
                    'description': props['description'],
                    'stats': stats,
                    'rock_type': rock_type,
                    'ores': rock_data.get('ores', {})
                })

        print(f"[INFO] {len(database)} Rock-Typen geladen für System {system}")
        return database

    def get_current_history(self):
        """Hole die aktuelle System-Historie"""
        if self.current_system == 'STANTON':
            return self.scan_history_stanton
        else:
            return self.scan_history_pyro

    def set_current_history(self, history):
        """Setze die aktuelle System-Historie"""
        if self.current_system == 'STANTON':
            self.scan_history_stanton = history
        else:
            self.scan_history_pyro = history

    def save_config(self):
        """Speichere Konfiguration"""
        try:
            self.config['scan_history_STANTON'] = self.scan_history_stanton[:10]
            self.config['scan_history_PYRO'] = self.scan_history_pyro[:10]
            self.config['gaming_mode_enabled'] = self.gaming_mode
            self.config['overlay_enabled'] = self.config.get('overlay_enabled', True)
            self.config['overlay_auto_hide_seconds'] = self.config.get('overlay_auto_hide_seconds', 10)
            self.config['selected_system'] = self.current_system
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"[INFO] Config gespeichert: Gaming={self.gaming_mode}, System={self.current_system}")
        except (IOError, TypeError) as e:
            print(f"[WARNING] Konfiguration konnte nicht gespeichert werden: {e}")

    def safe_evaluate_js(self, js_code):
        """Sichere JavaScript-Evaluation mit Window-Existenz-Prüfung"""
        try:
            if not webview.windows or len(webview.windows) == 0:
                print("[WARNING] Kein Webview-Fenster verfügbar für JS-Evaluation")
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

    def find_matching_rocks(self, signal_value):
        """Finde passende Gesteine basierend auf Signalwert"""
        all_matches = []

        # 1. Suche nach Grundwerten (1x)
        for rock in self.rock_database:
            if rock['signal'] == signal_value:
                rock_copy = rock.copy()
                rock_copy['accuracy'] = 100
                rock_copy['multima_factor'] = 1
                all_matches.append(rock_copy)

        # 2. Suche nach Multima-Werten (2x bis 30x) - nur Tier 2+
        for rock in self.rock_database:
            if rock.get('tier', 1) == 1:
                continue

            base_signal = rock['signal']
            if signal_value % base_signal == 0:
                factor = signal_value // base_signal
                if 2 <= factor <= 30:
                    rock_copy = rock.copy()
                    rock_copy['accuracy'] = 100
                    rock_copy['multima_factor'] = factor
                    rock_copy['signal'] = signal_value
                    rock_copy['name'] = f"{rock['name']} {factor}x Multima"
                    rock_copy['value'] = rock['value'] * factor
                    rock_copy['description'] = f"{rock['description']} (Multima-Formation mit {factor}x Konzentration)"
                    all_matches.append(rock_copy)

        if all_matches:
            return all_matches

        # 3. Snapping zu nächstbesten Werten
        distances = []

        for rock in self.rock_database:
            distance = abs(rock['signal'] - signal_value)
            if distance <= 50:
                rock_entry = rock.copy()
                rock_entry['multima_factor'] = 1
                distances.append((distance, rock_entry))

        for rock in self.rock_database:
            base_signal = rock['signal']
            for factor in range(2, 31):
                multima_signal = base_signal * factor
                distance = abs(multima_signal - signal_value)

                if distance <= 100:
                    rock_entry = rock.copy()
                    rock_entry['signal'] = multima_signal
                    rock_entry['multima_factor'] = factor
                    rock_entry['name'] = f"{rock['name']} {factor}x Multima"
                    rock_entry['value'] = rock['value'] * factor
                    rock_entry['description'] = f"{rock['description']} (Multima-Formation mit {factor}x Konzentration)"
                    distances.append((distance, rock_entry))

        if not distances:
            return []

        distances.sort(key=lambda x: x[0])
        min_distance = distances[0][0]

        closest_matches = []
        for distance, rock in distances:
            if distance == min_distance:
                if rock.get('multima_factor', 1) > 1:
                    accuracy = max(0, round((1 - distance / 100) * 100))
                else:
                    accuracy = max(0, round((1 - distance / 50) * 100))

                rock['accuracy'] = accuracy
                closest_matches.append(rock)
            else:
                break

        return closest_matches

    def generate_mineral_composition(self, rock):
        """Generiere realistische Mineralzusammensetzung basierend auf regolith.rocks Daten"""
        base_name = rock.get('rock_type', '')
        ores = rock.get('ores', {})

        if not ores:
            return []

        # Farben bleiben gleich...
        mineral_colors = {
            'QUANTANIUM': '#E91E63',
            'TARANITE': '#4CAF50',
            'BEXALITE': '#FF9800',
            'GOLD': '#FFD700',
            'AGRICIUM': '#8BC34A',
            'HEPHAESTANITE': '#FF5722',
            'TUNGSTEN': '#607D8B',
            'TITANIUM': '#9C27B0',
            'IRON': '#795548',
            'QUARTZ': '#E0E0E0',
            'CORUNDUM': '#F44336',
            'COPPER': '#FF5722',
            'ALUMINUM': '#9E9E9E',
            'BERYL': '#90EE90',
            'BORASE': '#8BC34A',
            'LARANITE': '#45B7D1',
            'ICE': '#87CEEB',
            'INERTMATERIAL': '#708090',
            'TIN': '#A9A9A9',
            'SILICON': '#778899',
            'RICCITE': '#FF6B6B',
            'STILERON': '#9370DB'
        }

        # Sammle alle Mineralien mit ihren Werten
        all_minerals = []
        for ore_name, ore_data in ores.items():
            if ore_name == 'INERTMATERIAL':
                continue

            prob = ore_data.get('prob', 0)
            med_pct = ore_data.get('medPct', 0)

            # NEUE LOGIK: Niedrigere Schwelle (3% statt 5%)
            # Damit werden auch seltene aber wertvolle Mineralien wie Quantanium angezeigt
            if prob > 0.03 and med_pct > 0:
                percentage = int(med_pct * 100)
                if percentage > 0:
                    display_name = ore_name.title()
                    color = mineral_colors.get(ore_name, '#808080')
                    # Speichere auch prob für spätere Sortierung
                    all_minerals.append((display_name, percentage, color, prob))

        # Sortiere nach medPct (Prozentsatz) absteigend
        all_minerals.sort(key=lambda x: x[1], reverse=True)

        # Nimm nur die Top 10 Mineralien (wie Regolith)
        composition = [(name, pct, color) for name, pct, color, _ in all_minerals[:10]]

        # Multima-Boost bleibt gleich...
        if rock.get('multima_factor', 1) > 1 and len(composition) > 0:
            factor = rock['multima_factor']
            new_comp = []
            total_boost = min(30, factor * 5)

            main_mineral = composition[0]
            boosted_pct = min(80, main_mineral[1] + total_boost)
            new_comp.append((main_mineral[0], boosted_pct, main_mineral[2]))

            if len(composition) > 1:
                reduction = total_boost / (len(composition) - 1)
                for mineral, percent, color in composition[1:]:
                    new_percent = max(1, int(percent - reduction))
                    new_comp.append((mineral, new_percent, color))

            composition = new_comp

        return composition

    # API-Methoden für JavaScript
    def search_signal(self, signal_value):
        """API: Suche nach Signal"""
        try:
            signal_value = int(signal_value)
            matches = self.find_matching_rocks(signal_value)

            for match in matches:
                match['minerals'] = self.generate_mineral_composition(match)
                match['stats'] = self.calculate_rock_stats(match, signal_value)

            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

            # Hole aktuelle System-Historie
            scan_history = self.get_current_history()

            existing_entry = None
            for entry in scan_history:
                if entry['signal'] == signal_value:
                    existing_entry = entry
                    break

            if existing_entry:
                if 'timestamps' not in existing_entry:
                    existing_entry['timestamps'] = [existing_entry.get('time', timestamp)]
                existing_entry['timestamps'].append(timestamp)
                existing_entry['count'] = len(existing_entry['timestamps'])
                existing_entry['time'] = timestamp
            else:
                scan_history.insert(0, {
                    'signal': signal_value,
                    'time': timestamp,
                    'count': 1,
                    'timestamps': [timestamp]
                })

            # Behalte nur Top 10
            scan_history = scan_history[:10]
            self.set_current_history(scan_history)
            self.save_config()

            if matches and self.config.get('overlay_enabled', True):
                self.show_overlay(signal_value, matches[0])

            return {
                'success': True,
                'signal': signal_value,
                'matches': matches,
                'history': scan_history,
                'timestamps': existing_entry['timestamps'] if existing_entry else [timestamp]
            }
        except ValueError:
            return {'success': False, 'error': 'Ungültiger Signalwert'}

    def calculate_rock_stats(self, rock, signal):
        """Berechne Stats für Rock - KORRIGIERT um originale JSON-Daten zu verwenden"""
        multima = rock.get('multima_factor', 1)

        # Hole die ORIGINALEN Stats aus der Datenbank
        original_rock = None
        rock_type = rock.get('rock_type', '')
        base_signal = rock.get('signal', signal)

        # Bei Multima: hole den base_signal
        if multima > 1:
            base_signal = base_signal // multima

        # Finde den Original-Rock in der Datenbank
        for db_rock in self.rock_database:
            if db_rock.get('rock_type') == rock_type and db_rock['signal'] == base_signal:
                original_rock = db_rock
                break

        # Verwende original stats falls vorhanden
        if original_rock and 'stats' in original_rock:
            orig_stats = original_rock['stats']
        else:
            orig_stats = {}

        # Berechne Cluster Stats
        cluster_min = 1
        cluster_max = orig_stats.get('cluster_max', max(11, multima * 3))
        cluster_med = max(6, min(cluster_max, multima * 2))

        # Berechne Mass Stats
        if 'mass_max' in orig_stats:
            rock_mass_max = orig_stats['mass_max']
            rock_mass_med = round(rock_mass_max * 0.048, 1)
        else:
            mass_factor = signal / 1000.0
            rock_mass_max = int(182 * mass_factor * multima)
            rock_mass_med = round(rock_mass_max * 0.048, 1)

        # Berechne Instability Stats
        if 'instability_max' in orig_stats:
            instability = orig_stats['instability_max']
            instability_med = int(instability * 0.065)
        else:
            instability = max(0, min(1000, (signal - 500) // 2))
            instability_med = instability // 2

        # Berechne Resistance Stats
        if 'resistance_max' in orig_stats:
            resistance_max = orig_stats['resistance_max']
            resistance_med = int(resistance_max * 0.2)
        else:
            resistance_max = min(100, int(instability * 0.1) + 20)
            resistance_med = resistance_max // 2

        return {
            'cluster': {'min': cluster_min, 'max': cluster_max, 'med': cluster_med},
            'mass': {'min': 0, 'max': f"{rock_mass_max}k", 'med': f"{rock_mass_med}k"},
            'instability': {'min': 0, 'max': instability, 'med': instability_med},
            'resistance': {'min': '0%', 'max': f"{resistance_max}%", 'med': f"{resistance_med}%"}
        }

    def show_overlay(self, signal, rock):
        """Zeige SC-ähnliches Overlay über dem Spiel"""
        if not WEBVIEW_AVAILABLE:
            return

        try:
            self.hide_overlay()

            minerals = self.generate_mineral_composition(rock)
            auto_hide_seconds = self.config.get('overlay_auto_hide_seconds', 10)

            max_mineral_name_length = max(len(name) for name, _, _ in minerals) if minerals else 10
            overlay_width = min(420, max(350, 350 + (max_mineral_name_length - 10) * 2))

            overlay_html = self.create_overlay_html(signal, rock, minerals, auto_hide_seconds, overlay_width)

            header_height = 62
            stats_height = 165
            mineral_header_height = 28
            mineral_row_height = 19
            mineral_list_height = len(minerals) * mineral_row_height
            multima_height = 38 if rock.get('multima_factor', 1) > 1 else 0
            bottom_padding = 18
            border_space = 2

            calculated_height = (header_height + stats_height + mineral_header_height +
                                 mineral_list_height + multima_height + bottom_padding + border_space)

            overlay_height = max(350, min(950, calculated_height))

            with self.overlay_lock:
                self.overlay_window = webview.create_window(
                    'SC Mining Overlay',
                    html=overlay_html,
                    width=overlay_width,
                    height=overlay_height,
                    x=self.config.get('overlay_position', {}).get('x', 20),
                    y=self.config.get('overlay_position', {}).get('y', 20),
                    min_size=(320, 300),
                    resizable=False,
                    on_top=True,
                    transparent=True,
                    frameless=True,
                    shadow=False
                )
            # --- Auto-Resize an Inhalt --------------------------------------
            # Passe die Fensterhöhe nach dem Rendern an den tatsächlichen DOM-Height an,
            # damit nichts abgeschnitten wird und auch nicht zu groß wird.
            def _autofit_overlay(attempt=0, last_height=0):
                try:
                    # Erfrage die gesamte Dokumenthöhe (Body/HTML)
                    js = '(function(){var b=document.body, d=document.documentElement; return Math.ceil(Math.max(b.scrollHeight, d.scrollHeight));})()'
                    h = self.overlay_window.evaluate_js(js)
                    if h is None:
                        h = 0
                    try:
                        h = int(float(h))
                    except Exception:
                        h = 0

                    # Zielhöhe mit Grenzen
                    min_h = 300
                    max_h = 1600
                    target_h = max(min_h, min(max_h, h))

                    if target_h and abs(target_h - last_height) > 2:
                        # Größe anpassen
                        self.overlay_window.resize(overlay_width, target_h)
                        last_height = target_h

                    # Wiederholen, solange sich der Inhalt noch setzt (Schriften/Images)
                    if attempt < 10:
                        threading.Timer(0.15, lambda: _autofit_overlay(attempt+1, last_height)).start()
                except Exception as e:
                    print(f"[WARN] Auto-resize failed: {e}")

            # initial nach kurzem Delay starten
            threading.Timer(0.2, _autofit_overlay).start()
            # -----------------------------------------------------------------


            if self.hide_timer:
                self.hide_timer.cancel()
            self.hide_timer = threading.Timer(float(auto_hide_seconds), self.hide_overlay)
            self.hide_timer.start()

        except Exception as e:
            print(f"[ERROR] Overlay konnte nicht erstellt werden: {e}")

    def hide_overlay(self):
        """Verstecke das Overlay"""
        with self.overlay_lock:
            if self.overlay_window:
                try:
                    self.overlay_window.destroy()
                except Exception as e:
                    print(f"[WARNING] Overlay-Fenster konnte nicht zerstört werden: {e}")
                finally:
                    self.overlay_window = None

        if self.hide_timer:
            self.hide_timer.cancel()
            self.hide_timer = None

    def save_price_overlay_position(self):
        """Speichere Position des Preis-Overlays"""
        if self.price_overlay_window:
            try:
                x = self.price_overlay_window.x
                y = self.price_overlay_window.y
                self.config['price_overlay_position'] = {'x': x, 'y': y}
                self.save_config()
                print(f"[INFO] Preis-Overlay Position gespeichert: x={x}, y={y}")
            except Exception as e:
                print(f"[WARNING] Position konnte nicht gespeichert werden: {e}")

    def toggle_price_overlay(self):
        """API: Zeige/Verstecke Preisliste als freistehendes Overlay"""
        with self.price_overlay_lock:
            if self.price_overlay_window:
                # Speichere Position vor dem Schließen
                self.save_price_overlay_position()
                # Schließe das Overlay
                try:
                    self.price_overlay_window.destroy()
                    print("[INFO] Preis-Overlay geschlossen")
                except Exception as e:
                    print(f"[WARNING] Preis-Overlay konnte nicht geschlossen werden: {e}")
                finally:
                    self.price_overlay_window = None
                return {'success': True, 'visible': False}
            else:
                # Öffne das Overlay als FREISTEHENDES Fenster
                try:
                    price_html = self.create_price_overlay_html()

                    # Fenstergröße (3 Spalten - breiter aber niedriger)
                    window_width = 720
                    window_height = 380

                    # Position berechnen
                    price_pos = self.config.get('price_overlay_position', None)

                    if price_pos is None:
                        # Erste Anzeige: Unten mittig am Bildschirm
                        try:
                            screen = webview.screens[0]
                            screen_width = screen.width
                            screen_height = screen.height

                            # Mittig horizontal
                            x = (screen_width - window_width) // 2
                            # Unten mit 50px Abstand
                            y = screen_height - window_height - 50
                        except:
                            # Fallback wenn Bildschirmgröße nicht ermittelt werden kann
                            x = 400
                            y = 600
                    else:
                        # Gespeicherte Position verwenden
                        x = price_pos.get('x', 400)
                        y = price_pos.get('y', 600)

                    # Erstelle Fenster mit berechneter Position
                    self.price_overlay_window = webview.create_window(
                        'Mineable Ore Prices',
                        html=price_html,
                        width=window_width,
                        height=window_height,
                        x=x,
                        y=y,
                        min_size=(450, 400),
                        resizable=False,
                        on_top=True,
                        transparent=True,
                        frameless=True,
                        shadow=False
                    )

                    # Starte Position-Tracking-Thread
                    threading.Timer(0.5, self._track_price_overlay_position).start()

                    print(f"[INFO] Preis-Overlay geöffnet at x={x}, y={y}")
                    return {'success': True, 'visible': True}
                except Exception as e:
                    print(f"[ERROR] Preis-Overlay konnte nicht erstellt werden: {e}")
                    return {'success': False, 'error': str(e)}

    def _track_price_overlay_position(self):
        """Tracke Position-Änderungen des Preis-Overlays"""
        last_x, last_y = None, None
        check_count = 0

        while self.price_overlay_window is not None:
            try:
                current_x = self.price_overlay_window.x
                current_y = self.price_overlay_window.y

                # Wenn Position sich geändert hat, speichere sie
                if (last_x is not None and last_y is not None):
                    if (current_x != last_x or current_y != last_y):
                        self.save_price_overlay_position()
                        print(f"[DEBUG] Position geändert: {current_x}, {current_y}")

                last_x = current_x
                last_y = current_y

                check_count += 1
                # Nach 20 Checks (10 Sekunden) nur noch alle 2 Sekunden prüfen
                if check_count > 20:
                    time.sleep(2)
                else:
                    time.sleep(0.5)

            except Exception as e:
                print(f"[DEBUG] Position-Tracking beendet: {e}")
                break

    def create_price_overlay_html(self):
        """Erstelle HTML für Preisliste-Overlay (kompakt, 3 Spalten, alle Ores komplett)"""
        html = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background: rgba(26, 26, 46, 0.95);
            color: #00d4ff;
            font-family: 'Segoe UI', Arial, sans-serif;
            border: 2px solid rgba(0, 212, 255, 0.4);
            border-radius: 10px;
            padding: 12px 15px;
            backdrop-filter: blur(5px);
            overflow: hidden;
        }

        h2 {
            text-align: center;
            margin-bottom: 10px;
            color: #00d4ff;
            font-size: 1.2em;
        }

        .price-tables {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 12px;
        }

        .price-table {
            min-width: 0;
        }

        .price-table table {
            width: 100%;
            border-collapse: collapse;
        }

        .price-table th {
            padding: 5px 3px;
            text-align: left;
            border-bottom: 2px solid rgba(0, 212, 255, 0.3);
            color: #7fb3d3;
            font-size: 0.7em;
        }

        .price-table th.tier-col {
            width: 22px;
            text-align: center;
        }

        .price-table th.price-col {
            text-align: right;
        }

        .price-table td {
            padding: 4px 3px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            font-size: 0.75em;
        }

        .tier-cell {
            text-align: center;
            font-weight: bold;
            width: 22px;
        }

        .tier-s { color: #FFD700; }
        .tier-1 { color: #FF6347; }
        .tier-2 { color: #90EE90; }
        .tier-3 { color: #87CEEB; }
        .tier-4 { color: #DDA0DD; }
        .tier-5 { color: #D3D3D3; }
        .tier-6 { color: #A9A9A9; }

        .resource-name {
            font-weight: bold;
            text-shadow: 
                -1px -1px 0 #000,
                 1px -1px 0 #000,
                -1px  1px 0 #000,
                 1px  1px 0 #000;
        }

        .price {
            text-align: right;
            color: #b0b0b0;
        }

        .price-quantainium { color: #FFD700; }
        .price-stileron { color: #9370DB; }
        .price-bexalite { color: #90EE90; }
        .price-borase { color: #90EE90; }
        .price-taranite { color: #90EE90; }
        .price-laranite { color: #90EE90; }
        .price-agricium { color: #90EE90; }
        .price-hephaestanite { color: #ffffff; }

        .close-hint {
            text-align: center;
            margin-top: 8px;
            color: #7fb3d3;
            font-size: 0.65em;
        }
    </style>
</head>
<body>
    <h2>Mineable Ore Prices</h2>
    <div class="price-tables">
        <div class="price-table">
            <table>
                <thead>
                    <tr>
                        <th class="tier-col">T</th>
                        <th>Resource</th>
                        <th class="price-col">Raw</th>
                        <th class="price-col">Ref</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td class="tier-cell tier-s">S</td>
                        <td class="resource-name price-quantainium">Quantainium</td>
                        <td class="price">44.00</td>
                        <td class="price">88.00</td>
                    </tr>
                    <tr>
                        <td class="tier-cell tier-s">S</td>
                        <td class="resource-name price-stileron">Stileron</td>
                        <td class="price">25.00</td>
                        <td class="price">50.00</td>
                    </tr>
                    <tr>
                        <td class="tier-cell tier-s">S</td>
                        <td class="resource-name">Ricote</td>
                        <td class="price">22.00</td>
                        <td class="price">44.00</td>
                    </tr>
                    <tr>
                        <td class="tier-cell tier-1">1</td>
                        <td class="resource-name price-bexalite">Bexalite</td>
                        <td class="price">20.33</td>
                        <td class="price">44.00</td>
                    </tr>
                    <tr>
                        <td class="tier-cell tier-1">1</td>
                        <td class="resource-name price-taranite">Taranite</td>
                        <td class="price">16.29</td>
                        <td class="price">35.21</td>
                    </tr>
                    <tr>
                        <td class="tier-cell tier-1">1</td>
                        <td class="resource-name">Gold</td>
                        <td class="price">3.20</td>
                        <td class="price">6.41</td>
                    </tr>
                    <tr>
                        <td class="tier-cell tier-2">2</td>
                        <td class="resource-name price-borase">Borase</td>
                        <td class="price">16.29</td>
                        <td class="price">35.21</td>
                    </tr>
                </tbody>
            </table>
        </div>
        <div class="price-table">
            <table>
                <thead>
                    <tr>
                        <th class="tier-col">T</th>
                        <th>Resource</th>
                        <th class="price-col">Raw</th>
                        <th class="price-col">Ref</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td class="tier-cell tier-2">2</td>
                        <td class="resource-name price-laranite">Laranite</td>
                        <td class="price">15.51</td>
                        <td class="price">30.94</td>
                    </tr>
                    <tr>
                        <td class="tier-cell tier-2">2</td>
                        <td class="resource-name price-agricium">Agricium</td>
                        <td class="price">13.75</td>
                        <td class="price">27.50</td>
                    </tr>
                    <tr>
                        <td class="tier-cell tier-2">2</td>
                        <td class="resource-name price-hephaestanite">Hephaestanite</td>
                        <td class="price">7.38</td>
                        <td class="price">15.85</td>
                    </tr>
                    <tr>
                        <td class="tier-cell tier-2">2</td>
                        <td class="resource-name">Beryl</td>
                        <td class="price">2.21</td>
                        <td class="price">4.35</td>
                    </tr>
                    <tr>
                        <td class="tier-cell tier-3">3</td>
                        <td class="resource-name">Ice</td>
                        <td class="price">0.50</td>
                        <td class="price">1.00</td>
                    </tr>
                    <tr>
                        <td class="tier-cell tier-3">3</td>
                        <td class="resource-name">Titanium</td>
                        <td class="price">4.47</td>
                        <td class="price">8.78</td>
                    </tr>
                    <tr>
                        <td class="tier-cell tier-3">3</td>
                        <td class="resource-name">Tungsten</td>
                        <td class="price">2.05</td>
                        <td class="price">4.06</td>
                    </tr>
                </tbody>
            </table>
        </div>
        <div class="price-table">
            <table>
                <thead>
                    <tr>
                        <th class="tier-col">T</th>
                        <th>Resource</th>
                        <th class="price-col">Raw</th>
                        <th class="price-col">Ref</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td class="tier-cell tier-4">4</td>
                        <td class="resource-name">Quartz</td>
                        <td class="price">0.78</td>
                        <td class="price">1.55</td>
                    </tr>
                    <tr>
                        <td class="tier-cell tier-4">4</td>
                        <td class="resource-name">Corundum</td>
                        <td class="price">1.35</td>
                        <td class="price">2.70</td>
                    </tr>
                    <tr>
                        <td class="tier-cell tier-4">4</td>
                        <td class="resource-name">Copper</td>
                        <td class="price">2.87</td>
                        <td class="price">6.16</td>
                    </tr>
                    <tr>
                        <td class="tier-cell tier-4">4</td>
                        <td class="resource-name">Tin</td>
                        <td class="price">0.55</td>
                        <td class="price">1.10</td>
                    </tr>
                    <tr>
                        <td class="tier-cell tier-4">4</td>
                        <td class="resource-name">Aluminum</td>
                        <td class="price">0.67</td>
                        <td class="price">1.30</td>
                    </tr>
                    <tr>
                        <td class="tier-cell tier-4">4</td>
                        <td class="resource-name">Silicon</td>
                        <td class="price">0.45</td>
                        <td class="price">0.90</td>
                    </tr>
                    <tr>
                        <td class="tier-cell tier-5">5</td>
                        <td class="resource-name">Diamond</td>
                        <td class="price">3.68</td>
                        <td class="price">7.35</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    <div class="close-hint">Numpad - zum Schließen | Verschiebbar mit Maus</div>
</body>
</html>
'''
        return html

    def create_overlay_html(self, signal, rock, minerals, auto_hide_seconds, overlay_width):
        """Erstelle HTML für SC-ähnliches Overlay"""

        stats = rock.get('stats', {})
        multima = rock.get('multima_factor', 1)

        mineral_bar_width = overlay_width - 150

        # Verwende die Stats direkt aus rock['stats']
        cluster_min = stats.get('cluster', {}).get('min', 1)
        cluster_max = stats.get('cluster', {}).get('max', 11)
        cluster_med = stats.get('cluster', {}).get('med', 6)

        rock_mass_min = stats.get('mass', {}).get('min', '0')
        rock_mass_max = stats.get('mass', {}).get('max', '182k')
        rock_mass_med = stats.get('mass', {}).get('med', '8.9k')

        instability_min = stats.get('instability', {}).get('min', 0)
        instability_max = stats.get('instability', {}).get('max', 711)
        instability_med = stats.get('instability', {}).get('med', 46)

        resistance_min = stats.get('resistance', {}).get('min', '0%')
        resistance_max = stats.get('resistance', {}).get('max', '64%')
        resistance_med = stats.get('resistance', {}).get('med', '16%')

        tier_colors = {
            1: '#808080',
            2: '#4169e1',
            3: '#9932cc',
            4: '#ffd700'
        }
        tier_color = tier_colors.get(rock.get('tier', 1), '#808080')

        html = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            background: rgba(15, 15, 20, 0.95);
            color: #ffffff;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 12px;
            line-height: 1.2;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            overflow: hidden;
            backdrop-filter: blur(5px);
        }}

        .header {{
            background: linear-gradient(90deg, rgba(30, 30, 40, 0.9), rgba(20, 20, 30, 0.9));
            padding: 10px 15px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.15);
            position: relative;
        }}

        .mineral-name {{
            font-size: 18px;
            font-weight: bold;
            color: {tier_color};
            margin-bottom: 3px;
        }}

        .signal-indicator {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .signal-dot {{
            width: 8px;
            height: 8px;
            background: #ffcc00;
            border-radius: 50%;
            box-shadow: 0 0 8px #ffcc00;
        }}

        .signal-value {{
            color: #ffcc00;
            font-weight: bold;
            font-size: 16px;
        }}

        .stats-section {{
            padding: 12px 15px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .stats-table {{
            width: 100%;
            border-collapse: collapse;
        }}

        .stats-table th {{
            text-align: right;
            color: #cccccc;
            font-weight: normal;
            padding: 3px 8px 3px 0;
            white-space: nowrap;
        }}

        .stats-table td {{
            text-align: center;
            color: #ffffff;
            font-weight: bold;
            padding: 3px 5px;
            min-width: 45px;
        }}

        .stats-header {{
            background: rgba(40, 40, 50, 0.7);
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }}

        .stats-header td {{
            color: #aaaaaa;
            font-size: 10px;
            padding: 5px 5px;
        }}

        .mineral-section {{
            padding: 8px 15px 10px 15px;
        }}

        .mineral-header {{
            color: #cccccc;
            font-weight: bold;
            margin-bottom: 8px;
            font-size: 11px;
        }}

        .mineral-list {{
            width: 100%;
        }}

        .mineral-table {{
            width: 100%;
            border-collapse: collapse;
            border-spacing: 0;
        }}

        .mineral-table td {{
            padding: 1px 0;
            border: none;
            vertical-align: middle;
        }}

        .mineral-bar-cell {{
            padding-right: 8px;
        }}

        .mineral-bar {{
            width: {mineral_bar_width}px;
            height: 16px;
            background: rgba(40, 40, 50, 0.8);
            border-radius: 2px;
            overflow: hidden;
            position: relative;
        }}

        .mineral-fill {{
            height: 100%;
            transition: width 0.3s ease;
            position: absolute;
            left: 0;
            top: 0;
        }}

        .mineral-name-in-bar {{
            position: absolute;
            left: 6px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 11px;
            font-weight: bold;
            white-space: nowrap;
            z-index: 1;
            color: #ffffff;
            text-shadow: 
                -1px -1px 0 #000,
                 1px -1px 0 #000,
                -1px  1px 0 #000,
                 1px  1px 0 #000,
                -1px  0   0 #000,
                 1px  0   0 #000,
                 0   -1px 0 #000,
                 0    1px 0 #000;
        }}

        .mineral-percentage-cell {{
            width: 40px;
            text-align: right;
        }}

        .mineral-percentage {{
            color: #ffffff;
            font-weight: bold;
            font-size: 11px;
        }}

        .close-indicator {{
            position: absolute;
            top: 5px;
            right: 8px;
            color: #888;
            font-size: 10px;
        }}

        .multima-indicator {{
            background: rgba(255, 165, 0, 0.2);
            border: 1px solid #ffa500;
            border-radius: 4px;
            padding: 2px 6px;
            margin-top: 5px;
            text-align: center;
            color: #ffa500;
            font-size: 10px;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="close-indicator">Auto-Hide {auto_hide_seconds}s</div>

    <div class="header">
        <div class="mineral-name">{rock['name']}</div>
        <div class="signal-indicator">
            <div class="signal-dot"></div>
            <span class="signal-value">{signal}</span>
        </div>
    </div>

    <div class="stats-section">
        <table class="stats-table">
            <tr class="stats-header">
                <th></th>
                <td>Min</td>
                <td>Max</td>
                <td>Med</td>
            </tr>
            <tr>
    <th>Cluster Rocks</th>
    <td>{cluster_min}</td>
    <td>{cluster_max}</td>
    <td>{cluster_med}</td>
</tr>
<tr>
    <th>Rock Mass (t)</th>
    <td>{rock_mass_min}</td>
    <td>{rock_mass_max}</td>
    <td>{rock_mass_med}</td>
</tr>
<tr>
    <th>Instability</th>
    <td>{instability_min}</td>
    <td>{instability_max}</td>
    <td>{instability_med}</td>
</tr>
<tr>
    <th>Resistance</th>
    <td>{resistance_min}</td>
    <td>{resistance_max}</td>
    <td>{resistance_med}</td>
</tr>
        </table>
    </div>

    <div class="mineral-section">
        <div class="mineral-header">Mineral Composition</div>
        <div class="mineral-list">
            <table class="mineral-table">
'''


        # ZEIGE MINERALIEN ALS TABELLE MIT Prob/Min/Max/Med (wie im Screenshot)
        ores = rock.get('ores', {})
        mineral_colors = {
            'QUANTANIUM': '#E91E63',
            'TARANITE': '#4CAF50',
            'BEXALITE': '#FF9800',
            'GOLD': '#FFD700',
            'AGRICIUM': '#8BC34A',
            'HEPHAESTANITE': '#FF5722',
            'TUNGSTEN': '#607D8B',
            'TITANIUM': '#9C27B0',
            'IRON': '#795548',
            'QUARTZ': '#E0E0E0',
            'CORUNDUM': '#F44336',
            'COPPER': '#FF5722',
            'ALUMINUM': '#9E9E9E',
            'BERYL': '#90EE90',
            'BORASE': '#8BC34A',
            'LARANITE': '#45B7D1',
            'ICE': '#87CEEB',
            'INERTMATERIAL': '#708090',
            'TIN': '#A9A9A9',
            'SILICON': '#778899',
            'RICCITE': '#FF6B6B',
            'STILERON': '#9370DB'
        }
        # Tabellenkopf
        html += f"""
            <tr>
                <th style="text-align: left; padding: 5px 3px; border-bottom: 2px solid rgba(0, 212, 255, 0.3); color: #7fb3d3; font-size: 0.7em;">Mineral</th>
                <th style="text-align: center; padding: 5px 3px; border-bottom: 2px solid rgba(0, 212, 255, 0.3); color: #7fb3d3; font-size: 0.7em;">Prob</th>
                <th style="text-align: center; padding: 5px 3px; border-bottom: 2px solid rgba(0, 212, 255, 0.3); color: #7fb3d3; font-size: 0.7em;">Min</th>
                <th style="text-align: center; padding: 5px 3px; border-bottom: 2px solid rgba(0, 212, 255, 0.3); color: #7fb3d3; font-size: 0.7em;">Max</th>
                <th style="text-align: center; padding: 5px 3px; border-bottom: 2px solid rgba(0, 212, 255, 0.3); color: #7fb3d3; font-size: 0.7em;">Med</th>
            </tr>
        """
        for ore_name, ore_data in ores.items():
            if ore_name == 'INERTMATERIAL':
                continue
            prob = int(round(ore_data.get('prob', 0) * 100))
            min_pct = int(round(ore_data.get('minPct', 0) * 100))
            max_pct = int(round(ore_data.get('maxPct', 0) * 100))
            med_pct = int(round(ore_data.get('medPct', 0) * 100))
            display_name = ore_name.title()
            color = mineral_colors.get(ore_name, '#ffffff')
            html += f"""
                <tr>
                    <td style="padding: 3px 3px;"><span style="color: {color}; font-weight: bold;">{display_name}</span></td>
                    <td style="text-align: center; padding: 3px 3px;">{prob}%</td>
                    <td style="text-align: center; padding: 3px 3px;">{min_pct}%</td>
                    <td style="text-align: center; padding: 3px 3px;">{max_pct}%</td>
                    <td style="text-align: center; padding: 3px 3px;">{med_pct}%</td>
                </tr>
            """


        html += '''
            </table>
        </div>
'''

        if multima > 1:
            html += f'''
        <div class="multima-indicator">
            {multima}x MULTIMA FORMATION - ENHANCED YIELD
        </div>
'''

        html += '''
    </div>
</body>
</html>
'''
        return html

    def get_cached_results(self, signal_value):
        """API: Hole gecachte Ergebnisse ohne neuen Scan"""
        try:
            signal_value = int(signal_value)
            matches = self.find_matching_rocks(signal_value)

            for match in matches:
                match['minerals'] = self.generate_mineral_composition(match)
                match['stats'] = self.calculate_rock_stats(match, signal_value)

            # Finde Timestamps aus aktueller System-Historie
            scan_history = self.get_current_history()
            timestamps = []
            for entry in scan_history:
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
        return self.get_current_history()

    def reset_scans(self):
        """API: Lösche Scan-Historie des aktuellen Systems"""
        self.set_current_history([])
        self.save_config()
        return {
            'success': True,
            'message': f'Scan-Historie für {self.current_system} wurde gelöscht'
        }

    def get_initial_state(self):
        """API: Hole initialen Status der Modi"""
        current_history = self.get_current_history()
        state = {
            'gaming_mode': self.gaming_mode,
            'overlay_enabled': self.config.get('overlay_enabled', True),
            'overlay_auto_hide_seconds': self.config.get('overlay_auto_hide_seconds', 10),
            'selected_system': self.current_system,
            'history': current_history
        }
        print(
            f"[DEBUG] Initial State wird geladen: System={self.current_system}, Historie={len(current_history)} Einträge")
        return state

    def change_system(self, system):
        """API: Wechsle zwischen Stanton und Pyro"""
        try:
            if system not in ['STANTON', 'PYRO']:
                return {'success': False, 'error': 'Ungültiges System'}

            old_system = self.current_system
            self.current_system = system
            self.rock_database = self.build_rock_database(system)
            self.config['selected_system'] = system
            self.save_config()

            # Hole Historie für das neue System
            new_history = self.get_current_history()

            print(f"[INFO] System gewechselt von {old_system} zu {system}")
            print(f"[DEBUG] Historie für {system}: {len(new_history)} Einträge")
            if len(new_history) > 0:
                print(f"[DEBUG] Erste Historie-Einträge: {new_history[0]}")

            return {
                'success': True,
                'system': system,
                'rocks_count': len(self.rock_database),
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

            self.config['overlay_auto_hide_seconds'] = seconds
            self.save_config()
            return {
                'success': True,
                'seconds': seconds,
                'message': f'Overlay-Timer auf {seconds} Sekunden gesetzt'
            }
        except (ValueError, TypeError) as e:
            return {'success': False, 'error': f'Ungültiger Wert: {e}'}

    def toggle_gaming_mode(self):
        """API: Gaming-Modus umschalten"""
        if not GLOBAL_HOTKEYS_AVAILABLE:
            return {'success': False, 'error': 'pynput nicht installiert'}

        if self.gaming_mode:
            self.gaming_mode = False
            if self.global_listener:
                try:
                    self.global_listener.stop()
                except Exception as e:
                    print(f"[WARNING] Listener konnte nicht gestoppt werden: {e}")
                finally:
                    self.global_listener = None
            self.save_config()
            return {'success': True, 'active': False, 'message': 'Gaming-Modus deaktiviert'}
        else:
            try:
                self.gaming_mode = True
                self.global_listener = keyboard.Listener(
                    on_press=self.on_global_key_press,
                    suppress=False
                )
                self.global_listener.start()
                self.save_config()
                return {'success': True, 'active': True, 'message': 'Gaming-Modus aktiviert'}
            except Exception as e:
                self.gaming_mode = False
                return {'success': False, 'error': str(e)}

    def pause_gaming_listener(self):
        """API: Pausiere Gaming-Listener temporär"""
        if self.gaming_mode and self.global_listener:
            try:
                self.global_listener.stop()
                self.global_listener = None
                print("[DEBUG] Gaming-Listener pausiert")
                return {'success': True}
            except Exception as e:
                print(f"[WARNING] Listener konnte nicht pausiert werden: {e}")
                return {'success': False, 'error': str(e)}
        return {'success': True}

    def resume_gaming_listener(self):
        """API: Setze Gaming-Listener fort"""
        if self.gaming_mode and not self.global_listener:
            try:
                self.global_listener = keyboard.Listener(
                    on_press=self.on_global_key_press,
                    suppress=False
                )
                self.global_listener.start()
                print("[DEBUG] Gaming-Listener fortgesetzt")
                return {'success': True}
            except Exception as e:
                print(f"[WARNING] Listener konnte nicht fortgesetzt werden: {e}")
                return {'success': False, 'error': str(e)}
        return {'success': True}

    def toggle_overlay(self):
        """API: Overlay ein/ausschalten"""
        self.config['overlay_enabled'] = not self.config.get('overlay_enabled', True)
        if not self.config['overlay_enabled']:
            self.hide_overlay()
        self.save_config()
        return {
            'success': True,
            'enabled': self.config['overlay_enabled'],
            'message': f"Overlay {'aktiviert' if self.config['overlay_enabled'] else 'deaktiviert'}"
        }

    def on_global_key_press(self, key):
        """Globale Tastatur-Eingaben für Gaming-Modus"""
        if not self.gaming_mode:
            return

        try:
            if key == keyboard.Key.f11:
                self.safe_evaluate_js("toggleGamingModeFromPython()")
                return

            if hasattr(key, 'vk'):
                vk = key.vk

                if 96 <= vk <= 105:
                    number = str(vk - 96)
                    js_code = f"addNumberFromGaming('{number}');"
                    self.safe_evaluate_js(js_code)
                    return

                elif 48 <= vk <= 57:
                    number = str(vk - 48)
                    js_code = f"addNumberFromGaming('{number}');"
                    self.safe_evaluate_js(js_code)
                    return

                elif vk == 107:
                    self.safe_evaluate_js("searchFromGaming();")
                    return

                elif vk == 109:
                    self.safe_evaluate_js("togglePriceListFromGaming();")
                    return

            if hasattr(key, 'char') and key.char and key.char.isdigit():
                number = key.char
                js_code = f"addNumberFromGaming('{number}');"
                self.safe_evaluate_js(js_code)
                return

            if hasattr(key, 'char') and key.char == '+':
                self.safe_evaluate_js("searchFromGaming();")
                return

            if hasattr(key, 'char') and key.char == '-':
                self.safe_evaluate_js("togglePriceListFromGaming();")
                return

            if key == keyboard.Key.esc:
                self.safe_evaluate_js("resetFromGaming();")
                return

            if key == keyboard.Key.backspace:
                self.safe_evaluate_js("backspaceFromGaming();")
                return

        except Exception as e:
            print(f"[ERROR] Gaming-Modus Tastaturverarbeitung fehlgeschlagen: {e}")


class StarCitizenMiningAnalyzer:
    def __init__(self):
        if not WEBVIEW_AVAILABLE:
            print("[ERROR] webview ist nicht installiert!")
            print("Installiere mit: pip install pywebview")
            return

        self.api = MiningAPI()
        self.create_overlay()

    def create_overlay(self):
        """Erstelle transparentes Overlay-Fenster"""

        html_content = '''
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Regolith Mining Analyzer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background: linear-gradient(135deg, rgba(26, 26, 46, 0.95), rgba(15, 52, 96, 0.95));
            color: #00d4ff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            overflow-x: hidden;
        }

        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(15, 52, 96, 0.3);
            border: 2px solid #00d4ff;
            border-radius: 10px;
        }

        .header h1 {
            font-size: 2.5em;
            background: linear-gradient(45deg, #00d4ff, #45b7d1);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }

        .controls {
            background: rgba(22, 33, 62, 0.8);
            border: 2px solid rgba(0, 212, 255, 0.3);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
        }

        .input-group {
            margin-bottom: 20px;
        }

        .input-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #00d4ff;
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
            font-family: 'Courier New', monospace;
        }

        #signalInput:focus {
            outline: none;
            border-color: #00d4ff;
            box-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
        }

        #systemSelect {
            width: 100%;
            padding: 15px;
            font-size: 1.2em;
            text-align: center;
            background: rgba(15, 20, 25, 0.9);
            border: 2px solid rgba(0, 212, 255, 0.5);
            border-radius: 8px;
            color: #00d4ff;
            font-weight: bold;
            cursor: pointer;
        }

        #systemSelect:focus {
            outline: none;
            border-color: #00d4ff;
            box-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
        }

        .timer-group {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 15px;
        }

        .timer-group label {
            color: #7fb3d3;
            font-size: 0.9em;
            white-space: nowrap;
        }

        #timerInput {
            width: 80px;
            padding: 8px;
            font-size: 1em;
            text-align: center;
            background: rgba(15, 20, 25, 0.9);
            border: 2px solid rgba(0, 212, 255, 0.5);
            border-radius: 5px;
            color: #00d4ff;
            font-family: 'Courier New', monospace;
        }

        #timerInput:focus {
            outline: none;
            border-color: #00d4ff;
        }

        .button-group {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin-top: 15px;
        }

        .btn {
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
        }

        .btn-gaming {
            background: #27ae60;
            color: white;
        }

        .btn-gaming:hover {
            background: #2ecc71;
            transform: translateY(-2px);
        }

        .btn-gaming.active {
            background: #e74c3c;
        }

        .btn-overlay {
            background: #9b59b6;
            color: white;
        }

        .btn-overlay:hover {
            background: #8e44ad;
            transform: translateY(-2px);
        }

        .btn-overlay.active {
            background: #2ecc71;
        }

        .history {
            background: rgba(22, 33, 62, 0.6);
            border: 2px solid rgba(0, 212, 255, 0.3);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 25px;
        }

        .history-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .history h3 {
            margin: 0;
            color: #00d4ff;
        }

        .btn-reset {
            padding: 6px 12px;
            background: #e74c3c;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 0.85em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .btn-reset:hover {
            background: #c0392b;
            transform: translateY(-1px);
        }

        .history-buttons {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .history-btn {
            padding: 8px 12px;
            background: rgba(15, 52, 96, 0.7);
            border: 1px solid rgba(0, 212, 255, 0.5);
            border-radius: 5px;
            color: #00d4ff;
            cursor: pointer;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            transition: all 0.2s ease;
        }

        .history-btn:hover {
            background: rgba(30, 90, 150, 0.8);
            transform: translateY(-1px);
        }

        .results {
            display: none;
        }

        .results.show {
            display: block;
        }

        .result-header {
            background: rgba(15, 52, 96, 0.8);
            border: 2px solid #00d4ff;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
        }

        .no-match {
            background: rgba(44, 24, 16, 0.9);
            border: 2px solid #ff6b6b;
            border-radius: 10px;
            padding: 30px;
            text-align: center;
            color: #ff6b6b;
        }

        .rock-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }

        .rock-card {
            background: rgba(22, 33, 62, 0.9);
            border: 3px solid;
            border-radius: 15px;
            padding: 20px;
            transition: all 0.3s ease;
            position: relative;
        }

        .rock-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }

        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 5px;
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }

        .pagination-btn {
            padding: 4px 8px;
            background: rgba(0, 212, 255, 0.2);
            border: 1px solid rgba(0, 212, 255, 0.4);
            border-radius: 3px;
            color: #00d4ff;
            cursor: pointer;
            font-size: 0.8em;
            transition: all 0.2s ease;
            min-width: 30px;
            text-align: center;
        }

        .pagination-btn:hover {
            background: rgba(0, 212, 255, 0.4);
            transform: translateY(-1px);
        }

        .pagination-btn.active {
            background: #00d4ff;
            color: #1a1a2e;
            font-weight: bold;
        }

        .pagination-btn.disabled {
            opacity: 0.4;
            cursor: not-allowed;
        }

        .pagination-ellipsis {
            color: #7fb3d3;
            padding: 0 5px;
        }

        .rock-header {
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 15px;
            text-align: center;
        }

        .rock-name {
            font-size: 1.4em;
            font-weight: bold;
            color: white;
        }

        .rock-info {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 15px;
        }

        .info-item {
            display: flex;
            justify-content: space-between;
            padding: 8px;
            background: rgba(15, 20, 25, 0.5);
            border-radius: 5px;
        }

        .info-label {
            color: #7fb3d3;
        }

        .info-value {
            font-weight: bold;
        }

        .signal-value {
            color: #00d4ff;
            font-family: 'Courier New', monospace;
        }

        .value-amount {
            color: #2ecc71;
        }

        .multima-badge {
            color: #f39c12;
            font-weight: bold;
        }

        .rock-description {
            background: rgba(15, 20, 25, 0.7);
            padding: 15px;
            border-radius: 8px;
            color: #b0b0b0;
            line-height: 1.4;
            margin-bottom: 15px;
        }

        .accuracy-bar {
            background: rgba(15, 20, 25, 0.7);
            border-radius: 10px;
            padding: 10px;
        }

        .accuracy-label {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            font-size: 0.9em;
        }

        .progress-bg {
            background: rgba(15, 20, 25, 0.8);
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #2ecc71, #27ae60);
            border-radius: 4px;
            transition: width 0.5s ease;
        }

        .tier-1 .rock-header { background: linear-gradient(45deg, #808080, #a0a0a0); }
        .tier-2 .rock-header { background: linear-gradient(45deg, #4169e1, #6fa8f5); }
        .tier-3 .rock-header { background: linear-gradient(45deg, #9932cc, #b965e0); }
        .tier-4 .rock-header { background: linear-gradient(45deg, #ffd700, #ffed4e); }

        .tier-1 { border-color: #808080; }
        .tier-2 { border-color: #4169e1; }
        .tier-3 { border-color: #9932cc; }
        .tier-4 { border-color: #ffd700; }

        .multima-alert {
            background: rgba(44, 62, 80, 0.9);
            border: 2px solid #f39c12;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            text-align: center;
            color: #f39c12;
            font-weight: bold;
        }

        .gaming-status {
            position: fixed;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.8);
            color: #00ff00;
            padding: 10px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            display: none;
        }

        .gaming-status.active {
            display: block;
        }

        .overlay-status {
            position: fixed;
            top: 40px;
            right: 10px;
            background: rgba(155, 89, 182, 0.8);
            color: #ffffff;
            padding: 8px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 10px;
            display: none;
        }

        .overlay-status.active {
            display: block;
        }

        .price-list {
            position: fixed;
            bottom: 20px;
            left: 20px;
            background: rgba(26, 26, 46, 0.9);
            border: 2px solid rgba(0, 212, 255, 0.4);
            border-radius: 10px;
            padding: 20px 30px;
            display: none;
            z-index: 1000;
            backdrop-filter: blur(5px);
        }

        .price-list.show {
            display: block;
        }

        .price-list h2 {
            text-align: center;
            margin-bottom: 15px;
            color: #00d4ff;
            font-size: 1.5em;
        }

        .price-tables {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }

        .price-table {
            min-width: 300px;
        }

        .price-table table {
            width: 100%;
            border-collapse: collapse;
        }

        .price-table th {
            padding: 8px;
            text-align: left;
            border-bottom: 2px solid rgba(0, 212, 255, 0.3);
            color: #7fb3d3;
            font-size: 0.9em;
        }

        .price-table td {
            padding: 6px 8px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .price-table .resource-name {
            font-weight: bold;
            text-shadow: 
                -1px -1px 0 #000,
                 1px -1px 0 #000,
                -1px  1px 0 #000,
                 1px  1px 0 #000;
        }

        .price-table .price {
            text-align: right;
            color: #b0b0b0;
        }

        .price-quantainium { color: #FFD700; }
        .price-bexalite { color: #90EE90; }
        .price-borase { color: #90EE90; }
        .price-taranite { color: #90EE90; }
        .price-laranite { color: #90EE90; }
        .price-agricium { color: #90EE90; }
        .price-hephaestanite { color: #ffffff; }
        .price-titanium { color: #ffffff; }
    </style>
</head>
<body tabindex="0">
    <div class="gaming-status" id="gamingStatus">
        GAMING-MODUS AKTIV - NUMPAD BEREIT
    </div>

    <div class="overlay-status" id="overlayStatus">
        SC-OVERLAY AKTIV
    </div>

    <div class="container">
        <div class="header">
            <h1>🛰️ REGOLITH MINING ANALYZER</h1>
            <p>Star Citizen Signal Detection System</p>
        </div>

        <div class="controls">
            <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 15px; align-items: start;">
                <div class="input-group">
                    <label for="signalInput">Signal Stärke eingeben:</label>
                    <input type="text" id="signalInput" placeholder="1800" maxlength="6" inputmode="numeric">
                </div>

                <div class="input-group">
                    <label for="systemSelect">System:</label>
                    <select id="systemSelect">
                        <option value="STANTON">STANTON</option>
                        <option value="PYRO">PYRO</option>
                    </select>
                </div>
            </div>

            <div class="timer-group">
                <label for="timerInput">Overlay Auto-Hide:</label>
                <input type="text" id="timerInput" min="1" max="300" value="10" maxlength="3" inputmode="numeric">
                <label>Sekunden</label>
            </div>

            <div class="button-group">
                <button id="gamingBtn" class="btn btn-gaming">🎮 GAMING-MODUS</button>
                <button id="overlayBtn" class="btn btn-overlay">🎯 SC-OVERLAY</button>
            </div>

            <p style="margin-top: 10px; color: #7fb3d3; font-size: 0.9em;">
                Eingabe: Numpad 0-9 | Numpad +: Suchen | Numpad -: Preisliste | ESC: Löschen<br>
                SC-Overlay: Zeigt Ergebnisse über Star Citizen
            </p>
        </div>

        <div class="history">
            <div class="history-header">
                <h3>📊 Letzte Scans:</h3>
                <button id="resetBtn" class="btn-reset">🗑️ RESET</button>
            </div>
            <div id="historyButtons" class="history-buttons">
            </div>
        </div>

        <div id="results" class="results">
        </div>

        <div id="priceList" class="price-list">
            <h2>Mineable Ore Prices</h2>
            <div class="price-tables">
                <div class="price-table">
                    <table>
                        <thead>
                            <tr>
                                <th>Resource</th>
                                <th>Price (Raw)</th>
                                <th>Price (Refined)</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td class="resource-name price-quantainium">Quantainium</td>
                                <td class="price">44.00</td>
                                <td class="price">88.00</td>
                            </tr>
                            <tr>
                                <td class="resource-name price-bexalite">Bexalite</td>
                                <td class="price">20.33</td>
                                <td class="price">44.00</td>
                            </tr>
                            <tr>
                                <td class="resource-name price-borase">Borase</td>
                                <td class="price">16.29</td>
                                <td class="price">35.21</td>
                            </tr>
                            <tr>
                                <td class="resource-name price-taranite">Taranite</td>
                                <td class="price">16.29</td>
                                <td class="price">35.21</td>
                            </tr>
                            <tr>
                                <td class="resource-name price-laranite">Laranite</td>
                                <td class="price">15.51</td>
                                <td class="price">30.94</td>
                            </tr>
                            <tr>
                                <td class="resource-name price-agricium">Agricium</td>
                                <td class="price">13.75</td>
                                <td class="price">27.50</td>
                            </tr>
                            <tr>
                                <td class="resource-name price-hephaestanite">Hephaestanite</td>
                                <td class="price">7.38</td>
                                <td class="price">15.85</td>
                            </tr>
                            <tr>
                                <td class="resource-name price-titanium">Titanium</td>
                                <td class="price">4.47</td>
                                <td class="price">8.78</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div class="price-table">
                    <table>
                        <thead>
                            <tr>
                                <th>Resource</th>
                                <th>Price (Raw)</th>
                                <th>Price (Refined)</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td class="resource-name">Diamond</td>
                                <td class="price">3.68</td>
                                <td class="price">7.35</td>
                            </tr>
                            <tr>
                                <td class="resource-name">Gold</td>
                                <td class="price">3.20</td>
                                <td class="price">6.41</td>
                            </tr>
                            <tr>
                                <td class="resource-name">Copper</td>
                                <td class="price">2.87</td>
                                <td class="price">6.16</td>
                            </tr>
                            <tr>
                                <td class="resource-name">Beryl</td>
                                <td class="price">2.21</td>
                                <td class="price">4.35</td>
                            </tr>
                            <tr>
                                <td class="resource-name">Tungsten</td>
                                <td class="price">2.05</td>
                                <td class="price">4.06</td>
                            </tr>
                            <tr>
                                <td class="resource-name">Corundum</td>
                                <td class="price">1.35</td>
                                <td class="price">2.70</td>
                            </tr>
                            <tr>
                                <td class="resource-name">Quartz</td>
                                <td class="price">0.78</td>
                                <td class="price">1.55</td>
                            </tr>
                            <tr>
                                <td class="resource-name">Aluminum</td>
                                <td class="price">0.67</td>
                                <td class="price">1.30</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentInput = '';
        let gamingMode = false;
        let overlayEnabled = true;
        let overlayTimer = 10;
        let priceListVisible = false;
        let cardPages = {};
        let currentSystem = 'STANTON';
        let resumeListenerTimer = null; // Timer für verzögertes Resume

        const signalInput = document.getElementById('signalInput');
        const timerInput = document.getElementById('timerInput');
        const systemSelect = document.getElementById('systemSelect');
        const results = document.getElementById('results');
        const historyButtons = document.getElementById('historyButtons');
        const gamingBtn = document.getElementById('gamingBtn');
        const overlayBtn = document.getElementById('overlayBtn');
        const resetBtn = document.getElementById('resetBtn');
        const gamingStatus = document.getElementById('gamingStatus');
        const overlayStatus = document.getElementById('overlayStatus');
        const priceList = document.getElementById('priceList');

        document.addEventListener('keydown', handleKeyPress);
        gamingBtn.addEventListener('click', toggleGamingMode);
        overlayBtn.addEventListener('click', toggleOverlay);
        resetBtn.addEventListener('click', resetScans);
        timerInput.addEventListener('change', updateOverlayTimer);
        systemSelect.addEventListener('change', changeSystem);

        // Focus-Management für Gaming-Modus mit verzögertem Resume
        signalInput.addEventListener('focus', () => {
            // Cancel pending resume timer
            if (resumeListenerTimer) {
                clearTimeout(resumeListenerTimer);
                resumeListenerTimer = null;
            }
            if (gamingMode) {
                console.log('[DEBUG] Input fokussiert - pausiere Gaming-Listener');
                pywebview.api.pause_gaming_listener();
            }
        });

        signalInput.addEventListener('blur', () => {
            // Synchronisiere currentInput beim Verlassen des Feldes
            currentInput = signalInput.value;
            if (gamingMode) {
                // Verzögertes Resume - wird gecancelt wenn neues Input fokussiert wird
                resumeListenerTimer = setTimeout(() => {
                    console.log('[DEBUG] Input verliert Focus - setze Gaming-Listener fort (verzögert)');
                    pywebview.api.resume_gaming_listener();
                    resumeListenerTimer = null;
                }, 150); // 150ms Verzögerung
            }
        });

        timerInput.addEventListener('focus', () => {
            // Cancel pending resume timer
            if (resumeListenerTimer) {
                clearTimeout(resumeListenerTimer);
                resumeListenerTimer = null;
            }
            if (gamingMode) {
                console.log('[DEBUG] Timer-Input fokussiert - pausiere Gaming-Listener');
                pywebview.api.pause_gaming_listener();
            }
        });

        timerInput.addEventListener('blur', () => {
            if (gamingMode) {
                // Verzögertes Resume - wird gecancelt wenn neues Input fokussiert wird
                resumeListenerTimer = setTimeout(() => {
                    console.log('[DEBUG] Timer-Input verliert Focus - setze Gaming-Listener fort (verzögert)');
                    pywebview.api.resume_gaming_listener();
                    resumeListenerTimer = null;
                }, 150); // 150ms Verzögerung
            }
        });

        systemSelect.addEventListener('focus', () => {
            // Cancel pending resume timer
            if (resumeListenerTimer) {
                clearTimeout(resumeListenerTimer);
                resumeListenerTimer = null;
            }
            if (gamingMode) {
                console.log('[DEBUG] System-Select fokussiert - pausiere Gaming-Listener');
                pywebview.api.pause_gaming_listener();
            }
        });

        systemSelect.addEventListener('blur', () => {
            if (gamingMode) {
                // Verzögertes Resume - wird gecancelt wenn neues Input fokussiert wird
                resumeListenerTimer = setTimeout(() => {
                    console.log('[DEBUG] System-Select verliert Focus - setze Gaming-Listener fort (verzögert)');
                    pywebview.api.resume_gaming_listener();
                    resumeListenerTimer = null;
                }, 150); // 150ms Verzögerung
            }
        });

        // Nur Zahlen in Input-Feldern zulassen
        signalInput.addEventListener('input', (e) => {
            // Entferne alle nicht-numerischen Zeichen
            e.target.value = e.target.value.replace(/[^0-9]/g, '');
            // NICHT mehr synchronisieren während der Eingabe - nur beim blur
        });

        timerInput.addEventListener('input', (e) => {
            // Entferne alle nicht-numerischen Zeichen
            e.target.value = e.target.value.replace(/[^0-9]/g, '');
        });

        function handleKeyPress(event) {
            const target = event.target;
            const key = event.key;

            // Komplett ignorieren für SELECT und INPUT-Felder (der Gaming-Listener ist pausiert)
            if (target.tagName === 'SELECT' || target.tagName === 'INPUT') {
                return; // Lasse normale Eingabe zu
            }

            // Nur für den Body/Document (außerhalb von Inputs)
            if ((key >= '0' && key <= '9') || 
                (key.startsWith('Numpad') && key.length === 7 && !isNaN(key.slice(-1)))) {

                let number;
                if (key.startsWith('Numpad')) {
                    number = key.slice(-1);
                } else {
                    number = key;
                }

                currentInput += number;
                updateDisplay();
                event.preventDefault();
            }
            else if (key === '+' || key === 'NumpadAdd') {
                if (currentInput) {
                    searchSignal(currentInput);
                    currentInput = '';
                    updateDisplay();
                }
                event.preventDefault();
            }
            else if (key === '-' || key === 'NumpadSubtract') {
                togglePriceList();
                event.preventDefault();
            }
            else if (key === 'Backspace') {
                currentInput = currentInput.slice(0, -1);
                updateDisplay();
                event.preventDefault();
            }
            else if (key === 'Escape') {
                currentInput = '';
                updateDisplay();
                hideResults();
                event.preventDefault();
            }
        }

        function updateDisplay() {
            signalInput.value = currentInput;
        }

        function updateOverlayTimer() {
            const seconds = parseInt(timerInput.value);
            if (seconds >= 1 && seconds <= 300) {
                pywebview.api.set_overlay_timer(seconds).then(result => {
                    if (result.success) {
                        overlayTimer = seconds;
                        console.log('Overlay-Timer aktualisiert:', seconds, 's');
                    } else {
                        alert('Fehler: ' + result.error);
                        timerInput.value = overlayTimer;
                    }
                });
            } else {
                alert('Timer muss zwischen 1 und 300 Sekunden sein');
                timerInput.value = overlayTimer;
            }
        }

        function changeSystem() {
            const newSystem = systemSelect.value;
            console.log('[DEBUG] Wechsle System zu:', newSystem);
            pywebview.api.change_system(newSystem).then(result => {
                console.log('[DEBUG] change_system Antwort:', result);
                if (result.success) {
                    currentSystem = newSystem;
                    console.log('[INFO] System gewechselt zu:', newSystem, '(' + result.rocks_count + ' Rocks)');
                    console.log('[DEBUG] Historie empfangen:', result.history ? result.history.length : 0, 'Einträge');
                    if (result.history && result.history.length > 0) {
                        console.log('[DEBUG] Erste Historie:', result.history[0]);
                    }
                    hideResults();
                    // Lade Historie für das neue System
                    updateHistory(result.history);
                } else {
                    alert('Fehler beim Systemwechsel: ' + result.error);
                    systemSelect.value = currentSystem;
                }
            }).catch(err => {
                console.error('[ERROR] Systemwechsel fehlgeschlagen:', err);
            });
        }

        function searchSignal(signal) {
            pywebview.api.search_signal(signal).then(result => {
                if (result.success) {
                    displayResults(result);
                    updateHistory(result.history);
                } else {
                    alert('Fehler: ' + result.error);
                }
            });
        }

        function displayResults(result) {
            const signal = result.signal;
            const matches = result.matches;
            const timestamps = result.timestamps;

            if (matches.length === 0) {
                results.innerHTML = `
                    <div class="no-match">
                        <h2>⚠️ KEIN MATCH GEFUNDEN</h2>
                        <p>Kein bekanntes Mineral mit Signal ${signal} ±50</p>
                    </div>
                `;
            } else {
                let html = `
                    <div class="result-header">
                        <h2>🔍 SCAN ERGEBNISSE FÜR SIGNAL ${signal}</h2>
                `;

                if (matches.length > 1) {
                    html += '<p style="color: #2ecc71; font-weight: bold; margin-top: 5px;">🎯 MULTIMA-FORMATION ERKANNT!</p>';
                }

                const hasMultima = matches.some(rock => rock.multima_factor > 1);
                if (hasMultima) {
                    html += '<div class="multima-alert">⚡ HOCHKONZENTRIERTE MULTIMA-SIGNALE ERKANNT!</div>';
                }

                html += '</div><div class="rock-grid">';

                matches.forEach(rock => {
                    html += createRockCard(rock, timestamps);
                });

                html += '</div>';
                results.innerHTML = html;
            }

            results.classList.add('show');
        }

        function createRockCard(rock, timestamps) {
            const tierClass = `tier-${rock.tier}`;
            const isMultima = rock.multima_factor > 1;
            const cardId = `card-${rock.signal}`;

            if (!cardPages[cardId]) {
                cardPages[cardId] = 1;
            }

            const currentPage = cardPages[cardId];
            const itemsPerPage = 10;
            const totalPages = Math.ceil(timestamps.length / itemsPerPage);

            const startIndex = (currentPage - 1) * itemsPerPage;
            const endIndex = Math.min(startIndex + itemsPerPage, timestamps.length);
            const displayTimestamps = timestamps.slice(startIndex, endIndex).reverse();

            let timestampList = '';
            if (displayTimestamps && displayTimestamps.length > 0) {
                timestampList = displayTimestamps.map((ts, index) => {
                    const globalIndex = timestamps.length - startIndex - index;
                    return `<div style="padding: 3px 0; font-size: 0.85em;">
                        <span style="color: #00d4ff; font-weight: bold;">#${globalIndex}</span>
                        <span style="color: #b0b0b0;"> → ${ts}</span>
                    </div>`;
                }).join('');
            }

            let pagination = '';
            if (totalPages > 1) {
                pagination = createPagination(currentPage, totalPages, cardId);
            }

            const stats = rock.stats || {};
            const statsTable = `
    <div style="margin-top: 15px; padding: 10px; background: rgba(15, 20, 25, 0.5); border-radius: 5px;">
        <div style="color: #00d4ff; font-weight: bold; margin-bottom: 8px; font-size: 0.9em;">
            📊 Gesteins-Statistiken:
        </div>
        <table style="width: 100%; font-size: 0.85em;">
            <tr style="background: rgba(40, 40, 50, 0.7); border-bottom: 1px solid rgba(255, 255, 255, 0.2);">
                <th style="text-align: left; padding: 5px; color: #7fb3d3;"></th>
                <th style="text-align: center; padding: 5px; color: #aaaaaa;">Min</th>
                <th style="text-align: center; padding: 5px; color: #aaaaaa;">Max</th>
                <th style="text-align: center; padding: 5px; color: #aaaaaa;">Med</th>
            </tr>
            <tr>
                <td style="padding: 5px; color: #cccccc;">Cluster Rocks</td>
                <td style="text-align: center; padding: 5px; color: #ffffff;">${stats.cluster?.min || 1}</td>
                <td style="text-align: center; padding: 5px; color: #ffffff;">${stats.cluster?.max || 11}</td>
                <td style="text-align: center; padding: 5px; color: #ffffff;">${stats.cluster?.med || 6}</td>
            </tr>
            <tr>
                <td style="padding: 5px; color: #cccccc;">Rock Mass (t)</td>
                <td style="text-align: center; padding: 5px; color: #ffffff;">${stats.mass?.min || '0'}</td>
                <td style="text-align: center; padding: 5px; color: #ffffff;">${stats.mass?.max || '182k'}</td>
                <td style="text-align: center; padding: 5px; color: #ffffff;">${stats.mass?.med || '8.9k'}</td>
            </tr>
            <tr>
                <td style="padding: 5px; color: #cccccc;">Instability</td>
                <td style="text-align: center; padding: 5px; color: #ffffff;">${stats.instability?.min || 0}</td>
                <td style="text-align: center; padding: 5px; color: #ffffff;">${stats.instability?.max || 711}</td>
                <td style="text-align: center; padding: 5px; color: #ffffff;">${stats.instability?.med || 46}</td>
            </tr>
            <tr>
                <td style="padding: 5px; color: #cccccc;">Resistance</td>
                <td style="text-align: center; padding: 5px; color: #ffffff;">${stats.resistance?.min || '0%'}</td>
                <td style="text-align: center; padding: 5px; color: #ffffff;">${stats.resistance?.max || '64%'}</td>
                <td style="text-align: center; padding: 5px; color: #ffffff;">${stats.resistance?.med || '16%'}</td>
            </tr>
        </table>
    </div>
`;

            let mineralComposition = '';
            if (rock.minerals && rock.minerals.length > 0) {
                const mineralBars = rock.minerals.map(([name, percentage, color]) => `
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                        <div style="flex: 1; background: rgba(40, 40, 50, 0.8); height: 16px; border-radius: 2px; position: relative; overflow: hidden;">
                            <div style="position: absolute; left: 0; top: 0; height: 100%; background: ${color}; width: ${percentage}%;"></div>
                            <span style="position: absolute; left: 6px; top: 50%; transform: translateY(-50%); font-size: 11px; font-weight: bold; color: #ffffff; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000;">
                                ${name}
                            </span>
                        </div>
                        <span style="min-width: 35px; text-align: right; font-size: 11px; color: #ffffff; font-weight: bold;">
                            ${percentage}%
                        </span>
                    </div>
                `).join('');

                mineralComposition = `
                    <div style="margin-top: 15px; padding: 10px; background: rgba(15, 20, 25, 0.5); border-radius: 5px;">
                        <div style="color: #00d4ff; font-weight: bold; margin-bottom: 8px; font-size: 0.9em;">
                            ⚗️ Mineralzusammensetzung:
                        </div>
                        ${mineralBars}
                    </div>
                `;
            }

            return `
                <div class="rock-card ${tierClass}" style="border-color: ${rock.color}40;">
                    <div class="rock-header">
                        <div class="rock-name">
                            ${isMultima ? '⚡' : '🪨'} ${rock.name}
                            ${!isMultima ? `(Tier ${rock.tier})` : ''}
                        </div>
                    </div>

                    <div class="rock-info">
                        <div class="info-item">
                            <span class="info-label">Signal:</span>
                            <span class="info-value signal-value">${rock.signal}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Wert:</span>
                            <span class="info-value value-amount">${rock.value} aUEC/SCU</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Typ:</span>
                            <span class="info-value" style="color: #45b7d1;">${rock.type}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">${isMultima ? 'Multima:' : 'Seltenheit:'}</span>
                            <span class="info-value ${isMultima ? 'multima-badge' : ''}" style="color: #ffcc5c;">
                                ${isMultima ? `${rock.multima_factor}x MULTIMA` : rock.rarity}
                            </span>
                        </div>
                    </div>

                    <div class="rock-description">
                        ${rock.description}
                    </div>

                    <div class="accuracy-bar">
                        <div class="accuracy-label">
                            <span>Genauigkeit:</span>
                            <span style="color: #2ecc71;">${rock.accuracy}%</span>
                        </div>
                        <div class="progress-bg">
                            <div class="progress-fill" style="width: ${rock.accuracy}%;"></div>
                        </div>
                    </div>

                    ${statsTable}
                    ${mineralComposition}

                    ${timestampList ? `
                    <div style="margin-top: 10px; padding: 10px; background: rgba(15, 20, 25, 0.6); border-radius: 5px; border-left: 3px solid #00d4ff;">
                        <div style="color: #00d4ff; font-weight: bold; margin-bottom: 5px; font-size: 0.9em;">
                            🕒 Scan-Historie (${timestamps.length} Scans):
                        </div>
                        <div>
                            ${timestampList}
                        </div>
                        ${pagination}
                    </div>
                    ` : ''}
                </div>
            `;
        }

        function createPagination(currentPage, totalPages, cardId) {
            let pages = [];

            pages.push(1);

            if (currentPage > 3) {
                pages.push('...');
            }

            for (let i = Math.max(2, currentPage - 1); i <= Math.min(totalPages - 1, currentPage + 1); i++) {
                if (!pages.includes(i)) {
                    pages.push(i);
                }
            }

            if (currentPage < totalPages - 2) {
                pages.push('...');
            }

            if (totalPages > 1 && !pages.includes(totalPages)) {
                pages.push(totalPages);
            }

            let html = '<div class="pagination">';

            pages.forEach(page => {
                if (page === '...') {
                    html += '<span class="pagination-ellipsis">...</span>';
                } else {
                    const isActive = page === currentPage;
                    html += `<button class="pagination-btn ${isActive ? 'active' : ''}" 
                             onclick="changePage('${cardId}', ${page})">${page}</button>`;
                }
            });

            html += '</div>';
            return html;
        }

        function changePage(cardId, page) {
            cardPages[cardId] = page;
            const signal = cardId.replace('card-', '');
            searchSignal(signal);
        }

        function updateHistory(history) {
            historyButtons.innerHTML = '';
            history.forEach(item => {
                const btn = document.createElement('button');
                btn.className = 'history-btn';
                btn.textContent = `${item.signal} (${item.count})`;
                btn.onclick = () => {
                    showCachedResults(item.signal.toString());
                };
                historyButtons.appendChild(btn);
            });
        }

        function showCachedResults(signal) {
            pywebview.api.get_cached_results(signal).then(result => {
                if (result.success) {
                    displayResults(result);
                } else {
                    alert('Fehler: ' + result.error);
                }
            });
        }

        function hideResults() {
            results.classList.remove('show');
        }

        function togglePriceList() {
            pywebview.api.toggle_price_overlay().then(result => {
                if (result.success) {
                    priceListVisible = result.visible;
                    console.log('Preis-Overlay:', priceListVisible ? 'geöffnet' : 'geschlossen');
                } else {
                    console.error('Fehler beim Toggle Preis-Overlay:', result.error);
                }
            }).catch(err => {
                console.error('Fehler beim Toggle Preis-Overlay:', err);
            });
        }

        function toggleGamingMode() {
            pywebview.api.toggle_gaming_mode().then(result => {
                if (result.success) {
                    updateGamingUI(result.active);
                } else {
                    alert('Fehler: ' + result.error);
                }
            });
        }

        function updateGamingUI(active) {
            gamingMode = active;
            gamingBtn.textContent = active ? '🔴 GAMING AKTIV' : '🎮 GAMING-MODUS';
            gamingBtn.className = active ? 'btn btn-gaming active' : 'btn btn-gaming';

            if (active) {
                gamingStatus.classList.add('active');
            } else {
                gamingStatus.classList.remove('active');
            }
        }

        function updateOverlayUI(enabled) {
            overlayEnabled = enabled;
            overlayBtn.textContent = enabled ? '🎯 SC-OVERLAY AKTIV' : '🎯 SC-OVERLAY';
            overlayBtn.className = enabled ? 'btn btn-overlay active' : 'btn btn-overlay';

            if (enabled) {
                overlayStatus.classList.add('active');
            } else {
                overlayStatus.classList.remove('active');
            }
        }

        function toggleOverlay() {
            pywebview.api.toggle_overlay().then(result => {
                if (result.success) {
                    updateOverlayUI(result.enabled);
                } else {
                    alert('Fehler: ' + result.error);
                }
            });
        }

        function resetScans() {
            if (confirm('Möchtest du wirklich alle Scan-Historie löschen?')) {
                pywebview.api.reset_scans().then(result => {
                    if (result.success) {
                        historyButtons.innerHTML = '';
                        console.log('Scan-Historie gelöscht');
                    } else {
                        alert('Fehler beim Löschen: ' + result.error);
                    }
                }).catch(err => {
                    console.error('Fehler beim Reset:', err);
                    alert('Fehler beim Löschen der Historie');
                });
            }
        }

        function addNumberFromGaming(number) {
            currentInput += number;
            updateDisplay();
        }

        function searchFromGaming() {
            if (currentInput) {
                searchSignal(currentInput);
                currentInput = '';
                updateDisplay();
            }
        }

        function togglePriceListFromGaming() {
            togglePriceList();
        }

        function resetFromGaming() {
            currentInput = '';
            updateDisplay();
            hideResults();
        }

        function backspaceFromGaming() {
            currentInput = currentInput.slice(0, -1);
            updateDisplay();
        }

        function toggleGamingModeFromPython() {
            toggleGamingMode();
        }

        function initializeApp() {
            if (typeof pywebview === 'undefined' || !pywebview.api) {
                console.log('Warte auf pywebview API...');
                setTimeout(initializeApp, 100);
                return;
            }

            console.log('pywebview API verfügbar, initialisiere App...');
            document.body.focus();

            pywebview.api.get_history().then(history => {
                console.log('Historie geladen:', history);
                updateHistory(history);
            }).catch(err => {
                console.error('Fehler beim Laden der Historie:', err);
            });

            pywebview.api.get_initial_state().then(state => {
                console.log('Initial State erfolgreich geladen:', state);

                gamingMode = state.gaming_mode;
                updateGamingUI(state.gaming_mode);

                overlayEnabled = state.overlay_enabled;
                updateOverlayUI(state.overlay_enabled);

                overlayTimer = state.overlay_auto_hide_seconds;
                timerInput.value = overlayTimer;

                currentSystem = state.selected_system || 'STANTON';
                systemSelect.value = currentSystem;

                console.log('UI aktualisiert - Gaming:', gamingMode, 'Overlay:', overlayEnabled, 'Timer:', overlayTimer, 's', 'System:', currentSystem);
            }).catch(err => {
                console.error('Fehler beim Laden des Initial State:', err);
                updateGamingUI(false);
                updateOverlayUI(true);
                timerInput.value = 10;
                systemSelect.value = 'STANTON';
            });
        }

        window.addEventListener('load', initializeApp);
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
            resizable=True,
            on_top=False,
            transparent=False
        )


def main():
    if not WEBVIEW_AVAILABLE:
        return

    analyzer = StarCitizenMiningAnalyzer()
    webview.start(debug=False)

    try:
        analyzer.api.save_config()
        analyzer.api.hide_overlay()
        if analyzer.api.global_listener:
            analyzer.api.global_listener.stop()
    except Exception as e:
        print(f"[WARNING] Cleanup fehlgeschlagen: {e}")


if __name__ == "__main__":
    main()