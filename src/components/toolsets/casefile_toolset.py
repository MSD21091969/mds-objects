import logging
import json
from typing import Optional, Dict, List, Any

from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.adk.tools import ToolContext
from google.genai import types as adk_types

from src.core.models.user import User
from src.components.casefile.service import CasefileService
from src.components.casefile.models import Casefile, CasefileUpdate

logger = logging.getLogger(__name__)


class CasefileToolset(BaseToolset):
    """A toolset for managing casefiles within the application."""

    def __init__(self, casefile_service: CasefileService):
        self._casefile_service = casefile_service

    def _get_user_id_from_context(self, tool_context: ToolContext) -> str:
        """Helper to extract user ID from the tool context state."""
        user_json = tool_context.state.get("current_user")
        if not user_json:
            raise ValueError("Could not find 'current_user' in tool context state.")
        try:
            user = User.model_validate_json(user_json)
            return user.username
        except Exception as e:
            raise ValueError(f"Failed to parse user from tool_context: {e}") from e

    async def _list_all_casefiles(
        self, tool_context: ToolContext
    ) -> List[Dict[str, str]]:
        """Lists all available casefiles, returning a list of their names and IDs."""
        casefiles = await self._casefile_service.list_all_casefiles()
        tool_context.state["casefiles_listed"] = True
        if not casefiles:
            return []
        return [{"id": cf.id, "name": cf.name} for cf in casefiles]

    async def _create_casefile(
        self, name: str, description: str, tool_context: ToolContext
    ) -> Optional[Dict[str, Any]]:
        """
        Creates a new casefile and returns the created casefile object as a dictionary.
        """
        user_id = self._get_user_id_from_context(tool_context)
        created_casefile = await self._casefile_service.create_casefile(
            name=name, description=description, user_id=user_id
        )
        return created_casefile.model_dump() if created_casefile else None

    async def _delete_casefile(self, casefile_id: str, tool_context: ToolContext) -> bool:
        """
        Deletes a casefile by its ID. Returns True on success, False on failure.
        """
        user_id = self._get_user_id_from_context(tool_context)
        return await self._casefile_service.delete_casefile(
            casefile_id=casefile_id, user_id=user_id
        )

    async def _get_casefile(
        self, casefile_id: str, tool_context: ToolContext
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single casefile by its ID. Returns the casefile object as a dictionary or None if not found.
        """
        casefile = await self._casefile_service.load_casefile(casefile_id=casefile_id)
        return casefile.model_dump() if casefile else None

    async def _update_casefile(
        self, casefile_id: str, updates: Dict[str, Any], tool_context: ToolContext
    ) -> Optional[Dict[str, Any]]:
        """
        Updates an existing casefile with new data. Returns the updated casefile object as a dictionary.
        """
        user_id = self._get_user_id_from_context(tool_context)
        updates_dict = CasefileUpdate(**updates).model_dump(exclude_unset=True)

        updated_casefile = await self._casefile_service.update_casefile(
            casefile_id=casefile_id, updates=updates_dict, user_id=user_id
        )
        return updated_casefile.model_dump() if updated_casefile else None

    async def _grant_access(
        self,
        casefile_id: str,
        user_id_to_grant: str,
        role: str,
        tool_context: ToolContext,
    ) -> Optional[Dict[str, Any]]:
        """
        Grants a user a specific role on a casefile. Returns the updated casefile object as a dictionary.
        """
        current_user_id = self._get_user_id_from_context(tool_context)
        updated_casefile = await self._casefile_service.grant_access(
            casefile_id=casefile_id,
            user_id_to_grant=user_id_to_grant,
            role=role,
            current_user_id=current_user_id,
        )
        return updated_casefile.model_dump() if updated_casefile else None

    async def _revoke_access(
        self, casefile_id: str, user_id_to_revoke: str, tool_context: ToolContext
    ) -> Optional[Dict[str, Any]]:
        """
        Revokes a user's access to a casefile. Returns the updated casefile object as a dictionary.
        """
        current_user_id = self._get_user_id_from_context(tool_context)
        updated_casefile = await self._casefile_service.revoke_access(
            casefile_id=casefile_id,
            user_id_to_revoke=user_id_to_revoke,
            current_user_id=current_user_id,
        )
        return updated_casefile.model_dump() if updated_casefile else None

    def get_tools(self) -> list[BaseTool]:
        """Returns a list of all the tool methods in this toolset."""
        casefile_schema = adk_types.Schema(
            type=adk_types.SchemaType.OBJECT,
            properties={
                "id": adk_types.Schema(type=adk_types.SchemaType.STRING),
                "name": adk_types.Schema(type=adk_types.SchemaType.STRING),
                "description": adk_types.Schema(type=adk_types.SchemaType.STRING),
                "created_at": adk_types.Schema(type=adk_types.SchemaType.STRING),
                "modified_at": adk_types.Schema(type=adk_types.SchemaType.STRING),
                "owner_id": adk_types.Schema(type=adk_types.SchemaType.STRING),
                "acl": adk_types.Schema(
                    type=adk_types.SchemaType.OBJECT,
                    additional_properties=adk_types.Schema(type=adk_types.SchemaType.STRING),
                ),
                "tags": adk_types.Schema(
                    type=adk_types.SchemaType.ARRAY,
                    items=adk_types.Schema(type=adk_types.SchemaType.STRING),
                ),
            },
        )

        update_casefile_schema = adk_types.Schema(
            type=adk_types.SchemaType.OBJECT,
            properties={
                "name": adk_types.Schema(type=adk_types.SchemaType.STRING),
                "description": adk_types.Schema(type=adk_types.SchemaType.STRING),
                "tags": adk_types.Schema(
                    type=adk_types.SchemaType.ARRAY,
                    items=adk_types.Schema(type=adk_types.SchemaType.STRING),
                ),
            },
        )

        return [
            FunctionTool(
                func=self._list_all_casefiles,
                declaration=adk_types.FunctionDeclaration(
                    name="list_all_casefiles",
                    description="Lists all available casefiles, returning a list of their names and IDs.",
                    parameters=adk_types.Schema(
                        type=adk_types.SchemaType.OBJECT, properties={}
                    ),
                    returns=adk_types.Schema(
                        type=adk_types.SchemaType.ARRAY,
                        items=adk_types.Schema(
                            type=adk_types.SchemaType.OBJECT,
                            properties={
                                "id": adk_types.Schema(type=adk_types.SchemaType.STRING),
                                "name": adk_types.Schema(type=adk_types.SchemaType.STRING),
                            },
                        ),
                    ),
                ),
            ),
            FunctionTool(
                func=self._create_casefile,
                declaration=adk_types.FunctionDeclaration(
                    name="create_casefile",
                    description="Creates a new casefile and returns the created casefile object.",
                    parameters=adk_types.Schema(
                        type=adk_types.SchemaType.OBJECT,
                        properties={
                            "name": adk_types.Schema(
                                type=adk_types.SchemaType.STRING,
                                description="The name of the new casefile.",
                            ),
                            "description": adk_types.Schema(
                                type=adk_types.SchemaType.STRING,
                                description="A brief description of the new casefile.",
                            ),
                        },
                        required=["name", "description"],
                    ),
                    returns=casefile_schema,
                ),
            ),
            FunctionTool(
                func=self._delete_casefile,
                declaration=adk_types.FunctionDeclaration(
                    name="delete_casefile",
                    description="Deletes a casefile by its ID. Returns True on success, False on failure.",
                    parameters=adk_types.Schema(
                        type=adk_types.SchemaType.OBJECT,
                        properties={
                            "casefile_id": adk_types.Schema(
                                type=adk_types.SchemaType.STRING,
                                description="The ID of the casefile to delete.",
                            )
                        },
                        required=["casefile_id"],
                    ),
                    returns=adk_types.Schema(type=adk_types.SchemaType.BOOLEAN),
                ),
            ),
            FunctionTool(
                func=self._get_casefile,
                declaration=adk_types.FunctionDeclaration(
                    name="get_casefile",
                    description="Retrieves a single casefile by its ID.",
                    parameters=adk_types.Schema(
                        type=adk_types.SchemaType.OBJECT,
                        properties={
                            "casefile_id": adk_types.Schema(
                                type=adk_types.SchemaType.STRING,
                                description="The ID of the casefile to retrieve.",
                            )
                        },
                        required=["casefile_id"],
                    ),
                    returns=casefile_schema,
                ),
            ),
            FunctionTool(
                func=self._update_casefile,
                declaration=adk_types.FunctionDeclaration(
                    name="update_casefile",
                    description="Updates an existing casefile with new data.",
                    parameters=adk_types.Schema(
                        type=adk_types.SchemaType.OBJECT,
                        properties={
                            "casefile_id": adk_types.Schema(
                                type=adk_types.SchemaType.STRING,
                                description="The ID of the casefile to update.",
                            ),
                            "updates": update_casefile_schema,
                        },
                        required=["casefile_id", "updates"],
                    ),
                    returns=casefile_schema,
                ),
            ),
            FunctionTool(
                func=self._grant_access,
                declaration=adk_types.FunctionDeclaration(
                    name="grant_access",
                    description="Grants a user a specific role on a casefile.",
                    parameters=adk_types.Schema(
                        type=adk_types.SchemaType.OBJECT,
                        properties={
                            "casefile_id": adk_types.Schema(
                                type=adk_types.SchemaType.STRING,
                                description="The ID of the casefile.",
                            ),
                            "user_id_to_grant": adk_types.Schema(
                                type=adk_types.SchemaType.STRING,
                                description="The ID of the user to grant access to.",
                            ),
                            "role": adk_types.Schema(
                                type=adk_types.SchemaType.STRING,
                                description="The role to assign (e.g., 'reader', 'writer', 'admin').",
                            ),
                        },
                        required=["casefile_id", "user_id_to_grant", "role"],
                    ),
                    returns=casefile_schema,
                ),
            ),
            FunctionTool(
                func=self._revoke_access,
                declaration=adk_types.FunctionDeclaration(
                    name="revoke_access",
                    description="Revokes a user's access to a casefile.",
                    parameters=adk_types.Schema(
                        type=adk_types.SchemaType.OBJECT,
                        properties={
                            "casefile_id": adk_types.Schema(
                                type=adk_types.SchemaType.STRING,
                                description="The ID of the casefile.",
                            ),
                            "user_id_to_revoke": adk_types.Schema(
                                type=adk_types.SchemaType.STRING,
                                description="The ID of the user whose access is to be revoked.",
                            ),
                        },
                        required=["casefile_id", "user_id_to_revoke"],
                    ),
                    returns=casefile_schema,
                ),
            ),
        ]
