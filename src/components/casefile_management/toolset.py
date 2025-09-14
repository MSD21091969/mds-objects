# src/components/casefile_management/toolset.py

import logging
from typing import Optional, List, Dict
from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools import FunctionTool, BaseTool, ToolContext

from src.components.casefile_management.manager import CasefileManager
from src.core.models.casefile import Casefile
from src.core.models.user import User

logger = logging.getLogger(__name__)

class CasefileToolset(BaseToolset):
    """A toolset for managing casefiles within the application."""

    def __init__(self, casefile_manager: CasefileManager):
        self._casefile_manager = casefile_manager

    def _get_user_from_context(self, tool_context: ToolContext) -> User:
        """Helper to extract and validate the user from the tool context state."""
        user_json = tool_context.state.get("current_user")
        if not user_json:
            raise ValueError("Could not find 'current_user' in tool context state.")
        try:
            user = User.model_validate_json(user_json)
            return user
        except Exception as e:
            logger.error(f"Failed to parse user from tool_context: {e}")
            raise ValueError("Failed to parse user from context.") from e

    async def get_casefile(self, casefile_id: str, tool_context: ToolContext) -> Optional[Casefile]:
        """
        Retrieves a single casefile by its ID.
        
        Args:
            casefile_id: The ID of the casefile to retrieve.
        """
        return await self._casefile_manager.get_casefile(casefile_id=casefile_id)

    async def list_casefiles(self, tool_context: ToolContext) -> List[Dict[str, str]]:
        """Lists all available casefiles, returning a list of their names and IDs."""
        casefiles = await self._casefile_manager.list_casefiles()
        if not casefiles:
            return []
        return [{"id": cf.id, "name": cf.name} for cf in casefiles]

    def get_tools(self) -> list[BaseTool]:
        """Returns a list of all the tool methods in this toolset."""
        return [
            FunctionTool(func=self.get_casefile),
            FunctionTool(func=self.list_casefiles),
        ]