import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.adk.tools import ToolContext
from google.genai import types as adk_types

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

    def _list_files_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Lists files from the user's Google Drive within a specified date range.

        Args:
            start_date: The start date in YYYY-MM-DD format.
            end_date: The end date in YYYY-MM-DD format.

        Returns:
            A list of dictionaries representing DriveFile objects.
        """
        self._ensure_service()
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Please use YYYY-MM-DD.")

        logger.info(f"Toolset is calling drive_service.list_files_by_date_range with start_date={start_date} and end_date={end_date}")
        files = self.drive_service.list_files_by_date_range(start_date=start_date_obj, end_date=end_date_obj)
        return [file.model_dump() for file in files]

    def _upload_file(self, file_path: str, file_name: str, mime_type: str) -> Optional[Dict[str, Any]]:
        """
        Uploads a file to Google Drive.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling drive_service.upload_file for file: {file_name}")
        uploaded_file = self.drive_service.upload_file(file_path, file_name, mime_type)
        return uploaded_file.model_dump() if uploaded_file else None

    def _download_file(self, file_id: str, destination_path: str) -> str:
        """
        Downloads a file from Google Drive.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling drive_service.download_file for file ID: {file_id}")
        self.drive_service.download_file(file_id, destination_path)
        return f"File with ID '{file_id}' downloaded successfully to '{destination_path}'."

    def _delete_file(self, file_id: str) -> str:
        """
        Deletes a file from Google Drive.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling drive_service.delete_file for file ID: {file_id}")
        self.drive_service.delete_file(file_id)
        return f"File with ID '{file_id}' deleted successfully."

    def get_tools(self, tool_context: "ToolContext") -> list[BaseTool]:
        """
        Returns a list of tools provided by this toolset.
        """
        drive_file_schema = adk_types.Schema(
            type=adk_types.Type.OBJECT,
            properties={
                'id': adk_types.Schema(type=adk_types.Type.STRING, description="The file's ID."),
                'name': adk_types.Schema(type=adk_types.Type.STRING, description="The name of the file."),
                'mime_type': adk_types.Schema(type=adk_types.Type.STRING, description="The MIME type of the file."),
                'created_time': adk_types.Schema(type=adk_types.Type.STRING, description="The creation time of the file in ISO 8601 format."),
                'modified_time': adk_types.Schema(type=adk_types.Type.STRING, description="The last modification time of the file in ISO 8601 format."),
                'web_view_link': adk_types.Schema(type=adk_types.Type.STRING, description="A link for opening the file in a web browser."),
                'icon_link': adk_types.Schema(type=adk_types.Type.STRING, description="A link to the file's icon."),
            }
        )

        list_files_declaration = adk_types.FunctionDeclaration(
            name="list_drive_files",
            description="Lists files from the user's Google Drive within a specified date range.",
            parameters=adk_types.Schema(
                type=adk_types.Type.OBJECT,
                properties={
                    'start_date': adk_types.Schema(type=adk_types.Type.STRING, description="The start date in YYYY-MM-DD format."),
                    'end_date': adk_types.Schema(type=adk_types.Type.STRING, description="The end date in YYYY-MM-DD format."),
                },
                required=['start_date', 'end_date']
            ),
            returns=adk_types.Schema(
                type=adk_types.Type.ARRAY,
                items=drive_file_schema
            )
        )

        upload_file_declaration = adk_types.FunctionDeclaration(
            name="upload_drive_file",
            description="Uploads a local file to Google Drive.",
            parameters=adk_types.Schema(
                type=adk_types.Type.OBJECT,
                properties={
                    'file_path': adk_types.Schema(type=adk_types.Type.STRING, description="The local path to the file to be uploaded."),
                    'file_name': adk_types.Schema(type=adk_types.Type.STRING, description="The name the file should have in Google Drive."),
                    'mime_type': adk_types.Schema(type=adk_types.Type.STRING, description="The MIME type of the file (e.g., 'text/plain', 'image/jpeg')."),
                },
                required=['file_path', 'file_name', 'mime_type']
            ),
            returns=drive_file_schema
        )

        download_file_declaration = adk_types.FunctionDeclaration(
            name="download_drive_file",
            description="Downloads a file from Google Drive to a local path.",
            parameters=adk_types.Schema(
                type=adk_types.Type.OBJECT,
                properties={
                    'file_id': adk_types.Schema(type=adk_types.Type.STRING, description="The ID of the file to download."),
                    'destination_path': adk_types.Schema(type=adk_types.Type.STRING, description="The local path where the file should be saved."),
                },
                required=['file_id', 'destination_path']
            ),
            returns=adk_types.Schema(type=adk_types.Type.STRING, description="A confirmation message indicating success.")
        )

        delete_file_declaration = adk_types.FunctionDeclaration(
            name="delete_drive_file",
            description="Permanently deletes a file from Google Drive. This action cannot be undone.",
            parameters=adk_types.Schema(
                type=adk_types.Type.OBJECT,
                properties={
                    'file_id': adk_types.Schema(type=adk_types.Type.STRING, description="The ID of the file to delete."),
                },
                required=['file_id']
            ),
            returns=adk_types.Schema(type=adk_types.Type.STRING, description="A confirmation message indicating success.")
        )

        return [
            FunctionTool(
                func=self._list_files_by_date_range,
                declaration=list_files_declaration
            ),
            FunctionTool(
                func=self._upload_file,
                declaration=upload_file_declaration
            ),
            FunctionTool(
                func=self._download_file,
                declaration=download_file_declaration
            ),
            FunctionTool(
                func=self._delete_file,
                declaration=delete_file_declaration
            )
        ]
