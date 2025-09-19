# src/components/toolsets/google_workspace/people/service.py

import logging
from typing import Dict, Any, Optional

from ..base_service import BaseGoogleService
from .models import SearchContactsResponse, SearchContactsQuery

logger = logging.getLogger(__name__)

class PeopleService(BaseGoogleService):
    def __init__(self, credential_manager):
        super().__init__(credential_manager)
        self.service_name = 'people'
        self.service_version = 'v1'
        self.scopes = ['https://www.googleapis.com/auth/contacts.readonly']

    async def search_contacts(self, user_id: str, query: SearchContactsQuery) -> Dict[str, Any]:
        logger.info(f"Searching contacts for user_id: {user_id} with query: '{query.query}'")
        service = await self.get_service(user_id)
        if not service:
            return {"status": "error", "message": "Failed to authenticate with Google."}

        try:
            # Gebruik model_dump() om de parameters naar de API te sturen
            api_params = query.model_dump(by_alias=True, exclude_none=True)
            results = service.people().searchContacts(**api_params).execute()

            # Valideer de API-respons met het Pydantic model
            return SearchContactsResponse.model_validate(results).model_dump()
        except Exception as e:
            logger.error(f"Failed to search contacts for user {user_id}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}