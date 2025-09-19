import logging
from typing import Any

from google.adk.agents import Agent
from google.adk.events import Event
from google.adk.plugins import BasePlugin
from google.adk.sessions import Session

from core.adk_monitoring.service import ADKMonitoringService

logger = logging.getLogger(__name__)


def estimate_tokens(text: str) -> int:
    """A simple heuristic to estimate token count. A common rule of thumb is 4 chars per token."""
    return len(text) // 4


class CostTrackingPlugin(BasePlugin):
    """
    An ADK plugin that estimates and logs token usage for agent interactions.
    """

    def __init__(self, monitoring_service: ADKMonitoringService):
        self.monitoring_service = monitoring_service
        self.name = "CostTrackingPlugin"
        logger.info("CostTrackingPlugin initialized.")

    async def on_run_start(self, session: Session, agent: Agent, **kwargs: Any) -> None:
        # Initialize a token counter in the session state for this run
        session.state["run_token_usage"] = {"input": 0, "output": 0}

    async def on_event(self, session: Session, event: Event, **kwargs: Any) -> None:
        # Track user input tokens
        if event.type == "USER_MESSAGE" and isinstance(event.content, str):
            tokens = estimate_tokens(event.content)
            session.state["run_token_usage"]["input"] += tokens

        # Track agent output tokens
        if event.type == "AGENT_MESSAGE" and isinstance(event.content, str):
            tokens = estimate_tokens(event.content)
            session.state["run_token_usage"]["output"] += tokens

    async def on_run_end(self, session: Session, agent: Agent, **kwargs: Any) -> None:
        # At the end of the run, log the total estimated usage
        usage = session.state.get("run_token_usage", {})
        if usage:
            self.monitoring_service.log_event(
                "adk_token_usage_summary",
                {"session_id": session.id, "user_id": session.user_id, **usage},
            )
            logger.info(f"Session {session.id} estimated token usage: {usage}")