import logging
from typing import Dict, Any, Optional, List, Union

from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.adk.tools import ToolContext

from src.core.models.user import User
from src.components.toolsets.google_workspace.sheets.service import GoogleSheetsService
from src.components.toolsets.google_workspace.sheets.models import GoogleSheet, ValueRange

logger = logging.getLogger(__name__)

class GoogleSheetsToolset(BaseToolset):
    """
    A toolset for interacting with Google Sheets.
    """
    def __init__(self, sheets_service: GoogleSheetsService):
        super().__init__()
        self._sheets_service = sheets_service

    def _get_user_id_from_context(self, tool_context: ToolContext) -> Optional[str]:
        """Helper to extract user ID from the tool context state."""
        user_json = tool_context.state.get("current_user")
        if not user_json:
            logger.warning("Could not find 'current_user' in tool context state.")
            return None
        try:
            user = User.model_validate_json(user_json)
            return user.username
        except Exception as e:
            logger.error(f"Failed to parse user from tool_context: {e}")
            return None

    async def create_spreadsheet(self, title: str, tool_context: ToolContext) -> Union[Dict[str, Any], str]:
        """
        Creates a new Google Spreadsheet.
        Args:
            title: The title for the new spreadsheet.
            tool_context: The runtime context.
        """
        user_id = self._get_user_id_from_context(tool_context)
        if not user_id:
            return "Error: Could not determine the user to perform this action for."

        logger.info(f"Toolset is calling sheets_service.create_spreadsheet for title: {title}")
        spreadsheet = await self._sheets_service.create_spreadsheet(user_id=user_id, title=title)
        if not spreadsheet:
            return f"Failed to create spreadsheet with title '{title}'."
        return spreadsheet.model_dump(by_alias=True)

    async def get_spreadsheet(self, spreadsheet_id: str, tool_context: ToolContext) -> Union[Dict[str, Any], str]:
        """
        Gets a Google Spreadsheet by its ID.
        Args:
            spreadsheet_id: The ID of the spreadsheet to retrieve.
            tool_context: The runtime context.
        """
        user_id = self._get_user_id_from_context(tool_context)
        if not user_id:
            return "Error: Could not determine the user to perform this action for."

        logger.info(f"Toolset is calling sheets_service.get_spreadsheet for ID: {spreadsheet_id}")
        spreadsheet = await self._sheets_service.get_spreadsheet(user_id=user_id, spreadsheet_id=spreadsheet_id)
        if not spreadsheet:
            return f"Spreadsheet with ID '{spreadsheet_id}' not found or access was denied."
        return spreadsheet.model_dump(by_alias=True)

    async def read_range(self, spreadsheet_id: str, range_name: str, tool_context: ToolContext) -> Union[Dict[str, Any], str]:
        """
        Reads a range of values from a Google Spreadsheet.
        Args:
            spreadsheet_id: The ID of the spreadsheet to read from.
            range_name: The A1 notation of the range to read (e.g., 'Sheet1!A1:B2').
            tool_context: The runtime context.
        """
        user_id = self._get_user_id_from_context(tool_context)
        if not user_id:
            return "Error: Could not determine the user to perform this action for."

        logger.info(f"Toolset is calling sheets_service.read_range for spreadsheet ID: {spreadsheet_id}, range: {range_name}")
        value_range = await self._sheets_service.read_range(user_id=user_id, spreadsheet_id=spreadsheet_id, range_name=range_name)
        if not value_range:
            return f"Could not read range '{range_name}' from spreadsheet '{spreadsheet_id}'."
        return value_range.model_dump()

    async def write_range(self, spreadsheet_id: str, range_name: str, values: List[List[Any]], tool_context: ToolContext) -> Union[Dict[str, Any], str]:
        """
        Writes a range of values to a Google Spreadsheet.
        Args:
            spreadsheet_id: The ID of the spreadsheet to write to.
            range_name: The A1 notation of the range to write (e.g., 'Sheet1!A1').
            values: A 2D list of values to write.
            tool_context: The runtime context.
        """
        user_id = self._get_user_id_from_context(tool_context)
        if not user_id:
            return "Error: Could not determine the user to perform this action for."

        logger.info(f"Toolset is calling sheets_service.write_range for spreadsheet ID: {spreadsheet_id}, range: {range_name}")
        result = await self._sheets_service.write_range(user_id=user_id, spreadsheet_id=spreadsheet_id, range_name=range_name, values=values)
        if not result:
            return f"Failed to write to range '{range_name}' in spreadsheet '{spreadsheet_id}'."
        return result

    async def delete_spreadsheet(self, spreadsheet_id: str, tool_context: ToolContext) -> bool:
        """
        Deletes a Google Spreadsheet by its ID. Returns True on success.
        Args:
            spreadsheet_id: The ID of the spreadsheet to delete.
            tool_context: The runtime context.
        """
        user_id = self._get_user_id_from_context(tool_context)
        if not user_id:
            logger.error("Cannot delete spreadsheet: user ID not found in context.")
            return False

        logger.info(f"Toolset is calling sheets_service.delete_spreadsheet for ID: {spreadsheet_id}")
        return await self._sheets_service.delete_spreadsheet(user_id=user_id, spreadsheet_id=spreadsheet_id)

    async def get_tools(self, tool_context: "ToolContext") -> list[BaseTool]:
        """
        Returns a list of tools provided by this toolset.
        """
        return [
            FunctionTool(func=self.create_spreadsheet),
            FunctionTool(func=self.get_spreadsheet),
            FunctionTool(func=self.read_range),
            FunctionTool(func=self.write_range),
            FunctionTool(func=self.delete_spreadsheet),
        ]
