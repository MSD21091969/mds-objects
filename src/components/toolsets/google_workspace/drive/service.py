import logging
import os
import asyncio
import io
from datetime import datetime, date, time
from typing import Dict, Any, TYPE_CHECKING, Optional, List

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from src.components.toolsets.google_workspace.base_service import BaseGoogleService
from src.core.managers.database_manager import DatabaseManager
from .models import DriveFile

logger = logging.getLogger(__name__)

# Update scopes to include write access
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_NAME = 'drive'
SERVICE_VERSION = 'v3'

class GoogleDriveService(BaseGoogleService):
    """
    A service class to interact with the real Google Drive API using OAuth 2.0.
    """
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
        self.service_name = SERVICE_NAME
        self.service_version = SERVICE_VERSION
        self.scopes = SCOPES

    async def list_files_by_date_range(self, user_id: str, start_date: date, end_date: date) -> List[DriveFile]:
        """
        Lists files in Google Drive within a specified date range, handling pagination.
        """
        service = await self.get_service_for_user(user_id)
        if not service:
            logger.error(f"Could not get authenticated Drive service for user {user_id}.")
            return []
        
        all_files = []
        page_token = None
        try:
            start_time = datetime.combine(start_date, time.min).isoformat() + 'Z'
            end_time = datetime.combine(end_date, time.max).isoformat() + 'Z'
            query = f"modifiedTime >= '{start_time}' and modifiedTime <= '{end_time}'"

            while True:
                results = await asyncio.to_thread(
                    service.files().list(
                        q=query,
                        pageSize=100,
                        fields="nextPageToken, files(id, name, mimeType, webViewLink, iconLink, modifiedTime, createdTime)",
                        orderBy='modifiedTime desc',
                        pageToken=page_token
                    ).execute,
                )
                
                files = results.get('files', [])
                for file_data in files:
                    try:
                        all_files.append(DriveFile(**file_data))
                    except Exception as e:
                        logger.warning(f"Could not parse file with ID {file_data.get('id')}. Error: {e}")

                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            
            logger.info(f"Found {len(all_files)} files in the specified date range for user '{user_id}'.")
            return all_files
        except HttpError as error:
            logger.error(f"An error occurred while listing files by date range for user '{user_id}': {error}")
            return []

    async def export_google_doc(self, user_id: str, file_id: str, mime_type: str = 'text/plain') -> Optional[str]:
        """Exports a Google Doc to the specified mimeType and returns its content."""
        service = await self.get_service_for_user(user_id)
        if not service:
            logger.error(f"Could not get authenticated Drive service for user {user_id}.")
            return None
        try:
            request = service.files().export_media(fileId=file_id, mimeType=mime_type)
            fh = io.BytesIO()
            
            # MediaIoBaseDownload is blocking, so it needs to be run in a thread
            await asyncio.to_thread(self._download_media, fh, request)

            return fh.getvalue().decode('utf-8')
        except HttpError as error:
            logger.error(f"An error occurred while exporting file {file_id}: {error}")
            return None

    async def upload_file(self, user_id: str, file_path: str, file_name: str, mime_type: str) -> Optional[DriveFile]:
        """
        Uploads a file to Google Drive.
        """
        service = await self.get_service_for_user(user_id)
        if not service:
            logger.error(f"Could not get authenticated Drive service for user {user_id}.")
            return None

        try:
            file_metadata = {'name': file_name}
            media = MediaFileUpload(file_path, mimetype=mime_type)
            file = await asyncio.to_thread(
                service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, name, mimeType, webViewLink, iconLink, modifiedTime, createdTime'
                ).execute,
            )
            logger.info(f"File '{file.get('name')}' uploaded successfully with ID: {file.get('id')}")
            return DriveFile(**file)
        except HttpError as error:
            logger.error(f"An error occurred while uploading the file: {error}")
            return None

    async def download_file(self, user_id: str, file_id: str, destination_path: str) -> bool:
        """
        Downloads a file from Google Drive. Returns True on success.
        """
        service = await self.get_service_for_user(user_id)
        if not service:
            logger.error(f"Could not get authenticated Drive service for user {user_id}.")
            return False

        try:
            request = service.files().get_media(fileId=file_id)
            fh = io.FileIO(destination_path, 'wb')
            await asyncio.to_thread(self._download_media, fh, request)
            logger.info(f"File with ID '{file_id}' downloaded successfully to '{destination_path}'.")
            return True
        except HttpError as error:
            logger.error(f"An error occurred while downloading the file: {error}")
            return False

    def _download_media(self, fh, request):
        """Helper function to run blocking MediaIoBaseDownload in a thread."""
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            logger.info(f"Download {int(status.progress() * 100)}%.")

    async def delete_file(self, user_id: str, file_id: str) -> bool:
        """
        Deletes a file from Google Drive. Returns True on success.
        """
        service = await self.get_service_for_user(user_id)
        if not service:
            logger.error(f"Could not get authenticated Drive service for user {user_id}.")
            return False
        try:
            await asyncio.to_thread(
                service.files().delete(fileId=file_id).execute,
            )
            logger.info(f"File with ID '{file_id}' deleted successfully.")
            return True
        except HttpError as error:
            logger.error(f"An error occurred while deleting the file: {error}")
            return False