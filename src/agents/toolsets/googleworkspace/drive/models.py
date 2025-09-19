# src/components/toolsets/google_workspace/drive/models.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class DriveFile(BaseModel):
    """
    Represents a Google Drive file resource with sufficient metadata
    for the Casefile and other application logic.
    """
    id: str
    name: str
    mimeType: str
    parents: Optional[List[str]] = Field(None, description="The IDs of the parents of the file.")
    
    # Extra velden voor gedetailleerde informatie
    createdTime: Optional[datetime] = None
    modifiedTime: Optional[datetime] = None
    webContentLink: Optional[str] = None
    webViewLink: Optional[str] = None
    iconLink: Optional[str] = None
    owners: Optional[List[Dict[str, Any]]] = None
    ownedByMe: Optional[bool] = None
    shared: Optional[bool] = None
    size: Optional[str] = None # Size is a string in the API
    permissionIds: Optional[List[str]] = None
    
    class Config:
        extra = 'ignore' # Negeer velden die niet in het model zijn gedefinieerd
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class FileList(BaseModel):
    """
    Represents a list of Google Drive files returned from the API,
    with pagination support.
    """
    kind: Optional[str] = None
    incompleteSearch: Optional[bool] = None
    nextPageToken: Optional[str] = None
    files: List[DriveFile] = []

    class Config:
        populate_by_name = True


class ListFilesQuery(BaseModel):
    """
    Input validation model for the list_files tool, with enhanced options.
    """
    query: Optional[str] = Field(None, description="A search query in Google Drive query language.")
    page_size: Optional[int] = Field(10, description="The maximum number of files to return.")
    corpora: Optional[str] = Field("user", description="The corpus of the files to search. 'user' or 'domain'.")
    fields: Optional[str] = Field(None, description="A comma-separated list of fields to return.")
    include_team_drive_items: Optional[bool] = False
    supports_team_drives: Optional[bool] = False