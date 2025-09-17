# MDSAPP/prefect_flows/shared_tasks.py

from prefect import task, get_run_logger
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict
import asyncio

# Dependency Getters
from MDSAPP.core.dependencies import (
    get_casefile_manager,
    get_google_drive_service,
    get_google_gmail_service,
    get_google_calendar_service,
)
from google.cloud import storage

# Models
from MDSAPP.core.models.GoogleWorkspace.drive import DriveFile
from MDSAPP.core.models.GoogleWorkspace.gmail import GmailMessage
from MDSAPP.core.models.GoogleWorkspace.calendar import GoogleCalendarEvent
from MDSAPP.CasefileManagement.models.casefile import CasefileUpdate

# --- Configuration ---
GCS_BUCKET_NAME = "mds7-casefile-artifacts"

# --- Pydantic Models ---
class FileArtifact(BaseModel):
    source_id: str # e.g., email messageId or drive fileId
    gcs_uri: str
    filename: str
    mime_type: str

# --- Reusable Tasks ---

@task
async def fetch_drive_files_task(date_range: Dict[str, datetime]) -> List[DriveFile]:
    logger = get_run_logger()
    logger.info("STARTING: fetch_drive_files_task")
    drive_service = get_google_drive_service()
    logger.info(f"Fetching Drive files from {date_range['start_time']} to {date_range['end_time']}...")
    files = drive_service.list_files_by_date_range(date_range['start_time'], date_range['end_time'])
    logger.info(f"COMPLETED: fetch_drive_files_task - Found {len(files)} files.")
    return files

@task
async def fetch_gmail_messages_task(date_range: Dict[str, datetime]) -> List[GmailMessage]:
    logger = get_run_logger()
    logger.info("STARTING: fetch_gmail_messages_task")
    gmail_service = get_google_gmail_service()
    logger.info(f"Fetching Gmail messages from {date_range['start_time']} to {date_range['end_time']}...")
    messages = gmail_service.search_emails(date_range['start_time'], date_range['end_time'])
    logger.info(f"COMPLETED: fetch_gmail_messages_task - Found {len(messages)} messages.")
    return messages

@task
async def fetch_calendar_events_task(date_range: Dict[str, datetime]) -> List[GoogleCalendarEvent]:
    logger = get_run_logger()
    logger.info("STARTING: fetch_calendar_events_task")
    calendar_service = get_google_calendar_service()
    logger.info(f"Fetching Calendar events from {date_range['start_time']} to {date_range['end_time']}...")
    events = calendar_service.list_events(time_min=date_range['start_time'], time_max=date_range['end_time'])
    logger.info(f"COMPLETED: fetch_calendar_events_task - Found {len(events)} events.")
    return events

@task
async def process_attachments_task(messages: List[GmailMessage]) -> List[FileArtifact]:
    logger = get_run_logger()
    logger.info(f"STARTING: process_attachments_task for {len(messages)} messages.")
    gmail_service = get_google_gmail_service()
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    processed_artifacts = []

    for msg in messages:
        if not msg.attachments:
            continue
        for att in msg.attachments:
            try:
                logger.info(f"Processing attachment '{att.filename}' from message {msg.id}...")
                logger.info(f"Downloading attachment '{att.filename}'...")
                file_data = gmail_service.get_attachment(msg.id, att.attachment_id)
                if file_data:
                    logger.info(f"Downloaded {len(file_data)} bytes for attachment '{att.filename}'.")
                if file_data:
                    blob_name = f"attachments/{msg.id}/{att.filename}"
                    blob = bucket.blob(blob_name)
                    logger.info(f"Uploading attachment '{att.filename}' to GCS bucket '{GCS_BUCKET_NAME}' as blob '{blob_name}'...")
                    blob.upload_from_string(file_data, content_type=att.mime_type)
                    logger.info(f"Successfully uploaded attachment '{att.filename}'.")
                    artifact = FileArtifact(
                        source_id=msg.id,
                        gcs_uri=f"gs://{GCS_BUCKET_NAME}/{blob_name}",
                        filename=att.filename,
                        mime_type=att.mime_type
                    )
                    processed_artifacts.append(artifact)
                    logger.info(f"Successfully uploaded '{att.filename}' to {artifact.gcs_uri}.")
            except Exception as e:
                logger.error(f"Failed to process attachment '{att.filename}': {e}")
    logger.info(f"COMPLETED: process_attachments_task - Processed {len(processed_artifacts)} attachments.")
    return processed_artifacts

@task
async def create_report_casefile_task(user_id: str, start_time: datetime, end_time: datetime, report_type: str = "Automated") -> str:
    logger = get_run_logger()
    logger.info("STARTING: create_report_casefile_task")
    casefile_manager = get_casefile_manager()
    report_name = f"Workspace Activity Report: {end_time.strftime('%Y-%m-%d %H:%M')}"
    report_description = f"{report_type} report of new Google Workspace activity for user '{user_id}' since {start_time.isoformat()}."
    logger.info(f"Creating casefile: '{report_name}'...")
    new_casefile = await casefile_manager.create_casefile(
        user_id=user_id, name=report_name, description=report_description
    )
    logger.info(f"COMPLETED: create_report_casefile_task - Created casefile with ID: {new_casefile.id}")
    return new_casefile.id

@task
async def aggregate_and_save_task(
    casefile_id: str,
    user_id: str,
    drive_files: List[DriveFile],
    gmail_messages: List[GmailMessage],
    calendar_events: List[GoogleCalendarEvent],
    artifacts: List[FileArtifact],
    tag: str = "automated-sync"
) -> None:
    logger = get_run_logger()
    casefile_manager = get_casefile_manager()

    # Update metadata in the main document
    updates = CasefileUpdate(
        tags=[tag, "google-workspace"],
        drive_files_count=len(drive_files),
        gmail_messages_count=len(gmail_messages),
        calendar_events_count=len(calendar_events),
        artifacts_count=len(artifacts)
    )
    
    await casefile_manager.update_casefile(
        casefile_id=casefile_id, 
        user_id=user_id, 
        updates=updates.model_dump(exclude_unset=True)
    )

    # Use asyncio.gather for concurrent subcollection writes
    tasks = []
    for item in drive_files:
        tasks.append(casefile_manager.add_document_to_subcollection(casefile_id, "drive_files", item.model_dump(), item.id))
    for item in gmail_messages:
        tasks.append(casefile_manager.add_document_to_subcollection(casefile_id, "gmail_messages", item.model_dump(), item.id))
    for item in calendar_events:
        tasks.append(casefile_manager.add_document_to_subcollection(casefile_id, "calendar_events", item.model_dump(), item.id))
    for item in artifacts:
        tasks.append(casefile_manager.add_document_to_subcollection(casefile_id, "artifacts", item.model_dump()))

    await asyncio.gather(*tasks)

    logger.info(f"Successfully aggregated all data and saved to casefile {casefile_id}.")
