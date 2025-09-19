import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# Import from new model file
from .models.user import User, UserInDB, Token, TokenData
# Import DB manager for dependency injection
from .dependencies import get_database_manager
from .managers.database_manager import DatabaseManager


# --- Configuration ---
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_that_should_be_in_env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440 # 24 hours

# --- Security Utils ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Authentication function ---
async def authenticate_user(db_manager: DatabaseManager, username: str, password: str) -> Optional[UserInDB]:
    user = await db_manager.get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

import logging

# ... (rest of the imports)

logger = logging.getLogger(__name__)

# ... (rest of the file)

async def get_user_from_token(token: str, db_manager: DatabaseManager) -> Optional[UserInDB]:
    if token is None:
        logger.warning("get_user_from_token received a None token.")
        return None
    try:
        logger.debug(f"Attempting to decode token: {token}")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Token payload missing 'sub' (username).")
            return None
        token_data = TokenData(username=username)
    except JWTError as e:
        logger.error(f"JWTError decoding token: {e}")
        return None
    
    user = await db_manager.get_user_by_username(token_data.username)
    if user is None:
        logger.warning(f"User '{token_data.username}' not found in database.")
    return user

# --- Dependency ---
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db_manager: DatabaseManager = Depends(get_database_manager)
) -> UserInDB:
    user = await get_user_from_token(token, db_manager)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
