# src/components/toolsets/google_workspace/gmail/models.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# --- Modellen voor API Data Structures ---

class GmailHeader(BaseModel):
    """Represents a single header in a Gmail message."""
    name: str
    value: str

class Attachment(BaseModel):
    """Represents a file attachment in a Gmail message."""
    attachmentId: str
    filename: str
    mimeType: str
    size: int
    data: Optional[str] = None # Base64-encoded data, only present for 'get_attachment' tool.

class GmailMessage(BaseModel):
    """Represents a single Gmail message resource."""
    id: str
    threadId: str
    labelIds: List[str] = Field(default_factory=list)
    snippet: Optional[str] = None
    
    # Payload velden voor gedetailleerde informatie
    headers: Optional[List[GmailHeader]] = Field(None, description="A list of name-value pairs for message headers.")
    body_text: Optional[str] = None # The decoded message body as plain text
    body_html: Optional[str] = None # The decoded message body as HTML
    attachments: Optional[List[Attachment]] = None

    class Config:
        extra = 'ignore' # Negeer velden die niet in het model zijn gedefinieerd
        populate_by_name = True

class MessageList(BaseModel):
    """Represents a list of messages returned by the Gmail API."""
    messages: List[GmailMessage] = []
    nextPageToken: Optional[str] = None
    
    class Config:
        extra = 'ignore'

# --- Modellen voor Tool Input Validatie ---

class ListMessagesQuery(BaseModel):
    """Input validation model for the list_messages tool."""
    query: Optional[str] = Field(None, description="Gmail search query, e.g., 'from:someone@example.com is:unread'")
    max_results: int = Field(10, description="The maximum number of messages to return.")
    page_token: Optional[str] = Field(None, description="Token to retrieve the next page of results.")
    
class GetMessageQuery(BaseModel):
    """Input validation model for the get_message tool."""
    message_id: str = Field(..., description="The ID of the message to retrieve.")
    format: Optional[str] = Field("full", description="The format of the message payload. 'full', 'metadata' or 'raw'.")