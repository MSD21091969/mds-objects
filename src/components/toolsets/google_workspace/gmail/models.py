# MDSAPP/core/models/google/gmail.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, List

class Attachment(BaseModel):
    """
    Represents an attachment within a Gmail message.
    """
    attachment_id: str = Field(..., alias='attachmentId')
    filename: str
    mime_type: str = Field(..., alias='mimeType')
    size: int

    model_config = ConfigDict(populate_by_name=True)

class GmailMessage(BaseModel):
    """
    Represents a message resource from the Gmail API (in full format).
    """
    id: str
    thread_id: str = Field(..., alias='threadId')
    snippet: str
    headers: Dict[str, str]
    body: Optional[str] = None
    attachments: List[Attachment] = Field(default_factory=list)
    internal_date: Optional[str] = Field(None, alias='internalDate')

    model_config = ConfigDict(populate_by_name=True)