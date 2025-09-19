# src/core/services/credential_store.py

import abc
import json
from typing import Optional, Dict, Any

from core.managers.database_manager import DatabaseManager


class CredentialStore(abc.ABC):
    """Abstract base class for storing and retrieving user credentials."""

    @abc.abstractmethod
    async def get_user_token(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the token information for a given user."""
        pass

    @abc.abstractmethod
    async def update_user_token(self, user_id: str, token_info: Dict[str, Any]) -> None:
        """Updates or stores the token information for a given user."""
        pass


class DatabaseCredentialStore(CredentialStore):
    """
    A concrete implementation of CredentialStore that uses DatabaseManager
    to interact with a database (e.g., Firestore).
    """
    def __init__(self, db_manager: DatabaseManager):
        """
        Initializes the DatabaseCredentialStore.

        Args:
            db_manager: An instance of DatabaseManager.
        """
        self.db_manager = db_manager

    async def get_user_token(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the user's Google token from the 'users' collection.

        Args:
            user_id: The ID of the user.

        Returns:
            A dictionary with the token information, or None if not found.
        """
        user_data = await self.db_manager.get("users", user_id)
        if user_data and "google_token" in user_data:
            return json.loads(user_data["google_token"])
        return None

    async def update_user_token(self, user_id: str, token_info: Dict[str, Any]) -> None:
        """
        Updates the user's Google token in the 'users' collection.

        Args:
            user_id: The ID of the user.
            token_info: The token dictionary to store.
        """
        await self.db_manager.update("users", user_id, {"google_token": json.dumps(token_info)})