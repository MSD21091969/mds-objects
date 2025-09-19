from fastapi import APIRouter, Depends
from typing import Any, Dict, List
from pydantic import BaseModel, Field

from MDSAPP.core.services.system_capabilities_service import SystemCapabilitiesService
from MDSAPP.core.dependencies import get_system_capabilities_service

# Import all models that should be exposed in Swagger UI
from MDSAPP.CasefileManagement.models.casefile import Casefile
from MDSAPP.CasefileManagement.api.v1 import CreateCasefileRequest, GrantAccessRequest, RevokeAccessRequest, UpdateCasefileRequest
from MDSAPP.core.models.ontology import CasefileType, CasefileRole
from MDSAPP.core.models.user import UserRole, User, UserInDB, Token, TokenData

router = APIRouter()

# Dummy model to expose all desired schemas in Swagger UI
class AllSystemSchemas(BaseModel):
    casefile: Casefile = Field(..., description="Schema for a Casefile.")
    create_casefile_request: CreateCasefileRequest = Field(..., description="Schema for a CreateCasefileRequest.")
    grant_access_request: GrantAccessRequest = Field(..., description="Schema for a GrantAccessRequest.")
    revoke_access_request: RevokeAccessRequest = Field(..., description="Schema for a RevokeAccessRequest.")
    update_casefile_request: UpdateCasefileRequest = Field(..., description="Schema for an UpdateCasefileRequest.")
    casefile_type: CasefileType = Field(..., description="Schema for CasefileType enum.")
    casefile_role: CasefileRole = Field(..., description="Schema for CasefileRole enum.")
    user_role: UserRole = Field(..., description="Schema for UserRole enum.")
    user: User = Field(..., description="Schema for User model.")
    user_in_db: UserInDB = Field(..., description="Schema for UserInDB model.")
    token: Token = Field(..., description="Schema for Token model.")
    token_data: TokenData = Field(..., description="Schema for TokenData model.")

def _recursive_serializer(obj: Any) -> Any:
    """
    Recursively traverses an object to convert Pydantic models and other
    non-serializable types into JSON-safe formats.
    """
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode='json')
    
    if hasattr(obj, 'copy_to_list'): # Handles proto.marshal.collections.repeated.Repeated
        return [_recursive_serializer(item) for item in obj.copy_to_list()]

    if isinstance(obj, list):
        return [_recursive_serializer(item) for item in obj]

    if isinstance(obj, dict):
        return {key: _recursive_serializer(value) for key, value in obj.items()}
    
    # For Google AI Schema objects that are not handled above
    if hasattr(obj, 'properties') and hasattr(obj, 'type') and obj.type.name == 'OBJECT':
        return _convert_google_schema_to_dict(obj)

    return obj

def _convert_google_schema_to_dict(schema_obj: Any) -> Dict[str, Any]:
    """
    Safely converts a Google AI Schema object into a JSON-serializable dictionary.
    """
    if not schema_obj or not hasattr(schema_obj, 'properties'):
        return {}
        
    properties = {}
    for key, value in schema_obj.properties.items():
        prop_dict = {
            'type': value.type.name if hasattr(value, 'type') else 'UNKNOWN',
            'description': getattr(value, 'description', '')
        }
        properties[key] = prop_dict
    
    required_fields = getattr(schema_obj, 'required', [])
    if hasattr(required_fields, 'copy_to_list'):
        required_fields = required_fields.copy_to_list()

    return {
        'type': 'OBJECT',
        'properties': properties,
        'required': list(required_fields) # Ensure it's a list
    }

@router.get("/system/capabilities", response_model=Dict[str, Any])
async def get_system_capabilities(
    capabilities_service: SystemCapabilitiesService = Depends(get_system_capabilities_service)
) -> Dict[str, Any]:
    """
    Returns an overview of the system's capabilities, including tools, agents, and flows.
    """
    capabilities = capabilities_service.get_all_capabilities()
    
    # Recursively serialize the entire capabilities dictionary
    return _recursive_serializer(capabilities)

@router.get("/system/schemas", response_model=AllSystemSchemas, include_in_schema=True)
async def get_system_schemas():
    """
    Exposes all core system Pydantic schemas in the OpenAPI documentation.
    This endpoint is not meant to be called directly, but to enrich the Swagger UI.
    """
    # Return dummy data; the purpose is to expose the schema via response_model
    return {
        "casefile": {"id": "string", "name": "string", "description": "string", "owner_id": "string", "acl": {}, "sub_casefile_ids": [], "created_at": "2023-01-01T00:00:00Z", "modified_at": "2023-01-01T00:00:00Z"},
        "create_casefile_request": {"name": "string", "description": "string"},
        "grant_access_request": {"user_id_to_grant": "string", "role": "reader"},
        "revoke_access_request": {"user_id_to_revoke": "string"},
        "update_casefile_request": {"updates": {"name": "string", "description": "string"}},
        "casefile_type": "erban",
        "casefile_role": "admin",
        "user_role": "admin",
        "user": {"username": "string"},
        "user_in_db": {"username": "string", "hashed_password": "string"},
        "token": {"access_token": "string", "token_type": "string"},
        "token_data": {"username": "string"}
    }
