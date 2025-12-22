import subprocess
from .base import BasePlugin
from typing import Dict, Any

class ShellPlugin(BasePlugin):
    @property
    def name(self): return "shell"

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        command = payload.get("command", "")
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "status": "success",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
