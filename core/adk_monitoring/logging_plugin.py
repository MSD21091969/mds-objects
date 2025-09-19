import logging
from typing import Any, Dict, Optional

from google.adk.plugins import BasePlugin
from google.adk.events import Event
from google.adk.sessions import Session
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from core.adk_monitoring.service import ADKMonitoringService

logger = logging.getLogger(__name__)

class LoggingPlugin(BasePlugin):
    """
    An ADK plugin that logs all lifecycle events and agent interactions
    using the ADKMonitoringService.
    """
    def __init__(self, monitoring_service: ADKMonitoringService):
        self.monitoring_service = monitoring_service
        self.name = "LoggingPlugin"
        logger.info("LoggingPlugin initialized.")

    def _get_common_log_data(self, session: Session, agent: Optional[Agent] = None) -> Dict[str, Any]:
        """Extracts common data points from the session and agent for consistent logging."""
        data = {
            "session_id": session.id,
            "user_id": session.user_id,
            "app_name": session.app_name,
            "casefile_id": session.state.get("casefile_id"), # Extract casefile_id if available
        }
        if agent:
            data["agent_name"] = agent.name
        return {k: v for k, v in data.items() if v is not None} # Filter out None values

    async def on_run_start(self, session: Session, agent: Agent, **kwargs: Any) -> None:
        self.monitoring_service.log_event(
            "adk_run_start",
            {
                **self._get_common_log_data(session, agent),
                "run_type": "agent_run",
                **kwargs
            }
        )

    async def on_event(self, session: Session, event: Event, **kwargs: Any) -> None:
        self.monitoring_service.log_event(
            "adk_event_processed",
            {
                **self._get_common_log_data(session),
                "event_type": event.type,
                "event_timestamp": event.timestamp.isoformat(),
                "event_content": str(event.content), # Convert content to string for logging
                **kwargs
            }
        )

    async def on_run_end(self, session: Session, agent: Agent, **kwargs: Any) -> None:
        self.monitoring_service.log_event(
            "adk_run_end",
            {
                **self._get_common_log_data(session, agent),
                "status": "success",
                **kwargs
            }
        )

    async def on_run_error(self, session: Session, agent: Agent, error: Exception, **kwargs: Any) -> None:
        self.monitoring_service.log_event(
            "adk_run_error",
            {
                **self._get_common_log_data(session, agent),
                "status": "error",
                "error_type": type(error).__name__,
                "error_message": str(error),
                **kwargs
            }
        )

    async def on_tool_start(self, session: Session, agent: Agent, tool: FunctionTool, **kwargs: Any) -> None:
        self.monitoring_service.log_event(
            "adk_tool_start",
            {
                **self._get_common_log_data(session, agent),
                "tool_name": tool.name,
                "tool_args": str(kwargs.get("tool_args")),
                **kwargs
            }
        )

    async def on_tool_end(self, session: Session, agent: Agent, tool: FunctionTool, result: Any, **kwargs: Any) -> None:
        self.monitoring_service.log_event(
            "adk_tool_end",
            {
                **self._get_common_log_data(session, agent),
                "tool_name": tool.name,
                "tool_result": str(result), # Convert result to string for logging
                **kwargs
            }
        )

    async def on_tool_error(self, session: Session, agent: Agent, tool: FunctionTool, error: Exception, **kwargs: Any) -> None:
        self.monitoring_service.log_event(
            "adk_tool_error",
            {
                **self._get_common_log_data(session, agent),
                "tool_name": tool.name,
                "error_type": type(error).__name__,
                "error_message": str(error),
                **kwargs
            }
        )

    # You can add more ADK lifecycle methods here as needed, e.g., on_agent_message, on_agent_response, etc.
