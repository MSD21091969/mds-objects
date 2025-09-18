import pytest
from pydantic import ValidationError
from freezegun import freeze_time
from src.components.casefile.models import Casefile, CreateCasefileRequest, CasefileUpdate, GrantAccessRequest, RevokeAccessRequest
from src.core.models.ontology import CasefileRole
import datetime

def test_casefile_creation_valid_data():
    casefile = Casefile(name="Test Casefile", description="A description", owner_id="user123")
    assert casefile.name == "Test Casefile"
    assert casefile.description == "A description"
    assert casefile.owner_id == "user123"
    assert casefile.id.startswith("case-")
    assert isinstance(casefile.created_at, str)
    assert isinstance(casefile.modified_at, str)
    assert casefile.acl == {"user123": CasefileRole.ADMIN}
    assert casefile.tags == []
    assert casefile.sub_casefile_ids == []
    assert casefile.parent_id is None

def test_casefile_creation_with_optional_fields():
    casefile = Casefile(
        name="Complex Casefile",
        description="Another description",
        owner_id="user456",
        casefile_type="investigation",
        tags=["urgent", "sensitive"],
        parent_id="parent-case-id",
        acl={"user456": CasefileRole.ADMIN, "viewer1": CasefileRole.READER}
    )
    assert casefile.name == "Complex Casefile"
    assert casefile.casefile_type == "investigation"
    assert casefile.tags == ["urgent", "sensitive"]
    assert casefile.parent_id == "parent-case-id"
    assert casefile.acl == {"user456": CasefileRole.ADMIN, "viewer1": CasefileRole.READER}

def test_casefile_creation_invalid_data_type():
    with pytest.raises(ValidationError):
        Casefile(name=123, description="A description", owner_id="user123")

def test_casefile_creation_missing_required_field():
    with pytest.raises(ValidationError):
        Casefile(description="A description", owner_id="user123") # Missing name

@freeze_time("2023-01-01 12:00:00")
def test_casefile_touch_method():
    casefile = Casefile(name="Touch Test", owner_id="user1")
    original_modified_at = casefile.modified_at
    with freeze_time("2023-01-01 12:00:01"):
        casefile.touch()
    assert casefile.modified_at != original_modified_at
    assert isinstance(casefile.modified_at, str)

def test_create_casefile_request_valid():
    req = CreateCasefileRequest(name="New Case", description="Desc")
    assert req.name == "New Case"
    assert req.description == "Desc"
    assert req.casefile_id is None
    assert req.parent_id is None

def test_create_casefile_request_with_ids():
    req = CreateCasefileRequest(name="New Case", casefile_id="custom-id", parent_id="p-id")
    assert req.casefile_id == "custom-id"
    assert req.parent_id == "p-id"

def test_casefile_update_valid():
    update = CasefileUpdate(name="Updated Name", tags=["new", "tags"])
    assert update.name == "Updated Name"
    assert update.tags == ["new", "tags"]
    assert update.description is None # Ensure unset fields are None

def test_casefile_update_all_fields():
    update = CasefileUpdate(
        name="New Name",
        description="New Desc",
        casefile_type="report",
        tags=["tag1"],
        drive_files_count=5,
        gmail_messages_count=10,
        calendar_events_count=2,
        artifacts_count=1,
        # Google Workspace objects are Optional[List] and can be None or empty list
        drive_files=[],
        gmail_messages=[],
        calendar_events=[],
        google_docs=[],
        google_sheets=[]
    )
    assert update.name == "New Name"
    assert update.drive_files_count == 5

def test_grant_access_request_valid():
    req = GrantAccessRequest(user_id_to_grant="user_grant", role=CasefileRole.WRITER)
    assert req.user_id_to_grant == "user_grant"
    assert req.role == CasefileRole.WRITER

def test_grant_access_request_invalid_role():
    with pytest.raises(ValidationError):
        GrantAccessRequest(user_id_to_grant="user_grant", role="invalid_role")

def test_revoke_access_request_valid():
    req = RevokeAccessRequest(user_id_to_revoke="user_revoke")
    assert req.user_id_to_revoke == "user_revoke"
