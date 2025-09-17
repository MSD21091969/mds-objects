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
        self._prompt_file_path = "/workspaces/mds-objects/docs/prompt chatagent.txt" # Hardcoded for now

    async def _load_prompt_from_file(self) -> str:
        """Loads the prompt template from the specified file."""
        try:
            with open(self._prompt_file_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Prompt file not found at {self._prompt_file_path}")
            return "You are a helpful assistant." # Fallback
        except Exception as e:
            logger.error(f"Error loading prompt from file {self._prompt_file_path}: {e}")
            return "You are a helpful assistant." # Fallback

    async def get_prompt_template(self, agent_name: str, task_name: str) -> str:
        """
        Haalt een prompt-template op. Voor nu laden we deze uit een bestand.
        Later wordt dit vervangen door een database-call.
        """
        prompt_key = f"{agent_name}-{task_name}"
        if prompt_key not in self._prompts:
            if agent_name == "ChatAgent" and task_name == "chat":
                template = await self._load_prompt_from_file()
            else:
                # Fallback for other agents/tasks if needed
                template = "You are a helpful assistant."
            self._prompts[prompt_key] = template
            logger.info(f"Loaded prompt for '{prompt_key}' from file.")
        
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
