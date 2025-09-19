import uuid
import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field

from core.models.ontology import CasefileRole
# from core.models.google_workspace.drive import DriveFile
# from core.models.google_workspace.gmail import GmailMessage
# from core.models.google_workspace.calendar import GoogleCalendarEvent
# from core.models.google_workspace.people import GooglePerson

class RelatedObject(BaseModel): # Placeholder
    id: str
    type: str

class ProcessedArtifact(BaseModel):
    """
    Represents a file that has been processed and stored in Google Cloud Storage.
    """
    gcs_uri: str = Field(description="The URI of the file in Google Cloud Storage (e.g., gs://bucket-name/path/to/file).")
    source_id: str = Field(description="The ID of the original source object (e.g., an email message ID or a drive file ID).")
    filename: str
    mime_type: str
    processed_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    size_bytes: Optional[int] = None

class Casefile(BaseModel):
    """
    The central, all-encompassing dossier-object for the MDS platform.
    It can be nested to represent a hierarchy of casefiles.
    """
    id: Optional[str] = Field(default_factory=lambda: f"case-{uuid.uuid4().hex}")
    name: str
    description: Optional[str] = ""
    casefile_type: str = "research"

    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    modified_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    owner_id: Optional[str] = None  # Added Optional for now
    acl: Dict[str, CasefileRole] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if self.owner_id and not self.acl:
            self.acl = {self.owner_id: CasefileRole.ADMIN}

    tags: List[str] = Field(default_factory=list)

    sub_casefile_ids: List[str] = Field(
        default_factory=list, description="A list of IDs of nested sub-casefiles."
    )
    parent_id: Optional[str] = None

    session_ids: List[str] = Field(
        default_factory=list, description="A list of IDs of associated ADK Session instances."
    )

    related_objects: List[RelatedObject] = Field(
        default_factory=list, description="A list of linked external objects with their metadata."
    )

    processed_files: List[ProcessedArtifact] = Field(
        default_factory=list, description="A list of artifacts processed during ingestion and stored in GCS."
    )
    
    drive_files_count: Optional[int] = 0
    gmail_messages_count: Optional[int] = 0
    calendar_events_count: Optional[int] = 0
    artifacts_count: Optional[int] = 0

    # New fields for Google Workspace objects
    # drive_files: Optional[List[DriveFile]] = None
    # gmail_messages: Optional[List[GmailMessage]] = None
    # calendar_events: Optional[List[GoogleCalendarEvent]] = None
    # google_people: Optional[List[GooglePerson]] = None

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
    related_objects: Optional[List[RelatedObject]] = None
    processed_files: Optional[List[ProcessedArtifact]] = None
    drive_files_count: Optional[int] = None
    gmail_messages_count: Optional[int] = None
    calendar_events_count: Optional[int] = None
    artifacts_count: Optional[int] = None
    # New fields for updating Google Workspace objects
    # drive_files: Optional[List[DriveFile]] = None
    # gmail_messages: Optional[List[GmailMessage]] = None
    # calendar_events: Optional[List[GoogleCalendarEvent]] = None
    # google_people: Optional[List[GooglePerson]] = None

class UpdateCasefileRequest(BaseModel):
    updates: CasefileUpdate

class GrantAccessRequest(BaseModel):
    user_id_to_grant: str
    role: CasefileRole

class RevokeAccessRequest(BaseModel):
    user_id_to_revoke: str
