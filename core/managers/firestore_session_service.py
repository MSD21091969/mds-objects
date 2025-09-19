# MDSAPP/core/services/firestore_session_service.py

import logging
import asyncio
import datetime
from typing import Optional, List, Dict, Any
from typing_extensions import override

from google.cloud.firestore_v1.base_query import FieldFilter
from google.adk.sessions import Session, BaseSessionService
from google.adk.sessions.base_session_service import GetSessionConfig
from google.adk.events import Event

logger = logging.getLogger(__name__)

class FirestoreSessionService(BaseSessionService):
    """
    A session service that manages ADK Session objects in Firestore,
    implementing the BaseSessionService interface for direct use with ADK Runners.
    """

    def __init__(self, collection_name: str = "adk_sessions"):
        from MDSAPP.core.dependencies import get_database_manager
        self._db_manager = get_database_manager()
        self._collection_name = collection_name
        self._collection_ref = self._db_manager.db.collection(self._collection_name)
        logger.info(f"FirestoreSessionService initialized for collection: '{self._collection_name}'")

    @override
    async def create_session(
        self,
        app_name: str,
        user_id: str,
        session_id: Optional[str] = None,
        state: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Session:
        """Creates a new Session object and saves it to Firestore."""
        session = Session(
            app_name=app_name, user_id=user_id, id=session_id, state=state, **kwargs
        )
        session_doc_ref = self._collection_ref.document(session.id)
        session_data = session.model_dump(exclude_none=True)
        await asyncio.to_thread(session_doc_ref.set, session_data)
        logger.info(f"Created and saved session '{session.id}' to Firestore.")
        return session

    @override
    async def get_session(
        self,
        app_name: str,
        user_id: str,
        session_id: str,
        config: Optional[GetSessionConfig] = None,
    ) -> Optional[Session]:
        """Retrieves a Session object from Firestore.""" 
        session_doc_ref = self._collection_ref.document(session_id)
        doc = await asyncio.to_thread(session_doc_ref.get)
        if not doc.exists:
            logger.warning(f"Session '{session_id}' not found in Firestore.")
            return None

        session_data = doc.to_dict()
        
        # Basic validation/compatibility
        if 'app_name' in session_data and session_data['app_name'] != app_name:
            logger.error(f"Session '{session_id}' app_name mismatch.")
            return None
        if 'user_id' in session_data and session_data['user_id'] != user_id:
            logger.error(f"Session '{session_id}' user_id mismatch.")
            return None

        # Retrieve events from the subcollection
        events_collection_ref = session_doc_ref.collection("events").order_by("__name__")
        events_stream = await asyncio.to_thread(events_collection_ref.stream)
        events = [Event(**evt.to_dict()) for evt in events_stream]
        session_data["events"] = events

        # Filter out fields that are not in the Session model
        session_fields = Session.model_fields.keys()
        filtered_session_data = {
            key: value for key, value in session_data.items() if key in session_fields
        }

        return Session(**filtered_session_data)

    @override
    async def append_event(self, session: Session, event: Event) -> None:
        """Appends an event to a session in Firestore."""
        await self.append_event_to_subcollection(session.id, event)
        session.last_update_time = datetime.datetime.now(datetime.timezone.utc).timestamp()
        
        session_doc_ref = self._collection_ref.document(session.id)
        
        # Use model_dump to convert the entire session to a dict
        session_data = session.model_dump(exclude=["events"], exclude_none=True)

        await asyncio.to_thread(session_doc_ref.set, session_data, merge=True)
        logger.debug(f"Appended event and updated session '{session.id}' in Firestore.")

    async def append_event_to_subcollection(self, session_id: str, event: Event) -> None:
        """Appends an event to a subcollection of the session document."""
        session_doc_ref = self._collection_ref.document(session_id)
        events_collection_ref = session_doc_ref.collection("events")
        
        # Use a timestamp for the event document ID
        event_id = str(datetime.datetime.now(datetime.timezone.utc).timestamp())
        event_doc_ref = events_collection_ref.document(event_id)
        
        event_data = event.model_dump(exclude_none=True)
        await asyncio.to_thread(event_doc_ref.set, event_data)
        logger.debug(f"Appended event '{event_id}' to subcollection for session '{session_id}'.")

    @override
    async def list_sessions(
        self, app_name: str, user_id: Optional[str] = None
    ) -> List[Session]:
        """Lists sessions from Firestore, optionally filtered by user_id."""
        query = self._collection_ref.where(filter=FieldFilter("app_name", "==", app_name))
        if user_id:
            query = query.where(filter=FieldFilter("user_id", "==", user_id))
        
        docs_stream = await asyncio.to_thread(query.stream)
        sessions = []
        for doc in docs_stream:
            data = doc.to_dict()
            
            # Retrieve events from the subcollection
            events_collection_ref = doc.reference.collection("events").order_by("__name__")
            events_stream = await asyncio.to_thread(events_collection_ref.stream)
            events = [Event(**evt.to_dict()) for evt in events_stream]
            data["events"] = events
            
            # Filter out fields that are not in the Session model
            session_fields = Session.model_fields.keys()
            filtered_data = {
                key: value for key, value in data.items() if key in session_fields
            }
            sessions.append(Session(**filtered_data))
        return sessions

    @override
    async def delete_session(self, app_name: str, user_id: str, session_id: str) -> None:
        """Deletes a session from Firestore."""
        session_doc_ref = self._collection_ref.document(session_id)
        await asyncio.to_thread(session_doc_ref.delete)
        logger.info(f"Deleted session '{session_id}' from Firestore.")

    async def save_session_directly(self, session: Session) -> None:
        """Saves a whole Session object to Firestore. Useful for updates outside of append_event."""
        session.last_update_time = datetime.datetime.now(datetime.timezone.utc).timestamp()
        session_doc_ref = self._collection_ref.document(session.id)
        session_data = session.model_dump(exclude_none=True)
        await asyncio.to_thread(session_doc_ref.set, session_data)
        logger.info(f"Saved session '{session.id}' directly to Firestore.")
