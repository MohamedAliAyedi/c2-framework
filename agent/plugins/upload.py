import os
import base64
try:
    from .base import BasePlugin
except (ImportError, ValueError):
    from base import BasePlugin
from typing import Dict, Any

class UploadPlugin(BasePlugin):
    @property
    def name(self): return "upload"

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Writes a file from a base64 string to the local disk."""
        filename = payload.get("filename", "")
        content_b64 = payload.get("content", "")
        dest_path = payload.get("path", ".")
        
        if not filename or not content_b64:
            return {"status": "error", "error": "Missing filename or content"}

        try:
            full_path = os.path.join(dest_path, filename)
            # Ensure directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            file_data = base64.b64decode(content_b64)
            with open(full_path, "wb") as f:
                f.write(file_data)
            
            return {
                "status": "success",
                "message": f"File uploaded successfully to {full_path}",
                "size": len(file_data)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
