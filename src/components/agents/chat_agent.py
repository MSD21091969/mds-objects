# src/components/agents/chat_agent.py

import logging
from pydantic import PrivateAttr
from typing import List

from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.base_tool import BaseTool

from src.core.managers.prompt_manager import PromptManager
from src.components.casefile.service import CasefileService
from src.core.models.user import User
from src.components.casefile.models import Casefile

logger = logging.getLogger(__name__)

class ChatAgent(LlmAgent):
    """
    Orchestrator for the chat experience, dynamically generating its system prompt.
    """
    _prompt_manager: PromptManager = PrivateAttr()
    _casefile_service: CasefileService = PrivateAttr()

    def __init__(
        self,
        name: str,
        model_name: str,
        prompt_manager: PromptManager,
        casefile_service: CasefileService,
        tools: List[BaseTool],
        **kwargs,
    ):
        super().__init__(
            name=name,
            model=model_name,
            instruction=self._provide_instruction,
            tools=tools,
            **kwargs,
        )
        self._prompt_manager = prompt_manager
        self._casefile_service = casefile_service
        logger.info("ChatAgent (LlmAgent) initialized.")

    async def _provide_instruction(self, context: ReadonlyContext) -> str:
        """Dynamically provides the system prompt based on session state."""
        casefile_id = context.state.get("casefile_id")
        user_json = context.state.get("current_user")
        # 1. Retrieve the dynamic context injected by the DynamicContextPlugin
        dynamic_context = context.state.get("dynamic_context", {})

        casefile: Casefile | None = None
        if casefile_id:
            casefile = await self._casefile_service.load_casefile(casefile_id)

        current_user = User.model_validate_json(user_json) if user_json else None

        # 2. Merge all context sources into a single dictionary
        prompt_context = {
            "casefile": casefile.model_dump() if casefile else {"name": "None"},
            "user": current_user.model_dump() if current_user else {"username": "Unknown"},
        }
        prompt_context.update(dynamic_context)
        
        return await self._prompt_manager.render_prompt(
            agent_name="ChatAgent",
            task_name="chat",
            context=prompt_context,
        )
