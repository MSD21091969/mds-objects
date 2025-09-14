# src/core/services/firestore_session_service.py

import logging
import asyncio
from typing import Optional, List, Dict, Any
from typing_extensions import override

from google.cloud.firestore_v1.base_query import FieldFilter
from google.adk.sessions import Session, BaseSessionService
from google.adk.sessions.base_session_service import GetSessionConfig
from google.adk.events import Event

from src.core.managers.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class FirestoreSessionService(BaseSessionService):
    """
    Manages ADK Session objects in Firestore, implementing the BaseSessionService
    interface for direct use with ADK Runners.
    """
    _collection_name = "adk_sessions"

    def __init__(self, db_manager: DatabaseManager):
        self._db_manager = db_manager
        self._collection_ref = self._db_manager.db.collection(self._collection_name)
        logger.info(f"FirestoreSessionService initialized for collection: '{self._collection_name}'")

    @override
    async def create_session(
        self, app_name: str, user_id: str, session_id: Optional[str] = None,
        state: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Session:
        """Creates a new Session object and saves it to Firestore."""
        session = Session(app_name=app_name, user_id=user_id, id=session_id, state=state, **kwargs)
        
        session_data = session.model_dump(exclude_none=True)
        await self._db_manager.save(self._collection_name, session.id, session_data)
        
        logger.info(f"Created and saved session '{session.id}' to Firestore.")
        return session

    @override
    async def get_session(
        self, app_name: str, user_id: str, session_id: str,
        config: Optional[GetSessionConfig] = None
    ) -> Optional[Session]:
        """Retrieves a Session object from Firestore."""
        session_data = await self._db_manager.get(self._collection_name, session_id)
        if not session_data:
            logger.warning(f"Session '{session_id}' not found in Firestore.")
            return None
        
        # This is a simplified version; a full implementation would also load events
        # from a subcollection if needed.
        return Session(**session_data)

    @override
    async def append_event(self, session: Session, event: Event) -> None:
        """Appends an event to a session's history in Firestore."""
        session.events.append(event)
        session_data = session.model_dump(exclude_none=True)
        await self._db_manager.save(self._collection_name, session.id, session_data)
        logger.debug(f"Appended event and updated session '{session.id}' in Firestore.")

    # De overige methodes (`list_sessions`, `delete_session`) laten we voor nu leeg.
    @override
    async def list_sessions(self, app_name: str, user_id: Optional[str] = None) -> List[Session]:
        return []

    @override
    async def delete_session(self, app_name: str, user_id: str, session_id: str) -> None:
        pass
