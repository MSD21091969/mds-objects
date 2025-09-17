# MDSAPP/core/models/google/sheets.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any

class GoogleSheet(BaseModel):
    """
    Represents a Google Sheet resource.
    """
    id: str = Field(..., alias='spreadsheetId')
    title: str
    url: Optional[str] = Field(None, alias='spreadsheetUrl')
    # You can add more fields as needed, e.g., properties, sheets, etc.

    model_config = ConfigDict(populate_by_name=True)

class SheetProperties(BaseModel):
    """
    Represents properties of a single sheet within a Google Sheet.
    """
    sheet_id: int = Field(..., alias='sheetId')
    title: str
    index: int
    sheet_type: str = Field(..., alias='sheetType')

    model_config = ConfigDict(populate_by_name=True)

class ValueRange(BaseModel):
    """
    Represents a range of cell values in a sheet.
    """
    range: str
    major_dimension: Optional[str] = Field(None, alias='majorDimension')
    values: List[List[Any]]

    model_config = ConfigDict(populate_by_name=True)
