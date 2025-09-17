import logging
from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.genai import types as adk_types
from typing import List

from src.components.toolsets.google_workspace.people.service import GooglePeopleService
from src.components.toolsets.google_workspace.people.models import Person

logger = logging.getLogger(__name__)

class PeopleToolset(BaseToolset):
    """A toolset for interacting with Google People API."""

    def __init__(self, client_secrets_path: str, token_path: str = "token.json"):
        self.people_service = GooglePeopleService(client_secrets_path, token_path)
        super().__init__()

    def _search_contacts(self, query: str) -> str:
        """Searches for contacts based on a query."""
        try:
            contacts = self.people_service.search_contacts(query)
            return "\n".join([contact.json() for contact in contacts])
        except Exception as e:
            logger.error(f"Error searching contacts: {e}")
            return f"Error searching contacts: {e}"

    def _get_contact(self, resource_name: str) -> str:
        """Gets a specific contact by its resource name."""
        try:
            contact = self.people_service.get_contact(resource_name)
            return contact.json() if contact else "Contact not found."
        except Exception as e:
            logger.error(f"Error getting contact: {e}")
            return f"Error getting contact: {e}"

    def get_tools(self) -> list[BaseTool]:
        """Returns a list of all the tool methods in this toolset."""
        search_contacts_declaration = adk_types.FunctionDeclaration(
            name="search_google_contacts",
            description="Searches for contacts based on a query.",
            parameters=adk_types.Schema(
                type=adk_types.SchemaType.OBJECT,
                properties={
                    "query": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The query to search for contacts (e.g., 'John Doe', 'john.doe@example.com').",
                    ),
                },
                required=["query"],
            ),
            returns=adk_types.Schema(
                type=adk_types.SchemaType.STRING,
                description="A JSON string containing a list of matching contacts.",
            ),
        )

        get_contact_declaration = adk_types.FunctionDeclaration(
            name="get_google_contact",
            description="Gets a specific contact by its resource name.",
            parameters=adk_types.Schema(
                type=adk_types.SchemaType.OBJECT,
                properties={
                    "resource_name": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The resource name of the contact (e.g., 'people/c123456789').",
                    ),
                },
                required=["resource_name"],
            ),
            returns=adk_types.Schema(
                type=adk_types.SchemaType.STRING,
                description="A JSON string containing the contact details, or 'Contact not found.'.",
            ),
        )

        return [
            FunctionTool(
                func=self._search_contacts,
                declaration=search_contacts_declaration,
            ),
            FunctionTool(
                func=self._get_contact,
                declaration=get_contact_declaration,
            ),
        ]
