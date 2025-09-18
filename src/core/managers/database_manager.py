import logging
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Any, List, Optional, Dict
import asyncio
import os

from src.components.casefile.models import Casefile
from src.core.models.user import UserInDB

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages the connection to the Firestore database and provides a
    central point for all database interactions.
    """
    def __init__(self):
        self._db = None
        self.users_collection_name = "users"
        self.casefiles_collection_name = "casefiles"
        self._connect()

    def _connect(self):
        """
        Initializes the connection to the Firestore database using the
        application's default credentials.
        """
        try:
            if not firebase_admin._apps:
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized successfully.")
            
            self._db = firestore.client(database_id='mds-objects')
            logger.info("Successfully connected to Firestore.")
        except Exception as e:
            logger.critical(f"Failed to connect to Firestore: {e}", exc_info=True)
            raise

    @property
    def db(self) -> Any:
        """Provides public access to the Firestore client instance."""
        if not self._db:
            self._connect()
        return self._db

    async def get(self, collection: str, doc_id: str) -> Optional[dict]:
        """Retrieves a single document from a collection."""
        doc_ref = self.db.collection(collection).document(doc_id)
        doc = await asyncio.to_thread(doc_ref.get)
        if doc.exists:
            return doc.to_dict()
        return None

    async def get_all(self, collection: str) -> List[dict]:
        """Retrieves all documents from a collection."""
        collection_ref = self.db.collection(collection)
        docs = await asyncio.to_thread(collection_ref.stream)
        return [doc.to_dict() for doc in docs]

    async def save(self, collection: str, doc_id: str, data: dict) -> None:
        """Saves (creates or overwrites) a document in a collection."""
        doc_ref = self.db.collection(collection).document(doc_id)
        await asyncio.to_thread(doc_ref.set, data)
        logger.info(f"Document '{doc_id}' saved in collection '{collection}'.")

    async def delete(self, collection: str, doc_id: str) -> bool:
        """Deletes a document from a collection."""
        doc_ref = self.db.collection(collection).document(doc_id)
        doc = await asyncio.to_thread(doc_ref.get)
        if doc.exists:
            await asyncio.to_thread(doc_ref.delete)
            logger.info(f"Document '{doc_id}' deleted from collection '{collection}'.")
            return True
        return False

    async def save_casefile(self, casefile: Casefile) -> None:
        """Saves a Casefile Pydantic model to the casefiles collection."""
        await self.save(
            self.casefiles_collection_name,
            casefile.id,
            casefile.model_dump(exclude_none=True)
        )

    async def delete_casefile(self, casefile_id: str) -> bool:
        """Deletes a casefile document from the casefiles collection."""
        return await self.delete(self.casefiles_collection_name, casefile_id)

    async def load_casefile(self, casefile_id: str) -> Optional[Casefile]:
        """
        Loads a specific casefile document from Firestore and converts it
        into a Casefile Pydantic model.
        """
        casefile_data = await self.get(self.casefiles_collection_name, casefile_id)
        if casefile_data:
            return Casefile(**casefile_data)
        return None

    async def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        """
        Loads a specific user document from Firestore and converts it
        into a UserInDB Pydantic model.
        """
        user_data = await self.get(self.users_collection_name, username)
        if user_data:
            return UserInDB(**user_data)
        return None
