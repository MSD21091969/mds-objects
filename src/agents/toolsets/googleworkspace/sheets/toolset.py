# src/components/toolsets/google_workspace/sheets/google_sheets_toolset.py

import logging
from typing import Optional

from google.adk.tools import FunctionTool, BaseToolset, ToolContext, Parameter
from google.adk.tools.base_tool import BaseTool

from .service import SheetsService
from .models import GetValuesQuery

logger = logging.getLogger(__name__)

class SheetsToolset(BaseToolset):
    """Exposes SheetsService methods as ADK Tools."""
    def __init__(self, sheets_service: SheetsService):
        self.sheets_service = sheets_service

    async def get_tools(self, readonly_context: Optional[ReadonlyContext] = None) -> list[BaseTool]:
        
        async def _get_values_tool(spreadsheet_id: str, range: str, tool_context: ToolContext) -> dict:
            """
            This tool reads data from a specified range within a Google Sheet.
            It's useful for answering questions about spreadsheet content.
            """
            user_id = tool_context.invocation_context.session.user_id
            
            # De toolset verzamelt de parameters van de LLM en maakt er een model van
            validated_query = GetValuesQuery(spreadsheet_id=spreadsheet_id, range=range)
            
            # Geeft het gevalideerde Pydantic model object direct door aan de service
            return await self.sheets_service.get_values(user_id=user_id, query=validated_query)

        tools = [
            FunctionTool(
                func=_get_values_tool,
                name="sheets_get_values",
                description="Retrieves a list of values from a specified range in a Google Sheet.",
                parameters=[
                    Parameter(
                        name="spreadsheet_id",
                        type=str,
                        description="The unique ID of the Google Sheet to read from.",
                        required=True
                    ),
                    Parameter(
                        name="range",
                        type=str,
                        description="The range in A1-notation (e.g., 'Sheet1!A1:B10') to read. This parameter is required.",
                        required=True
                    )
                ]
            )
        ]
        return tools