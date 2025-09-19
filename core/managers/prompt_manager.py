# src/core/managers/prompt_manager.py

import logging
from typing import Dict, Any
from typing import Optional
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
        self._prompt_file_path = "/workspaces/mds-objects/docs/prompt chatagent.txt"  # Hardcoded for now
        self.prompts_collection_name = "prompt_templates"

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

    async def _load_prompt_from_firestore(self, prompt_key: str) -> Optional[str]:
        """Attempts to load a prompt template from Firestore."""
        try:
            prompt_doc = await self.db_manager.get(self.prompts_collection_name, prompt_key)
            if prompt_doc and 'template' in prompt_doc:
                logger.info(f"Found prompt template '{prompt_key}' in Firestore.")
                return prompt_doc['template']
        except Exception as e:
            logger.error(f"Error loading prompt '{prompt_key}' from Firestore: {e}")
        return None

    async def get_prompt_template(self, agent_name: str, task_name: str) -> str:
        """
        Retrieves a prompt template, trying Firestore first and then falling back to a local file.
        """
        prompt_key = f"{agent_name}-{task_name}"
        if prompt_key not in self._prompts:
            # 1. Try to load from Firestore
            template = await self._load_prompt_from_firestore(prompt_key)

            # 2. If not in Firestore, fall back to local file
            if template is None:
                logger.warning(f"Prompt template '{prompt_key}' not found in Firestore. Falling back to local file.")
                if agent_name == "ChatAgent" and task_name == "chat":
                    template = await self._load_prompt_from_file()
                else:
                    # Fallback for other agents/tasks if needed
                    template = "You are a helpful assistant."
                logger.info(f"Loaded prompt for '{prompt_key}' from file.")

            self._prompts[prompt_key] = template

        return self._prompts[prompt_key]

    async def save_prompt_template(self, prompt_key: str, template_string: str):
        """Saves a prompt template to Firestore."""
        await self.db_manager.save(self.prompts_collection_name, prompt_key, {"template": template_string})
        logger.info(f"Saved prompt template '{prompt_key}' to Firestore.")

    async def render_prompt(self, agent_name: str, task_name: str, context: Dict[str, Any]) -> str:
        """
        Renders a prompt with the given context.
        """
        template_string = await self.get_prompt_template(agent_name, task_name)
        if not template_string:
            return "You are a helpful assistant." # Fallback
        
        template = self._jinja_env.from_string(template_string)
        return template.render(context)
