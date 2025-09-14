# src/core/managers/prompt_manager.py

import logging
from typing import Dict, Any
from jinja2 import Environment

# We importeren de DatabaseManager om er later mee te kunnen werken.
from .database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class PromptManager:
    """
    Manages loading, versioning, and rendering of prompts from a database.
    """
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        # In-memory cache voor geladen prompts om database-calls te verminderen.
        self._prompts: Dict[str, str] = {}
        self._jinja_env = Environment()

    async def get_prompt_template(self, agent_name: str, task_name: str) -> str:
        """
        Haalt een prompt-template op. Voor nu gebruiken we een hardcoded template.
        Later wordt dit vervangen door een database-call.
        """
        prompt_key = f"{agent_name}-{task_name}"
        if prompt_key not in self._prompts:
            # Placeholder: In de toekomst laden we dit uit Firestore.
            # Voor nu, een simpele, effectieve standaard prompt.
            template = (
                "You are a helpful assistant. "
                "The current casefile is '{{ casefile.name }}'. "
                "You are assisting user '{{ user.username }}'."
            )
            self._prompts[prompt_key] = template
            logger.info(f"Loaded placeholder prompt for '{prompt_key}'.")
        
        return self._prompts[prompt_key]

    async def render_prompt(self, agent_name: str, task_name: str, context: Dict[str, Any]) -> str:
        """
        Renders a prompt with the given context.
        """
        template_string = await self.get_prompt_template(agent_name, task_name)
        if not template_string:
            return "You are a helpful assistant." # Fallback
        
        template = self._jinja_env.from_string(template_string)
        return template.render(context)
