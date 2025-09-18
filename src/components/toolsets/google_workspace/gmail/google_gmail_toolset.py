import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Union

from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.adk.tools import ToolContext

from src.core.models.user import User
from src.components.toolsets.google_workspace.gmail.service import GoogleGmailService
from src.components.toolsets.google_workspace.gmail.models import GmailMessage

logger = logging.getLogger(__name__)

class GoogleGmailToolset(BaseToolset):
    """
    A toolset for interacting with Google Gmail.
    """
    def __init__(self, gmail_service: GoogleGmailService):
        super().__init__()
        self._gmail_service = gmail_service

    def _get_user_id_from_context(self, tool_context: ToolContext) -> Optional[str]:
        """Helper to extract user ID from the tool context state."""
        user_json = tool_context.state.get("current_user")
        if not user_json:
            logger.warning("Could not find 'current_user' in tool context state.")
            return None
        try:
            user = User.model_validate_json(user_json)
            return user.username
        except Exception as e:
            logger.error(f"Failed to parse user from tool_context: {e}")
            return None

    async def search_emails(self, tool_context: ToolContext, query: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Union[List[Dict[str, Any]], str]:
        """
        Searches for emails in the user's inbox using a query and/or a date range.

        Args:
            tool_context: The runtime context.
            query: The search query (e.g., 'from:example@test.com').
            start_date: The start date in YYYY-MM-DD format.
            end_date: The end date in YYYY-MM-DD format.

        Returns:
            A list of dictionaries, each representing a found email, or an error string.
        """
        user_id = self._get_user_id_from_context(tool_context)
        if not user_id:
            return "Error: Could not determine the user to perform this action for."

        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
        except (ValueError, TypeError):
            return "Invalid date format. Please use YYYY-MM-DD."

        logger.info(f"Toolset calling gmail_service.search_emails for user '{user_id}'")
        messages = await self._gmail_service.search_emails(user_id=user_id, query=query, start_date=start_date_obj, end_date=end_date_obj)
        return [msg.model_dump(by_alias=True) for msg in messages]

    async def get_email(self, message_id: str, tool_context: ToolContext) -> Union[Dict[str, Any], str]:
        """
        Gets a single email by its ID.
        Args:
            message_id: The ID of the email to retrieve.
            tool_context: The runtime context.
        """
        user_id = self._get_user_id_from_context(tool_context)
        if not user_id:
            return "Error: Could not determine the user to perform this action for."

        email = await self._gmail_service.get_email(user_id=user_id, message_id=message_id)
        if not email:
            return f"Email with ID '{message_id}' not found or access was denied."
        return email.model_dump(by_alias=True)

    async def send_email(self, to: str, subject: str, message_text: str, tool_context: ToolContext) -> Union[Dict[str, Any], str]:
        """
        Sends an email.
        Args:
            to: The recipient's email address.
            subject: The subject of the email.
            message_text: The body of the email.
            tool_context: The runtime context.
        """
        user_id = self._get_user_id_from_context(tool_context)
        if not user_id:
            return "Error: Could not determine the user to perform this action for."

        sent_email = await self._gmail_service.send_email(user_id=user_id, to=to, subject=subject, message_text=message_text)
        if not sent_email:
            return "Failed to send email."
        return sent_email.model_dump(by_alias=True)

    async def delete_email(self, message_id: str, tool_context: ToolContext) -> bool:
        """
        Deletes an email by its ID. Returns True on success.
        Args:
            message_id: The ID of the email to delete.
            tool_context: The runtime context.
        """
        user_id = self._get_user_id_from_context(tool_context)
        if not user_id:
            # Or raise an exception, depending on desired behavior
            logger.error("Cannot delete email: user ID not found in context.")
            return False
        return await self._gmail_service.delete_email(user_id=user_id, message_id=message_id)

    async def get_tools(self, tool_context: "ToolContext") -> list[BaseTool]:
        """
        Returns a list of tools provided by this toolset.
        """
        return [
            FunctionTool(func=self.search_emails),
            FunctionTool(func=self.get_email),
            FunctionTool(func=self.send_email),
            FunctionTool(func=self.delete_email),
        ]
