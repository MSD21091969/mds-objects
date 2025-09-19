import logging
import re
from typing import Any

from google.adk.events import Event
from google.adk.plugins import BasePlugin
from google.adk.sessions import Session

from core.adk_monitoring.service import ADKMonitoringService

logger = logging.getLogger(__name__)


class SanitizationPlugin(BasePlugin):
    """
    An ADK plugin that detects potentially malicious input or sensitive output.

    Note: This is a detection-only implementation. Modifying event content
    in-flight would require deeper changes to the ADK Runner.
    """

    def __init__(self, monitoring_service: ADKMonitoringService):
        self.monitoring_service = monitoring_service
        self.name = "SanitizationPlugin"
        # Simple regex to detect something that looks like an API key.
        self.sensitive_pattern = re.compile(r"\b(sk-[a-zA-Z0-9]{32,})(?:\s|\.|,|$)")
        self.injection_pattern = re.compile(r"\b(ignore|disregard|forget)\b.*(instructions|prompt)\b", re.IGNORECASE)
        logger.info("SanitizationPlugin initialized.")

    async def on_event(self, session: Session, event: Event, **kwargs: Any) -> None:
        if event.type == "AGENT_MESSAGE" and isinstance(event.content, str):
            if self.sensitive_pattern.search(event.content):
                log_data = {
                    "session_id": session.id,
                    "user_id": session.user_id,
                    "alert": "Sensitive data pattern detected in agent output.",
                }
                await self.monitoring_service.log_event("security_alert", log_data)
                logger.warning(f"Sensitive data pattern detected in agent output for session {session.id}.")

        # Check for prompt injection attempts in user input
        if event.type == "USER_MESSAGE" and isinstance(event.content, str):
            if self.injection_pattern.search(event.content):
                log_data = {
                    "session_id": session.id,
                    "user_id": session.user_id,
                    "alert": "Potential prompt injection attempt detected in user input.",
                }
                await self.monitoring_service.log_event("security_alert", log_data)
                logger.warning(f"Potential prompt injection attempt detected in user input for session {session.id}.")
