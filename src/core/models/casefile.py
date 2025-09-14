import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional

class Casefile(BaseModel):
    id: str = Field(default_factory=lambda: f"case-{uuid.uuid4().hex[:10]}")
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    owner_id: str
