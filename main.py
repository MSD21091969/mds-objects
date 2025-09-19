from dotenv import load_dotenv # NEW: Import load_dotenv
load_dotenv() # NEW: Load environment variables from .env file

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from src.core.security import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from src.core.models.user import Token
from src.components.casefile.api import router as casefile_router
from src.components.communication.api import router as chat_router # NIEUW
from src.core.dependencies import get_database_manager
from src.core.managers.database_manager import DatabaseManager
import os

from src.core.logging_config import setup_logging # NEW
from src.core.adk_monitoring.telemetry_setup import setup_opentelemetry # NEW

# Setup basic logging as early as possible
setup_logging() # NEW

# Setup OpenTelemetry
project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
setup_opentelemetry(project_id=project_id) # NEW

app = FastAPI(
    title="MDS7 Rebuild API",
    description="De centrale API voor het MDS7 platform.",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- Authenticatie Endpoint ---
@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    user = await authenticate_user(db_manager, form_data.username, form_data.password)
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
app.include_router(casefile_router, prefix="/api/v1", tags=["Casefile"])
app.include_router(chat_router, prefix="/api/v1", tags=["Communication"]) # NIEUW


# --- Root Endpoint ---
@app.get("/")
def read_root():
    return {"status": "MDS7 Rebuild API is running"}