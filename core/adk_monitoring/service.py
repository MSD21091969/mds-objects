import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

class ADKMonitoringService:
    """
    Central service for ADK monitoring, handling structured logging of events.
    """
    def __init__(self):
        logger.info("ADKMonitoringService initialized.")

    def log_event(self, event_name: str, data: Dict[str, Any]):
        """
        Logs a structured monitoring event.
        """
        logger.info(f"ADK_MONITORING_EVENT: {event_name}", extra=data)

    def log_session_interaction(self, action: str, session_id: str, user_id: str, details: Dict[str, Any]):
        """
        Logs a structured event for session interactions.
        """
        log_data = {
            "action": action,
            "session_id": session_id,
            "user_id": user_id,
            **details
        }
        self.log_event("session_interaction", log_data)

    # Future methods could include storing data to Firestore, publishing to Pub/Sub, etc.
