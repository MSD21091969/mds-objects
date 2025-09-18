import logging
from typing import Optional, List, Union, Dict, Any

from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.adk.tools import ToolContext

from src.core.models.user import User
from src.components.toolsets.google_workspace.people.service import GooglePeopleService
from src.components.toolsets.google_workspace.people.models import GooglePerson

logger = logging.getLogger(__name__)

class GooglePeopleToolset(BaseToolset):
    """
    A toolset for interacting with Google People.
    """
    def __init__(self, people_service: GooglePeopleService):
        super().__init__()
        self._people_service = people_service

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

    async def list_contacts(self, tool_context: ToolContext, page_size: int = 100) -> Union[List[Dict[str, Any]], str]:
        """
        Lists contacts from the user's Google Contacts.
        Args:
            tool_context: The runtime context.
            page_size: The maximum number of contacts to return.
        """
        user_id = self._get_user_id_from_context(tool_context)
        if not user_id:
            return "Error: Could not determine the user to perform this action for."

        logger.info(f"Toolset calling people_service.list_contacts for user '{user_id}'")
        contacts = await self._people_service.list_contacts(user_id=user_id, page_size=page_size)
        return [contact.model_dump(by_alias=True) for contact in contacts]

    async def get_contact(self, resource_name: str, tool_context: ToolContext) -> Union[Dict[str, Any], str]:
        """
        Gets a single contact by its resource name.
        Args:
            resource_name: The resource name of the contact to retrieve.
            tool_context: The runtime context.
        """
        user_id = self._get_user_id_from_context(tool_context)
        if not user_id:
            return "Error: Could not determine the user to perform this action for."

        logger.info(f"Toolset calling people_service.get_contact for user '{user_id}'")
        contact = await self._people_service.get_contact(user_id=user_id, resource_name=resource_name)
        if not contact:
            return f"Contact with resource name '{resource_name}' not found or access was denied."
        return contact.model_dump(by_alias=True)

    async def create_contact(self, given_name: str, family_name: str, tool_context: ToolContext, email: Optional[str] = None, phone: Optional[str] = None) -> Union[Dict[str, Any], str]:
        """
        Creates a new contact.
        Args:
            given_name: The contact's first name.
            family_name: The contact's last name.
            tool_context: The runtime context.
            email: The contact's email address.
            phone: The contact's phone number.
        """
        user_id = self._get_user_id_from_context(tool_context)
        if not user_id:
            return "Error: Could not determine the user to perform this action for."

        logger.info(f"Toolset calling people_service.create_contact for user '{user_id}'")
        contact = await self._people_service.create_contact(user_id=user_id, given_name=given_name, family_name=family_name, email=email, phone=phone)
        if not contact:
            return f"Failed to create contact '{given_name} {family_name}'."
        return contact.model_dump(by_alias=True)

    async def update_contact(self, resource_name: str, etag: str, tool_context: ToolContext, given_name: Optional[str] = None, family_name: Optional[str] = None, email: Optional[str] = None, phone: Optional[str] = None) -> Union[Dict[str, Any], str]:
        """
        Updates an existing contact.
        Args:
            resource_name: The resource name of the contact to update.
            etag: The etag of the contact, used for optimistic concurrency control.
            tool_context: The runtime context.
            given_name: The new first name.
            family_name: The new last name.
            email: The new email address.
            phone: The new phone number.
        """
        user_id = self._get_user_id_from_context(tool_context)
        if not user_id:
            return "Error: Could not determine the user to perform this action for."

        updates = {
            "given_name": given_name,
            "family_name": family_name,
            "email": email,
            "phone": phone,
        }

        logger.info(f"Toolset calling people_service.update_contact for user '{user_id}'")
        contact = await self._people_service.update_contact(user_id=user_id, resource_name=resource_name, etag=etag, updates=updates)
        if not contact:
            return f"Failed to update contact '{resource_name}'."
        return contact.model_dump(by_alias=True)

    async def delete_contact(self, resource_name: str, tool_context: ToolContext) -> bool:
        """
        Deletes a contact. Returns True on success.
        Args:
            resource_name: The resource name of the contact to delete.
            tool_context: The runtime context.
        """
        user_id = self._get_user_id_from_context(tool_context)
        if not user_id:
            logger.error("Cannot delete contact: user ID not found in context.")
            return False

        logger.info(f"Toolset calling people_service.delete_contact for user '{user_id}'")
        return await self._people_service.delete_contact(user_id=user_id, resource_name=resource_name)

    async def get_tools(self, tool_context: "ToolContext") -> list[BaseTool]:
        """
        Returns a list of tools provided by this toolset.
        """
        return [
            FunctionTool(func=self.list_contacts),
            FunctionTool(func=self.get_contact),
            FunctionTool(func=self.create_contact),
            FunctionTool(func=self.update_contact),
            FunctionTool(func=self.delete_contact),
        ]
