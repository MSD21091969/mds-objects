# MDSAPP/core/managers/state_manager.py

import logging
import datetime
import asyncio
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class StateManager:
    """
    Manages reading and writing persistent state, such as sync watermarks,
    to a dedicated document in Firestore.
    """
    def __init__(self, collection_name: str = "system_state", doc_id: str = "sync_watermarks"):
        from src.core.dependencies import get_database_manager
        self.db_manager = get_database_manager()
        self.collection_name = collection_name
        self.doc_id = doc_id
        self.doc_ref = self.db_manager.db.collection(self.collection_name).document(self.doc_id)

    async def get_watermarks(self) -> Dict[str, str]:
        """Fetches the entire watermark document from Firestore."""
        try:
            doc = await asyncio.to_thread(self.doc_ref.get)
            if doc.exists:
                return doc.to_dict()
            else:
                logger.warning(f"Watermark document '{self.doc_id}' not found. Will start with a default range.")
                return {}
        except Exception as e:
            logger.error(f"Error getting watermarks: {e}", exc_info=True)
            return {}

    async def update_watermark(self, service_name: str, timestamp: datetime.datetime):
        """Updates the timestamp for a specific service in the watermark document."""
        try:
            await asyncio.to_thread(self.doc_ref.set, {service_name: timestamp.isoformat()}, merge=True)
            logger.info(f"Successfully updated watermark for '{service_name}' to {timestamp.isoformat()}.")
        except Exception as e:
            logger.error(f"Error updating watermark for '{service_name}': {e}", exc_info=True)

    async def delete_watermarks(self):
        """Deletes the entire watermark document from Firestore."""
        try:
            await asyncio.to_thread(self.doc_ref.delete)
            logger.info(f"Watermark document '{self.doc_id}' deleted successfully.")
            return True
        except Exception as e:
            logger.error(f"Error deleting watermark document: {e}", exc_info=True)
            return False
