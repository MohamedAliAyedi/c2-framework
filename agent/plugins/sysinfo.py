import platform
import os
from .base import BasePlugin
from typing import Dict, Any

class SysinfoPlugin(BasePlugin):
    @property
    def name(self): return "sysinfo"

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            info = {
                "os": platform.system(),
                "os_version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "cwd": os.getcwd(),
                "user": os.getlogin() if hasattr(os, 'getlogin') else "unknown"
            }
            return {"status": "success", "info": info}
        except Exception as e:
            return {"status": "error", "error": str(e)}
