from fastapi import APIRouter, Depends, HTTPException
from .manager import CommunicationManager
from .models import ChatRequest, ChatResponse
from src.core.dependencies import get_communication_manager
from src.core.security import get_current_active_user # Functie bestaat nog niet, maar voegen we later toe
from src.core.models.user import User

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def handle_chat(
    request: ChatRequest,
    comm_manager: CommunicationManager = Depends(get_communication_manager),
    current_user: User = Depends(get_current_active_user) # Deze dependency beveiligt de route
):
    try:
        response_data = await comm_manager.handle_user_request(
            user_input=request.user_input,
            casefile_id=request.casefile_id,
            current_user=current_user
        )
        return ChatResponse(**response_data)
    except Exception as e:
        # In een productie-app zou je hier specifieke errors afvangen
        raise HTTPException(status_code=500, detail=str(e))
