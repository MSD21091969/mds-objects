# src/components/toolsets/google_workspace/base_service.py

import logging
from typing import List, Optional

from googleapiclient.discovery import build, Resource

from .credential_manager import GoogleCredentialManager, TokenError

logger = logging.getLogger(__name__)

class BaseGoogleService:
    """
    A refactored base class for Google API services that handles service building logic.
    It relies on a CredentialManager to handle all authentication aspects.
    """
    def __init__(self, credential_manager: GoogleCredentialManager):
        """
        Initializes the base service.

        Args:
            credential_manager: An instance of GoogleCredentialManager.
        """
        self.credential_manager = credential_manager
        self.service_name: str = ""
        self.service_version: str = ""
        self.scopes: List[str] = []

    async def get_service(self, user_id: str) -> Optional[Resource]:
        """
        Builds and returns an authenticated Google API service object for a specific user.

        Args:
            user_id: The ID of the user for whom to build the service.

        Returns:
            An authenticated Google API service resource, or None if authentication fails.
        """
        try:
            credentials = await self.credential_manager.get_credentials(user_id, self.scopes)
            service = build(self.service_name, self.service_version, credentials=credentials)
            logger.debug(f"Successfully built service '{self.service_name}' for user '{user_id}'.")
            return service
        except TokenError as e:
            logger.error(f"Authentication failed for user '{user_id}' when building service '{self.service_name}': {e}")
            # The tool calling this method should catch this and return a structured error to the agent.
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred building service '{self.service_name}' for user '{user_id}': {e}", exc_info=True)
            return None