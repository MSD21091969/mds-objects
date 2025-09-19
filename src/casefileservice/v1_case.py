# MDSAPP/CasefileManagement/api/v1.py

from fastapi import APIRouter, Depends, Body, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional

from .models import (
    Casefile,
    CreateCasefileRequest,
    UpdateCasefileRequest,
    GrantAccessRequest,
    RevokeAccessRequest,
)
from .service import CasefileService
from core.dependencies import get_casefile_service

from core.models.ontology import CasefileRole
from core.security import User, get_current_active_user

router = APIRouter()

@router.get("/casefiles/status", response_model=List[Dict[str, Any]])
async def get_all_casefiles_with_status(
    casefile_manager: CasefileService = Depends(get_casefile_service),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieves a list of all casefiles, each with a calculated status."""
    return await casefile_manager.list_all_casefiles_with_status()

@router.post("/casefiles", response_model=Casefile, status_code=201)
async def create_new_casefile(
    request: CreateCasefileRequest,
    casefile_manager: CasefileService = Depends(get_casefile_service),
    current_user: User = Depends(get_current_active_user)
):
    """
    Creates a new casefile. If a parent_id is provided, it will be nested
    under the parent. Returns the full created casefile object.
    """
    try:
        new_casefile = await casefile_manager.create_casefile(
            name=request.name,
            description=request.description,
            user_id=current_user.username,
            casefile_id=request.casefile_id,
            parent_id=request.parent_id,
        )
        return new_casefile
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) # For parent not found
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/casefiles", response_model=List[Casefile])
async def get_all_casefiles(
    casefile_manager: CasefileService = Depends(get_casefile_service),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieves a list of all top-level casefiles (those without a parent).
    """
    try:
        return await casefile_manager.list_top_level_casefiles()
    except Exception as e:
        # Log the exception for debugging purposes
        # In a real application, you'd use a proper logger
        print(f"Error loading casefiles: {e}")
        raise HTTPException(
            status_code=500,
            detail="Could not load casefiles. This might be due to a database connection issue. Please check the server logs and ensure that the application has the correct credentials to connect to Firestore."
        )

@router.get("/casefiles/{casefile_id}", response_model=Casefile)
async def get_casefile_by_id(
    casefile_id: str,
    casefile_manager: CasefileService = Depends(get_casefile_service),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieves a specific casefile by its ID."""
    casefile = await casefile_manager.load_casefile(casefile_id)
    if not casefile:
        raise HTTPException(status_code=404, detail="Casefile not found")
    return casefile

@router.delete("/casefiles/{casefile_id}", status_code=204)
async def delete_existing_casefile(
    casefile_id: str,
    casefile_manager: CasefileService = Depends(get_casefile_service),
    current_user: User = Depends(get_current_active_user)
):
    """Deletes a casefile by its ID."""
    try:
        success = await casefile_manager.delete_casefile(casefile_id=casefile_id, user_id=current_user.username)
        if not success:
            raise HTTPException(status_code=404, detail="Casefile not found for deletion")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return

@router.patch("/casefiles/{casefile_id}", response_model=Casefile)
async def update_existing_casefile(
    casefile_id: str,
    request: UpdateCasefileRequest,
    casefile_manager: CasefileService = Depends(get_casefile_service),
    current_user: User = Depends(get_current_active_user)
):
    """Updates an existing casefile."""
    try:
        updated_casefile = await casefile_manager.update_casefile(
            casefile_id=casefile_id,
            user_id=current_user.username,
            updates=request.updates.model_dump(exclude_unset=True)
        )
        return updated_casefile
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/casefiles/{casefile_id}/acl/grant", response_model=Casefile)
async def grant_casefile_access(
    casefile_id: str,
    request: GrantAccessRequest,
    casefile_manager: CasefileService = Depends(get_casefile_service),
    current_user: User = Depends(get_current_active_user)
):
    """Grants access to a casefile."""
    try:
        updated_casefile = await casefile_manager.grant_access(
            casefile_id=casefile_id,
            user_id_to_grant=request.user_id_to_grant,
            role=request.role,
            current_user_id=current_user.username
        )
        return updated_casefile
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/casefiles/{casefile_id}/acl/revoke", response_model=Casefile)
async def revoke_casefile_access(
    casefile_id: str,
    request: RevokeAccessRequest,
    casefile_manager: CasefileService = Depends(get_casefile_service),
    current_user: User = Depends(get_current_active_user)
):
    """Revokes access to a casefile."""
    try:
        updated_casefile = await casefile_manager.revoke_access(
            casefile_id=casefile_id,
            user_id_to_revoke=request.user_id_to_revoke,
            current_user_id=current_user.username
        )
        return updated_casefile
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

