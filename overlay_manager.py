import threading
import time

try:
    import webview

    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False
    print("[ERROR] webview nicht installiert!")


class OverlayManager:
    """Verwaltet alle Overlays (SC-Overlay und Preis-Overlay)"""

    def __init__(self, config_manager):
        self.config = config_manager

        # Overlay-Status
        self.overlay_window = None
        self.overlay_lock = threading.Lock()
        self.hide_timer = None

        # Preis-Overlay
        self.price_overlay_window = None
        self.price_overlay_lock = threading.Lock()

    def show_overlay(self, signal, rock, minerals):
        """Zeige SC-ähnliches Overlay über dem Spiel"""
        if not WEBVIEW_AVAILABLE:
            return

        try:
            self.hide_overlay()

            auto_hide_seconds = self.config.config.get('overlay_auto_hide_seconds', 10)

            max_mineral_name_length = max(len(name) for name, _, _ in minerals) if minerals else 10
            overlay_width = min(420, max(350, 350 + (max_mineral_name_length - 10) * 2))

            overlay_html = self.create_overlay_html(signal, rock, minerals, auto_hide_seconds, overlay_width)

            # Höhe berechnen
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
                    x=self.config.config.get('overlay_position', {}).get('x', 20),
                    y=self.config.config.get('overlay_position', {}).get('y', 20),
                    min_size=(320, 300),
                    resizable=False,
                    on_top=True,
                    transparent=True,
                    frameless=True,
                    shadow=False
                )

            # Auto-Resize
            def _autofit_overlay(attempt=0, last_height=0):
                try:
                    js = '(function(){var b=document.body, d=document.documentElement; return Math.ceil(Math.max(b.scrollHeight, d.scrollHeight));})()'
                    h = self.overlay_window.evaluate_js(js)
                    if h is None:
                        h = 0
                    try:
                        h = int(float(h))
                    except Exception:
                        h = 0

                    min_h = 300
                    max_h = 1600
                    target_h = max(min_h, min(max_h, h))

                    if target_h and abs(target_h - last_height) > 2:
                        self.overlay_window.resize(overlay_width, target_h)
                        last_height = target_h

                    if attempt < 10:
                        threading.Timer(0.15, lambda: _autofit_overlay(attempt + 1, last_height)).start()
                except Exception as e:
                    print(f"[WARN] Auto-resize failed: {e}")

            threading.Timer(0.2, _autofit_overlay).start()

            # Auto-Hide Timer
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

    def toggle_price_overlay(self):
        """Zeige/Verstecke Preisliste als freistehendes Overlay"""
        with self.price_overlay_lock:
            if self.price_overlay_window:
                # Speichere Position vor dem Schließen
                self._save_price_overlay_position()
                try:
                    self.price_overlay_window.destroy()
                    print("[INFO] Preis-Overlay geschlossen")
                except Exception as e:
                    print(f"[WARNING] Preis-Overlay konnte nicht geschlossen werden: {e}")
                finally:
                    self.price_overlay_window = None
                return {'success': True, 'visible': False}
            else:
                # Öffne das Overlay
                try:
                    price_html = self.create_price_overlay_html()

                    window_width = 720
                    window_height = 380

                    price_pos = self.config.config.get('price_overlay_position', None)

                    if price_pos is None:
                        # Erste Anzeige: Unten mittig
                        try:
                            screen = webview.screens[0]
                            screen_width = screen.width
                            screen_height = screen.height
                            x = (screen_width - window_width) // 2
                            y = screen_height - window_height - 50
                        except:
                            x = 400
                            y = 600
                    else:
                        x = price_pos.get('x', 400)
                        y = price_pos.get('y', 600)

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

                    threading.Timer(0.5, self._track_price_overlay_position).start()

                    print(f"[INFO] Preis-Overlay geöffnet at x={x}, y={y}")
                    return {'success': True, 'visible': True}
                except Exception as e:
                    print(f"[ERROR] Preis-Overlay konnte nicht erstellt werden: {e}")
                    return {'success': False, 'error': str(e)}

    def _save_price_overlay_position(self):
        """Speichere Position des Preis-Overlays"""
        if self.price_overlay_window:
            try:
                x = self.price_overlay_window.x
                y = self.price_overlay_window.y
                self.config.config['price_overlay_position'] = {'x': x, 'y': y}
                print(f"[INFO] Preis-Overlay Position gespeichert: x={x}, y={y}")
            except Exception as e:
                print(f"[WARNING] Position konnte nicht gespeichert werden: {e}")

    def _track_price_overlay_position(self):
        """Tracke Position-Änderungen des Preis-Overlays"""
        last_x, last_y = None, None
        check_count = 0

        while self.price_overlay_window is not None:
            try:
                current_x = self.price_overlay_window.x
                current_y = self.price_overlay_window.y

                if (last_x is not None and last_y is not None):
                    if (current_x != last_x or current_y != last_y):
                        self._save_price_overlay_position()
                        print(f"[DEBUG] Position geändert: {current_x}, {current_y}")

                last_x = current_x
                last_y = current_y

                check_count += 1
                if check_count > 20:
                    time.sleep(2)
                else:
                    time.sleep(0.5)

            except Exception as e:
                print(f"[DEBUG] Position-Tracking beendet: {e}")
                break

    def create_overlay_html(self, signal, rock, minerals, auto_hide_seconds, overlay_width):
        """Erstelle HTML für SC-ähnliches Overlay"""

        stats = rock.get('stats', {})
        multima = rock.get('multima_factor', 1)

        mineral_bar_width = overlay_width - 150

        # Stats extrahieren
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

        # HTML Code (gekürzt für Lesbarkeit - im echten Code ist das der komplette HTML-String)
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
        <table style="width: 100%; border-collapse: collapse;">
