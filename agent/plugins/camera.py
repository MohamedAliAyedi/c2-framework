import base64
import cv2
try:
    from .base import BasePlugin
except (ImportError, ValueError):
    from base import BasePlugin
from typing import Dict, Any

class CameraPlugin(BasePlugin):
    @property
    def name(self): return "camera"

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Captures a single frame from the default webcam."""
        try:
            # Index 0 is usually the default camera
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return {"status": "error", "error": "Could not open webcam"}
            
            # Allow camera to warm up/adjust light (optional frame skip)
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return {"status": "error", "error": "Failed to grab frame"}
            
            # Encode as JPG to reduce size
            _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
            encoded = base64.b64encode(buffer).decode('utf-8')
            
            return {
                "status": "success",
                "format": "jpg",
                "content": encoded,
                "size": len(buffer)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
