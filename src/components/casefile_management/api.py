from fastapi import APIRouter, HTTPException
from typing import List
from .manager import CasefileManager
from src.core.models.casefile import Casefile

router = APIRouter()
casefile_manager = CasefileManager() # In de toekomst gaan we dit via 'dependencies' doen

@router.post("/casefiles", response_model=Casefile, status_code=201)
def create_casefile_endpoint(name: str):
    # We hardcoden de user voor nu. Authenticatie is een aparte feature.
    return casefile_manager.create_casefile(name=name, owner_id="user-123")

@router.get("/casefiles/{casefile_id}", response_model=Casefile)
def get_casefile_endpoint(casefile_id: str):
    casefile = casefile_manager.get_casefile(casefile_id)
    if not casefile:
        raise HTTPException(status_code=404, detail="Casefile not found")
    return casefile

@router.get("/casefiles", response_model=List[Casefile])
def list_casefiles_endpoint():
    return casefile_manager.list_casefiles()
