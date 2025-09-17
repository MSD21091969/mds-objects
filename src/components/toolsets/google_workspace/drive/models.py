# MDSAPP/core/models/google/drive.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class DriveFile(BaseModel):
    """
    Represents a file resource from the Google Drive API.
    """
    id: str
    name: str
    mime_type: str = Field(..., alias='mimeType')
    web_view_link: Optional[str] = Field(None, alias='webViewLink')
    icon_link: Optional[str] = Field(None, alias='iconLink')
    modified_time: Optional[str] = Field(None, alias='modifiedTime')
    created_time: Optional[str] = Field(None, alias='createdTime')

    class Config:
        populate_by_name = True
