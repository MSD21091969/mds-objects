# src/components/communication/models.py

from pydantic import BaseModel

class ChatRequest(BaseModel):
    """Request model for an incoming chat message."""
    user_input: str
    casefile_id: str

class ChatResponse(BaseModel):
    """Response model for an outgoing chat message."""
    response: str
    casefile_id: str
