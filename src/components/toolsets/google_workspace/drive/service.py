import logging
import os
import io
from datetime import datetime, date, time
from typing import Dict, Any, TYPE_CHECKING, Optional, List

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from src.components.toolsets.google_workspace.base_service import BaseGoogleService
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
    def __init__(self, client_secrets_path: str, token_path: str = "token.json"):
        super().__init__(client_secrets_path, token_path)
        self._build_service(SERVICE_NAME, SERVICE_VERSION, SCOPES)

    

    def list_files_by_date_range(self, start_date: date, end_date: date) -> List[DriveFile]:
        """
        Lists files in Google Drive within a specified date range, handling pagination.
        """
        if not self.service:
            logger.error("GoogleDriveService is not authenticated. Cannot list files.")
            return []

        all_files = []
        page_token = None
        try:
            start_time = datetime.combine(start_date, time.min).isoformat() + 'Z'
            end_time = datetime.combine(end_date, time.max).isoformat() + 'Z'
            query = f"modifiedTime >= '{start_time}' and modifiedTime <= '{end_time}'"

            while True:
                results = self.service.files().list(
                    q=query,
                    pageSize=100,
                    fields="nextPageToken, files(id, name, mimeType, webViewLink, iconLink, modifiedTime, createdTime)",
                    orderBy='modifiedTime desc',
                    pageToken=page_token
                ).execute()
                
                files = results.get('files', [])
                for file_data in files:
                    try:
                        all_files.append(DriveFile(**file_data))
                    except Exception as e:
                        logger.warning(f"Could not parse file with ID {file_data.get('id')}. Error: {e}")

                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            
            logger.info(f"Found {len(all_files)} files in the specified date range.")
            return all_files
        except HttpError as error:
            logger.error(f"An error occurred while listing files by date range: {error}")
            return []

    def export_google_doc(self, file_id: str, mime_type: str = 'text/plain') -> Optional[str]:
        """Exports a Google Doc to the specified mimeType and returns its content."""
        if not self.service:
            logger.error("GoogleDriveService is not authenticated. Cannot export file.")
            return None
        try:
            request = self.service.files().export_media(fileId=file_id, mimeType=mime_type)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            return fh.getvalue().decode('utf-8')
        except HttpError as error:
            logger.error(f"An error occurred while exporting file {file_id}: {error}")
            return None

    def upload_file(self, file_path: str, file_name: str, mime_type: str) -> Optional[DriveFile]:
        """
        Uploads a file to Google Drive.
        """
        if not self.service:
            logger.error("GoogleDriveService is not authenticated. Cannot upload file.")
            return None

        try:
            file_metadata = {'name': file_name}
            media = MediaFileUpload(file_path, mimetype=mime_type)
            file = self.service.files().create(body=file_metadata,
                                               media_body=media,
                                               fields='id, name, mimeType, webViewLink, iconLink, modifiedTime, createdTime').execute()
            logger.info(f"File '{file.get('name')}' uploaded successfully with ID: {file.get('id')}")
            return DriveFile(**file)
        except HttpError as error:
            logger.error(f"An error occurred while uploading the file: {error}")
            return None

    def download_file(self, file_id: str, destination_path: str):
        """
        Downloads a file from Google Drive.
        """
        if not self.service:
            logger.error("GoogleDriveService is not authenticated. Cannot download file.")
            return

        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.FileIO(destination_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                logger.info(f"Download {int(status.progress() * 100)}%.")
            logger.info(f"File with ID '{file_id}' downloaded successfully to '{destination_path}'.")
        except HttpError as error:
            logger.error(f"An error occurred while downloading the file: {error}")

    def delete_file(self, file_id: str):
        """
        Deletes a file from Google Drive.
        """
        if not self.service:
            logger.error("GoogleDriveService is not authenticated. Cannot delete file.")
            return

        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"File with ID '{file_id}' deleted successfully.")
        except HttpError as error:
            logger.error(f"An error occurred while deleting the file: {error}")