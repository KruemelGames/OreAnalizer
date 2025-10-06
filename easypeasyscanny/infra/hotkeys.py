import threading, time
from ..infra.logger import get_logger
logger = get_logger(__name__)

class GamingState:
    def __init__(self):
        self.active = True  # global capture on
        self.focused = False  # text input focused in UI

STATE = GamingState()

class NumpadListener:
    def __init__(self, on_number, on_plus, on_minus):
        self.on_number = on_number; self.on_plus = on_plus; self.on_minus = on_minus
        self._stop = threading.Event(); self._thread=None
    def start(self):
        if self._thread and self._thread.is_alive(): return
        self._thread = threading.Thread(target=self._run, daemon=True); self._thread.start()
    def stop(self): self._stop.set()

    def _run(self):
        try:
            import keyboard
            buf=[]; logger.info("Keyboard hook aktiv (keyboard)")
            def on_key(e):
                if self._stop.is_set(): return False
                if not STATE.active or STATE.focused: return
                if e.event_type!='down': return
                name=e.name
                if name in [str(i) for i in range(10)] + [f"num {i}" for i in range(10)]:
                    digit=name[-1]; buf.append(digit); logger.debug("Numpad digit: %s", digit)
                elif name in ("num add","+"):
                    val = int(''.join(buf)) if buf else 0; buf.clear(); self.on_plus(val)
                elif name in ("num subtract","-"):
                    self.on_minus()
                elif name=="backspace":
                    if buf: buf.pop()
                elif name=="esc":
                    buf.clear()
            keyboard.hook(on_key)
            while not self._stop.is_set(): time.sleep(0.1)
        except Exception as e:
            logger.warning("keyboard-Hook fehlgeschlagen (%s).", e)
