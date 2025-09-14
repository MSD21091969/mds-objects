# src/core/managers/database_manager.py

import logging
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Any, List, Optional
import asyncio

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages the connection to the Firestore database and provides a
    central point for all database interactions.
    """
    def __init__(self):
        self._db = None
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
            
            self._db = firestore.client()
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
