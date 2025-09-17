import logging
from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.genai import types as adk_types
from typing import List

from src.components.toolsets.google_workspace.drive.service import GoogleDriveService
from src.components.toolsets.google_workspace.drive.models import DriveFile

logger = logging.getLogger(__name__)

class DriveToolset(BaseToolset):
    """A toolset for interacting with Google Drive."""

    def __init__(self, client_secrets_path: str, token_path: str = "token.json"):
        self.drive_service = GoogleDriveService(client_secrets_path, token_path)
        super().__init__()

    def _search_files(self, query: str) -> str:
        """Searches for files in Google Drive based on a query."""
        try:
            files = self.drive_service.search_files(query)
            return "\n".join([file.json() for file in files])
        except Exception as e:
            logger.error(f"Error searching Drive files: {e}")
            return f"Error searching Drive files: {e}"

    def _get_file_content(self, file_id: str) -> str:
        """Gets the content of a specific file by its ID."""
        try:
            content = self.drive_service.get_file_content(file_id)
            return content if content else "File content not found."
        except Exception as e:
            logger.error(f"Error getting Drive file content: {e}")
            return f"Error getting Drive file content: {e}"

    def get_tools(self) -> list[BaseTool]:
        """Returns a list of all the tool methods in this toolset."""
        search_files_declaration = adk_types.FunctionDeclaration(
            name="search_drive_files",
            description="Searches for files in Google Drive based on a query.",
            parameters=adk_types.Schema(
                type=adk_types.SchemaType.OBJECT,
                properties={
                    "query": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The query to search for files (e.g., 'type:document modifiedTime > \"2023-01-01T12:00:00\"').",
                    ),
                },
                required=["query"],
            ),
            returns=adk_types.Schema(
                type=adk_types.SchemaType.STRING,
                description="A JSON string containing a list of matching Drive files.",
            ),
        )

        get_file_content_declaration = adk_types.FunctionDeclaration(
            name="get_drive_file_content",
            description="Gets the content of a specific file by its ID.",
            parameters=adk_types.Schema(
                type=adk_types.SchemaType.OBJECT,
                properties={
                    "file_id": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The ID of the Drive file.",
                    ),
                },
                required=["file_id"],
            ),
            returns=adk_types.Schema(
                type=adk_types.SchemaType.STRING,
                description="The content of the file as a string, or 'File content not found.'.",
            ),
        )

        return [
            FunctionTool(
                func=self._search_files,
                declaration=search_files_declaration,
            ),
            FunctionTool(
                func=self._get_file_content,
                declaration=get_file_content_declaration,
            ),
        ]
