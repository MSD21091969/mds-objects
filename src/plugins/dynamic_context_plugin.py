import logging
from typing import Any

from google.adk.agents import Agent
from google.adk.plugins import BasePlugin
from google.adk.sessions import Session

logger = logging.getLogger(__name__)


class DynamicContextPlugin(BasePlugin):
    """
    An ADK plugin that injects dynamic, real-time context into the session
    state at the beginning of an agent run.

    This pattern allows the agent's prompt to be enriched with information
    that is only available at runtime.
    """

    def __init__(self):
        logger.info("DynamicContextPlugin initialized.")

    async def on_run_start(self, session: Session, agent: Agent, **kwargs: Any) -> None:
        """
        On run start, fetch or generate dynamic data and add it to the session state.
        """
        # In a real-world scenario, this could be an API call to get breaking news,
        # a database query for recent system alerts, or a check on the user's status.
        thought_of_the_day = "The best way to predict the future is to invent it."

        session.state["dynamic_context"] = {"thought_of_the_day": thought_of_the_day}
        logger.info(f"Injected dynamic context for session {session.id}.")