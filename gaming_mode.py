try:
    from pynput import keyboard

    GLOBAL_HOTKEYS_AVAILABLE = True
except ImportError:
    GLOBAL_HOTKEYS_AVAILABLE = False
    print("[INFO] pynput nicht installiert - Gaming-Modus nicht verfügbar")


class GamingMode:
    """Verwaltet Gaming-Modus mit globalen Hotkeys"""

    def __init__(self, js_callback):
        """
        js_callback: Funktion die JavaScript-Code ausführt
        """
        self.js_callback = js_callback
        self.gaming_mode = False
        self.global_listener = None

    def toggle(self):
        """Gaming-Modus ein/ausschalten"""
        if not GLOBAL_HOTKEYS_AVAILABLE:
            return {'success': False, 'error': 'pynput nicht installiert'}

        if self.gaming_mode:
            # Ausschalten
            self.gaming_mode = False
            if self.global_listener:
                try:
                    self.global_listener.stop()
                except Exception as e:
                    print(f"[WARNING] Listener konnte nicht gestoppt werden: {e}")
                finally:
                    self.global_listener = None
            return {'success': True, 'active': False, 'message': 'Gaming-Modus deaktiviert'}
        else:
            # Einschalten
            try:
                self.gaming_mode = True
                self.global_listener = keyboard.Listener(
                    on_press=self.on_global_key_press,
                    suppress=False
                )
                self.global_listener.start()
                return {'success': True, 'active': True, 'message': 'Gaming-Modus aktiviert'}
            except Exception as e:
                self.gaming_mode = False
                return {'success': False, 'error': str(e)}

    def pause_listener(self):
        """Pausiere Gaming-Listener temporär"""
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

    def resume_listener(self):
        """Setze Gaming-Listener fort"""
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

    def on_global_key_press(self, key):
        """Globale Tastatur-Eingaben für Gaming-Modus"""
        if not self.gaming_mode:
            return

        try:
            # F11 = Gaming-Modus Toggle
            if key == keyboard.Key.f11:
                self.js_callback("toggleGamingModeFromPython()")
                return

            # Numpad-Zahlen
            if hasattr(key, 'vk'):
                vk = key.vk

                # Numpad 0-9
                if 96 <= vk <= 105:
                    number = str(vk - 96)
                    js_code = f"addNumberFromGaming('{number}');"
                    self.js_callback(js_code)
                    return

                # Normale Zahlen 0-9
                elif 48 <= vk <= 57:
                    number = str(vk - 48)
                    js_code = f"addNumberFromGaming('{number}');"
                    self.js_callback(js_code)
                    return

                # Numpad Plus = Suchen
                elif vk == 107:
                    self.js_callback("searchFromGaming();")
                    return

                # Numpad Minus = Preisliste
                elif vk == 109:
                    self.js_callback("togglePriceListFromGaming();")
                    return

            # Normale Zahlen als Zeichen
            if hasattr(key, 'char') and key.char and key.char.isdigit():
                number = key.char
                js_code = f"addNumberFromGaming('{number}');"
                self.js_callback(js_code)
                return

            # Plus = Suchen
            if hasattr(key, 'char') and key.char == '+':
                self.js_callback("searchFromGaming();")
                return

            # Minus = Preisliste
            if hasattr(key, 'char') and key.char == '-':
                self.js_callback("togglePriceListFromGaming();")
                return

            # ESC = Reset
            if key == keyboard.Key.esc:
                self.js_callback("resetFromGaming();")
                return

            # Backspace = Letzte Ziffer löschen
            if key == keyboard.Key.backspace:
                self.js_callback("backspaceFromGaming();")
                return

        except Exception as e:
            print(f"[ERROR] Gaming-Modus Tastaturverarbeitung fehlgeschlagen: {e}")

    def is_active(self):
        """Prüfe ob Gaming-Modus aktiv ist"""
        return self.gaming_mode

    def cleanup(self):
        """Cleanup beim Beenden"""
        if self.global_listener:
            try:
                self.global_listener.stop()
            except:
                pass