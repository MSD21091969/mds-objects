# src/core/services/firestore_session_service.py

import logging
import asyncio
import time
import uuid
from typing import Optional, List, Dict, Any, Union

from typing_extensions import override

from google.cloud.firestore_v1.base_query import FieldFilter
from google.adk.sessions import Session, BaseSessionService
from google.adk.sessions.base_session_service import GetSessionConfig
from google.adk.events import Event, EventActions
from google.genai.types import Content

from opentelemetry import trace

from src.core.managers.database_manager import DatabaseManager
from src.core.adk_monitoring.service import ADKMonitoringService

logger = logging.getLogger(__name__)

class FirestoreSessionService(BaseSessionService):
    """
    Manages ADK Session objects in Firestore, implementing the BaseSessionService
    interface for direct use with ADK Runners.
    """
    _collection_name = "adk_sessions"

    def __init__(self, db_manager: DatabaseManager, monitoring_service: ADKMonitoringService):
        self._db_manager = db_manager
        self._collection_ref = self._db_manager.db.collection(self._collection_name)
        self.monitoring_service = monitoring_service
        self.tracer = trace.get_tracer(__name__)
        logger.info(f"FirestoreSessionService initialized for collection: '{self._collection_name}'")

    @override
    async def create_session(
        self, app_name: str, user_id: str, session_id: Optional[str] = None,
        state: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Session:
        """Creates a new Session object and saves it to Firestore."""
        with self.tracer.start_as_current_span("firestore_session.create_session") as span:
            span.set_attribute("session.app_name", app_name)
            span.set_attribute("session.user_id", user_id)
            span.set_attribute("session.session_id", session_id)

            session = Session(app_name=app_name, user_id=user_id, id=session_id, state=state, **kwargs)
            
            session_data = session.model_dump(exclude_none=True)
            await self._db_manager.save(self._collection_name, session.id, session_data)
            
            self.monitoring_service.log_session_interaction("create", session.id, user_id, {"app_name": app_name, "initial_state_keys": list(state.keys()) if state else []})
            logger.info(f"Created and saved session '{session.id}' to Firestore.")
            return session

    @override
    async def get_session(
        self, app_name: str, user_id: str, session_id: str,
        config: Optional[GetSessionConfig] = None
    ) -> Optional[Session]:
        """Retrieves a Session object from Firestore."""
        with self.tracer.start_as_current_span("firestore_session.get_session") as span:
            span.set_attribute("session.app_name", app_name)
            span.set_attribute("session.user_id", user_id)
            span.set_attribute("session.session_id", session_id)

            session_data = await self._db_manager.get(self._collection_name, session_id)
            if not session_data:
                self.monitoring_service.log_session_interaction("get_not_found", session_id, user_id, {"app_name": app_name})
                logger.warning(f"Session '{session_id}' not found in Firestore.")
                return None
            
            self.monitoring_service.log_session_interaction("get_found", session_id, user_id, {"app_name": app_name, "state_keys": list(session_data.get("state", {}).keys())})
            return Session(**session_data)

    @override
    async def append_event(self, session: Session, event: Any) -> None:
        """
        Appends an event to a session's history in Firestore.

        NOTE: This method performs runtime type checking for the 'event' parameter.
        It handles `google.adk.events.Event` as expected, but also contains
        a workaround for `google.genai.types.Content` objects that may be
        passed by the ADK runner. This is a defensive measure to prevent
        crashes and ensure all interactions are recorded.
        """
        actual_event: Event
        if isinstance(event, Content):
            logger.warning(
                "append_event received google.genai.types.Content "
                "instead of google.adk.events.Event. Attempting conversion."
            )
            synthetic_invocation_id = f"custom-gen-inv-{uuid.uuid4()}"
            synthetic_event_id = str(uuid.uuid4())
            actual_event = Event(
                invocation_id=synthetic_invocation_id,
                author='user',
                actions=EventActions(state_delta={}),
                content=event,
                id=synthetic_event_id,
                timestamp=time.time(),
            )
        elif isinstance(event, Event):
            actual_event = event
        else:
            logger.error(
                f"append_event received an unexpected type: {type(event)}. "
                "Only Event and Content objects are supported. Skipping event."
            )
            return

        with self.tracer.start_as_current_span("firestore_session.append_event") as span:
            span.set_attribute("session.session_id", session.id)
            
            event_type = "unknown"
            if actual_event.is_final_response():
                event_type = "final_response"
            elif actual_event.get_function_calls():
                event_type = "function_call"
            elif actual_event.get_function_responses():
                event_type = "function_response"
            elif actual_event.content and actual_event.content.parts:
                event_type = "content"
            elif actual_event.actions and (actual_event.actions.state_delta or actual_event.actions.artifact_delta):
                event_type = "state_artifact_update"

            span.set_attribute("session.event_type", event_type)

            session.events.append(actual_event)
            session_data = session.model_dump(exclude_none=True)
            await self._db_manager.save(self._collection_name, session.id, session_data)
            
            content_summary = ""
            if actual_event.content and actual_event.content.parts:
                content_summary = str(actual_event.content.parts[0].text)[:250]

            self.monitoring_service.log_session_interaction(
                "append_event", 
                session.id, 
                session.user_id, 
                {"event_type": event_type, "event_content_summary": content_summary}
            )
            logger.debug(f"Appended event and updated session '{session.id}' in Firestore.")

    @override
    async def list_sessions(self, app_name: str, user_id: Optional[str] = None) -> List[Session]:
        return []

    @override
    async def delete_session(self, app_name: str, user_id: str, session_id: str) -> None:
        pass
