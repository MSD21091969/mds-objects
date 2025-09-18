# src/components/toolsets/google_workspace/base_service.py

import logging
import os
import json
from typing import List, Optional, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

from src.core.managers.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class BaseGoogleService:
    """
    A base class for Google API services that handles user-specific authentication
    and service building logic.
    """
    def __init__(self, db_manager: DatabaseManager):
        """
        Initializes the base service with a database manager.

        Args:
            db_manager: An instance of DatabaseManager to interact with the database.
        """
        self.db_manager = db_manager
        self.service_name: str = ""
        self.service_version: str = ""
        self.scopes: List[str] = []

    async def get_service_for_user(self, user_id: str) -> Optional[Resource]:
        """
        Builds and returns a Google API service object for a specific user.

        It retrieves the user's OAuth token from the database, refreshes it if
        necessary, and then builds the service object.

        Args:
            user_id: The username or ID of the user to build the service for.

        Returns:
            An authenticated Google API service resource, or None if authentication fails.
        """
        user_data = await self.db_manager.get("users", user_id)
        if not user_data or "google_token" not in user_data:
            logger.error(f"No Google token found for user '{user_id}' in the database.")
            return None

        try:
            # The token is stored as a JSON string in the database
            token_info = json.loads(user_data["google_token"])
            creds = Credentials.from_authorized_user_info(token_info, self.scopes)

            if not creds.valid:
                if creds.expired and creds.refresh_token:
                    logger.info(f"Refreshing expired Google token for user '{user_id}'.")
                    creds.refresh(Request())
                    # Persist the new token back to the database
                    new_token_info = json.loads(creds.to_json())
                    await self.db_manager.update("users", user_id, {"google_token": json.dumps(new_token_info)})
                    logger.info(f"Successfully refreshed and saved new token for user '{user_id}'.")
                else:
                    logger.error(f"Google token for user '{user_id}' is invalid and cannot be refreshed.")
                    # Here you might want to trigger a re-authentication flow for the user.
                    return None

            service = build(self.service_name, self.service_version, credentials=creds)
            logger.debug(f"Successfully built service '{self.service_name}' for user '{user_id}'.")
            return service

        except (json.JSONDecodeError, KeyError, HttpError) as e:
            logger.error(f"Failed to build Google service for user '{user_id}': {e}", exc_info=True)
            return None