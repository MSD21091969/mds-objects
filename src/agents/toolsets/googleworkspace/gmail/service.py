# src/components/toolsets/google_workspace/gmail/service.py

import logging
from typing import Dict, Any, Optional

from google.api_core.exceptions import GoogleAPIError
from ..base_service import BaseGoogleService
from .models import GmailMessage, ListMessagesQuery, GetMessageQuery

logger = logging.getLogger(__name__)

class GmailService(BaseGoogleService):
    def __init__(self, credential_manager):
        super().__init__(credential_manager)
        self.service_name = 'gmail'
        self.service_version = 'v1'
        self.scopes = ['https://www.googleapis.com/auth/gmail.readonly']

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Retrieves the user's Gmail profile information."""
        logger.info(f"Retrieving user profile for user {user_id}")
        service = await self.get_service(user_id)
        if not service:
            return {"status": "error", "message": "Failed to authenticate with Google."}
        try:
            profile = service.users().getProfile(userId='me').execute()
            return profile
        except GoogleAPIError as e:
            logger.error(f"Google API Error when getting profile for user {user_id}: {e}", exc_info=True)
            return {"status": "error", "message": f"Google API error: {e}"}
        except Exception as e:
            logger.error(f"Failed to get user profile for {user_id}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def list_messages(self, user_id: str, query: ListMessagesQuery) -> Dict[str, Any]:
        """Lists email messages in the user's mailbox that match a search query."""
        logger.info(f"Listing messages for user {user_id} with query: '{query.query}'")
        service = await self.get_service(user_id)
        if not service:
            return {"status": "error", "message": "Failed to authenticate with Google."}
        try:
            api_params = query.model_dump(by_alias=True, exclude_none=True)
            results = service.users().messages().list(userId='me', **api_params).execute()
            return results
        except GoogleAPIError as e:
            logger.error(f"Google API Error when listing messages for user {user_id}: {e}", exc_info=True)
            return {"status": "error", "message": f"Google API error: {e}"}
        except Exception as e:
            logger.error(f"Failed to list messages for user {user_id}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def get_message(self, user_id: str, query: GetMessageQuery) -> Dict[str, Any]:
        """Retrieves the full content of a specific email message by its ID."""
        logger.info(f"Retrieving message {query.message_id} for user {user_id}")
        service = await self.get_service(user_id)
        if not service:
            return {"status": "error", "message": "Failed to authenticate with Google."}
        try:
            api_params = query.model_dump(by_alias=True, exclude_none=True)
            message = service.users().messages().get(userId='me', **api_params).execute()
            return message
        except GoogleAPIError as e:
            logger.error(f"Google API Error when getting message {query.message_id} for user {user_id}: {e}", exc_info=True)
            return {"status": "error", "message": f"Google API error: {e}"}
        except Exception as e:
            logger.error(f"Failed to get message {query.message_id} for {user_id}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}