from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

# Importeer de benodigde componenten uit de security module en modellen
from src.core.security import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from src.core.models.user import Token, User
from src.components.casefile_management.api import router as casefile_router

app = FastAPI(
    title="MDS7 Rebuild API",
    description="De centrale API voor het MDS7 platform.",
    version="0.2.0"
)

# --- Authenticatie Endpoint ---
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# --- API Routers ---
app.include_router(casefile_router, prefix="/api/v1", tags=["Casefile Management"])


# --- Root Endpoint ---
@app.get("/")
def read_root():
    return {"status": "MDS7 Rebuild API is running"}