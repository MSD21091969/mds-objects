# MDSAPP/api/v1/users.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel

from MDSAPP.core.models.user import User, UserRole
from MDSAPP.core.security import get_current_active_user
from MDSAPP.core.dependencies import get_database_manager
from MDSAPP.core.managers.database_manager import DatabaseManager

router = APIRouter()

@router.get("/users", response_model=List[User])
async def list_users(
    current_user: User = Depends(get_current_active_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can view all users.")
    users = await db_manager.get_all_users()
    return users

class RoleUpdate(BaseModel):
    role: UserRole

@router.put("/users/{username}/role", response_model=User)
async def update_user_role(
    username: str,
    role_update: RoleUpdate,
    current_user: User = Depends(get_current_active_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can change user roles.")
    
    if current_user.username == username and role_update.role != UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="Admins cannot revoke their own admin status.")

    updated_user = await db_manager.update_user_role(username, role_update.role)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found.")
    return updated_user
