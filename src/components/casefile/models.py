import uuid
import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field

from ...core.models.ontology import CasefileRole
from ..google_workspace.drive.models import DriveFile
from ..google_workspace.gmail.models import GmailMessage
from ..google_workspace.calendar.models import GoogleCalendarEvent
from ..google_workspace.docs.models import GoogleDoc
from ..google_workspace.sheets.models import GoogleSheet


class Casefile(BaseModel):
    """
    The central, all-encompassing dossier-object for the MDS platform.
    It can be nested to represent a hierarchy of casefiles.
    """
    id: Optional[str] = Field(default_factory=lambda: f"case-{uuid.uuid4().hex}")
    name: str
    description: str = ""
    casefile_type: str = "research"

    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    modified_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    owner_id: Optional[str] = None  # Added Optional for now
    acl: Dict[str, CasefileRole] = Field(default_factory=dict)

    tags: List[str] = Field(default_factory=list)

    sub_casefile_ids: List[str] = Field(
        default_factory=list, description="A list of IDs of nested sub-casefiles."
    )
    parent_id: Optional[str] = None

    session_ids: List[str] = Field(
        default_factory=list, description="A list of IDs of associated ADK Session instances."
    )

    processed_files: List[Dict[str, Any]] = Field(
        default_factory=list, description="A list of files processed during ingestion, including their metadata."
    )
    
    drive_files_count: Optional[int] = 0
    gmail_messages_count: Optional[int] = 0
    calendar_events_count: Optional[int] = 0
    artifacts_count: Optional[int] = 0

    # New fields for Google Workspace objects
    drive_files: Optional[List[DriveFile]] = None
    gmail_messages: Optional[List[GmailMessage]] = None
    calendar_events: Optional[List[GoogleCalendarEvent]] = None
    google_docs: Optional[List[GoogleDoc]] = None
    google_sheets: Optional[List[GoogleSheet]] = None

    embedding: Optional[List[float]] = None

    def touch(self):
        self.modified_at = (
            datetime.datetime.now(datetime.timezone.utc).isoformat()
        )

Casefile.model_rebuild()

class CreateCasefileRequest(BaseModel):
    name: str
    description: str = ""
    casefile_id: Optional[str] = None
    parent_id: Optional[str] = None

class CasefileUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    casefile_type: Optional[str] = None
    tags: Optional[List[str]] = None
    processed_files: Optional[List[Dict[str, Any]]] = None
    drive_files_count: Optional[int] = None
    gmail_messages_count: Optional[int] = None
    calendar_events_count: Optional[int] = None
    artifacts_count: Optional[int] = None
    # New fields for updating Google Workspace objects
    drive_files: Optional[List[DriveFile]] = None
    gmail_messages: Optional[List[GmailMessage]] = None
    calendar_events: Optional[List[GoogleCalendarEvent]] = None
    google_docs: Optional[List[GoogleDoc]] = None
    google_sheets: Optional[List[GoogleSheet]] = None

class UpdateCasefileRequest(BaseModel):
    updates: CasefileUpdate

class GrantAccessRequest(BaseModel):
    user_id_to_grant: str
    role: CasefileRole

class RevokeAccessRequest(BaseModel):
    user_id_to_revoke: str