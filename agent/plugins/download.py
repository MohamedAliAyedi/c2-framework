import os
import base64
try:
    from .base import BasePlugin
except (ImportError, ValueError):
    from base import BasePlugin
from typing import Dict, Any

class DownloadPlugin(BasePlugin):
    @property
    def name(self): return "download"

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Reads a local file and returns it as a base64 string."""
        path = payload.get("path", "")
        
        if not path or not os.path.exists(path):
            return {"status": "error", "error": f"File not found: {path}"}

        try:
            with open(path, "rb") as f:
                content = f.read()
            
            return {
                "status": "success",
                "filename": os.path.basename(path),
                "content": base64.b64encode(content).decode('utf-8'),
                "size": len(content)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
