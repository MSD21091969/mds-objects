import logging
from typing import Any, Dict

from fastapi import HTTPException, status
from google.adk.agents import Agent
from google.adk.plugins import BasePlugin
from google.adk.sessions import Session
from google.adk.tools import FunctionTool, ToolContext

from core.models.user import User, UserRole

logger = logging.getLogger(__name__)

# Define which roles are required to execute specific tools.
# Tools not listed here are considered public and accessible by any role.
TOOL_PERMISSIONS: Dict[str, UserRole] = {
    # Example: Only an ADMIN can execute a hypothetical 'delete_user' tool.
    # "delete_user": UserRole.ADMIN,
    # Example: Only an ANALYST or ADMIN can execute 'create_casefile'
    # "create_casefile": UserRole.ANALYST
}


class AuthorizationPlugin(BasePlugin):
    """
    An ADK plugin that enforces role-based access control (RBAC) on tools.
    It uses the on_tool_start callback to verify user permissions before a
    tool is executed.
    """

    def __init__(self):
        self.name = "AuthorizationPlugin"
        logger.info("AuthorizationPlugin initialized.")

    async def on_tool_start(
        self, session: Session, agent: Agent, tool: FunctionTool, **kwargs: Any
    ) -> None:
        tool_name = tool.name
        required_role = TOOL_PERMISSIONS.get(tool_name)

        # If the tool is not in our permissions map, it's public.
        if not required_role:
            return

        tool_context: ToolContext = kwargs.get("tool_context")
        user_json = tool_context.state.get("current_user")
        if not user_json:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "User context not found for tool authorization.")

        user = User.model_validate_json(user_json)

        # For now, we'll assume a simple hierarchy: ADMIN > ANALYST > REQUESTER
        # A more robust system might use a list of allowed roles.
        role_hierarchy = {UserRole.ADMIN: 3, UserRole.ANALYST: 2, UserRole.REQUESTER: 1}

        if role_hierarchy.get(user.role, 0) < role_hierarchy.get(required_role, 0):
            logger.warning(f"User '{user.username}' (role: {user.role}) denied access to tool '{tool_name}' (requires: {required_role}).")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have permission to use the '{tool_name}' tool. Required role: {required_role.value}.",
            )

        logger.info(f"User '{user.username}' authorized to use tool '{tool_name}'.")