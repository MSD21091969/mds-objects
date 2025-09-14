# src/core/security.py

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

# Importeer de Pydantic modellen die we nodig hebben
from src.core.models.user import TokenData, UserInDB

# --- Configuratie ---
# In een productieomgeving zou je dit uit een environment variable halen.
SECRET_KEY = os.getenv("SECRET_KEY", "een-geheim-dat-niemand-mag-weten")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 uur

# --- Security Utils ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifieert een plat wachtwoord tegen een gehashte versie."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genereert een hash van een plat wachtwoord."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creëert een nieuwe JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Dit is een placeholder. De echte implementatie volgt als we de DatabaseManager integreren.
async def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticeert een gebruiker. Retourneert de gebruiker of None."""
    # Placeholder: In een echte app haal je de gebruiker uit de database.
    # We simuleren een gebruiker voor testdoeleinden.
    if username == "testuser":
        # Het wachtwoord is "password"
        hashed_password = get_password_hash("password")
        if verify_password(password, hashed_password):
            return UserInDB(username="testuser", hashed_password=hashed_password)
    return None
