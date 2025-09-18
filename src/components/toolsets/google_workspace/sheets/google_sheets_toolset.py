import logging
from typing import Dict, Any, Optional, List

from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.adk.tools import ToolContext
from google.genai import types as adk_types

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

    def _create_spreadsheet(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Creates a new Google Spreadsheet.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling sheets_service.create_spreadsheet for title: {title}")
        spreadsheet = self.sheets_service.create_spreadsheet(title)
        return spreadsheet.model_dump() if spreadsheet else None

    def _get_spreadsheet(self, spreadsheet_id: str) -> Optional[Dict[str, Any]]:
        """
        Gets a Google Spreadsheet by its ID.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling sheets_service.get_spreadsheet for ID: {spreadsheet_id}")
        spreadsheet = self.sheets_service.get_spreadsheet(spreadsheet_id)
        return spreadsheet.model_dump() if spreadsheet else None

    def _read_range(self, spreadsheet_id: str, range_name: str) -> Optional[Dict[str, Any]]:
        """
        Reads a range of values from a Google Spreadsheet.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling sheets_service.read_range for spreadsheet ID: {spreadsheet_id}, range: {range_name}")
        value_range = self.sheets_service.read_range(spreadsheet_id, range_name)
        return value_range.model_dump() if value_range else None

    def _write_range(self, spreadsheet_id: str, range_name: str, values: List[List[Any]]) -> Optional[Dict[str, Any]]:
        """
        Writes a range of values to a Google Spreadsheet.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling sheets_service.write_range for spreadsheet ID: {spreadsheet_id}, range: {range_name}")
        return self.sheets_service.write_range(spreadsheet_id, range_name, values)

    def _delete_spreadsheet(self, spreadsheet_id: str) -> str:
        """
        Deletes a Google Spreadsheet by its ID.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling sheets_service.delete_spreadsheet for ID: {spreadsheet_id}")
        self.sheets_service.delete_spreadsheet(spreadsheet_id)
        return f"Spreadsheet with ID '{spreadsheet_id}' deleted successfully."

    def get_tools(self, tool_context: "ToolContext") -> list[BaseTool]:
        """
        Returns a list of tools provided by this toolset.
        """
        google_sheet_schema = adk_types.Schema(
            type=adk_types.Type.OBJECT,
            description="Represents a Google Sheets spreadsheet.",
            properties={
                'spreadsheet_id': adk_types.Schema(type=adk_types.Type.STRING, description="The unique ID of the spreadsheet."),
                'spreadsheet_url': adk_types.Schema(type=adk_types.Type.STRING, description="The URL of the spreadsheet."),
                'properties': adk_types.Schema(
                    type=adk_types.Type.OBJECT,
                    properties={
                        'title': adk_types.Schema(type=adk_types.Type.STRING, description="The title of the spreadsheet.")
                    }
                )
            }
        )

        value_range_schema = adk_types.Schema(
            type=adk_types.Type.OBJECT,
            description="Represents a range of values from a sheet.",
            properties={
                'range': adk_types.Schema(type=adk_types.Type.STRING, description="The A1 notation of the range that was read."),
                'major_dimension': adk_types.Schema(type=adk_types.Type.STRING, description="The major dimension of the values (ROWS or COLUMNS)."),
                'values': adk_types.Schema(type=adk_types.Type.ARRAY, items=adk_types.Schema(type=adk_types.Type.ARRAY, items=adk_types.Schema(type=adk_types.Type.STRING)), description="The data that was read or written.")
            }
        )

        create_spreadsheet_declaration = adk_types.FunctionDeclaration(
            name="create_google_sheet",
            description="Creates a new, empty Google Sheets spreadsheet with a specified title.",
            parameters=adk_types.Schema(
                type=adk_types.Type.OBJECT,
                properties={
                    'title': adk_types.Schema(type=adk_types.Type.STRING, description="The title for the new spreadsheet."),
                },
                required=['title']
            ),
            returns=google_sheet_schema
        )

        get_spreadsheet_declaration = adk_types.FunctionDeclaration(
            name="get_google_sheet",
            description="Retrieves metadata for a specific Google Sheets spreadsheet by its ID.",
            parameters=adk_types.Schema(
                type=adk_types.Type.OBJECT,
                properties={
                    'spreadsheet_id': adk_types.Schema(type=adk_types.Type.STRING, description="The ID of the spreadsheet to retrieve."),
                },
                required=['spreadsheet_id']
            ),
            returns=google_sheet_schema
        )

        read_range_declaration = adk_types.FunctionDeclaration(
            name="read_google_sheet_range",
            description="Reads a range of values from a Google Sheet. Use A1 notation (e.g., 'Sheet1!A1:B2').",
            parameters=adk_types.Schema(
                type=adk_types.Type.OBJECT,
                properties={
                    'spreadsheet_id': adk_types.Schema(type=adk_types.Type.STRING, description="The ID of the spreadsheet to read from."),
                    'range_name': adk_types.Schema(type=adk_types.Type.STRING, description="The range to read in A1 notation (e.g., 'Sheet1!A1:C5')."),
                },
                required=['spreadsheet_id', 'range_name']
            ),
            returns=value_range_schema
        )

        write_range_declaration = adk_types.FunctionDeclaration(
            name="write_google_sheet_range",
            description="Writes a range of values to a Google Sheet. The input values should be a list of lists.",
            parameters=adk_types.Schema(
                type=adk_types.Type.OBJECT,
                properties={
                    'spreadsheet_id': adk_types.Schema(type=adk_types.Type.STRING, description="The ID of the spreadsheet to write to."),
                    'range_name': adk_types.Schema(type=adk_types.Type.STRING, description="The range to write in A1 notation (e.g., 'Sheet1!A1')."),
                    'values': adk_types.Schema(type=adk_types.Type.ARRAY, items=adk_types.Schema(type=adk_types.Type.ARRAY, items=adk_types.Schema(type=adk_types.Type.ANY)), description="A list of lists representing the rows and cells to write."),
                },
                required=['spreadsheet_id', 'range_name', 'values']
            ),
            returns=adk_types.Schema(type=adk_types.Type.OBJECT, description="An object containing details about the write operation.")
        )

        delete_spreadsheet_declaration = adk_types.FunctionDeclaration(
            name="delete_google_sheet",
            description="Permanently deletes a Google Sheet. This action cannot be undone.",
            parameters=adk_types.Schema(
                type=adk_types.Type.OBJECT,
                properties={
                    'spreadsheet_id': adk_types.Schema(type=adk_types.Type.STRING, description="The ID of the spreadsheet to delete."),
                },
                required=['spreadsheet_id']
            ),
            returns=adk_types.Schema(type=adk_types.Type.STRING, description="A confirmation message indicating success.")
        )

        return [
            FunctionTool(func=self._create_spreadsheet, declaration=create_spreadsheet_declaration),
            FunctionTool(func=self._get_spreadsheet, declaration=get_spreadsheet_declaration),
            FunctionTool(func=self._read_range, declaration=read_range_declaration),
            FunctionTool(func=self._write_range, declaration=write_range_declaration),
            FunctionTool(func=self._delete_spreadsheet, declaration=delete_spreadsheet_declaration),
        ]
