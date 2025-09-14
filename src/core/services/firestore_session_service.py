# src/core/services/firestore_session_service.py

import logging
import asyncio
from typing import Optional, List, Dict, Any
from typing_extensions import override

from google.cloud.firestore_v1.base_query import FieldFilter
from google.adk.sessions import Session, BaseSessionService
from google.adk.sessions.base_session_service import GetSessionConfig
from google.adk.events import Event

from opentelemetry import trace # NEW

from src.core.managers.database_manager import DatabaseManager
from src.core.adk_monitoring.service import ADKMonitoringService # NEW

logger = logging.getLogger(__name__)

class FirestoreSessionService(BaseSessionService):
    """
    Manages ADK Session objects in Firestore, implementing the BaseSessionService
    interface for direct use with ADK Runners.
    """
    _collection_name = "adk_sessions"

    def __init__(self, db_manager: DatabaseManager, monitoring_service: ADKMonitoringService): # MODIFIED
        self._db_manager = db_manager
        self._collection_ref = self._db_manager.db.collection(self._collection_name)
        self.monitoring_service = monitoring_service # NEW
        self.tracer = trace.get_tracer(__name__) # NEW
        logger.info(f"FirestoreSessionService initialized for collection: '{self._collection_name}'")

    @override
    async def create_session(
        self, app_name: str, user_id: str, session_id: Optional[str] = None,
        state: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Session:
        """Creates a new Session object and saves it to Firestore."""
        with self.tracer.start_as_current_span("firestore_session.create_session") as span: # NEW
            span.set_attribute("session.app_name", app_name) # NEW
            span.set_attribute("session.user_id", user_id) # NEW
            span.set_attribute("session.session_id", session_id) # NEW

            session = Session(app_name=app_name, user_id=user_id, id=session_id, state=state, **kwargs)
            
            session_data = session.model_dump(exclude_none=True)
            await self._db_manager.save(self._collection_name, session.id, session_data)
            
            self.monitoring_service.log_session_interaction("create", session.id, user_id, {"app_name": app_name, "initial_state_keys": list(state.keys()) if state else []}) # NEW
            logger.info(f"Created and saved session '{session.id}' to Firestore.")
            return session

    @override
    async def get_session(
        self, app_name: str, user_id: str, session_id: str,
        config: Optional[GetSessionConfig] = None
    ) -> Optional[Session]:
        """Retrieves a Session object from Firestore."""
        with self.tracer.start_as_current_span("firestore_session.get_session") as span: # NEW
            span.set_attribute("session.app_name", app_name) # NEW
            span.set_attribute("session.user_id", user_id) # NEW
            span.set_attribute("session.session_id", session_id) # NEW

            session_data = await self._db_manager.get(self._collection_name, session_id)
            if not session_data:
                self.monitoring_service.log_session_interaction("get_not_found", session_id, user_id, {"app_name": app_name}) # NEW
                logger.warning(f"Session '{session_id}' not found in Firestore.")
                return None
            
            self.monitoring_service.log_session_interaction("get_found", session_id, user_id, {"app_name": app_name, "state_keys": list(session_data.get("state", {}).keys())}) # NEW
            # This is a simplified version; a full implementation would also load events
            # from a subcollection if needed.
            return Session(**session_data)

    @override
    async def append_event(self, session: Session, event: Event) -> None:
        """Appends an event to a session's history in Firestore."""
        with self.tracer.start_as_current_span("firestore_session.append_event") as span: # NEW
            span.set_attribute("session.session_id", session.id) # NEW
            span.set_attribute("session.event_type", event.type) # NEW

            session.events.append(event)
            session_data = session.model_dump(exclude_none=True)
            await self._db_manager.save(self._collection_name, session.id, session_data)
            self.monitoring_service.log_session_interaction("append_event", session.id, session.user_id, {"event_type": event.type, "event_content_summary": str(event.content)[:250]}) # NEW
            logger.debug(f"Appended event and updated session '{session.id}' in Firestore.")

    # De overige methodes (`list_sessions`, `delete_session`) laten we voor nu leeg.
    @override
    async def list_sessions(self, app_name: str, user_id: Optional[str] = None) -> List[Session]:
        return []

    @override
    async def delete_session(self, app_name: str, user_id: str, session_id: str) -> None:
        pass
