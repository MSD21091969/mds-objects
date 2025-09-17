import logging
from typing import Dict, Any, Optional, List

from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool

from src.components.google_workspace.people.service import GooglePeopleService
from src.components.toolsets.google_workspace.people.models import GooglePerson

logger = logging.getLogger(__name__)

class GooglePeopleToolset(BaseToolset):
    """
    A toolset for interacting with Google People.
    """
    def __init__(self, people_service: Optional[GooglePeopleService] = None):
        super().__init__()
        self.people_service = people_service

    def _ensure_service(self):
        """Checks if the People service is available."""
        if not self.people_service:
            raise ConnectionError("GooglePeopleService is not available.")

    def list_contacts(self, page_size: int = 100) -> List[GooglePerson]:
        """
        Lists contacts from the user's Google Contacts.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling people_service.list_contacts with page_size: {page_size}")
        return self.people_service.list_contacts(page_size)

    def get_contact(self, resource_name: str) -> Optional[GooglePerson]:
        """
        Gets a single contact by its resource name.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling people_service.get_contact for resource name: {resource_name}")
        return self.people_service.get_contact(resource_name)

    def create_contact(self, given_name: str, family_name: str, email: Optional[str] = None, phone: Optional[str] = None) -> Optional[GooglePerson]:
        """
        Creates a new contact.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling people_service.create_contact for {given_name} {family_name}")
        return self.people_service.create_contact(given_name, family_name, email, phone)

    def update_contact(self, resource_name: str, etag: str, given_name: Optional[str] = None, family_name: Optional[str] = None, email: Optional[str] = None, phone: Optional[str] = None) -> Optional[GooglePerson]:
        """
        Updates an existing contact.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling people_service.update_contact for resource name: {resource_name}")
        return self.people_service.update_contact(resource_name, etag, given_name, family_name, email, phone)

    def delete_contact(self, resource_name: str):
        """
        Deletes a contact.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling people_service.delete_contact for resource name: {resource_name}")
        self.people_service.delete_contact(resource_name)

    def get_tools(self) -> list[BaseTool]:
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
