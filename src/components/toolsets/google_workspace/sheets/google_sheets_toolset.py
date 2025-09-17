import logging
from typing import Dict, Any, Optional, List

from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool

from src.components.toolsets.google_workspace.sheets.service import GoogleSheetsService
from src.components.toolsets.google_workspace.sheets.models import GoogleSheet, ValueRange

logger = logging.getLogger(__name__)

class GoogleSheetsToolset(BaseToolset):
    """
    A toolset for interacting with Google Sheets.
    """
    def __init__(self, sheets_service: Optional[GoogleSheetsService] = None):
        super().__init__()
        self.sheets_service = sheets_service

    def _ensure_service(self):
        """Checks if the Sheets service is available."""
        if not self.sheets_service:
            raise ConnectionError("GoogleSheetsService is not available.")

    def create_spreadsheet(self, title: str) -> Optional[GoogleSheet]:
        """
        Creates a new Google Spreadsheet.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling sheets_service.create_spreadsheet for title: {title}")
        return self.sheets_service.create_spreadsheet(title)

    def get_spreadsheet(self, spreadsheet_id: str) -> Optional[GoogleSheet]:
        """
        Gets a Google Spreadsheet by its ID.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling sheets_service.get_spreadsheet for ID: {spreadsheet_id}")
        return self.sheets_service.get_spreadsheet(spreadsheet_id)

    def read_range(self, spreadsheet_id: str, range_name: str) -> Optional[ValueRange]:
        """
        Reads a range of values from a Google Spreadsheet.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling sheets_service.read_range for spreadsheet ID: {spreadsheet_id}, range: {range_name}")
        return self.sheets_service.read_range(spreadsheet_id, range_name)

    def write_range(self, spreadsheet_id: str, range_name: str, values: List[List[Any]]) -> Optional[Dict[str, Any]]:
        """
        Writes a range of values to a Google Spreadsheet.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling sheets_service.write_range for spreadsheet ID: {spreadsheet_id}, range: {range_name}")
        return self.sheets_service.write_range(spreadsheet_id, range_name, values)

    def delete_spreadsheet(self, spreadsheet_id: str):
        """
        Deletes a Google Spreadsheet by its ID.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling sheets_service.delete_spreadsheet for ID: {spreadsheet_id}")
        self.sheets_service.delete_spreadsheet(spreadsheet_id)

    def get_tools(self) -> list[BaseTool]:
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
