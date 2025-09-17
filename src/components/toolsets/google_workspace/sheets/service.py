import logging
from typing import List, Dict, Any, Optional

from googleapiclient.errors import HttpError

from src.components.toolsets.google_workspace.base_service import BaseGoogleService
from .models import GoogleSheet, ValueRange

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_NAME = 'sheets'
SERVICE_VERSION = 'v4'

class GoogleSheetsService(BaseGoogleService):
    """
    A service class to interact with the Google Sheets API, inheriting common logic
    from BaseGoogleService.
    """
    def __init__(self, client_secrets_path: str, token_path: str = "token.json"):
        super().__init__(client_secrets_path, token_path)
        self._build_service(SERVICE_NAME, SERVICE_VERSION, SCOPES)

    def create_spreadsheet(self, title: str) -> Optional[GoogleSheet]:
        """
        Creates a new Google Spreadsheet.
        """
        if not self.service:
            logger.error("GoogleSheetsService is not authenticated. Cannot create spreadsheet.")
            return None
        try:
            spreadsheet_body = {
                'properties': {
                    'title': title
                }
            }
            spreadsheet = self.service.spreadsheets().create(body=spreadsheet_body, fields='spreadsheetId,properties.title,spreadsheetUrl').execute()
            logger.info(f"Spreadsheet '{spreadsheet.get('properties', {}).get('title')}' created with ID: {spreadsheet.get('spreadsheetId')}")
            return GoogleSheet(**spreadsheet)
        except HttpError as error:
            logger.error(f"An error occurred while creating spreadsheet: {error}")
            return None

    def get_spreadsheet(self, spreadsheet_id: str) -> Optional[GoogleSheet]:
        """
        Gets a Google Spreadsheet by its ID.
        """
        if not self.service:
            logger.error("GoogleSheetsService is not authenticated. Cannot get spreadsheet.")
            return None
        try:
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id, fields='spreadsheetId,properties.title,spreadsheetUrl').execute()
            return GoogleSheet(**spreadsheet)
        except HttpError as error:
            logger.error(f"An error occurred while getting spreadsheet {spreadsheet_id}: {error}")
            return None

    def read_range(self, spreadsheet_id: str, range_name: str) -> Optional[ValueRange]:
        """
        Reads a range of values from a Google Spreadsheet.
        """
        if not self.service:
            logger.error("GoogleSheetsService is not authenticated. Cannot read range.")
            return None
        try:
            result = self.service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
            return ValueRange(**result)
        except HttpError as error:
            logger.error(f"An error occurred while reading range {range_name} from spreadsheet {spreadsheet_id}: {error}")
            return None

    def write_range(self, spreadsheet_id: str, range_name: str, values: List[List[Any]]) -> Optional[Dict[str, Any]]:
        """
        Writes a range of values to a Google Spreadsheet.
        """
        if not self.service:
            logger.error("GoogleSheetsService is not authenticated. Cannot write range.")
            return None
        try:
            body = {
                'values': values
            }
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id, range=range_name,
                valueInputOption='RAW', body=body).execute()
            logger.info(f"Wrote {result.get('updatedCells')} cells to {spreadsheet_id}!{range_name}")
            return result
        except HttpError as error:
            logger.error(f"An error occurred while writing range {range_name} to spreadsheet {spreadsheet_id}: {error}")
            return None

    def delete_spreadsheet(self, spreadsheet_id: str):
        """
        Deletes a Google Spreadsheet by its ID.
        """
        if not self.service:
            logger.error("GoogleSheetsService is not authenticated. Cannot delete spreadsheet.")
            return
        try:
            # The Sheets API does not have a direct delete method for spreadsheets.
            # Instead, you delete the file via the Drive API.
            # This would require the Drive API service to be available or to build it here.
            # For simplicity, we'll just log a message for now.
            logger.warning("Sheets API does not have a direct delete method. Use Drive API to delete spreadsheet files.")
            # If you want to implement this, you would need to:
            # from MDSAPP.core.services.drive_manager import GoogleDriveService
            # drive_service = GoogleDriveService(self.client_secrets_path, self.token_path)
            # drive_service.delete_file(spreadsheet_id)
        except Exception as error:
            logger.error(f"An error occurred while attempting to delete spreadsheet {spreadsheet_id}: {error}")