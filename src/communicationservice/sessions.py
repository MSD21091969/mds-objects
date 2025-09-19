# MDSAPP/api/v1/sessions.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

from MDSAPP.core.models.user import User
from MDSAPP.core.models.user import UserRole
from MDSAPP.core.security import get_current_active_user
from MDSAPP.core.dependencies import get_firestore_session_service
from MDSAPP.core.services.firestore_session_service import FirestoreSessionService
from google.adk.sessions import Session

router = APIRouter()

@router.get("/sessions", response_model=List[str])
async def list_sessions(
    current_user: User = Depends(get_current_active_user),
    session_service: FirestoreSessionService = Depends(get_firestore_session_service)
):
    """
    Lists all available session IDs.
    Only accessible by admin users.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can view sessions.")
    
    session_ids = await session_service.list_all_session_ids()
    return session_ids

@router.get("/sessions/{session_id}", response_model=Session)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    session_service: FirestoreSessionService = Depends(get_firestore_session_service)
):
    """
    Retrieves the full details of a specific session by its ID.
    Only accessible by admin users.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can view sessions.")

    session = await session_service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail=f"Session with ID '{session_id}' not found.")
    
    return session


@router.put("/sessions/{session_id}/state", response_model=Session)
async def update_session_state(
    session_id: str,
    state_update: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    session_service: FirestoreSessionService = Depends(get_firestore_session_service)
):
    """
    Updates the state dictionary of a specific session.
    This performs a merge, not a replacement, of the state.
    Only accessible by admin users.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can modify session state.")

    # Clean up the input state
    state_update.pop("additionalProp1", None)

    # Get the existing session
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session with ID '{session_id}' not found.")

    # Update the state and save the session
    session.state.update(state_update)
    await session_service.save_session(session)

    return session