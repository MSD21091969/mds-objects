# src/agents/toolsets/casefile_toolset.py

import logging
from typing import Optional, Dict, List
from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools import FunctionTool, BaseTool, ToolContext
from google.ai.generativelanguage_v1beta.types.content import Schema, Type
from core.models.user import User
from src.casefileservice.service import CasefileService
from src.casefileservice.models import Casefile, CasefileUpdate, CreateCasefileRequest, UpdateCasefileRequest, GrantAccessRequest, RevokeAccessRequest
from core.models.ontology import CasefileRole

logger = logging.getLogger(__name__)

class CasefileToolset(BaseToolset):
    """
    A toolset for managing casefiles within the application.
    This is the bridge layer between ADK agents and the CasefileManager business logic.
    """
    def __init__(self, casefile_service: CasefileService):
        self._casefile_service = casefile_service

    def _get_user_id_from_context(self, tool_context: ToolContext) -> Optional[str]:
        """Helper to extract user ID from the tool context state."""
        # Note: In a real ADK setup, this should come from context.invocation_context.session.user_id
        # For this file, we assume it's stored in a specific place for demonstration purposes.
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

    async def get_tools(self) -> list[BaseTool]:
        
        # Helper to get the user ID and raise an error if not found.
        def _get_user_id(tool_context: ToolContext) -> str:
            user_id = self._get_user_id_from_context(tool_context)
            if not user_id:
                raise ValueError("Could not determine user ID from context. User is not authenticated.")
            return user_id

        async def _list_all_casefiles_tool(tool_context: ToolContext) -> List[Dict[str, str]]:
            """
            Lists all available casefiles, returning their IDs and names.
            This is useful for getting an overview of available casefiles.
            """
            return await self._casefile_service.list_all_casefiles()

        async def _create_casefile_tool(
            name: str,
            description: str,
            tool_context: ToolContext
        ) -> dict:
            """
            Creates a new casefile with a given name and description.
            """
            user_id = _get_user_id(tool_context)
            created_casefile = await self._casefile_service.create_casefile(
                name=name, description=description, user_id=user_id
            )
            return created_casefile.model_dump()

        async def _delete_casefile_tool(casefile_id: str, tool_context: ToolContext) -> bool:
            """
            Deletes a casefile by its unique ID.
            """
            user_id = _get_user_id(tool_context)
            return await self._casefile_service.delete_casefile(
                casefile_id=casefile_id, user_id=user_id
            )

        async def _get_casefile_tool(casefile_id: str, tool_context: ToolContext) -> Optional[dict]:
            """
            Retrieves a single casefile by its ID.
            """
            casefile = await self._casefile_service.load_casefile(casefile_id=casefile_id)
            return casefile.model_dump() if casefile else None

        async def _update_casefile_tool(casefile_id: str, updates: CasefileUpdate, tool_context: ToolContext) -> Optional[dict]:
            """
            Updates an existing casefile with new data.
            """
            user_id = _get_user_id(tool_context)
            updated_casefile = await self._casefile_service.update_casefile(
                casefile_id=casefile_id, updates=updates.model_dump(exclude_unset=True), user_id=user_id
            )
            return updated_casefile.model_dump() if updated_casefile else None

        async def _grant_access_tool(casefile_id: str, user_id_to_grant: str, role: str, tool_context: ToolContext) -> Optional[dict]:
            """
            Grants a user a specific role on a casefile.
            """
            current_user_id = _get_user_id(tool_context)
            updated_casefile = await self._casefile_service.grant_access(
                casefile_id=casefile_id, user_id_to_grant=user_id_to_grant, role=role, current_user_id=current_user_id
            )
            return updated_casefile.model_dump() if updated_casefile else None
        
        async def _revoke_access_tool(casefile_id: str, user_id_to_revoke: str, tool_context: ToolContext) -> Optional[dict]:
            """
            Revokes a user's access to a casefile.
            """
            current_user_id = _get_user_id(tool_context)
            updated_casefile = await self._casefile_service.revoke_access(
                casefile_id=casefile_id, user_id_to_revoke=user_id_to_revoke, current_user_id=current_user_id
            )
            return updated_casefile.model_dump() if updated_casefile else None

        return [
            FunctionTool(
                func=_list_all_casefiles_tool,
                name="casefile_list_all",
                description="Lists all casefiles in the system. Use this to get an overview of existing casefiles by ID and name."
            ),
            FunctionTool(
                func=_create_casefile_tool,
                name="casefile_create",
                description="Creates a new top-level casefile with a unique ID, name, and description. This tool is the starting point for a new case.",
                parameters=Schema(
                    type_=Type.OBJECT,
                    properties={
                        "name": Schema(type_=Type.STRING, description="The name of the new casefile."),
                        "description": Schema(type_=Type.STRING, description="A brief description of the purpose of the casefile.")
                    },
                    required=["name", "description"]
                )
            ),
            FunctionTool(
                func=_delete_casefile_tool,
                name="casefile_delete",
                description="Deletes a specific casefile by its ID.",
                parameters=Schema(
                    type_=Type.OBJECT,
                    properties={
                        "casefile_id": Schema(type_=Type.STRING, description="The ID of the casefile to delete.")
                    },
                    required=["casefile_id"]
                )
            ),
            FunctionTool(
                func=_get_casefile_tool,
                name="casefile_get_by_id",
                description="Retrieves a specific casefile's details, including its content, linked objects, and metadata.",
                parameters=Schema(
                    type_=Type.OBJECT,
                    properties={
                        "casefile_id": Schema(type_=Type.STRING, description="The ID of the casefile to retrieve.")
                    },
                    required=["casefile_id"]
                )
            ),
            FunctionTool(
                func=_update_casefile_tool,
                name="casefile_update",
                description="Updates fields of an existing casefile. This is used to modify metadata, add tags, or append processed files.",
                parameters=Schema(
                    type_=Type.OBJECT,
                    properties={
                        "casefile_id": Schema(type_=Type.STRING, description="The ID of the casefile to update."),
                        "updates": Schema(type_=Type.OBJECT, description="A Pydantic object containing the fields to update.")
                    },
                    required=["casefile_id", "updates"]
                )
            ),
            FunctionTool(
                func=_grant_access_tool,
                name="casefile_grant_access",
                description="Grants a specific user a role (reader, writer, or admin) on a casefile's access control list (ACL).",
                parameters=Schema(
                    type_=Type.OBJECT,
                    properties={
                        "casefile_id": Schema(type_=Type.STRING, description="The ID of the casefile to modify."),
                        "user_id_to_grant": Schema(type_=Type.STRING, description="The ID of the user to grant access to."),
                        "role": Schema(type_=Type.STRING, description="The access role, which must be 'reader', 'writer', or 'admin'.")
                    },
                    required=["casefile_id", "user_id_to_grant", "role"]
                )
            ),
            FunctionTool(
                func=_revoke_access_tool,
                name="casefile_revoke_access",
                description="Revokes a user's access to a casefile.",
                parameters=Schema(
                    type_=Type.OBJECT,
                    properties={
                        "casefile_id": Schema(type_=Type.STRING, description="The ID of the casefile to modify."),
                        "user_id_to_revoke": Schema(type_=Type.STRING, description="The ID of the user whose access is to be revoked.")
                    },
                    required=["casefile_id", "user_id_to_revoke"]
                )
            ),
        ]
