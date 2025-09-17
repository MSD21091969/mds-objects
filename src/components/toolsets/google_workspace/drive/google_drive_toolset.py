import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool

from src.components.toolsets.google_workspace.drive.service import GoogleDriveService
from src.components.toolsets.google_workspace.drive.models import DriveFile

logger = logging.getLogger(__name__)

class GoogleDriveToolset(BaseToolset):
    """
    A toolset for interacting with Google Drive.
    """
    def __init__(self, drive_service: Optional[GoogleDriveService]):
        super().__init__()
        self.drive_service = drive_service

    def _ensure_service(self):
        """Checks if the Google Drive service is available."""
        if not self.drive_service or not self.drive_service.service:
            raise ConnectionError("GoogleDriveService is not available or not authenticated.")

    def list_files_by_date_range(self, start_date: str, end_date: str) -> List[DriveFile]:
        """
        Lists files from the user's Google Drive within a specified date range.

        Args:
            start_date: The start date in YYYY-MM-DD format.
            end_date: The end date in YYYY-MM-DD format.

        Returns:
            A list of DriveFile objects.
        """
        self._ensure_service()
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Please use YYYY-MM-DD.")

        logger.info(f"Toolset is calling drive_service.list_files_by_date_range with start_date={start_date} and end_date={end_date}")
        return self.drive_service.list_files_by_date_range(start_date=start_date_obj, end_date=end_date_obj)

    def upload_file(self, file_path: str, file_name: str, mime_type: str) -> Optional[DriveFile]:
        """
        Uploads a file to Google Drive.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling drive_service.upload_file for file: {file_name}")
        return self.drive_service.upload_file(file_path, file_name, mime_type)

    def download_file(self, file_id: str, destination_path: str):
        """
        Downloads a file from Google Drive.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling drive_service.download_file for file ID: {file_id}")
        self.drive_service.download_file(file_id, destination_path)

    def delete_file(self, file_id: str):
        """
        Deletes a file from Google Drive.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling drive_service.delete_file for file ID: {file_id}")
        self.drive_service.delete_file(file_id)

    def get_tools(self) -> list[BaseTool]:
        """
        Returns a list of tools provided by this toolset.
        """
        return [
            FunctionTool(
                func=self.list_files_by_date_range
            ),
            FunctionTool(
                func=self.upload_file
            ),
            FunctionTool(
                func=self.download_file
            ),
            FunctionTool(
                func=self.delete_file
            )
        ]
