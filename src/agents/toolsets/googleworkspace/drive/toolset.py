# src/components/toolsets/google_workspace/drive/google_drive_toolset.py

import logging
from typing import Optional

from google.adk.tools import FunctionTool, BaseToolset, ToolContext, ReadonlyContext, Parameter
from google.adk.tools.base_tool import BaseTool

from .service import DriveService
from .models import ListFilesQuery

logger = logging.getLogger(__name__)

class DriveToolset(BaseToolset):
    """Exposes DriveService methods as ADK Tools."""
    def __init__(self, drive_service: DriveService):
        self.drive_service = drive_service

    async def get_tools(self, readonly_context: Optional[ReadonlyContext] = None) -> list[BaseTool]:
        
        async def _list_files_tool(
            query: Optional[str] = None, 
            page_size: Optional[int] = 10, 
            corpora: Optional[str] = 'user',
            tool_context: ToolContext = None
        ) -> dict:
            """
            This tool searches for and lists files or folders in the user's Google Drive.
            It's useful for finding specific documents, spreadsheets, or other files.
            """
            user_id = tool_context.invocation_context.session.user_id
            validated_input = ListFilesQuery(
                query=query, 
                page_size=page_size, 
                corpora=corpora
            )
            return await self.drive_service.list_files(
                user_id=user_id, 
                query=validated_input
            )

        tools = [
            FunctionTool(
                func=_list_files_tool,
                name="drive_list_files",
                description="Searches for files and folders in the user's Google Drive. Use this to find documents, spreadsheets, images, or other file types.",
                parameters=[
                    Parameter(
                        name="query",
                        type=str,
                        description="A search query in Google Drive query language. This is a powerful search syntax that allows filtering by name, type, and content.",
                        required=False
                    ),
                    Parameter(
                        name="page_size",
                        type=int,
                        description="The maximum number of files to return. The default is 10.",
                        required=False
                    ),
                    Parameter(
                        name="corpora",
                        type=str,
                        description="The corpus of files to search, either 'user' for personal files or 'domain' for shared files. Defaults to 'user'.",
                        required=False
                    )
                ]
            )
        ]
        return tools