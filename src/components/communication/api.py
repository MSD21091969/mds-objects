from fastapi import APIRouter, Depends, HTTPException
import logging

from .service import CommunicationService
from .models import ChatRequest, ChatResponse
from src.core.dependencies import get_communication_service
from src.core.models.user import User
from src.core.security import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat", response_model=ChatResponse, summary="Send a message to the agent")
async def handle_chat(
    request: ChatRequest,
    comm_service: CommunicationService = Depends(get_communication_service),
    current_user: User = Depends(get_current_active_user)
):
    try:
        response_data = await comm_service.handle_user_request(
            user_input=request.user_input,
            casefile_id=request.casefile_id,
            current_user=current_user
        )
        return ChatResponse(**response_data)
    except Exception as e:
        logger.exception(f"Error handling chat request: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
