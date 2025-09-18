import logging
from typing import Dict, Any, Optional, List

from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.adk.tools import ToolContext
from google.genai import types as adk_types

from src.components.toolsets.google_workspace.people.service import GooglePeopleService
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

    def _list_contacts(self, page_size: int = 100) -> List[Dict[str, Any]]:
        """
        Lists contacts from the user's Google Contacts.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling people_service.list_contacts with page_size: {page_size}")
        contacts = self.people_service.list_contacts(page_size)
        return [contact.model_dump() for contact in contacts]

    def _get_contact(self, resource_name: str) -> Optional[Dict[str, Any]]:
        """
        Gets a single contact by its resource name.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling people_service.get_contact for resource name: {resource_name}")
        contact = self.people_service.get_contact(resource_name)
        return contact.model_dump() if contact else None

    def _create_contact(self, given_name: str, family_name: str, email: Optional[str] = None, phone: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Creates a new contact.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling people_service.create_contact for {given_name} {family_name}")
        contact = self.people_service.create_contact(given_name, family_name, email, phone)
        return contact.model_dump() if contact else None

    def _update_contact(self, resource_name: str, etag: str, given_name: Optional[str] = None, family_name: Optional[str] = None, email: Optional[str] = None, phone: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Updates an existing contact.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling people_service.update_contact for resource name: {resource_name}")
        contact = self.people_service.update_contact(resource_name, etag, given_name, family_name, email, phone)
        return contact.model_dump() if contact else None

    def _delete_contact(self, resource_name: str) -> str:
        """
        Deletes a contact.
        """
        self._ensure_service()
        logger.info(f"Toolset is calling people_service.delete_contact for resource name: {resource_name}")
        self.people_service.delete_contact(resource_name)
        return f"Contact with resource name '{resource_name}' deleted successfully."

    def get_tools(self, tool_context: "ToolContext") -> list[BaseTool]:
        """
        Returns a list of tools provided by this toolset.
        """
        google_person_schema = adk_types.Schema(
            type=adk_types.Type.OBJECT,
            description="Represents a person in Google Contacts.",
            properties={
                'resource_name': adk_types.Schema(type=adk_types.Type.STRING, description="The unique resource name for the contact."),
                'etag': adk_types.Schema(type=adk_types.Type.STRING, description="The ETag of the resource, required for updates."),
                'display_name': adk_types.Schema(type=adk_types.Type.STRING, description="The contact's full name."),
                'email_addresses': adk_types.Schema(type=adk_types.Type.ARRAY, items=adk_types.Schema(type=adk_types.Type.STRING), description="A list of the contact's email addresses."),
                'phone_numbers': adk_types.Schema(type=adk_types.Type.ARRAY, items=adk_types.Schema(type=adk_types.Type.STRING), description="A list of the contact's phone numbers."),
            }
        )

        list_contacts_declaration = adk_types.FunctionDeclaration(
            name="list_google_contacts",
            description="Lists contacts from the user's Google Contacts.",
            parameters=adk_types.Schema(
                type=adk_types.Type.OBJECT,
                properties={
                    'page_size': adk_types.Schema(type=adk_types.Type.INTEGER, description="The maximum number of contacts to return. Defaults to 100."),
                }
            ),
            returns=adk_types.Schema(
                type=adk_types.Type.ARRAY,
                items=google_person_schema
            )
        )

        get_contact_declaration = adk_types.FunctionDeclaration(
            name="get_google_contact",
            description="Gets a single contact by its unique resource name.",
            parameters=adk_types.Schema(
                type=adk_types.Type.OBJECT,
                properties={
                    'resource_name': adk_types.Schema(type=adk_types.Type.STRING, description="The resource name of the contact to retrieve (e.g., 'people/c123456')."),
                },
                required=['resource_name']
            ),
            returns=google_person_schema
        )

        create_contact_declaration = adk_types.FunctionDeclaration(
            name="create_google_contact",
            description="Creates a new contact in Google Contacts.",
            parameters=adk_types.Schema(
                type=adk_types.Type.OBJECT,
                properties={
                    'given_name': adk_types.Schema(type=adk_types.Type.STRING, description="The contact's first name."),
                    'family_name': adk_types.Schema(type=adk_types.Type.STRING, description="The contact's last name."),
                    'email': adk_types.Schema(type=adk_types.Type.STRING, description="The contact's primary email address."),
                    'phone': adk_types.Schema(type=adk_types.Type.STRING, description="The contact's primary phone number."),
                },
                required=['given_name', 'family_name']
            ),
            returns=google_person_schema
        )

        update_contact_declaration = adk_types.FunctionDeclaration(
            name="update_google_contact",
            description="Updates an existing contact. The 'etag' from a get_contact call is required for this operation.",
            parameters=adk_types.Schema(
                type=adk_types.Type.OBJECT,
                properties={
                    'resource_name': adk_types.Schema(type=adk_types.Type.STRING, description="The resource name of the contact to update."),
                    'etag': adk_types.Schema(type=adk_types.Type.STRING, description="The ETag of the contact, used for optimistic concurrency control."),
                    'given_name': adk_types.Schema(type=adk_types.Type.STRING, description="The contact's new first name."),
                    'family_name': adk_types.Schema(type=adk_types.Type.STRING, description="The contact's new last name."),
                    'email': adk_types.Schema(type=adk_types.Type.STRING, description="The contact's new primary email address."),
                    'phone': adk_types.Schema(type=adk_types.Type.STRING, description="The contact's new primary phone number."),
                },
                required=['resource_name', 'etag']
            ),
            returns=google_person_schema
        )

        delete_contact_declaration = adk_types.FunctionDeclaration(
            name="delete_google_contact",
            description="Deletes a contact from Google Contacts.",
            parameters=adk_types.Schema(
                type=adk_types.Type.OBJECT,
                properties={
                    'resource_name': adk_types.Schema(type=adk_types.Type.STRING, description="The resource name of the contact to delete."),
                },
                required=['resource_name']
            ),
            returns=adk_types.Schema(type=adk_types.Type.STRING, description="A confirmation message indicating success.")
        )

        return [
            FunctionTool(
                func=self._list_contacts,
                declaration=list_contacts_declaration
            ),
            FunctionTool(
                func=self._get_contact,
                declaration=get_contact_declaration
            ),
            FunctionTool(
                func=self._create_contact,
                declaration=create_contact_declaration
            ),
            FunctionTool(
                func=self._update_contact,
                declaration=update_contact_declaration
            ),
            FunctionTool(
                func=self._delete_contact,
                declaration=delete_contact_declaration
            ),
        ]
