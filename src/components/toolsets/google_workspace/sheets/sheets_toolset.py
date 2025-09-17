import logging
from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.genai import types as adk_types
from typing import List, Dict, Any

from src.components.toolsets.google_workspace.sheets.service import GoogleSheetsService

logger = logging.getLogger(__name__)

class SheetsToolset(BaseToolset):
    """A toolset for interacting with Google Sheets."""

    def __init__(self, client_secrets_path: str, token_path: str = "token.json"):
        self.sheets_service = GoogleSheetsService(client_secrets_path, token_path)
        super().__init__()

    def _read_sheet_data(self, spreadsheet_id: str, range_name: str) -> str:
        """Reads data from a specified range in a Google Sheet."""
        try:
            data = self.sheets_service.read_sheet_data(spreadsheet_id, range_name)
            return str(data) if data else "No data found."
        except Exception as e:
            logger.error(f"Error reading sheet data: {e}")
            return f"Error reading sheet data: {e}"

    def _write_sheet_data(self, spreadsheet_id: str, range_name: str, values: List[List[Any]]) -> str:
        """Writes data to a specified range in a Google Sheet."""
        try:
            response = self.sheets_service.write_sheet_data(spreadsheet_id, range_name, values)
            return str(response) if response else "Failed to write data."
        except Exception as e:
            logger.error(f"Error writing sheet data: {e}")
            return f"Error writing sheet data: {e}"

    def get_tools(self) -> list[BaseTool]:
        """Returns a list of all the tool methods in this toolset."""
        read_sheet_data_declaration = adk_types.FunctionDeclaration(
            name="read_google_sheet_data",
            description="Reads data from a specified range in a Google Sheet.",
            parameters=adk_types.Schema(
                type=adk_types.SchemaType.OBJECT,
                properties={
                    "spreadsheet_id": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The ID of the Google Spreadsheet.",
                    ),
                    "range_name": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The A1 notation of the range to read (e.g., 'Sheet1!A1:B10').",
                    ),
                },
                required=["spreadsheet_id", "range_name"],
            ),
            returns=adk_types.Schema(
                type=adk_types.SchemaType.STRING,
                description="A string representation of the data read from the sheet, or 'No data found.'.",
            ),
        )

        write_sheet_data_declaration = adk_types.FunctionDeclaration(
            name="write_google_sheet_data",
            description="Writes data to a specified range in a Google Sheet.",
            parameters=adk_types.Schema(
                type=adk_types.SchemaType.OBJECT,
                properties={
                    "spreadsheet_id": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The ID of the Google Spreadsheet.",
                    ),
                    "range_name": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The A1 notation of the range to write to (e.g., 'Sheet1!A1:B10').",
                    ),
                    "values": adk_types.Schema(
                        type=adk_types.SchemaType.ARRAY,
                        description="A list of lists representing the data to write.",
                        items=adk_types.Schema(
                            type=adk_types.SchemaType.ARRAY,
                            items=adk_types.Schema(type=adk_types.SchemaType.STRING) # Assuming string values for simplicity
                        )
                    ),
                },
                required=["spreadsheet_id", "range_name", "values"],
            ),
            returns=adk_types.Schema(
                type=adk_types.SchemaType.STRING,
                description="A string representation of the write response, or 'Failed to write data.'.",
            ),
        )

        return [
            FunctionTool(
                func=self._read_sheet_data,
                declaration=read_sheet_data_declaration,
            ),
            FunctionTool(
                func=self._write_sheet_data,
                declaration=write_sheet_data_declaration,
            ),
        ]
