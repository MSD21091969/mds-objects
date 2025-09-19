# src/components/toolsets/google_workspace/calendar/service.py

import logging
from typing import Dict, Any, Optional

from google.api_core.exceptions import GoogleAPIError
from ..base_service import BaseGoogleService
from .models import EventList, ListEventsQuery

logger = logging.getLogger(__name__)


class CalendarService(BaseGoogleService):
    """Service layer for handling Google Calendar business logic."""
    def __init__(self, credential_manager):
        super().__init__(credential_manager)
        self.service_name = 'calendar'
        self.service_version = 'v3'
        self.scopes = ['https://www.googleapis.com/auth/calendar.readonly']

    async def list_events(self, user_id: str, query: ListEventsQuery) -> Dict[str, Any]:
        """Lists events on a user's calendar based on a validated query model."""
        logger.info(f"Listing calendar events for user_id: {user_id}")
        service = await self.get_service(user_id)
        if not service:
            return {"status": "error", "message": "Failed to authenticate with Google."}

        try:
            # Converteer het Pydantic-model naar een dictionary voor de API-aanroep
            # 'exclude_none=True' zorgt ervoor dat alleen ingevulde velden worden meegenomen
            # De API aanroep wordt nu dynamisch gebouwd op basis van de query
            api_params = query.model_dump(by_alias=True, exclude_none=True)
            
            # De Google API-client library heeft specifieke parameter namen
            # Soms moet je deze mappen, maar in dit geval komen ze overeen.
            
            # Voeg vaste parameters toe die niet in het model staan
            api_params['singleEvents'] = True
            api_params['orderBy'] = 'startTime'

            events_result = service.events().list(**api_params).execute()

            # Valideer en converteer de API-respons naar het EventList-model
            return EventList.model_validate(events_result).model_dump()
        except GoogleAPIError as e:
            logger.error(f"Google API Error when listing events for user {user_id}: {e}", exc_info=True)
            return {"status": "error", "message": f"Google API error: {e}"}
        except Exception as e:
            logger.error(f"Failed to list calendar events for user {user_id}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}