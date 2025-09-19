# src/agents/chat_agent.py

import logging
from pydantic import PrivateAttr
from typing import List

from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools import BaseTool
from google.adk.tools.base_toolset import BaseToolset

# --- Core Managers & Services ---
from core.managers.prompt_manager import PromptManager
from core.managers.database_manager import DatabaseManager
from src.casefileservice.service import CasefileService
from core.models.user import User
from src.casefileservice.models import Casefile

# --- Authenticatie Componenten ---
# from src.components.toolsets.google_workspace.credential_manager import GoogleCredentialManager
# from src.core.services.credential_store import DatabaseCredentialStore

# --- Service & Toolset Imports ---
from src.agents.toolsets.casefile_toolset import CasefileToolset
# from src.components.toolsets.web_search.web_search_toolset import WebSearchToolset
# from src.components.toolsets.retrieval.toolset import RetrievalToolset
# from src.components.toolsets.google_workspace.gmail.google_gmail_toolset import GmailToolset
# from src.components.toolsets.google_workspace.gmail.service import GmailService
# Importeer hier toekomstige services en toolsets...

logger = logging.getLogger(__name__)

# ==============================================================================
# JOUW BESTAANDE ChatAgent KLASSE (Behouden en Gerespecteerd)
# ==============================================================================
class ChatAgent(LlmAgent):
    """
    Orchestrator for the chat experience, dynamically generating its system prompt.
    """
    _prompt_manager: PromptManager = PrivateAttr()
    _casefile_service: CasefileService = PrivateAttr()

    def __init__(
        self,
        name: str,
        model: str,
        prompt_manager: PromptManager,
        casefile_service: CasefileService,
        tools: List[BaseToolset], # Accepteert nu een lijst van toolsets
        **kwargs,
    ):
        super().__init__(
            name=name,
            model=model,
            instruction=self._provide_instruction, # Jouw dynamische instructie-methode
            tools=tools,
            **kwargs,
        )
        self._prompt_manager = prompt_manager
        self._casefile_service = casefile_service
        logger.info("Custom ChatAgent (LlmAgent) initialized with dynamic instruction provider.")

    async def _provide_instruction(self, context: ReadonlyContext) -> str:
        """Dynamically provides the system prompt based on session state."""
        casefile_id = context.state.get("casefile_id")
        user_json = context.state.get("current_user")
        
        # Voorbeeld: dynamic_context kan door een ADK-plugin worden toegevoegd
        dynamic_context = context.state.get("dynamic_context", {})

        casefile: Casefile | None = None
        if casefile_id:
            # Aanname: load_casefile is een async methode in de service
            casefile = await self._casefile_service.get_casefile(casefile_id)

        current_user = User.model_validate_json(user_json) if user_json else None

        prompt_context = {
            "casefile": casefile.model_dump() if casefile else None,
            "user": current_user.model_dump() if current_user else None,
        }
        prompt_context.update(dynamic_context)
        
        return await self._prompt_manager.render_prompt(
            agent_name=self.name,
            task_name="chat", # Aangenomen taaknaam
            context=prompt_context,
        )
