# src/components/toolsets/google_workspace/sheets/service.py

import logging
from typing import Dict, Any

from ..base_service import BaseGoogleService
from .models import Spreadsheet, GetValuesQuery

logger = logging.getLogger(__name__)

class SheetsService(BaseGoogleService):
    def __init__(self, credential_manager):
        super().__init__(credential_manager)
        self.service_name = 'sheets'
        self.service_version = 'v4'
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']

    async def get_values(self, user_id: str, query: GetValuesQuery) -> Dict[str, Any]:
        """Reads data from a specified range within a Google Sheet."""
        logger.info(f"Retrieving values from spreadsheet {query.spreadsheet_id} for user {user_id}")
        service = await self.get_service(user_id)
        if not service:
            return {"status": "error", "message": "Failed to authenticate with Google."}

        try:
            # We gebruiken model_dump() om de parameters uit het Pydantic model te halen
            result = service.spreadsheets().values().get(**query.model_dump(by_alias=True, exclude_none=True)).execute()
            return result
        except Exception as e:
            logger.error(f"Failed to get values for user {user_id}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}