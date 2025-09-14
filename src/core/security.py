# src/core/security.py

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

# Importeer de benodigde componenten
from src.core.models.user import TokenData, UserInDB
from src.core.dependencies import get_database_manager
from src.core.managers.database_manager import DatabaseManager

# --- Configuratie ---
SECRET_KEY = os.getenv("SECRET_KEY", "een-geheim-dat-niemand-mag-weten")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 uur

# --- Security Utils ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Authenticatie Functies (nu verbonden met de database) ---

async def authenticate_user(db_manager: DatabaseManager, username: str, password: str) -> Optional[UserInDB]:
    """Haalt een gebruiker op uit de DB en verifieert het wachtwoord."""
    user_data = await db_manager.get("users", username)
    if not user_data:
        return None
    
    user = UserInDB(**user_data)
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db_manager: DatabaseManager = Depends(get_database_manager)
) -> UserInDB:
    """Decodes a JWT token and returns the corresponding user from the database."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user_data = await db_manager.get("users", token_data.username)
    if user_data is None:
        raise credentials_exception
    
    return UserInDB(**user_data)

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Dependency die controleert of de huidige gebruiker actief is."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user