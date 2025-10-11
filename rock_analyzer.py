import json
import os


class RockAnalyzer:
    """Analysiert Gesteine basierend auf Signal-Werten"""

    def __init__(self):
        self.rocks_data = self.load_rocks_json()
        self.rock_database = {}

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
        """Erstelle Rock-Datenbank für ein System"""
        database = []

        if not self.rocks_data or system not in self.rocks_data:
            print(f"[ERROR] System {system} nicht in rocks.json gefunden!")
            return database

        system_data = self.rocks_data[system]

        # Definiere Signal-Werte und Eigenschaften für jeden Rock-Typ
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
        self.rock_database = database
        return database

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
        """Generiere realistische Mineralzusammensetzung"""
        ores = rock.get('ores', {})

        if not ores:
            return []

        # Mineral-Farben
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

            # Niedrigere Schwelle (3% statt 5%)
            if prob > 0.03 and med_pct > 0:
                percentage = int(med_pct * 100)
                if percentage > 0:
                    display_name = ore_name.title()
                    color = mineral_colors.get(ore_name, '#808080')
                    all_minerals.append((display_name, percentage, color, prob))

        # Sortiere nach medPct (Prozentsatz) absteigend
        all_minerals.sort(key=lambda x: x[1], reverse=True)

        # Nimm nur die Top 10 Mineralien
        composition = [(name, pct, color) for name, pct, color, _ in all_minerals[:10]]

        # Multima-Boost
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

    def calculate_rock_stats(self, rock, signal):
        """Berechne Stats für Rock"""
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