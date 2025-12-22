import subprocess
try:
    from .base import BasePlugin
except (ImportError, ValueError):
    from base import BasePlugin
from typing import Dict, Any

class ExecPlugin(BasePlugin):
    @property
    def name(self): return "exec"

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a process directly (binary) instead of through shell."""
        command = payload.get("command", "")
        args = payload.get("args", [])
        
        if not command:
            return {"status": "error", "error": "No command provided"}

        try:
            full_cmd = [command] + args
            result = subprocess.run(
                full_cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                timeout=30
            )
            return {
                "status": "success",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "error": "Execution timed out"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
