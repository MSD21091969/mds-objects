import logging
from typing import List, Dict, Any, Optional
import asyncio

from googleapiclient.errors import HttpError

from src.components.toolsets.google_workspace.base_service import BaseGoogleService
from src.core.managers.database_manager import DatabaseManager
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
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
        self.service_name = SERVICE_NAME
        self.service_version = SERVICE_VERSION
        self.scopes = SCOPES

    async def create_spreadsheet(self, user_id: str, title: str) -> Optional[GoogleSheet]:
        """
        Creates a new Google Spreadsheet.
        """
        service = await self.get_service_for_user(user_id)
        if not service:
            logger.error(f"Could not get authenticated Sheets service for user {user_id}.")
            return None
        try:
            spreadsheet_body = {
                'properties': {
                    'title': title
                }
            }
            spreadsheet = await asyncio.to_thread(
                service.spreadsheets().create(body=spreadsheet_body, fields='spreadsheetId,properties.title,spreadsheetUrl').execute
            )
            logger.info(f"Spreadsheet '{spreadsheet.get('properties', {}).get('title')}' created with ID: {spreadsheet.get('spreadsheetId')}")
            return GoogleSheet(**spreadsheet)
        except HttpError as error:
            logger.error(f"An error occurred while creating spreadsheet for user '{user_id}': {error}")
            return None

    async def get_spreadsheet(self, user_id: str, spreadsheet_id: str) -> Optional[GoogleSheet]:
        """
        Gets a Google Spreadsheet by its ID.
        """
        service = await self.get_service_for_user(user_id)
        if not service:
            logger.error(f"Could not get authenticated Sheets service for user {user_id}.")
            return None
        try:
            spreadsheet = await asyncio.to_thread(
                service.spreadsheets().get(spreadsheetId=spreadsheet_id, fields='spreadsheetId,properties.title,spreadsheetUrl').execute
            )
            return GoogleSheet(**spreadsheet)
        except HttpError as error:
            logger.error(f"An error occurred while getting spreadsheet {spreadsheet_id} for user '{user_id}': {error}")
            return None

    async def read_range(self, user_id: str, spreadsheet_id: str, range_name: str) -> Optional[ValueRange]:
        """
        Reads a range of values from a Google Spreadsheet.
        """
        service = await self.get_service_for_user(user_id)
        if not service:
            logger.error(f"Could not get authenticated Sheets service for user {user_id}.")
            return None
        try:
            result = await asyncio.to_thread(
                service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute
            )
            return ValueRange(**result)
        except HttpError as error:
            logger.error(f"An error occurred while reading range {range_name} from spreadsheet {spreadsheet_id} for user '{user_id}': {error}")
            return None

    async def write_range(self, user_id: str, spreadsheet_id: str, range_name: str, values: List[List[Any]]) -> Optional[Dict[str, Any]]:
        """
        Writes a range of values to a Google Spreadsheet.
        """
        service = await self.get_service_for_user(user_id)
        if not service:
            logger.error(f"Could not get authenticated Sheets service for user {user_id}.")
            return None
        try:
            body = {
                'values': values
            }
            result = await asyncio.to_thread(
                service.spreadsheets().values().update,
                spreadsheetId=spreadsheet_id, range=range_name,
                valueInputOption='RAW', body=body).execute()
            logger.info(f"Wrote {result.get('updatedCells')} cells to {spreadsheet_id}!{range_name}")
            return result
        except HttpError as error:
            logger.error(f"An error occurred while writing range {range_name} to spreadsheet {spreadsheet_id}: {error}")
            return None

    async def delete_spreadsheet(self, user_id: str, spreadsheet_id: str) -> bool:
        """
        Deletes a Google Spreadsheet by its ID. This requires the Drive API.
        """
        try:
            # Deleting a sheet is done via the Drive API. We assume a Drive service is available.
            # This is a simplified example. A better architecture might inject the Drive service.
            from src.components.toolsets.google_workspace.drive.service import GoogleDriveService
            drive_service = GoogleDriveService(self.db_manager)
            return await drive_service.delete_file(user_id=user_id, file_id=spreadsheet_id)
        except Exception as error:
            logger.error(f"An error occurred while attempting to delete spreadsheet {spreadsheet_id}: {error}")
            return False