# src/components/toolsets/casefile_toolset.py
import logging
from typing import Optional, Dict, List, Any, Union

from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.adk.tools import ToolContext

from src.core.models.user import User
from src.components.casefile.service import CasefileService
from src.components.casefile.models import CasefileUpdate
from src.core.models.google_workspace.drive import DriveFile
from src.core.models.google_workspace.people import GooglePerson
from src.core.models.ontology import CasefileRole

logger = logging.getLogger(__name__)


class CasefileToolset(BaseToolset):
    """A toolset for managing casefiles within the application."""

    def __init__(self, casefile_service: CasefileService):
        self._casefile_service = casefile_service
        super().__init__()

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

    async def list_all_casefiles(
        self, tool_context: ToolContext
    ) -> List[Dict[str, str]]:
        """Lists all available casefiles, returning a list of their names and IDs."""
        casefiles = await self._casefile_service.list_all_casefiles()
        tool_context.state["casefiles_listed"] = True
        if not casefiles:
            return []
        return [{"id": cf.id, "name": cf.name} for cf in casefiles]

    async def create_casefile(
        self, name: str, description: str, tool_context: ToolContext
    ) -> Dict[str, Any]:
        """
        Creates a new casefile.

        Args:
            name: The name of the new casefile.
            description: A brief description of the new casefile.
            tool_context: The runtime context.

        Returns:
            A dictionary containing the details of the newly created casefile.
        """
        user_id = self._get_user_id_from_context(tool_context)
        if not user_id:
            raise ValueError("Could not create casefile because user ID could not be determined from the context.")

        created_casefile = await self._casefile_service.create_casefile(
            name=name, description=description, user_id=user_id
        )
        return created_casefile.model_dump()

    async def delete_casefile(self, casefile_id: str, tool_context: ToolContext) -> bool:
        """
        Deletes a casefile by its ID. Returns True on success, False on failure.

        Args:
            casefile_id: The ID of the casefile to delete.
            tool_context: The runtime context.
        """
        user_id = self._get_user_id_from_context(tool_context)
        if not user_id:
            raise ValueError("Could not delete casefile because user ID could not be determined.")

        return await self._casefile_service.delete_casefile( # type: ignore
            casefile_id=casefile_id, user_id=user_id
        )

    async def get_casefile(
        self, casefile_id: str, tool_context: ToolContext
    ) -> Union[Dict[str, Any], str]:
        """
        Retrieves a single casefile by its ID.

        Args:
            casefile_id: The ID of the casefile to retrieve.
            tool_context: The runtime context.

        Returns:
            A dictionary containing the casefile details, or an error string if not found.
        """
        casefile = await self._casefile_service.load_casefile(casefile_id=casefile_id)
        if not casefile:
            return f"Casefile with ID '{casefile_id}' not found."
        return casefile.model_dump()

    async def update_casefile(
        self, casefile_id: str, updates: Dict[str, Any], tool_context: ToolContext
    ) -> Union[Dict[str, Any], str]:
        """
        Updates an existing casefile with new data.

        Args:
            casefile_id: The ID of the casefile to update.
            updates: A dictionary with the fields to update in the casefile.
            tool_context: The runtime context.

        Returns:
            A dictionary of the updated casefile, or an error string on failure.
        """
        user_id = self._get_user_id_from_context(tool_context)
        if not user_id:
            raise ValueError("Could not update casefile because user ID could not be determined.")

        # The service layer expects a raw dictionary for updates.
        # Pydantic validation on the input happens automatically by ADK.
        updates_dict = CasefileUpdate(**updates).model_dump(exclude_unset=True)

        updated_casefile = await self._casefile_service.update_casefile(
            casefile_id=casefile_id, updates=updates_dict, user_id=user_id
        )
        if not updated_casefile:
            return f"Failed to update or find casefile with ID '{casefile_id}'."
        return updated_casefile.model_dump()

    async def grant_access(
        self, casefile_id: str, user_id_to_grant: str, role: str, tool_context: ToolContext
    ) -> Union[Dict[str, Any], str]:
        """
        Grants a user a specific role on a casefile.

        Args:
            casefile_id: The ID of the casefile.
            user_id_to_grant: The ID of the user to grant access to.
            role: The role to assign (e.g., 'reader', 'writer', 'admin').
            tool_context: The runtime context.

        Returns:
            A dictionary of the updated casefile, or an error string on failure.
        """
        current_user_id = self._get_user_id_from_context(tool_context)
        if not current_user_id:
            raise ValueError("Could not grant access because the current user could not be determined.")

        updated_casefile = await self._casefile_service.grant_access(
            casefile_id=casefile_id,
            user_id_to_grant=user_id_to_grant,
            role=role,
            current_user_id=current_user_id,
        )
        if not updated_casefile:
            # The service layer raises exceptions on failure, but as a fallback:
            return f"Failed to grant access on casefile with ID '{casefile_id}'. Check permissions or user/casefile existence."
        return updated_casefile.model_dump()

    async def revoke_access(
        self, casefile_id: str, user_id_to_revoke: str, tool_context: ToolContext
    ) -> Union[Dict[str, Any], str]:
        """
        Revokes a user's access to a casefile.

        Args:
            casefile_id: The ID of the casefile.
            user_id_to_revoke: The ID of the user whose access is to be revoked.
            tool_context: The runtime context.

        Returns:
            A dictionary of the updated casefile, or an error string on failure.
        """
        current_user_id = self._get_user_id_from_context(tool_context)
        if not current_user_id:
            raise ValueError("Could not revoke access because the current user could not be determined.")

        updated_casefile = await self._casefile_service.revoke_access(
            casefile_id=casefile_id, user_id_to_revoke=user_id_to_revoke, current_user_id=current_user_id
        )
        if not updated_casefile:
            return f"Failed to revoke access on casefile with ID '{casefile_id}'. Check permissions or user/casefile existence."
        return updated_casefile.model_dump()

    async def add_drive_file_to_casefile(
        self,
        casefile_id: str,
        drive_file_data: Dict[str, Any],
        tool_context: ToolContext
    ) -> Union[Dict[str, Any], str]:
        """
        Adds a Google Drive file object to the specified casefile.
        The agent should first get the file using a Google Drive tool, and then pass the resulting object here.

        Args:
            casefile_id: The ID of the casefile to update.
            drive_file_data: A dictionary representing the full DriveFile object.
            tool_context: The runtime context.

        Returns:
            The updated casefile as a dictionary, or an error string.
        """
        user_id = self._get_user_id_from_context(tool_context)
        if not user_id:
            return "Error: Could not determine the user to perform this action for."

        try:
            # Validate the incoming data against the specific Pydantic model
            drive_file = DriveFile(**drive_file_data)
            update_payload = {"drive_files": [drive_file.model_dump(by_alias=True)]}
        except Exception as e:
            return f"Invalid drive_file_data provided. Validation error: {e}"

        logger.info(f"Adding Drive file '{drive_file.id}' to casefile '{casefile_id}'")
        updated_casefile = await self._casefile_service.update_casefile(casefile_id, update_payload, user_id)
        
        if not updated_casefile:
            return f"Failed to add Drive file to casefile '{casefile_id}'."
        return updated_casefile.model_dump()

    async def add_person_to_casefile(
        self,
        casefile_id: str,
        person_data: Dict[str, Any],
        tool_context: ToolContext
    ) -> Union[Dict[str, Any], str]:
        """
        Adds a Google Person object to the specified casefile.
        The agent should first get the contact using a Google People tool, and then pass the resulting object here.

        Args:
            casefile_id: The ID of the casefile to update.
            person_data: A dictionary representing the full GooglePerson object.
            tool_context: The runtime context.

        Returns:
            The updated casefile as a dictionary, or an error string.
        """
        user_id = self._get_user_id_from_context(tool_context)
        if not user_id:
            return "Error: Could not determine the user to perform this action for."
        try:
            person = GooglePerson(**person_data)
            update_payload = {"google_people": [person.model_dump(by_alias=True)]}
        except Exception as e:
            return f"Invalid person_data provided. Validation error: {e}"

        logger.info(f"Adding Person '{person.resource_name}' to casefile '{casefile_id}'")
        updated_casefile = await self._casefile_service.update_casefile(casefile_id, update_payload, user_id)
        if not updated_casefile:
            return f"Failed to add Person to casefile '{casefile_id}'."
        return updated_casefile.model_dump()

    async def get_tools(self, tool_context: "ToolContext") -> list[BaseTool]:
        """Returns a list of all the tool methods in this toolset."""
        return [
            FunctionTool(func=self.list_all_casefiles),
            FunctionTool(func=self.create_casefile),
            FunctionTool(func=self.delete_casefile),
            FunctionTool(func=self.get_casefile),
            FunctionTool(func=self.update_casefile),
            FunctionTool(func=self.grant_access),
            FunctionTool(func=self.revoke_access),
            FunctionTool(func=self.add_drive_file_to_casefile),
            FunctionTool(func=self.add_person_to_casefile),
        ]