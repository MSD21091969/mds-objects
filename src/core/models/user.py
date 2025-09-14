# src/core/models/user.py

from typing import Optional
from pydantic import BaseModel
from enum import Enum

class UserRole(str, Enum):
    """Defines the possible roles a user can have."""
    ADMIN = "admin"
    ANALYST = "analyst"
    REQUESTER = "requester"

class User(BaseModel):
    """The basic User model."""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: bool = False
    role: UserRole = UserRole.REQUESTER

class UserInDB(User):
    """User model as it is stored in the database, including the hashed password."""
    hashed_password: str

class Token(BaseModel):
    """Response model for the /token endpoint."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Data model for the contents of a JWT token."""
    username: Optional[str] = None
