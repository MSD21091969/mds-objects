# src/components/casefile_management/api.py

from fastapi import APIRouter, HTTPException, Depends
from typing import List

# Importeer de Pydantic modellen en de dependency getter
from src.core.models.casefile import Casefile
from src.components.casefile_management.manager import CasefileManager
from src.core.dependencies import get_casefile_manager
from src.core.security import get_current_user
from src.core.models.user import UserInDB

router = APIRouter()

@router.post("/casefiles", response_model=Casefile, status_code=201)
async def create_casefile_endpoint(
    name: str,
    casefile_manager: CasefileManager = Depends(get_casefile_manager),
    current_user: UserInDB = Depends(get_current_user)
):
    return await casefile_manager.create_casefile(name=name, owner_id=current_user.username)

@router.get("/casefiles/{casefile_id}", response_model=Casefile)
async def get_casefile_endpoint(
    casefile_id: str,
    casefile_manager: CasefileManager = Depends(get_casefile_manager)
):
    casefile = await casefile_manager.get_casefile(casefile_id)
    if not casefile:
        raise HTTPException(status_code=404, detail="Casefile not found")
    return casefile

@router.get("/casefiles", response_model=List[Casefile])
async def list_casefiles_endpoint(
    casefile_manager: CasefileManager = Depends(get_casefile_manager)
):
    return await casefile_manager.list_casefiles()