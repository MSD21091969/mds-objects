# src/components/toolsets/google_workspace/docs/models.py

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class GoogleDoc(BaseModel):
    """
    Represents a Google Docs document resource with detailed content and metadata.
    """
    documentId: str
    title: str
    revisionId: str
    body: Optional[Dict[str, Any]] = Field(None, description="The content of the document, including structural elements.")
    
    # Metadata fields from the API
    createdTime: Optional[datetime] = None
    modifiedTime: Optional[datetime] = None
    webViewLink: Optional[str] = None

    class Config:
        extra = 'ignore'
        populate_by_name = True

class CreateDocumentQuery(BaseModel):
    """Input validation model for the create_document tool."""
    title: str = Field(..., description="The title for the new Google Document.")

class GetDocumentQuery(BaseModel):
    """Input validation model for the get_document tool."""
    document_id: str = Field(..., description="The unique ID of the Google Document to retrieve.")
    fields: Optional[str] = Field(None, description="A comma-separated list of fields to return from the API. For example: 'documentId,title,body'.")