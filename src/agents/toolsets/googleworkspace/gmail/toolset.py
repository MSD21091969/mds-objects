# src/components/toolsets/google_workspace/gmail/google_gmail_toolset.py

import logging
from typing import Optional

from google.adk.tools import FunctionTool, BaseToolset, ToolContext, ReadonlyContext, Parameter
from google.adk.tools.base_tool import BaseTool

from .service import GmailService
from .models import ListMessagesQuery, GetMessageQuery

logger = logging.getLogger(__name__)

class GmailToolset(BaseToolset):
    """
    Exposes GmailService methods as ADK Tools. This is the bridge layer that
    connects the agent's runtime context to the stateless service layer.
    """
    def __init__(self, gmail_service: GmailService):
        self.gmail_service = gmail_service

    async def get_tools(self, readonly_context: Optional[ReadonlyContext] = None) -> list[BaseTool]:
        """
        Defines and returns the list of Gmail tools available to the agent.
        Each tool wrapper function uses the ToolContext to get the user_id.
        """
        
        # --- Tool 1: Get User Profile ---
        async def _get_user_profile_tool(tool_context: ToolContext) -> dict:
            """Retrieves the authenticated user's Gmail profile information, including email address."""
            user_id = tool_context.invocation_context.session.user_id
            logger.info(f"Tool triggered: get_user_profile for user_id: {user_id}")
            return await self.gmail_service.get_user_profile(user_id=user_id)

        # --- Tool 2: List Messages ---
        async def _list_messages_tool(query: str, max_results: int, tool_context: ToolContext) -> dict:
            """Lists email messages in the user's mailbox that match a search query."""
            user_id = tool_context.invocation_context.session.user_id
            logger.info(f"Tool triggered: list_messages for user_id: {user_id}")
            validated_input = ListMessagesQuery(query=query, max_results=max_results)
            return await self.gmail_service.list_messages(user_id=user_id, query=validated_input)

        # --- Tool 3: Get a Specific Message ---
        async def _get_message_tool(message_id: str, tool_context: ToolContext) -> dict:
            """Retrieves the full content of a specific email message by its ID."""
            user_id = tool_context.invocation_context.session.user_id
            logger.info(f"Tool triggered: get_message for user_id: {user_id}")
            validated_input = GetMessageQuery(message_id=message_id)
            return await self.gmail_service.get_message(user_id=user_id, query=validated_input)

        # Bundel de wrapper functies in FunctionTool objecten
        tools = [
            FunctionTool(func=_get_user_profile_tool, name="gmail_get_user_profile"),
            FunctionTool(
                func=_list_messages_tool,
                name="gmail_list_messages",
                description="Lists email messages in the user's mailbox that match a search query. This is useful for finding specific emails based on sender, subject, or content.",
                parameters=[
                    Parameter(name="query", type=str, description="The search query to filter messages. Uses standard Gmail search syntax.", required=True),
                    Parameter(name="max_results", type=int, description="The maximum number of messages to return.", required=False)
                ]
            ),
            FunctionTool(
                func=_get_message_tool,
                name="gmail_get_message_details",
                description="Retrieves the full content of a specific email message by its unique ID. This tool is useful for getting the body and headers of an email after it has been found with 'list_messages'.",
                parameters=[
                    Parameter(name="message_id", type=str, description="The unique ID of the message to retrieve.", required=True)
                ]
            )
        ]
        return tools