# src/components/toolsets/google_workspace/sheets/models.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Sheet(BaseModel):
    """
    Represents a single sheet within a Google Spreadsheet.
    """
    sheetId: int
    title: str
    index: int
    
class Spreadsheet(BaseModel):
    """
    Represents a Google Spreadsheet resource.
    """
    spreadsheetId: str
    properties: Dict[str, Any]
    sheets: Optional[List[Sheet]] = None

class GetValuesQuery(BaseModel):
    """Input validation model for the get_values tool."""
    spreadsheet_id: str = Field(..., description="The ID of the spreadsheet.")
    range: str = Field(..., description="The A1-notation of the range to retrieve, e.g., 'Sheet1!A1:B10'.")

class UpdateValuesQuery(BaseModel):
    """Input validation model for the update_values tool."""
    spreadsheet_id: str = Field(..., description="The ID of the spreadsheet to update.")
    range: str = Field(..., description="The A1-notation of the range to update.")
    values: List[List[Any]] = Field(..., description="The list of lists representing the rows and values to write.")