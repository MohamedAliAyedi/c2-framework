# shared/schemas.py
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

class Task(BaseModel):
    id: str
    type: str
    payload: Dict[str, Any]
    expires_at: datetime
