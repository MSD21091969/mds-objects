# src/components/toolsets/google_workspace/credential_manager.py

import logging
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

from ....core.services.credential_store import DatabaseCredentialStore

logger = logging.getLogger(__name__)


class TokenError(Exception):
    """Base exception for token-related errors."""
    pass

class TokenNotFoundError(TokenError):
    """Raised when a token for a user cannot be found."""
    pass

class TokenRefreshError(TokenError):
    """Raised when a token cannot be refreshed."""
    pass


class GoogleCredentialManager:
    """
    Handles the logic of retrieving, validating, and refreshing Google OAuth credentials.
    """
    def __init__(self, credential_store: DatabaseCredentialStore):
        """
        Initializes the manager with a credential storage backend.

        Args:
            credential_store: An object that implements the CredentialStore interface.
        """
        self.credential_store = credential_store

    async def get_credentials(self, user_id: str, scopes: List[str]) -> Credentials:
        """
        Gets valid Google API credentials for a specific user and scopes.

        Args:
            user_id: The ID of the user.
            scopes: A list of OAuth scopes required for the API call.

        Returns:
            A valid google.oauth2.credentials.Credentials object.

        Raises:
            TokenNotFoundError: If no token is found for the user.
            TokenRefreshError: If the token is invalid or expired and cannot be refreshed.
        """
        token_info = await self.credential_store.get_user_token(user_id)
        if not token_info:
            raise TokenNotFoundError(f"No Google token found for user '{user_id}'.")

        try:
            creds = Credentials.from_authorized_user_info(token_info, scopes)

            if creds.valid:
                return creds

            if creds.expired and creds.refresh_token:
                logger.info(f"Refreshing expired Google token for user '{user_id}'.")
                creds.refresh(Request())
                # Persist the new token back to the store
                new_token_info = json.loads(creds.to_json())
                await self.credential_store.update_user_token(user_id, new_token_info)
                logger.info(f"Successfully refreshed and saved new token for user '{user_id}'.")
                return creds
            
            raise TokenRefreshError(f"Token for user '{user_id}' is invalid and has no refresh token.")

        except HttpError as e:
            logger.error(f"HTTP error during token refresh for user '{user_id}': {e}", exc_info=True)
            raise TokenRefreshError(f"An HTTP error occurred during token refresh: {e}")
        except Exception as e:
            logger.error(f"Failed to process credentials for user '{user_id}': {e}", exc_info=True)
            raise TokenError(f"An unexpected error occurred while processing credentials: {e}")