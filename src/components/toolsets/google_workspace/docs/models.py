# MDSAPP/core/models/google/docs.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class GoogleDoc(BaseModel):
    """
    Represents a Google Document resource, focusing on key identifiers.
    """
    document_id: str = Field(..., alias='documentId')
    title: str
    document_url: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)