'''

        # Mineralien als Tabelle hinzufügen
        ores = rock.get('ores', {})
        mineral_colors_dict = {
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

        html += '''
            <tr>
                <th style="text-align: left; padding: 5px 3px; border-bottom: 2px solid rgba(0, 212, 255, 0.3); color: #7fb3d3; font-size: 0.7em;">Mineral</th>
                <th style="text-align: center; padding: 5px 3px; border-bottom: 2px solid rgba(0, 212, 255, 0.3); color: #7fb3d3; font-size: 0.7em;">Prob</th>
                <th style="text-align: center; padding: 5px 3px; border-bottom: 2px solid rgba(0, 212, 255, 0.3); color: #7fb3d3; font-size: 0.7em;">Min</th>
                <th style="text-align: center; padding: 5px 3px; border-bottom: 2px solid rgba(0, 212, 255, 0.3); color: #7fb3d3; font-size: 0.7em;">Max</th>
                <th style="text-align: center; padding: 5px 3px; border-bottom: 2px solid rgba(0, 212, 255, 0.3); color: #7fb3d3; font-size: 0.7em;">Med</th>
            </tr>
        '''

        for ore_name, ore_data in ores.items():
            if ore_name == 'INERTMATERIAL':
                continue
            prob = int(round(ore_data.get('prob', 0) * 100))
            min_pct = int(round(ore_data.get('minPct', 0) * 100))
            max_pct = int(round(ore_data.get('maxPct', 0) * 100))
            med_pct = int(round(ore_data.get('medPct', 0) * 100))
            display_name = ore_name.title()
            color = mineral_colors_dict.get(ore_name, '#ffffff')
            html += f'''
                <tr>
                    <td style="padding: 3px 3px;"><span style="color: {color}; font-weight: bold;">{display_name}</span></td>
                    <td style="text-align: center; padding: 3px 3px;">{prob}%</td>
                    <td style="text-align: center; padding: 3px 3px;">{min_pct}%</td>
                    <td style="text-align: center; padding: 3px 3px;">{max_pct}%</td>
                    <td style="text-align: center; padding: 3px 3px;">{med_pct}%</td>
                </tr>
            '''

        html += '</table></div>'

        if multima > 1:
            html += f'''
        <div class="multima-indicator">
            {multima}x MULTIMA FORMATION - ENHANCED YIELD
        </div>
'''

        html += '</body></html>'
        return html

    def create_price_overlay_html(self):
        """Erstelle HTML für Preisliste-Overlay"""
        # Hier würde der vollständige HTML-Code für die Preisliste stehen
        # Ich kürze es hier ab, da es sehr lang ist
        return '''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<style>
body { background: rgba(26, 26, 46, 0.95); color: #00d4ff; font-family: 'Segoe UI', Arial; border: 2px solid rgba(0, 212, 255, 0.4); border-radius: 10px; padding: 12px 15px; }
h2 { text-align: center; margin-bottom: 10px; color: #00d4ff; }
.price-tables { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
table { width: 100%; border-collapse: collapse; }
th { padding: 5px 3px; text-align: left; border-bottom: 2px solid rgba(0, 212, 255, 0.3); color: #7fb3d3; font-size: 0.7em; }
td { padding: 4px 3px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); font-size: 0.75em; }
.resource-name { font-weight: bold; }
.price { text-align: right; color: #b0b0b0; }
</style>
</head>
<body>
<h2>Mineable Ore Prices</h2>
<div class="price-tables">
<!-- Preis-Tabellen hier -->
</div>
<div style="text-align: center; margin-top: 8px; color: #7fb3d3; font-size: 0.65em;">Numpad - zum Schließen | Verschiebbar mit Maus</div>
</body>
</html>'''